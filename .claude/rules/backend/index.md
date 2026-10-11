---
paths:
  - "service/**/*.py"
---

# Backend conventions (`service/`)

- **No docstrings or comments:** including in tests. Do not annotate assertions to explain their values; when a query-count assertion changes, update the number only. **The one exception is DRF view docstrings**, which are extracted into the OpenAPI schema — write those.

- **Imports go at module top level:** No inline `import` inside a function or method body, even if you find an existing one nearby to copy. The only exception is breaking a genuine circular import — call it out in the PR description when you use it. Do not assume a circular import exists; resolve one only when it actually appears. For circular imports at module level, use `apps.get_model()`.

## Where logic lives

- **Models** — domain facts about one row, as properties (e.g. `Member.departure` and its precedence)
- **QuerySets and managers** — reusable queries, prefetch strategies and hydration shared by more than one caller, and complex creation and modification logic (e.g. `Game.objects.create_from_template()`)
- **Services** — a use case whose orchestration and policy do not naturally belong to one model (see below)
- **Serializers** — declare the wire contract; orchestrate manager calls, handle request-specific logic and validation, or serialize the rows a service supplies
- **Views** — thin: authentication, permissions and delegation only

Each app contains `models.py`, `serializers.py`, `views.py`, `urls.py`, `conftest.py`, `tests.py`, `admin.py`, plus `utils.py` and `service.py` when needed.

**A service is defined by responsibility, not size.** Reach for one when a cohesive use case spans several models and its policy — what to select, how to load it, what each result says, how results are grouped and ordered — would otherwise be spread as use-case-specific methods across a model or manager. A service is one concrete class named for the use case, in the owning app's `service.py`, constructed with its inputs and exposing a small public interface (`MyGamesService(user).current()`); everything else is private. It owns the whole operation, including any hydration only it needs and the order that hydration must run in, and it returns structured rows the serializer reads directly, never instances the serializer must call back into for policy. It reuses the queryset and manager methods that already exist rather than duplicating them. Do not add a base service class, a registry, or a generic per-model service, and do not move logic that naturally belongs on a model or manager into a service. A related operation joins its existing service when it is built, not before.

**Views and serializers live in the app that owns the model being acted on.** Creating a `Member` belongs in `member`, even if the seated user is a bot. Do not put create/list HTTP for one model inside another app because the trigger was a feature of that other app.

**URL routes belong in the owning app's `urls.py`**, even when the path nests under another resource's prefix (e.g. `/variants/<id>/nations/<id>/flag/` lives in `nation/urls.py`). The parent app may `include()` those urlpatterns to preserve the public path structure.

**Do not create a Django app for a 1:1 extension of an existing entity.** Extra fields on a user belong on `UserProfile`, not a parallel `BotProfile`-style sidecar app.

## Notification copy

**Notification copy follows a written style guide.** Read `notification-copy.md` before adding a spec to `service/notification/registry.py` or changing the copy in an existing one — title, tense, person, actor naming and links are settled there, not per spec.

## Error reporting

**`logger.error` is a Sentry error event.** The Sentry logging integration turns every ERROR record into an event against a small monthly quota, so reserve it for failures someone must act on. Log expected outcomes (a stale push token, a missing upload) at `warning` or below.

**Log with `%`-style arguments, never f-strings.** Sentry groups log events by the unformatted message template; interpolating counts or names into the string splits one problem into many issues.

**Trace sampling lives in `project/sentry.py`.** An endpoint the client polls on an interval belongs in its polled paths; a health or asset endpoint belongs in its untraced paths.

**Honeycomb sampling is decided by trace ID, identically on both sides.** `DeterministicSampler` in `project/otel_config.py` and `deterministicSampler` in `packages/web/src/observability.ts` keep a trace when the low 64 bits of its ID are divisible by `TRACE_SAMPLE_RATE`, so the web client and API keep the same traces without trusting the client's sampled flag. Change the rate or rule in both files together, and keep the `SampleRate` attribute on every kept span — Honeycomb multiplies counts by it.
