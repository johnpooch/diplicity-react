# Gap 10: Prompt Caching and the Shared/Private Context Split

## Gap statement

AI_Diplomacy does not use prompt caching at all — no `cache_control` blocks, no
prefix-ordering discipline; every call pays full input price (`generate_response`
implementations in `ai_diplomacy/clients.py` send plain system+user strings). It even
*defeats* provider-side implicit caching on purpose: `generate_random_seed`
(`ai_diplomacy/utils.py`) injects a random block at the **top of the system prompt** to get
variation at temperature 0, guaranteeing every prefix is unique. That is rational for a
research harness with a per-run budget; it is the opposite of our design. The TDD makes the
shared/private split with a cacheable shared block the *primary* cost lever (**Context** and
**Budget and cost saving**, `TECHNICAL_DESIGN.md`).

Our implementation has the split's *shape* but none of its *mechanics*.
`ContextBuilder` distinguishes shared and private sections
(`build_shared`/`build_private`, `service/bot/context/builder.py`) and tasks assemble
`shared + private + instruction` (`_submit_orders_from_context`, `service/bot/tasks.py`) —
but everything is joined into a single user string, the client sends no `cache_control`
markers (`service/bot/llm_client.py`), the system prompt differs by stage
(`select_orders_system.txt` vs `reply_system.txt`) which splits would-be cache entries, and
nothing guarantees the shared block is byte-identical across bots (it currently is, by luck
of deterministic sorting in `with_game_state`, but no test pins it). Cache read/write token
fields exist nowhere (Gap 01 adds them to `CompletionResult`; Gap 02 stores them).

Status: shared/private split **built in shape**; caching itself **described in the TDD but
not implemented**.

## Why it matters

This is the multiplier on every other doc's token math. Gap 03 grows the shared block to
1.5–3k tokens and Gap 05 adds a shared order-history section; across seven bots × (plan +
commit) plus replies, the same shared prefix is sent up to a few dozen times per phase.
Anthropic prices cached reads at ~10% of input and cache writes at ~125%, so a shared block
read N times costs roughly `1.25 + 0.1(N−1)` instead of `N` — at N=14 that is ~19% of the
uncached cost for that block. On the Qwen path, several hosts apply implicit prefix-cache
discounts with no API changes — but only if the prefix is actually identical, which is what
this doc enforces.

Depends on Gap 01 (system-as-blocks seam, usage fields), Gap 03 (the big deterministic shared
block worth caching), Gap 02 (cache read/write columns prove the savings). Best landed
immediately after Gap 03.

## Proposed approach

**One system prompt, stage-specific instructions in the user turn.** Merge
`select_orders_system.txt` and `reply_system.txt` into a single `system.txt` containing the
stage-independent rules (what Diplomacy is, how context is structured, honesty about JSON-only
output). Stage-specific text lives entirely in the instruction files already appended to the
user content. This makes the system prompt identical across every bot call in the deployment —
one cache entry, written once per TTL window, read by everything.

**Standardized call layout.** Every call assembles, in order:

1. `system`: the static rules block — `cache_control: {"type": "ephemeral"}` on it.
2. User content, shared prefix: game-state block + tactical annotations (Gap 03) + legal
   orders + previous-phase order history (Gap 05) — identical for every bot in the game
   within a phase — with a `cache_control` breakpoint after it.
3. User content, private suffix: persona (Gap 06), standing (Gap 08), diary (Gap 07),
   channel transcripts (Gap 05), then the stage instruction. Never cached.

Anthropic caches by prefix at the marked breakpoints, so bots in the same game share the
(1)+(2) prefix; the private suffix differs per bot and per call, which is fine. Concretely:
`complete` (Gap 01) accepts user content as a list of blocks, and
`_submit_orders_from_context` passes
`[{"type": "text", "text": shared, "cache_control": {...}}, {"type": "text", "text": private_plus_instruction}]`.
On the OpenAI/Qwen path the blocks are joined in the same order and the markers dropped —
prefix identity alone is what implicit caches key on. A provider-conditional in the client
(`BOT_LLM_PROVIDER`, Gap 01) is the only branching.

