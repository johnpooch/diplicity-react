# Routine: Author a PR from a `ready-for-claude` issue

## Purpose
On each scheduled run, pick **one** open issue labelled `ready-for-claude`, author a pull
request that resolves it, and open that PR. The defining responsibility of this routine is
**doing work in the right order**: many `ready-for-claude` issues are epics or sequenced
children of an epic, and implementing a child before its dependencies are merged produces a
broken, un-reviewable PR. So before writing any code the routine must work out whether the
issue **is** an epic/parent, **belongs to** an epic/parent, or **stands alone**, and only
proceed when the issue is genuinely the next actionable unit of work.

If an issue is too ambiguous, too large for a single PR, or blocked by unfinished
dependencies, the routine does **not** force a PR — it comments (for ambiguity) or steps
over it (for blocked/in-flight) and moves on.

## CRITICAL: GitHub calls run in the main session
Make **every** `mcp__github__*` call directly in the main session. Subagents do not inherit
MCP tool access and will silently fail, which is especially dangerous here (a missed
"already has an open PR" check leads to duplicate work). You may use the repo's specialist
agents (`django-backend-developer`, `react-frontend-developer`, `lint-typecheck-resolver`)
for the **code implementation** itself, but never for reading issues, creating the PR, or
commenting.

## Constants
- **Repo:** `johnpooch/diplicity-react`
- **Eligibility label:** `ready-for-claude`
- **Branch naming:** `claude/issue-<number>-<short-desc>`
- **Per-run budget:** author **one** PR to completion. If nothing is actionable this run,
  finish with a report and stop — do not force a low-quality PR.
- **Tools:** `mcp__github__*` (not `gh`) for all GitHub I/O; `git` for branch/commit/push.

## Environment
Runs in Claude Code on the web. Honour `CLAUDE.md`: use `service/.venv` for the backend,
the native Postgres cluster for tests, and the documented codegen/lint/test commands. Use
**MCP tools, not `gh`**.

---

## Step 1 — Gather candidates
Call `mcp__github__list_issues` (state `OPEN`, `labels: ["ready-for-claude"]`, `perPage:
100`). For each issue capture: number, title, body, labels, author.

If the list is empty, report "no open `ready-for-claude` issues" and end.

> Note: `list_issues`/`get_sub_issues` payloads can be very large. If a tool result is
> truncated to a file, slice it with `python3` rather than re-fetching — you only need
> number, state, title, and the dependency lines from each body.

## Step 2 — Classify every candidate (epic vs child vs standalone)
For each candidate, decide its shape from these signals:

- **Epic / parent / PRD** — do **not** implement directly. Signals (any one is enough):
  - Title starts with `Epic:` or `PRD:`.
  - `mcp__github__issue_read` (`method: get_sub_issues`) returns one or more sub-issues.
  - Body contains a milestone/sub-issue checklist (`- [ ] #NNN`) or text like "Sub-issues
    are listed below" / "## Milestones".
  - Body reads as a requirements document (`## Goals`, `## Functional Requirements`,
    `## Acceptance Criteria`) describing a feature area rather than one concrete change.
- **Child of an epic** — actionable, but only in order. Signals:
  - A `[N/M]` prefix in the title (e.g. `[4/9]`).
  - `Part of #NNN` / `Depends on …` lines in the body.
  - `mcp__github__issue_read` (`method: get`) returns a `parent_issue_url`, or the issue
    appears in some epic's `get_sub_issues`.
- **Standalone** — none of the above; a single self-contained change.

## Step 3 — Resolve dependencies and pick the next actionable issue
Build the set of **leaf** work items (standalones + the children of any epic candidate, even
children that don't themselves carry `ready-for-claude` — an epic can reference a child that
must land first). Then filter:

1. **Drop in-flight items.** Call `mcp__github__search_issues`
   (`is:pr is:open` in this repo) and check open PRs for one that resolves the issue —
   a `Closes #<n>` / `Fixes #<n>` in the body, the issue number in the title, or a branch
   named for it. If found, the issue is **in flight → skip**.
