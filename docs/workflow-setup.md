# Phase 1: Orchestrator Workflow Setup

## Overview

This document describes the setup of the Claude Code orchestrator workflow. It is intended to be handed directly to Claude Code, which will work through it autonomously, pausing at the explicitly marked human review points.

All work in Wave 1 can be launched simultaneously as parallel Claude Code sessions. Subsequent waves have explicit dependencies that must be satisfied before they begin.

---

## Wave 1: Independent — Launch All Simultaneously

### 1A: Engineering Philosophy Documents

**Task:** Study the real Diplicity React codebase and produce two draft documents:

1. **Issue Philosophy Document** — how issues should be scoped and structured. Cover: what makes a good problem statement, what acceptance criteria should look like (observable behaviour not implementation steps), how technical approach should be described, how dependencies should be documented, what risks and open questions should be surfaced.

2. **Code Philosophy Document** — implementation and review standards. Cover: observed patterns in the codebase for component structure, state management, hook design, test style, naming conventions, what the codebase avoids, preference for simplicity over premature optimisation, and any other patterns evident from studying the code.

Save both documents to `.claude/philosophy/issue-philosophy.md` and `.claude/philosophy/code-philosophy.md`.

> ⚠️ **Human review required.** Both documents must be reviewed and approved by the human before Wave 2 begins. The human's corrections and additions should be noted — they will form the first entries when the `/learn-from` commands run for the first time.

---

### 1B: GitHub Label Schema

**Task:** Create the following labels in both the dummy repo and the real Diplicity React repo:

| Label | Purpose |
|---|---|
| `workflow: needs-scoping` | Issue needs the scope command run |
| `workflow: needs-staff-review` | Issue has been scoped, awaiting staff engineer review |
| `workflow: needs-revision` | Staff engineer has reviewed, revisions required |
| `workflow: needs-human-review` | Revisions applied, awaiting human approval |
| `workflow: human-approved` | Human has approved, ready for implementation |
| `workflow: in-progress` | Implementation underway |
| `workflow: needs-pr-review` | PR raised, awaiting staff engineer review |
| `workflow: pr-needs-revision` | Staff engineer PR review complete, revisions required |
| `workflow: pr-needs-human-review` | PR revisions applied, awaiting human approval |
| `workflow: pr-human-approved` | Human has approved PR |
| `workflow: merge-ready` | PR approved and ready to merge |

No human review required for this task.

---

### 1C: Dummy Repo Setup

**Task:** Create a minimal TypeScript utility library repository on GitHub with the following:

- A basic `package.json`, `tsconfig.json`, and a simple existing utility function with a unit test, so the repo has some existing code for the workflow to reason about
- A parent GitHub issue titled "Dummy Milestone: Date and String Utilities" with a brief description
- Three sub-issues:
  - "Add a date formatting utility" (no dependencies)
  - "Add a string truncation utility" (no dependencies)
  - "Add a combined display formatter utility" (depends on both of the above)
- Apply `workflow: needs-scoping` to all three sub-issues
- Define the dependency graph explicitly in each issue body and in the parent issue

No human review required for this task.

---

### 1D: Environment Variable Checklist

**Task:** Read the `.env.example` file in the real Diplicity React repo. For each variable:

- Identify which external service it belongs to
- Note where the value can be recovered (e.g. Firebase console, Google Cloud Console, Apple Developer Portal, Django settings)
- Flag any variables whose source is unclear

Produce a markdown checklist grouped by service, saved to `.claude/setup/env-checklist.md`. The human will work through this checklist manually.

No human review required for the document itself, but the human must complete the checklist before Phase 3 begins.

---

## Wave 2: Depends on 1A (Human-Approved Philosophy Documents)

### 2A: Individual Claude Code Commands

**Task:** Write all individual workflow commands as Claude Code custom command files in `.claude/commands/`. Each command must reference the philosophy documents by path and follow the label transition rules defined in the schema.

Write the following commands:

**`/scope-issue`**
- Input: issue number
- Investigates the codebase thoroughly in relation to the issue topic
- Produces a rich issue description: problem statement, technical approach, relevant file paths, acceptance criteria (observable behaviour), dependency links to other issues, prerequisites (credentials or tokens required), open questions, risks
- Posts the description as an update to the GitHub issue
- Transitions label to `workflow: needs-staff-review`

**`/review-issue`**
- Input: issue number
- Reviews the issue as a staff engineer using `issue-philosophy.md`
- Checks: is the problem statement clear, are acceptance criteria testable, is the technical approach sound and appropriately simple, are dependencies correctly identified, are risks surfaced
- Posts feedback as a GitHub comment
- Transitions label to `workflow: needs-revision`

**`/apply-issue-feedback`**
- Input: issue number
- Reads the staff engineer comment
- Updates the issue description to address all feedback points
- Transitions label to `workflow: needs-human-review`

**`/learn-from-issue-review`**
- Input: issue number
- Reads the human's changes to the issue and any comments they made during review
- Extracts the underlying principle behind each change (not just the surface change)
- Appends new principles to `issue-philosophy.md` under the appropriate section
- Does not append duplicates of principles already present

