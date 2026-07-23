# Developer Guide

This is a hobby project maintained by volunteers from the Diplomacy community. New contributors are welcome.

The repo is built to be developed with an AI coding agent. A detailed [`CLAUDE.md`](CLAUDE.md) documents the architecture, conventions, and testing patterns, so a freshly-installed agent already knows how the codebase is organized. You'll move faster using one — strongly recommended.

## Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (this is how you run the whole app locally).
- [git](https://git-scm.com/), to clone the repo.
- Optionally, an AI coding agent such as [Claude Code](https://docs.anthropic.com/en/docs/claude-code/getting-started). Point it at `CLAUDE.md` and it will already understand the codebase.

You do **not** need any secrets, API keys, or a `.env` file to run the app locally. Everything needed for local development ships with sensible defaults. (Optional features like Google sign-in and push notifications need real credentials — see [When you need more keys](#when-you-need-more-keys) — but nothing in the core "run it and play a game" flow does.)

## Start the app

1. Clone the repo and `cd` into it.
2. Start every service:
   ```bash
   docker compose up service web db worker phase-resolver
   ```
   The first run builds the images and can take several minutes. Leave this terminal open — it streams logs from all the containers, which is useful for debugging.
3. Open http://localhost:5173 in your browser.

That's it. If you see the Diplicity home page, the stack is running.

### What each service does

The command above starts five containers, all on one Docker network:

| Service | What it is | Where |
| --- | --- | --- |
| `web` | React frontend (Vite dev server, hot reload) | http://localhost:5173 |
| `service` | Django REST API | http://localhost:8000 |
| `db` | PostgreSQL database | localhost:5432 |
| `worker` | Procrastinate background worker (notifications, bot moves, scheduled jobs) | — |
| `phase-resolver` | Polls the API every 10s to advance game phases whose deadline has passed | — |

Plain `docker compose up` (no service list) also works and additionally runs a one-off `codegen` container. That container regenerates the API types and then exits with code `0` — that exit is expected, not an error.

## Create a user

There is no seeded account, and a couple of things that work in production do **not** work on a local machine, so read this before trying to log in:

- **Your real diplicity.com account does not exist locally.** The local database is empty and separate from production.
- **Signing up through the web form does not complete locally.** Registration creates an inactive account and emails a verification link pointing at `diplicity.com`. Local dev has no email delivery, so the account never activates.

The reliable way to get a working local account is the `create_test_user` management command. With the stack running, open a second terminal and run:

```bash
docker compose exec service python manage.py create_test_user
```

This creates (or resets) an **active** account you can log in with immediately:

- **Email:** `test@example.com`
- **Password:** `password`

The command is idempotent — run it again any time to reset the account. You can also pass your own values:

```bash
docker compose exec service python manage.py create_test_user \
  --email you@example.com --name "Your Name" --password hunter2
```

### Create an admin (superuser)

To reach the Django admin panel you need a superuser. The easiest way is the same command with `--superuser`:

```bash
docker compose exec service python manage.py create_test_user --superuser
```

That gives `test@example.com` / `password` admin rights. (If you prefer the standard interactive Django flow instead, `docker compose exec service python manage.py createsuperuser` also works.)

## Log in and test manually

1. Go to http://localhost:5173.
2. Log in with **email** `test@example.com` and password `password`.
3. Create a game, join it, and submit orders to check the flow end to end. The `phase-resolver` service advances phases automatically once a deadline passes.

To exercise multiplayer flows (multiple players in one game), create extra users with different emails and log in as each in a separate browser or a private/incognito window:

```bash
docker compose exec service python manage.py create_test_user --email player2@example.com --name "Player Two"
```

## Access the admin panel locally

The Django admin is a web UI for inspecting and editing database records directly — handy for debugging game state.

1. Make sure you have a superuser (see [Create an admin](#create-an-admin-superuser)).
2. Open http://localhost:8000/admin.
3. Log in with the **username** (not the email) and password. For the default superuser the username is the part of the email before the `@`, so `test@example.com` logs in as username `test`, password `password`.

## Running tests

Backend (Django, pytest):

```bash
docker compose run --rm service python -m pytest -v                        # full suite
docker compose run --rm service python -m pytest game/tests/test_game_create.py -v   # one file
```

Frontend (from `packages/web`):

```bash
npm run test        # Vitest
npm run lint        # ESLint
```

## When you need more keys

The core local flow needs nothing extra. Some optional features do need real credentials, provided via a `.env` file in the repo root (copy [`.example.env`](.example.env) and fill in only what you need — leave the rest empty):

- Google / Apple sign-in — OAuth client IDs
- Push notifications — Firebase service account
- Telemetry and error tracking — Honeycomb and Sentry
- iOS native builds — Apple signing certs (more involved; talk to Johnpooch before starting work in this area)

DM **Johnpooch** on the [Diplicity Hub Discord](https://discord.gg/2TkZbBRPW) if you're working on any of those.

## Deploying a PR to staging

Every PR can be deployed to an isolated environment with a copy of the production database:

1. Open the PR against `main`.
2. Add the `deploy-to-staging` label.
3. A GitHub Actions workflow comments on the PR with the frontend preview URL and the backend URL.

Google OAuth is not configured for staging — use email/password login. The environment is torn down automatically when the PR closes or merges.

## Contribution norms

- Keep changes small and focused — one PR per concern. Big sweeping changes are hard to review and slow to land.
- Discuss meaningful new features, refactors, or architectural changes in the Diplicity Hub Discord before starting work. It's much easier to course-correct early than to rework a finished PR.

---

Stuck or unsure how to approach a problem? Ask in the [Diplicity Hub Discord](https://discord.gg/2TkZbBRPW). Don't wait until you're frustrated.
