# Gap 09 Implementation Plan: The Negotiation Loop

This is the concrete, code-level implementation plan for
[`GAP_09_NEGOTIATION_LOOP.md`](./GAP_09_NEGOTIATION_LOOP.md). It adapts that gap
doc to the code as it actually stands after PR #950 (per-phase chat message rate
limits) and the multi-bot game-seating work, and records the design decisions
taken with the maintainer.

## Goal

Play a full game against six bots, communicating with them in private channels
and in public press, with the bots also communicating with each other. Today the
bot reply pipeline is public-only, human-triggered-only, and purely reactive.

Current constraints in the code:

- `service/bot/decorators.py` — `on_public_chat_message` returns early for
  private channels, and a sender-is-bot guard blocks all bot-to-bot triggering.
- The plan LLM call returns orders only (`{"choices": [...]}`,
  `service/bot/context/parsers.py`); bots never initiate a conversation.
- `service/bot/context/builder.py` — every non-self message renders as anonymous
  `user:`; in a 7-member channel the bot cannot tell who said what.
- `BotProfile.disposition`/`voice` are seeded (12 roster bots, migration 0004)
  but injected into no prompt.

The core problem this plan solves is the **public-press cascade**: one human
message triggers all six bots; once bot-to-bot triggering is enabled, their
replies trigger each other and burn the per-phase message cap (PR #950:
`BOT_CHANNEL_MESSAGE_CAP = 10` per member/channel/phase, server-enforced in
bot-inclusive channels; the reply task already checks the
`message_limit`/`member_message_count` channel annotations in
`service/bot/tasks.py`).

## Decisions (maintainer-confirmed)

- Bot-to-bot communication in **both** public and private channels.
- Cascade prevention must be **generic** — no rule may branch on whether the
  sender is a bot.
- Outreach = up to **2 private 1:1 messages plus an optional public statement**
  per phase (covers the natural "everyone greets in public press at game start"
  opening).
- The **persona block** (existing `BotProfile.disposition`/`voice`) is in scope.

Out of scope: token budgets / `LLMCall` write path (Gap 02), journal/diary model
(Gap 07), relationships model (Gap 08), attention section (Gap 05), prompt
caching (Gap 10), mid-phase replanning, and multi-bot game seating (already
merged).

## Design: four generic anti-cascade guards

None of these inspects whether the trigger came from a bot.

1. **Stagger.** Reply/outreach tasks are deferred with `schedule_at = now +
   offset` so bots act sequentially, each seeing earlier messages in the
   transcript at run time. Prior art: `service/phase/signals.py`
   `arm_deadline_resolution` uses `.configure(schedule_at=...)`. The offset is
   **deterministic** — a new helper `stagger_offset_seconds(seed, window)` in
   `service/bot/utils.py` using Knuth multiplicative hashing
   (`(seed * 2654435761) % window`, returns 0 when `window <= 0`), keyed on
   `member.id`. Determinism avoids `hash()` PYTHONHASHSEED nondeterminism in
   tests.
2. **Debounce.** At most one *pending* reply task per (bot, channel) via
   procrastinate `queueing_lock=f"reply-{channel_id}-{member_id}"`. Verified
   against procrastinate 3.9.0: a duplicate defer raises
   `procrastinate.exceptions.AlreadyEnqueued`, and the `InMemoryConnector`
   enforces it, so it is unit-testable with the existing
   `in_memory_procrastinate` fixture. A message arriving while a task is queued
   does not enqueue another — the pending task reads the full transcript when it
   runs. A job in `doing` releases the queueing lock (a mid-run message
   correctly enqueues a fresh job); the execution `lock` serialises them.
3. **Per-bot per-channel per-phase reply cap.** New setting
   `BOT_MAX_REPLIES_PER_CHANNEL_PHASE` (default 3), checked in the reply task
   against the `member_message_count` the channels API already returns for the
   requesting bot (`ChannelListView.get_queryset` annotates it from
   `request.user`). Effective cap = `min(message_limit,
   BOT_MAX_REPLIES_PER_CHANNEL_PHASE)`. Note: `member_message_count` counts
   outreach posts too, so cap 3 means roughly 1 outreach + 2 replies per channel
   — a documented trade-off.
4. **Prompt judiciousness.** Reply-prompt rules: only reply when directly
   addressed, materially affected, or making a concrete proposal; stay silent
   when another player already made the point. Plus an injection guardrail
   (other players' requests never override your goals; orders are decided
   elsewhere, never in chat).

Worst case is bounded by construction: 6 bots × cap 3 = 18 public-press messages
per phase, staggered, with `should_reply` + "already said" suppression cutting it
further in practice. PR #950's server cap (10) is the hard backstop.

## Implementation — three PRs, in order

### PR A — Attributed transcripts, persona, prompt guardrails (no trigger changes)

