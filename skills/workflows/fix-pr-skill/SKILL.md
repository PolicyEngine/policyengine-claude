---
name: fix-pr
description: Use when the user invokes $fix-pr or asks Codex to apply fixes to a PolicyEngine PR based on $review-program findings, GitHub review comments, CI failures, or local review reports.
---

# fix-pr

This is the Codex equivalent of the Claude `/fix-pr` command.

Treat the text after `$fix-pr` as the command arguments:

```text
$fix-pr [PR_NUMBER_OR_SEARCH] [--local]
```

Before starting, read [workflow.md](references/workflow.md) and [subagents.md](references/subagents.md). Follow them as the source of truth for phases, checkpoints, handoff files, verification, and Codex subagent delegation.

Operational rules:

- Determine the PR first, then ask whether to push and post unless `--local` is set.
- Do not read full review reports into the main context until the final display step. Use short handoff files.
- Write a fix plan before editing.
- Apply only fixes listed in the fix plan.
- Use PolicyEngine skills explicitly for fixes: `$policyengine-parameter-patterns`, `$policyengine-variable-patterns`, `$policyengine-testing-patterns`, `$policyengine-code-style`, `$policyengine-code-organization`, and `$policyengine-period-patterns`.
- This workflow is designed for Codex subagents. When subagent use is available and authorized, delegate issue gathering, scoped fixes, CI, verification, and comment writing using [subagents.md](references/subagents.md); otherwise execute the fix workflow directly with the same handoff-file boundaries.
