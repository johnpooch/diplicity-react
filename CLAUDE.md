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
- agent — orchestration: signals, Procrastinate tasks, the game API client
  (read + write), context assembly, telemetry, fallback policy, and the
  build → inference.run → parse → side-effect glue. Everything that touches
  Django, the game, or the queue lives here.
- bot_profile — BotProfile persona (disposition, voice), roster-management
  endpoints, get_bot_user, and the roster seed.

Where does new code go? Deterministic + model-shaped → harness. Touches
Django/game/queue/side-effects → agent. Model-call mechanics/records →
inference. Persona/roster → bot_profile. If you want to eval something in
agent, a reasoning decision has leaked out of harness. If you want a plain
deterministic assertion in harness, that logic belongs in agent.

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
docker compose up codegen   # regenerates service/openapi-schema.yaml and src/api/generated/
```

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
8. **Write tests alongside features** — not as an afterthought.
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

## Maintaining This Document

If you discover patterns, make architectural decisions, or establish conventions during development, propose updates to this file (or the relevant domain doc). These documents should evolve with the codebase.