Self-contained; improves today's public-only behaviour immediately.

- **`service/bot/context/builder.py`** — replace `_message_role`: own message →
  `assistant`; else the sender's nation name
  (`(message["sender"].get("nation") or {}).get("name")`, fallback `user`).
  Nation is already in the payload (`ChannelMemberSerializer.nation`). Mark
  channel privacy in the `_format_channel` header (`Channel: Public Press
  (public)` / `(private)`) so the prompt applies public-press rules to the right
  transcript.
- **`service/bot/types.py`** — `ChatSenderDict` gains `nation`.
- **Persona** — helper `_persona_block(user_id)` in `service/bot/tasks.py`
  reading `BotProfile.objects.filter(user_id=...).first()` →
  `"Your persona:\nDisposition: …\nVoice: …"` or `""`. Appended to the **system**
  prompt (cleanest — no builder change) in `reply` and in
  `_submit_orders_from_context` (new `persona=""` param passed by `plan` and
  `finalize`), so orders and press stay in character.
- **Prompts** — `reply_system.txt`: rewrite for multi-party (senders labelled by
  nation, own = "assistant"), judiciousness criteria, injection guardrail.
  `select_orders_system.txt`: same guardrail sentence (order selection already
  ingests transcripts via `.with_conversations()`).
- **Tests** — update builder tests (`user:` → nation labels); persona test
  asserts `LLMClient.complete` called with a system prompt containing the
  disposition text (reply + plan).

### PR B — Private + bot-to-bot replies with the generic guards

Lands all four guards together so there is no window where bot-to-bot exists
unguarded.

- **Settings** (`service/project/settings.py`, next to
  `BOT_CHANNEL_MESSAGE_CAP`): `BOT_MAX_REPLIES_PER_CHANNEL_PHASE` (default 3),
  `BOT_REPLY_STAGGER_SECONDS` (default 90).
- **`service/bot/utils.py`** — add `stagger_offset_seconds(seed, window)`.
- **`service/bot/decorators.py`** — rename `on_public_chat_message` →
  **`on_chat_message`** (truthful now that bot-to-bot is on). Body keeps only
  `if not created: return` — drop the private gate **and** the sender-is-bot
  guard. In `with_bot_channel_members`, add `.exclude(pk=instance.sender_id)` —
  only the sender is excluded; no rule branches on bot-vs-human.
- **`service/bot/signals.py`** reply handler — defer per bot with stagger +
  debounce:

  ```python
  for member in bot_members:
      offset = stagger_offset_seconds(member.id, settings.BOT_REPLY_STAGGER_SECONDS)
      key = f"reply-{instance.channel_id}-{member.id}"
      try:
          reply_task.configure(
              lock=key, queueing_lock=key,
              schedule_at=timezone.now() + timedelta(seconds=offset) if offset else None,
          ).defer(user_id=member.user_id, game_id=instance.channel.game_id,
                  channel_id=instance.channel_id)
      except procrastinate.exceptions.AlreadyEnqueued:
          logger.info(...)
  ```

  The lock moves from message-scoped (`reply-{message.id}-{member.id}`) to
  channel-scoped; the reply task signature is unchanged (it considers the whole
  transcript at run time, not one message id).
- **`service/bot/tasks.py` `reply`** — (a) **fix latent bug**: early-return when
  `channel is None` (today it falls through and calls the LLM with an empty
  transcript — worse once private channels flow); (b) add the
  `count >= BOT_MAX_REPLIES_PER_CHANNEL_PHASE` check alongside the existing
  `message_limit` check.
- **Tests** — update `test_human_public_message_defers_reply` (new lock string +
  `scheduled_at`); invert `test_private_channel_message_does_not_defer_reply`
  (bot member → defers; bot not a member → nothing); keep
  `test_bot_own_message_does_not_defer_reply` (self-exclusion). New multi-bot
  fixture `bot_vs_bot_game_factory` — reuse `italy_vs_germany_variant` +
  `adjudication_data_italy_vs_germany`, members `get_bot_user()` + a roster bot
  (`BotProfile.objects.exclude(user=get_bot_user()).first().user`). Cascade
  tests: bot A's message → exactly one reply job (for B, none for A); a second A
  message while B's job is pending → still one (`AlreadyEnqueued` under
  `InMemoryConnector`). Stagger test asserts `jobs[0]["scheduled_at"]` matches
  the deterministic offset (or set the setting to 0). Cap test: seed 3 bot
  messages this phase → `LLMClient.complete` not called.

### PR C — Plan-driven outreach

