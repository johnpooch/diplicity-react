---
name: create-issue
description: Create a single GitHub issue for diplicity-react from a free-text description — infer whether it's a bug or feature, dig the codebase to resolve ambiguity, write a tight type-appropriate body, apply the bug/feature category label, and create it untriaged. Use when the user asks to create, open, file, or write up a GitHub issue.
allowed-tools: mcp__github__issue_write, mcp__github__issue_read, mcp__github__list_issues, mcp__github__get_label, Read, Grep, Glob, AskUserQuestion
---

# Create Issue

Create one GitHub issue in `johnpooch/diplicity-react` from a free-text description.
Default issue bodies are too wordy and over-structured; this skill exists to keep them
tight, correctly typed, and correctly labelled.

## The board model (read this first)

The Issues Board is homogeneous and agent-driven. Two rules constrain this skill:

- **Every open issue is exactly one dispatchable PR.** Anything bigger than a single PR
  is not a board issue — it belongs in GitHub Discussions as an RFC. See the
  epic-size guard below.
- **Issues carry two label dimensions.** A **category** (`bug` or `feature`) and a
  **status** (`needs-context` → `ready` → `in-progress`). This skill owns the category
  only. It **never** sets a status label: a newly created issue is **untriaged** (no
  status). `ready` in particular is a loaded gun — a cron routine auto-opens a PR for
  any `ready` issue — so status is owned solely by the triage routine or an explicit
  human, never self-applied here.

A well-formed issue from this skill should sail through daily triage; a thin one bounces
to `needs-context`. Your job is to make it well-formed.

## The core rule

An issue describes the goal in 1–2 sentences and, when there's something meaningful to
say, the context in 1–2 sentences. That is almost always the whole issue. When in doubt,
leave it out.

## Workflow

1. **Infer the type.** Decide from the description whether this is a `bug` (something is
   broken / behaves wrong) or a `feature` (something new or changed by design). Do not
   ask the user "bug or feature?" — infer it. Only ask if genuinely 50/50.

2. **Dig before asking.** Investigation effort scales with the ambiguity actually
   present, not a fixed form. Use `Read`/`Grep`/`Glob` to resolve anything the codebase
   can answer — file locations, component names, current behaviour, whether a thing
   already exists. Then ask (via `AskUserQuestion`) only the **minimum** questions the
   code *cannot* answer: intent, priority, or a UX/product choice. A trivial, fully
   specified issue needs **zero** questions. Calibration:
   - Don't ask what a 30-second grep would tell you.
   - Don't spelunk the whole codebase for a one-line copy change.
   - Stop digging once you can write a clear, single-PR spec.

3. **Apply the epic-size guard.** Before creating, ask yourself: *would one sensible PR
   close this?* If it spans multiple subsystems, needs sequenced phases, or reads as
   "do X, and then Y, and then Z", it is **not** a board issue. **Do not create it.**
   Tell the user it's larger than one PR and belongs in a
   [GitHub Discussion](https://github.com/johnpooch/diplicity-react/discussions) as an
   RFC, and stop. Do not auto-split it into multiple issues.

4. **Verify the category label exists.** Call `mcp__github__get_label` for the inferred
   category (`bug` or `feature`). If it does not exist, **do not create the label and do
   not create the issue** — stop and report that the category label is missing (this is
   a misconfigured-board signal, not something this skill papers over).

5. **Create directly.** Create the issue with `mcp__github__issue_write` (`method:
   create`), passing the body, a plain title, and `labels: ["bug"]` or
   `labels: ["feature"]` — **the category label only, no status label**. Do not
   draft-and-wait for approval.

6. **Report the link.** Reply with the new issue's URL.

## Body structure

One skeleton, with type-conditional sections. Use these sections, in order, and **no
others**.

**Feature:**

```
## Goal

<1–2 sentences: what we're adding or changing, by design.>

## Context

<1–2 sentences: why / background. Omit the section entirely if there's nothing
meaningful to add.>

## Approach

<How we'll do it. Include ONLY if an approach was actually discussed.>
```

**Bug:**

```
## Goal

<1 sentence: what needs fixing.>

## Current behaviour

<What happens now, as prose.>

## Expected behaviour

<What should happen instead, as prose.>

## Where

<The relevant file(s) / component / endpoint, when known from investigation. Omit if
genuinely not locatable or obvious.>

## Approach

<How we'll fix it. Include ONLY if an approach was actually discussed.>
```

Rules that apply to both:

- **Goal** — always present.
- **Approach** — for either type, include only when an approach was actually discussed
  in the lead-up to creating the issue. Never invent one.
- A bug's **Expected behaviour** is a short prose description, **not** an
  acceptance-criteria checklist.

## Never include

Regardless of how natural it feels:

- Acceptance criteria, Success criteria, Out of scope, or Open questions sections.
- A Tasks / breakdown checklist.
- Guiding-principles, philosophy, or rationale-for-the-rules sections.
- Self-justifying prose: "Why this is high-leverage", "Why this matters", and similar.
- A link back to the Claude conversation that produced the issue.
- Cross-links to other issues the user didn't ask to link.

## Style

- **Title** — short and plain. No marketing adjectives, no em-dash taglines, no
  "Idea N:" prefixes. Prefer `Sentry issue → GitHub issue → PR fix` over
  `Idea 1: Sentry → … the flagship telemetry loop`.
- **Emphasis** — use bold sparingly. An occasional bold term is fine; avoid the dense,
  every-other-phrase bolding that the default style tends to produce.
- **Legacy heading names** — if source material uses "Idea", rename to "Goal"; if it
  uses "Proposed loop", rename to "Approach".

## Example

A request like "the phase countdown timer on the game detail screen keeps showing
negative numbers after the deadline passes instead of saying the phase is resolving"
becomes a `bug` issue:

```
Title: Phase countdown shows negative numbers after the deadline

## Goal

Stop the game-detail phase countdown from displaying negative time once the deadline
has passed.

## Current behaviour

After a phase deadline passes, the countdown keeps ticking into negative values.

## Expected behaviour

Once the deadline passes, the countdown shows that the phase is resolving rather than a
negative duration.

## Where

The countdown component under the game detail screen in `packages/web/src/`.
```

No Context/Approach (neither was needed), category label `bug`, no status label.
