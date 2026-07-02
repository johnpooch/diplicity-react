# Gap 08: Relationship and Goal Tracking

## Gap statement

Every AI_Diplomacy agent carries `goals: List[str]` and `relationships: Dict[power, label]`
on a five-point scale — `Enemy, Unfriendly, Neutral, Friendly, Ally` (`ALLOWED_RELATIONSHIPS`,
`ai_diplomacy/agent.py`). They are initialized by a dedicated LLM call at game start
(`initialize_agent_state_ext`, `ai_diplomacy/initialization.py`, `initial_state_prompt.txt`),
updated after each negotiation round's diary call (`generate_negotiation_diary_entry` parses
`updated_relationships` and `goals` and applies validated changes), and — in no-press games —
refreshed by a dedicated state-update call after each movement phase
(`analyze_phase_and_update_state`, `state_update_prompt.txt`, which forces goal regeneration
by passing empty goals). Updates are strictly validated: unknown powers and off-scale labels
are dropped with logging. Both structures are injected into every context via
`build_context_prompt` ("Current Goals: … Relationships: …", `context_prompt.txt`), so
negotiation, planning, and orders all condition on them.

We track neither. No model, no prompt section, no update path — grep of `service/bot/` finds
no goals or relationship concept anywhere. The TDD promises both in private context ("goals
and relationships with other players", **Context**, `TECHNICAL_DESIGN.md`) and as inspectable
rows (**Telemetry and observability**). A bot today decides each reply and each order set with
no notion of who its friends are, which is why (combined with Gap 05's attribution loss) its
diplomacy cannot be coherent across even two messages.

Status: **described in the TDD but not implemented**.

## Why it matters

Relationships are the cheapest strong conditioning signal for both play and presence: "France:
Ally, Russia: Enemy" steers a small model's support orders and chat tone more reliably than
paragraphs of transcript. Goals give continuity across phases beyond the diary's narrative.
Gap 09's negotiation loop needs relationship state to decide whom to message and how, and the
prompt-injection guardrail in the TDD (**Prompt injection**) leans on orders being driven by
persisted state rather than by whatever a player last said in chat.

Depends on Gap 06 (per-bot identity) and Gap 07 (this state is written by the same plan-call
JSON and rendered alongside the diary). Feeds Gap 09.

## Proposed approach

**Models.** In `service/bot/models.py`, structured rows (not JSON blobs) so Metabase can chart
relationship trajectories per the TDD's inspection goal:

```python
class RelationshipQuerySet(models.QuerySet):
    def for_member(self, member):
        return self.filter(member=member)


class Relationship(BaseModel):
    objects = RelationshipManager()
    member = models.ForeignKey("member.Member", on_delete=models.CASCADE, related_name="bot_relationships")
    other_member = models.ForeignKey("member.Member", on_delete=models.CASCADE, related_name="bot_relationships_about")
    level = models.CharField(max_length=20, choices=RelationshipLevel.LEVEL_CHOICES, default=RelationshipLevel.NEUTRAL)

    class Meta:
        unique_together = ["member", "other_member"]


class Goal(BaseModel):
    objects = GoalManager()
    member = models.ForeignKey("member.Member", on_delete=models.CASCADE, related_name="bot_goals")
    phase = models.ForeignKey("phase.Phase", on_delete=models.CASCADE, related_name="bot_goals")
    body = models.TextField()
    active = models.BooleanField(default=True)
```

`RelationshipLevel` in `service/bot/constants.py` copies AI_Diplomacy's proven five-point
scale (`ENEMY, UNFRIENDLY, NEUTRAL, FRIENDLY, ALLY` with `LEVEL_CHOICES`). Relationships are
current-state rows (mutated in place — history reconstructable from `updated_at` plus diary
retrospectives; a full history table is over-engineering at this stage). Goals are
phase-stamped rows; superseded goals flip `active=False` rather than being deleted, keeping
the inspection trail.

**No initialization call.** AI_Diplomacy spends one LLM call per agent at game start to set
opening goals/relationships. We initialize for free: all relationships default `NEUTRAL`
(created lazily on first plan), no goals. The first plan call sets both — see next point —
one phase later than AI_Diplomacy at zero cost.

**Updates ride the plan call.** Extending Gap 04/07's response schema, the plan JSON gains:

```json
{
  "reasoning": "...",
  "retrospective": "...",
  "diary": "...",
  "goals": ["Take Belgium by 1902", "Keep Russia neutral in the north"],
  "relationships": {"France": "Friendly", "Russia": "Unfriendly"},
  "choices": [...]
}
```

The task validates exactly as AI_Diplomacy does: nation names must match game members, labels
must be on-scale, everything else is dropped silently (`analyze_phase_and_update_state`'s
validation loop is the model to follow, minus its multi-key fallbacks — our schema is fixed).
`relationships` is a sparse diff (only changed pairs), applied over existing rows; `goals`
replaces the active set (previous rows flipped inactive). Nation→member resolution uses the
members list already in the fetched game payload. One prompt line each in
`select_orders_instruction.txt` describes the two fields and the allowed labels.

The commit call does **not** update state (keeps its output minimal and its purpose sharp —
final orders + short diary). Reply calls never update state: this preserves the TDD's
injection guardrail — a player's chat can *ask* for anything, but goals/relationships only
move through the plan call, whose primary inputs are board state and resolved orders.

**Feed it back.** `ContextBuilder.with_standing(relationships, goals)` renders a private
block, adjacent to the persona and diary:

```
Your goals:
  - Take Belgium by 1902
Your relationships:
  France: Friendly · Germany: Neutral · Russia: Unfriendly
```

Included in plan, commit, and reply prompts. ~80–150 tokens.

## Cost impact

Zero additional LLM calls — the delta is ~60–120 output tokens on the plan call (sparse
relationship diff + a few goals) and ~80–150 private input tokens on each call that renders
the block. Compare AI_Diplomacy: one initialization call plus one state-update call per agent
per movement phase; folding both into the existing plan call is the cost-bounded
approximation. Risk flagged: piling retrospective + diary + goals + relationships + orders
into one call asks a lot of a 24B model; if quality suffers, the fallback design is to split
plan into a "state" call and an "orders" call — doubling critical-path calls but staying
inside the protected plan/commit budget. Decide from transcripts, not up front.

## Scope boundaries

Out of scope here:

- Using relationships to *choose* negotiation targets — Gap 09.
- Diary rendering and persistence mechanics — Gap 07 (this doc adds sibling fields to the
  same JSON and sibling blocks to the same private context).
- Betrayal *detection* content — that lives in the retrospective text (Gap 07); relationships
  are the numeric residue.
- Relationship history tables or decay heuristics — not until inspection shows a need.
- Anything visible to players — this state is hidden; no API exposure.

## Testing notes

In `service/bot/tests.py`:

- Plan task with mocked LLM returning goals + relationships: assert `Relationship` rows
  updated only for named pairs (others untouched at `NEUTRAL`), old `Goal` rows flipped
  inactive, new ones created and phase-stamped.
- Validation: off-scale label (`"BFF"`), unknown nation (`"Atlantis"`), and self-reference are
  dropped; orders still submitted.
- Lazy initialization: first plan in a fresh game creates `NEUTRAL` rows for every other
  member exactly once (idempotent on retry — `get_or_create`).
- `TestContextBuilder`: `with_standing` renders both sections; empty goals renders the
  relationships line only.
- Prompt feedback: reply-task prompt (captured via patched `LLMClient`) contains the standing
  block, and a second-phase plan prompt reflects first-phase updates (two-phase integration
  pattern from `service/integration/test_bot.py`).

## Open questions

- Relationships toward **humans** update only at plan time (once per phase). Is that too slow
  when a human betrays mid-phase via chat? Allowing the reply call to *propose* relationship
  changes would react faster but weakens the injection guardrail; recommend keeping plan-only
  until playtesting says otherwise.
- Should goals cap at N (AI_Diplomacy's prompts imply 2–4)? A cap of 4 in the instruction
  line is cheap insurance against goal-list bloat; needs a quick decision at implementation.
- Track relationships toward eliminated/civil-disorder members or prune them? Pruning saves
  tokens; keeping them preserves grudge continuity if the player returns.