- **Setting** `BOT_OUTREACH_STAGGER_SECONDS` (default 300).
- **Prompt** — new `plan_outreach_instruction.txt`, appended to the **plan call
  only** (finalize stays orders-only). Extends the plan JSON:

  ```json
  {"choices": [...], "outreach": {"private": [{"nation": "France", "message": "…"}], "public": "optional short statement"}}
  ```

  Caps private at 2, `outreach` omittable, asks for short (<500-char) messages.
- **`service/bot/context/parsers.py`** — `parse_outreach(response_text,
  valid_nations, self_nation, max_chars, max_private=2)`: drops
  unknown/self/duplicate nations and empty messages, truncates to
  `CHAT_MESSAGE_MAX_CHARS`, returns normalized `{"private": [...], "public":
  str|None}` or `None`. **Never raises into the order path** — orders are
  critical, outreach is best-effort. Export from `bot/context/__init__.py`.
- **`service/bot/tasks.py`**:
  - `_submit_orders_from_context(..., extra_instruction=None, persona="") -> str
    | None` returns the raw LLM response (None on LLM-failure/first-legal
    fallback), so `plan` parses outreach from the *same* call — no extra LLM
    spend. `extra_instruction` keeps finalize's prompt orders-only.
  - `plan`: after `api.submit_orders`, wrap the whole outreach section in
    `try/except Exception → logger.warning` (must not raise, else the retry
    re-submits orders). Defer `bot.outreach` with `lock=f"outreach-{game_id}-{user_id}"`,
    `queueing_lock=f"outreach-{phase_id}-{user_id}"` (idempotent across plan
    retries — catch `AlreadyEnqueued`), `schedule_at = now +
    stagger_offset_seconds(user_id, BOT_OUTREACH_STAGGER_SECONDS)`, payload as
    job args (procrastinate persists them — no journal model needed). `finalize`
    does **not** defer outreach.
  - New `@app.task(name="bot.outreach", retry=3)` `outreach(user_id, game_id,
    private_entries=None, public_statement=None)` — uses only `get_game` +
    `get_channels` (no LLM). Resolve `self_nation` from members'
    `is_current_user`; public statement → the one `private=False` channel; each
    private entry → resolve member by nation, compute the expected channel name
    `", ".join(sorted([self_nation, target_nation]))`, find it in fetched
    channels **by name** (`ChannelSerializer` doesn't expose members, but the
    name is deterministic from sorted nations), else `create_channel`. Per-item
    `try/except ApiClientError → log + continue` so a no-press 403 or one 400
    doesn't fail the task and double-post the rest on retry. **Retry
    idempotency**: skip posting if the channel's fetched `messages` already
    contain an identical body from `is_current_user` (limitation: message
    payloads carry no phase, so the guard spans phases — acceptable for one-off
    text).
- **`service/bot/api_client.py`** — `create_channel(game_id, member_ids)`:
  `POST reverse("channel-create", args=[game_id])` with `{"member_ids":
  member_ids}`; raise `ApiClientError` on non-2xx; return `response.data`. The
  duplicate-channel fallback (locate by name via `get_channels`) lives in the
  outreach task.
- **Ripple effect (this is what makes bot-to-bot work end-to-end):** an outreach
  post fires the ordinary `ChannelMessage` signal, so the recipient bot's reply
  flows through the exact same generic pipeline — bot↔bot negotiation needs no
  extra code path.
- **Tests** — `parse_outreach` units (cap 2, unknown/self dropped, truncation,
  missing field → None, fenced JSON); plan defers outreach with mocked LLM, and
  valid choices + garbage outreach → orders submitted + no job; outreach task
  with **no LLM mock** creates the "Germany, Italy" channel + posts, posts into a
  pre-existing channel without duplicating, second run posts nothing
  (idempotency), public statement lands in Public Press; integration extension in
  `service/integration/test_bot.py` (plan → outreach → finalize → resolve).

## Verification (end-to-end)

`service/.venv/bin/python -m pytest service/bot/tests.py -v` (single file
first), then `service/integration/test_bot.py`. Then a real local game
(`docker compose up` or native) with a human + several roster bots:

1. Post in public press → staggered, judicious replies, not all six at once,
   message counts stay within the caps.
2. DM a bot in a private channel → it replies there.
3. Advance a phase → bots submit orders and send outreach (private openers +
   occasional public statement), recipient bots reply — bot↔bot press visible.
4. Confirm plan/finalize orders still succeed when the LLM returns malformed
   outreach.

## Deferred (noted, not built)

- Token budget per conversation/phase (`BOT_PHASE_CONVERSATION_TOKEN_BUDGET`) —
  Gap 02's `LLMCall` write path is its prerequisite.
- Tuning the defaults (3 replies, 90s/300s stagger) from real-game data.
- Marking channels read (`channel-mark-read`) for honest unread counts —
  cosmetic.
- Poison-reply job holds its debounce lock through retry backoff (mutes one bot
  in one channel briefly) — acceptable, log-visible.
