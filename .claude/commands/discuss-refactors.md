---
description: "TEMPORARY — Discuss REFACTOR comments in a folder; propose plan + guidance updates (do not implement)"
argument-hint: <folder-path>
allowed-tools: Read, Grep, Glob, Bash(rg:*), Bash(find:*), Bash(ls:*)
---

# Discuss REFACTOR comments (temporary walkthrough command)

Interactive only. **Do not implement refactors. Do not edit application code.** After agreement, you may update guidance files and/or the ledger — never before the user agrees.

Folder: `$ARGUMENTS`

If `$ARGUMENTS` is empty, stop and ask for a folder path (e.g. `service/bot_profile` or `packages/web/src/components`).

## Collect comments

Run this (adapt the path if `$ARGUMENTS` is relative to the repo root):

```
!`rg -n -g '!**/migrations/**' -e 'REFACTOR|TODO.*refactor|FIXME.*refactor' -i -- "$ARGUMENTS" 2>/dev/null || true`
```

Also list files in the folder so you know what has no comments yet:

```
!`find "$ARGUMENTS" -type f \( -name '*.py' -o -name '*.ts' -o -name '*.tsx' -o -name '*.js' -o -name '*.jsx' -o -name '*.md' \) ! -path '*/migrations/*' ! -path '*/node_modules/*' ! -path '*/.venv/*' 2>/dev/null | sort`
```

If rg finds nothing, say so and stop — do not invent refactors.

Read every file that contains a match so you have full comment context (multi-line `REFACTOR` blocks). For each theme, skim enough surrounding call sites (imports, sibling apps, frontend consumers) to ground the discussion in evidence — cite file paths.

## Read current guidance before proposing changes

Read:

- @CLAUDE.md
- Relevant files under `.claude/rules/` (especially `.claude/rules/backend/` for `service/**`, `.claude/rules/frontend.md` for `packages/web/**`)
- @docs/codebase-walkthrough-ledger.md if it exists

## Discussion format

Talk to the user. Structure the first reply like this:

### 1. Themes
Group the `REFACTOR` comments into a small number of themes (not one bullet per comment). For each theme:
- What the comments ask for (paraphrase)
- Evidence from the codebase (current shape, duplication, call sites)
- Concrete refactor that would follow
- Open questions / design forks

### 2. Guidance impact
For each theme, say whether lasting guidance is needed:
- **No guidance** — one-off cleanup; once done, a rule would be stale (e.g. delete a dead helper).
- **Update existing rule** — cite the file/section that should change and draft the new wording.
- **New rule** — say which file under `.claude/rules/` (or `CLAUDE.md` if truly every-session) and draft concise wording.

Remember: path-scoped rules for part-of-codebase guidance; keep `CLAUDE.md` under 200 lines.

### 3. Clarifying questions
Ask only what blocks agreement. Prefer concrete forks (one endpoint vs two, which app owns X).

**Stop and wait for the user.** Do not write files yet.

## After the user replies

Iterate until themes and guidance wording are agreed.

Then, only when the user confirms:

1. **Guidance** — update `CLAUDE.md` and/or `.claude/rules/**` with the agreed lasting preferences (not the one-off cleanup).
2. **Ledger** — append/update work items in `docs/codebase-walkthrough-ledger.md` (refactor intents + status only — no preference essays). Create the file if missing; keep the header note that guidance does not live in the ledger.

Still do **not** implement the refactor unless the user explicitly asks in a later turn.

## Tone

Direct and concise. Evidence over assertion. Do not agree with a comment without checking the code. Do not expand scope beyond what the comments imply without flagging it.
