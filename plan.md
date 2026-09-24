# AI player evals: the order side

Implementation plan. Nothing here is built yet.

Source material: discussion [#1368 "AI player evals"](https://github.com/johnpooch/diplicity-react/discussions/1368),
a call with John, a design session on 22-23 September 2026, and voice notes from
23 September 2026 that moved the work into its own space in the repo. Where this
plan contradicts #1368, this plan is later and wins.

---

## 1. Goal

Build the data and the tooling needed to tell whether the AI player's order
selection is any good, and to make prompt iteration produce a trustworthy
signal rather than vibes.

The binding constraint is human labels. Everything downstream (scorers, answer
keys, judges) needs positions that a human has judged, and only a human can
produce those. So the first deliverable is not a metric, it is a tool that makes
labelling fast, plus the fixtures to label.

The second constraint is **iteration speed**. For at least the next few weeks the
loop is: change something, run the evals locally, look, repeat. Everything in this
plan is judged by how short it makes that loop. That is why the work lives in its
own space, cut off from the app (D16).

### In scope

- A new top-level **`evals/`** folder: a self-contained Django service plus its own
  frontend, deliberately decoupled from `service/` and `packages/` (D16).
- A **local tool** for order fixtures: board view, legal option list, run the
  model, see consequences, label options.
- **Prompt iteration inside that tool**: every part of the prompt is editable,
  the system prompt and the user prompt alike, including how the board is
  described (D13). Re-run against the loaded fixture and see straight away what
  the orders became and what they cost.
- **Running the whole eval suite from the tool**, with per-fixture, per-scorer
  results beside the human labels, so the evals themselves can be judged, not
  just the model (D20).
- **Eval-set curation**: mark a fixture as belonging to a named eval set, or
  discard it as unsuitable, from inside the tool.
- A **harvester** that turns real Diplicity phases into self-contained fixtures,
  without importing app code.
- **Fixture schema v2**, including what the real players actually ordered.
- A **one-phase counterfactual**: swap the model's order set in against the
  other nations' archived orders and measure what changes.
- **Zero-token dumbbot rollouts** to show board-level consequences a game-year out.
- **Per-option human labels** written back into the fixture, as the answer key
  future scorers will use.

### Explicitly out of scope

Do not build these as part of this plan. Each was considered and deferred.

- **Any change to code under `service/` or `packages/`.** Production keeps
  running on `service/harness` exactly as it is today (D17). The only file
  outside `evals/` this plan edits is root `CLAUDE.md`.
- **Reconnecting `evals/` to production.** Porting a better prompt back into
  `service/harness` is a later, separate piece of work.
- **Everything on the message side.** Message quality rubrics, the should-reply
  decision, prompt-injection and jailbreak fixtures, LLM-judge calibration.
  Parked by decision, see D11.
- **Order consistency with respect to reasoning** as an LLM judge. Deferred.
- **Persisting eval runs across sessions, and any long-lived dashboard.** Issue
  [#1142](https://github.com/johnpooch/diplicity-react/issues/1142) posed this
  and was closed as not planned. Suite results live in memory for the session
  (D20).
- **Deploying the tool.** Local only, see D5.
- **The dumbbot match protocol.** Settled in
  [#1126](https://github.com/johnpooch/diplicity-react/issues/1126). Do not
  redefine it.
- **Changing dumbbot or the adjudicator.** Both are used as they are (D18).
- **New inspect scorers.** This plan produces the labelled data a scorer would
  need. Writing scorers before labels exist leaves them idle.
- **Chat history in the `select_orders` context.** Moves and messages stay
  separate for now, see D11.

---

## 2. What exists today

Read these before changing anything.

- `service/harness/tasks/select_orders/evals.py` is the only inspect `Task` in
  the repo. Seven scorers over `dataset.json`.
- `service/harness/tasks/select_orders/dataset.json` holds 10 fixtures. They are
  hand-built toy positions, not harvested. One has a single legal option. Only 4
  carry `ranked_options`, which is why `quality_strong` and `quality_avoidance`
  report stderr of 0.14 and 0.24 in `EVAL_RESULTS.md`.
- **Production depends on `service/harness`.** `service/agent/orchestration.py:5-7`
  imports `harness.adapter`, `harness.tasks` and `dumbbot.policy` to build the live
  bot's prompts and orders, and `agent/tasks.py`, `agent/fallback.py`,
  `agent/context.py` and `agent/orders.py` import harness types. This is why the
  eval work cannot iterate inside `service/harness` without every change touching
  the live bot.
- `service/dumbbot/` holds a heuristic policy that plays legal Diplomacy for
  zero tokens (`service/dumbbot/EVAL_RESULTS.md`). It currently beats the LLM on
  every scorer, five of them trivially because it picks from the engine's own
  option enumeration and so cannot emit an illegal order.
- `service/adjudicator/` is the Diplomacy rules engine. It is pure and Django-free.
  Its public facade is `adjudicate(variant, game_state)`
  (`service/adjudicator/__init__.py:16`), which resolves a phase, and
  `service/adjudicator/options.py:47` exposes `get_options(state)`, which lists
  every legal order.
- `service/agent/management/commands/dump_phase.py` is the existing harvester. It
  only emits fixtures for a game's *current* phase
  (`service/agent/management/commands/dump_phase.py:94`) and needs the app's
  Django models. `evals/` does not use it (task 1.4).
- `packages/design-playground/` is a prototyping app. Not suitable for this
  tool, see R1. Its boundary section in root `CLAUDE.md` is the model for the
  `evals/` one.

---

## 3. Measured facts

Measured on 2026-09-23 against the classical variant in a local dev container.
Reproduce with `DJANGO_DEBUG=True service/.venv/bin/python manage.py shell`.

| Quantity | Value |
|---|---|
| `get_options` on a full board | 35 ms |
| `Engine().adjudicate` on a full board | 0.66 ms |
| Legal order sets, Spring 1901, Turkey (3 units) | 693 |
| Legal order sets, Spring 1901, Russia (4 units) | 9,216 |
| Legal options, constructed 6-unit midgame position | 133 |
| Legal order sets, that same position | 105,257,880 |

Consequences that shaped the design:

- Option enumeration costs about fifty times adjudication and dominates rollout
  cost. Budget roughly **40 ms per rollout phase**.
- The space of order sets is far too large for exact-set matching against a
  handful of hand-authored "reasonable" sets. Labelling is **per option**.
- Option enumeration is **per unit and unconditional**. Legality depends on where
  units physically stand, not on what other units are ordered. Convoy
  enumeration falls back to `convoy_path_exists` over physical fleet positions
  and deliberately does not depend on submitted convoys
  (`service/adjudicator/options.py:8`). This is why per-unit counts multiply
  cleanly, and why `support_coherence` and `convoy_coherence` exist at all: the
  option list cannot rule out legal-but-incoherent combinations.

### Legal by construction

The game API returns every legal order for the phase and the player picks from
that list, so an illegal order cannot be submitted. The bot works the same way:
the model is shown the list and answers with a reference into it
(`service/harness/tasks/select_orders/parser.py:20`). So the `legality` scorer
(0.993 today) does not measure Diplomacy knowledge. It measures whether the
model's answer mapped cleanly back onto the list. Read it as a format check, and
do not spend prompt effort chasing it.

### The supply-centre timing constraint

**Supply-centre ownership cannot change within a single phase.** Ownership is
recomputed only when the *next* phase is an Adjustment phase; otherwise current
ownership is carried through unchanged
(`service/adjudicator/engine.py:1143`). In the classical progression, Adjustment
follows Fall **Retreat**, not Fall Movement.

So a one-phase counterfactual always reports a supply-centre delta of zero,
whether the phase is Spring or Fall. Ownership moves once per game-year. This is
why the counterfactual measures occupancy and the rollout measures centres, and
why the rollout horizon is counted in game-years.

---

## 4. Key decisions

**D1. The UI has three jobs: labelling, prompt iteration, and judging the evals.**
Human labels are important to many downstream metrics, so labelling throughput
is one thing to optimise. The second is the loop someone actually runs when
improving the bot: edit the prompt, run it against a known position, see what
the orders became and what they cost on the board. Today that loop means editing
Python, running an inspect eval and reading aggregate scores, which is far too
slow to iterate against. The third is seeing whether the scorers themselves are
right (D20). A read-only inspection view serves none of these.

**D2. Label per option, three-way: reasonable / unreasonable / unlabelled.**
Forced by the combinatorics in section 3. Three-way rather than binary because
"unlabelled" is the honest state for most of a 30-option list, and forcing a
call on every option produces worse labels. The labeller must be able to label
options the model did *not* pick, which falls out of labelling over the full
legal list.

A label may cover a **tuple** of options, not only a single one. Some orders are
reasonable only in combination: a support is worth nothing unless the supported
move is also ordered. A tuple label is satisfied only when every option in it is
present in the order set. Singletons are the common case and tuples the
exception, which keeps labelling cheap while capturing the coupling that pure
per-option labelling would otherwise lose. This is the narrow, affordable part of
what full order-set labelling would have given us (R2).

**D3. Select from the option list, render on the board.** Authoring orders by
clicking provinces needs the interactive map (pan, zoom, hit-testing), which is
roughly 3,500 lines nobody wants a second copy of. Selecting from the list and
drawing the result on a board is cheap and is how judgement actually happens:
nobody can evaluate `Support Munich -> Silesia` as a string. Render the board
once and overlay arrows as SVG in the browser; do not round-trip to a PNG
renderer per click.

**D4. Order-set level machine measurement, order level human attribution.**
The machine resolves a whole order set and reports what changed. The human then
attributes that outcome to individual orders. Machines are bad at attribution
here and humans are bad at simulation, so each does what it is good at.

**D5. Local only.** `evals/` runs on a laptop and writes fixture JSON straight to
disk. This removes staff authentication, deployment, and the "how does a deployed
app write to git" problem in one move, and keeps the privacy question away from
the order work entirely. Deploy later only if it earns it.

**D6. Fixtures are self-contained JSON files committed to the repo.** They carry
their own variant id, phase, units, supply centres and full legal option list,
so the eval does not need a database at rest. This also delivers what John asked
for, a Diplomacy eval rather than a Diplicity-specific one: the portable
contract is the fixture schema plus `adjudicate()`, and only the harvester
touches Diplicity data.

**D7. Fixtures carry no user identifiers.** The current builder records nation
names only (`service/harness/adapter.py:214`). Preserve that deliberately: this
repository is public and fixtures will be committed to it. A source game id as
provenance is fine, user ids are not.

**D8. Rollout horizon is counted in game-years, not phases.** Default 1 game-year,
meaning roll forward until the next Adjustment has resolved. Forced by the
supply-centre timing constraint: a fixed 3-phase horizon stops one short of
Adjustment from a Spring position and overshoots from a Fall one. Counting in
game-years makes the supply-centre delta always defined and comparable across
fixtures.

**D9. Paired seeds across all candidate order sets.** The model's set, the human's
set and dumbbot's set are rolled out over the *same* seed list. Diplomacy
rollouts are high variance and the position dominates the outcome, so comparing
independent samples at 30 seeds mostly measures noise. Common random numbers
cancel the shared randomness. This is the difference between 30 seeds being
useful and 30 seeds being decorative.

**D10. Rollouts are a labelling aid, never a metric.** They are never a number
anyone tunes a prompt against. The value they measure is value against a weak
continuation, so optimising it would mean optimising against dumbbot's blind
spots. Their job is to stop the labeller staring at 133 options with no prior.

**D11. Moves and messages stay separate.** Consequence: the `select_orders`
prompt keeps no chat history for now, and the full-press move-quality eval stays
parked. Side benefit: the privacy policy gap (section 8) only binds on player
messages, so it gates nothing in this plan.

**D12. `option_labels` is the source of truth; `ranked_options` is derived.**
The existing `quality_strong` and `quality_avoidance` scorers read
`ranked_options` good/bad lists
(`service/harness/tasks/select_orders/scorers/quality.py:7`). In the `evals/`
copy of those scorers, derive that shape from `option_labels` at load time so
they keep working unchanged instead of being rewritten before there is data to
justify it.

**D13. Every part of the prompt is editable, so options are addressed by id.**
This reverses the earlier decision to keep the user prompt read-only. The board
description is very likely one of the more important parts of the prompt, and
nobody knows whether the current one is any good, so it must be as easy to change
as the strategy guidance. Reshaping it is encouraged: for example, dropping
provinces no unit can reach this phase, or grouping the board around the eval
nation's units, if that works better and can be built from data the fixture
already carries (D19).

What blocked this before is that the model answers with an `option_index`, a
position in the rendered per-province list
(`service/harness/tasks/select_orders/parser.py:20`). Any edit that reorders or
trims the list silently changes what an index means, and an out-of-range index is
skipped rather than raised (`service/harness/tasks/select_orders/parser.py:24`),
so a desync shows up as a missing order rather than an error.

So in `evals/`, options get a **stable id derived from their own content**
(source, order type, target, aux, unit type, named coast). An unknown id is
rejected exactly as an out-of-range index is today, so illegal orders stay
unrepresentable and the "legal by construction" property (section 3) holds,
while the rendered list can be reordered, trimmed or reformatted freely. The
parser rejects an unknown id loudly instead of skipping it. The cost is that
`evals/` numbers are not comparable with the `option_index` numbers in the
existing `EVAL_RESULTS.md`; that is accepted, since `evals/` re-baselines anyway
(task 4.2).

The prompt is therefore assembled from named parts, each editable in the tool:
the system blocks (`ROLE`, `PRINCIPLES`, the phase task instruction, `FORMAT`)
and the user prompt sections (players, board, units, supply centres, options).
Each user prompt section can have more than one renderer, and the tool lets you
pick between them. `FORMAT` stays editable but is marked as parser-coupled,
because it specifies the JSON shape the parser expects.

**D14. Baselines are precomputed at harvest, keyed by the settings they used.**
The human's order set and dumbbot's pick are properties of the fixture. Neither
depends on the model or on the prompt being iterated, so both rollouts are
computed once at harvest, stored in the fixture, and read for free thereafter.
Only the model's own rollout runs live.

A baseline is only valid against a model run that used the **same horizon and the
same seeds**, so a stored baseline is keyed by both and a mismatch invalidates it
rather than silently comparing unlike things. Two mechanisms keep that from
becoming a straitjacket:

- **Precompute every offered horizon.** The UI offers 1 and 2 game-years, so both
  are computed at harvest. A horizon nobody precomputed is computed on demand and
  cached into the fixture.
- **Use a canonical, nested seed list.** Seeds are `0..N-1` in order, so the first
  30 seeds of a 100-seed run are exactly the 30-seed run. Precompute baselines
  deep (100 seeds), and any live model run at `m <= 100` seeds compares against
  the first `m` baseline seeds and stays a valid paired comparison. Seed count
  then becomes a slider that trades precision against wait, with no
  recomputation.

**D15. The seed count is measured, not guessed.** Nobody knows what number is
enough, and it is an empirical question with a cheap answer: with baselines
precomputed to 100 seeds, plot the standard error of the paired difference
against seed count on the first real fixtures and read the default off the curve.
Until that is done, treat 30 as a placeholder rather than a decision. The number
that matters is not the seed count but whether the interval around a difference
is narrow enough to separate two order sets; the UI should show that interval
rather than a bare mean, so a difference that 30 seeds cannot resolve is visibly
unresolved.

**D16. `evals/` is a separate space, deliberately cut off from the app.**
A new top-level folder holding its own Django project and its own frontend. It
shares the repository only so that it can read real data and borrow from the
existing UI. The dependency rules:

- Nothing outside `evals/` imports from `evals/`. Production never learns it
  exists.
- `evals/` may import **read-only** from `service/adjudicator/` and
  `service/dumbbot/`, which are pure, Django-free Python (D18). It imports nothing
  else from `service/`: no Django apps, no models, no settings, no `agent`.
- The `evals/` frontend never imports from `packages/web` or
  `packages/design-playground`. It copies what it needs (the board SVG, arrow
  drawing).
- `evals/` starts from a **copy** of the `select_orders` code in
  `service/harness` (prompts, parser, scorers, options helpers, dataset) and then
  diverges freely.

The reason is speed. Iterating inside `service/harness` means every prompt or
scorer change is also a change to what the live bot does (section 2), so each PR
has to reason about production. Cutting the connection removes that, and makes
reconnecting later a deliberate port rather than a constant tax.

Python packages inside `evals/` must not reuse the names of packages it imports
from `service/` (`adjudicator`, `dumbbot`, `harness`, `common`), or imports will
resolve to the wrong one.

**D17. Stubs sit on the `evals/` side; production is untouched.** Wherever
`evals/` would otherwise need a live connection to the app (a running game, the
app's database, the agent), it uses fixture files or hard-coded data instead.
Nothing under `service/` or `packages/` is edited, stubbed or disabled, and the
production bot keeps running on `service/harness` exactly as it does today.

**D18. The adjudicator and dumbbot are imported, not copied.** `evals/` needs the
adjudicator to list legal options for harvested phases, to replay the
counterfactual, and to run rollouts, and needs dumbbot to play every seat in a
rollout. Neither will be changed as part of this work, and both are Django-free:
their imports are the standard library, `yaml`, `jsonschema`, and
`common/constants.py`, which itself only imports `adjudicator.types`. Dumbbot also
imports types and helpers from `service/harness` (`harness.types`,
`harness.utils`, `harness.exceptions`), which are plain Python. Importing them
read-only keeps a single engine and avoids a roughly 6,000-line copy drifting from the
one production uses. If one of them does need changing for eval purposes later,
copy it into `evals/` at that point.

**D19. Reshape the data however works best.** The fixture is raw material, not a
prompt. Any structure that helps the model or the labeller and can be built from
data the fixture already carries, or from the variant, is fair game: pruning
unreachable provinces, per-unit neighbourhoods, a different board encoding. These
live as prompt renderers (D13) so they can be compared on the same fixtures
rather than argued about.

**D20. The tool shows whether the evals are right, not only the model.**
Running the full suite from the tool shows, per fixture, every scorer's verdict
and explanation next to the human labels and the model's orders. A scorer that
disagrees with the labels, or passes an order set a human would reject, is then
visible at a glance. Results live in memory for the session; nothing is persisted
across sessions (see out of scope).

---

## 5. Rejected alternatives

**R1. Build the UI in `packages/design-playground`.** Proposed in #1368, rejected.
That package's own `CLAUDE.md` overrides the root one and forbids nearly
everything this tool needs: "no backend, no API client, no authentication and no
real data", "no MSW, no react-query, no generated OpenAPI types, and no network
layer. Do not add them", "Never rebuild the interactive map", "No tests. This
code is disposable", and prototypes get deleted once a decision lands. This tool
is durable, has a backend, and reads real data. It does not belong there.

**R2. Exact order-set matching against hand-authored "reasonable" sets.**
Rejected on the numbers in section 3. Against roughly 10^8 legal sets, exact
matching reads zero almost always and teaches nothing.

**R3. Per-order marginal rollouts.** The idea was to fix one order, let dumbbot
fill the remaining units, and read off that order's marginal value. Rejected
because order quality is tightly coupled within a set: a support only has value
if the supported move is also ordered, so fixing a support while something else
fills the rest makes good orders look worthless. Signal to noise is too poor.
Replaced by D4.

**R4. Supply-centre delta from a one-phase counterfactual.** Impossible, see the
timing constraint in section 3. It is always zero.

**R5. Win rate as the rollout statistic.** At a one-game-year horizon nobody has
won, so it is undefined. Over a full game against dumbbot it is almost entirely
variance. Use supply-centre delta and units lost, as a paired distribution.

**R6. Reporting a rollout without a baseline.** The position dominates the
outcome, so in a winning position every order rolls out well, and an absolute
distribution mostly describes the position rather than the orders. The first fix
proposed was a UI toggle trading the baselines away for speed, which would have
meant sometimes showing exactly the number this rejects. D14 removes the trade
rather than the principle: baselines are precomputed at harvest, so they cost
nothing at default settings and are always available. A toggle survives only as a
way to hide them on screen, never as a way to avoid computing them.

**R7. Relying on the existing dumbbot match for per-move signal.** The match
(`service/integration/test_dumbbot_match.py`, results in
`service/integration/MATCH_RESULTS.md`) measures a whole policy over a whole
game and cannot attribute the outcome to any single decision. Archive replay
gives only one phase of consequence, because the moment the model's orders are
substituted the real game diverges and every later archived order was
conditioned on a board that no longer exists. Neither gives "what did this order
set cost me a game-year later". Rollouts do.

**R8. Build the tool inside `service/`.** The first version of this plan added a
DEBUG-gated Django app to `service/`, extended `service/harness` in place and
taught `dump_phase` to read historical phases. Rejected because
`service/harness` is what the production bot runs on (section 2), so every
experiment would also be a production change. Replaced by D16.

**R9. Stub the production agent's side.** Considered as a way to cut the
connection: replace the agent's calls into `service/harness` with stubs that
return hard-coded data. Rejected because it would edit production code and make
the live bot play hard-coded orders. The stubs go on the `evals/` side instead
(D17).

**R10. Copy the adjudicator into `evals/`.** Rejected for now: roughly 6,000 lines
of engine that nobody intends to change, which would silently drift from the
engine production uses. See D18 for when this flips.

---

## 6. Fixture schema v2

One JSON file per fixture, at `evals/fixtures/<id>.json`, one file per fixture
rather than a single `dataset.json`, so label changes produce readable diffs.

Existing fields, keep as they are: `id`, `variant`, `nation`, `phase`
(`season`, `year`, `type`), `units`, `supply_centers`, `order_options`,
`max_orders` (optional), `notes`.

New fields:

- `schema_version`: `2`.
- `provenance`: `{ source: "harvested" | "handbuilt", game_id, phase_id,
  phase_ordinal, harvested_at, press_type }`. The existing 10 fixtures are
  `handbuilt` and behave nothing like harvested positions, so the distinction
  must be explicit rather than implied.
- `actual_orders`: the real order set **for every nation** in the phase, not just
  the eval nation. Without the other six, counterfactual re-adjudication is
  impossible. This is the single most important addition.
- `actual_outcome`: which orders succeeded or failed, and the resulting units and
  supply centres.
- `option_labels`: list of `{ options, label: "reasonable" | "unreasonable",
  labeller, labelled_at, note }`. `options` is a list of option ids (D13): one
  entry in the ordinary case, several when the judgement holds only for a
  combination (D2). Absence of an entry means unlabelled.
- `baselines`: the precomputed human and dumbbot rollout results (D14), keyed by
  horizon and seed list, keeping the per-seed results rather than only a summary,
  so a run at fewer seeds compares against a prefix of a deeper baseline.
- `eval_sets`: list of named eval sets this fixture belongs to. Empty by default.
  A harvested fixture starts in none: harvesting is cheap and deciding a position
  is worth evaluating against is a judgement, so they must be separate actions.
- `discarded`: `{ by, at, reason }`, or absent. A fixture judged unsuitable is
  marked rather than deleted, so the same position is not re-harvested and
  re-judged later.
- `decision_richness`: integer, the product of per-unit option counts for the
  eval nation. Free to compute while enumerating, and useful for sorting
  candidate positions by how much was actually at stake.

There is deliberately no `split` field. A dev/test split is just two eval sets
named for the purpose, so `eval_sets` already expresses it. See Q5.

---

## 7. Metrics

### One-phase counterfactual

Swap the eval nation's candidate order set in, hold the other six nations'
`actual_orders` fixed, adjudicate once. Report:

- units dislodged, own and enemy
- units lost outright (dislodged with no legal retreat)
- moves succeeded over moves attempted
- provinces taken, held, given up
- **occupancy** delta on supply-centre provinces

Do **not** report supply-centre ownership delta here. It is always zero. Occupancy
of supply-centre provinces is the leading indicator: occupying Munich in Fall is
what makes you own it at the following Adjustment.

### Rollout

- **Phase 0**: the candidate order set against the other nations' `actual_orders`.
  Not dumbbot. This keeps the first step grounded in reality and makes the
  one-phase counterfactual the zero-game-year case of the same code path rather
  than a second implementation.
- **Phases 1..N**: every seat plays dumbbot, RNG seeded per repeat.
- **Horizon**: 1 game-year by default (roll until the next Adjustment has
  resolved), with 2 game-years offered. Both are precomputed for the baselines
  (D14).
- **Seeds**: canonical list `0..N-1`, baselines precomputed to 100, live runs use
  any `m <= 100` and compare against the first `m`. Placeholder default 30, to be
  set properly by D15.
- **Candidates**: the model's order set, plus two baselines, the human's actual
  order set and dumbbot's own pick for the eval nation. All three over the same
  seed list (D9). The two baselines are precomputed at harvest and stored in the
  fixture (D14), so at default settings only the model's rollout runs live.
- **Report**: supply-centre count delta and units remaining at the horizon, as a
  distribution over seeds, shown as a paired difference against the baselines with
  its uncertainty, never a bare mean (D15).

Expected cost, from the 40 ms per phase measured in section 3:

| Setting | Phases | Per candidate | Three candidates, serial |
|---|---|---|---|
| 1 game-year from Fall, 30 seeds | 2 | ~2.5 s | ~7.5 s |
| 1 game-year from Spring, 30 seeds | 4 | ~5 s | ~15 s |
| 2 game-years from Spring, 30 seeds | 8 | ~10 s | ~30 s |

Only the model's rollout runs at labelling time, so the live cost is the
per-candidate column. Everything else is paid once at harvest: two baselines at
two horizons, 100 seeds each, is roughly 96 s for a Spring fixture and half that
for a Fall one, so a 30-fixture batch is under an hour single-core and a few
minutes across cores. That is a one-time job, not something anyone waits on.

The candidates are independent, so run them in parallel processes when all three
are needed. The UI toggle hides the baselines, it does not skip computing them
(R6).

---

## 8. Constraints and conventions

- Root `CLAUDE.md` applies inside `evals/` as it does everywhere else: follow
  existing patterns, no code comments or docstrings (DRF view docstrings
  excepted, they feed OpenAPI), never suppress lint or type errors, write tests
  alongside features, cite file and line when asserting something about the
  codebase. `evals/` gets no `CLAUDE.md` of its own for now.
- `.claude/rules/backend/` and `.claude/rules/frontend.md` are scoped by path to
  `service/` and `packages/web`, so they do not load automatically in `evals/`.
  Follow them anyway where they apply, notably the single `tests.py` per Django
  app and asserting behaviour through HTTP endpoints
  (`.claude/rules/backend/tests.md`). Pure functions (prompt rendering, the
  parser, the counterfactual, rollouts) are tested directly, the way
  `service/adjudicator/tests.py` does.
- The dependency rules in D16 are hard rules, not preferences.
- The adjudicator has its own architectural rubric in
  `service/adjudicator/CLAUDE.md`. `evals/` calls the engine from outside through
  `adjudicate()` and `get_options()`; it does not reach into it.
- `evals/` has no Postgres dependency. Fixtures are files, and it carries none of
  the Postgres-only migrations that rule out SQLite for `service/`.
- The adjudicator needs the variant in its canonical form, which `service/`
  builds from the database (`service/variant/utils.py:204`). `evals/` keeps a
  committed JSON export of the classical variant instead (task 0.1), the same way
  `service/harness/data/variants/classical.json` keeps the prompt-side variant.
- Running the model needs an Anthropic API key in the `evals/` environment.
  `service/` reads it from `BOT_ANTHROPIC_API_KEY`
  (`service/harness/management/commands/run_evals.py:18`); `evals/` reads its own.
- **Privacy**: `PRIVACY.md:67` lists four third parties and Anthropic is not among
  them, while `PRIVACY.md:76` states no data is shared with other third parties
  and `PRIVACY.md:38` confirms chat messages are collected. Production already
  sends player messages to Anthropic through the reply task, so the policy is
  inaccurate today. This blocks the message work, not this plan (D11), but it
  needs fixing before any message eval touches real data.

---

## 9. Open questions

- **Q1.** Where the harvester reads from. It must not import app code (D16), so
  the candidates are the app's HTTP API or a one-off export. Whether the HTTP API
  exposes past phases with every nation's orders and resolutions is **not
  verified**; check before building task 1.4. If it does not, a read-only SQL
  export is the fallback.
- **Q2.** Issue #1142 claimed `CLAUDE.md` explicitly forbids Django models in
  `harness`. That wording is not in the current `CLAUDE.md` or `.claude/rules/`.
  Moot for `evals/`, which needs no models (fixtures are files), but the rule
  should be written down or dropped for `service/harness`.
- **Q3.** How fixtures get selected for harvesting. Deliberately unanswered: criteria
  designed before anything has been labelled will be wrong. For the first batch,
  take 20 to 30 phases across 3 to 5 completed games spread over early, middle and
  late game, and let labelling teach us what matters. Positions the bot itself
  played are the highest-value source, since the bot's real orders, the resulting
  board and eventually whether it got kicked all come for free.
- **Q4.** Whether `decision_richness` is stored in the fixture or computed on load.
  Default: stored, since the harvester enumerates the options anyway.
- **Q5.** The dev/test split. Deferred by agreement, and it needs no schema work:
  two eval sets named for the purpose express it. The reason it matters is sharper
  now that prompt iteration happens inside the tool (D1), because iterating
  against a fixture is exactly what stops it being a fair test of the prompt.
  Decide before the first eval set is used to judge a prompt change.
- **Q7.** What "good enough" means for any of these metrics. Unanswered in #1368
  and still unanswered.

Q6 (fix `support_coherence` now) is resolved: yes, in the `evals/` copy (task
1.2). Q8 (address options by content-derived id) is resolved: yes, it is required
by D13 (task 0.4).

---

## 10. Tasks

Each task states how to tell it is done. Every task happens inside `evals/`,
except 0.2, which edits root `CLAUDE.md`. No task edits anything under `service/`
or `packages/`.

### Phase 0: the separate space

- [ ] **0.1 Scaffold `evals/`.**
  A new Django project with its own settings, `manage.py`, requirements and test
  setup, runnable locally with no Postgres. Import `service/adjudicator` and
  `service/dumbbot` read-only (D18). Commit a canonical export of the classical
  variant for the adjudicator (section 8).
  *Done when*: `python manage.py check` and the test suite pass inside `evals/`;
  a test adjudicates a Spring 1901 position and lists its legal options through
  the imported engine; a test fails if any `evals/` module imports from
  `service/` outside the allowed packages; and `git diff` shows nothing changed
  under `service/` or `packages/`.

- [ ] **0.2 Document the separation in root `CLAUDE.md`.**
  Add an `evals/` boundary section alongside the design-playground one: this part
  of the repo is deliberately cut off from everything else for fast eval
  development, it is local only and not deployed, the D16 dependency rules, and
  that the production bot still runs on `service/harness`.
  *Done when*: a fresh session could infer where eval code belongs, and what it
  may import, without reading this plan.

- [ ] **0.3 Copy the `select_orders` task into `evals/`.**
  Prompts, parser, options helpers, the seven scorers and the 10 hand-built
  fixtures, copied from `service/harness/tasks/select_orders/`, with the
  fixtures split one per file and marked `provenance.source: "handbuilt"`.
  `service/harness` is left untouched.
  *Done when*: the copied task, run with the zero-token dumbbot solver, produces
  the same scores over the 10 fixtures as `service/dumbbot/evals.py` does today.

- [ ] **0.4 Address options by content-derived id** (D13).
  Replace `option_index` with a stable id built from the option's content in the
  renderer, `FORMAT`, the output schema and the parser. The parser rejects an
  unknown id with an error instead of skipping it.
  *Done when*: reordering or trimming the rendered option list does not change
  which order a given id selects; an unknown id raises a parse error; and the
  dumbbot solver still scores as in 0.3.

- [ ] **0.5 Assemble the prompt from named, editable parts** (D13, D19).
  System blocks and user prompt sections become named parts that can be
  overridden per run, and each user prompt section can have several renderers.
  Ship the current rendering as the default, plus one reshaped board renderer
  (provinces reachable this phase only) to prove the mechanism.
  *Done when*: with no overrides, the rendered prompt matches what the copied
  code produced in 0.3; an override of any single part changes only that part;
  and switching the board renderer changes the board section and nothing else.

### Phase 1: data

- [ ] **1.1 Fixture schema v2** (section 6).
  *Done when*: a fixture round-trips through the schema with all new fields
  populated, a newly created fixture has `eval_sets` empty, and a test fails if a
  fixture contains a user identifier.

- [ ] **1.2 Fix the dangling-support false positive**, in the `evals/` copy.
  `dangling()` builds its destination map only from the eval nation's own orders
  (`service/harness/tasks/select_orders/scorers/coherence.py:20`), so supporting
  an *ally's* move always scores as incoherent, because the ally's unit never
  appears in the order set. Supporting an ally is normal full-press play.
  *Done when*: a test covering a support of a foreign nation's ordered move scores
  CORRECT, and the existing dangling-support tests still pass.

- [ ] **1.3 Derive `ranked_options` from `option_labels`** (D12).
  *Done when*: a fixture carrying only `option_labels` produces the same
  `quality_strong` and `quality_avoidance` scores as the equivalent
  `ranked_options` fixture.

- [ ] **1.4 Harvester.**
  Build v2 fixtures from Diplicity game data without importing app code, per Q1.
  Reconstruct each phase's state, list legal options with `get_options`, and
  record every nation's `actual_orders` and the real `actual_outcome`. Works for
  any phase, not only a game's current one.
  *Done when*: harvesting a past phase writes a fixture with a non-empty option
  list; `actual_orders` covers every nation with units in the phase; and a test
  asserts the options for a reconstructed past phase match those for the same
  board as a current phase.

- [ ] **1.5 Harvest the first batch.**
  20 to 30 phases per Q3. Commit the fixture files.
  *Done when*: `evals/fixtures/` holds the batch, every file validates against
  schema v2, and each declares `provenance.source: "harvested"`.

### Phase 2: the rollout engine, headless

- [ ] **2.1 One-phase counterfactual.**
  Pure function: fixture plus a candidate order set in, the section 7 metrics out.
  *Done when*: replaying a fixture's own `actual_orders` reproduces its
  `actual_outcome` exactly. That is the test that proves the counterfactual is
  wired up correctly.

- [ ] **2.2 N-game-year rollout.**
  Phase 0 against archived orders, all-dumbbot forward to the horizon, seeded per
  repeat, paired seeds across candidates (D8, D9).
  *Done when*: the same seed produces byte-identical results across runs; a
  one-game-year rollout from a Spring position advances through Adjustment so the
  supply-centre delta is defined; and a rollout with a horizon of zero game-years
  equals the 2.1 result.

- [ ] **2.3 Management command.**
  Run the counterfactual and rollout for a fixture and print the comparison for
  model, human and dumbbot candidates.
  *Done when*: the command runs end to end on a harvested fixture and its timings
  land within roughly the section 7 table. If they are far off, re-measure before
  building UI on top.

- [ ] **2.4 Precompute and store the baselines.**
  Compute the human and dumbbot rollouts for every fixture at both offered
  horizons over the canonical 100-seed list, and write them into `baselines`
  keyed by those settings, keeping per-seed results (D14).
  *Done when*: every harvested fixture carries both baselines at both horizons;
  reading them back reproduces what a live run with the same settings produces;
  and a 30-seed live run compares against the first 30 stored seeds rather than a
  resampled set.

- [ ] **2.5 Set the seed count from data.**
  With baselines precomputed to 100 seeds, plot the standard error of the paired
  difference against seed count across the first batch and choose the default
  from the curve (D15).
  *Done when*: the curve exists for the first batch, the default is set from it,
  and this plan records the number and the reasoning that replaced the 30
  placeholder.

### Phase 3: the tool

- [ ] **3.1 Frontend scaffold** inside `evals/`.
  Vite, React, TypeScript strict. No imports from `packages/web` or
  `packages/design-playground`, enforced by `no-restricted-imports` the way the
  playground does it.
  *Done when*: `npm run build` and `npm run lint` pass, and a deliberate import
  from `packages/web` fails lint.

- [ ] **3.2 Local backend API.**
  Endpoints: list fixtures, read a fixture, render the prompt for a set of part
  overrides, run the model against it, run the counterfactual and rollout, run
  the eval suite, and write `option_labels`, `eval_sets` and `discarded` back to
  the fixture file.
  *Done when*: every endpoint has a test, and the label-write endpoint round-trips
  a label into the JSON file on disk.

- [ ] **3.3 Fixture list and board view.**
  Board rendered from the fixture, arrows overlaid as SVG (D3). Copy the board
  SVG and drawing code from `packages/web`; do not import it.
  *Done when*: a harvested fixture renders with units, supply centres and the real
  orders drawn, with failed orders visibly distinguished.

- [ ] **3.4 Option list and labelling.**
  Full legal option list, filterable, grouped by unit. Click an option to see it
  drawn on the board. Mark reasonable, unreasonable, or leave unlabelled. Select
  several options together to label them as a tuple (D2).
  *Done when*: labelling an option writes it to the fixture file and the label
  survives a reload; options the model did not pick are labellable; a support and
  its supported move can be labelled as one tuple and both are drawn on the board
  together.

- [ ] **3.5 Prompt workbench.**
  Every prompt part editable (D13), board renderer selectable (D19), run against
  the loaded fixture, and show the model's chosen orders and its `reasoning`
  beside the option list and on the board. `FORMAT` is marked as parser-coupled.
  Show the fully rendered prompt exactly as sent. Keep the previous run visible so
  a prompt change can be compared against what it replaced.
  *Done when*: an edited `PRINCIPLES` block produces a different order set on the
  same fixture; an edited or reshaped board section is visible in the rendered
  prompt and the run uses it; the runs before and after an edit can be seen side
  by side; and an unparseable completion surfaces the parse error rather than
  failing silently.

- [ ] **3.6 Suite runner and eval-quality view** (D20).
  Run the current prompt over a chosen eval set from the tool. Show aggregate
  scores, and per fixture every scorer's verdict and explanation beside the human
  labels and the model's orders. Highlight disagreements between a scorer and the
  labels.
  *Done when*: a suite run over the 10 hand-built fixtures completes from the UI;
  each fixture's per-scorer results are inspectable; a fixture where a scorer
  passes an order labelled unreasonable is flagged; and two suite runs with
  different prompts can be compared.

- [ ] **3.7 Metrics panel.**
  One-phase counterfactual metrics, plus the rollout with its paired baselines.
  Horizon selectable between the two precomputed values, seed count adjustable up
  to the precomputed depth, so both stay valid paired comparisons without
  recomputing baselines (D14). A toggle hides the baselines on screen without
  skipping them (R6).
  *Done when*: the panel shows model, human and dumbbot as a paired comparison on
  the same seeds; only the model's rollout runs live, with baselines read from the
  fixture; switching horizon or seed count within the precomputed range keeps the
  comparison valid with no recomputation, and going outside it is visibly flagged
  rather than silently compared; differences carry their uncertainty rather than
  being bare means; and the order set dumbbot filled in around each candidate is
  inspectable, not just the summary number.

- [ ] **3.8 Eval-set curation.**
  Add the loaded fixture to a named eval set, remove it, or discard it with a
  reason, writing `eval_sets` and `discarded` back to the file.
  *Done when*: set membership and discarding both survive a reload; a discarded
  fixture is visibly excluded from the working list but still present on disk; and
  the fixture list can be filtered by eval set.

### Phase 4: close the loop

- [ ] **4.1 Load the inspect task from the fixture directory by eval set.**
  `evals/`'s `select_orders(eval_set=...)` loads `evals/fixtures/`, filtered by
  eval-set membership, so what an eval run covers is decided by curation rather
  than by which file someone edited.
  *Done when*: `select_orders(eval_set=...)` runs over exactly the fixtures in that
  set, discarded fixtures are never included, and an empty or unknown set name
  fails loudly rather than silently running zero samples.

- [ ] **4.2 Baseline the evals** against the harvested fixtures, for both the
  model and dumbbot, and record the results in an `EVAL_RESULTS.md` inside
  `evals/`. Note that the dataset and the answer format both changed, so the
  numbers are not comparable with `service/harness/tasks/select_orders/EVAL_RESULTS.md`,
  which stays as it is.
  *Done when*: the file records a run against the new dataset with its fixture
  count and the incomparability noted.

- [ ] **4.3 Reply to discussion #1368** summarising what was decided and what was
  dropped, so the thread does not stay at the original proposal.
  *Done when*: the comment is posted and links to this plan.

### Not now

Reconnecting `evals/` to production: porting a better prompt, the option-id
format or the reshaped board back into `service/harness`. Do this deliberately,
once there is a measured improvement worth shipping.

Message-side work, listed here only so it is not lost: the privacy policy
correction (section 8), message fixtures, the negatives-first rubric with
code-checkable board-grounding claims separated from judge-only ones, the
should-reply classifier (cheapest item on the list, its answer key needs no human
labelling since "did a human reply, and how fast" comes straight from the
archive), and prompt-injection fixtures.
