# Gap 02: Cost and Telemetry Persistence

## Gap statement

AI_Diplomacy logs every LLM interaction to a CSV file: `log_llm_response`
(`ai_diplomacy/utils.py`) appends timestamp, model, power, phase, response type, raw prompt,
raw response, and a success string to `llm_responses.csv`; error counts are aggregated into
`overview.jsonl` (`lm_game.py`, game-end section). That gives full inspection of what each
agent was told and said, but it captures **no token counts and no cost** — acceptable for a
research harness where a run's budget is decided up front, not for a service with a monthly
cap.

Our TDD is more ambitious than AI_Diplomacy here (see **Telemetry and observability** in
`TECHNICAL_DESIGN.md`): one row per LLM call with token usage including cache splits, computed
cost from a versioned price table, latency, status, and foreign keys to game, phase, member,
and stage — queryable from Metabase. None of it exists. `service/bot/models.py` contains only
`BotProfile`; `service/bot/llm_client.py` discards the provider's usage object; the tasks in
`service/bot/tasks.py` log free-text lines to the Python logger and nothing else. There is no
way today to answer "what did bots cost this month" or "which stage is over budget" — the two
questions the TDD's budget section depends on.

Status: **described in the TDD but not implemented**, and not present in AI_Diplomacy either —
this doc is where we deliberately exceed the reference.

## Why it matters

The €100/month cap and the per-phase token budgets are unenforceable and uninspectable without
per-call rows. Gap 09 (negotiation loop) needs a cheap query — "tokens this member has spent on
conversation this phase" — to enforce the conversation cap. Inspection (reading a bot's
prompts/responses while tuning) is also the TDD's stated evaluation method in place of a formal
eval harness.

Depends on Gap 01 (`CompletionResult` carries the usage numbers). Feeds Gap 09 (budget
enforcement) and the diary/relationship inspection pages later.

## Proposed approach

**Model.** In `service/bot/models.py`, following the QuerySet/Manager pattern from
`service/game/models.py`:

```python
class LLMCallQuerySet(models.QuerySet):
    def for_member_phase(self, member, phase):
        return self.filter(member=member, phase=phase)

    def conversation_tokens(self, member, phase):
        return self.for_member_phase(member, phase).filter(
            stage__in=[BotStage.REPLY, BotStage.NEGOTIATE]
        ).aggregate(
            total=Coalesce(Sum(F("input_tokens") + F("output_tokens")), 0)
        )["total"]


class LLMCall(BaseModel):
    objects = LLMCallManager()
    game = models.ForeignKey("game.Game", on_delete=models.CASCADE, related_name="bot_llm_calls")
    phase = models.ForeignKey("phase.Phase", null=True, on_delete=models.SET_NULL, related_name="bot_llm_calls")
    member = models.ForeignKey("member.Member", null=True, on_delete=models.SET_NULL, related_name="bot_llm_calls")
    stage = models.CharField(max_length=20, choices=BotStage.STAGE_CHOICES)
    model = models.CharField(max_length=100)
    status = models.CharField(max_length=20, choices=LLMCallStatus.STATUS_CHOICES)
    error = models.TextField(blank=True, default="")
    input_tokens = models.IntegerField(default=0)
    output_tokens = models.IntegerField(default=0)
    cache_read_tokens = models.IntegerField(default=0)
    cache_write_tokens = models.IntegerField(default=0)
    cost_micro_eur = models.BigIntegerField(default=0)
    price_version = models.CharField(max_length=50, blank=True, default="")
    latency_ms = models.IntegerField(default=0)
    prompt = models.TextField(blank=True, default="")
    response = models.TextField(blank=True, default="")
```

The bot app already reads game-side models (`Member`, `Phase` in `service/bot/decorators.py`),
so FKs from `bot` to `game`/`phase`/`member` respect the architecture rule — the dependency
points from `bot` into `game`, never the reverse.

**Constants.** In `service/bot/constants.py`, following the class-plus-`CHOICES` pattern from
`service/common/constants.py`:

```python
class BotStage:
    PLAN = "plan"
    NEGOTIATE = "negotiate"
    COMMIT = "commit"
    REPLY = "reply"

    STAGE_CHOICES = (...)


class LLMCallStatus:
    SUCCESS = "success"
    PARSE_ERROR = "parse_error"
    LLM_ERROR = "llm_error"

    STATUS_CHOICES = (...)
```

