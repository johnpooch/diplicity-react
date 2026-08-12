---
paths:
  - "service/**/*.py"
---

# Architecture

## Where logic lives

- **Managers** — complex creation and modification logic (e.g. `Game.objects.create_from_template()`)
- **Serializers** — orchestrate manager calls, handle request-specific logic and validation
- **Views** — thin: permissions and delegation only

Each app contains `models.py`, `serializers.py`, `views.py`, `urls.py`, `conftest.py`, `tests.py`, `admin.py`, and `utils.py` when needed.
