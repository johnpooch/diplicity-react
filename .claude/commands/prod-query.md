Run a read-only SQL query against the production database via pgweb.

## Arguments

Describe the data you want in plain English. Examples:
- `show me all active games with their player counts`
- `find users who joined in the last 7 days`
- `count orders by type for game 42`

Query: $ARGUMENTS

## Instructions

0. **Check pgweb is configured** before proceeding:
   ```bash
   echo $PGWEB_URL
   ```
   If it is empty, stop immediately and tell the user:
   > "pgweb is not configured in this session. Set `PGWEB_URL`, `PGWEB_USER`, and `PGWEB_PASSWORD` in the Claude Code on the web environment configuration."

1. **Understand the request** and determine which tables and fields are needed. Read the relevant model files under `service/` to understand the schema. Available apps: `game`, `member`, `phase`, `order`, `unit`, `channel`, `draw_proposal`, `nation`, `province`, `supply_center`, `user_profile`, `variant`, `victory`.

   Key schema notes:
   - `game_game.status` values: `active`, `staging`, `pending`, `completed`, `abandoned`
   - `phase_phase.completed_at` is always NULL — use `status = 'completed'` instead
   - `phase_phase.updated_at` is unreliable — batch operations reset it, clustering historical data in recent weeks. Use `scheduled_resolution` for time-bucketing
   - `phase_phase.started_at` is always NULL
   - Filter on `phase_phase.scheduled_resolution IS NOT NULL` when bucketing by it — manual-resolution games have no deadline, and their phases are a biased pocket (few rated seats, very high NMR), not a random sample
   - `phase_phase.scheduled_resolution` is when resolution was scheduled, not when it happened. Phases resolve early once everyone confirms, so it mis-times many completed phases, and the bias runs one way: low-NMR phases land in the wrong bucket

2. **Write the SQL** to `/tmp/prod-query.sql`. Always write to a file — never inline SQL in the curl command (shell escaping corrupts queries):
   ```bash
   cat > /tmp/prod-query.sql << 'EOF'
   SELECT ...
   EOF
   ```

3. **Execute via pgweb API:**
   ```bash
   curl -s -u "$PGWEB_USER:$PGWEB_PASSWORD" \
     -X POST "$PGWEB_URL/api/query" \
     --data-urlencode "query@/tmp/prod-query.sql" \
     | python3 -c "
   import json, sys
   d = json.load(sys.stdin)
   if 'error' in d:
       print('ERROR:', d['error'])
       sys.exit(1)
   print('\t'.join(d['columns']))
   for row in d['rows']:
       print('\t'.join(str(c) for c in row))
   print(f\"\n{d['stats']['rows_count']} rows ({d['stats']['query_duration_ms']:.0f}ms)\")
   "
   ```

4. **Present the results** clearly to the user. If the output is large, summarise it and highlight key findings.

## Safety

Do not write to production unless the user asks you to.
