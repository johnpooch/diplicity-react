# Bots in Diplicity Technical Design

## Overview

LLM-powered bot users in Diplicity that can be added to new games or used to substitute for civil-disorder players in active games.

## Objectives

This project has two primary objectives:

- **Fun:** Bot users must be fun to play against. See **Evaluating Quality**.
- **Affordable:** Bot users should be free for players while keeping LLM costs sustainable on a hobby-project budget. See **Budget and cost saving**.

## Product

Bot users appear throughout the system like human users: username, display name, profile picture, player info, chat, and orders. They are marked with a "bot" badge on their player card. Each bot also has a persona that shapes how it plays and communicates (see **Personas**).

Game admins can add bots in several ways:

- during game creation
- while the game is staging
- by replacing a civil-disorder player mid-game
- automatically when a player enters civil disorder, if configured at game creation

During a game, bots behave like human players. They negotiate and submit reasonable orders every phase.

Bots can chat in public press, private group channels, and one-to-one private channels. Response rate and message volume are capped to prevent abuse and control LLM cost. See **Budget and cost saving**.

When all human players have confirmed their orders, humans enter a brief lockout while bots submit. If some humans have not confirmed, bots submit shortly before the phase deadline.

Bot users cannot see any information unavailable to a human player in the same position.

## Personas

Each bot has a **persona** with two parts:

- **Disposition** — how it plays and negotiates (e.g. risk tolerance, aggression, willingness to ally or betray).
- **Voice** — how it writes in chat (e.g. clipped and formal vs warm and expansive).

Personas make bots distinct from each other. **Voice** shapes the tone and wording of chat messages. **Disposition** may also influence order selection and negotiation strategy — how far persona should affect tactical choices is still open.

Whether personas should read as realistic human players or deliberate caricatures is **deferred**; we will experiment and let player response guide the default.

## Architecture

**The `game` app should know nothing about bot runtime.** All bot behavior lives in a separate `bot` Django app within the same service and database. At runtime, the `bot` app never calls into game business logic directly — it acts as a player, using existing API endpoints via an authenticated test client.

The `bot` app registers signal receivers on game models (`Phase`, `PhaseState`, `ChannelMessage`). When those models are saved through normal game flows, the receivers queue background tasks (Procrastinate). The `game` app does not import or invoke the `bot` app.

## The Per-Phase Loop

Each phase, a bot runs three stages:

- **Plan:** At phase start, the bot reads the game state, dynamics, and conversation history. It drafts provisional orders and a negotiation agenda.

- **Negotiation:** During the phase, the bot pursues that agenda — opening conversations and responding to other players.

- **Commit:** Before the phase closes, the bot re-reads the game state and conversation, finalizes its orders, and confirms.

Mid-phase replanning (revising orders as negotiation unfolds) is deferred to control LLM cost.

**Future: shared game analysis.** A single LLM call at phase start could summarize game dynamics for all bots in a game, since every player sees the same board. That summary would live in the shared context block (see **Context**) and reduce per-bot token use.

## Context

LLM prompts are split into two layers so we can cache the expensive part.

**Shared context** is identical for every bot in a game. It describes facts any player could see: the current phase, unit locations, supply-center ownership, and legal orders for all nations. Order options include tactical annotations — nearest enemy units and supply centers (with distances), adjacent territories, and which units can move or support there — so the model can reason without re-deriving map geometry each call.

Because this block does not depend on which nation the bot plays, it can be cached across bots and across calls within a phase. That is the main lever for keeping LLM cost sustainable (see **Budget and cost saving**). A future shared game-dynamics summary (see **The Per-Phase Loop**) would also live here.

**Private context** is nation-specific and changes as the bot plays. It carries the bot's persona, goals and relationships with other players, an internal diary of plans and reasoning (updated across the phase loop), and the message history relevant to the current call. This layer cannot be shared between bots, so it is not cached.

Each call assembles: shared context, then private context, then the task-specific instruction (plan, reply, or commit).

## Evaluating Quality

We evaluate quality in two dimensions: **tactical competence** and **fun**. We will not build a formal eval harness up front — we read transcripts, play against the bot, and add metrics only to lock in fixes for problems we have already identified by hand.

