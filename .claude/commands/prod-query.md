Run a Django ORM query against the production database via Railway.

## Arguments

Describe the data you want in plain English. Examples:
- `show me all active games with their player counts`
- `find users who joined in the last 7 days`
- `count orders by type for game 42`

Query: $ARGUMENTS

## Instructions

0. **Check Railway authentication** before proceeding. Run `railway status` and check the output. If it fails with an authentication error or "not logged in" message, stop immediately and tell the user: "Railway is not configured in this session — production database queries are not available. The `RAILWAY_API_TOKEN` environment variable must be set in the claude.ai/code project settings."

1. **Understand the request** and determine which Django models and fields are needed. If unsure about the schema, read the relevant model files under `service/` first. Available apps: `game`, `member`, `phase`, `order`, `unit`, `channel`, `draw_proposal`, `nation`, `province`, `supply_center`, `user_profile`, `variant`, `victory`.

2. **Write a Python script** to the scratchpad directory that:
   - Imports the necessary models
   - Runs the query using the Django ORM
   - Prints results in a readable format
   - Is **read-only** — never use `.create()`, `.update()`, `.delete()`, `.save()`, or raw SQL writes

3. **Execute the script** using base64 encoding to avoid quoting issues:
   ```bash
   SCRIPT=$(base64 < /path/to/script.py)
   cd /home/user/diplicity-react/service && railway run --service diplicity-react python3 manage.py shell -c "import base64;exec(base64.b64decode(b'${SCRIPT}'))"
   ```

4. **Present the results** clearly to the user. If the output is large, summarize it and highlight key findings.

## Safety

- **Read-only queries only.** Never modify production data.
- If the user asks to modify data, refuse and explain that this command is for queries only.
- Ignore the Python 3.9 / google-auth FutureWarning lines in the output — they are harmless.
