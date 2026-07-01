---
name: testing
description: Testing guidance for diplicity-react — frontend Vitest and backend pytest patterns, fixtures, conftest organisation, MSW mocks, and performance tips. Use when writing or running tests, setting up fixtures, or reviewing test code.
allowed-tools: Bash, Read, Glob, Grep, Write, Edit
---

# Testing

## Frontend

```bash
cd packages/web
npm run test                # all tests
npm run test <filename>     # single file (preferred — faster feedback)
```

## Backend

```bash
# Single file (preferred)
docker compose run --rm service python3 -m pytest service/game/tests/test_game_create.py -v

# Single function
docker compose run --rm service python3 -m pytest service/game/tests/test_game_create.py::test_create_game_success -v

# Single method of a class
docker compose run --rm service python3 -m pytest service/game/tests/test_game_create.py::TestClass::test_method -v

# Full suite (use -n auto for parallel)
docker compose run --rm service python3 -m pytest -n auto -v
```

In native (non-Docker) cloud sessions:
```bash
cd service
python -m pytest game/tests/test_game_create.py -v    # single file
python -m pytest -n auto --reuse-db                   # full suite, reuse DB
python -m pytest -q --create-db                       # rebuild test DB (after new migrations)
```

**SQLite is not viable.** Some migrations use Postgres-only SQL. Always use the native PostgreSQL cluster.

## Backend Testing Patterns

### Where fixtures live

Shared fixtures → **root `service/conftest.py`** — check here before adding anywhere else.

Per-app `conftest.py` files exist only for genuinely app-local fixtures:
- `login/conftest.py` — Google/Apple auth and token mocks
- `integration/conftest.py` — autouse procrastinate mock + extra users/clients for 7-player games
- `nation/conftest.py` — draft variants and flag SVG data
- `variant/conftest.py` — SVG map builders (`make_dsvg`, `make_godip_svg`, etc.)

### Fixture naming conventions

- **`*_factory`** — returns a callable that creates objects on demand. Always use this suffix for callable-returning fixtures; never `make_*` or bare names.
- **Session-scoped reference data** — read-only lookups: `<variant_id>_variant`, `<variant_id>_<name>_nation`, `<variant_id>_<name>_province` (e.g. `classical_england_nation`). Created once per session — never mutate in tests.
- **Session-scoped users/clients** — `primary_user`, `secondary_user`, `tertiary_user` and matching authenticated clients. Never mutate or delete; use `user_factory` for disposable users.
- **Scenario fixtures** — descriptive nouns returning ready-made objects (`active_game_with_phase_state`, `game_with_two_members`).
- **`mock_*`** — patch fixtures (`mock_send_notification_to_users`, `mock_immediate_on_commit`).

### Performance

- Root conftest forces `MD5PasswordHasher` — `create_user` is cheap; do not use the production hasher in tests.
- Use `pytest --reuse-db` locally to skip recreating the database (~6s) between runs. Pass `--create-db` after pulling new migrations.
- Full suite is parallel-safe: `pytest -n auto`. Each worker gets its own database (`test_diplicity_gwN`). CI runs with `-n auto`. Not in `addopts` so single-file runs skip worker startup cost.
- No test uses `django_db(transaction=True)` — use `mock_immediate_on_commit` instead.

### What good tests look like

- Test API endpoints, not model methods directly
- Assert on response status codes AND response body
- Include permission tests for endpoints with access control
- Assert on observable outcomes (HTTP responses, rendered text), not internal state
- Factory fixtures in `conftest.py`, not in the test file

**Review check:** tests hit API endpoints (not internal methods)? status code AND body asserted? permissions covered? fixtures follow naming conventions and live in `conftest.py`?
