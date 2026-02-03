# Implementation Phase 2.3: Backend Extend Deadline

## Overview

**Goal:** Allow Game Masters to extend the current phase deadline from the backend.

**Current State:** Phase 2.1 and 2.2 are complete. The backend has:
- `IsGameMaster` permission class
- `SelectedGameMixin` for game context in views
- Pause/unpause endpoints as a reference pattern
- `scheduled_resolution` DateTimeField on Phase model
- `MovementPhaseDuration` choices and `duration_to_seconds` utility

**What Phase 2.3 Adds:**
- `extend_deadline` method on Game model
- `POST /game/{gameId}/extend-deadline/` endpoint (GM-only, accepts duration)
- Validation for active phase with scheduled resolution
- Tests for all scenarios

---

## Implementation Tasks

### Task 1: Add `extend_deadline` Method to Game Model

Add a method to the Game model that extends the current phase's deadline by a specified duration.

**Changes to `service/game/models.py`:**

```python
def extend_deadline(self, duration):
    if self.status != GameStatus.ACTIVE:
        raise ValueError("Can only extend deadline for an active game")
    if self.is_paused:
        raise ValueError("Cannot extend deadline while game is paused")

    current_phase = self.current_phase
    if not current_phase or not current_phase.scheduled_resolution:
        raise ValueError("No active phase with a scheduled resolution")

    extension_seconds = duration_to_seconds(duration)
    if not extension_seconds:
        raise ValueError("Invalid duration")

    current_phase.scheduled_resolution += timedelta(seconds=extension_seconds)
    current_phase.save()
```

**Rationale:**
- The method validates game state before modifying the deadline
- Paused games should not have their deadline extended (unpause first, then extend if needed)
- Uses existing `duration_to_seconds` utility for consistency
- Follows the same pattern as `pause()` and `unpause()` methods

**Files to modify:**
- `service/game/models.py` - Add `extend_deadline` method

---

### Task 2: Create `GameExtendDeadlineSerializer`

Create a serializer that accepts a duration and extends the deadline.

**Changes to `service/game/serializers.py`:**

```python
class GameExtendDeadlineSerializer(serializers.Serializer):
    duration = serializers.ChoiceField(
        choices=MovementPhaseDuration.MOVEMENT_PHASE_DURATION_CHOICES,
    )

    def validate(self, attrs):
        if self.instance.is_paused:
            raise serializers.ValidationError("Cannot extend deadline while game is paused")
        current_phase = self.instance.current_phase
        if not current_phase or not current_phase.scheduled_resolution:
            raise serializers.ValidationError("No active phase with a scheduled resolution")
        return attrs

    def update(self, instance, validated_data):
        instance.extend_deadline(validated_data["duration"])
        return instance

    def to_representation(self, instance):
        return GameRetrieveSerializer(instance, context=self.context).data
```

**Rationale:**
- Uses `ChoiceField` with existing `MOVEMENT_PHASE_DURATION_CHOICES` for consistency
- Validates game state in serializer (paused state, active phase existence)
- Delegates actual extension logic to the model method
- Returns full game representation like other game action endpoints

**Files to modify:**
- `service/game/serializers.py` - Add serializer class and import

---

### Task 3: Create `GameExtendDeadlineView`

Create the view endpoint for extending deadlines.

**Changes to `service/game/views.py`:**

```python
class GameExtendDeadlineView(SelectedGameMixin, generics.UpdateAPIView):
    permission_classes = [permissions.IsAuthenticated, IsActiveGame, IsGameMaster]
    serializer_class = GameExtendDeadlineSerializer

    def get_object(self):
        return self.get_game()
```

**Rationale:**
- Uses `UpdateAPIView` since we're modifying existing game data
- Reuses existing permission classes: `IsAuthenticated`, `IsActiveGame`, `IsGameMaster`
- Uses `SelectedGameMixin` for consistent game lookup pattern
- Follows exact same pattern as `GamePauseView` and `GameUnpauseView`

**Note:** The view uses PATCH/PUT methods via `UpdateAPIView`. The frontend will use the mutation hook generated from the OpenAPI schema.

**Files to modify:**
- `service/game/views.py` - Add view class and import serializer

