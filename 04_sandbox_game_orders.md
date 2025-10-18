# Sandbox Game Orders

## Overview

This document outlines the changes needed to support order creation, listing, and deletion in sandbox games. The key insight is that orderable provinces are mutually exclusive across phase states - each province can only be orderable for exactly one nation in a given phase.

## Key Principles

- **Mutually exclusive provinces**: Each orderable province belongs to exactly one nation's phase state
- **Reuse existing logic**: Leverage the `orderable_provinces` property to determine which phase state to use
- **No special casing**: Order views work the same for regular and sandbox games
- **Simple implementation**: Find the phase state where the source province is orderable

## Why Orderable Provinces Are Mutually Exclusive

### Movement/Retreat Phases

- Each province can have at most **ONE unit**
- Each unit belongs to **ONE nation**
- Therefore, each orderable province belongs to exactly **ONE nation's phase state**

### Adjustment Phases

**BUILD orders:**
- Can only build in supply centers you **OWN**
- Each supply center is owned by **ONE nation**
- Therefore, buildable provinces belong to exactly **ONE nation's phase state**

**DISBAND orders:**
- Can only disband units you **CONTROL**
- Each unit belongs to **ONE nation**
- Therefore, disbandable provinces belong to exactly **ONE nation's phase state**

**Conclusion**: It is impossible for two phase states to have the same orderable province in their `orderable_provinces` list.

---

## Order Model Changes

### Update `Order.objects.create_from_selected()`

**Current implementation** (lines 59-81 in `order/models.py`):
```python
def create_from_selected(self, user, phase, selected):
    phase_state = (
        phase.phase_states.select_related("member__user", "phase", "member", "phase__game__variant")
        .filter(member__user=user)
        .first()  # Only gets first match - problem for sandbox games!
    )
    # ... rest of method
```

**Problem**: Uses `.first()` which only returns the first phase state. For sandbox games, the user has multiple phase states, and we need to determine which one based on the source province.

**New implementation**:
```python
def create_from_selected(self, user, phase, selected):
    order_data = get_order_data_from_selected(selected)
    source = self.try_get_province(phase, order_data["source"])

    # Find the phase state where source is an orderable province
    # Since orderable provinces are mutually exclusive, only one phase state will match
    phase_state = None
    for ps in phase.phase_states.filter(member__user=user):
        if ps.orderable_provinces.filter(id=source.id).exists():
            phase_state = ps
            break

    if not phase_state:
        raise exceptions.ValidationError(
            f"Cannot create order: {source.name} is not orderable for this user"
        )

    # Create order with determined phase_state
    order = Order(phase_state=phase_state, source=source)

    # Build order properties from selected array
    if "order_type" in order_data:
        order.order_type = order_data["order_type"]
    if "unit_type" in order_data:
        order.unit_type = order_data["unit_type"]
    if "target" in order_data:
        order.target = self.try_get_province(phase, order_data["target"])
    if "aux" in order_data:
        order.aux = self.try_get_province(phase, order_data["aux"])
    if "named_coast" in order_data:
        order.named_coast = self.try_get_province(phase, order_data["named_coast"])

    return order
```

**Why this works**:
- **Regular games**: User has 1 phase state, loop runs once, finds the match
- **Sandbox games**: User has N phase states, loop checks each until it finds the one where `source` is orderable
- **All phase types**: Works for movement, retreat, and adjustment phases (BUILD/DISBAND)
- **Validation**: If source is not orderable for any of the user's phase states, raises clear error

---

## View Changes

### OrderListView - No Changes Needed

**Current implementation** (lines 11-16 in `order/views.py`):
```python
class OrderListView(SelectedPhaseMixin, generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = OrderSerializer

    def get_queryset(self):
        return Order.objects.visible_to_user_in_phase(self.request.user, self.get_phase()).with_related_data()
```

**Analysis of `visible_to_user_in_phase()`** (lines 15-19 in `order/models.py`):
```python
def visible_to_user_in_phase(self, user, phase):
    return self.filter(
        Q(phase_state__phase=phase)
        & (Q(phase_state__phase__status=PhaseStatus.COMPLETED) | Q(phase_state__member__user=user))
    )
```

