---
paths:
  - "service/**/*.py"
---

# Backend conventions (`service/`)

- **No docstrings or comments:** including in tests and DRF views. Do not annotate assertions to explain their values; when a query-count assertion changes, update the number only. A view docstring becomes the operation `description` in the OpenAPI schema, and the schema is consumed only by our own generated clients — it needs no prose.

- **Imports go at module top level:** No inline `import` inside a function or method body, even if you find an existing one nearby to copy. The only exception is breaking a genuine circular import — call it out in the PR description when you use it. Do not assume a circular import exists; resolve one only when it actually appears. For circular imports at module level, use `apps.get_model()`.

## Where logic lives

- **Managers** — complex creation and modification logic (e.g. `Game.objects.create_from_template()`)
- **Serializers** — orchestrate manager calls, handle request-specific logic and validation
- **Views** — thin: permissions and delegation only

Each app contains `models.py`, `serializers.py`, `views.py`, `urls.py`, `conftest.py`, `tests.py`, `admin.py`, and `utils.py` when needed.

**Views and serializers live in the app that owns the model being acted on.** Creating a `Member` belongs in `member`, even if the seated user is a bot. Do not put create/list HTTP for one model inside another app because the trigger was a feature of that other app.

**URL routes belong in the owning app's `urls.py`**, even when the path nests under another resource's prefix (e.g. `/variants/<id>/nations/<id>/flag/` lives in `nation/urls.py`). The parent app may `include()` those urlpatterns to preserve the public path structure.

**Do not create a Django app for a 1:1 extension of an existing entity.** Extra fields on a user belong on `UserProfile`, not a parallel `BotProfile`-style sidecar app.
