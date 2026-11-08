# Diplicity

An online Diplomacy platform where people, and bots, play games of Diplomacy by turns with deadlines.

## Language

### Bots

**Bot**:
A player seat held by software instead of a person. Bots are always shown as bots.
_Avoid_: AI player, computer player, NPC

**Algorithmic bot**:
A bot that chooses orders by fixed rules, with no model calls. Shown in the UI as "Bot".
_Avoid_: Procedural bot, dumbbot (the name of one algorithmic bot, not the category)

**Inference bot**:
A bot that chooses orders and writes press using a language model. Shown in the UI as "AI bot".
_Avoid_: LLM bot

**Automatic replacement**:
A game setting under which a bot takes over any vacant seat, stepping in at the deadline of the phase that would put a player into civil disorder.
_Avoid_: Auto-fill, bot backfill

**Inference consent**:
A player's agreement, given before joining, to play in a game that allows inference bots.
_Avoid_: Opt-in, AI waiver

**Bot-only game**:
A staff-created game in which every seat is a bot, used for research and analysis.
_Avoid_: Simulation, self-play game

**Solo game**:
A private game with one human and bot opponents.
_Avoid_: Practice game, single-player game

**Algorithmic fallback**:
The orders a bot is given when it has not chosen its own by the time finalizing ends.
_Avoid_: Default orders, safe orders

### Games

**Game admin**:
The member who manages a game: the game master if there is one, otherwise the creator.
_Avoid_: Owner, host

### Phases

**Finalizing**:
The stage of a phase after orders close to humans and before adjudication, in which the bots choose their orders. Only phases in which a bot has orders to give pass through it.
_Avoid_: Processing, bot turn, thinking
