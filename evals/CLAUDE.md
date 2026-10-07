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
cd evals/web && npm run build && npm run lint && npm test
```

## The tool

A local web UI for viewing fixtures and runs and for labelling order sets. The API is the `workbench` app in this Django project and the frontend is `evals/web`; both run on your machine only.

```bash
cd evals && .venv/bin/python manage.py runserver 8001
cd evals/web && npm install && npm run dev   # http://localhost:5176
```

- **Labelling writes straight to the fixture file.** Review the diff and commit it like any other change.
- **The tool and `run_evals` cover one eval set**, named by `EVALS_EVAL_SET`. A fixture joins it through its `eval_sets` field; fixtures outside the set stay on disk for the tests and are not shown or run.
- **Runs are read from `evals/logs/`, never started from the UI.** Produce one with `python manage.py run_evals`; `--epochs N` calls the model N times per fixture in one run, so do not pass it unless the user asks for repeated runs. Only successful runs of the model task are listed: an errored run has nothing to judge, and a dumbbot run is the same every time.
- **The board shows the position and one order set, nothing else.** Whether a set is reasonable does not depend on how it resolved or on what the other nations ordered, so neither is drawn.
- **The tool has three views with one job each**: Fixtures curates the labelled order sets, Runs summarises a run and diffs its prompts, and the review queue labels a run's unseen order sets. Do not add a control to a view that serves another view's job.
- **A label is global to a fixture and an order set.** It lives in the fixture's `order_set_labels` with an optional `reason`, and counts in every run that produces that set. Do not store labels, verdicts or scores in logs.
- **Unreasonable means an order is wasted whatever the other nations do**: a self-bounce with nothing to defend, a support for a move nobody can contest, a support for a move that is not being made. A set that is strategically weak but wastes nothing is reasonable; say why it is weak in the `reason`. Strength is a separate measure, not part of this label.
- **An order set is identified by its content**: the same option ids in any order are the same set. Go through `select_orders/order_sets.py`; do not compare sets any other way.
- **An order set is named by its content, never by where it came from.** `select_orders/notation.py` renders the name from the variant's province ids and the fixture's units; do not hardcode a map or name a set after a run or an epoch.
- **A run's score is the share of its distinct order sets labelled reasonable**, per fixture and overall, computed when the run is viewed. A set produced in several epochs counts once, and an unlabelled set counts against the score until it is reviewed.
- **The review queue holds only unlabelled order sets.** Labelled sets are reported as a count.
- **Prompt diffs go through `evals/web/src/promptDiff.ts`**, which wraps jsdiff: paragraphs are matched line by line and changed ones are highlighted word by word.
- **The board renderer in `evals/web/src/board/` is a copy of the web app's.** Re-copy it to pick up changes; do not edit it in place or import the original.
- **Use the shadcn components in `evals/web/src/components/ui/` over raw HTML controls.** They are copies of the playground's; copy another one in when you need it.

## Harvesting fixtures

Two steps. The export is a read-only query against the app's Postgres; nothing else in `evals/` touches the app. Snapshots go in `evals/snapshots/`, which is gitignored; only the fixtures built from them are committed.

```bash
psql "<connection string>" -v ON_ERROR_STOP=1 -v games=<game id>,<game id> -At \
  -f evals/harvest/export.sql > evals/snapshots/<name>.json
cd evals && .venv/bin/python manage.py build_fixtures snapshots/<name>.json [--phase <id>] [--nation <name>]
```

Only completed phases in the classical variant are harvested. A phase whose replay disagrees with the stored game is skipped with the reason, and an existing fixture file is never overwritten, so its labels survive a re-harvest.
