# Gap 06: Bot Identity and Persona Model

## Gap statement

In AI_Diplomacy every power is a distinct agent with its own system prompt. `DiplomacyAgent`
loads `<power>_system_prompt.txt` and falls back to a generic `system_prompt.txt`
(`ai_diplomacy/agent.py`, constructor; e.g. `ai_diplomacy/prompts/france_system_prompt.txt`
gives France a named strategic doctrine), and an optional mode swaps in country-specific
instruction files per task (`config.COUNTRY_SPECIFIC_PROMPTS`,
`ai_diplomacy/prompt_constructor.py` and `build_conversation_prompt`,
`ai_diplomacy/clients.py`). Identity is per-power, injected at the system-prompt level, and
shapes both negotiation voice and order strategy.

We have exactly one bot. Migrations seed a single user (`bot@diplicity.com`,
`service/bot/migrations/0001_create_bot_user.py`) with a single `BotProfile` whose
`disposition` and `voice` fields hold one generic persona
(`service/bot/migrations/0002_create_bot_profile.py`). Contrary to an easy assumption, the
model layer is **not** empty — `BotProfile(user, disposition, voice)` exists with a proper
QuerySet/Manager (`service/bot/models.py`) and bot detection is already profile-based
(`user__bot_profile__isnull=False` throughout `service/bot/decorators.py`), not email-based.
But the persona fields are **dead data**: nothing outside the seeding migration reads
`disposition` or `voice` — not the prompts (`service/bot/prompts/*.txt` contain no persona
block), not the tasks, not the context builder. `get_bot_user()` does
`User.objects.get(bot_profile__isnull=False)` (`service/bot/utils.py`), which structurally
assumes exactly one bot user in the system and breaks (MultipleObjectsReturned) the moment a
second is seeded. Game creation adds that single bot via `include_bot_opponent`
(`service/game/serializers.py:454-470, 569-571`), so two bots in one game — or bots in two
concurrent games with distinct identities — are impossible. No API field marks a member as a
bot (`is_bot` appears nowhere; the TDD's "bot badge" has no backend support —
`service/member/serializers.py`).

Status: profile model and profile-based detection are **built and working**; multiple
identities, persona-in-prompt, and the bot badge are **described in the TDD but not
implemented**.

## Why it matters

Personas are the TDD's core "fun" mechanism (**Personas**, `TECHNICAL_DESIGN.md`): distinct
dispositions and voices are what make seven bots feel like seven players rather than one
process. Every downstream feature keys on per-bot identity — diaries (Gap 07), relationships
(Gap 08), and negotiation style (Gap 09) are meaningless if all bots share one user row. This
doc is therefore a hard prerequisite for Gaps 07–09.

## Why-it-matters dependency: this doc must land before Gaps 07, 08, 09.

## Proposed approach

**Seed a pool of bot users.** A data migration creates `BOT_POOL_SIZE` (seven — one per
classical nation, the natural upper bound per game) users, each with a `UserProfile` (name,
picture) and a `BotProfile` carrying a distinct handwritten persona. Personas live in the
migration as literals, in the two-field shape the model already defines, e.g.:

```python
BOT_PERSONAS = [
    {"username": "bot-margrave", "name": "The Margrave", "disposition": "Patient and defensive; keeps agreements until clearly betrayed.", "voice": "Formal, clipped, slightly archaic."},
    {"username": "bot-corsair", "name": "Corsair", "disposition": "Opportunistic; probes for weakness and switches sides readily.", "voice": "Breezy, teasing, short sentences."},
]
```

The existing `bot@diplicity.com` user stays as pool member zero (its profile text updated),
so no existing games break.

**Replace the singleton accessor.** `service/bot/utils.py`:

```python
def get_bot_users(game, count=1):
    return list(
        get_user_model().objects.filter(bot_profile__isnull=False)
        .exclude(members__game=game)
        .order_by("?")[:count]
    )
```

`get_bot_user()` is kept as `get_bot_users(game, 1)[0]`-style shim during the transition and
removed once call sites migrate: `service/game/serializers.py` (creation),
`service/bot/tests.py`, `service/integration/test_bot.py`,
`service/game/tests/test_bot_opponent.py`. Random ordering gives persona variety across games;
the exclude prevents the same identity appearing twice in one game.

