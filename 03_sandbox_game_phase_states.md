# Sandbox Game Phase States

## Overview

This document outlines the changes needed to support phase states in sandbox games. The key challenge is that sandbox games have multiple phase states per user (one per nation), while regular games have only one phase state per user.

## Key Principles

- **Consistent API**: Same endpoint works for both game types, returning an array in both cases
- **Frontend aggregation**: Frontend merges orderable provinces from all phase states
- **No backend special-casing**: Backend doesn't need `if sandbox` logic in most places
- **Defensive programming**: Use `.filter().first()` instead of `.get()` to avoid crashes

## View Changes

### Convert `PhaseStateRetrieveView` → `PhaseStateListView`

**Current behavior** (retrieve):
- Returns single phase state object
- Uses `CurrentGameMemberMixin` to get the user's member
- Fails for sandbox games (multiple members match)

**New behavior** (list):
- Returns array of phase states
- Filters by user, returns all matching phase states
- Works for both regular (1 result) and sandbox (N results) games

```python
# In phase/views.py

from rest_framework import permissions, generics, views, status
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from common.permissions import (
    IsActiveGame,
    IsActiveGameMember,
    IsCurrentPhaseActive,
    IsUserPhaseStateExists,
    IsNotSandboxGame,
)
from common.views import SelectedGameMixin, CurrentGameMemberMixin
from common.constants import PhaseStatus
from .models import Phase
from .serializers import PhaseStateSerializer, PhaseResolveResponseSerializer


class PhaseStateUpdateView(SelectedGameMixin, CurrentGameMemberMixin, generics.UpdateAPIView):
    permission_classes = [
        permissions.IsAuthenticated,
        IsActiveGame,
        IsActiveGameMember,
        IsCurrentPhaseActive,
        IsUserPhaseStateExists,
        IsNotSandboxGame,  # Block sandbox games from manual confirmation
    ]
    serializer_class = PhaseStateSerializer

    def get_object(self):
        game = self.get_game()
        member = self.get_current_game_member()
        current_phase = game.current_phase
        return current_phase.phase_states.get(member=member)


class PhaseStateListView(SelectedGameMixin, generics.ListAPIView):
    """
    List all phase states for the current user in the current phase.

    For regular games: Returns array with 1 phase state
    For sandbox games: Returns array with N phase states (one per nation)
    """
    permission_classes = [
        permissions.IsAuthenticated,
        IsActiveGame,
        IsActiveGameMember,
    ]
    serializer_class = PhaseStateSerializer

    def get_queryset(self):
        game = self.get_game()
        current_phase = game.current_phase
        return current_phase.phase_states.filter(member__user=self.request.user)
```

---

## Mixin Changes

### Update `CurrentGameMemberMixin` for Defensive Programming

**Problem**: Using `.get()` raises `MultipleObjectsReturned` for sandbox games before permission checks can run.

**Solution**: Use `.filter().first()` to return the first member without crashing.

```python
# In common/views.py

class CurrentGameMemberMixin:
    """
    Used by views that have a game parameter in the URL. Provides a get_current_game_member
    method that returns the user's member for the game. Also adds game member to the serializer context.
    """

    def get_current_game_member(self):
        game = self.get_game()
        return game.members.filter(user=self.request.user).first()  # Changed from .get()

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["current_game_member"] = self.get_current_game_member()
        return context
```

**Why this is better**:
- **Regular games**: Returns the one member (no behavior change)
- **Sandbox games**: Returns first member instead of crashing
- **Permission checks**: Still run and provide proper error messages
- **Defensive**: Won't crash if accidentally called on sandbox game

**Views using this mixin**:
- `PhaseStateUpdateView` - Protected by `IsNotSandboxGame` permission
- `ChannelCreateView` - Sandbox games have no channels, so using first member is safe
- `ChannelMessageCreateView` - Sandbox games have no channels, so using first member is safe

---

## URL Changes

Update phase URLs to use list endpoint:

```python
# In phase/urls.py

from django.urls import path
from . import views

urlpatterns = [
    # Confirm phase (regular games only)
    path(
        "game/<str:game_id>/confirm-phase/",
        views.PhaseStateUpdateView.as_view(),
        name="game-confirm-phase",
    ),
    # List phase states (both game types)
    path(
        "game/<str:game_id>/phase-states/",  # Changed from phase-state (singular)
        views.PhaseStateListView.as_view(),
        name="phase-state-list",
    ),
    # Resolve single phase (sandbox games only)
    path(
        "game/<str:game_id>/resolve-phase/",
        views.PhaseResolveView.as_view(),
        name="game-resolve-phase",
    ),
    # Resolve all due phases (background service)
    path(
        "phase/resolve-all/",
        views.PhaseResolveAllView.as_view(),
        name="phase-resolve-all"
    ),
]
```

