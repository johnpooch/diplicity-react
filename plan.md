# AI player evals: the order side

Implementation plan. Nothing here is built yet.

Source material: discussion [#1368 "AI player evals"](https://github.com/johnpooch/diplicity-react/discussions/1368),
a call with John, and a design session on 22-23 September 2026. Where this plan
contradicts #1368, this plan is later and wins.

---

## 1. Goal

Build the data and the tooling needed to tell whether the AI player's order
selection is any good, and to make prompt iteration produce a trustworthy
signal rather than vibes.

The binding constraint is human labels. Everything downstream (scorers, answer
keys, judges) needs positions that a human has judged, and only a human can
produce those. So the first deliverable is not a metric, it is a tool that makes
labelling fast, plus the fixtures to label.

### In scope

- A **local tool** for order fixtures: board view, legal option list, run the
  model, see consequences, label options.
- **Prompt iteration inside that tool**: view and edit the system prompt, re-run
  it against the loaded fixture, and see straight away what the orders became and
  what they cost. The tool is as much a prompt workbench as a labelling tool.
- **Eval-set curation**: mark a fixture as belonging to a named eval set, or
  discard it as unsuitable, from inside the tool.
- A **harvester** that turns real archived Diplicity phases into self-contained
  fixtures.
- **Fixture schema v2**, including what the real players actually ordered.
- A **one-phase counterfactual**: swap the model's order set in against the
  other nations' archived orders and measure what changes.
- **Zero-token dumbbot rollouts** to show board-level consequences a game-year out.
- **Per-option human labels** written back into the fixture, as the answer key
  future scorers will use.

### Explicitly out of scope

Do not build these as part of this plan. Each was considered and deferred.

- **Everything on the message side.** Message quality rubrics, the should-reply
  decision, prompt-injection and jailbreak fixtures, LLM-judge calibration.
  Parked by decision, see D11.
- **Order consistency with respect to reasoning** as an LLM judge. Deferred.
- **Persisting eval runs, and any dashboard.** Issue
  [#1142](https://github.com/johnpooch/diplicity-react/issues/1142) posed this
  and was closed as not planned.
- **Deploying the tool.** v1 is local only, see D5.
- **Changing production bot behaviour.** This plan is measurement only.
- **The dumbbot match protocol.** Settled in
  [#1126](https://github.com/johnpooch/diplicity-react/issues/1126). Do not
  redefine it.
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
- `service/dumbbot/` holds a heuristic policy that plays legal Diplomacy for
  zero tokens (`service/dumbbot/EVAL_RESULTS.md`). It currently beats the LLM on
  every scorer, five of them trivially because it picks from the engine's own
  option enumeration and so cannot emit an illegal order.
- `service/adjudicator/` is a pure, Django-free engine. Its public facade is
  `adjudicate(variant, game_state)` (`service/adjudicator/__init__.py:16`), and
  `service/adjudicator/options.py:47` exposes `get_options(state)`.
- `service/agent/management/commands/dump_phase.py` is the existing harvester.
  It has two problems, see D6.
- `packages/design-playground/` is a prototyping app. Not suitable for this
  tool, see R1.

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

**D1. The UI has two jobs: labelling and prompt iteration.**
Human labels are important to many downstream metrics, so labelling throughput
is one thing to optimise. The other is the loop someone actually runs when
improving the bot: edit the prompt, run it against a known position, see what
the orders became and what they cost on the board. Today that loop means editing
Python, running an inspect eval and reading aggregate scores, which is far too
slow to iterate against. A read-only inspection view serves neither job.

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

**D5. v1 is local only.** Runs against a local Django and writes fixture JSON
straight to disk. This removes staff authentication, deployment, and the
"how does a deployed app write to git" problem in one move, and keeps the
privacy question away from the order work entirely. Deploy later only if it
earns it.

**D6. Fixtures are self-contained JSON files committed to the repo.** They carry
their own variant id, phase, units, supply centres and full legal option list,
so the eval does not need a database at rest. This also delivers what John asked
for, a Diplomacy eval rather than a Diplicity-specific one: the portable
contract is the fixture schema plus `adjudicate()`, and only the harvester
touches Django.

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
(`service/harness/tasks/select_orders/scorers/quality.py:7`). Derive that shape
from `option_labels` at load time so those scorers keep working unchanged
instead of being rewritten before there is data to justify it.

**D13. The system prompt is editable in the tool; the user prompt is read-only
for now.**
The system prompt is assembled from a few constant text blocks plus a
phase-dependent task instruction
(`service/harness/tasks/select_orders/system_prompt.py:61`), so exposing those
blocks as editable text is straightforward, and `PRINCIPLES` is where the
Diplomacy strategy guidance actually lives. The user prompt is not text: it is
rendered from the context in Python
(`service/harness/tasks/select_orders/user_prompt.py:15`), and its rendered
option list is positionally coupled to the parser, which maps each
`option_index` into `group_options_by_source(context["order_options"])`
(`service/harness/tasks/select_orders/parser.py:20`). Let someone reorder or trim
that list as free text and indices silently map to different orders. Worse, an
out-of-range index is skipped rather than raised
(`service/harness/tasks/select_orders/parser.py:24`), so a desync surfaces as a
missing order rather than an error.

This is a v1 limitation, not a judgement that the user prompt does not matter.
The board description is very likely one of the more important parts of the
prompt and nobody knows yet whether the current one is any good, so it should
become editable. What blocks it is the positional index, not the generated text:
options are addressed by their position in the rendered list, so any edit that
reorders or trims that list silently changes what an index means. Until that is
fixed, changing how the board is described is a code change to `user_prompt.py`.
See Q8 for the change that would lift the restriction.

The `FORMAT` block is a special case: it is editable text like the rest of the
system prompt, but it specifies the JSON shape the parser expects, so editing it
will break parsing. Mark it as such in the UI.

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

---

## 6. Fixture schema v2

One JSON file per fixture. Recommended location
`service/harness/tasks/select_orders/fixtures/<id>.json`, one file per fixture
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
  supply centres. `_order_state` already computes a `failed` flag per order
  (`service/agent/management/commands/dump_phase.py:35`).
- `option_labels`: list of `{ options, label: "reasonable" | "unreasonable",
  labeller, labelled_at, note }`. `options` is a list: one entry in the ordinary
  case, several when the judgement holds only for a combination (D2). Absence of
  an entry means unlabelled.
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

- Root `CLAUDE.md` applies: follow existing patterns, no code comments or
  docstrings (DRF view docstrings excepted, they feed OpenAPI), never suppress
  lint or type errors, write tests alongside features, cite file and line when
  asserting something about the codebase.
- `packages/web` must never import from any prototype or tool package, and the
  reverse holds too.
- The new frontend package must not import from `packages/web` or from
  `packages/design-playground`. Copy what it needs.
- The adjudicator has its own architectural rubric in
  `service/adjudicator/CLAUDE.md` and deviations get rejected even when they
  work. Rollout code calls the engine from outside; it does not reach into it.
- `service/harness/` has no `models.py` today and the rollout logic needs none,
  so it stays that way. See Q2.
- Backend runs on `service/.venv/bin/python`. System `python3` is 3.11 and Django
  6 needs 3.12+.
- SQLite is not viable; some migrations use Postgres-only SQL.
- Variants are seeded by data migrations, so a local database has the classical
  variant after `migrate`. No production data is needed to run the engine.
- **Privacy**: `PRIVACY.md:67` lists four third parties and Anthropic is not among
  them, while `PRIVACY.md:76` states no data is shared with other third parties
  and `PRIVACY.md:38` confirms chat messages are collected. Production already
  sends player messages to Anthropic through the reply task, so the policy is
  inaccurate today. This blocks the message work, not this plan (D11), but it
  needs fixing before any message eval touches real data.

---

## 9. Open questions

- **Q1.** Name and location of the backend app that serves the tool. A DEBUG-gated
  URL include in a small Django app gets DRF and existing serializer patterns for
  free; a standalone management command serving HTTP is simpler but diverges from
  every other pattern in the service.
- **Q2.** Issue #1142 claimed `CLAUDE.md` explicitly forbids Django models in
  `harness`. That wording is not in the current `CLAUDE.md` or `.claude/rules/`.
  `harness` has no `models.py` today and this plan adds none, so nothing is
  blocked, but the rule should be written down or dropped.
- **Q3.** How fixtures get selected for harvesting. Deliberately unanswered: criteria
  designed before anything has been labelled will be wrong. For the first batch,
  take 20 to 30 phases across 3 to 5 completed games spread over early, middle and
  late game, and let labelling teach us what matters. Positions the bot itself
  played are the highest-value source, since the bot's real orders, the resulting
  board and eventually whether it got kicked all come for free.
- **Q4.** Whether `decision_richness` is stored in the fixture or computed on load.
- **Q5.** The dev/test split. Deferred by agreement, and it needs no schema work:
  two eval sets named for the purpose express it. The reason it matters is sharper
  now that prompt iteration happens inside the tool (D1), because iterating
  against a fixture is exactly what stops it being a fair test of the prompt.
  Decide before the first eval set is used to judge a prompt change.
- **Q6.** The `support_coherence` bug in section 10, task 0.1: fix now or when
  press lands.
- **Q7.** What "good enough" means for any of these metrics. Unanswered in #1368
  and still unanswered.
- **Q8.** Whether to address options by a content-derived id instead of by
  position, which is what would make the user prompt editable as text (D13).
  Today the model returns an `option_index` into the rendered per-province list.
  That is not an accident: an index cannot name an order that is not on the list,
  so illegal orders are unrepresentable, which is part of why `legality` sits at
  0.993. A stable id derived from the option's own content
  (source, order type, target, aux) keeps that property, since an unknown id is
  rejected exactly as an out-of-range index is, while surviving any reordering or
  trimming of the rendered list. It would also let the parser reject an unknown id
  loudly instead of skipping it
  (`service/harness/tasks/select_orders/parser.py:24`). The cost is a change to
  `FORMAT`, the parser and the output schema, and a re-baseline of every scorer,
  so it is a real piece of work rather than a free fix.

---

## 10. Tasks

Each task states how to tell it is done.

Test placement is governed by `.claude/rules/backend/tests.md`: every Django app
keeps a single `tests.py`, never a `tests/` package or split modules, and
behaviour is asserted through HTTP endpoints rather than against models,
managers or querysets directly. Pure engine-side functions are tested directly,
the way `service/adjudicator/tests.py` does.

### Phase 0: groundwork

- [ ] **0.1 Fix the dangling-support false positive.**
  `dangling()` builds its destination map only from the eval nation's own orders
  (`service/harness/tasks/select_orders/scorers/coherence.py:9`), so supporting an
  *ally's* move always scores as incoherent, because the ally's unit never appears
  in the order set. Supporting an ally is normal full-press play. See Q6 for
  whether to do this now.
  *Done when*: a test covering a support of a foreign nation's ordered move scores
  CORRECT, and the existing dangling-support tests still pass.

- [ ] **0.2 Teach the harvester to read historical phases.**
  `dump_phase` only emits fixture stubs when the phase is the game's *current*
  phase, and otherwise skips with "order options unavailable"
  (`service/agent/management/commands/dump_phase.py:94`), because it pulls the
  option list from the live API. The archive is entirely historical phases, so the
  harvester cannot currently do the job it exists for. Reconstruct the state and
  call `get_options` instead.
  *Done when*: `dump_phase --game <id> --phase <historical id>` writes a fixture
  with a non-empty `order_options`, and a test asserts the enumerated options for a
  reconstructed historical phase match those for the same board as a current phase.

- [ ] **0.3 Implement fixture schema v2.**
  Add the fields in section 6 to the fixture builder
  (`service/harness/adapter.py:214`) and have `dump_phase` populate them, including
  every nation's `actual_orders` and the real `actual_outcome`.
  *Done when*: a harvested fixture round-trips through the schema with all new
  fields populated, a test asserts `actual_orders` covers every nation with units
  in the phase, a newly harvested fixture has `eval_sets` empty, and no fixture
  contains a user identifier.

- [ ] **0.4 Derive `ranked_options` from `option_labels`.**
  Keep `quality_strong` and `quality_avoidance` working unchanged (D12).
  *Done when*: `python -m pytest service/harness -v` passes, and a fixture carrying
  only `option_labels` produces the same scores as the equivalent legacy
  `ranked_options` fixture.

- [ ] **0.5 Harvest the first batch.**
  20 to 30 phases per Q3. Commit the fixture files.
  *Done when*: the fixture directory holds the batch, every file validates against
  schema v2, and each declares `provenance.source: "harvested"`.

### Phase 1: the rollout engine, headless

- [ ] **1.1 One-phase counterfactual.**
  Pure function: fixture plus a candidate order set in, the section 7 metrics out.
  No Django models.
  *Done when*: replaying a fixture's own `actual_orders` reproduces its
  `actual_outcome` exactly. That is the test that proves the counterfactual is
  wired up correctly.

- [ ] **1.2 N-game-year rollout.**
  Phase 0 against archived orders, all-dumbbot forward to the horizon, seeded per
  repeat, paired seeds across candidates (D8, D9).
  *Done when*: the same seed produces byte-identical results across runs; a
  one-game-year rollout from a Spring position advances through Adjustment so the
  supply-centre delta is defined; and a rollout with a horizon of zero game-years
  equals the 1.1 result.

- [ ] **1.3 Management command.**
  Run the counterfactual and rollout for a fixture and print the comparison for
  model, human and dumbbot candidates.
  *Done when*: the command runs end to end on a harvested fixture and its timings
  land within roughly the section 7 table. If they are far off, re-measure before
  building UI on top.

- [ ] **1.4 Precompute and store the baselines.**
  Compute the human and dumbbot rollouts for every fixture at both offered
  horizons over the canonical 100-seed list, and write them into `baselines`
  keyed by those settings, keeping per-seed results (D14).
  *Done when*: every harvested fixture carries both baselines at both horizons;
  reading them back reproduces what a live run with the same settings produces;
  and a 30-seed live run compares against the first 30 stored seeds rather than a
  resampled set.

- [ ] **1.5 Set the seed count from data.**
  With baselines precomputed to 100 seeds, plot the standard error of the paired
  difference against seed count across the first batch and choose the default
  from the curve (D15).
  *Done when*: the curve exists for the first batch, the default is set from it,
  and this plan records the number and the reasoning that replaced the 30
  placeholder.

### Phase 2: the tool

- [ ] **2.1 Package scaffold.**
  New frontend package, Vite, React, TypeScript strict. No imports from
  `packages/web` or `packages/design-playground`, enforced by
  `no-restricted-imports` the way the playground does it.
  *Done when*: `npm run build` and `npm run lint` pass, and a deliberate import
  from `packages/web` fails lint.

- [ ] **2.2 Local backend API.**
  Per Q1. Endpoints: list fixtures, read a fixture, run the model against an
  edited prompt, run counterfactual and rollout, write `option_labels` back to
  the fixture file.
  *Done when*: every endpoint has a test, and the label-write endpoint round-trips
  a label into the JSON file on disk.

- [ ] **2.3 Fixture list and board view.**
  Board rendered from the fixture, arrows overlaid as SVG (D3).
  *Done when*: a harvested fixture renders with units, supply centres and the real
  orders drawn, with failed orders visibly distinguished.

- [ ] **2.4 Option list and labelling.**
  Full legal option list, filterable, grouped by unit. Click an option to see it
  drawn on the board. Mark reasonable, unreasonable, or leave unlabelled. Select
  several options together to label them as a tuple (D2).
  *Done when*: labelling an option writes it to the fixture file and the label
  survives a reload; options the model did not pick are labellable; a support and
  its supported move can be labelled as one tuple and both are drawn on the board
  together.

- [ ] **2.5 Prompt workbench.**
  Expose the system prompt's blocks as editable text, run the edited prompt
  against the loaded fixture, and show the model's chosen orders and its
  `reasoning` beside the option list. The user prompt is shown read-only, and the
  `FORMAT` block is marked as parser-coupled (D13). The user prompt is displayed
  in full so its board description can be read and judged even though it cannot
  yet be edited, and the UI says why. Keep the previous run visible so a prompt
  change can be compared against what it replaced.
  *Done when*: an edited `PRINCIPLES` block produces a different order set on the
  same fixture; the run before and after an edit can be seen side by side; the
  user prompt cannot be edited; and an unparseable completion surfaces the parse
  error rather than failing silently.

- [ ] **2.6 Metrics panel.**
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

- [ ] **2.7 Eval-set curation.**
  Add the loaded fixture to a named eval set, remove it, or discard it with a
  reason, writing `eval_sets` and `discarded` back to the file.
  *Done when*: set membership and discarding both survive a reload; a discarded
  fixture is visibly excluded from the working list but still present on disk; and
  the fixture list can be filtered by eval set.

### Phase 3: close the loop

- [ ] **3.1 Point the inspect task at the fixture directory.**
  `select_orders` currently loads a single `dataset.json`
  (`service/harness/tasks/select_orders/evals.py:22`). Load the fixture directory
  instead, filtered by eval-set membership, so what an eval run covers is decided
  by curation rather than by which file someone edited.
  *Done when*: `select_orders(eval_set=...)` runs over exactly the fixtures in that
  set, discarded fixtures are never included, and an empty or unknown set name
  fails loudly rather than silently running zero samples.

- [ ] **3.2 Re-baseline the evals** against the harvested fixtures and update
  `EVAL_RESULTS.md` and `service/dumbbot/EVAL_RESULTS.md`. Note in each that the
  dataset changed, so the new numbers are not comparable to the old ones.
  *Done when*: both files record a run against the new dataset with its fixture
  count and the incomparability noted.

- [ ] **3.3 Write the conventions down.** Root `CLAUDE.md` requires that an
  architectural decision is recorded in the same session it is made. Add the new
  package's boundary (what may import what, that it is local only and not
  deployed) alongside the existing design-playground boundary, and resolve Q2.
  *Done when*: root `CLAUDE.md` describes the boundary and a fresh session could
  infer where this tool's code belongs without reading this plan.

- [ ] **3.4 Reply to discussion #1368** summarising what was decided and what was
  dropped, so the thread does not stay at the original proposal.
  *Done when*: the comment is posted and links to this plan.

### Not now

Message-side work, listed here only so it is not lost: the privacy policy
correction (section 8), message fixtures, the negatives-first rubric with
code-checkable board-grounding claims separated from judge-only ones, the
should-reply classifier (cheapest item on the list, its answer key needs no human
labelling since "did a human reply, and how fast" comes straight from the
archive), and prompt-injection fixtures.
