---
paths:
  - "service/**/permissions.py"
  - "service/**/views.py"
---

# Permissions

Custom permissions live in `service/common/permissions.py` — never in a per-app `permissions.py`. Each class checks exactly one thing and carries a descriptive `message`. Read that file before adding a new class: an existing one often already covers the rule, sometimes on a related object (e.g. draft-variant ownership checked on `Variant` vs on `Nation` via `nation.variant`). Deduplicate rather than copy.

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

## Player or participant

Permission names say which kind of member they admit: a `…GamePlayer` class admits only members holding a seat, a `…GameParticipant` class admits any member row, so a non-playing game master passes. Reach for the participant variant only for capabilities a game master genuinely shares with players — reading and posting in public press — and the player variant for everything tied to a nation. A permission that lets a game master submit orders or claim a seat is a bug, not a generous default.

## Permissions vs validation

Permissions answer questions about the resource being acted on and the identity of the requester — game status, membership, ownership, mode. They must not need request data. Validation that depends on the payload belongs in the serializer.

Never check the same condition in both. A permission returning 403 and a `validate()` returning 400 for one condition is a bug, not defence in depth — the status code becomes whichever layer happens to run first.

**Review check:** checks exactly one concept? composed with other permissions in the view? an existing class already covers it? does the serializer re-check anything a permission already covers?
