#!/bin/bash
set -euo pipefail

# SessionStart hook for Claude Code on the web.
#
# Prepares the container so the full local (non-Docker) dev workflow is ready
# the moment a session starts:
#   - Python 3.12 virtualenv + backend dependencies (service/.venv)
#   - PostgreSQL 17 (installed from apt.postgresql.org) replacing the image's 16
#     cluster, started, with the `diplicity` database created
#     and migrated (SQLite is NOT viable — some migrations use Postgres-only
#     raw SQL such as `ALTER TABLE ... ADD COLUMN IF NOT EXISTS`)
#   - Frontend npm dependencies (packages/web)
#   - Railway CLI installed (production access additionally requires the Railway
#     API host to be in the network egress allowlist — see notes below)
#   - Session env vars (venv on PATH + local DB config) via $CLAUDE_ENV_FILE

# Only run in the remote (Claude Code on the web) environment.
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
VENV_DIR="$PROJECT_DIR/service/.venv"

log() { echo "[session-start] $*"; }

###############################################################################
# 1. Python backend: virtualenv (Python 3.12) + dependencies
#    Django 6 requires Python 3.12+, but the system default `python3` is 3.11.
###############################################################################
if ! command -v python3.12 >/dev/null 2>&1; then
  log "WARNING: python3.12 not found — backend cannot run (Django 6 needs 3.12+)."
else
  if [ ! -x "$VENV_DIR/bin/python" ]; then
    log "Creating Python 3.12 virtualenv at service/.venv"
    python3.12 -m venv "$VENV_DIR"
  fi
  log "Installing backend dependencies"
  "$VENV_DIR/bin/pip" install --quiet --upgrade pip
  "$VENV_DIR/bin/pip" install --quiet \
    -r "$PROJECT_DIR/service/requirements.txt" \
    -r "$PROJECT_DIR/service/dev_requirements.txt"
fi

###############################################################################
# 2. PostgreSQL 17 (matches production and docker-compose): install it from
#    apt.postgresql.org, which must be in the network egress allowlist, and
#    replace the image's PostgreSQL 16 cluster with a 17 cluster on port 5432.
#    /migration-check restores production dumps into this cluster.
###############################################################################
if [ ! -x /usr/lib/postgresql/17/bin/postgres ]; then
  log "Installing PostgreSQL 17"
  install -d /usr/share/postgresql-common/pgdg
  if curl -fsSL -o /usr/share/postgresql-common/pgdg/apt.postgresql.org.asc \
       https://apt.postgresql.org/pub/repos/apt/ACCC4CF8.asc; then
    echo "deb [signed-by=/usr/share/postgresql-common/pgdg/apt.postgresql.org.asc] https://apt.postgresql.org/pub/repos/apt noble-pgdg main" \
      > /etc/apt/sources.list.d/pgdg.list
    { apt-get update -qq && DEBIAN_FRONTEND=noninteractive apt-get install -y -q postgresql-17; } >/dev/null 2>&1 \
      || log "WARNING: PostgreSQL 17 install failed — falling back to the existing cluster."
  else
    log "WARNING: apt.postgresql.org not reachable — add it to the network egress allowlist for PostgreSQL 17."
  fi
fi
if [ -x /usr/lib/postgresql/17/bin/postgres ] && command -v pg_lsclusters >/dev/null 2>&1; then
  pg_lsclusters -h | awk '$1 != 17 {print $1, $2}' | while read -r ver name; do
    log "Dropping PostgreSQL $ver/$name cluster in favour of 17"
    pg_dropcluster --stop "$ver" "$name"
  done
  if ! pg_lsclusters -h | awk '$1 == 17 && $2 == "main"' | grep -q .; then
    pg_createcluster 17 main --port 5432 >/dev/null
  elif [ "$(pg_lsclusters -h | awk '$1 == 17 && $2 == "main" {print $3}')" != 5432 ]; then
    pg_ctlcluster 17 main stop >/dev/null 2>&1 || true
    pg_conftool 17 main set port 5432
  fi
