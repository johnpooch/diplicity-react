---
paths:
  - "service/**/serializers.py"
  - "service/**/models.py"
---

# Transactions

Use `transaction.atomic()` when creating multiple related objects, and `transaction.on_commit()` for side effects that must only run after a successful commit (e.g. notifications).

```python
def create(self, validated_data):
    with transaction.atomic():
        game = Game.objects.create_from_template(variant, ...)
        game.members.create(user=request.user, is_game_master=True)
        game.channels.create(name="Public Press", private=False)
    return Game.objects.all().with_related_data().get(id=game.id)
```
