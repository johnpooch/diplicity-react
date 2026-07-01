# Gap 05: Message and Negotiation-History Serialization

## Gap statement

AI_Diplomacy serializes conversation and outcome history with structure aimed at negotiation
quality. `get_messages_this_round` (`ai_diplomacy/game_history.py`) splits the current phase
into a **global messages** section and **per-counterpart private conversation** sections, each
line attributed `SENDER: content`. `get_recent_messages_to_power` surfaces the last three
messages addressed to the power, injected into the conversation prompt as "RECENT MESSAGES
REQUIRING YOUR ATTENTION" (`build_conversation_prompt`, `ai_diplomacy/clients.py`).
`get_ignored_messages_by_power` detects counterparts who have not replied across recent phases
and feeds a "POWERS NOT RESPONDING TO YOUR MESSAGES" block into the negotiation-diary prompt
(`generate_negotiation_diary_entry`, `ai_diplomacy/agent.py`). Alongside messages,
`get_order_history_for_prompt` renders the previous movement phase's **orders with outcomes** —
`(success)`, `(bounce)`, `(void: no effect)`, `(Rejected by engine: invalid)` — for all powers,
which is what lets an agent notice a betrayal by comparing promises against resolved moves.

Our serialization (`service/bot/context/builder.py`) is a raw transcript dump.
`with_conversations` concatenates **every message of every channel the bot is in, for the whole
game**, unbounded. Each line is rendered by `_message_role` as `user:` or `assistant:` — the
sender's **name and nation are discarded**, so in a public channel with six opponents the model
sees six indistinguishable `user:` voices (the sender name is available in the payload —
`ChannelMessageSerializer` includes `sender` with nation, `service/channel/serializers.py:17` —
and even in the bot's own `ChatSenderDict` type, `service/bot/types.py`). There is no
this-phase/earlier split (messages carry `created_at` but it is unused), no
needs-response section, no ignored-counterpart tracking, and **no order history at all**: the
bot never sees what anyone (including itself) did last phase, even though resolved orders for
completed phases are visible to every player via the order-list endpoint
(`Order.objects.visible_to_user_in_phase`, `service/order/models.py:16` — all orders once
`PhaseStatus.COMPLETED`; `order-list` route in `service/order/urls.py`), with per-order
resolution status (`OrderResolutionSerializer`, `service/order/serializers.py:34`).

Status: transcript inclusion is **built and working** but lossy and unbounded; attribution,
structure, order history, and attention/ignored tracking are **not implemented** (the TDD's
private-context section assumes "the message history relevant to the current call").

## Why it matters

Sender-less transcripts make coherent negotiation impossible — the bot cannot tell an ally's
proposal from an enemy's threat, so replies read as generic and "presence" collapses. The
missing order history blocks any betrayal/collaboration awareness (Gaps 07/08 need it as
input). Unbounded transcripts are also a live cost bug: a chatty long game grows every prompt
linearly, directly against the fixed per-phase budget.

Depends on: nothing hard; pairs naturally with Gap 03. Feeds Gaps 07 (phase retrospective), 08
(relationship updates), 09 (negotiation loop).

## Proposed approach

All changes in `service/bot/context/` plus one fetch addition.

**Attribute and bound messages.** Rewrite `_format_channel`
(`service/bot/context/builder.py`) to render:

```
Channel: Public Press (public)
  England (you): Anyone interested in a western truce?
  France: Depends what you mean by truce.
```

Sender name and nation come from the message payload's `sender` (extend `ChatMessageDict` /
`ChatSenderDict` in `service/bot/types.py` with the nation already serialized by
`ChannelMemberSerializer`); the bot's own lines are tagged `(you)` instead of relying on
role labels. Keep the user/assistant role mapping only where the reply task builds actual
multi-turn message arrays — for pasted transcripts, names beat roles.

Bound the transcript: last `BOT_CHANNEL_MESSAGE_LIMIT` (default 15) messages per channel, and
skip channels with no messages. This replaces "whole game history" with "recent, relevant" at
a fixed token ceiling.

