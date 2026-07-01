# Gap Analysis: Diplicity Bots vs. AI_Diplomacy

This is the index for a set of implementation-ready design documents comparing the current
bot implementation (`service/bot/`) against the intended design
(`service/bot/docs/TECHNICAL_DESIGN.md`) and the reference implementation,
[GoodStartLabs/AI_Diplomacy](https://github.com/GoodStartLabs/AI_Diplomacy). Each gap doc is
independently implementable in roughly one PR and contains its own evidence, design, cost
analysis, scope boundaries, testing notes, and open questions.

The governing constraint throughout: AI_Diplomacy optimises play quality with frontier models
and many LLM calls per phase (≈21 calls per movement phase for negotiation alone, plus
per-agent diary, state-update, and planning calls — `lm_game.py`,
`ai_diplomacy/negotiations.py`). Our target is **parity in functionality within a
< €100/month budget** on a cheap ~24B model — so several reference capabilities are
deliberately approximated by folding them into existing calls rather than copied
call-for-call. Every doc's **Cost impact** section accounts for this.

## Where the implementation actually stands

Verified against code, since parts of the folklore about this app are stale:

- **Built and working:** the player-via-API boundary (`service/bot/api_client.py` — DRF test
  client against real endpoints, no game-logic imports); signal→Procrastinate wiring for
  plan/finalize/reply (`service/bot/signals.py`, `service/bot/decorators.py`); index-based
  order selection with max_orders capping (`service/bot/context/parsers.py`,
  `service/bot/tasks.py`); board/options/transcript serialization
  (`service/bot/context/builder.py`); profile-based bot detection
  (`user__bot_profile__isnull=False`, `service/bot/decorators.py`) — **not** email-based; and
  a `BotProfile` model with `disposition`/`voice` fields (`service/bot/models.py`) — the
  model layer is not empty.
- **Stubbed/partial:** `BotProfile.disposition`/`voice` are seeded by migration
  (`service/bot/migrations/0002_create_bot_profile.py`) but read by nothing at runtime; the
  shared/private context split exists in shape (`build_shared`/`build_private`) but with no
  caching mechanics; replies exist but only in public channels, only reactively
  (`on_public_chat_message` skips private channels).
- **In the TDD but absent from code:** tactical annotations; personas in prompts; multiple
  bot identities; diary/memory; goals and relationships; negotiation initiation and budget
  caps; prompt caching; token/cost accounting of any kind; the Qwen-capable model
  abstraction.

## The documents, in dependency order

Implementation should proceed roughly in numeric order; the hard edges are listed per doc.

**[GAP_01_MODEL_CLIENT.md](GAP_01_MODEL_CLIENT.md)** — *no prerequisites.*
The client (`service/bot/llm_client.py`) returns bare text from a hard-coded Anthropic call
with fixed `max_tokens=1024`, discarding the usage object. This doc makes `complete()` return
a `CompletionResult` (tokens incl. cache splits, latency, model), adds per-call `max_tokens`,
and adds a settings-switched OpenAI-compatible path — the whole Anthropic-now→Qwen-later
switch as configuration. Deliberately no per-provider class hierarchy (AI_Diplomacy needs
seven concurrent providers; we need one at a time). Foundation for Gaps 02 and 10.

**[GAP_02_COST_TELEMETRY.md](GAP_02_COST_TELEMETRY.md)** — *depends on 01.*
The TDD's cost/telemetry design exists nowhere (and exceeds the reference, whose CSV log has
no token counts). This doc adds the `LLMCall` model — one row per call with token usage, cost
in micro-euro computed from a versioned in-code price table, latency, status, and FKs to
game/phase/member/stage — a `record_llm_call` write path wrapped around every call, and the
`conversation_tokens` aggregate that Gap 09 uses for budget enforcement. Opt-in prompt/response
capture via `BOT_LOG_PROMPTS`.

**[GAP_03_GAME_STATE_SERIALIZATION.md](GAP_03_GAME_STATE_SERIALIZATION.md)** — *no hard
prerequisites; do early.*
AI_Diplomacy pre-computes what a small model cannot: BFS distances to nearest enemy units and
nearest uncapturable supply centers, and annotated adjacencies per unit
(`ai_diplomacy/possible_order_context.py`). We ship none of it, and the prompt never even
names the bot's nation. This doc exposes `Province.adjacencies` through the variant API
(public map knowledge — boundary preserved), builds the graph bot-side
(`bot/context/map.py`), and adds deterministic per-unit annotation and phase-type framing
sections to the shared context. Biggest single input-token increase; the content Gap 10
amortizes.

**[GAP_04_ORDER_ROBUSTNESS.md](GAP_04_ORDER_ROBUSTNESS.md)** — *depends on 01; best after 03.*
Our index-based selection cannot produce illegal orders (structurally ahead of AI_Diplomacy's
parse-and-repair pipeline), but any malformed response discards the model's whole answer for
arbitrary first-legal orders. This doc adds a reasoning field to the order schema, tolerant
JSON extraction plus exactly one re-ask on parse failure, a Hold-preferring fallback, and
telemetry status for fallbacks.

