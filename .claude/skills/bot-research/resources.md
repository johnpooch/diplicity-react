# Bot Research — Resource Catalogue

Annotated index of prior art for the LLM Diplomacy bot. Grouped by the question it
helps answer. For each open-source project, the **files worth opening** are listed so a
code-structure study can go straight to the relevant code.

> Confidence: repo code and model cards were read directly and are high-confidence.
> Figures from papers on blocked hosts (arxiv / science / meta / aclanthology) are
> snippet-sourced — see the egress caveat in `SKILL.md` and re-verify before quoting.

---

## The two reference implementations (read these first)

### Cicero — `facebookresearch/diplomacy_cicero`
Meta's human-level Diplomacy agent. **Not** our architecture (classical-map-only
training, an RL planner rather than a general LLM), but the source of the
plan-then-speak, draft-then-filter, and when-to-speak ideas. Best for: dialogue
grounding, message filtering, chattiness control.

Files to open:
- `fairdiplomacy/pseudo_orders.py` — the "intent" representation (`PseudoOrders` /
  `JointAction`): a structured per-power set of intended orders, generated *before* prose.
- `fairdiplomacy/agents/parlai_message_handler.py` — the **sleep gate** (when/whom to
  message, per-recipient; `INF` = stay silent; separate initiate-vs-reply thresholds),
  pseudo-order caching, and filter orchestration.
- `parlai_diplomacy/utils/game2seq/format_helpers/message_editing.py` —
  `MessageFiltering` / `FilterReasons`: the generate-then-filter battery (grounding /
  consistency / nonsense / toxicity).
- `fairdiplomacy/agents/br_corr_bilateral_search.py` — the strategic planner.
- `fairdiplomacy/annotate/lie_detection.py` — broken-commitment / honesty annotation
  (communicated intent vs final action).
- `model_cards/` — `imitation_intent.md`, `dialogue.md`, `sleep_classifier.md`,
  `nonsense_ensemble/README.md`. The model cards state the designs plainly and are the
  most reachable, highest-signal read.

Papers (often blocked — snippet-sourced figures): Science 2022,
`https://www.science.org/doi/10.1126/science.ade9097`; TR PDF
`https://noambrown.github.io/papers/22-Science-Diplomacy-TR.pdf`.

### Every's AI_Diplomacy — `EveryInc/AI_Diplomacy` (also `Alx-AI/AI_Diplomacy`)
Off-the-shelf prompted LLMs that negotiate in chat and emit engine-validated legal
orders, no fine-tuning. **This is the closest existing implementation of our design** —
the best starting point for code structure. Backed the 2025 frontier-model tournament
(Twitch + GoodStartLabs leaderboard).

What it contains (confirm exact paths in-repo):
- BFS-pathfinding board context (its answer to board representation).
- Multi-round private + global negotiation.
- A three-tier per-power **diary** with **yearly summarization** (= our "consolidate"
  phase).
- A 5-level **Enemy↔Ally trust scale** (= the trust registry).
- Order validation against the `diplomacy` engine's `get_all_possible_orders()`.

---

## Q: How do we measure quality of play? (evals)

- **Sum-of-Squares game score** — outcome metric; an equal-skill agent baselines at
  **1/7 ≈ 14%** board share. Use share-of-board, not win-rate (outright wins are rare).
- **Frozen-baseline self-play** — 1v6 / 6v1 against DumbBot or DipNet; the standard
  cheap comparison. (DumbBot source below.)
- **TrueSkill / Elo pools** for ranking many variants (watch the league "flat Elo" trap
  — keep a frozen suite).