**Why it works for both game types**:
- **If phase is COMPLETED**: Returns ALL orders (for game history viewing)
- **If phase is ACTIVE**: Returns orders where `phase_state__member__user=user`
  - Regular games: Returns orders for the user's ONE nation
  - Sandbox games: Returns orders for ALL nations the user controls

**Conclusion**: ✅ No changes needed - already works correctly!

---

### OrderCreateView - No Changes Needed

**Current implementation** (lines 19-23 in `order/views.py`):
```python
class OrderCreateView(CurrentPhaseMixin, generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated, IsActiveGame, IsActiveGameMember]
    serializer_class = OrderSerializer
```

**Why it works**:
- View doesn't determine phase_state - that's handled by `create_from_selected()`
- Serializer calls `create_from_selected()` which now correctly determines phase_state
- Permissions check user is a member (works for any of their nations in sandbox games)

**Conclusion**: ✅ No changes needed - the updated `create_from_selected()` handles everything!

---

### OrderDeleteView - No Changes Needed

**Current implementation** (lines 25-36 in `order/views.py`):
```python
class OrderDeleteView(CurrentPhaseMixin, generics.DestroyAPIView):
    permission_classes = [permissions.IsAuthenticated, IsActiveGame, IsActiveGameMember]
    serializer_class = EmptySerializer

    def get_object(self):
        phase = self.get_phase()
        return get_object_or_404(
            Order,
            source__province_id=self.kwargs["source_id"],
            phase_state__member__user=self.request.user,
            phase_state__phase=phase,
        )
```

**Why it works for both game types**:
- Each province can only have ONE unit/order per phase
- The unique constraint `unique_order_per_province_per_phase` (line 106 in `order/models.py`) is on `[phase_state, source]`
- Filtering by `source__province_id` + `phase_state__member__user` uniquely identifies the order

**For sandbox games**:
- User has multiple phase states, but only ONE phase state can have an order at a given source
- The filter correctly finds the single order for that source among all the user's phase states

**Conclusion**: ✅ No changes needed - unique constraint ensures correct order is deleted!

---

## Serializer Changes - No Changes Needed

**OrderSerializer** (lines 20-58 in `order/serializers.py`):
```python
class OrderSerializer(serializers.Serializer):
    # ... field definitions ...

    selected = serializers.ListField(
        child=serializers.CharField(),
        allow_empty=False,
        required=False,
    )

    def validate_selected(self, value):
        order = Order.objects.create_from_selected(
            self.context["request"].user,
            self.context["phase"],
            value
        )
        try:
            get_options_for_order(order.phase.transformed_options, order)
        except Exception as e:
            raise exceptions.ValidationError(e)
        return order.selected

    def create(self, validated_data):
        order = Order.objects.create_from_selected(
            self.context["request"].user,
            self.context["phase"],
            validated_data["selected"]
        )
        if order.complete:
            Order.objects.delete_existing_for_source(order.phase_state, order.source)
            order.save()
        return order
```

**Why it works**:
- Serializer calls `create_from_selected()` which now handles phase_state determination
- No changes needed to serializer logic

**Conclusion**: ✅ No changes needed!

---

## Order Creation Flow

### Regular Games

1. **Frontend fetches phase states**: `GET /game/{id}/phase-states/`
   - Returns array with 1 phase state
2. **Frontend displays orderable provinces**: Shows provinces from that phase state
3. **User clicks province**: Starts order creation
4. **User builds order**: Selects order type, target, etc.
5. **Frontend submits**: `POST /game/{id}/orders/` with `selected` array
6. **Backend determines phase_state**:
   - Loops through user's phase states (just 1)
   - Finds the one where source is orderable
   - Creates order with that phase_state
7. **Order saved**: Order created for user's nation

### Sandbox Games

1. **Frontend fetches phase states**: `GET /game/{id}/phase-states/`
   - Returns array with N phase states (one per nation)
