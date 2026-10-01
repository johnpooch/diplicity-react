---
paths:
  - "service/**/*.py"
---

# Backend conventions (`service/`)

- **No docstrings or comments:** including in tests. Do not annotate assertions to explain their values; when a query-count assertion changes, update the number only. **The one exception is DRF view docstrings**, which are extracted into the OpenAPI schema — write those.

- **Imports go at module top level:** No inline `import` inside a function or method body, even if you find an existing one nearby to copy. The only exception is breaking a genuine circular import — call it out in the PR description when you use it. Do not assume a circular import exists; resolve one only when it actually appears. For circular imports at module level, use `apps.get_model()`.

## Where logic lives

- **Managers** — complex creation and modification logic (e.g. `Game.objects.create_from_template()`)
- **Serializers** — orchestrate manager calls, handle request-specific logic and validation
- **Views** — thin: permissions and delegation only

Each app contains `models.py`, `serializers.py`, `views.py`, `urls.py`, `conftest.py`, `tests.py`, `admin.py`, and `utils.py` when needed.

**Views and serializers live in the app that owns the model being acted on.** Creating a `Member` belongs in `member`, even if the seated user is a bot. Do not put create/list HTTP for one model inside another app because the trigger was a feature of that other app.

**URL routes belong in the owning app's `urls.py`**, even when the path nests under another resource's prefix (e.g. `/variants/<id>/nations/<id>/flag/` lives in `nation/urls.py`). The parent app may `include()` those urlpatterns to preserve the public path structure.

**Do not create a Django app for a 1:1 extension of an existing entity.** Extra fields on a user belong on `UserProfile`, not a parallel `BotProfile`-style sidecar app.

## Notification copy

**Notification copy follows a written style guide.** Read `notification-copy.md` before adding a spec to `service/notification/registry.py` or changing the copy in an existing one — title, tense, person, actor naming and links are settled there, not per spec.

## Error reporting

**`logger.error` is a Sentry error event.** The Sentry logging integration turns every ERROR record into an event against a small monthly quota, so reserve it for failures someone must act on. Log expected outcomes (a stale push token, a missing upload) at `warning` or below.

**Log with `%`-style arguments, never f-strings.** Sentry groups log events by the unformatted message template; interpolating counts or names into the string splits one problem into many issues.

**Trace sampling lives in `project/sentry.py`.** An endpoint the client polls on an interval belongs in its polled paths; a health or asset endpoint belongs in its untraced paths.
