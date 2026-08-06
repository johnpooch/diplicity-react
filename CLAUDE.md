# CLAUDE.md

Guidance for Claude Code when working in this repository.

---

## !!! READ THIS FIRST — Evidence-Based Reasoning !!!

**Never agree with any assertion or claim without concrete, evidence-based reasoning.**

- Provide supporting evidence from context for every claim, deduction, or inference.
- Corroborate findings before acting: `Based on what I found <here>, <yes/no> because <why>`.
- Never assume or guess. If information is unavailable, say so.

---

## !!! External Service UIs Change !!!

Google Play Console, Google Cloud Console, Firebase Console, and similar services update their UIs frequently. **Never give step-by-step navigation instructions from memory.** Instead: describe what the user is trying to accomplish, give the direct URL if known, and ask for a screenshot if they can't find something.

---

## Project Overview

Diplicity React is a full-stack web app for the Diplomacy board game:
- **Frontend**: React + TypeScript (`/packages/web/`)
- **Backend**: Django REST API + PostgreSQL (`/service/`)
- **Architecture**: Microservices with Docker containers

## AI player architecture

The AI player system is four apps with a strict one-way dependency graph:

    agent → harness → (nothing in prod)
    agent → inference
    agent → bot_profile
    harness → inference   (eval/test code only)

Governing rule: **harness is pure; agent is where the world touches it.**

- inference — the Inference model, the client over the LLM provider, and
  Inference.objects.run(...). Records every model call. No HTTP API; browse
  calls in Django admin. Must not import from harness or agent.
- harness — pure prompt engineering: Block classes (shared prompt assembly),
  build_prompt(), TaskDefinitions (select_orders, reply), prompt text, parsers,
  and evals. No Django models, game API, queues, or telemetry in production
  code. A TaskDefinition is declarative; build_prompt is shared; parse() is
  per-task and raises ParseError on unusable output.
- agent — orchestration: emit consumer specs (agent/registry.py), Procrastinate
  tasks, the game API client (read + write), context assembly, telemetry,
  fallback policy, and the build → inference.run → parse → side-effect glue.
  Everything that touches Django, the game, or the queue lives here. The
  AgentTask model is the durable record of bot work to be done (kind =
  plan/finalize/reply): agent is a third emit consumer alongside notification
  and channel event, so an emit event (phase_started, phase_state_confirmed,
  channel_message) drives AgentTask.objects.create_from_event, which creates
  pending rows and defers agent.run — that loads the row, transitions its
  status, and dispatches to the executor. One AgentTask may span several
  Inference calls. A periodic agent.reconcile task re-drives rows whose job
  was lost or stalled (pending or stuck in running past a timeout), so a
  hand-inserted row runs on the next sweep. A bot plans when a phase starts
  and finalizes (submits *and* confirms) once no human is still pending, which
  both specs decide through the shared `Phase.has_unconfirmed_human` check: normally that
  lands on phase_state_confirmed, but a phase where no human has possible
  orders — a retreat only a bot must answer, an all-bot game — already
  satisfies it at phase_started, so PhaseStartedSpec queues finalize instead
  of plan for those seats rather than waiting for an event that never comes.
- bot_profile — BotProfile persona (disposition, voice), roster-management
  endpoints, get_bot_user, and the roster seed.