**Determinism becomes a contract.** Add sorting guarantees where they are currently
incidental: `with_orders` iterates `group_options_by_source` in payload order — sort sources
by id; annotation and order-history sections sort as specified in Gaps 03/05. A test pins
byte-identity of `build_shared()` across two builds and across two different bot members of
the same game (the shared block must not depend on which member fetched it — note
`get_order_options` returns only the acting user's options
(`service/order/views.py`, `OrderOptionsView` filters by the requesting user's nations), so
**legal orders are per-bot, not shared**: the legal-orders section therefore moves to the
private suffix, or the shared block ends before it. This is a real correction to the TDD's
assumption that "legal orders for all nations" sit in shared context — the API the bot is
allowed to use only serves its own options. Shared prefix = game state + annotations + order
history; per-bot options open the private suffix.)

**Timing awareness, not scheduling.** Anthropic's default cache TTL is five minutes. Plan
tasks for all bots in a game are queued together on phase activation
(`service/bot/signals.py`), so they naturally land inside one TTL window; commit tasks are
queued together by `when_humans_confirmed` (`service/bot/decorators.py`) — also clustered.
Replies straggle across hours and will often miss the cache; accepted, since replies carry
the smallest shared payload benefit anyway. No scheduler changes.

**Measure it.** Nothing extra to build: Gap 01 surfaces `cache_read_tokens` /
`cache_write_tokens`, Gap 02 stores them, and a Metabase question (cache hit ratio by stage)
verifies the lever is working. If reads stay near zero, the prefix is diverging — the
byte-identity test is the debugging tool.

## Cost impact

No new LLM calls; this doc only reprices existing ones. Worked example with Gap 03/05 sizes,
classical seven-bot game, one movement phase: shared prefix ≈ 3.5k tokens, system ≈ 0.5k.
Fourteen critical calls (7 bots × plan+commit): uncached ≈ 56k prefix-tokens billed at full
rate; cached ≈ one write (4k × 1.25) + 13 reads (4k × 0.1) ≈ 10.2k effective full-rate
tokens — an ~80% cut on the prefix, which is the bulk of critical-call input. Cache writes
cost 25% extra, so the scheme only pays when ≥2 calls share a prefix within the TTL — true
for every game with ≥1 bot because plan and commit both run per phase, and strongly true for
multi-bot games. Risk: Anthropic requires a minimum cacheable prefix length (model-dependent,
roughly 1–4k tokens; check current docs for the configured model) — below it, markers are
silently ignored and we simply pay the normal price, so the failure mode is neutral, not
negative.

## Scope boundaries

Out of scope here:

- The context *content* — Gaps 03/05/06/07/08 own their blocks; this doc owns ordering,
  markers, and determinism.
- The shared game-analysis LLM summary (TDD future work) — it would slot into the shared
  prefix when it exists.
- Multi-breakpoint strategies (e.g. separately caching a per-game static block vs per-phase
  block) — one breakpoint after the shared prefix is the minimum that captures most of the
  value; revisit with Gap 02 data.
- Extended-TTL (1h) caching — costs 2× on writes; only worth it if reply traffic shows heavy
  TTL misses, decide from data.

## Testing notes

In `service/bot/tests.py`:

- Byte-identity: `build_shared()` equal across two `ContextBuilder` constructions from the
  same fetched data, and across data fetched as two different bot members of one game
  (options excluded from shared per the correction above).
- Client: with `BOT_LLM_PROVIDER="anthropic"` and a mocked SDK, assert the outgoing request
  has `cache_control` on the system block and on the shared user block only; with
  `"openai"`, assert plain concatenated strings with the shared text as an exact prefix.
- Prompt-order regression: instruction text is last, private block precedes it, shared block
  precedes both (string-index assertions on the captured prompt in the plan-task test).
- Telemetry integration (with Gap 02): mocked usage including cache fields lands in the
  `LLMCall` row.

## Open questions

- Where exactly to end the shared prefix now that legal orders are per-bot: game state +
  annotations + order history is the safe answer, but annotations are per-*unit* and units
  belong to nations — they are still the same board facts for every viewer, so they stay
  shared. Confirm no other per-viewer leakage exists in the phase payload
  (`province_nations` and `supply_centers` are viewer-independent —
  `service/phase/serializers.py`).
- Qwen host choice (Gap 01's open question) decides whether implicit caching exists at all on
  the target path; if the chosen host has none, the shared-prefix discipline still costs
  nothing but the savings math above applies only to the Haiku phase. This materially affects
  how much of the €100 budget headroom survives the model switch.
