# CLAUDE.md — evals/

`evals/` is where the AI player's order evals are developed. It is deliberately cut off from the rest of the repo so it can change fast: it runs locally only, is not deployed and has no CI. Its plan is `evals/plan.md`.

The root `CLAUDE.md` applies here as everywhere else. This file adds the boundary rules.

## Boundary

- **Nothing outside `evals/` imports from it.** Production never depends on it. The live bot still runs on `service/harness`; `evals/` started from a copy of that code and diverges freely. Do not edit `service/harness` for eval work.
- **From `service/`, `evals/` imports only `adjudicator` and `dumbbot`, read-only.** `service/` is on its import path, so an `evals/` package must never reuse a `service/` package name. `evals/config/tests.py` enforces both.
- **Stubs sit on the `evals/` side.** Where it would need the running app, its database or the agent, it uses fixture files or hard-coded data instead. Never stub or edit production code to serve it.
- **Its frontend never imports from `packages/`.** Copy what it needs.

## Setup

`evals/` has its own virtualenv and no database:

```bash
python3.12 -m venv evals/.venv
evals/.venv/bin/pip install -r evals/requirements.txt -r evals/dev_requirements.txt
cd evals && .venv/bin/python -m pytest
```

## Harvesting fixtures

Two steps. The export is a read-only query against the app's Postgres; nothing else in `evals/` touches the app. Snapshots go in `evals/snapshots/`, which is gitignored; only the fixtures built from them are committed.

```bash
psql "<connection string>" -v ON_ERROR_STOP=1 -v games=<game id>,<game id> -At \
  -f evals/harvest/export.sql > evals/snapshots/<name>.json
cd evals && .venv/bin/python manage.py build_fixtures snapshots/<name>.json [--phase <id>] [--nation <name>]
```

Only completed phases in the classical variant are harvested. A phase whose replay disagrees with the stored game is skipped with the reason, and an existing fixture file is never overwritten, so its labels survive a re-harvest.
