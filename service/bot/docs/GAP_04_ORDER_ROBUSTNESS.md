# Gap 04: Order Generation Robustness

## Gap statement

AI_Diplomacy treats the model's order output as untrusted text and repairs it in layers.
Extraction tries multiple formats — `PARSABLE OUTPUT:{...}`, fenced code blocks, bare JSON with
an `"orders"` key, bracket-literal fallback (`_extract_moves`, `ai_diplomacy/clients.py`), plus
`json5`/`json_repair` parsers elsewhere (`_extract_json_from_text`,
`ai_diplomacy/agent.py`). Validation checks each order string against the possible-orders list,
collects invalid ones, and **fills every unordered unit with its Hold option**
(`_validate_orders`, `fallback_orders` — "Just picks HOLD if possible"). A second round-trip
validation pushes orders through the engine itself and returns `{"valid": [...], "invalid":
[...]}` (`get_valid_orders`, `ai_diplomacy/utils.py`), and rejected submissions are shown back
to the model in the next phase's order history as `(Rejected by engine: invalid)`
(`get_order_history_for_prompt`, `ai_diplomacy/game_history.py`). The order prompt explicitly
asks for free-text reasoning before the parsable block
(`ai_diplomacy/prompts_simple/order_instructions_movement_phase.txt`: "Reasoning: … PARSABLE
OUTPUT: …"), and an optional two-step mode has a cheap formatter model convert a pure
natural-language answer into JSON (`ai_diplomacy/formatter.py`).

Our pipeline already has one structural advantage: the model selects **indices into the legal
option list** (`parse_order_selections`, `service/bot/context/parsers.py`), so it cannot emit
syntactically illegal orders at all — validation-by-construction instead of
validation-by-repair. The weaknesses are around that core:

- `_extract_json` (`service/bot/context/parsers.py`) handles exactly one deviation (a markdown
  fence); any other formatting raises `LLMError` and the task abandons the model's answer
  entirely, falling back to `first_legal_selections` (`service/bot/tasks.py`).
- `first_legal_selections` (`service/bot/context/orders.py`) picks the **first** option per
  source, which is whatever order `flatten_options` produced — not Hold, potentially a random
  move or a self-defeating support.
- An invalid or missing index for one source silently takes that same arbitrary first option
  (`parse_order_selections`).
- There is no re-ask: a malformed response is never retried with the error shown to the model.
- The prompt forbids reasoning ("Respond with JSON only",
  `service/bot/prompts/select_orders_system.txt`), which suppresses exactly the thinking a
  small model needs, and `max_tokens=1024` (`service/bot/llm_client.py`) would truncate a large
  late-game order set if reasoning were added naively.
- Nothing records that a fallback happened anywhere queryable (log lines only).

Status: index-based selection and max_orders capping are **built and working**; repair,
re-ask, Hold-preferring fallback, and reasoning are **absent** (the TDD does not discuss this
layer explicitly — it is implied by "submit reasonable orders every phase").

## Why it matters

Every parse failure currently converts the bot's turn into near-random orders, which reads as
lobotomy-level play to opponents — worse for "fun" than a Hold-everything turn, and invisible
because nothing is recorded. Cheap models fail formatting more often than frontier ones, so
the Qwen switch (Gap 01) raises the failure rate exactly when play quality matters. Reasoning
before selection is also the cheapest known quality lever for small models on this task.

Depends on Gap 01 (per-call `max_tokens`, telemetry status codes via Gap 02). Independent of
Gaps 03/05 but lands best after Gap 03 so the reasoning has annotations to reason over.

## Proposed approach

Four changes, all inside `service/bot/`:

**Reasoning field.** Change `select_orders_system.txt` / `select_orders_instruction.txt` to
request:

```json
{"reasoning": "<3-6 sentences>", "choices": [{"source_id": "...", "option_index": 0}, ...]}
```

`parse_order_selections` ignores `reasoning` for order purposes; Gap 07 stores it as the diary
seed. The plan/commit calls pass `max_tokens=2048` explicitly (Gap 01's per-call parameter) so
reasoning plus a 17-unit choice list cannot truncate.

**Tolerant extraction plus one re-ask.** Extend `_extract_json` to also try a first-`{` /
last-`}` slice before giving up (the cheapest of AI_Diplomacy's fallbacks; skip `json5` /
`json_repair` dependencies — with index-based selection there is nothing else worth
repairing). If parsing still fails, `_submit_orders_from_context` makes **one** re-ask: append
the model's previous output and a one-line correction ("Your previous reply was not valid
JSON…") as additional messages and call `complete` again. One retry, not AI_Diplomacy's five —
this is a formatting nudge, not transport retry, and the cap bounds cost.

**Hold-preferring fallback.** Replace `first_legal_selections`'s arbitrary pick with
Hold-preference, mirroring `fallback_orders`:

```python
def default_selection(source_options):
    hold = next((o for o in source_options if o["order_type"]["id"] == OrderType.HOLD), None)
    return option_to_selected(hold or source_options[0])
```

Used in all three places: total parse failure, per-source invalid index, and per-source
missing choice. Retreat/adjustment phases have no Hold option, so `source_options[0]` remains
the fallback there (for adjustments, choosing not to order at all is legal and arguably
better — see open questions).

**Record the failure.** The task passes `status=parse_error` (after a failed re-ask) or
per-source fallback counts into the Gap 02 telemetry row, so fallback frequency per model is a
Metabase query instead of a log grep.

The engine round-trip that AI_Diplomacy needs (`get_valid_orders`) is deliberately not copied:
our `submit_orders` already exercises the real order-creation endpoint per order
(`service/bot/api_client.py`), and `OrderSerializer.validate_selected`
(`service/order/serializers.py`) validates against `phase.transformed_options` server-side.
A rejected POST is currently only logged; change `submit_orders` to return the count of
failures so the task can fall back to `default_selection` for just those sources.

## Cost impact

Reasoning adds ~150–400 output tokens to plan and commit calls: at two calls per bot-phase
that is under 1k extra output tokens per bot-phase, the protected "critical prompts" slice of
the TDD's per-phase budget. The re-ask doubles one call's cost in the failure case only; with
a p95 parse-failure rate of a few percent the expected overhead is negligible, and the single
re-ask cap keeps the worst case bounded at one extra call per stage. No effect on the cached
shared prefix (Gap 10): all changes are in instructions and output.

## Scope boundaries

Out of scope here:

- Persisting the reasoning text as a diary entry — Gap 07 (this doc only makes it exist).
- The two-step formatter-model pattern (`ai_diplomacy/formatter.py`) — rejected: a second
  model per call is the opposite of our cost posture, and index selection removes most of the
  need.
- Mid-phase replanning — deferred by the TDD.
- Changes to the reply parser (`parse_reply`) — it inherits the tolerant `_extract_json` for
  free; the re-ask applies only to order calls where a fallback is costly.

## Testing notes

In `service/bot/tests.py`:

- `TestSelectOrders`: responses with leading prose, trailing prose, and a bare JSON object all
  parse; a `reasoning` key is tolerated and ignored by selection.
- New `TestDefaultSelection`: Hold chosen when present regardless of option order; first
  option when no Hold exists (Build-only options, reusing `TestAdjustmentOrderLimit`'s
  fixtures).
- Re-ask: patch `LLMClient` so the first `complete` returns garbage and the second returns
  valid JSON; assert two calls and the second answer's orders submitted. Both calls garbage →
  assert Hold fallback and a `parse_error` telemetry row (with Gap 02).
- `test_invalid_or_missing_index_falls_back_per_source` updates from first-option to
  Hold-option expectations.
- Integration (`service/integration/test_bot.py`): unchanged flows still pass; the plan task
  with the real prompt files still produces complete orders (`orders.count() > 0`,
  `complete=True` as asserted today).

## Open questions

- For adjustment phases with a failed parse, is submitting nothing better than an arbitrary
  build/disband? Skipping a build is safe; skipping a required disband may be resolved by the
  engine's civil-disorder rules — needs a decision from someone who knows the resolution
  behaviour for missing disbands.
- Should the re-ask also fire when more than half the sources fell back individually (parsed
  JSON but mostly invalid indices)? Recommended no for now — bounded blast radius per source —
  but transcript review may change this.
