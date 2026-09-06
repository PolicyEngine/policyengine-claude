# Claude Code launcher: encode-policy-v2

Read the canonical [workflow.md](workflow.md). This adapter maps capabilities without
adding stages, audits, test commands or approval prompts.

- Parse raw arguments, including local-only mode and source reuse/budget, as specified.
- The workflow is registered only as a skill, without a same-named command stub. Resolve
  its installed base directory from the Skill result. Pass the installed review-program
  directory and canonical paths to the fresh review coordinator; do not search the
  filesystem or recursively invoke a compatibility stub. If the Skill result is an old
  compatibility stub (a session registry that predates the stub removal), do not invoke
  it again: take the plugin root from a sibling skill's reported base directory (for
  example model-development's), read `skills/encode-policy-v2/SKILL.md` and its
  references from there, and record `stub-resolved` in the run state.
- Use the runtime's user-question tool for unresolved material scope/reuse/repair
  decisions. Batch related questions within its actual capacity; honor prior decisions.
- The coordinator performs research, requirements, coverage/validation, Git and reporting.
  It may inspect code and evidence directly. Do not delegate those routine steps merely
  to preserve a summary-only context rule.
- For the substantive `implementer` and `test-author`, launch the installed `model-worker`
  profile (Skill access, no delegation or web tools) with the full canonical role, exact
  owned paths, artifact contracts, relevant skill sections, concrete `WORKTREE_ROOT`,
  `WORKTREE_ID`, `RUN_ROOT`, `PREFIX` and local/publication mode. If that profile is not
  installed, or cannot be spawned as a retained named worker in this runtime, use
  `general-purpose` with an explicit no-delegation instruction and record the
  substitution. A specialized standalone agent is not required and must not add its
  own audits, dependency sync, formatting, test suites, commits or pushes to this role
  contract. Give both workers the same shared contract block; do not paraphrase it per
  worker.
- Retain the same workers for repairs. Start test-source analysis while implementation
  runs when independent; finalize tests only against the actual variable contract. Use
  runtime-supported messaging, or coordinator handoffs when unavailable. Never assume
  team, background, monitor or message parameters exist.
- Every model worker must have access to the `Skill` tool and invoke the installed
  `policyengine-model-development` skill by its resolved name before work, then read its
  role references. Include the canonical loading contract in dispatch and require the
  successful Skill result in `SKILLS_READY`; a `Load skills:` list alone does not load
  anything. If the selected agent lacks Skill access or the skill is unavailable, apply
  `SKILLS_BLOCKED` instead of silently using a general-purpose agent without it.
- Wait for completion notifications with the canonical progress/recovery bounds. Watch
  each worker's `{PREFIX}-encode-progress-{role}.log`; routine progress can also arrive
  by message or artifact; a partial report is not DONE. If delegation is unavailable,
  perform the roles directly, retaining independent review context.
- Run the test runner through `run_bounded.py --seconds 540` with the Bash tool's
  `timeout` at its 600000-millisecond maximum, so the wrapper's deadline fires first and
  its exit-status line survives; redirect output to the log. The default two-minute Bash
  limit kills a program suite mid-run and discards its status. Pass the same instruction
  to workers for their single self-check.
- Invoke review-program in a fresh `general-purpose` coordinator with its exact local or
  published arguments, approved scope, captured head, source manifest and runtime
  constraints. Require that coordinator to load both review-program and model-development
  before substantive model work. The canonical review workflow supplies its reviewer
  tasks; do not append a bespoke audit checklist. Leave sufficient capacity for its two
  reviewers. Consume its completed decision directly for repair routing, without another
  encoder verification pass. Time dispatch through acceptance of the returned result.
  Tell it that nested dispatches must omit the Agent `name` parameter: a delegated
  context cannot create named teammates, the call is rejected, and each retry costs
  about a minute. Nested reviewers are therefore unnamed; their role identity comes from
  the progress-log path they are given.
- Only the encoding coordinator stages, commits, pushes and writes GitHub state. In
  `--local`, it may make local implementation/review-fix commits but never creates an
  issue/PR, pushes or posts comments. Otherwise use explicit verified targets and the
  canonical pre-edit head check; don't map Git work to a standalone pusher routine.
- Resolve skill names by the installed suffix, not an assumed plugin namespace. Load
  only the references needed for the assigned task.