2. **Frontend displays orderable provinces**: Merges provinces from all phase states
3. **User clicks province** (e.g., "London"): Starts order creation
4. **User builds order**: Selects order type, target, etc.
5. **Frontend submits**: `POST /game/{id}/orders/` with `selected` array: `["lon", "MOVE", "yor"]`
6. **Backend determines phase_state**:
   - Loops through user's phase states (7 for Classic)
   - Checks each: Is "lon" in this phase_state's orderable_provinces?
   - Finds Britain's phase state (London belongs to Britain)
   - Creates order with Britain's phase_state
7. **Order saved**: Order created for Britain

**Key insight**: The backend automatically determines which nation the order belongs to based on the source province, without the frontend needing to specify it!

---

## API Examples

### Create Order - Regular Game

**Request**: `POST /game/{game_id}/orders/`
```json
{
  "selected": ["lon", "MOVE", "yor"]
}
```

**Backend logic**:
1. Parse selected: source="lon", order_type="MOVE", target="yor"
2. Get user's phase states (1 phase state for Britain)
3. Check if "lon" is orderable in Britain's phase state → YES
4. Create order for Britain's phase state
5. Return order

**Response**:
```json
{
  "source": {
    "id": "lon",
    "name": "London",
    "provinceId": "lon"
  },
  "orderType": "MOVE",
  "target": {
    "id": "yor",
    "name": "Yorkshire",
    "provinceId": "yor"
  },
  "nation": {
    "id": "england",
    "name": "England"
  },
  "complete": true
}
```

### Create Order - Sandbox Game

**Request**: `POST /game/{game_id}/orders/`
```json
{
  "selected": ["par", "MOVE", "bur"]
}
```

**Backend logic**:
1. Parse selected: source="par", order_type="MOVE", target="bur"
2. Get user's phase states (7 phase states: Britain, France, Germany, Italy, Austria, Turkey, Russia)
3. Check if "par" is orderable:
   - Britain's phase state → NO
   - France's phase state → YES (Paris belongs to France)
4. Create order for France's phase state
5. Return order

**Response**:
```json
{
  "source": {
    "id": "par",
    "name": "Paris",
    "provinceId": "par"
  },
  "orderType": "MOVE",
  "target": {
    "id": "bur",
    "name": "Burgundy",
    "provinceId": "bur"
  },
  "nation": {
    "id": "france",
    "name": "France"
  },
  "complete": true
}
```

### List Orders - Sandbox Game

**Request**: `GET /game/{game_id}/orders/{phase_id}`

**Response**: Returns orders for ALL nations the user controls
```json
[
  {
    "source": {"id": "lon", "name": "London"},
    "orderType": "MOVE",
    "target": {"id": "yor", "name": "Yorkshire"},
    "nation": {"id": "england", "name": "England"},
    "complete": true
  },
  {
    "source": {"id": "par", "name": "Paris"},
    "orderType": "MOVE",
    "target": {"id": "bur", "name": "Burgundy"},
    "nation": {"id": "france", "name": "France"},
    "complete": true
  },
  {
    "source": {"id": "ber", "name": "Berlin"},
    "orderType": "HOLD",
    "nation": {"id": "germany", "name": "Germany"},
    "complete": true
  }
  // ... more orders for other nations
]
```

### Delete Order - Sandbox Game

**Request**: `DELETE /game/{game_id}/orders/delete/par`

**Backend logic**:
1. Find order where:
   - `source.province_id = "par"`
   - `phase_state.member.user = request.user`
   - `phase_state.phase = current_phase`
2. In sandbox game, user has 7 phase states, but only France's phase state has an order at "par"
3. Delete that order

**Response**: `204 No Content`

---

## Testing Strategy

### Order Creation Tests

**create_from_selected() Method** (`order/tests/test_order_model.py`):
- [ ] Test regular game: Finds the single phase state
- [ ] Test sandbox game: Finds correct phase state based on source province
- [ ] Test sandbox game with different nations: Creates orders for different phase states
- [ ] Test error when source not orderable for any phase state
- [ ] Test works for movement phase orders
- [ ] Test works for retreat phase orders
- [ ] Test works for adjustment phase BUILD orders
- [ ] Test works for adjustment phase DISBAND orders

