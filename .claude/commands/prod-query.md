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
   - `phase_phase.updated_at` is unreliable — use `scheduled_resolution` for time-bucketing

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

- **Read-only queries only.** Never issue `INSERT`, `UPDATE`, `DELETE`, `DROP`, `TRUNCATE`, or any DDL.
- If the user asks to modify data, refuse and explain that production data changes must go through a migration or a controlled admin process.
