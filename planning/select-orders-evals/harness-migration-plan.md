# Harness migration plan: `harness` → `harness_v2` → `harness`

Branch: `harness-migration` (off `select-orders-evals`).

Note on sources: `planning/select-orders-evals/decisions-log.md` does not exist on disk or
anywhere in git history. This plan relies on the decision summary provided with the task
(composer in agent; harness stays pure; `option_to_selected` demoted to an agent-side
submission serializer; canonical Context is harness_v2's shape; `fetch_context` adapts
raw API → Context in agent; ContextError degrades to first-legal fallback).

## Verified inventory

The entire agent→harness surface is four files (verified by grep; nothing else outside
`harness/` imports it):

- `agent/tasks.py:12-14` — `ParseError`, `ReplyTask`/`SelectOrdersTask`, `Persona`/`TaskContext`
- `agent/orchestration.py:3` — `build_prompt`
- `agent/context.py:4` — `ContextData`
- `agent/fallback.py:1-2` — `option_to_selected`, `OrderOptionDict`

Other references to the old app: `project/settings.py:106` (`INSTALLED_APPS`),
`harness/management/commands/run_evals.py`. References to `harness_v2` outside the package:
`docker-compose.yml:20` (codegen output path) and `CLAUDE.md`. `harness_v2/` is currently
untracked (never committed), so Phase 4 is `mv` + `git add`, not `git mv`.

## Resolved question 1: persona in select_orders

Old production **does** inject persona into the select_orders system prompt. Evidence:
`agent/tasks.py:41` builds `TaskContext(persona=_persona(user_id))` for the select_orders
path, and `harness/prompt.py:16-17` appends `render_persona(persona)` to the system prompt
whenever a persona is present — task-agnostically. `agent/tests.py::
test_plan_injects_persona_into_system_prompt` asserts it.

**Decision: preserve persona.** harness_v2 gains a `persona.py` module (the
`persona_system.txt` preamble as an inline constant, `render_persona`, plus a `Persona`
TypedDict in `types.py`). The agent composer appends `render_persona(persona)` to
`system_prompt(context)` — mirroring where the old `build_prompt` did it. select_orders
evals keep calling `system_prompt(context)` with no persona, so eval prompts are unchanged.

## Resolved question 2: the `selected` submission contract

`order/utils.py::get_order_data_from_selected` decodes the posted path with exactly the
sequences old `harness/orders.py::option_to_selected` encodes:

| order_type | selected path |
|---|---|
| Hold / Disband | `[source, type]` |
| Build | `[source, Build, unit_type, named_coast?]` |
| Move / MoveViaConvoy | `[source, type, target, named_coast?]` |
| Support / Convoy | `[source, type, aux, target]` |

The new agent-side serializer (`agent/orders.py::option_to_selected`) reproduces this
sequence from harness_v2's flat `OrderOption` (plain-string fields instead of
`{id, label}` dicts). Same branch structure keyed on `common.constants.OrderType`;
`named_coast` appended only when truthy, exactly as today.

## Resolved question 3: output_schema