**OrderCreateView** (`order/tests/test_order_create.py`):
- [ ] Test regular game: User can create order for their nation
- [ ] Test sandbox game: User can create order for any nation they control
- [ ] Test sandbox game: Creating order for Britain (source="lon")
- [ ] Test sandbox game: Creating order for France (source="par")
- [ ] Test sandbox game: Creating order for Germany (source="ber")
- [ ] Test sandbox game: Cannot create order for non-orderable province
- [ ] Test sandbox game: User cannot create order for province not in any of their phase states
- [ ] Test permissions: Unauthenticated user cannot create order
- [ ] Test permissions: Non-member cannot create order

### Order List Tests

**OrderListView** (`order/tests/test_order_list.py`):
- [ ] Test regular game: Returns orders for user's nation
- [ ] Test sandbox game: Returns orders for ALL nations user controls
- [ ] Test sandbox game with multiple orders: Returns orders from multiple phase states
- [ ] Test completed phase: Shows all orders (for any user viewing)
- [ ] Test active phase: Only shows user's orders
- [ ] Test user only sees their own orders in active phase

### Order Delete Tests

**OrderDeleteView** (`order/tests/test_order_delete.py`):
- [ ] Test regular game: User can delete their order
- [ ] Test sandbox game: User can delete order from any phase state they control
- [ ] Test sandbox game: Delete Britain's order (source="lon")
- [ ] Test sandbox game: Delete France's order (source="par")
- [ ] Test sandbox game: Delete Germany's order (source="ber")
- [ ] Test cannot delete non-existent order (404)
- [ ] Test cannot delete other user's order (404)
- [ ] Test permissions: Unauthenticated user cannot delete
- [ ] Test permissions: Non-member cannot delete

### Integration Tests

**Sandbox Game Order Flow** (`integration/tests.py`):
- [ ] Test complete order flow for sandbox game:
  1. Create sandbox game (7 nations)
  2. Fetch phase states (7 phase states returned)
  3. Create order for Britain (source="lon")
  4. Verify order created with Britain's phase state
  5. Create order for France (source="par")
  6. Verify order created with France's phase state
  7. List orders - verify both orders returned
  8. Delete Britain's order
  9. Verify only France's order remains
  10. Create orders for all 7 nations
  11. Resolve phase
  12. Verify all orders resolved correctly

**Adjustment Phase Orders** (`integration/tests.py`):
- [ ] Test BUILD orders in sandbox game:
  1. Create sandbox game with adjustment phase
  2. User can build in any nation's home supply centers
  3. Backend correctly determines nation from supply center ownership
- [ ] Test DISBAND orders in sandbox game:
  1. User can disband any nation's units
  2. Backend correctly determines nation from unit ownership

---

## Implementation Checklist

- [ ] Update `Order.objects.create_from_selected()` to find phase state by orderable provinces
- [ ] Verify `OrderListView` works correctly (no changes needed)
- [ ] Verify `OrderCreateView` works correctly (no changes needed)
- [ ] Verify `OrderDeleteView` works correctly (no changes needed)
- [ ] Write tests for `create_from_selected()` with regular games
- [ ] Write tests for `create_from_selected()` with sandbox games
- [ ] Write tests for order creation in sandbox games
- [ ] Write tests for order listing in sandbox games
- [ ] Write tests for order deletion in sandbox games
- [ ] Write integration tests for complete order flow
- [ ] Write tests for adjustment phase orders (BUILD/DISBAND)

---

## Notes

- **Elegant solution**: Leverages existing `orderable_provinces` property - no need to check units/supply centers directly
- **Mutually exclusive**: Design guarantees each province belongs to exactly one phase state
- **No view changes**: All three order views (list, create, delete) work without modification
- **Works for all phase types**: Movement, retreat, and adjustment phases all handled the same way
- **Frontend simplicity**: Frontend doesn't need to specify which nation - backend determines it automatically
- **Performance**: Loop checks at most 7 phase states (for Classic Diplomacy), with efficient queryset operations
- **Error handling**: Clear validation error if source province is not orderable
