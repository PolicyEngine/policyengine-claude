# Claude Code launcher: encode-policy-v2

Read this file only when executing encode-policy-v2 in Claude Code. Read the canonical
[workflow.md](workflow.md) first. This adapter maps its semantic roles and operations to
Claude Code mechanics and adds no workflow behavior.

## Mechanics

- **Raw arguments** → parse the text passed to the skill exactly as the canonical grammar
  specifies.
- **Ask the user** → use `AskUserQuestion` for a missing argument, the existing-program
  route, unreachable references, every scope choice, blocked CI, and the optional final
  review-fix round. Batch related decisions into as few calls as possible: one
  `AskUserQuestion` call carries up to 4 questions, so N simultaneous decisions take
  ceil(N/4) calls — never one call per decision. In Phase 2A, gather the overall-scope
  question and every program-specific decision first, then ask them together; reserve a
  later call only for a question that depends on a prior answer. Keep the canonical
  option order within each question.
- **Issue/PR discovery** → run `issue-manager` once with `MODE=discover` (read-only; it
  stops after searching). On `DECISION_NEEDED`, ask the issue and PR choices together in
  one `AskUserQuestion` call (two questions); on `NO_CANDIDATES`, use create-new for both. Then invoke a new `issue-manager`
  with `MODE=execute`, both explicit decisions, and the canonical repository values
  (`BASE_REPO`, `BASE_REPO_URL`, `PUSH_REPO`, `PUSH_REPO_URL`). Continue only on
  `SETUP_COMPLETE`; treat `BLOCKED` or a partial result as a blocking gate.
- **Run identity** → after deriving `WORKTREE_ID` and `PREFIX`, create
  `TeamCreate({WORKTREE_ID}-{PREFIX}-encode)` and pass
  `team_name: "{WORKTREE_ID}-{PREFIX}-encode"` to each delegated agent.
- **Delegate role X** → spawn the agent resolved from the table below. Its prompt contains
  the complete role contract from the canonical workflow, concrete run/worktree values,
  exact owned paths and inputs/outputs, relevant `Load skills:` entries, the PDF page rule
  when parameters are touched, and the canonical DONE line. Do not recreate the phase
  prose in this adapter.
- **Namespacing** → plugin agents and skills use the installed plugin's namespace. Resolve
  the unprefixed names below against the session's available agents/skills by suffix;
  never assume `complete:` or another fixed prefix. If a specialized agent is unavailable,
  use `general-purpose` with the full role and skill contract in its prompt.
- **Concurrency** → use `run_in_background: true` only for independent work: initial
  document collection may run in the background, and each review round spawns the vars
  and tests fixers together in one message. Wait for the whole batch; never poll. All
  dependency-ordered implementation, validation, CI, and Git roles run sequentially.
- **Nested review** → invoke the installed `review-program` skill through the Skill tool
  with the exact canonical arguments; that skill owns all review mechanics.
- **Coordinator context** → read only artifacts the canonical Handoff table marks
  `Coordinator may read? Yes`. Never read full research/spec/PDF/code/review files or
  implement/fix code.

## Role → agent type

Agent names are unprefixed; resolve them using the namespacing rule above.

| Canonical role | Agent |
|---|---|
| document-collector | `document-collector` |
| user-document-processor | `general-purpose` |
| requirements-consolidator | `general-purpose` |
| issue-manager | `issue-manager` |
| parameter-implementer | `rules-engineer` |
| variable-implementer | `rules-engineer` |
| test-creator | `test-creator` |
| requirements-tracker | `general-purpose` |
| gap-fixer | `rules-engineer` |
| implementation-validator | `implementation-validator` |
| validator-escalation-fixer | `rules-engineer` |
| ci-fixer | `ci-fixer` |
| quick-auditor | `general-purpose` |
| audit-fixer | `rules-engineer` or `test-creator`, by owned file |
| initial-pusher | `pr-pusher` |
| reporter | `general-purpose` |
| review-fixer-vars | `rules-engineer` |
| review-fixer-tests | `test-creator` |
| review-ci-fixer | `ci-fixer` |
| review-round-pusher | `pr-pusher` |