---

### Task 4: Add URL Route

Add the URL route for the extend deadline endpoint.

**Changes to `service/game/urls.py`:**

```python
path(
    "game/<str:game_id>/extend-deadline/",
    views.GameExtendDeadlineView.as_view(),
    name="game-extend-deadline",
),
```

**Placement:** Add after the `unpause` route to keep GM actions grouped together.

**Files to modify:**
- `service/game/urls.py` - Add URL path

---

### Task 5: Write Tests for Extend Deadline

Add comprehensive tests for the extend deadline functionality.

**Test cases to add to `service/game/tests.py`:**

```python
extend_deadline_viewname = "game-extend-deadline"


class TestGameExtendDeadline:

    @pytest.mark.django_db
    def test_extend_deadline_success(self, authenticated_client, active_game_with_gm):
        game = active_game_with_gm()
        phase = game.current_phase
        original_deadline = phase.scheduled_resolution

        url = reverse(extend_deadline_viewname, args=[game.id])
        response = authenticated_client.patch(url, {"duration": "1 hour"})

        assert response.status_code == status.HTTP_200_OK
        phase.refresh_from_db()
        expected_deadline = original_deadline + timedelta(hours=1)
        assert abs((phase.scheduled_resolution - expected_deadline).total_seconds()) < 1

    @pytest.mark.django_db
    def test_extend_deadline_24_hours(self, authenticated_client, active_game_with_gm):
        game = active_game_with_gm()
        phase = game.current_phase
        original_deadline = phase.scheduled_resolution

        url = reverse(extend_deadline_viewname, args=[game.id])
        response = authenticated_client.patch(url, {"duration": "24 hours"})

        assert response.status_code == status.HTTP_200_OK
        phase.refresh_from_db()
        expected_deadline = original_deadline + timedelta(hours=24)
        assert abs((phase.scheduled_resolution - expected_deadline).total_seconds()) < 1

    @pytest.mark.django_db
    def test_extend_deadline_non_game_master_forbidden(
        self, api_client, active_game_with_gm, secondary_user
    ):
        game = active_game_with_gm()
        game.members.create(user=secondary_user)
        api_client.force_authenticate(user=secondary_user)
        url = reverse(extend_deadline_viewname, args=[game.id])
        response = api_client.patch(url, {"duration": "1 hour"})
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.django_db
    def test_extend_deadline_non_member_forbidden(
        self, api_client, active_game_with_gm, secondary_user
    ):
        game = active_game_with_gm()
        api_client.force_authenticate(user=secondary_user)
        url = reverse(extend_deadline_viewname, args=[game.id])
        response = api_client.patch(url, {"duration": "1 hour"})
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.django_db
    def test_extend_deadline_unauthenticated(self, unauthenticated_client, active_game_with_gm):
        game = active_game_with_gm()
        url = reverse(extend_deadline_viewname, args=[game.id])
        response = unauthenticated_client.patch(url, {"duration": "1 hour"})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.django_db
    def test_extend_deadline_pending_game_forbidden(
        self, authenticated_client, pending_game_with_gm
    ):
        game = pending_game_with_gm()
        url = reverse(extend_deadline_viewname, args=[game.id])
        response = authenticated_client.patch(url, {"duration": "1 hour"})
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.django_db
    def test_extend_deadline_paused_game_returns_400(
        self, authenticated_client, active_game_with_gm
    ):
        game = active_game_with_gm()
        game.pause()
        url = reverse(extend_deadline_viewname, args=[game.id])
        response = authenticated_client.patch(url, {"duration": "1 hour"})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.django_db
    def test_extend_deadline_invalid_duration_returns_400(
        self, authenticated_client, active_game_with_gm
    ):
        game = active_game_with_gm()
        url = reverse(extend_deadline_viewname, args=[game.id])
        response = authenticated_client.patch(url, {"duration": "invalid"})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.django_db
    def test_extend_deadline_missing_duration_returns_400(
        self, authenticated_client, active_game_with_gm
    ):
        game = active_game_with_gm()
        url = reverse(extend_deadline_viewname, args=[game.id])
        response = authenticated_client.patch(url, {})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.django_db
    def test_extend_deadline_multiple_times(self, authenticated_client, active_game_with_gm):
        game = active_game_with_gm()
        phase = game.current_phase
        original_deadline = phase.scheduled_resolution

        url = reverse(extend_deadline_viewname, args=[game.id])

        response = authenticated_client.patch(url, {"duration": "1 hour"})
        assert response.status_code == status.HTTP_200_OK

        response = authenticated_client.patch(url, {"duration": "12 hours"})
        assert response.status_code == status.HTTP_200_OK

        phase.refresh_from_db()
        expected_deadline = original_deadline + timedelta(hours=13)
        assert abs((phase.scheduled_resolution - expected_deadline).total_seconds()) < 1
```

