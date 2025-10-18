# Sandbox Game Phase Resolution

## Overview

This document outlines the changes needed to support phase resolution in sandbox games. The key difference is that sandbox games use manual, on-demand phase resolution (via a "Resolve Phase" button) rather than time-based or confirmation-based resolution used in regular games.

## Key Principles

- **Separate resolution flows**: Regular games use time-based + confirmation resolution; sandbox games use manual resolution only
- **Permission-based enforcement**: Custom permissions prevent misuse of endpoints
- **Explicit naming**: Rename existing endpoint to clarify it resolves ALL phases (for background service)

## Permission Changes

### New Permission: `IsSandboxGame`

Add permission class to restrict actions to sandbox games only:

```python
# In common/permissions.py

class IsSandboxGame(permissions.BasePermission):
    message = "This action is only available for sandbox games."

    def has_permission(self, request, view):
        game = view.get_game()
        return game.sandbox
```

### New Permission: `IsNotSandboxGame`

Add permission class to block sandbox games from certain actions:

```python
# In common/permissions.py

class IsNotSandboxGame(permissions.BasePermission):
    message = "Cannot manually confirm phases in sandbox games."

    def has_permission(self, request, view):
        game = view.get_game()
        return not game.sandbox
```

## View Changes

### Update `PhaseStateUpdateView` (Block Sandbox Games)

Prevent manual phase confirmation for sandbox games:

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
        IsNotSandboxGame,  # NEW: Block sandbox games from manual confirmation
    ]
    serializer_class = PhaseStateSerializer

    def get_object(self):
        game = self.get_game()
        member = self.get_current_game_member()
        current_phase = game.current_phase
        return current_phase.phase_states.get(member=member)
```

**Impact**: Calling `PATCH /game/{game_id}/confirm-phase/` on a sandbox game will return 403 Forbidden.

---

### Rename `PhaseResolveView` → `PhaseResolveAllView`

Make it explicit that this endpoint resolves ALL due phases (used by background service):

```python
# In phase/views.py

class PhaseResolveAllView(views.APIView):
    permission_classes = []  # Public endpoint for background service
    serializer_class = PhaseResolveResponseSerializer

    def post(self, request, *args, **kwargs):
        result = Phase.objects.resolve_due_phases()
        return Response(result, status=status.HTTP_200_OK)
```

**Purpose**: Background service calls this periodically to resolve phases that are time-due or have all players ready.

---

### Create `PhaseResolveView` (Sandbox Game Resolution)

New endpoint to resolve the current phase of a specific sandbox game:

```python
# In phase/views.py

from rest_framework import permissions, generics, views, status
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from common.permissions import IsActiveGame, IsActiveGameMember, IsSandboxGame
from common.views import SelectedGameMixin
from common.constants import PhaseStatus
from .models import Phase
from .serializers import PhaseResolveResponseSerializer


class PhaseResolveView(SelectedGameMixin, views.APIView):
    permission_classes = [
        permissions.IsAuthenticated,
        IsActiveGame,
        IsActiveGameMember,
        IsSandboxGame,  # Only allow for sandbox games
    ]
    serializer_class = PhaseResolveResponseSerializer

    def post(self, request, *args, **kwargs):
        game = self.get_game()
        current_phase = get_object_or_404(
            Phase,
            game=game,
            status=PhaseStatus.ACTIVE
        )

        # Resolve just this one phase
        result = Phase.objects.resolve_phase(current_phase)

        return Response(result, status=status.HTTP_200_OK)
```

**Purpose**: User clicks "Resolve Phase" button in sandbox game UI, which calls this endpoint to immediately resolve the current phase.

**Validation**:
- Must be authenticated
- Must be a member of the game
- Must be a sandbox game (enforced by `IsSandboxGame` permission)
- Must have an active phase (enforced by `get_object_or_404`)

---

## Phase Manager Changes

### Add `resolve_phase()` Method

Extract single-phase resolution logic into a reusable method:

```python
# In phase/models.py

from django.db import models
from django.utils import timezone
from django.db.models import Count, F, Q

from adjudication import service as adjudication_service
from phase import utils as phase_utils
from common.constants import PhaseStatus


