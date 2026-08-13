---
paths:
  - "service/**/permissions.py"
  - "service/**/views.py"
---

# Permissions

Custom permissions live in `service/common/permissions.py` — never in a per-app `permissions.py`. Each class checks exactly one thing and carries a descriptive `message`. Before adding a new class, check whether an existing one already covers the same rule on a related object (e.g. draft-variant ownership checked on `Variant` vs on `Nation` via `nation.variant`); deduplicate rather than copy.

```python
class IsGameMaster(BasePermission):
    message = "Only the Game Master can perform this action."

    def has_permission(self, request, view):
        game_id = view.kwargs.get("game_id")
        game = get_object_or_404(Game, id=game_id)
        member = game.members.filter(user=request.user).first()
        if not member:
            self.message = "User is not a member of the game."
            return False
        return member.is_game_master
```

Check the existing classes before writing a new one:

| Class | Checks |
| --- | --- |
| `IsActiveGame` | Game status is `ACTIVE` |
| `IsActiveOrCompletedGame` | Status is `ACTIVE`, `COMPLETED`, or `ABANDONED` |
| `IsPendingGame` | Status is `PENDING` |
| `IsGameMember` / `IsNotGameMember` | User is / is not a member |
| `IsActiveGameMember` | Non-eliminated, non-kicked member |
| `IsGameMaster` | User is the game master |
| `IsChannelMember` | Member of the channel (public channels always pass) |
| `IsSpaceAvailable` | Fewer members than variant nations |
| `IsCurrentPhaseActive` | Current phase status is `ACTIVE` |
| `IsUserPhaseStateExists` | User has a phase state for the current phase |
| `IsSandboxGame` / `IsNotSandboxGame` | Game is / is not a sandbox |
| `IsOwnedDraftForWrite` | Draft variant owned by request user (works on `Variant` or `Nation`) |

## Permissions vs validation

Permissions answer questions about the resource being acted on and the identity of the requester — game status, membership, ownership, mode. They must not need request data. Validation that depends on the payload belongs in the serializer.

Never check the same condition in both. A permission returning 403 and a `validate()` returning 400 for one condition is a bug, not defence in depth — the status code becomes whichever layer happens to run first.

**Review check:** checks exactly one concept? composed with other permissions in the view? an existing class already covers it? does the serializer re-check anything a permission already covers?
