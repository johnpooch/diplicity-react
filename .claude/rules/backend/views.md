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

A view that deletes a row re-fetches it under `select_for_update()` inside the transaction that deletes it — `resolve_game(request, game_id, lock=True)` for games — and re-runs `check_permissions` against the locked row. Django cascades deletes in Python: an unlocked delete collects children in one snapshot and removes them in another, so anything committed in between survives and the deferred foreign keys reject the whole transaction at COMMIT.

Every view needs a docstring. drf-spectacular extracts it, and without one it picks up the mixin's — which is why unrelated endpoints in the committed schema are described as "Used by views that have a game parameter in the URL".

## Polled endpoints answer unchanged polls with 304

Any GET the client polls mixes in `ConditionalGetMixin` from `common.views`. It hashes the rendered body into an ETag, sets `Cache-Control: private, no-cache`, and returns an empty 304 when `If-None-Match` matches (weak comparison, so Railway's gzip-downgraded `W/` ETags still match). Because the ETag is the body, it cannot go stale — but a polled response must not contain values that change on their own between polls (a countdown in seconds, a server `now`), or every poll becomes a 200 again. The 304 test for the endpoint guards this.

`ConditionalGetMixin` saves bandwidth, not server work: the body is still built on every poll. When building it is expensive, a polled endpoint may mix in `PrecomputedConditionalGetMixin` instead and implement `get_fingerprint()`. The mixin answers a matching `If-None-Match` with an empty 304 after authentication and permissions have run, without calling the list or retrieve handler. Use it only when tests cover every response input:

- Fingerprint what the response exposes, not the raw inputs behind it. Compute values the way the response does: reuse the queryset annotations, policy functions and serializers for small dependencies such as members or events. Do not maintain a second handwritten list of their fields. A raw input whose change leaves the response unchanged, such as a read timestamp behind an unchanged unread count, only causes needless 200s.
- Do not load or serialize the history the endpoint exists to skip. Summarize it with aggregates such as count, maximum ID and maximum `updated_at`. Those aggregates assume the rows are append-only or are changed only through `save()`. A `QuerySet.update()` that rewrites a row without advancing `updated_at` goes undetected, so do not add one to a fingerprinted model.
- Bump the fingerprint's representation-version salt whenever serialization changes without a database change.
- For each input, the endpoint's tests take an ETag, perform the mutation, and assert a 200 with a different ETag. Add tests that changes the response doesn't expose still get a 304. Add a test that an unchanged poll skips the expensive build. Add tests that its query count stays the same as history and related rows grow, comparing two equivalent conditional requests.
- A fixed query count is not fixed database work. Aggregating history still scans it, so describe the saving as skipping serialization and transfer, not as cost independent of history.

`channel/utils.py` holds the reference implementation for the channel list.

**Review check:** using a DRF generic, not a raw `APIView`? permission classes declared rather than checked in the body? view is thin? mixins used for shared context? queryset uses a QuerySet method (`with_list_data()`, etc.)? generic matches the mutation, with no body override just to change the status code? docstring present?

- When two endpoints differ only in a small input (who is seated) or authz, share one create path. Thin wrappers are fine when the public API wants distinct operations.