---

## Serializer (No Changes Needed)

The existing `PhaseStateSerializer` works for both game types:

```python
# In phase/serializers.py - NO CHANGES NEEDED

class PhaseStateSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    orders_confirmed = serializers.BooleanField(read_only=True)
    eliminated = serializers.BooleanField(read_only=True)
    orderable_provinces = ProvinceSerializer(read_only=True, many=True)
```

---

## API Response Examples

### Regular Game

**Request**: `GET /game/{game_id}/phase-states/`

**Response**: Array with ONE phase state
```json
[
  {
    "id": "phase-state-123",
    "orders_confirmed": false,
    "eliminated": false,
    "orderable_provinces": [
      {
        "id": "lon",
        "name": "London",
        "provinceId": "lon"
      },
      {
        "id": "lvp",
        "name": "Liverpool",
        "provinceId": "lvp"
      },
      {
        "id": "edi",
        "name": "Edinburgh",
        "provinceId": "edi"
      }
    ]
  }
]
```

### Sandbox Game

**Request**: `GET /game/{game_id}/phase-states/`

**Response**: Array with MULTIPLE phase states (one per nation)
```json
[
  {
    "id": "phase-state-britain-123",
    "orders_confirmed": false,
    "eliminated": false,
    "orderable_provinces": [
      {
        "id": "lon",
        "name": "London",
        "provinceId": "lon"
      },
      {
        "id": "lvp",
        "name": "Liverpool",
        "provinceId": "lvp"
      },
      {
        "id": "edi",
        "name": "Edinburgh",
        "provinceId": "edi"
      }
    ]
  },
  {
    "id": "phase-state-france-124",
    "orders_confirmed": false,
    "eliminated": false,
    "orderable_provinces": [
      {
        "id": "par",
        "name": "Paris",
        "provinceId": "par"
      },
      {
        "id": "mar",
        "name": "Marseilles",
        "provinceId": "mar"
      },
      {
        "id": "bre",
        "name": "Brest",
        "provinceId": "bre"
      }
    ]
  },
  {
    "id": "phase-state-germany-125",
    "orders_confirmed": false,
    "eliminated": false,
    "orderable_provinces": [
      {
        "id": "ber",
        "name": "Berlin",
        "provinceId": "ber"
      },
      {
        "id": "mun",
        "name": "Munich",
        "provinceId": "mun"
      },
      {
        "id": "kie",
        "name": "Kiel",
        "provinceId": "kie"
      }
    ]
  }
  // ... 4 more nations (Italy, Austria, Turkey, Russia)
]
```

---

## Frontend Integration

### Fetching Phase States

```typescript
// Both game types use the same API call
const phaseStates = await fetch(`/game/${gameId}/phase-states/`)
  .then(res => res.json());

// phaseStates is always an array
// Regular game: length = 1
// Sandbox game: length = 7 (for Classic Diplomacy)
```

### Aggregating Orderable Provinces

```typescript
// Merge all orderable provinces from all phase states
const allOrderableProvinces = phaseStates.flatMap(
  ps => ps.orderableProvinces
);

// Remove duplicates by province ID
const uniqueOrderableProvinces = Array.from(
  new Map(
    allOrderableProvinces.map(p => [p.provinceId, p])
  ).values()
);

// Mark these provinces as clickable on the map
markProvincesAsOrderable(uniqueOrderableProvinces);
```

### Checking Orders Confirmed Status

```typescript
// Check if ALL phase states have orders confirmed
const allOrdersConfirmed = phaseStates.every(
  ps => ps.ordersConfirmed
);

// For sandbox games, we won't show "Confirm Orders" UI anyway
// But this logic works consistently for both game types
if (allOrdersConfirmed && !game.sandbox) {
  showConfirmOrdersButton();
}
```

### Conditional UI Based on Game Type

```typescript
if (game.sandbox) {
  // Sandbox game: Show "Resolve Phase" button
  // User can place orders for all nations, then resolve manually
  showResolvePhaseButton();
} else {
  // Regular game: Show "Confirm Orders" button
  // User can confirm when ready, phase auto-resolves on timer
  showConfirmOrdersButton();
}
```

