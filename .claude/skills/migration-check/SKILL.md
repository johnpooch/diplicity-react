---
name: migration-check
description: Sanity-check the current branch's migrations against a throwaway copy of the production database restored inside the cloud container, run any requested data checks, then drop the copy. Run only when the user explicitly asks.
disable-model-invocation: true
allowed-tools: Bash, Read, Glob, Grep
---

# Migration check against a copy of production

Checks requested: $ARGUMENTS

The copy lives only in this container. It is restored from pgweb's export endpoint because the container cannot open a Postgres connection to production (see `.claude/hooks/session-start.sh`, pgweb section). Nothing is created on Railway.

The dump holds real user data. Keep it in the scratchpad directory, never commit it, upload it, or paste rows that identify users into chat, a PR, or an issue. Report aggregates.

## 0. Preconditions

Stop and tell the user what is missing if any of these fail:

```bash
echo "$PGWEB_URL"
pg_lsclusters
```

- `PGWEB_URL` empty → pgweb is not configured (see `/prod-query`).
- No online `17` cluster on port 5432 → the session-start hook could not install PostgreSQL 17. `apt.postgresql.org` must be in the environment's network allowlist.

List what this branch adds so the report can name it:

```bash
git diff --name-only --diff-filter=A origin/main...HEAD -- 'service/**/migrations/*.py'
```

## 1. Dump production

Set `WORK` to a fresh directory inside the scratchpad, then:

```bash
start=$(date +%s)
curl -fsS -u "$PGWEB_USER:$PGWEB_PASSWORD" "$PGWEB_URL/api/export" -o "$WORK/prod.dump"
echo "dump took $(( $(date +%s) - start ))s"
ls -la "$WORK/prod.dump"
head -c 5 "$WORK/prod.dump" | od -c | head -1
```

Identify the format from the first bytes:

- `037 213` → gzip-compressed plain SQL
- `P G D M P` → `pg_dump` custom format
- `-` or `S` (a `--` comment or `SET`) → plain SQL
- `{` → pgweb returned an error. Show it and stop. A version-mismatch error means pgweb's `pg_dump` is older than production's server.

## 2. Restore into a throwaway database

```bash
dropdb -h 127.0.0.1 -U postgres --if-exists --force diplicity_prodcopy
createdb -h 127.0.0.1 -U postgres diplicity_prodcopy
```

Restore with the command matching the format, logging errors:

```bash
gunzip -c "$WORK/prod.dump" | psql -X -q -h 127.0.0.1 -U postgres -d diplicity_prodcopy 2> "$WORK/restore.log" >/dev/null
psql -X -q -h 127.0.0.1 -U postgres -d diplicity_prodcopy -f "$WORK/prod.dump" 2> "$WORK/restore.log" >/dev/null
pg_restore --no-owner --no-acl -h 127.0.0.1 -U postgres -d diplicity_prodcopy "$WORK/prod.dump" 2> "$WORK/restore.log"
```

`PGPASSWORD=postgres` is needed for every `psql`, `pg_restore`, `createdb` and `dropdb` call.

Then inspect `restore.log`. Errors about missing roles, ownership, grants, or `DROP` of objects that do not exist yet are expected for a dump restored into an empty local database. Anything else (a failed `CREATE TABLE` or `COPY`) means the copy is incomplete: report it and go to step 5.

Confirm the copy is usable:

```bash
psql -X -h 127.0.0.1 -U postgres -d diplicity_prodcopy -c "SELECT count(*) FROM django_migrations"
```

## 3. Apply the branch's migrations

From `service/`, pointing Django at the copy:

```bash
DATABASE_NAME=diplicity_prodcopy python manage.py showmigrations --plan 2>/dev/null | grep '\[ \]'
start=$(date +%s)
DATABASE_NAME=diplicity_prodcopy python manage.py migrate --noinput 2>&1 | tee "$WORK/migrate.log"
echo "migrate took $(( $(date +%s) - start ))s"
```

Pending migrations that are not on this branch mean production is behind `main`; say so, since their time is included.

If a migration fails, keep the traceback for the report and continue to step 4 only for checks that still make sense.

## 4. Run the requested checks

Run each check the user asked for against `diplicity_prodcopy` with `psql -X`, writing SQL to a file first as `/prod-query` does. Read the relevant models under `service/` to get table and column names right. When no checks were requested, run none beyond step 3.

## 5. Clean up

Always, including after a failure:

```bash
dropdb -h 127.0.0.1 -U postgres --if-exists --force diplicity_prodcopy
rm -rf "$WORK"
```

Confirm both are gone before reporting.

## 6. Report

- Dump: size, format, and how long it took
- Restore: clean, or the unexpected errors
- Migrations: which were applied, whether each applied cleanly, total time, and the failure output if any
- Checks: what each found, as aggregates
- Cleanup: confirmed