**Price table.** Providers return tokens, not money, so cost is computed in Django. A code-level
table in `service/bot/constants.py` is enough — prices change rarely and a code change with the
`price_version` string stored per row preserves history without a table and admin UI:

```python
BOT_MODEL_PRICES = {
    "claude-haiku-4-5": {
        "version": "2026-07",
        "input_per_m_eur": ...,
        "output_per_m_eur": ...,
        "cache_read_per_m_eur": ...,
        "cache_write_per_m_eur": ...,
    },
}
```

Cost is stored as integer micro-euro (`cost_micro_eur`) to avoid float drift; Metabase divides
by 1e6. An unknown model records zero cost and an empty `price_version` rather than failing the
task.

**Write path.** A new `service/bot/telemetry.py` with a single function:

```python
def record_llm_call(*, game_id, phase_id, member_id, stage, result=None, error=None, prompt="", response=""):
```

It computes cost from `BOT_MODEL_PRICES`, truncates nothing, and stores `prompt`/`response`
only when `settings.BOT_LOG_PROMPTS` is true (default off — the TDD makes full capture opt-in
to limit storage and avoid persisting hidden game information). Tasks call it in a
`try/finally` around each `LLMClient.complete`, so a parse failure after a successful call
still records the spend with `status=parse_error`. The write happens inside the Procrastinate
task, not a request cycle, matching the TDD's inspection design.

The tasks currently pass only `user_id`/`game_id`; they resolve `member` via the game payload
they already fetch (`api_client.get_game` returns members) or a direct
`Member.objects.get(game_id=..., user_id=...)` — the latter is simpler and consistent with the
existing use of game models in `decorators.py`. `phase_id` comes from
`data["game"]["current_phase_id"]` which `fetch_context` already retrieves
(`service/bot/context/fetch.py`).

**Dashboards.** Nothing to build in code: Metabase questions over `bot_llmcall` (spend by
month vs cap, tokens by stage/phase, error rates). Out of code scope.

## Cost impact

No new LLM calls; one INSERT per LLM call, executed in background tasks. This is the
measurement layer the budget depends on — it is what turns "stay under €100/month" from an
intention into a queryable number, and it provides the aggregate (`conversation_tokens`) that
Gap 09 uses as a hard cutoff.

## Scope boundaries

Out of scope here:

- Budget **enforcement** — Gap 09 consumes `conversation_tokens`; this doc only records.
- Diary/relationship rows and their inspection UI — Gaps 07/08.
- A staff inspector page — deferred entirely; Metabase over these rows covers cost visibility,
  and transcripts are readable in the admin once `BOT_LOG_PROMPTS` is on.
- Alerting/thresholds — Metabase configuration, not code.

## Testing notes

In `service/bot/tests.py`:

- Unit-test `record_llm_call`: given a `CompletionResult` with known token counts and a model
  present in `BOT_MODEL_PRICES`, assert one `LLMCall` row with the expected `cost_micro_eur`,
  `price_version`, and FKs; unknown model → zero cost, empty version; `BOT_LOG_PROMPTS` off →
  empty `prompt`/`response` fields.
- Extend `TestPlanTask.test_plan_creates_orders_without_confirming` (uses
  `bot_game_factory`): after `tasks.plan(...)`, assert `LLMCall.objects.filter(game=game,
  stage=BotStage.PLAN).count() == 1` and that `member` points at the bot member. With the LLM
  mocked to raise `LLMError`, assert a row with `status=llm_error` is still written and the
  first-legal fallback still submits orders.
- Query-count check on `conversation_tokens` (single aggregate query), in line with the repo's
  N+1 test habit.

## Open questions

- Is integer micro-euro the right unit, or should we store raw token counts only and leave all
  pricing to Metabase? Storing computed cost matches the TDD ("computed cost… from a versioned
  price table") and survives price-table edits; the open question is whether anyone wants
  historical rows re-priced, which the stored-cost design deliberately prevents.
- Retention: do `LLMCall` rows live forever, or get pruned after N months once Metabase has
  aggregated them? At a few dozen phases/day the table stays small for years; deferring is safe.
