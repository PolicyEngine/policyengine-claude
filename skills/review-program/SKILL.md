---
name: review-program
description: ALWAYS LOAD THIS SKILL for PolicyEngine PR reviews, including when the user invokes $review-program or Codex /review on a PolicyEngine PR. Performs read-only code validation, source-reference checks, regulatory review, optional PDF audit, summary reporting, and optional GitHub comment posting.
metadata:
  category: workflows
---

# review-program

This is the Codex equivalent of the Claude `/review-program` command.

Use this skill for PolicyEngine-specific PR reviews even when the user starts from Codex's built-in `/review`. The built-in review flow is generic; this skill adds PolicyEngine source, reference, regulatory, PDF, and test-review rules.

Treat the text after `$review-program` or `/review` as the command arguments when available:

```text
$review-program [PR_NUMBER_OR_SEARCH] [PDF_URL] [--local] [--local-diff] [--full]
  [--skip-pdf] [--600dpi] [--resume] [--incremental REPORT]
/review [PR_NUMBER_OR_SEARCH] [PDF_URL] [--local] [--local-diff] [--full]
  [--skip-pdf] [--600dpi] [--resume] [--incremental REPORT]
```

Before starting, read [workflow.md](references/workflow.md) and [subagents.md](references/subagents.md). Follow them as the source of truth for phases, handoff files, severity rules, and Codex subagent delegation.

Mandatory completion gate:

- Do not stop after individual validators or PDF audits.
- The review is incomplete until `{RUN_ROOT}/{PREFIX}-review-full-report.md` and `{RUN_ROOT}/{PREFIX}-review-summary.md` both exist.
- Phase 6 consolidation is required before displaying or posting findings.

Operational rules:

- Resolve the target PR first. If no PR number or search text was supplied, ask the user
  for a PR number or title. Do not ask which program to review; infer program context from
  the selected PR's diff.
- Read-only mode: do not edit source files or change the user's branch.
- Derive the worktree-scoped `RUN_ROOT` exactly as specified in `workflow.md`. Never use
  process-global `/tmp/{PREFIX}-...` paths.
- Save large diffs, PDF text, screenshots, and detailed findings to `{RUN_ROOT}/{PREFIX}-review-...` files.
- During analysis, read only short summary files in the main context.
- Use PolicyEngine skills explicitly for validation: `$policyengine-parameter-patterns`, `$policyengine-variable-patterns`, `$policyengine-testing-patterns`, `$policyengine-code-style`, `$policyengine-code-organization`, `$policyengine-aggregation`, and `$policyengine-period-patterns`.
- This workflow is designed for Codex subagents. When subagent use is available and authorized, delegate independent validators to `worker` or `explorer` agents using [subagents.md](references/subagents.md); otherwise run the validators directly with the same file handoff contract.