**Personas are currently switched off.** No prompt receives a `disposition` or a
`voice` block; production and the evals now run the same neutral system prompt,
which is the only prompt the `EVAL_RESULTS.md` baseline has ever measured. The
roster, its columns and its seed migrations are deliberately kept — the plan
([#1131](https://github.com/johnpooch/diplicity-react/issues/1131)) is to re-add
disposition first (into both `select_orders` and `reply`, gated on a larger
ranked fixture set) and voice second (into `reply` only, rewritten as
register-only), measuring each layer before the next. Do not re-inject either
half without that measurement.

Where does new code go? Deterministic + model-shaped → harness. Touches
Django/game/queue/side-effects → agent. Model-call mechanics/records →
inference. Persona/roster → bot_profile. If you want to eval something in
agent, a reasoning decision has leaked out of harness. If you want a plain
deterministic assertion in harness, that logic belongs in agent.

### Running the harness evals

The `select_orders` evals run against the real model via a management command
(`service/`):

```bash
python manage.py run_evals              # full dataset, model/key from settings
python manage.py run_evals --limit 1    # quick smoke run
python manage.py run_evals --model anthropic/claude-...   # override model
```

It needs `BOT_ANTHROPIC_API_KEY` set (model defaults to `BOT_LLM_MODEL`); it
prints a skip line and exits if the key is missing. Each eval hits the LLM
provider, so it costs real tokens.

**Permission policy:** running a single epoch (the default — one pass over the
dataset) is fine without asking. Do **not** run multiple epochs (each sample
repeated N times) unless the user explicitly asks — that multiplies model calls
and cost. When asked for multiple epochs, invoke `inspect_ai.eval(...)` with
`epochs=N` directly (the command exposes no `--epochs` flag).

The latest recorded baseline lives in
`service/harness/tasks/select_orders/EVAL_RESULTS.md` — update it when you take
a new baseline run.

The `quality_strong`/`quality_avoidance` scorers only aggregate over dataset
samples that declare `ranked_options` (a `good`/`neutral`/`bad` labelling of the
legal moves); every other sample is `Score.unscored()` (NaN) and excluded. Those
two scorers are the only ones that measure judgement rather than legality, so a
new eval only bites if it carries `ranked_options`.

### Harvesting eval candidates from real games

`dump_phase` (in `agent`) turns a live game phase into eval raw material:

```bash
python manage.py dump_phase --game <id> --out phase_dumps
cd packages/web
npx vite-node scripts/render-phase.mjs ../../service/phase_dumps/<prefix>_render.json /tmp/board.png
```

It writes a board `RenderState` JSON (render it to a PNG with `render-phase.mjs`
to eyeball what the bots did) plus one `select_orders` fixture stub per nation.
Turn a bad decision into an eval by adding a `ranked_options` block to a stub —
what the bot should have done under `good`, the mistake under `bad` — and
appending it to `dataset.json`. Order *options* only exist for a game's current
phase, so a resolved/historical phase (`--phase <id>`) is render-only. Output
lives in the gitignored `phase_dumps/`.

### Seating a bot in an abandoned seat

`replace_member_with_bot` (in `agent`) hands a nation over to a roster bot —
used when a player deletes their account or walks away mid-game:

```bash
python manage.py replace_member_with_bot --game <id> --nation Italy --bot dealmakerbot
```

It creates a *new* member for the bot in the same nation and marks the original
`kicked`, pointing `replaced_by` at the replacement — the original row is kept so
its phase states and messages remain attributable for statistics. The
replacement joins every channel the original was in (the original stays too, so
its past messages still render with the right sender). On the current phase it
takes over the phase state, and the original's pending orders are discarded so
adjudication does not receive two order sets for one nation. Finally it queues a
`plan` AgentTask so the bot acts in the phase already under way.

A kicked member's phase states are created with `has_possible_orders=False`, which
keeps a replaced seat out of the "is everyone done?" checks — early resolution
(`filter_due_phases`), the bot finalize trigger (`Phase.has_unconfirmed_human`), NMR
extensions and deadline warnings all key off that flag.

A replaced player keeps their account, so every write path has to lock them out.
Orders, order confirmation and draw proposals were already gated on
`IsActiveGameMember`, which rejects kicked members; chat and civil-disorder
recovery only checked `IsGameMember` and now use `IsNotKickedGameMember`. Read
access is deliberately left open — a replaced player can still view the game and
the channels they were in.

`--nation` resolves to the seat's *current* holder — the member with no
`replaced_by` — so a seat already handed over once resolves to the bot rather
than the member it replaced. Note that `kicked` does not mean "replaced": account
deletion kicks a member without ever setting `replaced_by`, and that is precisely
the seat the command exists to fill.

An unrecognised `--bot` errors with the list of bots still available for that
game. A production run needs a shell on the deployed service (`railway ssh`),
because `railway run` executes locally and cannot resolve Railway's internal
database host.

### Re-planning a bot's orders

`replan_member` (in `agent`) makes a bot think again about the phase already
under way — used after a harness change, when existing games should re-plan
against the new prompts:

```bash
python manage.py replan_member --game <id> --nation Italy
```

It discards the bot's orders for the current phase, then re-opens the seat's
`plan` AgentTask and defers the job. A seat that already planned has a
`succeeded` row which `enqueue` would return untouched (and
`unique_phase_agent_task` forbids a second one), so the shared `agent.replan`
helper goes through `AgentTask.objects.requeue`, which resets the existing row
to `pending` instead. `--nation` resolves to the seat's *current* holder, as in
`replace_member_with_bot`. The command errors if the seat is not played by a
bot, if that member has been kicked, or if the game has no active phase.

The same operation is a **Re-plan orders (bot members only)** action on the
Members changelist in Django admin, which takes a multi-select — that is the
route for re-planning several seats at once.

---

## Development Setup

### Docker (standard)
```bash
docker compose up   # frontend at :5173, API at :8000, DB at :5432
```

### Cloud / native (non-Docker)

The `.claude/hooks/session-start.sh` hook provisions everything automatically (Python venv, PostgreSQL, npm install, Railway CLI). It is idempotent.

Key facts:
- Always use `service/.venv/bin/python` — system `python3` is 3.11, Django 6 requires 3.12+. The hook prepends the venv to `PATH`.
- **SQLite is not viable** — some migrations use Postgres-only SQL. Use the native cluster.
- `DJANGO_DEBUG=True` alone is sufficient to start the service against the local DB.
- Features disabled without credentials: Firebase push notifications (`FIREBASE_PROJECT_ID`) and Google OAuth (`GOOGLE_CLIENT_ID`).

### Railway network access (cloud sessions)

`railway` commands and `/prod-query` require Railway hosts to be allowlisted. In the Claude Code on the web environment: set **Network access** to **Custom**, add `*.railway.com` and `*.railway.app`, and tick "Also include default list of common package managers".

### Codegen

```bash
docker compose up codegen   # regenerates all four generated artefacts
```

Codegen produces two OpenAPI schemas from the same serializers, because the API has two
wire representations:

| Artefact | Casing | Consumer |
|---|---|---|
| `service/openapi-schema.yaml` | camelCase | HTTP clients — drives `src/api/generated/` via orval |
| `service/openapi-schema.internal.yaml` | snake_case | in-process clients — drives `service/harness/generated/api.py` |

The camelCase form is produced by `CamelCaseJSONRenderer` at *render* time, so `response.data`
(what `agent/api_client.py` reads via DRF's `APIClient`) is snake_case. The internal schema is
generated by passing `--custom-settings project.openapi.INTERNAL_SCHEMA_SETTINGS`, which drops
the camelize postprocessing hook for that invocation only.

Never hand-edit `service/harness/generated/api.py` — it is regenerated by `datamodel-codegen`.

After codegen, run `npx tsc -b --noEmit` in `packages/web` to catch downstream type errors. See the `backend` skill for environment requirements to match committed output.

---

## Key Commands

### Frontend (`/packages/web/`)
```bash
npm run dev           # dev server
npm run dev:mocks     # dev server with all API calls mocked (no backend needed)
npm run build         # production build
npm run lint          # ESLint
npm run test          # Vitest
npm run storybook     # Storybook at :6006
npm run screenshot    # Playwright screenshot (see frontend skill)
```

### Backend (`/service/`)
```bash
python manage.py migrate
python manage.py runserver
python -m pytest <file> -v          # single file (preferred)
python -m pytest -n auto --reuse-db # full suite
```

---

## Development Guidelines

1. **Follow existing patterns** — new code should be indistinguishable from existing code in style and structure. Raise deviations as a discussion, don't silently deviate.
2. **TypeScript strict mode** — never use `any`. The one existing `any` in `CreateGame.tsx` is a known compromise — do not add more.
3. **Lint and type-check before submitting**:
   - `npm run lint` in `packages/web` (changed files only when possible)
   - `npx tsc -b --noEmit` in `packages/web` (required after codegen or type changes)
4. **Run tests to validate changes** — single file at a time for faster feedback.
5. **Never suppress lint/type violations** — no `eslint-disable`, `@ts-ignore`, `# noqa`, `pytest.mark.skip`. The only exception is the documented mutation-in-`useEffect` pattern (see the `frontend` skill).
6. **No comments or docstrings** — do not add code comments or docstrings, including in tests; do not annotate assertions to explain their values. The only exceptions are DRF view docstrings (extracted for OpenAPI) and the `eslint-disable` comment on the documented mutation-in-`useEffect` pattern.
7. **Prefer derived state over effects** — minimise `useEffect` usage in React.
8. **Write tests alongside features** — not as an afterthought. All tests for a single app live in that app's `tests.py`; do not split them across multiple test modules (e.g. `tests_emit.py`).
9. **Self-review non-trivial PRs with `/review-pr`** before requesting human review. Address or explicitly respond to all findings. Trivial PRs (typo fixes, dep bumps, doc-only) are exempt.
10. **PR description must match the diff** — run `git diff main` and confirm every described change is visible. Do not describe work from a prior PR or session.
11. **Python imports go at module top-level** — do not add an inline `import` inside a function/method body, even if you find an existing one nearby to copy. The only exception is breaking a genuine circular import, and that exception should be rare enough to call out in a PR description when used.

---

## GitHub Workflow

See `CONTRIBUTING.md` for full contributor guidelines.

### WIP limits
Soft limits: **5 open PRs**, **10 open issues**. A bot warns when exceeded. Before opening a new PR, check the current count.

### GitHub Discussions for ambiguous work
Before creating an issue where the right approach is unclear, open a [GitHub Discussion](https://github.com/johnpooch/diplicity-react/discussions). Once agreed, create a focused issue with an `## Approach` section.

### Issue format
Three sections (enforced by the `create-issue` skill): **Goal** (always), **Context** (when useful), **Approach** (when discussed). No acceptance criteria, implementation checklists, or sub-issues. If work is too large for one PR, split into two issues.

### PR screenshots
If a PR changes anything visible in the web app — new screens, layout, styling, copy, empty/error states — you MUST take screenshots of the changed component and embed them in the PR description. This is a completion criterion, not optional polish; the reviewer should see what changed without pulling the branch. See the `frontend` skill for the screenshot and attachment workflow.

**Never commit screenshots to the repository.** Write them to a temporary location outside the working tree (e.g. `/tmp/shots/`) and embed them in the PR description by uploading them as GitHub attachments — do not add image files to the repo or reference them via `raw.githubusercontent.com`. `screenshots/` and `shots/` are gitignored to guard against accidental commits; if you find committed screenshots, remove them.

---

## Code Philosophy

Five tenets that govern all code decisions. Apply them when implementing and when running `/review-pr`.

1. **Match existing patterns** — could a reviewer tell which code is new by style alone? If yes, it doesn't match.
2. **Simplicity is correctness** — minimum code for the current requirement. Can any line/function/file be removed without breaking an acceptance criterion? If yes, remove it.
3. **Observable over internal** — quality is judged by what the code produces (API responses, rendered UI, test assertions), not internal cleverness.
4. **Evidence over assertion** — every change justified by evidence: failing test that now passes, user flow that now works, linked issue.
5. **Fix, don't suppress** — when the linter, type checker, or test framework flags something, fix the root cause.

---

## Declarative class-based subsystems

For a subsystem with a reasonable amount of complexity — a family of cases that share one lifecycle but differ per case — model it as a base class plus a registry, in the style of Django's class-based views. Do not reach for this when the cases are few and uniform; a handful of functions is simpler and correct there. Use it once a module is accumulating parallel per-case functions that a central table stitches back together.

The unit of cohesion is the case, not the step: everything about one case lives in one class. A registry references each class by name (via a decorator) and never re-assembles behaviour from scattered parts.

Pick the mechanism by how the behaviour varies:

- Fixed configuration → declarative class attribute (`transports = [Push, Timeline]`).
- One of a small, closed set of interchangeable behaviours reused across cases → composition: assign a strategy _class_ to an attribute, following Django's `permission_classes = [AllowAny]` (the base instantiates it).
- A dominant default with per-case exceptions → template method: the base supplies the default, a case overrides only what differs (`get_body`).
- A bespoke behaviour used by a single case → override the method directly (`get_recipients`) rather than invent a single-use strategy class. A case supplies _either_ a strategy attribute _or_ a method override, mirroring Django's `queryset =` vs `get_queryset()`.

```python
@register("some_case")
class SomeCase(BaseSpec):
    transports = [Push, Timeline]        # declarative config
    recipient_provider = AllPlayers      # composed strategy (a class)

    def get_body(self, event):           # template-method override
        return f"..."
```

Diagnostic: if you override a method only to return a value from a small fixed menu, it should have been a composed attribute; if you assign a strategy used exactly once that holds real logic, it should have been a method override.

### Naming

**Files (Python).** In a Django app, a module that houses one class hierarchy is named after its base class, singular — `audience.py` holds `Audience` and its subclasses, `transport.py` holds `Transport`. A module that is a flat collection of many concrete registered cases is plural — `specs.py`. If you can name a file after a single base class, do; reserve the plural for genuine collections. (Frontend file naming follows React conventions instead — PascalCase components, `useX.ts` hooks.)

**Classes and attributes.** Name a class for the abstraction it represents, never the caller that consumes it (`ActiveExceptActor`, not `DrawProposal`). When a subclass narrows its parent, name it parent-plus-exception (`AllPlayersExceptActor`). Don't overload a term the domain already uses — we chose `transport` over `channel` because a channel is a chat construct. Prefer a plain descriptive word over jargon (`Active`, not `Canonical`). Never give an attribute a name that repeats its owner (`context.payload`, not `context.context`). A declarative attribute is singular or plural by its cardinality: `audience = Active` (one strategy), `transports = [Push, Timeline]` (a list).

---

## Maintaining This Document

If you discover patterns, make architectural decisions, or establish conventions during development, propose updates to this file (or the relevant domain doc). These documents should evolve with the codebase.