- **Normalized-rank-among-top-N** (our idea) — sound, effectively unpublished for
  Diplomacy; precedent is **ChessBench Action-Ranking** (Kendall's τ vs. engine). Do it
  **per-unit** (joint action space ~10²⁰).
- **Maia** chess work — evidence that move-matching accuracy is **decoupled from**
  strength; don't optimise "matches best/human move".
- **SPIN-Bench** — LLM-judge rubric for negotiation quality.
- **Landmine:** the **webDiplomacy / DipNet corpus (~156k games)** license **forbids
  training website-deployed bots** — conflicts with our use case. Offline eval only, or
  self-generated labels.

## Q: How does a phase work?

See Cicero above (`pseudo_orders.py`, `parlai_message_handler.py`,
`br_corr_bilateral_search.py`): structured intent first, prose conditioned on it,
**continuous re-planning** around each message, final orders at the deadline.

## Q: How do we represent the board / how much do we help the LLM?

- **"Democratizing Diplomacy: A Harness for Evaluating Any LLM on Full-Press
  Diplomacy"** — arXiv 2508.07485. Data-driven *textual* board representation that lets
  any off-the-shelf LLM play full-press with no fine-tuning. Most relevant to our
  variant-agnostic, no-training constraint.
- **DipLLM** (ICML 2025) — fine-tunes; **no-press only**; transferable gem is **per-unit
  autoregressive order selection** (mirrors our `bot/llm.py`).
- **DAIDE press language** — a proven, variant-agnostic **commitment ontology**
  (`PRP`, `ALY/VSS`, `DMZ`, `XDO`, `PCE`, `DRW`, …) for a structured-commitments chat
  side-channel.
- **godip** (diplicity's engine) exposes legal orders as a recursive
  `Options map[OptionValue]Options` tree; diplicity flattens it into indexed legal
  options — what `bot/llm.py` selects from.
- ML feature tensors (DipNet / Cicero strategic core) are per-province and map-specific
  — useful only as a checklist of which facts matter, not as a representation to copy.

## Q: When / how should the bot talk?

- **Cicero** `sleep_classifier.md` + `parlai_message_handler.py` — first-class "stay
  silent" action, per-recipient gate, separate initiate-vs-reply thresholds.
- **Cicero** `message_editing.py` (`MessageFiltering`) — draft → check → send/resample.
- **ReCon — "Avalon's Game of Thoughts"** — ACL Findings 2024, arXiv 2310.01320, code
  `github.com/Shenzhi-Wang/recon`. Draft→self-critique loop with explicit 1st/2nd-order
  theory-of-mind (what does X believe about the board / about me?).
- Per-recipient intents = the deception/persuasion lever (Cicero conditions prose on a
  per-pair intent; the gap between *claimed* and *actual* intent is the deception dial).

## Q: How does the bot remember betrayal? (memory / journal)

- **Every's diary + trust scale** (above) — the working reference: per-player trust
  level + promise-vs-action checks + yearly summarization.
- **"Trust, Lies, and Long Memories"** (Multi-Round Avalon) — arXiv 2604.20582.
  Reputation emerges from cross-game memory; strong agents build trust early to spend it
  on a late betrayal ("trust as a resource").
- **WOLF** — arXiv 2512.09187. LLMs deceive well but **detect deception poorly** → the
  bot needs explicit help noticing it's being lied to.
- Honesty/broken-commitment definition: compare communicated intent to final action
  (Cicero `lie_detection.py`; the ACL follow-up below formalises it).

## Q: Baseline opponents (eval floor/ceiling + fallback)

- **DumbBot** — source + exact tuning constants in `github.com/diplomacy/daide-client`.
  Two-stage: value every province (supply-centre worth + proximity diffusion over the
  adjacency graph), then greedily assign each unit to its best reachable destination.
  Adjacency-driven, so it ports to variants. Reimplementable in ~1–3 days; serves as
  **both** the deterministic fallback and the frozen eval floor.
- **Albert** (van Hal) — strongest classic bot; **closed-source Windows binary**;
  best-reply search + opponent modelling. Eval *ceiling* only; wire in later via the
  `diplomacy` Python package's **DAIDE adapter** (which runs Albert/DumbBot).

## Other LLM-Diplomacy agents & negotiation research

- **Richelieu** (NeurIPS 2024) — LLM agent with planning + social reasoning + self-play;
  reportedly matches Cicero without human data (figure snippet-sourced).
- **Welfare Diplomacy** — variant + finding: honest/cooperative bots are exploitable
  (relevant to the fun objective — exploitable-but-characterful may be a feature).
- **"More Victories, Less Cooperation: Assessing Cicero's Diplomacy Play"** — ACL 2024,
  arXiv 2406.04643. Defines reusable, human-rater-free metrics computable from logs:
  **broken-commitment rate** and **persuasion success**.
- Negotiation/deception/ToM: "Werewolf agent that does not truly trust LLMs"
  (arXiv 2409.01575); MultiMind (arXiv 2504.18039); "Cheap Talk, Empty Promise"
  (arXiv 2604.04782); NegotiationToM (arXiv 2404.13627); TERMS-BENCH (arXiv 2605.13909).
- Survey index: `github.com/git-disl/awesome-LLM-game-agent-papers`.