**Persona enters the prompt.** The tasks resolve the acting member's `BotProfile` (the user id
is a task argument already; `BotProfile.objects.with_related_data().get(user_id=...)`).
`ContextBuilder` gains `with_persona(profile, nation_name)` producing a private-context block —
subsuming Gap 03's `with_identity`:

```
You are playing England as "The Margrave".
Disposition: Patient and defensive; keeps agreements until clearly betrayed.
Voice: Formal, clipped, slightly archaic. Write all chat messages in this voice.
```

It is prepended to the private sections for **all** stages (plan, commit, reply), so
disposition can influence order selection and voice governs chat, matching the TDD's split.
System prompts (`select_orders_system.txt`, `reply_system.txt`) stay persona-free and
identical across bots — deliberately unlike AI_Diplomacy's per-power system prompts — because
a shared system prompt is a cacheable prefix (Gap 10) while a per-bot one is not.

**Expose the badge.** Add to `BaseMemberSerializer` (`service/member/serializers.py`):

```python
is_bot = serializers.SerializerMethodField()

@extend_schema_field(serializers.BooleanField)
def get_is_bot(self, obj):
    return obj.user is not None and hasattr(obj.user, "bot_profile")
```

with `select_related`/`prefetch` of `user__bot_profile` added to the member-loading QuerySets
to avoid N+1 (verify with the repo's query-count tests). Codegen re-run required; the frontend
badge itself is a separate frontend PR.

**Multi-bot game filling stays out.** `include_bot_opponent` remains a single-bot boolean in
this doc; "fill remaining slots with bots" / add-bot-while-staging are product API changes to
the `game` app with their own permission questions, split into a future issue (kept out to
hold this at one PR).

## Cost impact

The persona block is ~60–100 tokens of **private** (uncacheable) context per call — at four to
six calls per bot-phase this is a few hundred input tokens per bot-phase, negligible against
the budget. Keeping personas out of the system prompt preserves the shared cacheable prefix,
which is the material cost decision in this doc. No new LLM calls; persona generation by LLM
is explicitly not proposed (handwritten personas are free and tunable).

## Scope boundaries

Out of scope here:

- Diary, goals, relationships — Gaps 07/08 (they key off the per-bot member this doc enables).
- Negotiation behaviour shaped by disposition — Gap 09 consumes the block, this doc defines it.
- Frontend badge rendering and any UI — backend field plus codegen only.
- Game-app API for adding N bots / auto-substitution on civil disorder (TDD **Product**
  features) — separate issue in the `game` app's territory.
- Realism-vs-caricature persona tuning — explicitly deferred by the TDD; the seeded texts are
  first drafts to playtest.

## Testing notes

- `service/bot/tests.py`: `get_bot_users` returns distinct users, never one already in the
  game (create a game containing bot #1, assert exclusion); `MultipleObjectsReturned` is gone
  with seven seeded profiles (the two tests in `TestBotIdentificationByProfile` update from
  `get_bot_user` to the new accessor).
- `TestContextBuilder`: `with_persona` renders nation, name, disposition, voice into
  `build_private`; plan-task test asserts (via patched `LLMClient`) the prompt contains the
  persona lines.
- `service/game/tests/test_bot_opponent.py`: creation with `include_bot_opponent=True` still
  yields exactly one bot member; two games created back-to-back may get different bot users
  (assert only membership validity, not which persona, to keep the test deterministic).
- Member serializer: response includes `is_bot=True` for the bot member and `False` for
  humans; query-count assertion unchanged after the prefetch.
- Migration reversibility: `RunPython` with a noop reverse, matching the existing bot
  migrations.

## Open questions

- Does the anonymous-game masking path (`_is_masked`, `service/member/serializers.py`) also
  hide `is_bot`? Arguments both ways: masking it preserves anonymity; showing it is honest
  about non-human opponents. Needs a product call.
- Random persona assignment vs. creator choice at game creation — the TDD's **Product**
  section implies admins add bots deliberately; picking a persona is a natural extension but
  expands the API surface. Deferred with the multi-bot API.
- Seven personas: enough variety for launch, or should the pool exceed max-bots-per-game so
  repeat opponents feel fresh?