**Needs-response section.** New builder method `with_attention(channel_id=None)` emitting up
to three most recent messages that (a) are not from the bot and (b) arrived after the bot's
last message in that channel — the cheap equivalent of `get_recent_messages_to_power`:

```
Messages awaiting your reply:
  From France in Public Press: "Depends what you mean by truce."
```

Computable from data already fetched (`channels` with ordered messages,
`service/bot/context/fetch.py`); no new endpoint.

**Order history with outcomes.** `service/bot/api_client.py` gains
`get_orders(game_id, phase_id)` against the existing `order-list` route. `fetch_context` looks
up the previous phase id (`previous_phase_id` on the current phase payload,
`service/phase/serializers.py:67`) and, when it exists, fetches that phase's orders into
`ContextData["previous_orders"]`. New builder method `with_order_history()` renders, grouped
by nation and sorted deterministically:

```
Previous phase (Spring 1901, Movement) orders:
  England: F lon -> nth (succeeded), A lvp -> yor (succeeded)
  France: A par -> bur (bounced by mun)
```

Resolution strings come from `resolution.status` / `resolution.by` in the order payload. This
section is shared context — every player can see resolved orders — so it belongs in
`build_shared` and joins the cacheable prefix (Gap 10).

**Ignored-counterpart tracking: cost-bounded approximation.** AI_Diplomacy's
cross-phase ignored-message detection exists to feed an extra diary LLM call we are not
making. Approximate it with zero extra calls: the attention section already encodes "who is
waiting on you", and Gap 08's relationship update sees the transcript, from which
non-response is inferable. A dedicated ignored-tracking structure is deliberately dropped;
revisit only if transcripts show bots endlessly courting silent players.

## Cost impact

No new LLM calls. Net token effect is a **reduction with a ceiling**: today's unbounded
transcript is replaced by ≤15 messages/channel (~25 tokens each ⇒ ~400 tokens/channel), an
attention section (≤3 messages), and an order-history block (~15–40 lines, ~200–500 tokens).
One extra API fetch per task run (previous-phase orders) — DRF test-client call, no LLM cost.
The order-history block is shared and cacheable; per-channel transcripts are private and are
the main uncacheable payload, which the message limit now bounds.

## Scope boundaries

Out of scope here:

- Sending messages, initiating channels, reply gating — Gap 09.
- Storing summaries of old conversation (diary/consolidation) — Gap 07.
- Relationship inference from the transcript — Gap 08.
- Multi-phase order history (AI_Diplomacy shows one movement phase back; we match that and no
  more).
- Any backend/channel-API change — everything reads existing endpoints.

## Testing notes

In `service/bot/tests.py`, extending `TestContextBuilder`:

- Channel rendering shows `Name (nation)` attribution and `(you)` tagging; message #16 of a
  17-message channel fixture is present while #1 is not (limit enforcement).
- `with_attention`: bot's last message older than two human messages → both listed; bot spoke
  last → section omitted.
- `with_order_history`: fixture `previous_orders` payload renders grouped, outcome-tagged,
  deterministically sorted lines; no previous phase → section omitted.
- `fetch_context`: with a mocked client (pattern from `TestAdjustmentOrderLimit._fake_client`),
  assert the extra order-list GET happens only when `previous_phase_id` is set.
- Integration: after resolving the first phase in the `test_bot_can_play_the_next_phase` flow
  (`service/integration/test_bot.py`), assert the second `plan` call's prompt (capture via
  patched `LLMClient`) contains the previous-phase order lines.

## Open questions

- Is 15 messages per channel the right bound, and should the public channel get a larger
  budget than 1:1 channels? Needs transcript review once real games run.
- Should the bot's own **unsent plans** ever appear here? No — that is diary material (Gap
  07); flagged only to keep the boundary explicit.
- The order payload's resolution vocabulary (`get_status_display` values) needs a short
  legend in the prompt if the strings turn out cryptic in practice — decide after reading real
  payloads.
