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

## Email bodies

Email HTML lives in `email_service/templates.py` as a function returning the rendered body. Serializers and tasks call the template and pass the result to `email_service.utils.send_email` — they never hold HTML literals.

Transactional mail (verification, password reset) calls `send_email` directly. It does not go through `emit`: notification deliveries are gated on `profile.email_notifications_enabled` and their specs assume a game context.