class PhaseManager(models.Manager):

    def resolve_phase(self, phase):
        """
        Resolve a single phase.

        Args:
            phase: Phase instance to resolve

        Returns:
            dict with resolution result containing:
                - resolved_phase_id: ID of resolved phase
                - next_phase_id: ID of next phase (or None if game ended)
                - game_id: ID of the game
        """
        # Call adjudication service to resolve orders
        result = adjudication_service.resolve(phase)

        # Update phase status to completed
        phase.status = PhaseStatus.COMPLETED
        phase.save()

        # Create next phase based on resolution result
        next_phase = phase_utils.create_next_phase(phase, result)

        return {
            "resolved_phase_id": phase.id,
            "next_phase_id": next_phase.id if next_phase else None,
            "game_id": phase.game.id,
        }

    def resolve_due_phases(self):
        """
        Resolve all phases that are due for resolution.

        A phase is due if:
        - Time-based: scheduled_resolution time has passed
        - Confirmation-based: All phase states have orders_confirmed=True

        Returns:
            dict with count of resolved phases
        """
        # Find time-due phases (excludes infinite duration phases)
        time_due_phases = Phase.objects.filter(
            status=PhaseStatus.ACTIVE,
            scheduled_resolution__lte=timezone.now(),
            scheduled_resolution__isnull=False,
        )

        # Find all-ready phases (includes infinite duration phases)
        all_ready_phases = Phase.objects.filter(
            status=PhaseStatus.ACTIVE,
        ).annotate(
            total_states=Count('phase_states'),
            ready_states=Count(
                'phase_states',
                filter=Q(phase_states__orders_confirmed=True)
            )
        ).filter(
            total_states=F('ready_states'),
            total_states__gt=0,
        )

        # Combine both querysets and remove duplicates
        phases_to_resolve = (time_due_phases | all_ready_phases).distinct()

        resolved_count = 0
        for phase in phases_to_resolve:
            self.resolve_phase(phase)
            resolved_count += 1

        return {
            "resolved_phases_count": resolved_count,
        }
```

**Key changes**:
- Extracted single-phase resolution into `resolve_phase()`
- Both `resolve_phase()` and `resolve_due_phases()` can now be used
- `resolve_due_phases()` calls `resolve_phase()` for each phase
- Properly handles `None` scheduled_resolution (infinite duration)

---

## URL Routing Changes

Update phase URL patterns:

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
    # Get phase state
    path(
        "game/<str:game_id>/phase-state/",
        views.PhaseStateRetrieveView.as_view(),
        name="phase-state-retrieve",
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

**Endpoints**:
- `POST /game/{game_id}/resolve-phase/` - NEW: Resolve sandbox game phase
- `POST /phase/resolve-all/` - RENAMED: Resolve all due phases (background service)
- `PATCH /game/{game_id}/confirm-phase/` - UPDATED: Blocked for sandbox games

---

## Resolution Flow Comparison

### Regular Games

1. **User places orders**: `POST /game/{id}/orders/`
2. **User confirms phase** (optional): `PATCH /game/{id}/confirm-phase/`
3. **Background service runs**: `POST /phase/resolve-all/` (called periodically)
4. **Phase resolves when**:
   - `scheduled_resolution` time passes, OR
   - All players have confirmed (`orders_confirmed=True`)

### Sandbox Games

1. **User places orders for all nations**: `POST /game/{id}/orders/` (multiple times, one per nation)
2. **User clicks "Resolve Phase"**: `POST /game/{id}/resolve-phase/`
3. **Phase resolves immediately**
4. **Note**: Cannot call `PATCH /game/{id}/confirm-phase/` (returns 403)

---

## Game Model Updates

### Update `phase_confirmed()` Method

No changes needed to this method. For sandbox games:
- Returns `True` if any of the user's phase states have `orders_confirmed=True`
- Since manual confirmation is blocked, this will typically be `False`
- The method remains consistent across both game types

```python
# In game/models.py - NO CHANGES NEEDED

def phase_confirmed(self, user):
    current_phase = self.current_phase
    for phase_state in current_phase.phase_states.all():
        if phase_state.member.user.id == user.id and phase_state.orders_confirmed:
            return True
    return False
