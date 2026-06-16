# Contributing

This is a hobby project maintained by two contributors. Keeping the backlog small is deliberate — a small backlog reduces noise, prevents stale work accumulating, and makes it easier to stay focused on what is actually in flight.

---

## WIP limits

| Thing | Limit |
|-------|-------|
| Open pull requests | 5 |
| Open issues | 10 |

A bot will warn (via comment) when a new PR or issue pushes the count over the limit. The warning is advisory — it does not block — but treat it as a prompt to close or merge something before continuing.

---

## Stale policy

Issues and pull requests that receive no activity for **7 days** are labelled `stale`. After a further **7 days** of inactivity they are closed automatically.

Any activity (commit, comment, review) resets the timer. Use the `pinned` label to exempt something from the stale bot permanently.

---

## Issues

### When to open a Discussion first

If the right approach to a piece of work is not obvious — if you need to weigh options or explore trade-offs before knowing what to build — open a [GitHub Discussion](https://github.com/johnpooch/diplicity-react/discussions) first. Once the approach is clear, create a focused issue that captures the agreed approach.

Skip the Discussion if both the goal and the approach are already clear.

### Issue format

Issues follow a tight three-section format:

```
## Goal

What we are doing. (1–2 sentences, always present.)

## Context

Why / background. Include only when genuinely useful — omit the section entirely if the goal is self-explanatory.

## Approach

How we will do it. Include only when an approach was actually discussed. Never invent one.
```

Keep issues short. A single `## Goal` section is a complete issue.

### What not to include

- Sub-issues or epics. If work is too large for one issue, split it into two or three focused, independent issues.
- Acceptance criteria checklists.
- Out of scope sections.
- Tasks or implementation breakdowns.
- A list of files to change.

### Scope

Each issue should result in a **single, reviewable PR**. If a change touches both backend and frontend and the pieces are independently deployable, split into two issues: one for the backend, one for the frontend.

---

## Pull requests

### Before opening

Check the current open PR count. If it is already at 5, close or merge something first.

### Checklist

- [ ] This PR does one thing — no unrelated fixes or drive-by cleanups
- [ ] Tests cover the change
- [ ] `RELEASE_NOTES.md` updated if the change is user-facing
- [ ] Screenshots embedded in the PR description for any visual changes
- [ ] For PRs of any significant complexity: `/review-pr` run in Claude Code and findings addressed

### Screenshots

If a PR changes anything a user can see, include screenshots. See the Playwright screenshot workflow in `CLAUDE.md`.
