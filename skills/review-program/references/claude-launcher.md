# Claude Code launcher: review-program

Read the canonical [workflow.md](workflow.md) first. This adapter maps its operations
to Claude Code; it adds no review stages or completion gates.

- **Arguments**: preserve positional arguments and flags, including `--sources` and
  `--source-budget`, according to the canonical grammar.
- **Entrypoint**: this workflow is registered as a skill, without a same-named command
  stub. Check that Skill returns this entrypoint and resolve `REVIEW_SKILL_ROOT` from its
  reported base directory. Pass that path to workers; never use a filesystem-wide search
  or recursive Skill invocation to recover a compatibility stub. If an older session
  registry returns the stub instead, read SKILL.md and the references from the
  `REVIEW_SKILL_ROOT` the caller passed (or the sibling `skills/review-program` of a
  successfully loaded skill's base directory) and record `stub-resolved` in the run state.
- **Questions**: use `AskUserQuestion` for missing/ambiguous PR identity or a posting
  decision. Honor decisions already provided; review can finish before asking to post.
- **Delegation**: launch the installed `review-worker` profile for the canonical `policy-reviewer`
  and `code-reviewer` in one parallel tool batch as soon as the snapshot exists, before writing the scope
  brief; send the brief's questions afterwards with `SendMessage`. Use the active
  `Agent`/delegation tool's actual schema; do not pass `run_in_background` or `team_name`
  unless it supports them. Write shared paths, scope, runtime, source budget and measured
  review start once in the run state. Use short role prompts pointing to that file and
  the canonical role/finding sections, with each role's output/progress paths and resolved
  skill names. Workers read those sections before work; do not transcribe the workflow
  into separate multi-page prompts. Resolve installed skill names by suffix, never by
  assuming the `complete:` namespace.
  This thin profile retains Skill access and excludes Agent/Task delegation tools. Use
  it for both initial and incremental reviewers. Do not substitute Explore or a generic
  agent with delegation access. If unavailable, report the missing installed profile;
  the coordinator may perform that role directly after its own required skill load.
  Never pass the Agent `name` parameter from a delegated context (for example when this
  coordinator was itself spawned by encode-policy-v2): named teammates cannot be nested,
  the call is rejected and each retry costs about a minute. Unnamed reviewers are
  identified by their progress-log path.
- **Test runs**: the code reviewer invokes the runner once through
  `run_bounded.py --seconds 540` with the Bash tool's `timeout` at its 600000-millisecond
  maximum, so the wrapper's deadline fires first and its exit-status line survives, and
  output redirected to its log; the default two-minute Bash limit kills a program suite
  mid-run and discards its status.
- **Model-development loading**: the country-model review coordinator and reviewers invoke the resolved installed
  skill with the `Skill` tool in their own context, then read the relevant references.
  Require canonical `SKILLS_READY` evidence before accepting their work. A worker without
  Skill access or the required installed skill returns `SKILLS_BLOCKED`; the skill list
  in its prompt is not proof of loading.
- **Decision ownership**: reviewers validate their findings; the coordinator consolidates
  their completed evidence directly. Only a named missing premise or material conflict
  triggers targeted adjudication. Do not add coordinator source checks or diagnostic
  reruns for every critical, or pass the result back for an encode-level verification.
- **Agent contracts**: `review-worker` supplies only tool restrictions and the canonical
  role reference. Do not substitute document-collector/program-reviewer/validator agents
  whose standalone routines add overlapping work. Reviewers do not create nested teams
  or delegate verification, including read-only dependency tracing.
  Do not require `TeamCreate`; use it only if available and required by that runtime.
- **Completion**: wait for background completion notifications. The only file the
  coordinator watches is each role's `{PREFIX}-review-progress-{role}.log`: check it when a
  sibling completes, or use `Monitor` with an until-loop on its modification time for a
  bounded wait. Silence over five minutes: `SendMessage` the role "finalize now with what
  you have"; two more minutes: `TaskStop` it and apply the canonical recovery. Never treat
  a partial report as finished. The coordinator reads the reports and writes both final
  outputs. Use completion notifications; do not implement waits with multi-minute shell
  sleeps. The liveness threshold is not the polling interval.
- **Adjudication**: send the specific material uncertainty allowed in Phase 5 to the
  original reviewer first. Use one additional reader only if that targeted resolution
  still needs independence; that reader also uses `review-worker`. No automatic verifier
  per finding, source, page or parameter.
- **Coordinator reads**: the diff, code, source evidence and findings are available
  to the coordinator for a named missing premise or material conflict. Completed,
  evidenced findings go directly to assembly without reopening each critical's evidence.
