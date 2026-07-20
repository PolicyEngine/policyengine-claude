---
name: encode-policy-v2
description: Use when the user invokes $encode-policy-v2 or asks Codex or Claude Code to implement a new PolicyEngine-US state benefit program or a new structural program component from official rules. Covers existing-program routing, source collection and full PDF rendering, user-approved scope, implementation, tests, validation, draft PR preparation, and independent review-fix rounds.
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
  [--resume] [--from-phase N] [--full-validation]
```

Mandatory gates that no surface may skip:

- Route purely parametric changes to `encode-reform` unless the user chooses to continue.
- Make no GitHub write before the user-approved scope decision exists.
- Render every page of every collected PDF; extracted text is not a substitute.
- Do not push through a red structural or quick-audit gate, or silently push failing tests.
- Keep the PR draft and complete the required follow-up review after any review-fix round.
- Do not finish before the Phase 7 summary and canonical completion contract are satisfied.

Surface adapters:

- **Claude Code**: also read
  [references/claude-launcher.md](references/claude-launcher.md), which maps canonical
  roles and abstract operations to Claude Code mechanics.
- **Codex**: use the delegation mapping below.

Codex delegation mapping, when subagent use is available and authorized:

- Use `worker` for every role that writes repository files, runtime artifacts, reports,
  GitHub state, or Git state. Use `explorer` only for bounded read-only discovery or audit
  questions whose result can be returned directly without writing an artifact.
- Preserve canonical dependencies. Run independent review-fixer-vars and
  review-fixer-tests roles concurrently; keep implementation, validation, and push roles
  in canonical order.
- Pass concrete `WORKTREE_ROOT`, `WORKTREE_ID`, `RUN_ROOT`, and `PREFIX` values, the role's
  full canonical task contract, owned paths, required outputs, and named PolicyEngine
  skills to every subagent. Do not assume child agents inherit parent skill context.
- Remind every implementation subagent that other agents may share the worktree, it must
  not revert unrelated edits, and only the canonical pusher roles may commit or push.
- If subagents are unavailable or not authorized, execute roles directly in phase order
  while preserving the same ownership, handoff files, user checkpoints, and gates.
