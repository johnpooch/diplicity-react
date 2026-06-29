# Bot Telemetry & Observability — Prior Art and Recommendation

Research and design notes for the LLM-bot telemetry/observability layer. Two goals drive
everything below:

1. **Cost / token visibility** — see cost and token usage per call, per bot, per phase, per
   game, and in aggregate over time.
2. **See the bots think, in real time** — watch a bot's transcripts, reasoning, and internal
   state (diary, agenda, provisional vs. final orders) as a phase unfolds.

Every factual claim is tagged **VERIFIED** (read from source — repo file or official doc) or
**INFERRED / SECONDARY** (deduced, or from a comparison article). Source URLs and file paths
are inline.

---

## 0. Where we are today (verified from this repo)

The `bot` app already runs a per-phase loop via Procrastinate tasks, but records **no
telemetry at all**. The relevant facts, read from source:

- `service/bot/llm_client.py:22` — `LLMClient.run()` calls
  `self._client.messages.create(...)`, iterates `message.content` for the tool-use block, and
  returns the parsed result. It **discards `message.usage`** entirely. The token data we need
  for cost tracking is already on the response object and is being thrown away.
- The Anthropic SDK (`anthropic==0.113.0`, installed) exposes on `message.usage`:
  `input_tokens`, `output_tokens`, `cache_creation_input_tokens`, `cache_read_input_tokens`,
  `cache_creation`, `output_tokens_details`, `server_tool_use`, `service_tier`. (VERIFIED via
  `anthropic.types.Usage.model_fields`.) This is exactly the cache-aware split cost tracking
  needs.
- Model + key come from settings: `BOT_LLM_MODEL` (default `claude-haiku-4-5`) and
  `ANTHROPIC_API_KEY` (`service/project/settings.py:261-262`). The client is a thin, swappable
  wrapper — the single call site is `LLMClient(settings.ANTHROPIC_API_KEY).run(action)`.
- Tasks (`service/bot/tasks.py`, all `@app.task(... retry=3)`): `bot.plan`, `bot.finalize`,
  `bot.reply`, signatures `(user_id, game_id[, channel_id])`. The richer **Plan → Negotiate →
  Commit** loop with diary/agenda/trust described in the design brief is **aspirational** —
  current code is plan/finalize/reply with no diary. The schema below is designed for the
  aspirational shape but degrades gracefully to today's code.
- `service/bot/models.py` is **empty** (no models yet) — a clean slate for a telemetry model.
- The bot acts as a `User`; `Member` links user↔game↔nation
  (`service/member/models.py:8-11`). FK targets for telemetry: `Game.id` is a
  `CharField(primary_key=True)` slug (`service/game/models.py:356`); `Phase` and `Member` have
  default integer PKs; all inherit `BaseModel` (`created_at`/`updated_at`,
  `service/common/models.py`).

**Implication:** the single highest-leverage change is to capture `message.usage` at
`llm_client.py:35` and write a row. Everything else is built on that.

---

## 1. Prior-art summary

### 1a. Every's `AI_Diplomacy` (`EveryInc/AI_Diplomacy`) — the closest reference

Off-the-shelf LLMs negotiate, keep a private diary, track a discrete trust scale, and emit
validated orders. This is the nearest neighbour to what we're building.

