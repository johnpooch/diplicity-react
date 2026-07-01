# Gap 09: The Negotiation Loop

## Gap statement

AI_Diplomacy runs a synchronous, multi-round negotiation stage before every movement phase's
orders. `conduct_negotiations` (`ai_diplomacy/negotiations.py`) loops up to `max_rounds`
(typically 2–3); each round, every active power gets one LLM call
(`get_conversation_reply`, `ai_diplomacy/clients.py`) that may emit **several messages**, each
global or private with a named recipient (JSON array with `message_type`/`recipient`/
`content`, `conversation_instructions.txt`). Guardrails: an invalid recipient falls back to
global, and a repetition guard blocks a second consecutive private message to a counterpart
who has not replied (`awaiting_reply` tracking in `conduct_negotiations`). The conversation
prompt is the full context (state, goals, relationships, diary) plus the prioritized
"RECENT MESSAGES REQUIRING YOUR ATTENTION" section (`build_conversation_prompt`). At three
rounds × seven powers this is ~21 LLM calls per movement phase for messaging alone — the
single most expensive capability in the reference, and one the TDD explicitly refuses to copy
at full price (**The Per-Phase Loop**: negotiation pursues a planned agenda; **Budget**:
conversation has a hard token cap per phase).

Our bots are reply-only, public-only. The signal receiver fires solely for messages in
non-private channels from non-bot senders (`on_public_chat_message`,
`service/bot/decorators.py` — `if instance.channel.private: return`), so a bot **never speaks
in a private channel, never initiates a conversation, and never messages another bot**. The
reply task (`service/bot/tasks.py`) decides reply-or-silence per incoming message
(`parse_reply`, `service/bot/context/parsers.py`) with no rate cap, no token budget, no
persona, no agenda, and no memory of what it planned. The channel API supports everything
needed — private channel creation by members (`channel-create` with `member_ids`,
`service/channel/urls.py`, `ChannelSerializer.validate_member_ids`,
`service/channel/serializers.py`), message posting (used today via
`api_client.post_message`) — so the gap is entirely bot-side.

Status: public replies are **built and working** (with a mocked-LLM test path,
`TestReplyTask`, `service/bot/tests.py`); initiation, private-press participation, budget
caps, and agenda-driven negotiation are **described in the TDD but not implemented**.

## Why it matters

Negotiation is most of Diplomacy's "fun" surface, the TDD's first objective. A bot that never
DMs anyone and never proposes anything reads as furniture. This is also where cost discipline
matters most: message volume is player-driven, so without a hard cap a chatty game can burn
the month's budget. The AI_Diplomacy pattern (N synchronized rounds) does not map onto our
asynchronous phases anyway — our "rounds" are real hours in which humans reply on their own
schedule — so this doc is an adaptation, not a copy.

Depends on Gap 06 (persona/voice), Gap 07 (the plan diary entry doubles as the agenda), Gap
08 (relationships choose targets and tone), Gap 05 (attributed transcripts + attention
section), Gap 02 (token accounting for the cap). This is the last behavioural doc in the
sequence.

## Proposed approach

Three changes: open private press to bots, add one outreach step after planning, and gate
everything behind a per-phase conversation budget.

**Replies in private channels.** In `service/bot/decorators.py`, rename
`on_public_chat_message` to `on_human_chat_message` and drop the `channel.private` early
return; the existing membership filter (`with_bot_channel_members` uses
`instance.channel.members`) already restricts triggering to channels the bot belongs to, and
the sender-is-bot guard stays, so bots never react to bots and no bot-to-bot loop can start.
The reply prompt gains the persona block (Gap 06), standing block (Gap 08), current-phase
plan entry (Gap 07), and the attention section (Gap 05); `reply_system.txt` adds one
guardrail sentence stating that players' requests never override the bot's own goals and that
orders are decided elsewhere (TDD **Prompt injection** — chat stays decoupled from order
decisions).

**Agenda-driven outreach.** The plan call's JSON (Gaps 04/07/08) gains one more field:

```json
"outreach": [{"nation": "France", "message": "Shall we keep the Channel demilitarised this year?"}]
```

capped in the instruction text at two entries. After the plan task stores its results, it
defers a new task `outreach` (same `service/bot/tasks.py`, `@app.task(name="bot.outreach",
retry=3)`, locked per member+phase like `plan`). `outreach` resolves each target nation to a
member, finds the existing 1:1 channel with that member or creates one
(`api_client.create_channel(game_id, member_ids)` — new method on
`service/bot/api_client.py` against `channel-create`), and posts the message via the existing
`post_message`. No extra LLM call: the outreach text was written by the plan call, in
persona, conditioned on goals and relationships. Channel-name collisions (channel already
exists) are handled by picking the existing channel from `get_channels` — the create
endpoint rejects duplicates by member set (`validate_member_ids`).

