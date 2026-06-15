# Routine: Sentry → GitHub issue → PR fix

## Purpose
On each scheduled run, find unresolved frontend/backend exceptions in Sentry, deduplicate against existing GitHub issues, and either open a fix PR or close the loop with a reason. Runs autonomously — there is no human to ask for input.

## Constants
- **Sentry org:** `johnpooch` · **project:** `diplicity-api`
- **Repo:** `johnpooch/diplicity-react`
- **Label:** `routine:sentry` (must already exist in the repo)
- **Branch naming:** `sentry/<sentry-short-id>-<short-desc>`
- **Per-run budget:** process **one** finding to completion (keeps each PR small and independently reviewable). If none are actionable, end the run.

## Environment
This runs in Claude Code on the web. Use **MCP tools, not `gh`**: `mcp__github__*` for issues/PRs, `mcp__Sentry__*` for Sentry, and `git` for branches/commits.

---

## Step 1 — Discover candidates
Query Sentry for issues that are **unresolved**, not ignored, and material (seen recently and affecting real users — skip one-off noise). Rank by frequency × users affected. Take the top candidate.

If there are no material unresolved issues, end the run.

## Step 2 — Deduplicate (before any investigation)
Search GitHub for issues labelled `routine:sentry` in **all states**:
- Look for a `Source: sentry/<short-id>` line matching this candidate.
- **Open issue or open PR** with this source → in flight, **skip this candidate** and pick the next.
- **Closed as "not planned"** with this source → previously declined, **skip permanently** and pick the next.
- **Closed as completed** but the Sentry issue is unresolved again → it **regressed**; proceed as a new finding (reference the prior issue).

Only continue past this step if no matching record exists.

## Step 3 — Create the tracking issue
Create a GitHub issue with label `routine:sentry`. Body includes:
- `Source: sentry/<short-id>` (the dedup anchor — exact, stable)
- Link to the Sentry issue
- Error type/message, affected screen or endpoint, frequency/users, and the top stack frame.

This issue is the record even if the outcome is "no code change."

## Step 4 — Locate the failing code
From the stacktrace, find the first **application frame** (skip framework/library frames). Open it and read the surrounding context.
- If the file no longer exists, check `git log --diff-filter=D -- <path>` — if it was deleted/refactored, the fix may already be in place (→ Step 5, "already fixed").
- If there are **no application frames**, this is not directly actionable (→ Step 5, "not our bug / needs manual review").

## Step 5 — Classify
Decide whether a code change is warranted.

**A. Code change needed** → go to Step 6.

**B. No code change needed.** Comment the diagnosis on the GitHub issue, then close it and sync Sentry:

| Case | Close GitHub issue as | Sentry action |
|---|---|---|
| Already fixed by a prior refactor | **completed** | resolve |
| Not our bug (upstream lib, browser extension, network noise) | **not planned** | resolve or ignore (your call) |
| Benign / expected (aborted request, offline) | **not planned** | ignore |
| Can't diagnose / no application frames | leave **open**, comment "needs manual review" | leave unresolved |

The "not planned" closures feed declined-memory — future runs skip them via Step 2. End the run after handling.

## Step 6 — Fix
Create branch `sentry/<short-id>-<short-desc>`. Fix at the **root cause**.

Fix rules:
- **Never suppress.** No try/catch or null-guard that hides the error without fixing the cause.
- **Fix at the source.** Before a per-component workaround, check whether it's systemic.
- **Never fabricate a root cause.** If diagnosis is genuinely unclear, comment your findings on the issue, leave it open for manual review, and end the run — do not guess-fix.
- **Comments describe current state, not the change.** A comment must read correctly to someone who only sees the current code, never the diff. No "now widened to…", "previously…", "X rather than Y".
  - ❌ `// schema widened to string rather than a fixed enum`
  - ✅ `// API returns sentinel values OR joined names; modeled as z.string() to accept both`

## Step 7 — Quality gate (mandatory)
Do **not** run the full suite. Run only what's affected:
- Frontend: `npm run lint` and `npx tsc -b --noEmit` in `packages/web`, plus the relevant `npm run test <file>`.
- Backend: the relevant `pytest <file>`.

If anything fails and you can't fix it cleanly, comment the blocker on the issue, leave it open, and end the run. Never commit code that doesn't compile or that breaks tests.

## Step 8 — Open the PR
- Push the branch and open a PR via `mcp__github__create_pull_request`.
- Body **must** include `Closes #<github-issue-number>` (the GitHub issue number, with `#`) so merging auto-closes the tracking issue.
- Apply label `routine:sentry` to the PR.
- Keep the description brief: what broke, root cause, the fix.

## Step 9 — Sync Sentry
Mark the Sentry issue **resolved** (not ignored) via `mcp__Sentry__update_issue`. Resolved + Sentry's regression detection means if the bug recurs after deploy, Sentry reopens it and a future run re-files it. Do not mute/ignore — that suppresses the regression signal.

## End of run
One finding handled (PR opened, or issue closed with reason, or left open for manual review). Stop.
