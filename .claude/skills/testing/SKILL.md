---
name: testing
description: Testing guidance for diplicity-react — running frontend Vitest and backend pytest, MSW mocks, and frontend test patterns. Use when writing or running tests, setting up fixtures, or reviewing test code.
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

Backend test conventions (factories, naming, what to assert) are in `.claude/rules/backend.md`.