**`/implement-issue`**
- Input: issue number
- Creates a git worktree in `.worktrees/<issue-number>-<slug>`
- Creates a branch named `issue/<issue-number>-<slug>`
- Implements the work described in the issue, following `code-philosophy.md`
- Runs the full test suite and confirms it passes
- Creates a PR linked to the issue with a description summarising the approach and referencing the acceptance criteria
- Transitions issue label to `workflow: in-progress`
- Applies `workflow: needs-pr-review` to the PR

**`/review-pr`**
- Input: PR number
- Reviews the PR as a staff engineer using `code-philosophy.md` and the linked issue's acceptance criteria
- Checks: does the implementation satisfy all acceptance criteria, are there regressions, is the approach clean and appropriately simple, is test coverage adequate
- Posts inline comments directly on the PR for specific issues
- Posts a summary review comment
- If satisfied: transitions label to `workflow: pr-needs-human-review`
- If not satisfied: transitions label to `workflow: pr-needs-revision`

**`/address-pr-feedback`**
- Input: PR number
- Reads all open review comments on the PR
- Addresses each comment conservatively — minimum changes required, no scope creep, no opportunistic refactoring
- Pushes changes
- Transitions label to `workflow: needs-pr-review` to trigger another review pass

**`/learn-from-pr-review`**
- Input: PR number
- Reads the human's review comments and any changes they requested
- Extracts the underlying principle behind each piece of feedback
- Appends new principles to `code-philosophy.md` under the appropriate section
- Does not append duplicates

> ⚠️ **Human review required** for each command before Wave 3 begins. Review for: does the command do what it says, will it produce the right label transitions, does it reference the philosophy documents correctly, is the staff engineer persona well-calibrated.

---

### 2B: Orchestrator Command

**Task:** Write the `/orchestrate` command in `.claude/commands/`.

The orchestrator:
- Takes a parent issue number as input
- Reads all linked sub-issues and their current labels
- Reads all PRs associated with those issues and their current labels
- Builds the dependency graph from the issue descriptions
- For each work item, determines what action is available based on current label state:
  - `workflow: needs-scoping` + dependencies met → spawn sub-agent to run `/scope-issue`
  - `workflow: needs-revision` → spawn sub-agent to run `/apply-issue-feedback`
  - `workflow: needs-human-review` → skip, add to waiting report
  - `workflow: human-approved` → spawn sub-agent to run `/implement-issue`
  - PR `workflow: needs-pr-review` → spawn sub-agent to run `/review-pr`
  - PR `workflow: pr-needs-revision` → spawn sub-agent to run `/address-pr-feedback`
  - PR `workflow: pr-needs-human-review` → skip, add to waiting report
- Spawns sub-agents for all actionable items in parallel where they are independent
- On completion, prints a summary: what was actioned, what is waiting for human review, what is blocked and why
- Exits cleanly

The orchestrator does no implementation work itself. It is a conductor only.

> ⚠️ **Human review required** before Wave 3 begins.

---

## Wave 3: Depends on 1B, 1C, and Human-Approved 2A and 2B

### 3A: Write CLAUDE.md

**Task:** Write a `CLAUDE.md` file in the root of both the dummy repo and the real repo documenting:

- The full workflow and what each command does
- The label schema and what each label means
- Branch naming convention: `issue/<number>-<slug>`
- Worktree convention: `.worktrees/<number>-<slug>`
- PR description format
- Links to both philosophy documents
- All Claude Code permissions required by the workflow

---

### 3B: Configure Claude Code Permissions

**Task:** Do a dry run of each command against the dummy repo. For every permission prompt that appears:

- Log the permission that was requested
- Grant it in Claude Code settings
- Document it in `.claude/setup/permissions.md`

Continue until all commands run without any permission prompts. The goal is zero interruptions during the end-to-end test.

---

## Wave 4: Depends on 3A and 3B

### 4A: End-to-End Orchestrator Test on Dummy Repo

**Task:** Run `/orchestrate` against the dummy repo parent issue and work through the full pipeline.

Verify the following:

- All three sub-issues are scoped correctly and independently
- The dependency ordering is respected — the combined formatter issue is not implemented until both utility issues are merged
- Human pause points occur at `workflow: needs-human-review` and `workflow: pr-needs-human-review` and nowhere else
- The PR feedback loop works — deliberately leave a review comment on one PR and verify `/address-pr-feedback` handles it correctly
- `/learn-from-issue-review` and `/learn-from-pr-review` produce sensible principle additions to the philosophy documents after human reviews
- Parallel unblocked issues are handled concurrently

> ⚠️ **Human review required** at each pause point during the test run. After the full run, do a final review of the philosophy documents to confirm the learning commands are producing useful output.

Iterate on commands and philosophy documents based on what the test surfaces. Re-run as needed until quality is satisfactory.

---

## Wave 5: Depends on Wave 4 Sign-Off

### 5A: Stub Real Repo Parent Issue and Sub-Issues

**Task:** In the real Diplicity React repo, create:

- A parent issue: "Milestone: Capacitor JS iOS Integration" — include the high-level context from the overview document
- Sub-issues for all known work items (see the Capacitor work overview document for the full list)
- Apply `workflow: needs-scoping` to all sub-issues
- Define the initial dependency graph between issues in each issue body and in the parent

The orchestrator will then take over and run the scoping phase autonomously, pausing for human review at each issue before implementation begins.
