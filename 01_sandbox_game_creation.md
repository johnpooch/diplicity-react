# Sandbox Game Creation

## Overview

This document outlines the plan for implementing sandbox game creation functionality. Sandbox games allow a single player to control all nations for practice and experimentation purposes.

## Key Principles

- **Minimize bespoke logic**: Sandbox games should leverage existing game models and logic as much as possible
- **Explicit differentiation**: A `sandbox` boolean field on the Game model makes sandbox games easily identifiable
- **Serializer-level differences**: The main difference between regular and sandbox games is handled at the serializer level

## Game Model Changes

### New Field: `sandbox`

Add a boolean field to the Game model to identify sandbox games:

```python
class Game(BaseModel):
    # ... existing fields ...
    sandbox = models.BooleanField(default=False)
```

### Phase Duration: Allow `None`

Update `movement_phase_duration` to allow `None` for "infinite" duration:

```python
movement_phase_duration = models.CharField(
    max_length=20,
    choices=MovementPhaseDuration.MOVEMENT_PHASE_DURATION_CHOICES,
    null=True,
    blank=True,
)
```

When `movement_phase_duration` is `None`:
- The phase will not auto-resolve based on time
- The phase will only resolve when all players have confirmed their orders
- This is useful for both sandbox games and regular games without time pressure

### Update `movement_phase_duration_seconds` Property

Handle `None` case in the property:

```python
@property
def movement_phase_duration_seconds(self):
    if self.movement_phase_duration is None:
        return None
    # ... existing logic ...
```

### Update `start()` Method

Handle `scheduled_resolution = None` for infinite duration games:

```python
def start(self):
    # ... existing logic ...

    if self.movement_phase_duration is not None:
        current_phase.scheduled_resolution = timezone.now() + timedelta(
            seconds=self.movement_phase_duration_seconds
        )
    else:
        current_phase.scheduled_resolution = None

    # ... rest of logic ...
```

## Manager Method Refactoring

### Extract Member & Channel Creation from `create_from_template`

**Current behavior** (line 58-88):
- Creates game
- Creates ONE member for the user
- Creates public press channel
- Creates initial phase with units/supply centers

**New behavior**:
- Creates game only
- Creates initial phase with units/supply centers
- Member creation moves to serializer
- Channel creation moves to serializer

```python
def create_from_template(self, variant, **kwargs):
    template_phase = variant.template_phase
    game = self.create(variant=variant, **kwargs)

    # Create initial phase
    phase = game.phases.create(
        game=game,
        variant=variant,
        season=template_phase.season,
        year=template_phase.year,
        type=template_phase.type,
        status=PhaseStatus.PENDING,
        ordinal=1,
    )

    # Copy units from template
    for template_unit in template_phase.units.all():
        phase.units.create(
            type=template_unit.type,
            nation=template_unit.nation,
            province=template_unit.province,
            dislodged_by=template_unit.dislodged_by,
        )

    # Copy supply centers from template
    for template_sc in template_phase.supply_centers.all():
        phase.supply_centers.create(
            nation=template_sc.nation,
            province=template_sc.province,
        )

    return game
```

## Serializer Changes

### Update `GameSerializer` (Regular Games)

Move member and channel creation into the serializer:

```python
def create(self, validated_data):
    request = self.context["request"]
    variant = Variant.objects.get(id=validated_data["variant_id"])

    with transaction.atomic():
        game = Game.objects.create_from_template(
            variant,
            name=validated_data["name"],
            nation_assignment=validated_data["nation_assignment"],
            movement_phase_duration=validated_data.get("movement_phase_duration"),
            private=validated_data["private"],
        )

        # Create ONE member for the creator
        game.members.create(user=request.user)

        # Create public press channel
        game.channels.create(name="Public Press", private=False)

        return game
```

### Create `SandboxGameSerializer`

New serializer for sandbox games with minimal configurable fields:

