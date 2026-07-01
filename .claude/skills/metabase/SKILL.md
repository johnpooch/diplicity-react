---
name: metabase
description: Metabase analytics guidance for diplicity-react — native SQL patterns for multi-hop joins, base64 encoding workflow, and schema gotchas in the diplicity production database. Use when writing Metabase queries or working around schema limitations.
allowed-tools: Bash, Read, Glob, Grep
---

# Metabase Analytics

## Native SQL (required for multi-hop joins)

Metabase MCP tools (`query`, `construct_query`) only support single-hop implicit FK traversal. For any query needing more than one FK hop, use native SQL.

**Always write SQL to a file — never inline it in a shell command.** Shell escaping corrupts SQL (`=` becomes `:`, DEL chars appear silently).

```python
# 1. Write SQL to /tmp/query.sql via the Write tool

# 2. Encode
import json, base64

with open('/tmp/query.sql') as f:
    sql = f.read().strip()

payload = {
    'lib/type': 'mbql/query',
    'stages': [{'lib/type': 'mbql.stage/native', 'native': sql, 'template-tags': {}}],
    'database': 2   # production diplicity DB
}
encoded = base64.b64encode(json.dumps(payload).encode('ascii')).decode('ascii')

# 3. Always roundtrip-assert before using
decoded = json.loads(base64.b64decode(encoded))
assert decoded['stages'][0]['native'] == sql

print(encoded)
```

**Use the base64 immediately in the next tool call** — do not store it and reference it in a later message. The context window can corrupt long base64 strings between turns.

Always test with `execute_query` before `create_question`. If the query looks correct but `execute_query` fails with a syntax error, regenerate the base64 from the file rather than fixing the stored string.

To save to the root "Our analytics" collection, pass `collection_id=null`.

## Schema Gotchas (phase / game tables)

- `phase_phase.completed_at` is **always NULL** — use `status = 'completed'` to identify resolved phases
- `phase_phase.updated_at` is **unreliable for time-bucketing** — batch operations reset it, clustering all historical data in recent weeks. Use `scheduled_resolution` instead
- `phase_phase.scheduled_resolution IS NOT NULL` is required — ~21% of phases have no deadline (manual-resolution games)
- `phase_phase.started_at` is always NULL
- Two-hop FK joins (`phase_phasestate → phase_phase → game_game`) require native SQL — implicit FK fails with "missing FROM-clause entry"