Old select_orders passes `ORDER_SELECTION_SCHEMA` to `Inference.objects.run`, and
`BOT_LLM_STRUCTURED_OUTPUTS` defaults to True (`project/settings.py:267`), so structured
outputs are live in production. **Decision: preserve.** The schema matches harness_v2's
FORMAT text (`{"reasoning", "choices": [{"source_id", "option_index"}]}`), so it moves
into `harness_v2/tasks/select_orders/schema.py` and the agent composer passes it. Evals
run without enforcement (inspect's plain `generate()`), which is the strictly harder
condition — acceptable, pre-existing drift, recorded here.

## Resolved question 4: shape returned by `fetch_context`

`fetch_context` will return **ApiData** (raw snake_case responses, plus a `channels` key),
with `data_to_context` applied inside the composer, not inside `fetch_context`. Three
forcing reasons:

1. Fallback: ContextError must degrade to first-legal, so raw `orders` must survive a
   failed Context assembly. If `fetch_context` returned Context and died, there would be
   nothing to fall back on.
2. `finalize` reads `game.phase_confirmed` and `_phase()` reads `game.current_phase_id` —
   neither exists on Context.
3. The Phase-1 reply path still runs the old `ReplyTask` and reads
   `phase` / `phase_states` / `channels` — the raw dict satisfies both consumers, since old
   `ContextData` keys are the same api_client payloads.

The raw→Context transform still lives in exactly one place (`harness_v2.adapter.
data_to_context`), invoked from agent. `adapter` gains a public
`orders_to_options(orders) -> list[OrderOption]` (extracted from `data_to_context`, which
then uses it) so the fallback can flatten raw options without a full Context.

## Behavioural deltas accepted (each justified)

- **Parse leniency**: old parse raised ParseError when options existed but no valid
  selection was produced; v2 returns `[]`. The agent's existing missing-unit fill then
  produces first-legal for every source — the submitted orders are identical, so no test
  outcome changes.
- **Strict context assembly**: `data_to_context` will raise `ContextError` on malformed
  data (wrapped `KeyError`/`TypeError`), and agent degrades to first-legal.
  `TestAdjustmentOrderLimit._fake_client` returns skeletal payloads (`{"phase_confirmed":
  False}` for game/variant/phase); its mocks get enriched to a minimal complete ApiData so
  `test_plan_fills_units_missing_from_response_with_first_legal` keeps exercising the fill
  path rather than silently passing via fallback. Justification: the fetch contract
  changed from "blocks tolerate anything" to "adapter validates".
- **max_orders capping** stays in `agent/tasks.py` reading raw
  `phase_states[0]["max_orders"]` (endpoint is filtered to the requesting user —
  `phase/views.py:53` — so `[0]` is the bot's own state), unchanged from today, and works
  even on the fallback path where no Context exists.

## Phase 1 — select_orders composer in agent

- `harness_v2/persona.py` (+ `Persona` in `types.py`); `harness_v2/tasks/select_orders/schema.py`.
- `harness_v2/adapter.py`: extract `orders_to_options`; raise `ContextError` from
  `data_to_context` on malformed data.
- `agent/context.py`: `fetch_context` returns ApiData incl. `channels`.
- `agent/orchestration.py`: keep `run_task` (reply still uses it); add `run_select_orders`
  — `data_to_context` → `system_prompt` + persona append → `user_prompt` →
  `Inference.objects.run(...)` (same phase/member recording, schema) → `parse_completion`.
- `agent/orders.py`: new `option_to_selected` over flat `OrderOption`.
- `agent/fallback.py`: `first_legal_selections(options: list[OrderOption]) ->
  list[OrderOption]` (first option per source).
- `agent/tasks.py`: select_orders path catches `(ContextError, InferenceError,
  ParsingError)` → fallback; missing-unit fill and cap logic keyed on
  `option["source"]`; serialize via `option_to_selected` at submit time. Reply path
  untouched (old harness).

Gate: `python -m pytest agent -v` green; `inspect eval
harness_v2/tasks/select_orders/evals.py --model mockllm/model` runs end-to-end (negative
control: mock completions parse to nothing and score INCORRECT, proving scorers bind to
the production parse).

## Phase 2 — reply in harness_v2

- Grow `Context` with `channels` (safe empty default in `data_to_context` via
  `data.get("channels", [])`) and `ApiData` with the channel payload type; canonical
  channel shape: `{id, name, private, messages: [{sender_nation|sender_name, body}]}`.
- `harness_v2/tasks/reply/`: `system_prompt.py` (old `system.txt` text + persona handled
  by composer), `user_prompt.py` (game state + identity + the target channel's
  conversation, `user_prompt(context, channel_id)`), `parser.py`
  (`parse_completion(completion) -> str | None`, empty → None), `schema.py` (REPLY_SCHEMA).
- `agent/orchestration.py`: replace `run_task` with `run_reply`; `agent/tasks.py::reply`
  repointed; message-cap check and truncation stay in agent, unchanged.

Gate: reply tests green — cap, truncation, empty-message silence, inference-failure
silence, persona injection ("Voice governs how you communicate" must appear: the preamble
constant carries it).

## Phase 3 — drop old harness

- Grep proves zero `from harness.` / `from harness ` importers.
- Remove `"harness"` from `INSTALLED_APPS`; `git rm -r service/harness`.
- `run_evals` dies with the app. Follow-up flagged (not in this PR): a replacement entry
  point for running harness_v2 evals against the real model (plain `inspect eval` CLI
  covers dev use; a management command would need app registration, which we are not
  keeping).
- Old `harness/tests.py` scorer/parse coverage is re-established as
  `harness_v2/tests.py` unit tests against the v2 parser/scorers (pytest discovers plain
  packages; no app registration needed), so deleting the app does not silently drop
  coverage of behaviour that lives on in v2.

Gate: `python -m pytest agent harness_v2 -v` green; `manage.py check` clean.

## Phase 4 — rename harness_v2 → harness

- `mv service/harness_v2 service/harness` (+ `git add`; harness_v2 was never committed).
- Rewrite `harness_v2.` → `harness.` imports across `service/` (package-internal, agent,
  tests), `docker-compose.yml` codegen output path, `CLAUDE.md` references.
- `generated/api.py` moves with the tree; regenerate only if codegen must prove the new
  path (the file content is path-independent — just the output location changes).
- Stays a plain package: no models, no management commands, so no `apps.py` /
  `INSTALLED_APPS` entry.

Final gate: `python -m pytest agent harness -v` green; `manage.py check` clean; grep shows
no `harness_v2`, no `harness.tasks import Reply/SelectOrders`, no `harness.prompt`;
`black --check` clean on touched files.

## What moved where (running list for the PR)

| Old | New |
|---|---|
| `harness.prompt.build_prompt` + `TaskContext` | agent composer (`agent/orchestration.py`) |
| `harness.orders.option_to_selected` | `agent/orders.py` (flat-string serializer) |
| `harness.types.Persona` / `blocks.persona` | `harness_v2/types.py` + `harness_v2/persona.py` |
| `harness.tasks.select_orders` (blocks + schema) | `harness_v2/tasks/select_orders/` (already present; + `schema.py`) |
| `harness.tasks.reply` | `harness_v2/tasks/reply/` (Phase 2) |
| `harness.exceptions.ParseError` | `harness_v2.exceptions.ParsingError` (+ `ContextError` now load-bearing) |
| `harness.evals` + `run_evals` command | `harness_v2` inspect evals; runner entry point flagged as follow-up |
| `harness/tests.py` | `harness_v2/tests.py` (Phase 3 port) |
