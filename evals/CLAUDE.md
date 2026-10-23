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

A local web UI for viewing fixtures and runs, for labelling order sets and for reviewing games. The API is the `workbench` app in this Django project and the frontend is `evals/web`; both run on your machine only.

```bash
cd evals && .venv/bin/python manage.py runserver 8001
cd evals/web && npm install && npm run dev   # http://localhost:5176
```

- **To run it without a local Python, create a Codespace with the `evals` devcontainer** (`.devcontainer/evals/`). It installs both halves, starts them on attach and opens the UI. It runs no Docker and no database; keep it that way.
- **Labelling writes straight to the fixture file.** Review the diff and commit it like any other change.
- **The tool and `run_evals` cover one eval set**, named by `EVALS_EVAL_SET`. A fixture joins it through its `eval_sets` field; fixtures outside the set stay on disk for the tests and are not shown or run.
- **Runs are read from `evals/logs/`, never started from the UI.** Produce one with `python manage.py run_evals`; `--epochs N` calls the model N times per fixture in one run, so do not pass it unless the user asks for repeated runs. `evals/logs/` is committed, overriding the root `logs` ignore, so a run everyone should see is committed like a fixture change. Only successful runs of the model task are listed: an errored run has nothing to judge, and a dumbbot run is the same every time.
- **A hand-written prompt runs on one named fixture.** `render_prompt --fixture <id>` writes that fixture's current prompts to `evals/prompts/<id>/`, which is gitignored; edit them and pass `--system-file` and/or `--user-file` to `run_evals` with the same `--fixture`. A file replaces its whole message, so every legal option id must still appear in the user text, and the run refuses to start otherwise. Once a hand-written version wins, code it into `select_orders/prompt.py`.
- **A run's prompt is named by its content.** `run_evals` hashes the fixture ids and the exact messages sent, and names the hash `adjective-noun-month-day` after the day it was first run. A hash already in `evals/logs/` keeps its name. Both are written to the log's eval metadata; go through `select_orders/prompt_names.py`. The workbench reads the name from the log header, never the full log; a run from before names has none and shows as unknown.
- **`--prompt-name` names a run's prompt in advance**, so runs of one prompt variant on different fixtures share a name. A name then no longer identifies one prompt text: decide whether two runs sent the same prompt by their digests, never by their names.
- **A prompt variant is code, not a hand-edited file.** A variant is a function in `prompt_builder/` from a fixture's context to the whole user prompt, registered in `prompt_builder/variants.py`. `build_prompts` writes every variant for every fixture to `prompts/<fixture>/<variant>.txt` and refuses to overwrite a file that has been edited. `run_evals --user-variant <variant>` sends each fixture its own file, so one run covers the whole eval set. Variants are written for movement phases only. Builders reuse the baseline's sections through `user_sections` and `render_part` in `select_orders/prompt.py` rather than copying its templates.
- **The Fixtures and Runs boards show the position and one order set, nothing else.** Whether a set is reasonable does not depend on how it resolved or on what the other nations ordered, so neither is drawn.
- **A game board shows every nation's orders, each in its nation's colour, with failed orders drawn as failed and the units the phase dislodged.** A game is reviewed as a sequence of resolved phases, so how each phase resolved is the point. The multi-nation mapping is `evals/web/src/gameBoard.ts`; it feeds the renderer's `RenderState` and leaves the copied renderer alone.
- **The tool has four views with one job each**: Fixtures curates the labelled order sets, Runs summarises and compares runs and shows their prompts, the review queue labels a run's unseen order sets, and Games plays back and reviews game runs. Do not add a control to a view that serves another view's job.
- **A run's fixture page is part of Runs and is read-only.** It shows what that run produced on the fixture: each distinct order set with its current label, the epochs that produced it and their reasoning, and each failed answer with its problem and raw completion. Labels are changed in Fixtures or the review queue, never there.
- **A run's breakdown always adds up**: reasonable, unreasonable and unmarked answers sum to its answers minus its failed ones, which is the score's denominator. A failed answer is one that is not a legal order set; it counts towards no other metric.
- **A label is global to a fixture and an order set.** It lives in the fixture's `order_set_labels` with an optional `reason`, and counts in every run that produces that set. Do not store labels, verdicts or scores in logs.
- **Unreasonable means an order is wasted whatever the other nations do**: a self-bounce with nothing to defend, a support for a move nobody can contest, a support for a move that is not being made. A set that is strategically weak but wastes nothing is reasonable; say why it is weak in the `reason`. Strength is a separate measure, not part of this label.
- **An order set is identified by its content**: the same option ids in any order are the same set. Go through `select_orders/order_sets.py`; do not compare sets any other way.
- **An order set is named by its content, never by where it came from.** `select_orders/notation.py` renders the name from the variant's province ids and the fixture's units; do not hardcode a map or name a set after a run or an epoch.
- **A run's score is the share of its answers whose order set is labelled reasonable**, per fixture and overall, computed when runs are listed or viewed. A set produced in several epochs counts once per epoch, so a set picked 99 times outweighs one picked once, and an unlabelled set counts against the score until it is reviewed. The review queue still holds each distinct set once.
- **A score is always shown with its answer count and its 95% interval**, so a swing within the noise is not read as a win. The interval is Wilson's, over the score's denominator, and goes through `evals/web/src/stats.ts`. Ranking by score ranks by the interval's lower end.
- **Runs are compared only on the fixtures both cover.** The model and the fixture set vary between runs as well as the prompt, so the Runs list shows each run's own score and never a difference between rows. A comparison goes through `evals/web/src/runComparison.ts`, names how many fixtures it covers, says when the models differ, and is not made when the runs share no fixture.
- **A run's own prompt is always viewable.** Diffing it against another run is opt-in and never the only way to see it.
- **The workbench reads fixtures through a per-file cache that reparses a file whenever its content changes** (`_fixtures` in `workbench/views.py`), because schema validation dominates the cost of scoring every run on the list. The cached dicts are shared, so never mutate one; read the file afresh before writing it.
- **The review queue holds only unlabelled order sets.** Labelled sets are reported as a count.
- **Prompt diffs go through `evals/web/src/promptDiff.ts`**, which wraps jsdiff: paragraphs are matched line by line and changed ones are highlighted word by word.
- **The board renderer in `evals/web/src/board/` is a copy of the web app's.** Re-copy it to pick up changes; do not edit it in place or import the original.
- **Use the shadcn components in `evals/web/src/components/ui/` over raw HTML controls.** They are copies of the playground's; copy another one in when you need it.