```

---

## Testing Strategy

### Permission Tests

**IsNotSandboxGame Permission** (`test_permissions.py`):
- [ ] Test regular game allows access
- [ ] Test sandbox game denies access (403)
- [ ] Test error message is correct

**IsSandboxGame Permission** (`test_permissions.py`):
- [ ] Test sandbox game allows access
- [ ] Test regular game denies access (403)
- [ ] Test error message is correct

### PhaseStateUpdateView Tests

**Blocking Sandbox Games** (`phase/tests/test_phase_state_update.py`):
- [ ] Test regular game allows phase confirmation
- [ ] Test sandbox game returns 403 when attempting to confirm phase
- [ ] Test error message indicates sandbox games cannot manually confirm

### PhaseResolveView Tests (Sandbox Resolution)

**Valid Resolution** (`phase/tests/test_phase_resolve.py`):
- [ ] Test authenticated user can resolve their sandbox game phase
- [ ] Test phase status changes to COMPLETED
- [ ] Test next phase is created
- [ ] Test response contains correct phase IDs
- [ ] Test adjudication service is called with correct phase

**Permission Tests** (`phase/tests/test_phase_resolve.py`):
- [ ] Test unauthenticated user cannot resolve phase (401)
- [ ] Test non-member cannot resolve phase (403)
- [ ] Test regular game returns 403 (IsSandboxGame blocks it)
- [ ] Test sandbox game member from different game cannot resolve (404)

**Edge Cases** (`phase/tests/test_phase_resolve.py`):
- [ ] Test resolving when no active phase returns 404
- [ ] Test resolving when phase is already COMPLETED returns 404
- [ ] Test resolving when game is not active (PENDING/COMPLETED) fails appropriately

### PhaseResolveAllView Tests

**Existing Tests Updated** (`phase/tests/test_phase_resolve.py`):
- [ ] Test endpoint renamed to `/phase/resolve-all/`
- [ ] Test resolves all time-due phases
- [ ] Test resolves all all-ready phases
- [ ] Test excludes phases with `scheduled_resolution=None` and not all ready
- [ ] Test includes phases with `scheduled_resolution=None` when all ready
- [ ] Test returns correct count of resolved phases

### Phase Manager Tests

**resolve_phase() Method** (`phase/tests/test_phase_model.py`):
- [ ] Test resolves single phase correctly
- [ ] Test updates phase status to COMPLETED
- [ ] Test creates next phase
- [ ] Test calls adjudication service
- [ ] Test returns correct result dict

**resolve_due_phases() Method** (`phase/tests/test_phase_model.py`):
- [ ] Test resolves multiple phases in single call
- [ ] Test handles time-due phases
- [ ] Test handles all-ready phases
- [ ] Test excludes infinite duration phases that aren't all ready
- [ ] Test includes infinite duration phases when all ready
- [ ] Test calls resolve_phase() for each phase
- [ ] Test returns correct count

### Integration Tests

**Sandbox Game Resolution Flow** (`integration/tests.py`):
- [ ] Test complete sandbox game resolution flow:
  1. Create sandbox game (auto-started)
  2. Place orders for all nations
  3. Call `POST /game/{id}/resolve-phase/`
  4. Verify phase resolved and next phase created
  5. Repeat for multiple phases
  6. Verify game progresses correctly

**Regular Game Resolution Flow** (`integration/tests.py`):
- [ ] Test regular game resolution still works:
  1. Create regular game
  2. Players join and game starts
  3. Players place orders and confirm
  4. Background service resolves phase
  5. Verify phase resolved correctly

---

## Implementation Checklist

- [ ] Add `IsSandboxGame` permission to `common/permissions.py`
- [ ] Add `IsNotSandboxGame` permission to `common/permissions.py`
- [ ] Update `PhaseStateUpdateView` to include `IsNotSandboxGame` permission
- [ ] Rename `PhaseResolveView` to `PhaseResolveAllView`
- [ ] Create new `PhaseResolveView` for sandbox game resolution
- [ ] Add `resolve_phase()` method to `PhaseManager`
- [ ] Update `resolve_due_phases()` to use `resolve_phase()`
- [ ] Update `resolve_due_phases()` to handle `None` scheduled_resolution correctly
- [ ] Update URLs in `phase/urls.py`
- [ ] Write tests for new permissions
- [ ] Write tests for updated `PhaseStateUpdateView`
- [ ] Write tests for new `PhaseResolveView`
- [ ] Write tests for updated `PhaseResolveAllView`
- [ ] Write tests for phase manager methods
- [ ] Write integration tests for both game types

---

## Notes

- **Clear separation**: Regular games use time/confirmation-based resolution; sandbox games use manual resolution
- **Permission-based**: Permissions enforce correct endpoint usage for each game type
- **Reusable logic**: `resolve_phase()` method can be used by both resolution flows
- **Explicit naming**: `PhaseResolveAllView` makes it clear this is for bulk resolution
- **Frontend impact**: Frontend needs "Resolve Phase" button for sandbox games instead of "Confirm Orders"
