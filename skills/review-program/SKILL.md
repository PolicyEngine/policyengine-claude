---
name: review-program
description: ALWAYS LOAD THIS SKILL for PolicyEngine PR reviews, including when the user invokes $review-program or Codex /review on a PolicyEngine PR. Performs read-only code validation, source-reference checks, regulatory review, optional PDF audit, summary reporting, and optional GitHub comment posting.
metadata:
  category: workflows
---

# review-program

Thin launcher. The canonical workflow — phases, roles, gates, severity rules, artifact
contracts — lives in [references/workflow.md](references/workflow.md). Read it completely
before acting and follow it exactly; this file only adapts it to this surface. Do not
redefine flags, phases, severity rules, file ownership, or completion gates here.

Use this skill for PolicyEngine-specific PR reviews even when the user starts from a
generic built-in review command (such as Codex `/review`): the canonical workflow adds
PolicyEngine source, reference, regulatory, PDF, and test-review rules a generic review
lacks.

Treat the text after `$review-program` or `/review` as the raw workflow arguments:

```text
$review-program [PR_NUMBER_OR_SEARCH] [PDF_URL] [--local] [--local-diff] [--full]
  [--skip-pdf] [--600dpi] [--resume] [--incremental REPORT] [--prefix NAME]
```

Mandatory completion gate:

- Do not stop after individual validators or PDF audits.
- The review is incomplete until `{RUN_ROOT}/{PREFIX}-review-full-report.md` and
  `{RUN_ROOT}/{PREFIX}-review-summary.md` both exist.
- Phase 6 consolidation is required before displaying or posting findings.

Surface adapters:

- **Claude Code**: also read
  [references/claude-launcher.md](references/claude-launcher.md) — it maps canonical
  roles to this plugin's agent types and the workflow's abstract operations to Claude
  Code mechanics.
- **Codex**: use the delegation mapping below.

Delegation mapping (when subagent use is available and authorized):

- Map every role in the canonical Roles table to a `worker` when it writes report or
  artifact files, or an `explorer` for read-only codebase questions.
- Pass concrete `RUN_ROOT`, `WORKTREE_ID`, and `PREFIX` values and the role's task spec
  from the canonical workflow to every subagent; name the role's skills explicitly in the
  subagent prompt — do not assume a worker infers them from parent context.
- Every subagent finishes by writing its assigned file and returning the one-line DONE
  message from the canonical completion contract.
- If subagents are unavailable or not authorized, execute the roles directly in phase
  order, preserving the same handoff files and read-only contract.
