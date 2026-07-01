---
name: production
description: Production debugging guidance for diplicity-react — Railway CLI token conflict pattern, pgweb queries, write safety rules, and staging environments. Use when debugging production issues, querying the production database, or deploying PR staging environments.
allowed-tools: Bash, Read, Glob, Grep
---

# Production Debugging

App deployed on **Railway** (project: `devoted-rejoicing`, service: `diplicity-react`).

## Railway CLI — Token Conflict

Two tokens, different scopes:

| Variable | Scope | Used for |
|---|---|---|
| `RAILWAY_API_TOKEN` | Account | `whoami`, `status`, `logs` |
| `RAILWAY_TOKEN` | Project | `railway run` (inject prod env vars) |

When both are set, Railway CLI v5 gives `RAILWAY_TOKEN` priority for all commands, breaking account-scoped ones with "Unauthorized". Always unset the irrelevant token:

```bash
# Account-scoped
env -u RAILWAY_TOKEN railway whoami
env -u RAILWAY_TOKEN railway status
env -u RAILWAY_TOKEN railway logs --lines 50

# Project-scoped
env -u RAILWAY_API_TOKEN railway run --service diplicity-react python manage.py shell
```

## Access Tiers

- **Owner / trusted contributor**: both tokens configured — all commands available
- **Casual contributor**: no tokens — Railway commands unavailable

If any `railway` command fails with an auth or "not logged in" error, **stop immediately**. Tell the user:
> "Railway is not configured in this session. Set `RAILWAY_API_TOKEN` in the Claude Code on the web environment, and allowlist `*.railway.com` and `*.railway.app` under Custom network access."

## Write Safety

`railway run` injects production env vars and runs locally against the **live production database**. Never execute write operations:
- No `.create()`, `.update()`, `.delete()`, `.save()` in Django ORM
- No `INSERT`, `UPDATE`, `DELETE` in raw SQL
- No state-modifying management commands (`migrate`, `flush`, `loaddata`)

If the user asks to modify production data, refuse — production changes must go through a migration or controlled admin process.

## Common Commands

```bash
env -u RAILWAY_TOKEN railway status                            # deployment health
env -u RAILWAY_TOKEN railway logs --lines 50                   # recent logs
env -u RAILWAY_TOKEN railway logs --lines 200 | grep ERROR     # filter errors
env -u RAILWAY_TOKEN railway logs --lines 200 | grep "GET /api" # filter by endpoint
```

## Production Database Queries (pgweb)

Cloud sessions can't reach the production DB via `railway run` (Railway's internal hostname is not externally resolvable). Use **pgweb** instead — a web-based PostgreSQL client deployed as a Railway service over HTTPS.

Required env vars (set in cloud environment config; session-start hook exports them):
- `PGWEB_URL` — e.g. `https://pgweb-production-124e.up.railway.app`
- `PGWEB_USER` / `PGWEB_PASSWORD` — basic-auth credentials

```bash
# Write SQL to a file first (avoids shell escaping issues)
cat > /tmp/query.sql << 'EOF'
SELECT status, COUNT(*) FROM game_game GROUP BY status ORDER BY count DESC
EOF

curl -s -u "$PGWEB_USER:$PGWEB_PASSWORD" \
  -X POST "$PGWEB_URL/api/query" \
  --data-urlencode "query@/tmp/query.sql" \
  | python3 -c "
import json, sys
d = json.load(sys.stdin)
print('\t'.join(d['columns']))
for row in d['rows']:
    print('\t'.join(str(c) for c in row))
"
```

Use the `/prod-query` skill for guided read-only queries.

pgweb is read-only by configuration. Never issue `INSERT`, `UPDATE`, `DELETE`, or DDL.

Check https://status.railway.com for platform-wide incidents.

---

# PR Staging Environments

PRs can be deployed to an isolated staging environment with a copy of the production database — useful for testing migrations against real data or validating end-to-end behavior.

## Deploy

Add the `deploy-to-staging` label to a PR. `.github/workflows/pr-staging.yml` will:
1. Find or create a Railway environment (`staging-pr-<number>`)
2. Clone the production database via `pg_dump`/`pg_restore`
3. Configure CORS/ALLOWED_HOSTS for the staging domain
4. Deploy the PR branch
5. Comment on the PR with the frontend preview and staging backend URLs

The Netlify deploy preview automatically derives the staging backend URL from the PR number (`packages/web/netlify.toml` uses `REVIEW_ID`).

## Redeploy

Add the `deploy-to-staging` label again — the workflow reuses the existing environment and re-clones the database.

## Teardown

Staging environments are automatically deleted when the PR is closed or merged.

## Details

- Email/password login only — Google OAuth is not configured for staging
- One staging environment per PR (no shared pool)
- Railway GraphQL API manages environments (not the CLI)
- Railway project ID: `39039c2c-4f5d-4a37-8c0d-f8e4279fce61`
