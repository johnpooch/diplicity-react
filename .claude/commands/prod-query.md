Run a Django ORM query against the production database via Railway SSH.

## Arguments

Describe the data you want in plain English. Examples:
- `show me all active games with their player counts`
- `find users who joined in the last 7 days`
- `count orders by type for game 42`

Query: $ARGUMENTS

## Instructions

1. **Understand the request** and determine which Django models and fields are needed. If unsure about the schema, read the relevant model files under `service/` first. Available apps: `game`, `member`, `phase`, `order`, `unit`, `channel`, `draw_proposal`, `nation`, `province`, `supply_center`, `user_profile`, `variant`, `victory`.

2. **Write a Python script** to the scratchpad directory that:
   - Imports the necessary models
   - Runs the query using the Django ORM
   - Prints results in a readable format
   - Is **read-only** — never use `.create()`, `.update()`, `.delete()`, `.save()`, or raw SQL writes

3. **Execute the script** using base64 encoding to avoid quoting issues:
   ```bash
   SCRIPT=$(base64 < /path/to/script.py)
   railway ssh "python3 manage.py shell -c \"import base64;exec(base64.b64decode(b'${SCRIPT}'))\""
   ```

4. **Present the results** clearly to the user. If the output is large, summarize it and highlight key findings.

## Safety

- **Read-only queries only.** Never modify production data.
- If the user asks to modify data, refuse and explain that this command is for queries only.
- Ignore the Python 3.9 / google-auth FutureWarning lines in the output — they are harmless.
