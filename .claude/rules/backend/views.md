---
paths:
  - "service/**/views.py"
---

# Views

Use DRF generic views. Declare permission classes. Use mixins from `common.views` for shared context. Keep the view body empty of business logic.

```python
# GOOD
class GameRetrieveView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = GameRetrieveSerializer
    queryset = Game.objects.all().with_retrieve_data()

    def get_object(self):
        return get_object_or_404(self.queryset, id=self.kwargs.get("game_id"))

class GamePauseView(SelectedGameMixin, generics.UpdateAPIView):
    permission_classes = [permissions.IsAuthenticated, IsActiveGame, IsGameMaster]
    serializer_class = GamePauseSerializer

    def get_object(self):
        return self.get_game()

# BAD - business logic in the view body
class GamePauseView(generics.UpdateAPIView):
    def update(self, request, *args, **kwargs):
        game = self.get_object()
        if game.is_paused:
            return Response({"error": "Already paused"}, status=400)
        ...
```

## Pick the generic that matches the mutation

Mutating a row that already exists is an `UpdateAPIView`, whatever the operation is called. If a serializer's `create()` starts with a `.get()`, or a `perform_destroy()` sets a flag instead of deleting, the view is the wrong generic.

Resolving the object is the view's job, in `get_object()` — not the serializer's. Prefer DRF's default response over an overridden `create()` / `update()` / `destroy()`: an override to change the status code costs a view body and an `@extend_schema` annotation to keep the schema honest.

No view docstrings. The schema is consumed only by our own generated clients, so operation descriptions earn nothing. Keep `common/views.py` docstring-free too: drf-spectacular falls back to the mixin's docstring, so one there leaks into every endpoint that uses the mixin.

**Review check:** using a DRF generic, not a raw `APIView`? permission classes declared rather than checked in the body? view is thin? mixins used for shared context? queryset uses a QuerySet method (`with_list_data()`, etc.)? generic matches the mutation, with no body override just to change the status code?

- When two endpoints differ only in a small input (who is seated) or authz, share one create path. Thin wrappers are fine when the public API wants distinct operations.
