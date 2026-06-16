# [Routine] Triage and prioritize open issues against an agreed rubric

## Goal

On a schedule, sweep open issues and assign each a discrete priority label
(`priority:P0`–`P3`) by scoring it against a committed, version-controlled
rubric — keeping the whole board consistently triaged without ever imposing a
brittle total ordering.

## Context

The board has no priority signal today, so "what to work on next" is re-derived
by hand every time. This routine is a *third class* alongside the epic's fix
routines (open a PR) and proposal routines (open an issue): it **annotates**
existing work rather than creating new work. Buckets, not a ranking — per-issue
and idempotent, so a re-run only changes a label when the inputs materially
change, avoiding the O(n²) churn of ordering the board. The rubric lives in
`.claude/routines/priority-rubric.md` so priority decisions are auditable,
tunable over time, and explainable — in the spirit of #715 feeding lessons back
into the tooling.

## Approach

1. **Maintain the rubric as a committed artifact**
   (`.claude/routines/priority-rubric.md`): define the four buckets and the
   weighted factors — **reach** (players affected) × **severity/impact** ÷
   **effort**, adjusted by **strategic fit** and **whether it blocks/unblocks
   other work**, with **staleness** as a tiebreak. The rubric file is the source
   of truth; the routine reads it at the start of every run.
2. **Select the working set** (sweep): every open issue with no `priority:*`
   label, plus any already-labeled issue whose inputs changed materially since
   it was last scored. Skip the epic/tracking issues themselves.
3. **Respect manual overrides** — if the most recent priority-label change on an
   issue was made by a human (not this routine), treat it as authoritative and
   do not re-flip it. (Lock signal TBD with #712's label scheme, e.g. a
   `priority:locked` marker or last-actor check.)
4. **Score and apply** — for each issue in the set, compute the bucket from the
   rubric, set the `priority:Px` label, and record a one-line rationale citing
   the factors that drove it (e.g. "P1: high reach, low effort, blocks #730").
5. **Converge, don't churn** — only write a label when it differs from the
   current one; never re-litigate an unchanged decision. A per-run summary of
   what changed is enough; no per-issue comment spam.

## Dependencies / notes

- Builds on #712 (needs the `agentic-routine` + `priority:*` / `routine:triage`
  labels created via the API/web UI first, plus the manual-override convention).
- Unlike the fix routines this sweeps the board rather than picking one item,
  because labeling is cheap and the goal is *consistent coverage* — but it stays
  idempotent via the converge rule in step 5.

## Open questions

- Whether to include a `P0` bucket at all, or just P1–P3.
- The exact override-lock mechanism — likely belongs in #712's label-scheme
  decision rather than here.
