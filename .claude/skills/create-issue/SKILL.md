---
name: create-issue
description: Create a GitHub issue for diplicity-react in a concise house style — a short Goal, optional Context, and an Approach only when one was discussed. Use when the user asks to create, open, file, or write up a GitHub issue (including sub-issues / epics).
allowed-tools: mcp__github__issue_write, mcp__github__sub_issue_write, mcp__github__issue_read, mcp__github__list_issues, AskUserQuestion
---

# Create Issue

Create a GitHub issue in `johnpooch/diplicity-react` that is short and free of fluff.
Default issue bodies are too wordy; this skill exists to keep them tight.

## The core rule

An issue describes the goal in 1–2 sentences and, when there's something
meaningful to say, the context in 1–2 sentences. That is almost always the whole
issue. When in doubt, leave it out.

## Body structure

The body uses these sections, in this order, and **no others**:

```
## Goal

<1–2 sentences: what we're doing.>

## Context

<1–2 sentences: why / background.>

## Approach

<How we'll do it.>
```

- **Goal** — always present.
- **Context** — include only when there's genuinely useful background. If there's
  nothing meaningful to add, omit the whole `## Context` section. An issue can be
  just a `## Goal`.
- **Approach** — include **only when an approach was actually discussed** in the
  lead-up to creating the issue. If no approach was discussed, omit the section
  entirely. Never invent one.

## Never include

Do not add any of the following, regardless of how natural it feels:

- Cross-links to other epics or issues the user didn't ask to link. The
  parent↔child relationship is already implicit via GitHub's native sub-issue
  link — never write a "parent: #N" line in the body.
- Guiding-principles, philosophy, or rationale-for-the-rules sections.
- A list of sub-issues. GitHub renders the sub-issue list automatically; repeating
  it in the body is redundant.
- Self-justifying prose: "Why this is the flagship", "Why this is high-leverage",
  "Why this matters", and similar.
- Out of scope, Open questions, Success criteria, or Acceptance criteria sections.
- A Tasks / breakdown checklist. Break work down with sub-issues instead.
- A link back to the Claude conversation that produced the issue.

## Style

- **Title** — short and plain. No marketing adjectives, no em-dash taglines, no
  "Idea N:" prefixes. Prefer `Sentry issue → GitHub issue → PR fix` over
  `Idea 1: Sentry → … the flagship telemetry loop`.
- **Emphasis** — use bold sparingly. An occasional bold term is fine; avoid the
  dense, every-other-phrase bolding that the default style tends to produce.
- **Legacy heading names** — if the source material uses "Idea", rename to "Goal";
  if it uses "Proposed loop", rename to "Approach".

## Workflow

1. **Clarify only if needed.** Write from what the user gave you. Ask a clarifying
   question (via `AskUserQuestion`) only when the goal is genuinely ambiguous
   enough that you'd likely guess wrong — otherwise proceed.
2. **Create directly.** Create the issue on GitHub immediately with
   `mcp__github__issue_write`; do not draft-and-wait for approval.
3. **No labels, no issue type.** Leave labels and issue type unset — the user sets
   those.
4. **Sub-issues use native linking.** When the issue is a sub-issue of an existing
   issue, attach it with `mcp__github__sub_issue_write` (parent/child link) rather
   than mentioning the parent in the body.
5. **Report the link.** After creating, reply with the new issue's URL.

## Example

A request like "create an issue for the Sentry → GitHub issue → PR fix routine; we
talked about the loop being: read the Sentry issue, reproduce, write a failing test,
fix, open a PR" becomes:

```
Title: Sentry issue → GitHub issue → PR fix

## Goal

Stand up a routine that turns a Sentry issue into a fix PR automatically.

## Approach

Read the Sentry issue, reproduce it, write a failing regression test, fix it,
and open a PR.
```

No Context section (none was needed), no Approach unless it had been discussed —
here it was, so it's kept and named "Approach".