---

## Phase State Flow Comparison

### Regular Games

1. **Fetch phase states**: `GET /game/{id}/phase-states/`
   - Returns array with 1 phase state
2. **Display orderable provinces**: Show provinces for user's nation
3. **User places orders**: `POST /game/{id}/orders/`
4. **User confirms**: `PATCH /game/{id}/confirm-phase/`
5. **Background resolution**: Phase resolves when time expires OR all players confirm

### Sandbox Games

1. **Fetch phase states**: `GET /game/{id}/phase-states/`
   - Returns array with N phase states (one per nation)
2. **Display orderable provinces**: Merge provinces from all nations
3. **User places orders for all nations**: `POST /game/{id}/orders/` (multiple times)
4. **User resolves phase**: `POST /game/{id}/resolve-phase/`
5. **Immediate resolution**: Phase resolves immediately when user clicks "Resolve Phase"

---

## Testing Strategy

### PhaseStateListView Tests

**Basic Functionality** (`phase/tests/test_phase_state_list.py`):
- [ ] Test authenticated user can list phase states
- [ ] Test unauthenticated user cannot list phase states (401)
- [ ] Test non-member cannot list phase states (403)
- [ ] Test returns empty array when no phase states exist

**Regular Game Tests** (`phase/tests/test_phase_state_list.py`):
- [ ] Test regular game returns array with 1 phase state
- [ ] Test phase state includes correct orderable provinces
- [ ] Test phase state includes correct `orders_confirmed` status
- [ ] Test phase state includes correct `eliminated` status

**Sandbox Game Tests** (`phase/tests/test_phase_state_list.py`):
- [ ] Test sandbox game returns array with N phase states (one per nation)
- [ ] Test each phase state belongs to different nation
- [ ] Test each phase state has nation-specific orderable provinces
- [ ] Test with Classic variant returns 7 phase states
- [ ] Test user only sees their own phase states (not other users' sandbox games)

**Edge Cases** (`phase/tests/test_phase_state_list.py`):
- [ ] Test game with no current phase returns empty array
- [ ] Test eliminated member still appears in list (eliminated=true)
- [ ] Test phase state list reflects current phase (not old phases)

### CurrentGameMemberMixin Tests

**Defensive Behavior** (`common/tests/test_views.py`):
- [ ] Test regular game: Returns the one member
- [ ] Test sandbox game: Returns first member (doesn't crash)
- [ ] Test game with no members: Returns None
- [ ] Test mixin adds member to serializer context

### Integration Tests

**Regular Game Flow** (`integration/tests.py`):
- [ ] Test complete flow:
  1. Create regular game
  2. Join game and start
  3. Fetch phase states → verify array with 1 item
  4. Place orders
  5. Confirm orders
  6. Verify phase resolves

**Sandbox Game Flow** (`integration/tests.py`):
- [ ] Test complete flow:
  1. Create sandbox game
  2. Fetch phase states → verify array with 7 items
  3. Verify orderable provinces span all nations
  4. Place orders for multiple nations
  5. Resolve phase manually
  6. Verify phase resolved and next phase created

---

## Implementation Checklist

- [ ] Convert `PhaseStateRetrieveView` to `PhaseStateListView`
- [ ] Update `CurrentGameMemberMixin` to use `.filter().first()`
- [ ] Update URL from `/phase-state/` to `/phase-states/`
- [ ] Update API documentation to reflect list endpoint
- [ ] Write tests for `PhaseStateListView` with regular games
- [ ] Write tests for `PhaseStateListView` with sandbox games
- [ ] Write tests for updated `CurrentGameMemberMixin`
- [ ] Write integration tests for phase state flows
- [ ] Update frontend to handle array response
- [ ] Update frontend to aggregate orderable provinces
- [ ] Update frontend to check all phase states for confirmation status

---

## Notes

- **Backward compatibility**: The endpoint URL changes from `/phase-state/` (singular) to `/phase-states/` (plural), which will require frontend updates
- **Response shape**: Response is now always an array, making frontend handling more consistent
- **Scalability**: This approach works for any number of nations (1 to N)
- **No special-casing**: Backend doesn't need sandbox-specific logic in the view
- **Frontend flexibility**: Frontend can choose to merge provinces or display them per-nation
- **Defensive programming**: Using `.filter().first()` prevents crashes in edge cases