**[GAP_05_MESSAGE_HISTORY.md](GAP_05_MESSAGE_HISTORY.md)** — *no hard prerequisites; pairs
with 03.*
Today's transcripts drop sender names (six opponents all render as `user:`), include the
whole game's history unbounded, and include no order history whatsoever. This doc adds
name+nation attribution, per-channel message limits, a "messages awaiting your reply" section
(the cheap version of AI_Diplomacy's attention/ignored tracking), and a previous-phase
orders-with-outcomes block fetched from the existing order-list endpoint — the raw material
for betrayal awareness. Net token reduction with a ceiling.

**[GAP_06_PERSONA_IDENTITY.md](GAP_06_PERSONA_IDENTITY.md)** — *no hard prerequisites; blocks
07–09.*
One seeded bot user; `get_bot_user()` structurally assumes a singleton; `disposition`/`voice`
are dead data; no `is_bot` on the API. This doc seeds a pool of seven persona-bearing bot
users, replaces the accessor with game-aware selection, injects a persona block into the
private context of every call (system prompts stay shared for cacheability — a deliberate
inversion of AI_Diplomacy's per-power system prompts), and exposes `is_bot` on the member
serializer for the TDD's bot badge.

**[GAP_07_DIARY_MEMORY.md](GAP_07_DIARY_MEMORY.md)** — *depends on 04, 05, 06.*
AI_Diplomacy's dual-layer diary with three dedicated LLM calls per phase is folded into our
existing calls at zero extra call cost: plan writes a `PLAN` entry and a `RETROSPECTIVE` on
the previous phase (betrayal analysis included, since Gap 05 put resolved orders in the
prompt), commit writes a `COMMIT` entry. A `DiaryEntry` model keyed to member+phase+kind,
linked to the producing `LLMCall`, feeds back into prompts through a fixed 12-entry window;
LLM consolidation is deferred.

**[GAP_08_RELATIONSHIPS_GOALS.md](GAP_08_RELATIONSHIPS_GOALS.md)** — *depends on 06, 07.*
AI_Diplomacy's five-level relationships and goal lists, initialized and updated by dedicated
calls, become `Relationship` and `Goal` rows updated by extra fields on the plan call's JSON —
zero extra calls, lazy Neutral initialization, strict validation copied from the reference.
Updates flow only through the plan call, which is also the TDD's prompt-injection guardrail:
chat can never directly move goals, relationships, or orders.

**[GAP_09_NEGOTIATION_LOOP.md](GAP_09_NEGOTIATION_LOOP.md)** — *depends on 02, 05, 06, 07,
08. Last behavioural doc.*
The reference's N-round synchronized negotiation (~21 calls/phase) is replaced by an
asynchronous, budget-capped equivalent: bots reply in private channels (one-line decorator
change), initiate up to two outreach messages per phase written by the plan call itself (zero
extra calls, channels created via the existing channel-create endpoint), and every reply call
is gated by a hard per-phase conversation token budget (`conversation_tokens` from Gap 02)
plus a per-channel reply cap. Bot-to-bot press remains off pending loop-prevention design.

**[GAP_10_PROMPT_CACHING.md](GAP_10_PROMPT_CACHING.md)** — *depends on 01, 03; measurable via
02. Land right after 03.*
The TDD's primary cost lever, absent from both codebases (AI_Diplomacy actively defeats
caching with random-seed prefixes). One merged system prompt, a standardized
system → shared-prefix → private-suffix call layout with `cache_control` breakpoints on the
Anthropic path and byte-identical prefixes for implicit caching on the Qwen path, and a
determinism contract with tests. Includes one correction to the TDD: legal orders are
per-bot on our API (`OrderOptionsView` serves only the requesting user's options), so the
shared cacheable prefix is game state + annotations + order history, with options opening the
private suffix. Worked example: ~80% off critical-call prefix input in a seven-bot game.

## Sequencing summary

```
01 model client ─┬─► 02 cost & telemetry ─────────────┐
                 └─► 10 prompt caching ◄── 03 state    │
03 state serialization ─┬──────────────────────────────┤
05 message history ─────┤                              │
04 order robustness ────┤                              ▼
06 persona/identity ────┴─► 07 diary ─► 08 goals ─► 09 negotiation loop
```

Two tracks can run in parallel: the plumbing track (01 → 02, then 10 after 03) and the
context track (03, 05, 04). They join at 06/07/08, and 09 lands last. Docs 03+10 together
define the cost envelope; 06–09 together define the "presence" the TDD's fun objective asks
for.

## What is deliberately not proposed anywhere

- A formal eval harness (TDD defers it; transcripts + Metabase are the loop).
- Mid-phase replanning (TDD defers it; commit re-reads the world, which is the cheap form).
- The shared game-analysis summary call (TDD marks it future; Gap 10 reserves its slot).
- AI_Diplomacy's two-step formatter model, five-way provider matrix, per-power system
  prompts, multi-round synchronous negotiation, and LLM diary consolidation — each rejected
  or approximated in the relevant doc with the cost argument stated.
