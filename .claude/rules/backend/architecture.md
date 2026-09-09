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

Email HTML lives in `email_service/templates.py` as a function returning the rendered body. Serializers call the template and pass the result to `email_service.utils.send_email` — they never hold HTML literals.

The service sends email only in the authentication flow (verification and password reset). There is no email notification channel: player-facing notifications go out over push only, via `notification/registry.py`. Do not add an email transport to the notification pipeline without a product decision to turn it on.