**Tactical competence.** Capped self-play against **Dumb Bot** (one LLM bot vs six Dumb Bots, and the reverse). Primary metric: average supply-center share, not win rate — share above ~14% (the equal split) indicates the bot beats the baseline. Eval cost is excluded from the monthly budget (see **Budget and cost saving**).

**Fun.** Judged through direct playtesting (see **Telemetry and observability**).

## Budget and cost saving

Bot LLM spend must stay under **€100 per month**. Players will not pay for bot usage. Eval runs are excluded from this cap. We may exceed the target briefly during development if the path to savings is clear.

Monthly spend is hard to forecast: games may have one bot or seven, phase deadlines vary in length, and chat volume is player-driven. Cost control therefore happens at **phase granularity**, not by predicting game volume.

Each bot will have a **fixed token budget per phase**, split between conversation and critical prompts (plan and commit). Conversation will have a hard cap — once exhausted, the bot stops replying for the rest of the phase. Plan and commit will always run; their allocation is protected so chat cannot prevent orders from being submitted.

Other cost levers:

- cheap model and hosted inference (see **Model**)
- shared prompt caching (see **Context**)
- fewer LLM calls per phase (see **The Per-Phase Loop**)
- message length and rate limits on human and bot chat (see **Product**)

We will monitor token use against these budgets and the monthly cap (see **Telemetry and observability**).

## Model

Bots will need a capable but cheap LLM. We will use a pay-per-token API rather than host our own model — self-hosting would need a GPU and exceed the hobby budget at our expected volume (see **Budget and cost saving**).

Our target is an open-weights **Qwen 3** model in the ~24B class (e.g. Qwen3-32B), served through a hosted inference API. Evaluations of out-of-the-box LLMs in full-press Diplomacy suggest models around this size play competently at roughly €1 per game. Tactical quality will depend more on prompt design (see **Context**) than on chasing the largest model. Open weights will also leave room to self-host later if volume ever justifies it.

During early implementation we will use **Claude Haiku** while the per-phase loop and context layers are built out. Once the system works end-to-end, we will switch to the Qwen endpoint and tune for cost.

## Prompt injection

Players may try to manipulate a bot through chat — instructing it to move a unit a certain way, ignore its goals, or override its persona. This risk is higher with a cheaper, weaker model (see **Model**).

The primary guardrail is to **decouple chat from order decisions**. Plan and commit will not treat player messages as authoritative instructions; order selection will rely on game state, the bot's diary, and its persona (see **Context**, **The Per-Phase Loop**). Negotiation is a separate LLM call from commit, so an injected chat prompt cannot directly write orders without passing through a distinct decision step.

Even a fully compromised bot has limited blast radius. It can only send chat messages and submit legal orders — the same actions available to any player. It cannot access other accounts, admin functions, or anything outside the game.

## Telemetry and observability

Two goals: **cost visibility** — token spend per call, bot, phase, game, and over time — and **inspection** — read a bot's diary, plans, chat, and provisional vs final orders as a phase unfolds (see **Evaluating Quality**).

We will build this in Postgres and Metabase rather than adopt a separate observability stack. External tools add infrastructure we do not need on a hobby budget, and they cannot attribute spend to game domain concepts (phase, stage, bot) unless we thread that metadata anyway.

**Cost tracking.** Every LLM call will write one row at the client, capturing token usage (including cache read/write splits), computed cost, latency, status, and foreign keys to game, phase, member, and stage (plan, negotiate, commit, reply). Cost will be computed in Django from a versioned price table — provider responses give tokens, not dollars. Metabase will dashboard spend against the monthly cap and per-phase budgets (see **Budget and cost saving**), with thresholds when usage exceeds expectations for a stage.

**Inspection.** Bot reasoning will live in structured rows keyed to member and phase — diary entries, relationships, and provisional vs final orders — linked back to the LLM call that produced them. A staff-only inspector page will poll these rows during an active phase (writes happen in background tasks, not the request cycle). Full prompt/response capture will be opt-in to limit storage and protect hidden game information.