## Games

The model plays one nation of the classical variant against six dumbbots from Spring 1901 to the start of the Fall 1905 Adjustment. The `games` app plays them and the workbench serves them to the Games view.

```bash
cd evals && .venv/bin/python manage.py play_games --nation England [--games N] [--first-seed 0] [--model ...]
cd evals && .venv/bin/python manage.py dumbbot_reference --nation England --seeds 100
```

- **Each game is billed, about 20 model calls.** `play_games` plays one game by default; do not raise `--games` or rerun it unless the user asks. A game run's log goes to `evals/logs/` and is committed like an order run; Games lists the successful ones, apart from order runs.
- **A game is one sample, its seed is its id.** The same seed gives byte-identical dumbbot play: each dumbbot nation's random stream is derived from the seed and the nation (`games/play.py`). Every game is paired with the all-dumbbot game on its seed, of which only the final centres are kept.
- **The model gets the unmodified `select_orders` prompt for each phase, stateless.** No history, no previous orders, no game-specific wording. Change the prompt in `select_orders/prompt.py`, never by forking it for games. A game run's prompt name hashes the nation and the prompts rendered on the opening board (`game_prompt_digest`).
- **A failed answer submits no orders and is not retried.** A model error, unparseable JSON or an unknown option id leaves the phase failed with its problem and raw completion; the units hold, an undirected retreat disbands and an adjustment falls back to civil disorder. Only the first order for a province is submitted.
- **Nobody is called for a phase with no legal option for them.** Such a phase is still resolved and recorded.
- **A game's score is derived when it is read**: 100 × own centres² over the sum of every nation's centres², and 100 to a soloist and 0 to everyone else. It comes from the final centres in the log through `games/scoring.py`, and is always shown with the raw centre count.
- **The dumbbot reference is a committed file per nation** in `evals/data/dumbbot_reference/`, written by `dumbbot_reference`. It assumes dumbbot and the adjudicator do not change, so it carries no source hash; regenerate it by hand if they do. The UI shows its mean and a 95% interval for the mean through `meanInterval` in `evals/web/src/stats.ts`.
- **Feedback lives in `evals/feedback/<run log>/<seed>.json`, never in logs.** One optional plain-text overall note and one per phase, keyed `1902-Fall-Movement` (`games/feedback.py`). The workbench reads the file afresh and writes one note at a time; an empty note is dropped and a file with no note left is deleted. Review the diff and commit it like a fixture change. A feedback file whose game no longer exists is shown as an error in the Games list.

## Harvesting fixtures

Two steps. The export is a read-only query against the app's Postgres; nothing else in `evals/` touches the app. Snapshots go in `evals/snapshots/`, which is gitignored; only the fixtures built from them are committed.

```bash
psql "<connection string>" -v ON_ERROR_STOP=1 -v games=<game id>,<game id> -At \
  -f evals/harvest/export.sql > evals/snapshots/<name>.json
cd evals && .venv/bin/python manage.py build_fixtures snapshots/<name>.json [--phase <id>] [--nation <name>]
```

Only completed phases in the classical variant are harvested. A phase whose replay disagrees with the stored game is skipped with the reason, and an existing fixture file is never overwritten, so its labels survive a re-harvest.
