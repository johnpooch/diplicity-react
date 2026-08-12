---
paths:
  - "service/**/tests.py"
  - "service/**/tests/*.py"
  - "service/**/conftest.py"
---

# Tests

## Keep an app's tests in one `tests.py`

Do not split an app across modules like `tests_emit.py` or `tests_permissions.py`.

## Name tests for the capability under test

Name the behaviour the API guarantees, not what the test body does.

**Good:** `test_admin_can_add_bot`, `test_update_user_profile_name_too_short`

**Bad:** `test_posting_to_add_bot_returns_201_and_creates_member`

## Drive behaviour through the HTTP API

Call endpoints and assert on the response. Treat view, serializer, and manager internals as implementation details.

**Good:** `POST` to add a bot, then assert status and that the member appears on a subsequent `GET`

**Bad:** Call `BotMemberCreateView` directly, or assert `Member.objects.filter(...).exists()` without going through the API

## One test class per view

Name it `Test<ViewName>`. A cross-cutting concern — ordering, character limits, permission variants, mode-specific rules — belongs in the test class of the view that exposes it, not in a class of its own. There are no test classes for models, managers, or querysets: if behaviour cannot be observed through an endpoint, either it is dead or the endpoint is missing.

## Prefer shared fixtures over inline setup

Put reusable state in the root `service/conftest.py` — check there first, it already holds the users, clients, factories, and scenario fixtures. An app-local `conftest.py` is for fixtures genuinely specific to that app. Create state inline only when it is specific to that one test.

## Use `reverse()` and the shared client fixtures

Build URLs from the URL name, never a hardcoded path string — hardcoded paths are what make renaming a view expensive. Authenticate with `authenticated_client` / `authenticated_client_factory`; do not hand-roll JWT credentials in a test helper.

## Cover the interesting edges, not just the happy path

For a write endpoint (or any capability with branching behaviour), do not stop at a single success case. Walk the axes that change the outcome:

- **Variants of the domain** — each mode or configuration that alters behaviour
- **Side effects** — who is affected, what is created, what stays unchanged; assert the absence of effects when none should fire
- **Auth and permissions** — unauthenticated, outsider, and every distinct forbidden role
- **Validation** — empty, whitespace-only, over-limit, and other boundary inputs
- **Missing resources** — nonexistent IDs → 404
- **Domain gates** — statuses or modes that forbid the action

One focused test per edge. Name each for the guarantee it pins down.
