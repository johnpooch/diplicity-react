---
name: bot-research
description: Prior-art catalogue and research playbook for the LLM-driven Diplomacy bot. Use when researching how to build or improve the bot — evals, the phase loop, board representation, when/how the bot talks, memory/trust, or baseline opponents — or when studying how other open-source Diplomacy / LLM-agent projects structure their code. Knows which projects and papers to read and where the relevant code lives in each.
allowed-tools: Task, WebSearch, WebFetch, Read, Grep, Glob, Bash
---

# Bot Research

This skill is the standing knowledge base for building the **LLM-driven Diplomacy
bot** for diplicity. The aim of the bot is **to be fun to play against**, not to be
maximally strong — almost all prior art optimises for strength, so its machinery is
reusable but its goal is not ours. Keep that distinction in mind when reading anything
linked here.

It exists so that recurring research questions ("how does Cicero ground dialogue?",
"what does Every's diary look like?", "how do we measure play quality?") can be
answered by reading a known source rather than re-discovering it from scratch.

## When to use this

- Studying how an existing project (Cicero, Every's AI_Diplomacy, etc.) structures its
  code — which files to open and what each one does.
- Looking for prior art on a specific bot design question (evals, negotiation timing,
  board representation, trust/memory, baseline bots).
- Kicking off a new round of deeper research on any of these topics.

## Index

- **[resources.md](./resources.md)** — annotated catalogue of every project and paper,
  with URLs, what each is good for, and **the specific files to read** inside the
  open-source repos. Start here for "where do I look for X".

## How to do a round of bot research

The catalogue was built by fanning out parallel research agents, one per topic. Repeat
that pattern for new questions:

1. Scope each question tightly and give one agent per topic (`Task`, `general-purpose`,
   run in background for concurrency).
2. Tell each agent to **fetch primary sources directly** (the repo code and model
   cards, the paper PDFs), **cross-check** claims across sources, and **tag confidence**
   (fact / inference / speculation).
3. Have each agent **write a cited markdown report** to a scratch dir and return a short
   summary. Fold durable findings back into `resources.md` / `findings.md` here.

### Egress caveat (important)

In cloud sessions the proxy frequently **blocks `arxiv.org`, `science.org`,
`ai.meta.com`, and `aclanthology.org`** (403), while **`github.com` and
`raw.githubusercontent.com` are reachable**. So:

- Prefer reading the **open-source repo code and model cards** — they are reachable and
  are the highest-confidence source anyway.
- Any figure quoted from a *blocked* paper (e.g. Cicero's league results, Richelieu /
  DipLLM win rates) currently comes from **search snippets, not primary text** — treat
  those numbers as unverified and re-check before quoting externally.
- To try to unblock a host, see `/root/.ccr/README.md` and
  `curl -sS "$HTTPS_PROXY/__agentproxy/status"` for per-tool fixes. Never disable TLS
  verification.

## Our own bot code

Don't forget the code already in this repo — it is the most relevant resource of all:

- `service/bot/llm.py` — already implements **per-unit, index-constrained selection
  from engine-computed legal moves** (illegal moves impossible by construction; fully
  variant-agnostic). This is the orders core other projects converge on.
- `NationView` (`service/adjudicator/types.py`) — already computes the per-nation board
  context the bot needs as prompt input.

(Paths verified at time of writing; re-check with `grep`/`glob` if the bot app moves.)