fi

###############################################################################
# 3. PostgreSQL: start the native cluster and ensure role + database exist.
###############################################################################
PG_READY=false
if command -v pg_ctlcluster >/dev/null 2>&1; then
  PG_VER=$(pg_lsclusters -h | awk 'NR==1{print $1}')
  PG_CLUSTER=$(pg_lsclusters -h | awk 'NR==1{print $2}')
  if ! pg_lsclusters -h | awk 'NR==1{print $4}' | grep -q online; then
    log "Starting PostgreSQL cluster $PG_VER/$PG_CLUSTER"
    pg_ctlcluster "$PG_VER" "$PG_CLUSTER" start || true
  fi
  for _ in $(seq 1 15); do
    if su postgres -c "pg_isready -q" >/dev/null 2>&1; then
      PG_READY=true
      break
    fi
    sleep 1
  done
  if [ "$PG_READY" = true ]; then
    su postgres -c "psql -tAc \"ALTER USER postgres WITH PASSWORD 'postgres';\"" >/dev/null 2>&1 || true
    if ! su postgres -c "psql -tAc \"SELECT 1 FROM pg_database WHERE datname='diplicity'\"" 2>/dev/null | grep -q 1; then
      log "Creating 'diplicity' database"
      su postgres -c "createdb -O postgres diplicity" || true
    fi
  else
    log "WARNING: PostgreSQL did not become ready — backend tests will not run."
  fi
else
  log "WARNING: PostgreSQL not found — backend tests will not run."
fi

###############################################################################
# 4. Apply migrations to the local dev database (so `runserver` works too).
###############################################################################
if [ "$PG_READY" = true ] && [ -x "$VENV_DIR/bin/python" ]; then
  log "Applying database migrations"
  if ! ( cd "$PROJECT_DIR/service" && \
         DATABASE_HOST=127.0.0.1 DATABASE_PORT=5432 DATABASE_NAME=diplicity \
         DATABASE_USER=postgres DATABASE_PASSWORD=postgres \
         DJANGO_SECRET_KEY="${DJANGO_SECRET_KEY:-local-development-only}" \
         "$VENV_DIR/bin/python" manage.py migrate --noinput ) >/tmp/diplicity-migrate.log 2>&1; then
    log "WARNING: migrate failed (see /tmp/diplicity-migrate.log)"
  fi
fi

###############################################################################
# 5. Frontend: npm dependencies.
###############################################################################
if [ -f "$PROJECT_DIR/packages/web/package.json" ]; then
  log "Installing frontend dependencies"
  ( cd "$PROJECT_DIR/packages/web" && npm install --no-audit --no-fund --silent )
fi

###############################################################################
# 6. Railway CLI for production access.
#    The CLI authenticates from $RAILWAY_API_TOKEN, but every railway command
#    reaches production via Railway's hosts (e.g. backboard.railway.com), which
#    must be in the environment's network egress allowlist, otherwise commands
#    fail with "Host not in allowlist".
###############################################################################
if [ -n "${RAILWAY_API_TOKEN:-}" ]; then
  if ! command -v railway >/dev/null 2>&1; then
    log "Installing Railway CLI"
    npm install -g --silent @railway/cli || log "WARNING: Railway CLI install failed"
  fi
  if command -v railway >/dev/null 2>&1; then
    # `railway whoami` exercises the real API + token. The egress block returns a
    # 403 "Host not in allowlist" page (not JSON), so the CLI exits non-zero —
    # this distinguishes a genuinely reachable API from an allowlist block.
    if railway whoami >/dev/null 2>&1; then
      log "Railway CLI ready (authenticated, API reachable)."
    else
      log "Railway CLI installed, but the Railway API is NOT reachable — add backboard.railway.com to the network egress allowlist to enable production commands."
    fi
  fi
