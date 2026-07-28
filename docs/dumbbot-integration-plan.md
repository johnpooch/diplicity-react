# DumbBot integration plan

An implementation plan for adding a second automated player type — a **dumbbot**,
driven by David Norman's rule-based DumbBot algorithm — alongside the existing
LLM-backed bot.

This document is a plan, not an implementation. It is written to be handed to an
implementer who has not explored the codebase. Every design decision below cites
the code that motivates it.

---

## 0. What exists today (evidence)

Read these before starting; the plan assumes them.

| Concern | Where it lives today |
|---|---|
| "This member is automated" | `user__bot_profile__isnull=False` — the *only* signal. Used in `agent/decorators.py:13,43,58,70`, `member/serializers.py:28`, `channel/models.py:38,146`, `channel/serializers.py:36`, `game/models.py:779`, `draw_proposal/models.py:24,29` |
| Bot identity/persona | `bot_profile.BotProfile` (`user` OneToOne, `disposition`, `voice`); roster of 12 personas seeded in `bot_profile/migrations/0002_seed_roster.py`, plus a legacy `diplicitybot` user |
| Joining a game as a bot | `POST game/<id>/add-bot/` → `bot_profile/views.py::BotMemberCreateView` → `BotMemberCreateSerializer.create` does `game.members.create(user=...)` then `game.start_if_full()` |
| Scheduling bot work | `agent/signals.py` (three receivers) → `AgentTask.objects.create_from_event(...)` → `AgentTask.defer()` → `agent.tasks.run` → `_dispatch` → `plan` / `finalize` / `reply` |
| Turning a game into model input | `agent/context.py::fetch_context` (six HTTP calls via `agent/api_client.py`) → `harness/adapter.py::data_to_context` → `harness.types.Context` |
| Deciding orders | `agent/orchestration.py::run_select_orders` → `inference.Inference.objects.run(...)` → `harness.tasks.select_orders.parse_completion` → **`list[OrderOption]`** |
| Submitting orders | `agent/tasks.py::_submit_orders_from_context` → `agent/orders.py::option_to_selected` → `ApiClient.submit_orders` |
| Fallback when the model fails | `agent/fallback.py::first_legal_options` (first enumerated option per source) |
| Legal-order enumeration | `adjudication/service.py::start`/`resolve` → `python_options_to_godip_dict` → stored on `Phase.options` (JSONField) → `phase/utils.py::transform_options` → `order/views.py::OrderOptionsView` → flat `FlatOrderOption` records |
| Board adjacency | `province.Province.adjacencies` — a static per-variant JSONField of `{"to": <province_id>, "pass": "army"\|"fleet"\|"both"}` |
| Integration test conventions | `integration/` holds `tests.py`, `test_bot.py`, `test_replay.py`, `dsl.py`, `conftest.py`. `integration/conftest.py` patches every `procrastinate` `.defer()`, so tests drive `agent.tasks.plan/finalize` **directly** rather than via signals (`integration/test_bot.py:67,77`) |
| Expensive tests | `test_replay.py` is excluded from the default run via `addopts = "--ignore=integration/test_replay.py"` in `service/pyproject.toml`. Credential-gated tests use a module-level `pytest.mark.skipif` (`notification/tests_devices.py:4`) |

Two facts that shape the whole design:

1. **The game engine does not know what a bot is.** `member.Member` has no bot
   field; `phase/models.py`, `adjudication/`, `adjudicator/` never reference
   `bot_profile`. Automation is entirely an `agent`-app concern layered on top of
   the ordinary membership flow. A dumbbot therefore needs **zero** game-engine
   changes.
2. **The LLM path's output type is already board-shaped, not prose-shaped.**
   `parse_completion` returns `list[OrderOption]`, where every element is an
   object taken verbatim from `context["order_options"]`. Everything downstream
   of that point (coverage top-up, `max_orders` capping, `option_to_selected`,
   submission) is model-agnostic. That is the seam a dumbbot plugs into.

---

## 1. Design decisions

### 1.1 Does dumbbot use the harness, or bypass it?

**Bypass the prompt-engineering half, reuse the context half.**

- `harness` is defined in `CLAUDE.md` as *"pure prompt engineering: Block
  classes, `build_prompt()`, TaskDefinitions, prompt text, parsers, evals."* A
  rule-based order policy is none of those. Putting it in `harness` would break
  that one-sentence description.
