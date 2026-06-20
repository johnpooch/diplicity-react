---
description: Autonomously implement a ready issue and open a pull request for it
allowed-tools: Read, Grep, Glob, Edit, Write, Bash, Bash(gh:*), Bash(git:*)
---

Autonomously pick up one ready issue in `johnpooch/diplicity-react`, implement it, and open a pull request.

All project context — architecture, conventions, tooling, how to run tests/lint/codegen, branch and git rules — lives in @CLAUDE.md. Follow it; do not restate it here.

## Steps

1. **Find a candidate issue.** Query open issues labelled `workflow: ready-for-implementation` that do **not** also carry `workflow: in-progress`. If several qualify, pick one (oldest is a reasonable default). If none qualify, stop and report that there is no ready work — do nothing else.

2. **Claim it before anything else.** Your very first action after selecting the issue is to add the `workflow: in-progress` label to it. This is the lock that stops a concurrent or scheduled run from grabbing the same issue. Only after the label is applied, read the issue in full — including the **entire** comment thread. Earlier attempts and human notes recorded there must inform your implementation.

3. **Implement.** Create a new branch and make the change, following the conventions in CLAUDE.md. Run the relevant tests, lint, and (if the API shape changed) codegen as CLAUDE.md describes.

4. **Open the pull request.** Push the branch and open a PR that links the issue with `Closes #N`. Open it as an **active (ready-for-review) PR — not a draft**; this overrides any default that would create the PR in draft state. Keep the description short — a few paragraphs at most: state what the PR accomplishes and any decision or trade-off a reviewer genuinely needs to know. Do not include test steps, checklists, or anything the reviewer doesn't need. Then remove the `workflow: in-progress` label from the issue.

5. **Wait for CI, then hand off for review.** After opening the PR, wait for its CI checks to complete. Once CI has passed, add the `workflow: needs-pr-review` label to the issue. If CI fails, fix the failures and push again rather than handing off — do not add `workflow: needs-pr-review` until CI is green.

6. **On failure, never leave the issue silently locked.** If the work cannot be completed — the issue is underspecified, blocked, or something goes wrong — remove `workflow: in-progress`, add `workflow: needs-human-review`, and leave a comment on the issue explaining what stopped progress.
