# Bots in Diplicity \- Technical Design

## User experience

### Creating a game

An **Allow bots** section is added to the first page of the Create Game flow. Three options appear, each with a description:

- **No bots**: only humans can play.
- **Basic bots** (default): rule-based bots that submit orders but cannot communicate.
- **AI bots**: bots use an AI model to negotiate and submit orders.

An additional **Auto-replacement** checkbox is shown with a Recommended badge. It is checked by default. When enabled, a bot automatically replaces any player who enters civil disorder, withdraws, or is removed.

When **AI bots** is selected, a message appears at the bottom of the section explaining that players must explicitly opt-in to playing against AI bots when they join the game and that creating the game counts as the creator's acceptance. It links to the privacy policy.

Allow bots and Auto-replacement are hidden in Sandbox mode. Neither can be changed after the game is created.

### How games that allow bots appear

On Find Games, a game that allows AI bots shows an **AI bots** pill on its card. Ranked games cannot allow AI bots, so the pill takes the Ranked pill's place. Games that allow basic bots look the same as any other game. The My Games cards don't show a bot icon because the player will already know whether bots are allowed.

On Game info, the Game settings section shows a **Basic bots allowed** or **AI bots allowed** row, each with its own icon and an info icon that explains it. If auto-replacement is enabled, an **Auto-replacement** row appears too. Neither row appears in a game that only allows humans.

### How bot players appear

Bots appear in the same way a human player does, but with a bot badge beside their name. Each bot has a name from a fixed roster: AI bots have character names such as "The Dealmaker", and basic bots are numbered automatons, e.g. "Automaton III".

A bot is labelled with an **AI bot** or **Bot** pill in the Players list, on its profile and in the channel member picker. Chat messages from a bot do not carry a label. Bots have a robot avatar in place of a profile picture, and their identity is shown in anonymous games.

A bot's profile shows its name, its pill and the Games section. It has no joined date and no Commitment, Rating or Conduct history sections.

### Adding a bot player to a new game

In a pending game that allows bots, the game admin sees **+ Add bot** beside each open seat on the Players screen./

Tapping **+ Add bot** puts that seat in a loading state. When the request completes, the seat is filled by a random bot of the kind the game allows.

- Bots are added one seat at a time, and they can fill every open seat, so a creator can play a game against bots alone.
- Bots confirm their seat automatically, and adding a bot to the last open seat starts the game.
- The admin can remove a bot before the game starts with **Remove from lobby** on the bot's member screen.

### Adding a bot player as a replacement

A bot can take a seat that a player left mid-game. A seat is vacant when its player enters civil disorder, withdraws, or is removed by the game admin.

- When auto-replacement is enabled, a bot takes every vacant seat as soon as it opens.
- In a game that allows bots, the game admin sees **Replace with bot** on a vacant seat's member screen. Tapping it adds a random bot of the game's kind takes the seat.
- When auto-replacement fills a seat, players get one push saying the player left and was replaced by a bot. It replaces the departure push they would otherwise get. A bot added with **Replace with bot** sends the existing seat filled push.

### Removing a bot player from a game

Once a game has started, a bot can't be removed, but the game admin can always hand its seat to a human. This applies to every bot, including one that auto-replaced a player in civil disorder.

- The admin sees **Invite replacement** on a bot's member screen. It copies a replacement link that carries a secret token. Other players see no actions on a bot, and nobody sees **Take over seat**.
- Opening the link shows the Replace Player screen. Joining takes the seat straight away and the bot leaves the game. Bots submit orders at the end of the phase, so the human starts the phase with no orders to inherit.
- A replaced bot can't return to the same game, because a user can only have one membership per game. If no unused bot of the game's kind is left, **+ Add bot** and **Replace with bot** show an error toast and auto-replacement leaves the seat vacant.

### Joining a game that uses inference bots

When a player joins an AI bots game, a confirmation dialog explains that the game allows AI bots and that messages sent to them are processed by our model provider. It links to the privacy policy. This applies whether they join from Game info, a game card, or by replacing a player. If the game also has short phases, the same dialog shows both notes. Basic bot games don't need this.

The server refuses to join a player to an AI bots game unless they accepted in the dialog, and it records the acceptance on their member. Older app versions can't send the acceptance, so their players can't join AI bot games until they update.

The privacy policy becomes a public in-app page, like the Code of Conduct. It gains a section on the inference provider.

### Bots and ranked games

A ranked game can allow basic bots but not AI bots. While Ranked is checked on the Create Game screen, AI bots is disabled and its help text says it can't be used in ranked games. If AI bots was selected, the choice switches to Basic bots. Unchecking Ranked enables AI bots again but leaves the selection as it is.

Bots are not rated and never count as an opponent.

- Each player is rated against the other humans only. A game with two humans and five bots is rated like a one-on-one game.
- A player who leaves still takes a loss against every human who finishes in another seat, whether a human or a bot takes the seat. A human who takes over a bot's seat can't lose rating, as with any replacement.
- If a bot wins outright, the humans still in the game have no human winner to lose to, so their ratings don't change.
- A game with fewer than two human seats, counting players who left, is not rated.