else
  log "RAILWAY_API_TOKEN not set — Railway production access unavailable."
fi

# RAILWAY_TOKEN (project-scoped) powers `railway run` for /prod-query and
# /debug-production. The backend deps it needs are already in service/.venv
# (installed above and put on PATH below), so no extra install is needed here.
if [ -n "${RAILWAY_TOKEN:-}" ]; then
  log "RAILWAY_TOKEN set — 'railway run' (prod-query) available."
else
  log "RAILWAY_TOKEN not set — 'railway run' (prod-query) unavailable."
fi

###############################################################################
# 7. pgweb: production database query access over HTTPS.
#    The cloud environment's network policy blocks non-standard ports (22, 59667),
#    so `railway ssh` and `railway run` cannot reach the production database.
#    pgweb is deployed as a Railway service and exposes a REST API over port 443.
#    Set PGWEB_URL, PGWEB_USER, PGWEB_PASSWORD in the cloud environment config.
###############################################################################
if [ -n "${PGWEB_URL:-}" ]; then
  log "pgweb configured — production queries available via /prod-query."
else
  log "PGWEB_URL not set — /prod-query unavailable (set PGWEB_URL, PGWEB_USER, PGWEB_PASSWORD in environment config)."
fi

###############################################################################
# 8. GitHub CLI (gh). Authenticates automatically from $GH_TOKEN (set in the
#    cloud environment config). The mcp__github__* tools cover most GitHub
#    workflows; gh adds shell-driven access (gh api, gh pr, gh issue, gh label).
#    Without GH_TOKEN it is left uninstalled, since it would be unauthenticated.
###############################################################################
if [ -n "${GH_TOKEN:-}" ]; then
  if ! command -v gh >/dev/null 2>&1; then
    log "Installing GitHub CLI"
    apt-get install -y -q gh >/dev/null 2>&1 \
      || ( apt-get update -qq >/dev/null 2>&1 && apt-get install -y -q gh >/dev/null 2>&1 ) \
      || log "WARNING: gh install failed"
  fi
  if command -v gh >/dev/null 2>&1; then
    # gh auth status validates GH_TOKEN against api.github.com.
    if gh auth status >/dev/null 2>&1; then
      log "GitHub CLI ready (authenticated via GH_TOKEN)."
    else
      log "WARNING: gh installed but 'gh auth status' failed — check GH_TOKEN validity/permissions."
    fi
  fi
else
  log "GH_TOKEN not set — GitHub CLI not installed (use the mcp__github__* tools instead)."
fi

###############################################################################
# 9. Persist session environment: venv on PATH + local DB config, so that
#    `python`, `pytest`, and `manage.py` work without per-command env setup.
###############################################################################
if [ -n "${CLAUDE_ENV_FILE:-}" ]; then
  {
    echo "export PATH=\"$VENV_DIR/bin:\$PATH\""
    echo "export DATABASE_HOST=127.0.0.1"
    echo "export DATABASE_PORT=5432"
    echo "export DATABASE_NAME=diplicity"
    echo "export DATABASE_USER=postgres"
    echo "export DATABASE_PASSWORD=postgres"
    echo "export DJANGO_SECRET_KEY=\"${DJANGO_SECRET_KEY:-local-development-only}\""
    # pgweb credentials — exported if set in the environment config
    [ -n "${PGWEB_URL:-}" ]      && echo "export PGWEB_URL=\"${PGWEB_URL}\""
    [ -n "${PGWEB_USER:-}" ]     && echo "export PGWEB_USER=\"${PGWEB_USER}\""
    [ -n "${PGWEB_PASSWORD:-}" ] && echo "export PGWEB_PASSWORD=\"${PGWEB_PASSWORD}\""
  } >> "$CLAUDE_ENV_FILE"
fi

log "Ready: backend venv (service/.venv), PostgreSQL (diplicity), frontend deps."