**LLM-call logging — a single flat CSV, `llm_responses.csv`.** (VERIFIED)
- Path built per run in `lm_game.py`: `os.path.join(run_dir, "llm_responses.csv")`, where
  `run_dir = f"./results/{timestamp_str}"`.
  ([lm_game.py](https://github.com/EveryInc/AI_Diplomacy/blob/main/lm_game.py))
- Writer is `log_llm_response()` in
  [`ai_diplomacy/utils.py`](https://github.com/EveryInc/AI_Diplomacy/blob/main/ai_diplomacy/utils.py)
  (`csv.DictWriter`, `QUOTE_ALL`). **Schema (verified):**

  ```
  ["timestamp", "model", "power", "phase", "response_type", "raw_input", "raw_response", "success"]
  ```

  `power` = power name or `"game"`; `phase` e.g. `S1901M`; `raw_input` = full prompt;
  `raw_response` = full completion; `success` is a **free-text string** ("Success" / "Failure:
  …"), not a boolean.
- `response_type` is the primary categorical dimension. Verified literals:
  `order_generation`, `negotiation_message`, `negotiation_diary`, `order_diary`,
  `phase_result_diary`, `diary_consolidation`, `state_update` (+ `state_update_*` error
  variants).
- **Crucially, no token counts and no cost are recorded.** Every client's
  `generate_response(...) -> str` returns bare text and never inspects `response.usage`; a
  source comment literally says *"token_usage and cost can be added later if available."*
  ([clients.py](https://github.com/EveryInc/AI_Diplomacy/blob/main/ai_diplomacy/clients.py))
  This is the single biggest gap in the closest prior art — and the easiest thing for us to do
  better, since (§0) our `usage` object is right there.

**Diary / reasoning / trust** lives on a `DiplomacyAgent` instance per power
([agent.py](https://github.com/EveryInc/AI_Diplomacy/blob/main/ai_diplomacy/agent.py)).
(VERIFIED)
- `goals: List[str]`; `relationships: Dict[str, str]` (power → label). **Trust scale is a
  fixed 5-point ordinal:** `["Enemy", "Unfriendly", "Neutral", "Friendly", "Ally"]`.
- Three diary stores: `full_private_diary` (permanent, append-only, phase-prefixed),
  `private_diary` (the LLM-context version, periodically consolidated), `private_journal`
  (debug).
- Diary entries are themselves LLM calls returning JSON, then parsed. The JSON contracts
  (verified): negotiation diary → `negotiation_summary`, `intent`, `relationship_updates`,
  `goals`; order diary → `order_summary`; state update → `updated_goals`,
  `updated_relationships`. Older entries are summarized into a single `"[CONSOLIDATED
  HISTORY]"` line by `run_diary_consolidation`
  ([diary_logic.py](https://github.com/EveryInc/AI_Diplomacy/blob/main/ai_diplomacy/diary_logic.py)).

**Replay UI — a full React/Vite/Three.js frontend at `ai_animation/`.** (VERIFIED) It loads
`./games/${id}/game.json` + optional `moments.json`, validated with **Zod**. The replay game
JSON (verified TS in
[`gameState.ts`](https://github.com/EveryInc/AI_Diplomacy/blob/main/ai_animation/src/types/gameState.ts)):

```ts
GamePhase = {
  messages: { sender, recipient, time_sent, phase, message }[];
  name: string;                                  // "S1901M"
  orders:  Record<Power, string[] | null>;
  results: { A: …; F: … };
  state:   { units, centers, homes, influence };
  year?: number;
  summary?: string;                              // phase narrative
  agent_relationships?: Record<Power, Record<Power, RelationshipStatus>>;
}
```

A **`moments.json`** analytics layer (verified Zod in
[`moments.ts`](https://github.com/EveryInc/AI_Diplomacy/blob/main/ai_animation/src/types/moments.ts))
powers betrayal/lie callouts: `MomentSchema` with `category` (BETRAYAL, PLAYING_BOTH_SIDES,
…), `promise_agreement` vs `actual_action`, `interest_score` (0–10), `powers_involved`; plus a
`LieSchema` (`promise`, `diary_intent`, `actual_action`, `intentional`). This is computed
**after** the game from the raw logs — a derived analytics table, not write-time telemetry.

**In-memory phase record** (verified dataclasses,
[`game_history.py`](https://github.com/EveryInc/AI_Diplomacy/blob/main/ai_diplomacy/game_history.py))
keeps a distinction we should copy: `submitted_orders_by_power` (raw model output) vs
`orders_by_power` (validated/accepted) — the basis of an "invalid-order rate" metric (mirrored
by `invalid_moves_by_model` in `moments.json`).

**Directly reusable for us:** the `llm_responses.csv` columns map almost 1:1 to an `LLMCall`
table (just add the token/cost fields they punted on, and make `success` a real enum); the
`response_type` taxonomy is a ready-made `stage`/`kind` vocabulary; the diary JSON contract is
a good `DiaryEntry` shape; the 5-point trust enum + `power→power→status` matrix are clean
Metabase facets; `moments.json` is a model for a post-game "interesting events" dashboard built
by a periodic job.

### 1b. Cicero (`facebookresearch/diplomacy_cicero`)

Cicero is an RL/search agent (not an off-the-shelf-LLM agent), so its *value* is architectural,
not copy-paste. The key pattern: **two-tier persistence** that keeps the durable game record
clean of model internals and puts reasoning in a separate sidecar.

- **Game JSON** (the `diplomacy`/`dipcc` save format, serialized by `Game::to_json()` in
  [`dipcc/dipcc/cc/game.cc`](https://github.com/facebookresearch/diplomacy_cicero/blob/main/dipcc/dipcc/cc/game.cc)):
  top-level `version, id, map, scoring_system, is_full_press, phases, metadata`; per-phase
  `name, state, orders, messages, results, logs`. `message` fields (verified in
  [`json.cc`](https://github.com/facebookresearch/diplomacy_cicero/blob/main/dipcc/dipcc/cc/json.cc)):
  `sender, recipient, phase, message, time_sent`. This is the upstream
  [`diplomacy` package](https://github.com/diplomacy/diplomacy/blob/master/diplomacy/utils/export.py)
  `to_saved_game_format` schema, extended. (VERIFIED)
- **Reasoning sidecar — `MetaAnnotator`, append-only JSONL**, one `RawRecord` per line
  ([`fairdiplomacy/viz/meta_annotations/annotator.py`](https://github.com/facebookresearch/diplomacy_cicero/blob/main/fairdiplomacy/viz/meta_annotations/annotator.py)).
  (VERIFIED) Record shape:

  ```
  RawRecord { pointer: GamePointer, tag: str, version: int, json_data: str }
  GamePointer { phase: str, timestamp: Optional[int], datetime: str, phase_hash: str }
  ```

  - `phase_hash = game.compute_order_history_hash()` keys every annotation to an exact game
    state, so the sidecar can be replayed against the game JSON even though it's written
    out-of-order.
  - Sentinel timestamps `NEXT_MSG = -100` / `LAST_MSG = -101` let an annotation attach to a
    message **before it exists** — record the *plan*, then bind it when the message lands.
  - Tags include `"pseudoorders"` (predicted orders for all powers — the plan behind the next
    message), `"MESSAGE_FILTERED_TAG"` with `bad_tags` (**why** a candidate message was
    rejected), and a generic `add_dict_*(data, tag, version)` escape hatch that JSON-stringifies
    any dict. Callers are in
    [`parlai_message_handler.py`](https://github.com/facebookresearch/diplomacy_cicero/blob/main/fairdiplomacy/agents/parlai_message_handler.py).
- **Search internals** (CFR policies/values/regrets) are surfaced via Python `logging` only —
  unstructured text, **not** persisted to a queryable artifact. (VERIFIED that they're logged;
  INFERRED that they're not durably stored.) A gap, not a model to copy.
- **Released transcripts:** `data/cicero_redacted_games/` ships 40+ real game JSONs in the same
  schema (dialogue redacted to consenting players). (VERIFIED)

**Directly reusable for us:** the two-tier split (clean episode record + separate reasoning
stream); keying every telemetry row back to the episode with a `{phase, content_hash}` pointer;
forward-referencing a plan before the message exists; and **recording rejected candidates with
reasons**, not just accepted output.

### 1c. What the two references teach, contrasted

| Concern | AI_Diplomacy | Cicero | Takeaway for us |
|---|---|---|---|
| Per-call log | flat CSV, **no tokens/cost** | none (text logs) | Build the call log they didn't — with tokens/cost |
| Reasoning store | diary JSON on agent | JSONL sidecar keyed by phase_hash | Store diary as structured rows keyed to phase + stage |
| Accepted vs rejected | keeps submitted vs validated orders | logs filtered-message reasons | Record provisional→final and rejected candidates |
| Replay | React frontend over game.json + moments.json | HTML over game JSON | A simple web page over our Postgres rows |
| Trust model | 5-point ordinal enum + matrix | n/a | Adopt the ordinal enum + per-phase relationship edges |
| Analytics | post-game `moments.json` job | redacted released games | Derive "interesting events" in a periodic job, not write-time |

---

## 2. Best-practice synthesis (LLM observability & cost tracking)

### 2a. Per-call cost / token tracking

**OpenTelemetry GenAI semantic conventions** (official, *experimental*) standardize the
attribute names — worth adopting as field names even if we never run an OTel collector.
(VERIFIED against the
[OTel registry](https://opentelemetry.io/docs/specs/semconv/registry/attributes/gen-ai/) and
[GenAI spans doc](https://opentelemetry.io/docs/specs/semconv/gen-ai/gen-ai-spans/).)

- `gen_ai.operation.name` (`chat`, `embeddings`, `execute_tool`, `invoke_agent`, …),
  `gen_ai.provider.name` (renamed from `gen_ai.system`: `anthropic`, `openai`, …),
  `gen_ai.request.model` / `gen_ai.response.model`.
- Usage: `gen_ai.usage.input_tokens`, `gen_ai.usage.output_tokens`,
  `gen_ai.usage.cache_read.input_tokens`, `gen_ai.usage.cache_creation.input_tokens`,
  `gen_ai.usage.reasoning.output_tokens`.
- Correlation: `gen_ai.conversation.id` (session/thread), `gen_ai.response.id`,
  `gen_ai.response.finish_reasons`.
- **There is no cost attribute in the OTel GenAI registry** — it tracks tokens only; cost is
  left to the backend to compute. (VERIFIED) This is precisely the gap we fill in Metabase.
- Prompt/response content is **opt-in and off by default** (it can be sensitive), gated by
  `OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT`. The old `gen_ai.prompt`/`gen_ai.completion`
  attributes are **deprecated** in favour of `gen_ai.input.messages`/`gen_ai.output.messages`.

**Purpose-built tools — what they record and whether they fit our stack.** (VERIFIED against
each project's docs.)

| Tool | Self-host? | Free/OSS? | Storage | Fit for Postgres+Metabase |
|---|---|---|---|---|
| **Roll-your-own Postgres table + Metabase** | yes | yes | Postgres | **Best fit** |
| **LiteLLM proxy** | yes | OSS | **Postgres** | **Good** — already writes cost/token rows to Postgres |
| **Phoenix (Arize)** | yes | OSS | SQLite/Postgres | Good — OTel-native, has `llm.cost.*`, LLM-as-judge evals |
| **Helicone** | yes | Apache-2.0 | own | Good if you want a proxy; lightweight |
| **Langfuse** | yes | OSS (confirm MIT vs Apache) | **Postgres + ClickHouse** | Partial — ClickHouse mandatory, heavy for a hobby box |
| **LangSmith** | enterprise only | No (SaaS) | n/a | Poor for hobby self-host |

- **Langfuse** data model: `trace` → `observations` of type `span`/`event`/`generation`; a
  `generation` carries model, prompt, completion, input/output/cached token counts, cost,
  latency. Cost from per-model **per-usage-type** price tables. **Self-hosting now requires
  ClickHouse in addition to Postgres** — heavier than our box wants.
  ([token-and-cost-tracking](https://langfuse.com/docs/observability/features/token-and-cost-tracking),
  [clickhouse requirement](https://langfuse.com/self-hosting/deployment/infrastructure/clickhouse))
- **Phoenix / OpenInference** carries cost **on the span** via the `llm.cost.*` attribute group
  (`llm.cost.prompt`, `llm.cost.completion`, `llm.cost.total`), and token detail via
  `llm.token_count.prompt_details.cache_read` / `cache_write`. OTLP ingest + auto-instrumentation
  for Anthropic/OpenAI. ([OpenInference spec](https://arize-ai.github.io/openinference/spec/semantic_conventions.html))
- **LiteLLM proxy**: a built-in price DB → per-request cost, an `x-litellm-response-cost`
  header, and rows (key, user, model, prompt/completion/total tokens, spend USD) written to
  **Postgres** you can point Metabase straight at.
  ([cost_tracking](https://docs.litellm.ai/docs/proxy/cost_tracking))

**Proxy/gateway accounting** (Helicone, LiteLLM, OpenRouter, Cloudflare AI Gateway) sits in the
request path, reads the provider `usage`, multiplies by a price table, logs a row — zero app
telemetry code. (VERIFIED) **OpenRouter** even returns `cost`, `cached_tokens`,
`cache_write_tokens`, `cache_discount` in its `usage` object
([usage-accounting](https://openrouter.ai/docs/guides/guides/usage-accounting)).
*Trade-off:* lowest friction, but it's another hop and it can't attribute cost to internal
concepts (which game, which phase, which Procrastinate stage) **unless you thread metadata
through headers**. In-app logging is the inverse — more wiring, but you record exactly the
domain FKs you want, which is what suits Django + Metabase.

**The recurring per-call record** (synthesised across OTel, OpenInference, Langfuse, LiteLLM,
OpenRouter): identity (model, provider, operation) · tokens (input, output, total, cache-read,
cache-write, reasoning) · cost (input, output, total USD) · timing (start, end, latency) ·
correlation (trace/span id, conversation/session id, user) · metadata/tags · status/error ·
opt-in content (prompt, completion). This is **one wide table**.

### 2b. Cost computation & the caching subtlety

The universal recipe: **`cost = Σ (tokens_of_type × price_per_token_of_that_type)`** using a
per-model, **per-usage-type** price table. Raw Anthropic/OpenAI responses **do not** include
cost (OpenRouter and Cloudflare do); you compute it.

**Cached input tokens are priced differently and must be tracked separately** (VERIFIED the
split exists in the SDK; SECONDARY for the multipliers, which drift — confirm against the
provider page and the repo's `claude-api` skill before hard-coding):
- Anthropic: cache **reads ≈ 0.1× input (90% off)**; cache **writes 1.25× input** (5-min TTL) or
  **2× input** (1-hour TTL).
- OpenAI: cached reads ~0.1–0.5× input depending on model.

So the cost row needs **four input-side multipliers**: uncached input, cache-read input,
cache-write input, and output. Store `cache_read_input_tokens` and `cache_creation_input_tokens`
(both on our `message.usage`) as separate columns. This matters a lot for us specifically: the
shared game context (board state, rules, history) is large and repeated across the Plan →
Negotiate → Commit calls within a phase — exactly the case prompt caching is designed for, so
the cached/uncached split is where the real cost signal lives.

### 2c. Exposing agent reasoning / transcripts

Recurring patterns across the references and tools:
- **Trace/span tree** keyed by a conversation/session id (OTel `gen_ai.conversation.id`,
  Langfuse `trace`, Phoenix spans). For us, the natural session key is `(game, phase, bot)`.
- **Two-tier persistence** (Cicero): clean episode record + separate reasoning stream keyed back
  by a pointer.
- **Structured diary entries** (AI_Diplomacy): reasoning as parseable JSON rows, not prose blobs.
- **Record rejected candidates with reasons** (Cicero `MESSAGE_FILTERED_TAG`).
- **Derived analytics built post-hoc** (AI_Diplomacy `moments.json`), not at write time.

---

## 3. Concrete recommendation for our stack

**Headline:** build it yourself in Postgres + Metabase. The per-call record is one small,
well-defined table (§2a); OTel GenAI has no cost field anyway, so an external tracer buys us
little; Langfuse self-host now drags in ClickHouse; and our `message.usage` already carries the
cache-aware token split that's the whole point. Adopt OTel/OpenInference *field names* so the
schema stays portable, and keep the door open to emitting OTLP later. Three Django models, one
service-side change at `llm_client.py`, Metabase for cost, a thin Django page for live
inspection.

### 3a. The LLM-call record (`bot.LLMCall`)

One wide row per call, written in `LLMClient.run()` right where `message.usage` is currently
discarded. Proposed fields (names mirror OTel GenAI / OpenInference for portability):

| Field | Type | Notes |
|---|---|---|
| `id` | BigAuto / UUID | PK |
| `created_at` / `updated_at` | from `BaseModel` | |
| **Correlation** | | |
| `game` | FK → `game.Game` (slug PK), `null=True` | the episode |
| `phase` | FK → `phase.Phase`, `null=True` | the turn |
| `member` | FK → `member.Member`, `null=True` | which bot/nation |
| `stage` | CharField + `CHOICES` | `plan` / `negotiate` / `commit` / `reply` — the `response_type` analogue |
| `action_name` | CharField | `select_order`, `reply`, … (from `Action.name`) |
| `request_id` | CharField, `null=True` | provider `response.id` for cross-ref |
| **Identity** | | |
| `provider` | CharField | `anthropic` (→ `gen_ai.provider.name`) |
| `request_model` | CharField | `settings.BOT_LLM_MODEL` |
| `response_model` | CharField, `null=True` | `message.model` (may differ) |
| `operation` | CharField | `chat` (→ `gen_ai.operation.name`) |
| **Tokens** | | |
| `input_tokens` | IntegerField | `usage.input_tokens` |
| `output_tokens` | IntegerField | `usage.output_tokens` |
| `cache_read_input_tokens` | IntegerField, default 0 | `usage.cache_read_input_tokens` |
| `cache_write_input_tokens` | IntegerField, default 0 | `usage.cache_creation_input_tokens` |
| **Cost (USD)** | | |
| `cost_input` / `cost_output` / `cost_cache_read` / `cost_cache_write` | DecimalField | computed from a price table; keep components |
| `cost_total` | DecimalField | sum; the headline number |
| `price_version` | CharField | which price table produced this (rates drift) |
| **Timing / status** | | |
| `latency_ms` | IntegerField | wall-clock around the call |
| `status` | CharField + `CHOICES` | `success` / `error` (a real enum — AI_Diplomacy's free-text `success` is a trap) |
| `error` | TextField, `null=True` | exception text on failure |
| `finish_reason` | CharField, `null=True` | `message.stop_reason` |
| **Content (opt-in)** | | |
| `prompt` | JSONField, `null=True` | messages array — gated by a setting (see §3d) |
| `response` | JSONField, `null=True` | tool input / completion — gated |
| `metadata` | JSONField, default `{}` | tags / escape hatch (Cicero's `add_dict`) |

Notes:
- **Cost is computed in Django, not stored by the provider.** Keep a small price table keyed by
  `(model, usage_type, price_version)` — a constants dict or a tiny `LLMPrice` model. Store the
  component costs *and* `cost_total` so Metabase doesn't recompute, and stamp `price_version` so
  a later rate change doesn't silently rewrite history. Confirm rates via the `claude-api` skill.
- **Make `status` an enum**, per the repo's class-based `CHOICES` convention
  (`service/common/constants.py`).
- Index `(game, phase)`, `(member, created_at)`, `(stage, created_at)` for the dashboards.
- This is independent of the swappable client: when production moves to the managed Qwen
  endpoint, the same row is written — only `provider`/`request_model` and the price table change.

**Metabase wiring (goal 1).** Metabase queries Postgres directly (per CLAUDE.md), so the table is
immediately dashboard-ready. Native-SQL cards (the project already documents the base64 MCP flow
for these): cost per game (`SUM(cost_total) GROUP BY game_id`), cost per phase over time
(bucket by `phase.scheduled_resolution`, **not** `updated_at` — per the CLAUDE.md schema gotcha),
cost per stage (`GROUP BY stage`), tokens in/out and **cache hit rate**
(`cache_read_input_tokens / NULLIF(input_tokens + cache_read_input_tokens, 0)`), and a rolling
daily spend line. Cache hit rate is the single most actionable cost lever given the large shared
context.

### 3b. Diary / reasoning / internal state (`bot.DiaryEntry`)

Capture the bot's evolving internal state as **structured rows keyed to `(member, phase,
stage)`**, mirroring AI_Diplomacy's diary JSON contract but normalized into Postgres rather than
a per-agent in-memory list.

| Field | Type | Notes |
|---|---|---|
| `member` / `phase` | FKs | whose diary, which turn |
| `stage` | CharField + `CHOICES` | `plan` / `negotiate` / `commit` |
| `kind` | CharField + `CHOICES` | `negotiation_summary` / `order_summary` / `state_update` / `consolidation` (AI_Diplomacy's `response_type` vocabulary) |
| `summary` | TextField | the narrative entry |
| `intent` | TextField, `null=True` | from the negotiation-diary contract |
| `goals` | JSONField, default `[]` | `List[str]` |
| `llm_call` | FK → `LLMCall`, `null=True` | the call that produced it (ties reasoning ↔ cost) |

Plus a small **relationship/trust** table for the per-phase `power→power` matrix, using the
verified 5-point ordinal enum (`Enemy/Unfriendly/Neutral/Friendly/Ally`):

`bot.Relationship { member (FK), phase (FK), toward_nation (FK → nation.Nation), status (CharField + CHOICES) }`

— one row per (bot, phase, other-nation). This is a clean Metabase facet (trust drift over time)
and a clean UI feed.

**Provisional vs. final orders.** Adopt AI_Diplomacy's `submitted` vs `validated` distinction and
Cicero's plan-before-commit: record the Plan stage's **provisional** orders and the Commit
stage's **final** orders (each as a `DiaryEntry` of `kind='order_summary'` or a dedicated small
table), so the inspector can show provisional → final diff and we can compute an invalid/changed-
order rate.

### 3c. Real-time inspection web page (goal 2)

**Recommendation: build a thin Django-rendered page, not adopt a tool.** Rationale, evidence-
based:
- The data already lives in our Postgres; a tool (Langfuse/Phoenix) means standing up a second
  service (Langfuse drags in ClickHouse) and double-writing — disproportionate for a hobby box.
- The DRF API + React frontend already exist; a read-only inspector is a small addition.
- AI_Diplomacy's elaborate Three.js `ai_animation` is for a public stream, not live debugging —
  over-scoped for "watch a bot think."

Simplest viable build:
1. **Read model:** a DRF read endpoint (e.g. `/game/<id>/bot-trace/`) that returns, for the
   current phase: the `LLMCall` rows (stage, tokens, cost, latency, status, and — when content
   capture is on — prompt/response), the `DiaryEntry` rows, the `Relationship` matrix, and
   provisional vs final orders. Reuse the existing `serializers.Serializer` + thin-view
   conventions.
2. **"Real-time" without infrastructure:** the writes happen in **Procrastinate** worker tasks,
   not the request cycle, so the web tier can't push events. The pragmatic path is **short-
   interval polling** from a React inspector screen (e.g. refetch every 2–5 s while a phase is
   active) — trivial with the existing React Query setup, no WebSocket/Channels/Redis needed.
   Because each LLM call commits its row as the stage completes, polling surfaces Plan, then
   Negotiate, then Commit as they land — which is exactly "watch it think" at phase granularity.
   *If* sub-second liveness is ever needed, revisit Django Channels or Postgres `LISTEN/NOTIFY`;
   it isn't needed for v1, and adding it now violates the repo's "simplicity is correctness"
   tenet.
3. **Frontend:** a Suspense screen following the repo's wrapper pattern (`ScreenContainer` +
   `ScreenHeader` + `QueryErrorBoundary` + `Suspense`), one panel per stage, a token/cost
   strip per call, the diary feed, and the trust matrix. Gate it behind game-master / staff so
   transcripts aren't exposed to opponents mid-game (a bot's diary is hidden information).

This satisfies goal 2 with the smallest surface: three models, one read endpoint, one polling
screen — and it reuses cost rows from §3a verbatim.

### 3d. Pitfalls — cost, privacy, storage volume

- **Storing full prompts when context is large and cached is the main storage trap.** The shared
  game context (board, rules, history) is large and repeats across Plan/Negotiate/Commit; naively
  persisting every full `prompt` per call duplicates megabytes per phase and dwarfs the metrics.
  Mitigations: (a) **always store token counts + cost** (cheap, the metrics that matter), and make
  full prompt/response capture **opt-in** via a setting (mirrors OTel's content-capture-off-by-
  default); (b) when capturing, store the **shared context once per phase** and only the
  per-call delta on each `LLMCall`, rather than the full prompt every time; (c) optionally retain
  full content only for in-progress / recent games and prune older rows to counts+cost.
- **Privacy / hidden information.** A bot's diary, agenda, and provisional orders are secret game
  state. The inspector must be access-controlled (game master / staff only) so it can't leak
  another player's plans mid-game. Use the existing permission classes (`IsGameMaster`, staff
  checks).
- **Cost-table drift.** Provider per-token rates change; cached-read/write multipliers especially.
  Stamp `price_version` on every row and never recompute historical cost in place — otherwise a
  rate change silently rewrites past dashboards.
- **PII / secrets in prompts.** Negotiation text is user-generated chat; treat captured content as
  sensitive (retention limits, access control), consistent with OTel keeping content opt-in.
- **Write-path safety.** Telemetry must never break a turn. Wrap the row write so a logging failure
  is swallowed (log-and-continue), and prefer `transaction.on_commit` for any derived side-effects
  — the bot submitting orders is the contract; telemetry is best-effort.
- **Volume of negotiation calls.** The Negotiate stage can fan out per channel/message window, so
  `LLMCall` rows will dominate. Index for the dashboards (§3a) and consider a retention/rollup job
  (a Procrastinate periodic task) that aggregates old per-call rows into daily per-game/per-stage
  summaries — the same "derive analytics in a job" pattern as AI_Diplomacy's `moments.json`.

---

## 4. Pressure-testing the original half-formed plan

The brief's plan was: *(a) a Django model to record each LLM call, (b) visualize tokens in
Metabase, (c) a simple web page for transcripts/reasoning.* Verdict: **the shape is right** —
the prior art and the tool landscape both converge on exactly this for a Postgres+Metabase stack.
Refinements the evidence adds:

1. **Capture the `usage` object you're already discarding** (`llm_client.py:35`) — including the
   **cache-read/cache-write split**, which is where the real cost signal lives given the large
   shared context. AI_Diplomacy proves how easy it is to ship without this and regret it.
2. **Compute and store cost in Django** (provider responses omit it), with a versioned price table
   and component costs — don't make Metabase do token×price math, and don't let rate changes
   rewrite history.
3. **Make `status` a real enum, not free text** (AI_Diplomacy's string `success` is a known
   smell).
4. **Two-tier the storage** (Cicero): a clean `LLMCall` metrics table + a structured `DiaryEntry`/
   `Relationship` reasoning store keyed to `(member, phase, stage)`, with an FK from diary → the
   call that produced it.
5. **"Real-time" = polling, not sockets** — the writes are in Procrastinate workers; React Query
   polling every few seconds is the simplest thing that delivers "watch it think" without new
   infrastructure.
6. **Adopt OTel/OpenInference field names** so the schema stays portable and could emit OTLP to
   Phoenix later without a rewrite — but **don't adopt a tool now**; build-your-own is the correct
   call for a hobby budget on this stack.
7. **Gate transcript content** behind opt-in capture (storage) and access control (privacy).

---

## Appendix — source index

**Repos (read from source):**
- AI_Diplomacy: [lm_game.py](https://github.com/EveryInc/AI_Diplomacy/blob/main/lm_game.py) ·
  [utils.py](https://github.com/EveryInc/AI_Diplomacy/blob/main/ai_diplomacy/utils.py) ·
  [clients.py](https://github.com/EveryInc/AI_Diplomacy/blob/main/ai_diplomacy/clients.py) ·
  [agent.py](https://github.com/EveryInc/AI_Diplomacy/blob/main/ai_diplomacy/agent.py) ·
  [diary_logic.py](https://github.com/EveryInc/AI_Diplomacy/blob/main/ai_diplomacy/diary_logic.py) ·
  [game_history.py](https://github.com/EveryInc/AI_Diplomacy/blob/main/ai_diplomacy/game_history.py) ·
  [gameState.ts](https://github.com/EveryInc/AI_Diplomacy/blob/main/ai_animation/src/types/gameState.ts) ·
  [moments.ts](https://github.com/EveryInc/AI_Diplomacy/blob/main/ai_animation/src/types/moments.ts)
- Cicero: [game.cc](https://github.com/facebookresearch/diplomacy_cicero/blob/main/dipcc/dipcc/cc/game.cc) ·
  [json.cc](https://github.com/facebookresearch/diplomacy_cicero/blob/main/dipcc/dipcc/cc/json.cc) ·
  [annotator.py](https://github.com/facebookresearch/diplomacy_cicero/blob/main/fairdiplomacy/viz/meta_annotations/annotator.py) ·
  [api.py](https://github.com/facebookresearch/diplomacy_cicero/blob/main/fairdiplomacy/viz/meta_annotations/api.py) ·
  [datatypes.py](https://github.com/facebookresearch/diplomacy_cicero/blob/main/fairdiplomacy/viz/meta_annotations/datatypes.py) ·
  [parlai_message_handler.py](https://github.com/facebookresearch/diplomacy_cicero/blob/main/fairdiplomacy/agents/parlai_message_handler.py)
- Upstream format: [diplomacy/utils/export.py](https://github.com/diplomacy/diplomacy/blob/master/diplomacy/utils/export.py)

**Standards / tools (official docs):**
- OTel GenAI: [attribute registry](https://opentelemetry.io/docs/specs/semconv/registry/attributes/gen-ai/) ·
  [spans](https://opentelemetry.io/docs/specs/semconv/gen-ai/gen-ai-spans/) ·
  [blog primer](https://opentelemetry.io/blog/2024/otel-generative-ai/)
- Langfuse: [token-and-cost](https://langfuse.com/docs/observability/features/token-and-cost-tracking) ·
  [ClickHouse requirement](https://langfuse.com/self-hosting/deployment/infrastructure/clickhouse)
- Phoenix / OpenInference: [semantic conventions](https://arize-ai.github.io/openinference/spec/semantic_conventions.html) ·
  [repo](https://github.com/Arize-ai/openinference)
- Helicone: [cost tracking](https://docs.helicone.ai/guides/cookbooks/cost-tracking) ·
  [self-hosting](https://www.helicone.ai/blog/self-hosting-launch)
- LiteLLM: [cost tracking](https://docs.litellm.ai/docs/proxy/cost_tracking)
- OpenRouter: [usage accounting](https://openrouter.ai/docs/guides/guides/usage-accounting)
- Cloudflare AI Gateway: [analytics](https://developers.cloudflare.com/ai-gateway/observability/analytics/)
- Caching cost (secondary, verify before hard-coding):
  [prompt caching comparison](https://www.prompthub.us/blog/prompt-caching-with-openai-anthropic-and-google-models)
- Write-ups: [Traceloop — bills to budgets](https://www.traceloop.com/blog/from-bills-to-budgets-how-to-track-llm-token-usage-and-cost-per-user) ·
  [LiteLLM + Postgres tracking](https://medium.com/@hithasrinivas4/tracking-llm-usage-spend-with-litellm-postgresql-and-litellm-ui-8ca9e6773f17)