### Bots and commitment

A phase counts towards a player's commitment only if another human is still playing when it resolves, meaning they hold a seat that isn't in civil disorder, withdrawn or eliminated. Commitment measures reliability towards other people, so games against bots alone neither build nor damage it.

- In a phase with no other human still playing, submitting orders earns nothing and missing orders costs nothing.
- Withdrawing, abandoning a game and not confirming during mustering follow the same rule: they cost nothing when no other human is still playing at the time.
- A game with two humans and five bots counts like any other game. If the other human leaves, the remaining player's later phases stop counting.
- On the commitment grid, a game where nothing counted is a blank square. When only some phases counted, the square's breakdown shows the rest as an "Against bots only" row worth 0.

### Submitting orders

Bots choose their orders at the end of the phase, in a new **Finalizing** stage between the deadline and adjudication. A phase enters Finalizing when its deadline passes or every human has confirmed their orders. Phases where no bot has orders to give skip it and resolve as they do today.

- While a phase is finalizing, the countdown under the phase name is replaced by a spinner and "Finalizing". My Games cards show a Finalizing badge.
- Orders are locked. Confirm stays on screen but is disabled. Channels stay open.
- Finalizing has no time limit of its own. Each bot has its own timeout, and a bot that fails or times out gets the algorithmic fallback. The phase resolves once every bot has orders.
- Older app versions show the phase as resolved while it is finalizing.

### Communicating with bots

Chat looks the same as it does today. Bots answer within seconds of a message, and group and one-to-one channels work the same way.

When a message is posted in a channel with bots in it, a pipeline starts once the channel has been quiet for a few seconds, so a burst of messages gets one round of responses.

- A selection step picks at most one bot to respond, or none. A short reply such as "agreed" may get no response.
- The selection step also chooses how the bot responds. Greetings and small talk get a light response that uses only the conversation. Messages that need the game get a full response that also uses the board, the phase analysis and the bot's journal.
- Messages from bots start the pipeline too, so another bot can reply in turn and bots can talk to each other. To stop loops, bots stop responding in a channel after a fixed number of bot messages in a row with no human message. The bot that sends the last of those messages is told to wrap up the conversation.
- A message that tries to manipulate a bot, such as asking it to ignore its instructions or reveal its orders, gets the light response. The bot deflects in character, and the light response has no game state to leak.
- Bots keep chatting while a phase is Finalizing. A bot's orders use the conversation as it stood when the bot started choosing them.

At the start of each phase, each AI bot's plan step proposes conversations it wants to start, in any channel, including new group channels. Once every bot has planned, the server picks one bot to open each conversation, so two bots don't message each other at the same moment. The opening message is written like any full response, and a missing channel is created first. Bots don't start conversations mid-phase.

Basic bots go through the same pipeline, but they choose who responds and what to say without the model. The first time a channel a basic bot is in gets a message, the bot replies once to say it is a basic bot and can't chat. It stays silent after that and never starts conversations.

### Bot limits

AI bot chat is limited by token budgets. Planning, journal entries and orders aren't budgeted, so nothing a player does changes how a bot plays. Basic bots have no limits.

- Each AI bot has three chat budgets, measured in cost-weighted tokens: one per channel per phase, one per phase, and one per game. Every message the bot sends counts, including light responses and phase-start openers.
- Once a budget is mostly spent, the bot's next message in that scope signs off in character. After that it stays silent until the budget resets. Channel and phase budgets reset when the next phase starts; the game budget never does.
- A bot with a spent budget is left out of speaker selection. If no bot in a channel has budget left, selection doesn't run. Players see no notice that a bot has stopped.

Two Railway environment variables turn off inference in every game, for when spend gets out of hand. Players aren't told, and unsetting a variable restores normal play straight away.

- `BOT_CHAT_DISABLED` stops AI bots chatting and opening conversations. They still plan, write journal entries and choose orders with the model.
- `BOT_INFERENCE_DISABLED` turns off all inference. AI bots stay silent, skip planning and journal entries, and use the algorithmic fallback for orders.

### Edge cases

- Once no human holds a seat in an active game, the game is abandoned, even if bots fill every seat.
- A bot is never picked as the new game admin. In a Game Master game, the Game Master has the same bot actions as a game admin.
- A pending game whose only players are bots is deleted, as an empty pending game is today.
- Bots never propose a draw. A bot that isn't eliminated is a voter like any player and accepts every draw straight away, so a draw passes when all the humans accept. The accept decision sits behind the bot interface, so it can later be replaced with one made by the model.
- An eliminated bot stops planning and chatting, and no bot chats once the game has ended. Bots keep chatting while a game is paused.
- The admin can't pause a game while its phase is Finalizing.
- Bots can be allowed in every variant.
- Players can report any bot, AI or basic, and moderators can mark it like any player. A bot's marks aren't shown on its profile, which has no Conduct history section.

