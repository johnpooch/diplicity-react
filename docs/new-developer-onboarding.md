# New Developer Onboarding

Welcome aboard. This guide orients a new contributor around the Diplicity React project. It's a companion to the two existing setup docs — read those first for the mechanics, then come back here for the map:

- **[DEVELOPER.md](../DEVELOPER.md)** — the canonical setup steps (Docker, `.env`, Discord).
- **[README.md](../README.md)** — project summary and how to run it.
- **[CLAUDE.md](../CLAUDE.md)** — the deep reference (architecture, conventions, testing, debugging). It's written for an AI agent but it's also the single best human reference in the repo.

This doc adds three things those don't: a **single access/credentials checklist**, and pointers tailored to the two areas you're most likely to gravitate toward — the **data / Metabase work** and the **agentic coding harness**.

---

## 1. What the project is

Diplicity React is a full-stack web app for the board game Diplomacy, maintained by volunteers from the Diplomacy community.

- **Frontend** — React + TypeScript + Vite, TanStack Query for server state, shadcn/ui + Tailwind. Lives in `packages/web/`.
- **Backend** — Django REST Framework + PostgreSQL. Lives in `service/`, split into apps by domain concept (`game`, `order`, `phase`, `user_profile`, …).
- **Deployment** — Railway (production), Netlify (frontend previews). Live at https://diplicity.com.
- **Native** — Capacitor wrappers for iOS and Android also live under `packages/web/`.

The API contract is generated: backend serializers → OpenAPI schema (DRF Spectacular) → TypeScript client (orval) in `packages/web/src/api/generated/`. Never hand-edit the generated files.

---

## 2. Access & credentials checklist

Work top-to-bottom. The first three get you developing; the rest unlock specific areas. Items marked **(John provisions)** can only be granted by the maintainer — they involve creating accounts or production state, so don't expect to self-serve them.

| # | Access | How you get it | Needed for |
|---|--------|----------------|------------|
| 1 | **Discord** — Diplicity Hub server | Invite link, then say hi | Everything; this is where decisions happen |
| 2 | **GitHub** — contributor on `johnpooch/diplicity-react` | **(John provisions)** repo invite | PRs, issues, discussions |
| 3 | **Dev `.env` file** | **(John provisions)** — DM Johnpooch on Discord; drop it in the repo root | Google login + the basics, locally |
| 4 | **Metabase** account | **(John provisions)** — a user invite to the Metabase instance | Analytics / the data work |
| 5 | **Django admin** login | **(John provisions)** — a staff/superuser account on production (and/or a local superuser you create yourself, see below) | Inspecting and managing game/user data |
| 6 | **Honeycomb + Sentry** (optional) | **(John provisions)** — invites | Telemetry and error tracking |
| 7 | **Railway** (optional, advanced) | **(John provisions)** — project access / tokens | Production logs and debugging |

A few notes worth being explicit about:

- **Keys are shared on trust.** The `.env` holds real third-party credentials. Keep it to yourself, never commit it (it's gitignored), never paste it anywhere.
- **You can make your own *local* Django superuser** without anyone's help — it only touches your local database:
  ```bash
  docker compose run --rm service python3 manage.py createsuperuser
  ```
  Then visit http://localhost:8000/admin. Access to the *production* admin is separate and only John can grant it.
- **Metabase and production Django admin are read/observe surfaces for you to start.** Don't expect production write access early; the project deliberately routes data changes through migrations and controlled processes rather than ad-hoc admin edits.

---

## 3. Getting the app running locally

The short version (full detail in [DEVELOPER.md](../DEVELOPER.md)):

```bash
docker compose up service web db phase-resolver
# web:    http://localhost:5173
# api:    http://localhost:8000
# admin:  http://localhost:8000/admin
```

Run the backend tests to confirm the environment is healthy:

```bash
docker compose run --rm service python3 -m pytest game/tests/test_game_create.py -v
```

Frontend checks live in `packages/web/`:

```bash
npm run dev        # dev server
npm run test       # Vitest
npm run lint       # ESLint
npm run dev:mocks  # run the whole app with mocked API data, no backend needed
```

That last one — **mock mode** — is genuinely useful: the frontend ships an MSW layer that serves canonical fixtures for every endpoint, so you can poke around the full UI (logged in as "Mock Player") with no backend at all. See the fixture registry in `packages/web/src/mocks/fixtures/index.ts`.

---

## 4. The data / Metabase work (your wheelhouse)

This is where a data-engineering background pays off immediately. Everything below is documented in more depth in the **"Metabase Analytics"** and **"Production Debugging"** sections of `CLAUDE.md` — read those, they encode hard-won lessons.

**Where the data lives.** Production is a single PostgreSQL database on Railway. The core tables are `game_game`, `phase_phase`, `phase_phasestate`, plus the per-domain tables (`order_*`, `channel_*`, `nation_*`). The Django app structure under `service/` mirrors the schema one-app-per-concept, so the models are the most readable schema documentation you'll find.

**Two ways to query production, both read-only:**

1. **Metabase** — for dashboards and saved questions. Note the big gotcha: the Metabase MCP tooling only supports single-hop implicit FK joins, so anything multi-hop (e.g. `phase_phasestate → phase_phase → game_game`) must be a **native SQL** question. CLAUDE.md documents the exact base64-encoding workflow for creating those reliably.
2. **pgweb** — a web SQL client for one-off read-only queries, wired up as the `/prod-query` workflow. Safer and faster than Metabase for exploration.

**Schema landmines you'll hit on day one** (all in CLAUDE.md, repeated here because they'll save you an afternoon):

