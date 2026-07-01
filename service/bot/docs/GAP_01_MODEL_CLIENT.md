# Gap 01: LLM Client — Usage Reporting and Provider Abstraction

## Gap statement

AI_Diplomacy runs every LLM call through a provider abstraction. `BaseModelClient`
(`ai_diplomacy/clients.py`) defines `generate_response(prompt, temperature)` and is subclassed
per provider (`OpenAIClient`, `ClaudeClient`, `GeminiClient`, `DeepSeekClient`,
`OpenRouterClient`, `TogetherAIClient`, `RequestsOpenAIClient`). A factory,
`load_model_client` (`ai_diplomacy/clients.py`, bottom section), parses model specs of the form
`<prefix:>model[@base_url][#api_key]`, so the same code drives a frontier API, an OpenRouter
model, or a self-hosted OpenAI-compatible endpoint. Per-model `max_tokens` is configurable
(`BaseModelClient.max_tokens`, overridden per power via `--max_tokens_per_model` in
`lm_game.py`). Transport failures are retried with exponential backoff — five attempts in
`run_llm_and_log` (`ai_diplomacy/utils.py`). Notably, AI_Diplomacy does **not** capture token
usage or cost from provider responses; its CSV log (`log_llm_response`,
`ai_diplomacy/utils.py`) records only model, power, phase, response type, raw prompt/response,
and a success string.

Our client (`service/bot/llm_client.py`) is a single hard-coded Anthropic call:
`max_tokens=1024` is fixed, the model comes from `settings.BOT_LLM_MODEL` (default
`claude-haiku-4-5`, `service/project/settings.py:262`), the return value is the concatenated
text blocks only, and the `usage` object on the Anthropic response is discarded. There is no
provider abstraction, no per-call `max_tokens`, no latency measurement, and no way to point the
client at the Qwen endpoint the TDD targets (see **Model** in `TECHNICAL_DESIGN.md`) without
rewriting the client. Transport errors surface as `LLMError` and the calling Procrastinate
tasks retry up to three times (`retry=3` in `service/bot/tasks.py`).

This doc distinguishes:

- **Built and working:** single Anthropic call path, `LLMError` wrapping, task-level retry.
- **Described in the TDD but not implemented:** the Anthropic-now → Qwen-later switch, and the
  per-call usage capture that cost tracking (Gap 02) requires.

## Why it matters

Every other gap doc adds or reshapes LLM calls. Cost tracking (Gap 02) cannot exist until the
client returns token usage. The TDD's model plan — build on Claude Haiku, switch to a hosted
Qwen3-class endpoint once the loop works — requires the call site to be provider-agnostic
before the rest of the system grows around Anthropic-specific behaviour. Fixed
`max_tokens=1024` also silently truncates any future response that includes reasoning plus a
full order set (Gap 04) or a long diary note (Gap 07).

Dependencies: none. This is the foundation for Gap 02 (cost & telemetry) and a prerequisite
for Gap 10 (prompt caching, which needs provider-conditional cache markers).

## Proposed approach

Keep a single `LLMClient` class in `service/bot/llm_client.py` with the same
`complete(system=..., messages=...)` entry point, extended as follows.

**Return a result object instead of a string.** Add a dataclass:

```python
@dataclass
class CompletionResult:
    text: str
    model: str
    input_tokens: int
    output_tokens: int
    cache_read_tokens: int
    cache_write_tokens: int
    latency_ms: int
```

Anthropic populates the token fields from `message.usage` (`input_tokens`, `output_tokens`,
`cache_read_input_tokens`, `cache_creation_input_tokens`); OpenAI-compatible responses populate
them from `response.usage` (`prompt_tokens`, `completion_tokens`, and
`prompt_tokens_details.cached_tokens` when the host reports it), with cache fields defaulting
to zero. `latency_ms` is measured around the request in the client.

**Provider switch by settings.** New settings in `service/project/settings.py`:

