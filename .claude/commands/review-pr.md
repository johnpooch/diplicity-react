---
description: Review the current PR — high-precision, concise inline comments posted to GitHub
argument-hint: [pr-number]
allowed-tools: Read, Grep, Glob, Bash(gh:*), Bash(git:*), Bash(python3:*)
---

Review this pull request like an expert human reviewer: **few comments, only real issues, high precision**. Explore the codebase before commenting. Do not guess when you can verify with Read, Grep, or Glob.

## Project guidance

Read these before reviewing:

- @CLAUDE.md — project conventions and agent instructions

## PR context

PR number: `$ARGUMENTS` (empty = current branch)

```
!`if [ -n "$ARGUMENTS" ]; then gh pr view "$ARGUMENTS" --json number,title,author,body,baseRefName,headRefName,headRefOid,url; else gh pr view --json number,title,author,body,baseRefName,headRefName,headRefOid,url; fi`
```

Changed files:

```
!`if [ -n "$ARGUMENTS" ]; then gh pr diff "$ARGUMENTS" --name-only; else gh pr diff --name-only; fi`
```

Diff:

```
!`if [ -n "$ARGUMENTS" ]; then gh pr diff "$ARGUMENTS"; else gh pr diff; fi`
```

Current branch:

```
!`git branch --show-current`
```

## How to work

1. **Understand intent** — What problem does the PR description say it solves?
2. **Explore the codebase** — For each non-trivial change, read surrounding code, trace call sites, check types/interfaces, serializers, permissions, migrations, and frontend consumers. Verify the change is complete (no dangling references).
3. **Verify correctness** — Trace execution paths. Look for edge cases, off-by-one errors, null/undefined hazards, stale React state, missing error handling, auth/permission gaps, and description–diff mismatches.
4. **Filter ruthlessly** — Only comment on issues you are confident a skilled reviewer would flag. Skip style nits, obvious reformatting, and speculative concerns you did not verify.

**Do NOT** use git log, git blame, GitHub review threads, or any information beyond what is in the PR description and diff above.

## Comment rules

- **Budget**: 0–3 comments typical. Hard cap: 5. Silence is better than noise.
- **Severity**:
  - `blocking` — bug, correctness issue, security/data risk, broken behavior, incomplete change
  - `suggestion` — meaningful improvement worth mentioning; not merge-blocking
- **Format**: 1–2 sentences per comment. State the issue and why it matters. Optional one-line fix. No preamble, no praise, no "nice work".
- **Line numbers**: Must point to a line visible in the PR diff (right side / new file). Use Grep/Read to confirm the line number.
- **Do not comment** on generated files, lockfiles, or pure formatting unless there is a real bug.

## Required output

First, write your private analysis inside `<systematic_review>` tags (exploration notes, call-site checks, edge cases considered). This section is not posted.

Then output structured results:

<comments>
[{"file": "path/to/file", "line": 42, "comment": "...", "severity": "blocking|suggestion"}]
</comments>

<rationale>
2–4 sentence review summary: what the PR does, whether it looks correct, and why you did or did not flag issues. If no comments, say so explicitly.
</rationale>

If you find no issues worth flagging: `<comments>[]</comments>`

## Post to GitHub

Save your output, then run this (fill in the heredoc with your actual `<comments>` and `<rationale>`):

```bash
cat > /tmp/pr-review-output.md << 'REVIEW_EOF'
<systematic_review>...</systematic_review>
<comments>[...]</comments>
<rationale>...</rationale>
REVIEW_EOF

python3 << 'POST_EOF'
import json, re, subprocess, sys

text = open("/tmp/pr-review-output.md").read()
pr_arg = "$ARGUMENTS".strip()

def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        print(r.stderr or r.stdout, file=sys.stderr)
        sys.exit(r.returncode)
    return r.stdout.strip()

def tag(name):
    m = re.search(rf"<{name}>\s*(.*?)\s*</{name}>", text, re.DOTALL)
    return m.group(1).strip() if m else ""

comments_raw = json.loads(tag("comments") or "[]")
rationale = tag("rationale")

pr_cmd = ["gh", "pr", "view"]
if pr_arg:
    pr_cmd.append(pr_arg)
pr = json.loads(run(pr_cmd + ["--json", "number,headRefOid"]))
repo = run(["gh", "repo", "view", "--json", "nameWithOwner", "-q", ".nameWithOwner"])
commit_id = pr["headRefOid"]
pr_number = pr["number"]

prefix = lambda s: "🛑 **blocking**" if s == "blocking" else "💡 **suggestion**"
gh_comments = [
    {"path": c["file"], "line": int(c["line"]), "body": f"{prefix(c.get('severity','suggestion'))}: {c['comment']}"}
    for c in comments_raw if c.get("file") and c.get("line") and c.get("comment")
]

blocking = sum(1 for c in comments_raw if c.get("severity") == "blocking")
summary = f"### PR Review\n\n{rationale}\n\n**{len(gh_comments)}** inline comment(s) ({blocking} blocking, {len(gh_comments)-blocking} suggestion)."

if not gh_comments:
    run(["gh", "pr", "review", str(pr_number), "--comment", "--body", summary])
    print(f"Posted summary on PR #{pr_number} (no inline comments)")
    sys.exit(0)

payload = {"commit_id": commit_id, "body": summary, "event": "COMMENT", "comments": gh_comments}
r = subprocess.run(
    ["gh", "api", f"repos/{repo}/pulls/{pr_number}/reviews", "--method", "POST", "--input", "-"],
    input=json.dumps(payload), capture_output=True, text=True,
)
if r.returncode == 0:
    print(f"Posted review on PR #{pr_number}: {len(gh_comments)} inline comment(s)")
    sys.exit(0)

print("Batch post failed, retrying individually...", file=sys.stderr)
posted, skipped = 0, []
for c in gh_comments:
    r = subprocess.run(
        ["gh", "api", f"repos/{repo}/pulls/{pr_number}/reviews", "--method", "POST", "--input", "-"],
        input=json.dumps({"commit_id": commit_id, "body": c["body"], "event": "COMMENT", "comments": [c]}),
        capture_output=True, text=True,
    )
    if r.returncode == 0:
        posted += 1
    else:
        skipped.append(f"{c['path']}:{c['line']}")

if skipped:
    note = summary + "\n\n**Skipped** (line not in diff):\n" + "\n".join(f"- `{s}`" for s in skipped)
    run(["gh", "pr", "review", str(pr_number), "--comment", "--body", note])
print(f"Done: {posted} posted, {len(skipped)} skipped")
POST_EOF
```

If `$ARGUMENTS` is empty, the heredoc still works — it uses the current branch's PR.