- `phase_phase.completed_at`, `started_at` are **always NULL** — use `status = 'completed'` to find resolved phases.
- `phase_phase.updated_at` is **unreliable for time-bucketing** (batch ops reset it) — bucket on `scheduled_resolution` instead.
- ~21% of phases have `scheduled_resolution IS NULL` (manual-resolution games) — filter them out for deadline/NMR analysis.

**A good first data task** is usually a new Metabase question or dashboard answering a question the community actually asks (engagement, NMR rates, game completion funnels). Float the idea in Discord first.

---

## 5. The agentic coding harness (your other interest)

This repo is unusually invested in AI-assisted development — it's arguably a second product. The harness lives in `.claude/` and is worth studying as a system:

- **`CLAUDE.md`** (repo root) — the agent's primary brief. Conventions, philosophy, every gotcha. ~80KB and dense; skim the headings first.
- **`.claude/commands/`** — custom slash-commands: `/review-pr`, `/implement-issue`, `/prod-query`, `/debug-production`, `/study-backend-structure`, `/add-entry-to-changelog`.
- **`.claude/skills/`** — richer multi-file skills: `create-issue`, `create-discussion`, and a deep `react` skill (components, data-loading, forms, tests, zod, useEffect-minimization).
- **`.claude/agents/`** — specialized sub-agent definitions (`django-backend-developer`, `react-frontend-developer`, `technical-architect`, `lint-typecheck-resolver`).
- **`.claude/philosophy/issue-philosophy.md`** — the rubric an agent uses to scope and review *issues* (the code-philosophy counterpart is the "Code Philosophy" section of CLAUDE.md).

The design intent behind all this is captured in **`docs/high-level-overview.md`** and **`docs/workflow-setup.md`**: a GitHub-issue-driven state machine where agents scope issues, apply a staff-engineer review calibrated to the project's philosophy, implement in isolated worktrees, and pause for human review at every critical gate. If you want to understand *why* the harness is shaped the way it is, start there.

The project also supports **Claude Code on the web** — cloud sessions provisioned natively (no Docker) via the `.claude/hooks/session-start.sh` hook. That's a good area to contribute to if harness tooling is your interest.

---

## 6. Picking up your first bugs

The project runs a deliberately small backlog. Read **[CONTRIBUTING.md](../CONTRIBUTING.md)** — the norms matter here more than in most hobby projects:

- **WIP limits** — soft caps of **5 open PRs** and **10 open issues**. A bot warns when you exceed them. Check the count before opening new work.
- **One PR does one thing.** No drive-by fixes or opportunistic refactors bundled in.
- **Discuss first when the approach isn't obvious.** Open a [GitHub Discussion](https://github.com/johnpooch/diplicity-react/discussions) for anything where the right approach needs weighing; create a focused issue once it's settled. Skip the Discussion when goal *and* approach are already clear.
- **Issue format** is a tight three-section template (Goal / Context / Approach) — no acceptance-criteria checklists, no sub-issues. The `create-issue` skill enforces it.
- **Screenshots are mandatory** for any visible UI change in a PR — there's a Playwright + mock-data workflow for producing them (CLAUDE.md, "UI Verification & PR Screenshots").
- **Run `/review-pr`** on any non-trivial PR before requesting human review.

Good first targets: small frontend bugs (the mock-mode + fixture setup makes them fast to reproduce) or backend bugs with a clear failing test. Filter open issues for anything small and well-scoped, and ask in Discord which are genuinely up for grabs.

---

## 7. The five tenets (how code is judged here)

Every review leans on these (full detail in CLAUDE.md → "Code Philosophy"):

1. **Match existing patterns** — new code should be indistinguishable from existing code.
2. **Simplicity is correctness** — the minimum code for today's requirement; no speculative abstraction.
3. **Observable over internal** — judged by API responses / rendered UI / test assertions, not cleverness.
4. **Evidence over assertion** — every change justified by a failing test now passing, a flow now working, a linked issue.
5. **Fix, don't suppress** — never `eslint-disable` / `@ts-ignore` / `# noqa`; fix the root cause.

---

## Quick reference

| You want to… | Go to |
|--------------|-------|
| Set up locally | `DEVELOPER.md` |
| Understand a convention | `CLAUDE.md` (search the headings) |
| Query production data | `CLAUDE.md` → Metabase Analytics / Production Debugging; `/prod-query` |
| Understand the AI workflow | `docs/high-level-overview.md`, `docs/workflow-setup.md`, `.claude/` |
| Write an issue | `create-issue` skill, `.claude/philosophy/issue-philosophy.md` |
| Write React | `.claude/skills/react/` |
| Ask a human | Diplicity Hub Discord |
