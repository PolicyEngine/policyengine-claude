---
name: fix-pr
description: Use when the user invokes $fix-pr or asks Codex or Claude Code to apply fixes to a PolicyEngine PR based on $review-program findings, GitHub review comments, CI failures, or local review reports.
metadata:
  category: workflows
---

# fix-pr

Thin launcher. The canonical workflow — phases, roles, consent gates, verification
gates, artifact contracts — lives in [references/workflow.md](references/workflow.md).
Read it completely before acting and follow it exactly; this file only adapts it to this
surface. Do not redefine flags, phases, ownership, or gates here.

Treat the text after `$fix-pr` as the raw workflow arguments:

```text
$fix-pr [PR_NUMBER_OR_SEARCH] [--local] [--resume] [--full-validation]
```

Hard rules restated from the canonical workflow (they cannot be skipped on any surface):

- Determine the PR first, then ask about push/post mode unless `--local` is set.
- No edit before the user-approved fix plan file exists; fix only what it lists.
- Never push while a verification gate is red.
- Never read full review reports into the main context; use the short handoff files.

Surface adapters:

- **Claude Code**: also read
  [references/claude-launcher.md](references/claude-launcher.md) — it maps canonical
  roles to this plugin's agent types and the workflow's abstract operations to Claude
  Code mechanics.
- **Codex**: use the delegation mapping below.

Delegation mapping (when subagent use is available and authorized):

- Map every role in the canonical Roles table to a `worker` when it edits files or
  writes reports, or an `explorer` for read-only codebase questions.
- Pass concrete `RUN_ROOT`, `WORKTREE_ID`, and `PREFIX` values and the role's task spec
  from the canonical workflow to every subagent; name the role's skills explicitly in
  the subagent prompt.
- Respect the canonical ownership table — no worker edits outside its assigned files;
  only the fix-pusher role commits or pushes.
- If subagents are unavailable or not authorized, execute the roles directly in phase
  order, preserving the same handoff files and gates.