2. **Drop blocked items.** An item is blocked if any of its stated dependencies is **not
   done**. A dependency is *done* only when its issue is **closed as completed** (read state
   via `mcp__github__issue_read`) or already merged. Resolve dependencies from:
   - explicit `Depends on [k/M]` / `Depends on #NNN` lines on the child,
   - the `[N/M]` sequence (treat a lower-numbered sibling as a prerequisite unless its body
     says "Ships alone" / "independent"),
   - the parent epic's dependency graph ("#X must be done before #Y").
   Do **not** treat "still carries `ready-for-claude`" as "not done" and do **not** treat
   "lost the label" as "done" — read the issue **state**. (e.g. at time of writing #586 and
   #584 are closed-completed, which unblocks their frontend counterparts.)
3. **Order what remains.** Among unblocked, not-in-flight items, prefer the one that
   unblocks the most downstream work: for a sequenced epic that is the lowest `[N/M]`; for
   a dependency-graph epic the earliest node with all prerequisites done; otherwise the
   oldest standalone (FIFO by creation date).

Pick the **single** highest-priority actionable item. Carry forward which epic it belongs to
(if any) for the PR description.

If **every** candidate is in-flight or blocked, report that (listing what each is waiting
on) and end — there is nothing to do this run.

## Step 4 — Ambiguity / size gate (comment-only outcomes)
Before implementing, sanity-check that the chosen issue is a buildable, single-PR unit of
work. **Leave a comment and stop** (don't force a PR) when:

- **Too ambiguous** — you cannot tell what concrete change is wanted, or there are multiple
  plausible interpretations with materially different implementations.
- **Too large for one PR** — the chosen item is itself an epic/PRD with **no decomposed
  sub-issues to descend into** (e.g. a standalone PRD like #624). A single PR cannot
  responsibly deliver a whole requirements document.

When either applies:
- Post one concise `mcp__github__add_issue_comment` that says specifically what is missing
  or how it should be split — enough that a human can act on it without guessing. For an
  undecomposed epic/PRD, suggest the concrete sub-issues it should be broken into.
- **Remove `ready-for-claude`** via `mcp__github__issue_write` (`method: update`, label set
  = all current labels minus `ready-for-claude`). This is the dedup: the issue leaves the
  worklist until a human re-triages it, so the routine won't re-comment on it next run.
- Report the outcome and **end the run** (this counts as the run's one unit of work).

Never invent a scope to make an ambiguous issue buildable, and never delete or rewrite the
issue body — comment only.

## Step 5 — Implement
Create the branch `claude/issue-<number>-<short-desc>` off the latest `main`. Implement the
change, following `CLAUDE.md` and the repo conventions exactly:

- Backend in `service/` (managers/serializers/views split, `service/.venv`, native
  Postgres); frontend in `packages/web/` (React Query + Suspense, shadcn/ui, no Redux).
- If the change touches the API surface, run codegen (`docker compose up codegen`, or the
  native `spectacular` + `orval` path) and then `npx tsc -b --noEmit` in `packages/web`.
- Add/extend tests **alongside** the change (backend `pytest`, frontend Vitest).
- Add a `RELEASE_NOTES.md` entry if the change is player-facing.

Stay scoped to the chosen issue — if you discover the issue actually depends on unfinished
work you missed in Step 3, stop, leave a comment noting the blocker, and end (do not expand
scope or implement the dependency too).

## Step 6 — Quality gate (mandatory, scoped)
Do **not** run the full suite. Run only what the change touches:
- Frontend: `npm run lint` and `npx tsc -b --noEmit` in `packages/web`, plus the relevant
  `npm run test <file>`.
- Backend: the relevant `pytest <file>` (single file/test for fast feedback).

If anything fails and you can't fix it cleanly, comment the blocker on the issue, leave the
issue labelled, push nothing broken, and end. Never open a PR on code that doesn't compile
or whose tests fail.

## Step 7 — Visual evidence (frontend changes only)
If the change alters anything a user can see, capture screenshots per `CLAUDE.md`
(`npm run dev:mocks` + `npm run screenshot`, picking a fixture from the registry; mobile
viewport when the change affects mobile). Push them to a `screenshots/*` branch and embed
commit-pinned raw URLs in the PR body. If there are genuinely no visual changes, say so
explicitly in the PR description.

## Step 8 — Open the PR
Push the branch (`git push -u origin <branch>`, retrying with backoff on network errors).
Open the PR with `mcp__github__create_pull_request` (base `main`). The body **must**:
- Start with `Closes #<issue-number>` so merging auto-closes the issue.
- If the issue is a child of an epic, link the parent ("Part of #<epic>") and note which
  earlier sub-issues this builds on.
- Briefly state what changed and how it was verified; include the screenshots (or the
  explicit "no visual changes" note).

For any non-trivial PR, run `/review-pr` against it and address (or explicitly respond to)
the findings before finishing, per the repo convention.

## Step 9 — Report
End with a concise summary:
- **Authored:** `#<issue> → PR #<pr>` (and the epic it belongs to, if any).
- **Or commented:** `#<issue>: <one-line reason>` (ambiguous / undecomposed epic).
- **Skipped this run:** in-flight and blocked items, each with what it's waiting on — so the
  next run's starting point is clear.

## End of run
One unit of work handled — a PR opened, or an ambiguous issue commented + de-labelled, or a
clean "nothing actionable" report. Stop.
