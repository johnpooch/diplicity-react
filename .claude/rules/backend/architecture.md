---
paths:
  - "service/**/*.py"
---

# Architecture

## Where logic lives

- **Models** — domain facts about one row, as properties (e.g. `Member.departure` and its precedence)
- **QuerySets and managers** — reusable queries, prefetch strategies and hydration shared by more than one caller, and complex creation and modification logic (e.g. `Game.objects.create_from_template()`)
- **Services** — a use case whose orchestration and policy do not naturally belong to one model (see below)
- **Serializers** — declare the wire contract; orchestrate manager calls, handle request-specific logic and validation, or serialize the rows a service supplies
- **Views** — thin: authentication, permissions and delegation only

Each app contains `models.py`, `serializers.py`, `views.py`, `urls.py`, `conftest.py`, `tests.py`, `admin.py`, plus `utils.py` and `service.py` when needed.

**A service is defined by responsibility, not size.** Reach for one when a cohesive use case spans several models and its policy — what to select, how to load it, what each result says, how results are grouped and ordered — would otherwise be spread as use-case-specific methods across a model or manager. A service is one concrete class named for the use case, in the owning app's `service.py`, constructed with its inputs and exposing a small public interface (`MyGamesService(user).current()`); everything else is private. It owns the whole operation, including any hydration only it needs and the order that hydration must run in, and it returns structured rows the serializer reads directly, never instances the serializer must call back into for policy. It reuses the queryset and manager methods that already exist rather than duplicating them. A paginated operation returns a lazily sliced sequence of rows with a `count()` method, so the view stays a plain `ListAPIView` and the service loads and hydrates only the page DRF slices. Do not add a base service class, a registry, or a generic per-model service, and do not move logic that naturally belongs on a model or manager into a service. A related operation joins its existing service when it is built, not before.

## Email bodies

Email HTML lives in `email_service/templates.py` as a function returning the rendered body. Serializers call the template and pass the result to `email_service.utils.send_email` — they never hold HTML literals.

The service sends email only in the authentication flow (verification and password reset). There is no email notification channel: player-facing notifications go out over push only, via `notification/registry.py`. Do not add an email transport to the notification pipeline without a product decision to turn it on.
