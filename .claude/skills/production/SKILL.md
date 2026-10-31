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

`railway run` injects production env vars and runs locally against the **live production database**. Do not write to production unless the user asks you to.

## Admin superuser

`service/entrypoint.sh` creates the `superuser` account from `DJANGO_SUPERUSER_PASSWORD` only when it does not exist, and never rewrites it. Changing the variable does not change the password: the user rotates it in the Django admin or with `manage.py changepassword superuser`.

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

pgweb is read-only by configuration.

Check https://status.railway.com for platform-wide incidents.

---

# PR Staging Environments

Staging is one persistent Railway environment at https://diplicity-react-staging.up.railway.app. It has its own Postgres and allowlisted variables, with no production data or secrets. Never fork production or restore its database into staging.

## Deploy

Add the `deploy-to-staging` label to a same-repository PR. `.github/workflows/pr-staging.yml` resolves the target from current labels after acquiring the shared `staging` concurrency group, with cancellation disabled. The latest request wins, including requests whose queued runs were replaced.

1. Build `service/Dockerfile`'s production target with the commit's `GIT_SHA`, using the GitHub Actions layer cache, and push `ghcr.io/johnpooch/diplicity-service:<full sha>`.
2. Point the staging Django instance at the image and deploy it. Its existing pre-deploy command resets the schema; startup migrates and runs `seed_staging --skip-if-seeded`.
3. Wait for that exact deployment to succeed, then deploy and wait for the worker at the same image tag.
4. Smoke-test email login and the test account's paginated games list.
5. Comment on the target PR with its branch and SHA, backend, Netlify preview and run links, plus the test login.

The backend is shared by every Netlify preview (`https://deploy-preview-<number>--diplicity-react.netlify.app`). Previews pre-fill `test-user@example.com` / `password`. Email/password login is available; Google OAuth is not configured.

## Redeploy

The label stays on the holder. Pushing to it redeploys its current head; pushing to another PR skips deployment. Deploying a different PR removes the label from every other open PR and comments on each displaced PR. Fork PRs are skipped without credentials.

Every deployment resets the schema before migrations and seeds fresh data. Restarts do not reset it. Failed pre-deploy, migrations or seeding fail the deployment; staging may be broken until the next successful deploy. A failed image build never changes Railway.

## Return to main

A push to `main` or a manual **PR Staging Environment** workflow run deploys `main` and removes the label from open PRs, with a moved comment. Closing or merging the holder deploys another labelled open PR if one exists, otherwise `main`. Closing a non-holder does nothing. The environment is never torn down.

## Safety

- Railway project: `39039c2c-4f5d-4a37-8c0d-f8e4279fce61`; staging environment: `3082daa9-9287-4eef-9439-162ab737beb8`.
- Production environment `0372f6a0-88ab-4a58-b472-16789135ad71` is guarded against all mutations. Never delete a production repo trigger when switching staging to images.
- The workflow uses `RAILWAY_ACCOUNT_TOKEN` for GraphQL. Do not add staging variables or change the pre-deploy command.
- Images must be publicly pullable. If GHCR creates a private package, ask John to make it public; do not add registry credentials.
- Do not remove `DATABASE_PUBLIC_URL` or `RAILWAY_TOKEN`; bundle releases still use them.
