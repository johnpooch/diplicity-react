Run a production health check by gathering data from multiple sources.

## Instructions

0. **Check Railway authentication** before proceeding. Run `railway status` and check the output. If it fails with an authentication error or "not logged in" message, stop immediately and tell the user: "Railway is not configured in this session — production debugging is not available. The `RAILWAY_ACCOUNT_TOKEN` environment variable must be set in the claude.ai/code project settings."

1. **Check deployment status** by running `railway status` to see the current deployment state, uptime, and any recent deployment failures.

2. **Check recent logs** by running `railway logs --lines 50` and scanning for:
   - Error-level messages (ERROR, CRITICAL, Traceback, Exception)
   - Gunicorn worker crashes or restarts
   - Database connection errors
   - HTTP 5xx responses

3. **Check Railway platform status** by using WebFetch to check https://status.railway.com for any ongoing platform incidents that could affect the deployment.

4. **Summarize findings** clearly:
   - Deployment status (healthy / degraded / down)
   - Any errors or patterns found in logs
   - Whether there are platform-wide Railway incidents
   - Suggested next steps if issues are found

## Tips

- If you see database connection errors, check Postgres health with: `railway ssh 'python3 manage.py dbshell -c "SELECT 1"'`
- If you see Gunicorn worker crashes, check for memory issues or unhandled exceptions in the log context
- Use `/prod-query` for follow-up Django ORM queries against the production database