```python
BOT_LLM_PROVIDER = os.getenv("BOT_LLM_PROVIDER", "anthropic")
BOT_LLM_BASE_URL = os.getenv("BOT_LLM_BASE_URL", "")
BOT_LLM_API_KEY = os.getenv("BOT_LLM_API_KEY", os.getenv("ANTHROPIC_API_KEY", ""))
BOT_LLM_MAX_TOKENS = int(os.getenv("BOT_LLM_MAX_TOKENS", "1024"))
```

`LLMClient.__init__` branches on `BOT_LLM_PROVIDER`: `"anthropic"` uses the existing
`anthropic` SDK; `"openai"` uses the `openai` package pointed at `BOT_LLM_BASE_URL` (this is
the Qwen path — every serious Qwen host exposes an OpenAI-compatible endpoint). Two private
methods (`_complete_anthropic`, `_complete_openai`) normalize both responses into
`CompletionResult`. No per-provider subclasses, no factory, no model-spec mini-language —
AI_Diplomacy needs seven concurrent providers per game; we need exactly one at a time.

**Per-call max_tokens.** `complete(system, messages, max_tokens=None)` with `None` falling back
to `BOT_LLM_MAX_TOKENS`. Call sites that expect longer output (Gap 04 reasoning, Gap 07 diary)
pass an explicit value.

**Retry stays at the task layer.** AI_Diplomacy retries five times inside the call wrapper
because a failed call aborts a whole in-process game. Our calls run inside Procrastinate tasks
that already retry three times (`service/bot/tasks.py`), and every task has a non-LLM fallback
(first-legal orders, staying silent). Adding client-level retry on top would multiply worst-case
latency and spend. The client makes one attempt; `LLMError` propagates as today.

**System prompt as blocks.** `complete` accepts `system` as either a string or a list of
`{"type": "text", "text": ...}` blocks, passed through to Anthropic unchanged and joined with
`"\n\n"` for the OpenAI path. This is the seam Gap 10 uses for `cache_control` markers without
another client change.

Call sites in `service/bot/tasks.py` change from `response_text = ...complete(...)` to
`result = ...complete(...)` / `result.text`, and hand `result` to the telemetry recorder once
Gap 02 lands.

## Cost impact

No new LLM calls. Neutral on tokens. Strictly enabling: usage capture is what makes the
per-phase budgets and the €100/month cap observable (Gap 02), and the OpenAI-compatible path is
what unlocks the ~5–10× cheaper Qwen pricing the TDD's budget assumes. Removing client-level
retry (never present) and keeping one attempt per task run keeps worst-case spend per task at
one call.

## Scope boundaries

Out of scope here:

- Writing usage rows to the database — Gap 02 owns the `LLMCall` model and write path.
- `cache_control` placement and context restructuring — Gap 10.
- Any prompt or parsing changes — Gaps 03–05.
- Choosing the actual Qwen host and model; this doc only makes the switch a settings change.

## Testing notes

Extend `TestLLMClient` in `service/bot/tests.py`:

- Mock the Anthropic SDK response with a `usage` object; assert `CompletionResult` fields
  (tokens, model, text) are populated and `latency_ms >= 0`.
- With `settings.BOT_LLM_PROVIDER = "openai"` and a mocked `openai` client, assert the same
  normalization from `response.usage`.
- Assert `max_tokens` passed per call overrides `settings.BOT_LLM_MAX_TOKENS`.
- Assert `system` given as a block list reaches Anthropic unchanged and is joined to a single
  string on the OpenAI path.
- Existing task tests (`TestPlanTask`, `TestReplyTask`) keep passing with the new return type —
  they patch `LLMClient`, so update the mocks to return a `CompletionResult`.

## Open questions

- Which Qwen host to target first (Together, Fireworks, DeepInfra, OpenRouter routing)? Pricing
  and implicit prefix-caching behaviour differ; the choice affects Gap 10's savings estimate.
- Should `BOT_LLM_MAX_TOKENS` default rise from 1024 now, or only when Gap 04 adds a reasoning
  field to the order response? Raising it costs nothing until the model actually emits more.