- But `harness/adapter.py::data_to_context` and `harness/types.py::Context` are
  *not* prompt engineering — they are the neutral, denormalised board snapshot
  that the prompt builder happens to consume. `Context` already carries province
  adjacency with pass-type, unit positions/types/ownership, supply-centre
  ownership (including unowned centres as `nation: None`), and the full legal
  option list. That is precisely DumbBot's input.

So: **new Django app `dumbbot`**, sibling to `harness`, holding the algorithm.
It consumes `harness.types.Context` and returns `list[OrderOption]`. It imports
nothing from `agent`, `inference`, `bot_profile`, or any Django model — same
purity contract as `harness`. Resulting dependency graph (still strictly
one-way):

```
agent → harness
agent → dumbbot → harness (types only)
agent → inference
agent → bot_profile
```

`dumbbot` is a Django app rather than a plain package for consistency with
`harness`, which likewise has no models or views but is registered in
`INSTALLED_APPS` — and so that its tests live in `dumbbot/tests.py` per the
project's one-`tests.py`-per-app rule.

### 1.2 Does it emit the harness's response shape, or operate on legal orders?

**Operate directly on legal orders. No adapter is needed, because the harness's
*post-parse* representation is already `list[OrderOption]`.**

The `{"reasoning": ..., "choices": [{"source_id", "option_index"}]}` JSON in
`harness/tasks/select_orders/schema.py` exists only because an LLM has to
express a choice in text. Making a deterministic function serialise to JSON so
another function can parse it back would be pure ceremony.

This costs nothing in eval compatibility, because the `inspect_ai` scorers in
`harness/tasks/select_orders/scorers/` all work by running the *completion text*
through `parse_completion` and then scoring the resulting `list[OrderOption]`
against the sample's `context`. A dumbbot that produces the same list is scored
by the same logic. See §5.3 for the optional (recommended, zero-token) eval
harness that exploits this.

### 1.3 Flag on the user model, or a distinct user kind?

**A `kind` field on the existing `BotProfile`.** Not a new model, not a field on
`User`.

Rationale, from the grep in §0: sixteen call sites across seven apps detect
automation with `user__bot_profile__isnull=False`. A separate `DumbbotProfile`
model would require auditing and editing all of them, and every future one. With
`kind` on `BotProfile`:

- every existing "is this member automated?" query keeps working unchanged,
  including `member/serializers.py::_is_bot` (so `is_bot` stays `true` for
  dumbbots — correct: they *are* automated), anonymous-game unmasking, channel
  visibility, and `Game.delete_if_empty_pending`;
- only the three places that must distinguish *how* a bot decides consult
  `kind`.

Implications:

- **Auth**: none. Dumbbot users are ordinary `auth.User` rows created by a data
  migration exactly like the current roster (`get_or_create` on email, no
  password set → unusable password, `is_active=True`). They never log in; the
  agent layer authenticates as them in-process with
  `rest_framework.test.APIClient.force_authenticate` (`agent/api_client.py:25`).
- **Matchmaking**: dumbbots flow through the existing
  `BotProfile.objects.available_for_game(game)` queryset and the existing
  `add-bot` endpoint, so they "really join" like any bot. Surface `kind` in
  `AvailableBotSerializer` so the picker can label them.
- **Game engine**: unchanged, per §0 fact 1.

### 1.4 Does a dumbbot talk?

**No.** DumbBot is a no-press policy by definition. Suppress it at the *signal*
layer, not inside the task, so a dumbbot never even gets a `REPLY` `AgentTask`
row: filter `with_bot_channel_members` (`agent/decorators.py:65`) to LLM-kind
bots only. This is cheaper and more observable than creating a task that returns
immediately.

Consequence to accept deliberately: a human writing to a channel containing only
dumbbots gets silence. That matches the algorithm's definition. Note it in the
PR description.

### 1.5 Policy dispatch: branch or class registry?

**A plain branch, in one place.**

`CLAUDE.md`'s declarative-class-plus-registry guidance is explicit that it is not
for cases that are "few and uniform". After §1.4 removes the reply axis, exactly
one function varies across exactly two policies. A two-class hierarchy plus a
registry for that would be more code than the thing it organises, violating
"Simplicity is correctness".

