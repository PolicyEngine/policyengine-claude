---
name: encode-policy-v2
description: Use when the user invokes $encode-policy-v2 or asks Codex or Claude Code to implement a new PolicyEngine-US state benefit program or a new structural program component from official rules. Covers existing-program routing, source collection and selective PDF inspection, user-approved scope, implementation, tests, validation, draft PR preparation, and independent review-fix rounds.
metadata:
  category: workflows
---

# encode-policy-v2

Thin launcher. The canonical workflow—routing, arguments, phases, roles, checkpoints,
artifact contracts, retry budgets, and completion gates—lives in
[references/workflow.md](references/workflow.md). Read it completely before acting and
follow it exactly; do not redefine or compress its behavior here.

Treat the text after `$encode-policy-v2` as raw workflow arguments:

```text
$encode-policy-v2 STATE PROGRAM [--skip-review] [--research-only] [--600dpi]
  [--resume] [--from-phase N] [--full-validation] [--local]
  [--sources MANIFEST] [--source-budget MINUTES]
```

Mandatory gates that no surface may skip:

- Load model-development in each model worker's own context and verify its load evidence
  under the canonical loading contract before accepting work; missing skills block it.
- Route purely parametric changes to `encode-reform` unless the user chooses to continue.
- Make no GitHub write before the user-approved scope decision exists.
- Read all relevant rules and visually inspect tables, scans or ambiguous PDF evidence;
  share validated originals and extracts with the independent review.
- Do not push through a red structural or quick-audit gate, or silently push failing tests.
- Workers never delegate; brief both owners from one shared contract block, and treat the
  coordinator's single bounded test invocation as the run of record.
- In local mode, make no GitHub writes or pushes; preserve the implementation worktree.
- Keep new PRs draft and complete follow-up review after any review-fix round.
- Maximum two reviews: a second, incremental review follows repairs to confirmed
  criticals from the first. Stop after round 2 with any remaining blockers reported.
- Do not finish before the Phase 7 summary and canonical completion contract are satisfied.

Surface adapters:

- **Claude Code**: also read
  [references/claude-launcher.md](references/claude-launcher.md), which maps canonical
  roles and abstract operations to Claude Code mechanics.
- **Codex**: use the delegation mapping below.

Codex delegation mapping, when subagent use is available and authorized:

- The coordinator handles research, requirements, coverage/validation, Git and reporting;
  it may read code and full evidence directly. No summary-only read restriction.
- Use persistent workers for the two substantive roles: implementer (parameters and
  variables together) and test-author. Pass exact owned paths, concrete worktree/run
  values, approved scope, artifact contracts and the needed skill references.
- Each Codex worker resolves `policyengine-model-development` from its own available
  skills catalog and reads that entrypoint using its catalog-specified access mechanism,
  then its task references. Include the canonical loading contract in the prompt; a
  repository path alone does not demonstrate runtime skill availability. Do not assume
  the parent session's skill load supplies the worker's context.
- Test-source analysis can overlap implementation; final tests use the published variable
  contract. Reuse owners for repairs. Workers never stage, commit, push or independently
  sync/format the shared environment. They do their own work without helper or nested
  agents, run at most one bounded self-check of their owned tests, and report a
  `CONTRACT MISMATCH` instead of relocating cases; the coordinator runs the tests of record.
- Run review-program in a fresh review coordinator context with its canonical local or
  published arguments, raw source manifest, captured head and scope. Require that
  coordinator's own model-development load. Leave capacity for its reviewers and consume
  its completed decision directly for repair routing, without a second review by the encoder.
- Use only supported runtime capabilities. When delegation is unavailable, perform the
  implementation roles directly while preserving independent review context and gates.