```python
class SandboxGameSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    status = serializers.CharField(read_only=True)
    phases = PhaseSerializer(many=True, read_only=True)
    variant = VariantSerializer(read_only=True)
    members = MemberSerializer(many=True, read_only=True)

    # Only these fields are user-configurable
    name = serializers.CharField()
    variant_id = serializers.CharField(write_only=True)

    def validate_variant_id(self, value):
        if not Variant.objects.filter(id=value).exists():
            raise serializers.ValidationError("Variant with this ID does not exist.")
        return value

    def create(self, validated_data):
        request = self.context["request"]
        variant = Variant.objects.get(id=validated_data["variant_id"])

        with transaction.atomic():
            # Create game with sandbox-specific settings
            game = Game.objects.create_from_template(
                variant,
                name=validated_data["name"],
                sandbox=True,
                private=True,
                nation_assignment=NationAssignment.ORDERED,
                movement_phase_duration=None,  # Infinite
            )

            # Create member for EACH nation (all assigned to the same user)
            for nation in variant.nations.all():
                game.members.create(user=request.user)

            # NO channel creation (no chat functionality in sandbox games)

            # Start the game immediately
            game.start()

            return game
```

## View Changes

### Create `CreateSandboxGameView`

New view for creating sandbox games:

```python
class CreateSandboxGameView(generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = SandboxGameSerializer
```

### Update `GameListView` Filtering

**Default behavior**: Exclude sandbox games from the list

**Updated view**:
```python
class GameListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = GameSerializer
    filterset_class = GameFilter
    filter_backends = [DjangoFilterBackend]

    def get_queryset(self):
        queryset = Game.objects.all().with_related_data()

        # By default, exclude sandbox games
        if 'sandbox' not in self.request.query_params:
            queryset = queryset.filter(sandbox=False)

        return queryset
```

**Usage**:
- `GET /games/` → Returns only non-sandbox games (default)
- `GET /games/?sandbox=true` → Returns only sandbox games
- `GET /games/?sandbox=false` → Explicitly returns only non-sandbox games

### Update `GameFilter`

Add sandbox filter:

```python
class GameFilter(django_filters.FilterSet):
    sandbox = django_filters.BooleanFilter(field_name='sandbox')
    # ... other existing filters

    class Meta:
        model = Game
        fields = ['sandbox', ...]
```

## URL Routing

Add new route for sandbox game creation:

```python
urlpatterns = [
    path("game/", views.GameCreateView.as_view(), name="game-create"),
    path("sandbox-game/", views.CreateSandboxGameView.as_view(), name="sandbox-game-create"),
    # ... other routes
]
```

## Phase Resolution Logic

Update phase resolver to handle `None` scheduled_resolution:

The phase resolver should skip phases where `scheduled_resolution` is `None` unless all phase states are ready.

```python
# In Phase.objects.resolve_due_phases() or similar
def resolve_due_phases(self):
    # Existing logic for time-based resolution
    time_due_phases = Phase.objects.filter(
        status=PhaseStatus.ACTIVE,
        scheduled_resolution__lte=timezone.now(),
    )

    # Also check for phases where all players are ready (even if not time-due)
    all_ready_phases = Phase.objects.filter(
        status=PhaseStatus.ACTIVE,
    ).annotate(
        total_states=Count('phase_states'),
        ready_states=Count('phase_states', filter=Q(phase_states__orders_confirmed=True))
    ).filter(
        total_states=F('ready_states'),
        total_states__gt=0,
    )

    phases_to_resolve = (time_due_phases | all_ready_phases).distinct()
    # ... resolution logic
```

## Sandbox Game Properties

When a sandbox game is created:

1. **`sandbox = True`** - Explicitly marked as sandbox
2. **`private = True`** - Not visible to other players (hardcoded)
3. **`movement_phase_duration = None`** - Infinite duration (hardcoded)
4. **`nation_assignment = ORDERED`** - Predictable nation order (hardcoded)
5. **Multiple members** - One member per nation, all assigned to creator
6. **No channels** - Chat functionality disabled
7. **Immediate start** - Game starts immediately upon creation

## Implementation Checklist

- [ ] Add `sandbox` field to Game model (requires migration)
- [ ] Allow `movement_phase_duration = None` (requires migration)
- [ ] Refactor `Game.objects.create_from_template()` to remove member/channel creation
- [ ] Update `GameSerializer.create()` to handle member/channel creation
- [ ] Create `SandboxGameSerializer` with sandbox-specific logic
- [ ] Create `CreateSandboxGameView` endpoint
- [ ] Update `Game.start()` to handle `scheduled_resolution = None`
- [ ] Update `Game.movement_phase_duration_seconds` to handle `None`
- [ ] Update phase resolver to handle `None` scheduled_resolution
- [ ] Update `GameListView` to filter sandbox games by default
- [ ] Update `GameFilter` to support sandbox filtering
- [ ] Add URL route for sandbox game creation
- [ ] Write tests for sandbox game creation
- [ ] Write tests for sandbox game filtering