**Files to modify:**
- `service/game/tests.py` - Add viewname constant and test class

---

### Task 6: Regenerate API Client

After implementing the backend changes, regenerate the OpenAPI schema and TypeScript client.

**Command:**
```bash
docker compose up codegen
```

This will:
1. Generate the updated OpenAPI schema from Django
2. Generate TypeScript hooks including `useGameExtendDeadlinePartialUpdate`

**Files generated (do not manually edit):**
- `packages/web/src/api/generated/endpoints.ts`
- `packages/web/src/api/generated/model.ts`

---

## Acceptance Criteria

- [ ] Game Masters can extend the current phase deadline using the API
- [ ] Non-Game Masters receive 403 Forbidden
- [ ] Non-members receive 403 Forbidden
- [ ] Unauthenticated users receive 401 Unauthorized
- [ ] Pending games return 403 Forbidden (via IsActiveGame permission)
- [ ] Paused games return 400 Bad Request
- [ ] Invalid duration values return 400 Bad Request
- [ ] Missing duration returns 400 Bad Request
- [ ] Multiple extensions are additive (extending twice adds both durations)
- [ ] All duration choices are accepted (1h, 12h, 24h, 48h, 3d, 4d, 1w, 2w)
- [ ] All tests pass
- [ ] API client is regenerated with new hooks

---

## File Summary

### Files to Modify
```
service/game/
├── models.py       # Add extend_deadline method
├── serializers.py  # Add GameExtendDeadlineSerializer
├── views.py        # Add GameExtendDeadlineView
├── urls.py         # Add URL route
└── tests.py        # Add test class
```

### Files Generated (via codegen)
```
packages/web/src/api/generated/
├── endpoints.ts    # New useGameExtendDeadlinePartialUpdate hook
└── model.ts        # GameExtendDeadline type
```

---

## Implementation Order

1. **Task 1**: Add `extend_deadline` method to Game model
2. **Task 2**: Create `GameExtendDeadlineSerializer`
3. **Task 3**: Create `GameExtendDeadlineView`
4. **Task 4**: Add URL route
5. **Task 5**: Write tests and verify they pass
6. **Task 6**: Regenerate API client

This order ensures the model method is available before the serializer uses it, and tests can be run before regenerating the client.

---

## Design Notes

### Duration Choices
Using the existing `MovementPhaseDuration` choices for consistency. All options (1h through 2w) are available for extension. This provides flexibility for GMs to make small (1h) or large (2w) extensions as needed.

### Paused Game Handling
The endpoint returns 400 if the game is paused. This is intentional:
- Extending while paused creates ambiguity about when the extension applies
- GMs should unpause first (which recalculates the deadline), then extend if needed
- This matches the mental model: "the game is paused, so nothing time-related should change"

### HTTP Method
Using PATCH via `UpdateAPIView` since we're modifying existing game state. This is consistent with the pause/unpause endpoints.

### Response Format
Returns the full game representation via `GameRetrieveSerializer`, same as pause/unpause. This ensures the frontend has updated phase data including the new `scheduled_resolution`.

### Error Handling
- Permission errors (403) handled by DRF permission classes
- Validation errors (400) handled by serializer validation
- Model-level validation provides a safety net but serializer should catch errors first

### Sandbox Games
Sandbox games have `movement_phase_duration=None` and phases without `scheduled_resolution`. The endpoint will return 400 for sandbox games since there's no deadline to extend. This is correct behavior - sandbox games are untimed.
