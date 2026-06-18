---
name: create-discussion
description: Create a single RFC in GitHub Discussions for diplicity-react from a free-text description — interview to nail the scope and a machine-readable definition of done, investigate the codebase to resolve ambiguity, write a tight RFC body, and post it to the RFC category as "under discussion". Use when the user wants to open an RFC, epic, or Discussion for work bigger than one PR.
allowed-tools: Bash, Read, Grep, Glob, AskUserQuestion
---

# Create Discussion (RFC)

Create one RFC in `johnpooch/diplicity-react`'s GitHub **Discussions** from a
free-text description. Discussions are the messy-notebook surface for work too big
for the board; this skill exists to turn a rough epic into a well-scoped RFC with a
concrete stop condition.

## The two surfaces (read this first)

The project runs on two deliberately separate surfaces:

- **The Issues Board is pristine.** Every open issue is exactly one dispatchable PR.
  A cron routine triages and auto-implements them. The `create-issue` skill owns this
  surface.
- **GitHub Discussions are the other surface.** They hold (a) **epics expressed as
  RFCs** and (b) loose aspirational braindumps. Discussions are *exempt* from the
  board's cleanliness rules — that separation is the whole point.

This skill produces **RFCs only**. A loose braindump does not need a skill — it gets
typed straight into Discussions by hand, with no definition of done forced on it. If
the request is genuinely just an idea dump rather than an epic with a destination,
say so and stop; do not inflate it into an RFC.

## How an RFC becomes work (why definition-of-done is required)

An RFC moves through a label state machine: **(no label = under discussion)** →
`needs-context` (optional) → `human-approved` → `in-progress` → closed.

- `human-approved` is a **human gate** — a person signs off the RFC. **This skill must
  never apply it**, exactly as the `create-issue` skill must never apply `ready`.
- Once approved, a cron routine slices the RFC into board issues **one at a time**,
  adaptively: each cycle it reads the RFC, the already-merged slices, and the codebase,
  then decides the next slice — or closes the discussion when the goal is met.

So the bot owns the **sequencing**; the human owns the **destination**. The RFC's
**Definition of done is the machine-readable STOP CONDITION** for that slicing routine.
That is why it is **required** here — and why you must **not** pre-write a slice
breakdown: the bot derives slices dynamically. (Sequencing constraints, if any genuinely
exist, may be noted as prose. Never a task checklist.)

> Note: the sibling `create-issue` skill *bans* "success/acceptance criteria" on issues.
> Do **not** cargo-cult that ban here. On an RFC, definition-of-done is mandatory.

## The core rule

An RFC states the goal and a concrete, checkable definition of done. Add context only
when there's something meaningful to say. Keep it tight — no slice breakdown, no
self-justifying prose.

## Workflow

1. **Confirm it's an epic, not a board issue or a braindump.** If one sensible PR would
   close it, it belongs on the board — tell the user to use `create-issue` and stop. If
   it's a loose idea with no destination, tell them to drop it straight into Discussions
   and stop. Only proceed when it's an epic with a real end state.

2. **Dig before asking.** Investigation effort scales with the ambiguity actually
   present. Use `Read`/`Grep`/`Glob` to resolve anything the codebase can answer —
   current behaviour, file locations, whether parts already exist, what the realistic
   surface area is.

3. **Run a focused mini grill.** An RFC warrants more questions than a bug, because the
   slicing bot will run unattended against whatever you write. Via `AskUserQuestion`, ask
   the minimum needed to pin down two things the code cannot tell you:
   - **Scope** — what's in and what's explicitly out.
   - **Definition of done** — a concrete, checkable end state the bot can test against to
     know when to stop slicing.
   **Stop point:** once the goal and a testable stop-condition are clear enough that a
   single destination is unambiguous. Do **not** design the solution or enumerate the
   slices — that is the bot's job, not the RFC's.

4. **Verify the RFC category and discussions:write access.** Resolve the repository ID
   and the **RFC** discussion category ID:

   ```bash
   gh api graphql -f query='
     query {
       repository(owner:"johnpooch", name:"diplicity-react") {
         id
         discussionCategories(first:20) { nodes { id name } }
       }
     }'
   ```

   If there is no **RFC** category, **stop** and tell the user to create it in the GitHub
   UI first (a `.github/DISCUSSION_TEMPLATE/rfc.yml` form exists but is inert until the
   category does). This is a misconfiguration signal, not something to paper over by
   filing into the wrong category.

5. **Create the discussion — or fall back to pasteable markdown.** Post directly with the
   `createDiscussion` mutation, applying **no label** so it lands as "under discussion":

   ```bash
   gh api graphql -f query='
     mutation($repo:ID!, $cat:ID!, $title:String!, $body:String!) {
       createDiscussion(input:{
         repositoryId:$repo, categoryId:$cat, title:$title, body:$body
       }) { discussion { url } }
     }' -f repo="$REPO_ID" -f cat="$CATEGORY_ID" -f title="$TITLE" -f body="$BODY"
   ```

   If this fails because the token lacks `discussions:write` (or any write-scope error),
   do **not** keep retrying — print the full RFC markdown and the target category so the
   user can paste it into Discussions by hand.

6. **Report the link** (or the pasteable markdown if you fell back).

## Body structure

Use these sections, in order, and **no others**:

```
## Goal

<2–4 sentences: what we're building and why it matters.>

## Definition of done

<Concrete, checkable success criteria — the end state that means this RFC is fully
delivered. Describe the destination, not the steps. This is the stop condition the
slicing routine tests against.>

## Context

<Background, constraints, or sequencing notes. Omit the section entirely if there's
nothing meaningful to add.>
```

Rules:

- **Goal** — always present.
- **Definition of done** — always present, and concrete enough to be checkable. Vague
  aspirations ("make it better") are not a stop condition; push back until it's testable.
- **Context** — include only when it adds something. Sequencing constraints, if real, go
  here as prose.

## Never include

- A slice / task / phase breakdown or any implementation checklist — the bot derives
  slices dynamically.
- A status label, and **never** `human-approved` (the human sign-off gate).
- Guiding-principles, philosophy, or rationale-for-the-rules sections.
- Self-justifying prose: "Why this is high-leverage", "Why this matters", and similar.
- A link back to the Claude conversation that produced the RFC.

## Style

- **Title** — short and plain. No marketing adjectives, no em-dash taglines, no
  "Epic N:" or "RFC:" prefixes.
- **Emphasis** — use bold sparingly.
- Match the tight, un-padded register of the `create-issue` skill.
