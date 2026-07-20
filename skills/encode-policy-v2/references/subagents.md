# Codex Subagent Plan: encode-policy-v2

Use this plan when Codex subagent use is available and authorized.

Codex does not have Claude's named agent types. Simulate each Claude role by spawning a `worker` for implementation or write-heavy tasks and an `explorer` for read-only codebase questions. Tell every worker that it is not alone in the codebase, must not revert others' edits, and must respect the file ownership listed below.

Subagents can use PolicyEngine skills, but the orchestrator should name them explicitly in each subagent prompt. Do not assume a worker will infer the right skills from the parent context.

## Role Mapping

| Claude role | Codex role | Responsibility | Output |
|---|---|---|---|
| issue-manager | worker | Find/create issue, branch, draft PR | PR/issue identifiers |
| document-collector | worker | Find official sources, extract text, render every PDF page | `sources/working_references.md`, `{RUN_ROOT}/{PREFIX}-research-summary.md` |
| consolidator | worker | Extract requirements and write specs | `{RUN_ROOT}/{PREFIX}-impl-spec.md`, checklist, scope summary |
| rules-engineer parameters | worker | Create parameter YAML only | parameter files |
| rules-engineer variables | worker | Create variables and the implementation contract | variable files, implementation manifest |
| test-creator | worker | Create unit, integration, and edge-case tests | test files, test manifest |
| requirements-tracker | worker | Verify requirement coverage | `{RUN_ROOT}/{PREFIX}-coverage-report.md` |
| implementation-validator | worker | Structural validation and mechanical fixes | `{RUN_ROOT}/{PREFIX}-validator-report.md` |
| ci-fixer | worker | Run focused tests and fix failures | `{RUN_ROOT}/{PREFIX}-ci-fixer-status.md` |
| quick-auditor | explorer or worker | Audit final diff | `{RUN_ROOT}/{PREFIX}-checkpoint.md` |
| pr-pusher | worker | Changelog, format, commit, push | commit/push |
| reporter | worker | PR body and final report | `{RUN_ROOT}/{PREFIX}-pr-description.md`, final report |
| review-fixer-vars | worker | Fix critical parameter and variable review findings | `{RUN_ROOT}/{PREFIX}-checklist-vars-r{N}.md` |
| review-fixer-tests | worker | Fix critical test review findings | `{RUN_ROOT}/{PREFIX}-checklist-tests-r{N}.md` |

## Skills to Pass to Workers

Include these lines in subagent prompts as relevant:

- Parameter worker: "Use `$policyengine-parameter-patterns`, `$policyengine-variable-patterns`, and `$policyengine-code-organization`."
- Variable worker: "Use `$policyengine-variable-patterns`, `$policyengine-parameter-patterns`, `$policyengine-vectorization`, `$policyengine-aggregation`, `$policyengine-period-patterns`, `$policyengine-code-style`, and `$policyengine-code-organization`."
- Test worker: "Use `$policyengine-testing-patterns`, `$policyengine-period-patterns`, `$policyengine-aggregation`, `$policyengine-variable-patterns`, and `$policyengine-code-organization`."
- Edge-case worker: "Use `$policyengine-testing-patterns`, `$policyengine-period-patterns`, and `$policyengine-variable-patterns`."
- Validator worker: "Use `$policyengine-parameter-patterns`, `$policyengine-variable-patterns`, `$policyengine-code-organization`, `$policyengine-code-style`, `$policyengine-aggregation`, and `$policyengine-period-patterns`."
- CI worker: "Use `$policyengine-testing-patterns`, `$policyengine-variable-patterns`, `$policyengine-parameter-patterns`, `$policyengine-period-patterns`, `$policyengine-code-style`, `$policyengine-aggregation`, `$policyengine-vectorization`, and `$policyengine-code-organization`."
- Review-fixer vars worker: "Use `$policyengine-variable-patterns`, `$policyengine-code-style`, `$policyengine-parameter-patterns`, `$policyengine-period-patterns`, and `$policyengine-vectorization`."
- Review-fixer tests worker: "Use `$policyengine-testing-patterns`, `$policyengine-period-patterns`, and `$policyengine-variable-patterns`."

## Delegation Pattern

1. Do the immediate blocking setup locally: parse arguments and derive the worktree-safe
   `RUN_ROOT`, `WORKTREE_ID`, and `PREFIX`. Clean only this command's artifacts inside
   `RUN_ROOT`; preserve matching artifacts for resume.
2. Spawn the document collector. Keep research read-only.
3. If document collection fails, stop.
4. Spawn consolidator as a worker. Read only its short checklist and scope summary locally.
5. Ask user scope questions locally.
6. After scope approval, spawn issue-manager unless this is `--research-only`, then spawn
   implementation workers by dependency:
   - parameters worker first
   - variables worker and implementation manifest after parameters
   - one test worker after the variable manifest
7. Spawn requirements tracker. If gaps remain, spawn one gap-fixer worker and rerun tracker.
8. Spawn validator and CI workers in sequence, with specialist fixers only for escalations.
9. Spawn reporter and pusher only after validation and audit gates pass.
10. In review-fix rounds, spawn vars and tests fixers in parallel but make them write separate checklist files. Merge those files locally after both finish.

## Ownership

- Parameter worker owns `policyengine_us/parameters/gov/states/{ST}/...`.
- Variable worker owns `policyengine_us/variables/gov/states/{ST}/...`.
- Test workers own `policyengine_us/tests/policy/baseline/gov/states/{ST}/...`.
- Reporter owns `{RUN_ROOT}/{PREFIX}-pr-description.md` and `{RUN_ROOT}/{PREFIX}-final-report.md`.
- Pusher owns changelog creation, format, commit, and push.

Workers must not edit outside their ownership without stating why and coordinating through the main agent.
Pass the concrete `RUN_ROOT`, `WORKTREE_ID`, and `PREFIX` to every worker. No worker may
read or write process-global `/tmp/{PREFIX}-...` paths.
