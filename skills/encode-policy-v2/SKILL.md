---
name: encode-policy-v2
description: Use when the user invokes $encode-policy-v2 or asks Codex to implement a new PolicyEngine-US state benefit program from official rules. Covers research, source collection, requirement extraction, scoped implementation, tests, validation, and draft PR preparation.
metadata:
  category: workflows
---

# encode-policy-v2

This is the Codex equivalent of the Claude `/encode-policy-v2` command.

Treat the text after `$encode-policy-v2` as the command arguments:

```text
$encode-policy-v2 STATE PROGRAM [--skip-review] [--research-only] [--600dpi]
  [--resume] [--from-phase N] [--full-validation]
```

Before starting, read [workflow.md](references/workflow.md) and [subagents.md](references/subagents.md). Follow them as the source of truth for phases, checkpoints, handoff files, validation gates, and Codex subagent delegation.

Operational rules:

- Derive the worktree-scoped `RUN_ROOT` exactly as specified in `workflow.md` before any
  handoff-file operation. Never use process-global `/tmp/{PREFIX}-...` paths.
- Use `{RUN_ROOT}/{PREFIX}-...` handoff files to keep large research, diffs, PDFs, and reports out of the main context.
- Ask the user before making scope decisions that affect modeled requirements.
- Use PolicyEngine skills explicitly when implementing: `$policyengine-us`, `$policyengine-parameter-patterns`, `$policyengine-variable-patterns`, `$policyengine-testing-patterns`, `$policyengine-code-style`, `$policyengine-code-organization`, and `$policyengine-vectorization`.
- This workflow is designed for Codex subagents. When subagent use is available and authorized, delegate independent phases to `worker` or `explorer` agents using [subagents.md](references/subagents.md); otherwise execute the same steps directly while preserving handoff-file boundaries.
- Every PDF reference href must include `#page=XX`, using the PDF file page number.
