# Developer Guide

This is a hobby project maintained by volunteers from the Diplomacy community. New contributors are welcome.

The repo is built to be developed with an AI coding agent. A detailed [`CLAUDE.md`](CLAUDE.md) documents the architecture, conventions, and testing patterns, so a freshly-installed agent already knows how the codebase is organized. You'll move faster using one — strongly recommended.

## Setup

1. Install [Docker Desktop](https://www.docker.com/products/docker-desktop/).
2. Install [Claude Code](https://docs.anthropic.com/en/docs/claude-code/getting-started) (or another AI agent — point it at `CLAUDE.md`).
3. Clone the repo.
4. DM **Johnpooch** on the [Diplicity Hub Discord](https://discord.gg/QETtwGR) for the dev `.env` file. Drop it in the repo root. Keep the keys to yourself — they're shared on trust.
5. Start the app:
   ```bash
   docker compose up service web db phase-resolver
   ```
   Then open http://localhost:5173.

If you're using Claude Code, you can also just point it at this guide and ask it to set up the dev environment for you.

## When you need more keys

The default `.env` covers Google login and the basics. Other features need extra credentials:

- Push notifications — Firebase service account
- Telemetry and error tracking — Honeycomb and Sentry
- iOS native builds — Apple signing certs (more involved; talk to Johnpooch before starting work in this area)

DM Johnpooch if you're working on any of those.

## Deploying a PR to staging

Every PR can be deployed to an isolated environment with a copy of the production database:

1. Open the PR against `main`.
2. Add the `deploy-to-staging` label.
3. A GitHub Actions workflow comments on the PR with the frontend preview URL and the backend URL.

Google OAuth is not configured for staging — use email/password login. The environment is torn down automatically when the PR closes or merges.

## Contribution norms

- Keep changes small and focused — one PR per concern. Big sweeping changes are hard to review and slow to land.
- Discuss meaningful new features, refactors, or architectural changes in the Diplicity Hub Discord before starting work. It's much easier to course-correct early than to rework a finished PR.
- Update `RELEASE_NOTES.md` for user-visible changes. Internal refactors don't need a note.

---

Stuck or unsure how to approach a problem? Ask in the [Diplicity Hub Discord](https://discord.gg/QETtwGR). Don't wait until you're frustrated.