## Testing Strategy

### Test Organization

```
service/game/tests/
├── test_game_create.py           # Existing regular game creation tests
├── test_sandbox_game_create.py   # New sandbox game creation tests
├── test_game_list.py             # Existing + new filtering tests
├── test_game_retrieve.py         # Existing (should pass unchanged)
└── test_game_model.py            # Model-level tests for new functionality

service/phase/tests/
├── test_phase_resolve.py         # Updated to test None scheduled_resolution

service/integration/tests.py      # E2E sandbox game creation test
```

### 1. Backward Compatibility Tests

**Objective**: Ensure existing functionality is not broken

- [ ] All existing game creation tests should pass unchanged
- [ ] All existing game list/retrieve tests should pass unchanged
- [ ] All existing member, order, and phase tests should pass unchanged

### 2. New Feature Tests: `None`/Infinite Phase Duration

**Objective**: Test infinite phase duration feature in regular games

**Game Model Tests** (`test_game_model.py`):
- [ ] Test `Game.movement_phase_duration_seconds` returns `None` when `movement_phase_duration=None`
- [ ] Test `Game.movement_phase_duration_seconds` still calculates correctly for existing durations (24h, 48h, 1 week)
- [ ] Test `Game.start()` sets `scheduled_resolution=None` when `movement_phase_duration=None`
- [ ] Test `Game.start()` sets correct `scheduled_resolution` for time-based durations

**Phase Resolution Tests** (`phase/tests/test_phase_resolve.py`):
- [ ] Test phase with `scheduled_resolution=None` does NOT resolve when only some members are ready
- [ ] Test phase with `scheduled_resolution=None` DOES resolve when all members are ready
- [ ] Test regular time-based phase resolution still works (resolves when time passes, even if not all ready)

**Regular Game Creation Tests** (`test_game_create.py`):
- [ ] Test creating regular game with `movement_phase_duration=None`
- [ ] Test game is created with infinite duration and remains pending until joined

### 3. Sandbox Game Creation Tests

**Objective**: Comprehensive coverage of sandbox game creation flow

**SandboxGameSerializer Tests** (`test_sandbox_game_create.py`):
- [ ] Test sandbox game creation with valid data succeeds
- [ ] Test sandbox game creation sets `sandbox=True`
- [ ] Test sandbox game creation sets `private=True`
- [ ] Test sandbox game creation sets `nation_assignment=ORDERED`
- [ ] Test sandbox game creation sets `movement_phase_duration=None`
- [ ] Test sandbox game creation with invalid `variant_id` fails with validation error
- [ ] Test only `name` and `variant_id` are required/accepted fields

**Member Creation Tests** (`test_sandbox_game_create.py`):
- [ ] Test sandbox game creates member for each nation in variant
- [ ] Test all members belong to the same user (creator)
- [ ] Test each member is assigned a different nation
- [ ] Test nations are assigned in ORDERED fashion (predictable order)
- [ ] Test with Classic variant (7 nations) creates 7 members
- [ ] Test with different variant creates correct number of members

**Channel Creation Tests** (`test_sandbox_game_create.py`):
- [ ] Test sandbox game does NOT create any channels
- [ ] Test `game.channels.count() == 0` after creation

**Game Start Tests** (`test_sandbox_game_create.py`):
- [ ] Test sandbox game starts immediately (status=ACTIVE)
- [ ] Test phase states are created for all members
- [ ] Test current phase status is ACTIVE
- [ ] Test current phase `scheduled_resolution=None`
- [ ] Test adjudication service is called to generate options

**Comparison Tests** (`test_sandbox_game_create.py`):
- [ ] Test regular GameSerializer creates only ONE member
- [ ] Test regular GameSerializer creates public press channel
- [ ] Test regular game does NOT start immediately (remains PENDING)

### 4. Game List Filtering Tests