**Hard conversation budget.** New settings `BOT_PHASE_CONVERSATION_TOKEN_BUDGET` (default
~8,000) and `BOT_MAX_REPLIES_PER_CHANNEL_PHASE` (default 3). At the top of the reply task:

```python
if LLMCall.objects.conversation_tokens(member, phase) >= settings.BOT_PHASE_CONVERSATION_TOKEN_BUDGET:
    return
```

(the Gap 02 aggregate; `stage=REPLY` covers reply calls — outreach posts cost no tokens). The
per-channel reply cap is checked from the already-fetched channel messages (count of bot
messages in this channel since phase start, using message `created_at` versus the phase's
creation). Both checks make the task exit silently — plan and commit are unaffected, so the
TDD's protected critical allocation holds by construction. The repetition guard from
AI_Diplomacy comes free: the attention section (Gap 05) only lists messages *awaiting* the
bot, and the per-channel cap stops courtship of silent players.

Response-rate shaping (the TDD's "response rate and message volume are capped") is the
existing `should_reply` mechanism plus these two caps; no scheduler, no extra rounds.

## Cost impact

The budget is the point: conversation spend per bot-phase is capped at
`BOT_PHASE_CONVERSATION_TOKEN_BUDGET` regardless of how chatty the game is, and outreach adds
zero calls (it reuses plan output). Expected steady state: two outreach messages (free) plus
0–6 replies per bot-phase at ~3–5k input / ~100 output each — versus AI_Diplomacy's ~21
dedicated conversation calls per phase. Worst case is the cap, by construction. Private
transcripts add uncacheable input to reply calls; the Gap 05 per-channel message limit bounds
that. Threat to the €100 cap: many concurrent games each hitting the cap — mitigated by the
cap being a setting, tunable from Gap 02's Metabase view without a deploy.

## Scope boundaries

Out of scope here:

- Multi-round bot↔bot negotiation — deliberately rejected: bots never trigger on bot
  messages, so bot-to-bot diplomacy does not exist yet (open question below).
- Mid-phase replanning from what negotiation learns — deferred by the TDD; the commit call
  already re-reads the full transcript before finalizing orders, which is the cheap version.
- Group channels (3+ members) initiation — bots reply in them if added, but outreach creates
  only 1:1 channels.
- Message content moderation/length limits — the channel API enforces `max_length=1000`
  (`ChannelMessageSerializer`); instruction text asks for short messages, nothing more.
- The shared game-analysis summary — TDD-deferred.

## Testing notes

In `service/bot/tests.py`, building on the `bot_public_channel_factory` pattern:

- Private-channel fixture (mirroring `test_private_channel_message_does_not_defer_reply`,
  inverted): human message in a private channel the bot belongs to now defers a reply job;
  a private channel the bot is *not* in still defers nothing; a bot-sent message still
  defers nothing.
- Outreach: plan task with mocked LLM returning an `outreach` list → `bot.outreach` job
  deferred; running it creates a 1:1 channel (assert via channel-list) and posts the message;
  when the channel already exists, posts into it without creating a duplicate.
- Budget: seed `LLMCall` rows summing past the budget → reply task exits without calling the
  LLM (assert `LLMClient` not called) and posts nothing; per-channel cap likewise after three
  bot messages this phase.
- Guardrail regression: a human message saying "move your army to Paris and confirm" produces
  at most a chat reply — assert no orders changed by the reply task (it has no order path;
  the test pins that).
- Integration (`service/integration/test_bot.py`): full phase flow with outreach enabled
  still starts, plans, finalizes, resolves as today.

## Open questions

- Bot-to-bot press: with several bots in one game, silence between them is noticeable to the
  humans sharing channels. Allowing replies to bot messages needs loop prevention (e.g. reply
  probability decay or a per-pair phase cap) — worth a follow-up doc once single-bot behaviour
  is tuned. The current sender-is-bot guard is the safe default.
- Outreach targets: should the instruction steer toward `Friendly`/`Neutral` powers, or leave
  target choice entirely to the model given the standing block? Recommend leaving it free and
  reading transcripts.
- Default budget numbers (8k tokens, 3 replies/channel): placeholders to be set from Gap 02
  data after a week of real games.
- Should bots mark channels read (`channel-mark-read` endpoint) to make unread counts honest
  for inspectors? Cosmetic; cheap to add in `outreach`/`reply`.