If a third policy ever lands, or if the policies diverge on a second behaviour,
that is the moment to promote it to an `OrderPolicy` base class in `agent/` —
call it out in the PR description as the deliberate escape hatch.

---

## 2. The contract `dumbbot` must satisfy

One public entry point, in `dumbbot/policy.py`:

```
select_orders(context: Context, *, rng: random.Random) -> list[OrderOption]
```

**Inputs**

- `context`: a `harness.types.Context`. The function reads only
  `members` (to find `is_current_user` → its own nation name, via
  `harness.utils.current_nation`), `phase` (`season`, `year`, `type`),
  `max_orders`, `provinces` (`id`, `type`, `supply_center`, `parent_id`,
  `adjacencies[].to`, `adjacencies[].allows`), `units`
  (`type`, `nation`, `province`, `dislodged`), `supply_centers`
  (`nation` — `None` when unowned — and `province`), and `order_options`.
  It must never read `channels`.
- `rng`: injected `random.Random`. Do **not** call module-level `random.*`.
  Injection is what makes the unit tests and the fast integration test
  deterministic (seeded) while production stays varied.

**Output**

- A list of `OrderOption` **objects taken by identity from
  `context["order_options"]`** — never newly constructed dicts. This guarantees,
  for free, that the output is legal (it is a subset of the engine's own
  enumeration) and that `agent/orders.py::option_to_selected` can serialise it.
- At most one entry per distinct `source`.
- Best-effort coverage: one entry per orderable source. The caller still tops up
  and caps (see below), so a short list is not a failure.

**Failure mode**

- Raise `dumbbot.exceptions.DumbbotError` (a single new exception class) on
  unusable input — e.g. `current_nation` cannot be resolved. The caller catches
  it exactly as it catches `ContextError | InferenceError | ParsingError` today
  and falls back to `first_legal_options`.
- Never raise on a merely *degenerate* board. `integration/test_bot.py:120`
  proves adjacency data can legitimately be empty
  (`Province.objects.update(adjacencies=[])`); with an empty graph all proximity
  values collapse to zero and the policy must still return one option per source
  (whatever wins the tie-break). Add a unit test mirroring that case.

**Guarantees the caller keeps providing** (do not duplicate them inside
`dumbbot`): coverage top-up from `first_legal_options`, `max_orders` capping,
and submission — all already in `agent/tasks.py::_submit_orders_from_context`
lines 56–68.

---

## 3. Data and plumbing changes

Ordered. Each step should be independently reviewable.

### Step 1 — `bot_profile`: add `kind`

1. `bot_profile/constants.py`: add a `BotKind` class following the existing
   constants idiom in `common/constants.py` (`LLM = "llm"`,
   `DUMBBOT = "dumbbot"`, `KIND_CHOICES = (...)`).
2. `bot_profile/models.py`: add
   `kind = models.CharField(max_length=20, choices=BotKind.KIND_CHOICES, default=BotKind.LLM)`.
   Keep `disposition`/`voice` as they are; dumbbot rows store `""`.
3. Migration: schema migration adding the field (existing rows default to
   `llm`).
4. `bot_profile/models.py`: add a `BotProfileQuerySet.llm()` helper
   (`filter(kind=BotKind.LLM)`) — used by the reply decorator in Step 3. Expose
   it on the manager alongside `with_related_data` / `available_for_game`,
   matching the existing manager style.

### Step 2 — `bot_profile`: seed the dumbbot roster

New data migration, modelled on `0002_seed_roster.py`:

- A `DUMBBOT_ROSTER` list of entries with `name` and `slug` only (no
  disposition/voice — the algorithm has no persona).
- Seed **at least 7** so a full classical game can be filled entirely with
  dumbbots; 8–12 gives headroom. Names should read as machine players (e.g.
  "Automaton I".."Automaton VII") so a human in a mixed game is not misled about
  what they are dealing with.
- Emails `<slug>@bots.diplicity.com`, usernames `<slug>bot`, `is_active=True` —
  identical construction to the LLM roster, with `kind=BotKind.DUMBBOT` and
  `disposition=""`, `voice=""`.
- Provide the matching `reverse_code` deleting those users, as the existing
  migration does.

### Step 3 — `agent`: route by kind

