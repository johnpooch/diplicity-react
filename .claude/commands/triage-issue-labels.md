# Routine: Open-issue category labelling

## Purpose
On each run, audit open GitHub issues and make sure every one carries **exactly one
category label**. Apply the correct category when it's clear; **flag — never guess —**
when it's genuinely ambiguous. Labelling is cheap and reversible, so the routine acts
directly (no PR), but it touches only the four category labels and reports everything it
did.

## Arguments
Optional batch size (how many issues to bring into compliance this run): `$ARGUMENTS`
- Default **15** when none given. Keeps each run small enough to eyeball.
- The routine is idempotent — re-running picks up where the last run left off, so testing
  is "run, review the summary, run again."

## Constants
- **Repo:** `johnpooch/diplicity-react`
- **Category labels (mutually exclusive — exactly one per issue):** `bug`, `enhancement`,
  `ai`, `chore`
- **Tools:** `mcp__github__*` only (this environment has no `gh` CLI). `list_issues` /
  `issue_read` to read, `issue_write` (method `update`) to set labels.

## Category rubric
Classify by **subject and intent**, not by which area of the code is touched.

- **`bug`** — something is broken or behaves incorrectly versus its intended behaviour;
  fixing it restores expected behaviour. Signals: "Bug:", "Fix", a reproduction, a
  screenshot of wrong output, "doesn't work", "incorrect". A *new* capability is not a bug.
- **`ai`** — the subject **is the AI / agentic development tooling itself**: Claude
  routines, the agentic-coding harness (#638 / #711 families), `CLAUDE.md`, Fable
  consistency passes, or codebase-health work whose stated purpose is making Claude / agent
  sessions more effective. Signals: "[Routine]", "[Routines]", "agentic", "Claude",
  "Fable", "CLAUDE.md", "harness".
- **`chore`** — non-feature engineering with **no direct player-facing outcome**: CI/CD,
  release pipelines / store automation, refactors or simplifications with no behaviour
  change, observability / monitoring / analytics infra, dependency or data maintenance.
  Signals: "CI", "GitHub Actions", "deploy", "pipeline", "refactor", "simplify", "monitor",
  "latency", "Metabase", standalone "migration".
- **`enhancement`** — the default. Any new player-facing feature or improvement, **and the
  backend / frontend / infra work that delivers one** — including a technical sub-task of a
  feature epic. If a task is a child of (or "Part of") a feature epic, it inherits
  `enhancement` even when the task itself is plumbing.

### Precedence (apply in order; stop at the first match)
1. Broken / incorrect behaviour → **`bug`**
2. Else, subject is the AI / agentic tooling → **`ai`** (this is why the Fable / CLAUDE.md
   passes are `ai`, not `chore`)
3. Else, pure non-feature engineering with no player-facing outcome → **`chore`**
4. Else → **`enhancement`**

### Flag — don't guess
Leave the issue's labels untouched and list it under "Needs human triage" (with a one-line
reason) when it sits on a real fault line, e.g.:
- A "## Problem"-framed item that both fixes broken behaviour *and* adds new behaviour
  (`bug` vs `enhancement`).
- Wrong-behaviour framing that is really a new rule (`bug` vs `enhancement`).
- A thin stub with too little detail to classify, unless the **title alone** is decisive
  (e.g. a "Bug:" title → `bug`).
- A technical refactor / migration where it's unclear whether it's standalone cleanup
  (`chore`) or part of a feature (`enhancement`).

Do not invent a category to avoid flagging. A flagged issue is a successful outcome.

---

## Step 1 — Gather open issues
List **open** issues (`mcp__github__list_issues`, `state: OPEN`, `perPage: 100`). The
payload is large — if a single call exceeds the output limit, read it from the saved file
in batches rather than re-fetching, or page through with `issue_read` per issue. For each
issue capture: number, title, body, and current labels.

## Step 2 — Find non-compliant issues
An issue needs work if it has **zero** category labels or **more than one**. Build the
worklist in ascending issue-number order (deterministic, so successive test runs are
predictable). Ignore all non-category labels entirely — `routine:*`, `deploy-to-staging`,
etc. are out of scope and must be preserved.

If the worklist is empty, report "all open issues are correctly categorised" and end.

## Step 3 — Take a batch
Take the first **N** issues from the worklist (N = `$ARGUMENTS` or 15). Leave the rest for
the next run.

## Step 4 — Classify each issue
For each issue in the batch, read title + body and apply the rubric and precedence above.
Decide one of: a single category, or **flag for human triage**.

- A `[Backend]` / `[Frontend]` prefix is neutral — judge by content.
- An epic or PRD for a player-facing feature is `enhancement`; an epic for the agentic
  tooling is `ai`.

## Step 5 — Apply labels
For each confidently-classified issue, call `issue_write` (method `update`) with the full
label set = **all existing non-category labels + the one chosen category label**. This both
adds the missing category and, when an issue had a wrong/extra category (e.g. an agentic
routine still tagged `enhancement` that should be `ai`), removes the incorrect one — the
`labels` array on update replaces the whole set, so always include the non-category labels
you want to keep.

Never:
- Touch non-category labels.
- Apply more than one category label.
- Open issues, comment on issues, or create PRs. This routine only edits labels.

## Step 6 — Report
End with a concise run summary for the user (not posted to GitHub):
- **Applied:** per issue — `#<n> → <category>` (note when a wrong category was corrected,
  e.g. `#714 enhancement → ai`).
- **Needs human triage:** per issue — `#<n>: <reason>`.
- **Remaining:** how many non-compliant issues are still in the worklist for the next run.

## End of run
One batch handled. Stop. Re-run to continue through the backlog.