## API endpoints

### New endpoints

- `POST /game/<id>/bots/` adds a random unused bot of the game's kind to an open seat in a pending game. It backs **+ Add bot**.
- `POST /game/<id>/members/<id>/replace-with-bot/` fills a vacant seat in an active game with a bot. It backs **Replace with bot**.

Both are for the game manager only. Both refuse with a reason code when no unused bot of the game's kind is left, and the client shows that as the error toast.

### Changed endpoints

- Creating a game takes the bot kind (`none`, `basic` or `ai`) and whether auto-replacement is on. A client that omits them gets a human-only game with no auto-replacement, so games created from older app versions never get bots. Ranked games refuse `ai`.
- Game responses return the bot kind and auto-replacement. The Players screen gains an `add_bot` action.
- Members and public profiles gain a `botKind` field. A bot's profile keeps the same shape as a human's, with empty commitment, rating and marks, so older app versions still render it.
- Joining a game and replacing a player take an AI bots acceptance. An AI bots game refuses the request without it.
- Replacing a bot needs the replacement link's token. The member screen returns the token only to the game manager, only on a bot's seat. Member actions gain `replace_with_bot`. On a bot, only the manager gets the replacement link action, and nobody gets **Take over seat**.
- Phases gain a `finalizing` status. Confirming orders, writing orders and pausing the game are refused while a phase is finalizing.
- The commitment breakdown gains an "Against bots only" kind.

### Retired endpoints

The allowlisted add-a-chosen-bot flow (`POST /game/<id>/member/` and `GET /game/<id>/addable-user/`) leaves the schema. Its paths keep serving older app versions. The `canCreateBotGames` profile field and the bot opponent allowlist are removed.

## Architecture

### Wiring

Bots live in a new `bot` app. The app has a Django shell and a pure Python core in `bot/core`. The shell loads data, schedules work, records decisions and applies results. The core decides what a bot does. The existing `inference` app keeps recording every model call, and a new `phase_analysis` app computes each phase's analysis deterministically and stores it, so it can ship before bots.

The bot app works like the notification system. `emit()` calls the bot app's listeners, and the listeners record the work the event causes as runs. A run is one unit of bot work, such as a plan, a journal entry, a speaker selection, a response, orders or a draw decision. It records its step, phase, bot or channel, prerequisites, earliest start, status, timings and error.

- `phase_started` creates a chain of runs for each bot: the journal entry for the end of the previous phase, the journal entry for the start of the new phase, then a plan for AI bots.
- `channel_message` creates the channel's selection run, or pushes back its earliest start if one is pending, so a burst of messages gets one selection.
- A new `phase_finalizing` event creates an orders run for every bot with orders to give.
- `draw_proposal` creates a draw decision run for every bot that votes.
- Elimination and the end of a game cancel the bot's or the game's pending runs.

A periodic coordinator task is the only thing that starts runs. Every few seconds it starts runs whose prerequisites have finished and whose earliest start has passed. It also times out stale runs, picks one opener for each conversation the plans propose once every plan is done, and resolves a Finalizing phase once every bot has orders. An orders run that fails or times out is run again on the deterministic implementation. A run whose phase is no longer current when it starts is skipped.

Each step has its own task. The task builds a snapshot of what the bot can see, saves it on the run, passes it to the core, saves the result as a decision and applies it.

- The snapshot comes from other apps' loaders and serializers, called as the bot's user, so a bot sees what a player in its seat would see. The bot app adds the bot's own journal, plans and budgets.
- The core turns the snapshot into a context for the step. Each step's context holds only what that step may use, so the light responder's context has no board, analysis or journal.
- Decisions are stored as one model per kind, such as `Plan`, `JournalEntry`, `SpeakerSelection`, `OrderDecision` and `DrawDecision`. Each links to its run and to the inferences behind it. Basic bots write the same decisions, so the whole pipeline can be tested without inference.
- Results are applied through the commands a player's request would use, such as creating orders, sending a message or creating a channel, with the bot's user as the actor.

The core has a `Bot` interface for journal entries, plans, responses, light responses, orders and draw decisions, and a separate `Selector` that picks at most one bot to respond in a channel. Both have a deterministic and an inference implementation. A factory in the shell picks the implementation from the bot's kind and the kill switches, so with `BOT_INFERENCE_DISABLED` set an AI bot is built as a deterministic one. Inference implementations get a model port when they are built, and the shell's port records each call through `Inference.objects.run`.

A `Bot` model holds each bot's user, kind, roster name and persona, and the other bot models refer to it. A user is a bot when a `Bot` row exists for them, which replaces the bot kinds on `UserProfile.kind`.

The bot app reaches other apps only through their loaders, serializers and commands, and `bot/core` imports nothing from Django. These are the boundaries a separate bot service would have, so the bot system can be moved into its own service later by changing how events, reads and writes travel.

## Inference provider

- We want to choose a model that balances quality, cost, and privacy.