1. `agent/tasks.py::_persona` — return `None` when the profile's `kind` is not
   `LLM`. This alone makes persona rendering a no-op for dumbbots
   (`agent/orchestration.py::_system` already handles `persona=None`).
2. `agent/orchestration.py` — add `run_dumbbot_orders(*, data)`:
   `data_to_context(data)` → `dumbbot.policy.select_orders(context, rng=...)`.
   Keep it a sibling of `run_select_orders` so the two decision paths sit
   side by side. It records no `Inference` row (there is no model call) — see
   §6.4 for the observability consequence.
3. `agent/tasks.py::_submit_orders_from_context` — take the bot kind as an
   argument (resolved once by the caller from the member's `BotProfile`) and
   pick between `run_dumbbot_orders` and `run_select_orders`. Extend the existing
   `except (ContextError, InferenceError, ParsingError)` tuple with
   `DumbbotError`. Everything after the try/except is untouched.
4. `agent/decorators.py::with_bot_channel_members` — restrict to LLM bots
   (`user__bot_profile__kind=BotKind.LLM`). Leave `with_bot_members` and
   `_bot_user_ids_for_phase` matching **all** bots: dumbbots must still get
   `PLAN`/`FINALIZE` tasks and must still count as non-humans in
   `when_humans_confirmed`.

### Step 4 — `dumbbot`: the app

- `dumbbot/apps.py`, `dumbbot/__init__.py`; register `"dumbbot"` in
  `INSTALLED_APPS` (`project/settings.py`, next to `harness`).
- `dumbbot/exceptions.py` — `DumbbotError`.
- `dumbbot/board.py` — the derived board model (§4.1).
- `dumbbot/weights.py` — the tuning constants (§4.5).
- `dumbbot/policy.py` — `select_orders` and the per-phase-type scorers (§4.2–4.4).
- `dumbbot/tests.py` — all tests for the app in one module, per `CLAUDE.md`.

### Step 5 — API surface and codegen

- `bot_profile/serializers.py::AvailableBotSerializer` — add a read-only `kind`
  field so the bot picker can distinguish and label the two types.
- Run `docker compose up codegen` and commit **all four** generated artefacts
  (`service/openapi-schema.yaml`, `service/openapi-schema.internal.yaml`,
  `packages/web/src/api/generated/`, `service/harness/generated/api.py`). Then
  `npx tsc -b --noEmit` in `packages/web`.
- Frontend: `packages/web/src/components/PlayerInfoContent.tsx:148` renders a
  badge off `member.isBot`. `isBot` stays `true` for dumbbots, so nothing breaks
  without a frontend change. **Deciding whether the UI should distinguish the two
  bot types is out of scope for this plan** — if it is added in the same PR,
  screenshots are mandatory per `CLAUDE.md`.

### Step 6 — Tests alongside each step

- `bot_profile/tests.py`: dumbbot profiles are returned by
  `available_for_game`; `kind` is serialised.
- `agent/tests.py`: a dumbbot member gets `PLAN`/`FINALIZE` `AgentTask` rows but
  **no** `REPLY` row when a human posts; `plan` for a dumbbot member submits
  orders and creates **zero** `Inference` rows (mirror the existing mocked-client
  style at `agent/tests.py:62`, asserting the mock was never called).
- `dumbbot/tests.py`: §4 unit tests.

---

## 4. The algorithm in this codebase

DumbBot is deterministic apart from one explicit randomisation. It has two
stages: value the board, then score every enumerated legal order against those
values.

### 4.1 Derived board model (`dumbbot/board.py`)

Built once per `select_orders` call from `Context`. Pure data, no scoring.

- **Locations vs provinces.** Adjacency in `Context` is over *locations*: named
  coasts appear as first-class province entries with a `parent_id`
  (`bul/sc`, `spa/nc`, …) and are legitimate adjacency targets — verified in
  `harness/data/variants/classical.json`. Build the graph over locations; keep a
  `parent_of(location)` map from `province["parent_id"]` and collapse to parent
  provinces whenever valuing supply centres or comparing to unit positions.
  Getting this wrong is the single most likely source of subtle bugs.
- **Typed adjacency.** `Adjacency.allows` is a list — `["army"]`, `["fleet"]`, or
  `["army", "fleet"]` (`harness/adapter.py::PASS_TO_ALLOWS`). Every graph walk is
  parameterised by unit type; armies and fleets see different graphs.
- **Ownership.** `owner_of[province] = supply_center["nation"]` (may be `None`).
- **Power size.** `size_of[nation] = ` count of supply centres owned. Powers with
  no centres are size 0.
- **Adjacent-unit tallies** per location and unit type: how many of *our* units
  could move/support into it, and, per other power, how many of *theirs* could.

Note: DumbBot needs only *current* ownership, not ownership history — `Context`
supplies that already, so no new persistence or pre-computation is required.
There is no existing "board-dynamics pre-computation" subsystem in this
repository to source from: what exists is `Phase.options` (the engine's legal-move
enumeration, recomputed per phase by `adjudication.service`) and the static
per-variant `Province.adjacencies` JSON. Both are already reachable via
`Context`, which is why the derived model above is cheap to build in-process and
needs no caching in v1 (classical is 75 provinces × ~10 proximity rounds).

### 4.2 Province values

For the current nation `us`:

- `attack_value[province]` — non-zero only for supply centres not owned by `us`:
  the size of the owning power (unowned centres get a small fixed floor so they
  are still attractive). Bigger powers are more attractive targets.
- `defence_value[province]` — non-zero only for supply centres owned by `us`:
  the strength of the largest single adjacent enemy presence.

### 4.3 Proximity

The core of DumbBot. For each location and each unit type, compute a proximity
vector `proximity[0..N-1]`:

- `proximity[0][loc] = attack_value[parent_of(loc)] * attack_weight
                     + defence_value[parent_of(loc)] * defence_weight`
  (weights vary by phase — §4.5).
- `proximity[n][loc] = (proximity[n-1][loc] + Σ over type-reachable neighbours
   of proximity[n-1]) / (neighbour_count + 1)`.

This diffuses value outwards, so a unit ten provinces from a fat enemy centre
still feels a faint pull toward it. `N = 10` in the reference implementation.

### 4.4 Scoring the enumerated options

Because the engine hands us every legal order, DumbBot's "generate candidate
moves" step becomes "score `context["order_options"]`". For each option, derive
its *destination location*: the `target` for `Move`/`MoveViaConvoy`, the
`source` for `Hold`, the supported order's destination for `Support`, the
build/disband location otherwise.

```
destination_score(loc, unit_type) =
      Σ_n proximity[n][loc] * proximity_weight[phase][n]
    + our_adjacent_units[loc]        * strength_weight[phase]
    - max_rival_adjacent_units[loc]  * competition_weight[phase]
```

Then, per phase type:

- **Movement.** Order our units by their best available destination score,
  descending. Walk that order; for each unit take its highest-scoring option,
  except that with probability `play_alternative` pick a random lower-ranked
  option, weighted so that options far below the best are unlikely
  (`alternative_difference_modifier`). This is the deliberate unpredictability.
  If a unit's chosen destination is already claimed by one of our own units,
  prefer a legal `Support` of that move instead; if no support is legal, fall
  back to the next-best option, then `Hold`. Support of a *hold* on our
  most-threatened own centre is the last resort.
- **Retreat.** Retreat options arrive under the `Move` order type
  (`adjudication/options_adapter.py:109` rewrites the engine's native `Retreat`
  back to `Move` for the wire format) — so do **not** look for an order type
  named `Retreat`. Pick the highest-scoring destination; if none scores above
  zero and `Disband` is enumerated, disband.
- **Adjustment — builds.** `Build` options carry a `unit_type` and possibly a
  `named_coast` (`agent/orders.py:11`). Rank the enumerated build locations by
  defence-weighted proximity and take the top `max_orders`. Both army and fleet
  builds are enumerated separately at the same province; score them
  independently so a threatened coastal home centre naturally prefers a fleet.
- **Adjustment — disbands.** Rank our units by the value of the location they
  occupy, ascending, and disband from the bottom until the count is satisfied.

`max_orders` (`Context["max_orders"]`, sourced from the current user's
`PhaseState`) is authoritative in adjustment phases; the caller also caps, but
respecting it in the policy avoids submitting orders that will be discarded.

### 4.5 Weights (`dumbbot/weights.py`)

One frozen table per phase category (spring movement, fall movement, build,
remove), each holding a 10-element proximity weight vector plus attack, defence,
strength and competition weights, and the two randomisation constants
`play_alternative` and `alternative_difference_modifier`.

**Do not take these numbers from memory or from this document.** Port them from
the published DumbBot 1.4 reference source and cite that source in a header
comment — this is one of the two documented comment exceptions being requested
explicitly, so confirm with the reviewer, or record the provenance in the PR
description instead if they prefer to keep the no-comments rule absolute.
Norman's own note is that the values were hand-picked, not tuned, so treat them
as a faithful-port target, not something to improve in this PR.

### 4.6 Unit tests (`dumbbot/tests.py`)

Build `Context` objects the same way the harness evals do — `fixture_to_context`
from `harness/adapter.py` over small hand-written fixtures — so the test inputs
match the production input type exactly.

- Every returned option is identity-present in `context["order_options"]`.
- At most one option per `source`; sources covered.
- A seeded `rng` gives byte-identical output across runs.
- With `play_alternative` forced to 0 and a contrived board, the unit adjacent to
  a fat undefended enemy centre moves into it.
- Empty-adjacency board (mirroring `integration/test_bot.py:120`) still returns
  one option per source.
- Named-coast fixture: a fleet ordered to a multi-coast province emits the
  `named_coast` field, so `option_to_selected` produces a 4-element selection.
- Retreat fixture: retreat options presented as `Move` are handled.
- Adjustment fixture: build and disband counts respect `max_orders`.

---

## 5. The integration eval

### 5.1 Files

- `integration/test_dumbbot.py` — **fast, deterministic, runs in CI by default.**
  A 7-dumbbot classical game driven a handful of phases with a seeded rng. No
  LLM. Guards the plumbing: game setup, task dispatch, order submission,
  confirmation, resolution, and the scoring helper. This is what actually
  protects the feature day to day.
- `integration/test_dumbbot_match.py` — **the slow LLM match described in the
  brief.** Two full games to Spring 1910.
- `integration/scoring.py` — shared `sum_of_squares(phase)` helper (see §5.5),
  imported by both.

### 5.2 Why the split

Game A alone is 6 LLM bots × roughly 30–40 phases from Spring 1901 to Spring
1910 ≈ 200 real model calls; Game B adds ~35 more. That is real money and tens
of minutes. It cannot sit in the default suite.

Follow the two existing precedents rather than inventing a mechanism:

1. Add `--ignore=integration/test_dumbbot_match.py` to the `addopts` in
   `service/pyproject.toml`, next to the existing `test_replay.py` ignore, and
   extend the comment above it. Invoke explicitly:
   `pytest integration/test_dumbbot_match.py`.
2. Module-level `pytestmark = pytest.mark.skipif(not settings.BOT_ANTHROPIC_API_KEY, ...)`,
   copying `notification/tests_devices.py:4`, so an explicit invocation without
   a key skips cleanly instead of erroring.

### 5.3 Optional but recommended: a token-free harness eval

Separately from the integration tests, add `dumbbot/evals.py` mirroring
`harness/tasks/select_orders/evals.py`: reuse the **same** `dataset.json` and the
**same** seven scorers, with a solver that runs `dumbbot.policy.select_orders`
and emits the `{"choices": [...]}` JSON the existing `parse_completion` expects.
Costs zero tokens, runs in seconds, and yields a directly comparable
`quality_strong` / `quality_avoidance` number against the LLM baseline in
`harness/tasks/select_orders/EVAL_RESULTS.md`. Note that only dataset samples
carrying a `ranked_options` block contribute to those two scorers; the rest are
`Score.unscored()`. This is the cheapest possible answer to "is the dumbbot any
good?" and worth doing before the expensive match.

### 5.4 Game setup

Both games use `classical_variant` (7 playable nations — `England`, `France`,
`Germany`, `Italy`, `Austria`, `Turkey`, `Russia`) and must contain **no human
players**. Use the real HTTP flow; a Game Master game makes this possible
without hacking around the model layer:

1. An allowlisted client creates the game with
   `{"private": true, "game_master": true, "nation_assignment": "ordered",
     "deadline_mode": "duration", "movement_phase_duration": "24 hours"}`.
   Evidence that this yields a zero-member game whose creator is both
   `game_master` and `admin`: `game/tests/test_game_master.py:47-54` asserts
   `game.members.count() == 0`; `game/serializers.py:502` requires `private` for
   `game_master`; `common/permissions.py:189` gates `add-bot` on
   `game.admin_id == request.user.id`.
   The allowlist is set the same way `integration/test_bot.py:50` does it —
   a fixture assigning `settings.BOT_OPPONENT_ALLOWLIST`, required by
   `CanUseBotOpponent`.
2. `POST game/<id>/add-bot/` seven times with the chosen bots' `user_id`s.
   `IsSpaceAvailable` permits members `< 7`, and the seventh call triggers
   `start_if_full()` → `game.start()` → nations assigned, first phase ACTIVE.
   - **Game A**: 6 profiles with `kind=llm` + 1 with `kind=dumbbot`.
   - **Game B**: 1 profile with `kind=llm` + 6 with `kind=dumbbot`.
   - With `nation_assignment: ordered`, seat order is join order, so the games
     are reproducible. Vary *which* seat the minority bot occupies between the
     two games only if you intend to control for positional advantage — and if
     you do not, say so when reporting, because England and Austria are not
     equivalent seats.
3. Fixtures needed: `mock_send_notification_to_users` and
   `mock_immediate_on_commit` (as `test_replay.py` uses), plus the autouse
   procrastinate patch already in `integration/conftest.py`.

### 5.5 Driving to Spring 1910

Drive the loop explicitly; do not rely on signals (`integration/conftest.py`
patches `.defer()` away, and `integration/test_bot.py` establishes calling
`agent.tasks` functions directly as the convention).

Per iteration:

1. Read `game.current_phase`. Stop if it is `Spring 1910 Movement`.
2. For each member whose `PhaseState` on the current phase has
   `has_possible_orders=True`, call `agent.tasks.finalize(user_id, game_id)`.
   `finalize` both submits orders and confirms (`agent/tasks.py:86-102`), so a
   separate `plan` pass would double the LLM spend for no benefit. Iterate
   members in a stable order.
3. `POST reverse("phase-resolve-all")`. With every phase state confirmed, the
   `all_confirmed` branch of `PhaseQuerySet.filter_due_phases`
   (`phase/models.py:71-86`) makes the phase due without any clock manipulation.
4. Assert the phase advanced; abort with a clear message if it did not (this is
   the deadlock detector — see §6.1).

Termination and guards:

- Stop early if `game.status != GameStatus.ACTIVE`. A solo victory at 18 centres
  ends the game (`victory/utils.py::check_for_solo_winner`), and abandonment is
  possible too. This is a legitimate outcome, not a test failure: score the final
  phase and report *why* it stopped.
- Hard iteration cap (~120 phases) so a stall fails fast instead of burning
  tokens.
- Emit a progress line per phase (phase name, per-nation centre counts) so a long
  run is observable while it happens.

Spring 1901 → Spring 1910 is 9 game-years; retreat and adjustment phases with no
possible orders are skipped by the engine (`integration/dsl.py:203-212` documents
this), so expect roughly 30–40 phases rather than a fixed number. Match on
`(season, year, type) == ("Spring", 1910, "Movement")`, never on an ordinal.

### 5.6 Sum-of-squares scoring

In `integration/scoring.py`:

- Given a phase, count supply centres per nation from `phase.supply_centers`
  (grouped by `nation_id`; `supply_center.SupplyCenter` has `phase`, `nation`,
  `province`).
- Per-nation score = `count ** 2`; game total = the sum over all nations.
- Classify each nation via `member.user.bot_profile.kind`, and report three
  numbers per game: the LLM cohort's summed score, the dumbbot cohort's summed
  score, and the total.
- Return a plain dataclass/dict so the test can both assert on it and print it.

Reporting: print a readable per-nation table plus the cohort totals for each
game, and the two games side by side. Since the interesting output is a
*measurement*, the assertions must not encode an expected winner — assert only
invariants:

- the game reached Spring 1910 Movement, or terminated early for a stated reason;
- every nation's centre count is `>= 0` and the totals sum to the variant's
  supply-centre count minus unowned centres;
- the sum-of-squares total is positive.

Any assertion of the form "LLM bots beat dumbbots" would make the test a coin
flip; the number is for humans to read. If a baseline is wanted, record the
observed figures in a short results file next to
`harness/tasks/select_orders/EVAL_RESULTS.md` and update it on re-runs.

---

## 6. Open risks and ambiguities

**6.1 An all-bot game may deadlock in production (pre-existing, now reachable).**
`agent/signals.py::plan` fires on phase activation and submits orders but never
confirms. Confirmation happens in `finalize`, which is triggered by a
`PhaseState` `post_save` with `orders_confirmed=True` and gated by
`when_humans_confirmed` (`agent/decorators.py:90`). In a game with no humans,
nothing ever saves a confirmed `PhaseState`, so the trigger never fires and the
phase only advances when its deadline passes. The integration eval sidesteps this
by driving `finalize` directly, so **the eval passing is not evidence that
all-bot games work in production.** Decide explicitly whether this feature is
meant to enable all-bot games; if so, it needs its own fix (e.g. have `plan`
confirm when no human members exist, or let the reconciler drive it) and its own
issue. Do not silently fix it inside this PR.

**6.2 The DumbBot constants must be sourced, not remembered.** §4.5. Any
weight table reproduced from memory is unverifiable and will produce a bot that
resembles DumbBot without being it. Port from the reference source and cite it.

**6.3 `CLAUDE.md` describes a harness that is ahead of the code.** It refers to
"Block classes", "`build_prompt()`", and "TaskDefinitions"; the actual
`harness/tasks/select_orders/` exposes plain `system_prompt()` / `user_prompt()`
/ `parse_completion()` functions with no such abstractions. Follow the **code**,
not the doc, and flag the drift so the doc can be corrected separately.

**6.4 Dumbbot decisions are invisible in the admin.** Every LLM decision leaves an
`Inference` row browsable in Django admin (`inference/admin.py`); a dumbbot
records nothing but its resulting `Order` rows and an `AgentTask` row. Debugging a
bad dumbbot turn will mean re-running the policy against a `dump_phase` fixture.
`agent/management/commands/dump_phase.py` already produces exactly the right
artefacts for that, which is adequate for v1 — but if reviewers want parity,
persisting a compact per-decision score trace is the follow-up, and it belongs in
`agent`, not `dumbbot` (which must stay side-effect-free).

**6.5 Convoys are effectively unmodelled.** DumbBot treats `MoveViaConvoy` as
another destination and does not plan a convoy chain. The engine only enumerates
a convoy move when a chain is available, so nothing illegal can be produced, but
dumbbots will rarely execute deliberate convoys. Acceptable for a faithful port;
worth stating in the PR so it is not later read as a bug.

**6.6 Cost and runtime of the LLM match are not yet measured.** The ~200-call
estimate for Game A is derived from phase counts, not observed. Before running
both games, run the fast dumbbot-only test and one *short* LLM game (e.g. to
Spring 1903) to calibrate wall-clock and token spend, and report the projection.
Note also that `BOT_LLM_MODEL` defaults to `claude-haiku-4-5`
(`project/settings.py:266`) — the recorded result is meaningless unless the model
actually used is reported alongside it.

**6.7 Seat assignment is a confound.** With `nation_assignment: ordered` the
minority bot's power is fixed by join order. One game per configuration is a
sample of one; the sum-of-squares figures indicate direction at best. If a
defensible comparison is wanted, that means repeated runs across seats — a much
larger piece of work than this plan covers, and it should be a separate issue.

**6.8 `finalize` confirms unconditionally.** `agent/tasks.py:97` calls
`api.confirm_phase` after submitting, without checking whether the member had
possible orders this phase. The driver loop should only invoke it for phase
states with `has_possible_orders=True` (as §5.5 specifies). If a
`game-confirm-phase` call for an order-less member turns out to 4xx, the loop
must surface it rather than swallow it — `ApiClient.confirm_phase` raises
`ApiClientError`, which `finalize` catches and logs as an abort, so a silent
stall is the failure mode to watch for.

**6.9 Naming.** This document uses `dumbbot` (app), `BotKind.DUMBBOT`, and
`select_orders` as the entry point, deliberately avoiding "`DumbbotAgent`" — the
existing LLM path has no `Agent` class either, and introducing one for a single
function would not match the surrounding code. If the reviewer prefers the
`Agent` name, it should be introduced for *both* policies at once, as the
promotion described in §1.5.