**Objective**: Test sandbox game filtering in list views

**Default Filtering Tests** (`test_game_list.py`):
- [ ] Test `GET /games/` excludes sandbox games by default
  - Create 2 regular games and 2 sandbox games
  - Request without query params
  - Verify only 2 regular games returned
- [ ] Test user only sees their own regular games (existing behavior should still work)

**Explicit Sandbox Filtering Tests** (`test_game_list.py`):
- [ ] Test `GET /games/?sandbox=true` returns only sandbox games
  - Create 2 regular games and 2 sandbox games
  - Request with `sandbox=true`
  - Verify only 2 sandbox games returned
- [ ] Test `GET /games/?sandbox=false` explicitly excludes sandbox games
  - Create 2 regular games and 2 sandbox games
  - Request with `sandbox=false`
  - Verify only 2 regular games returned
- [ ] Test user only sees their own sandbox games
  - User A creates sandbox game
  - User B requests `GET /games/?sandbox=true`
  - User B should not see User A's sandbox game (private=True)

**GameFilter Tests**:
- [ ] Test `GameFilter` supports `sandbox` field
- [ ] Test combining `sandbox` filter with other filters works correctly

### 5. Game Retrieve Tests

**Objective**: Ensure sandbox games can be retrieved correctly

**GameRetrieveView Tests** (`test_game_retrieve.py`):
- [ ] Test `GET /game/{sandbox_game_id}/` returns complete game data
- [ ] Test response includes all members (all belonging to same user)
- [ ] Test response includes `sandbox=True`
- [ ] Test response includes `movement_phase_duration=None`
- [ ] Test response includes phases with correct initial state
- [ ] Test user can retrieve their own sandbox game
- [ ] Test user cannot retrieve another user's sandbox game (private=True)

### 6. Permission & Edge Case Tests

**Objective**: Ensure sandbox games cannot be joined or left

**Join/Leave Restriction Tests** (`test_sandbox_game_create.py` or `member/tests.py`):
- [ ] Test cannot join sandbox game (game is already started)
  - User A creates sandbox game
  - User B attempts `POST /game/{sandbox_game_id}/join/`
  - Should fail with appropriate error (game not pending or permission denied)
- [ ] Test cannot leave sandbox game (game is already active)
  - User creates sandbox game
  - User attempts `POST /game/{sandbox_game_id}/leave/`
  - Should fail with appropriate error (game not pending)
- [ ] Test `game.can_join()` returns False for sandbox games
- [ ] Test `game.can_leave()` returns False for sandbox games

### 7. Integration Tests

**Objective**: End-to-end validation of sandbox game creation flow

**Integration Test** (`integration/tests.py`):
- [ ] Test complete sandbox game creation flow:
  1. Authenticate user
  2. Create sandbox game via API
  3. Verify game created with correct properties
  4. Verify all members created and assigned nations
  5. Verify game started immediately
  6. Verify phase states exist for all members
  7. Verify no channels created
  8. Verify game appears in `GET /games/?sandbox=true`
  9. Verify game does NOT appear in `GET /games/`

### 8. Performance Tests (Optional)

**Objective**: Ensure query performance with multiple members

**Query Optimization Tests**:
- [ ] Test `Game.objects.with_related_data()` efficiently loads sandbox games
- [ ] Test N+1 query issues don't occur when listing sandbox games
- [ ] Verify prefetch queries work correctly with multiple members per game

### Test Coverage Requirements

- **Minimum coverage**: 90% for all new code (serializers, views, model methods)
- **Critical paths**: 100% coverage for game creation and member assignment logic
- **Edge cases**: All permission checks and validation errors must be tested

### Testing Notes

- Use pytest fixtures in `conftest.py` for creating test games, variants, and users
- Use `@pytest.mark.django_db` for database-dependent tests
- Use factory pattern for creating test data (e.g., `create_sandbox_game()` fixture)
- Test both happy paths and error cases
- Verify database state after operations (don't just check response status codes)

## Notes

- This design allows sandbox and regular games to share almost all game logic
- The key difference is in **member creation** (one vs many for same user) and **channel creation** (yes vs no)
- Sandbox games automatically start, while regular games wait for players to join
- Frontend will need to handle sandbox games differently in the UI (separate tab on MyGames screen)
