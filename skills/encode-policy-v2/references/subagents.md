# Codex Subagent Plan: encode-policy-v2

Use this plan when Codex subagent use is available and authorized.

Codex does not have Claude's named agent types. Simulate each Claude role by spawning a `worker` for implementation or write-heavy tasks and an `explorer` for read-only codebase questions. Tell every worker that it is not alone in the codebase, must not revert others' edits, and must respect the file ownership listed below.

Subagents can use PolicyEngine skills, but the orchestrator should name them explicitly in each subagent prompt. Do not assume a worker will infer the right skills from the parent context.

## Role Mapping

| Claude role | Codex role | Responsibility | Output |
|---|---|---|---|
| issue-manager | worker | Find/create issue, branch, draft PR | PR/issue identifiers |
| document-collector | worker | Find official sources, download/extract/render PDFs | `sources/working_references.md`, `/tmp/{PREFIX}-research-summary.md` |
| consolidator | worker | Extract requirements and write specs | `/tmp/{PREFIX}-impl-spec.md`, checklist, scope summary |
| rules-engineer parameters | worker | Create parameter YAML only | parameter files |
| rules-engineer variables | worker | Create variable Python files only | variable files |
| test-creator | worker | Create baseline YAML tests only | test files |
| edge-case-generator | worker | Append edge cases to existing tests | test files |
| requirements-tracker | worker | Verify requirement coverage | `/tmp/{PREFIX}-coverage-report.md` |
| implementation-validator | worker | Structural validation and mechanical fixes | `/tmp/{PREFIX}-validator-report.md` |
| ci-fixer | worker | Run focused tests and fix failures | `/tmp/{PREFIX}-ci-fixer-status.md` |
| quick-auditor | explorer or worker | Audit final diff | `/tmp/{PREFIX}-checkpoint.md` |
| pr-pusher | worker | Changelog, format, commit, push | commit/push |
| reporter | worker | PR body and final report | `/tmp/{PREFIX}-pr-description.md`, final report |
| review-fixer-vars | worker | Fix critical parameter and variable review findings | `/tmp/{PREFIX}-checklist-vars-r{N}.md` |
| review-fixer-tests | worker | Fix critical test review findings | `/tmp/{PREFIX}-checklist-tests-r{N}.md` |

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

1. Do the immediate blocking setup locally: parse arguments, derive `PREFIX`, and clean stale `/tmp/{PREFIX}-*.md` files.
2. Spawn independent setup workers in parallel:
   - issue-manager
   - document-collector
3. Wait for both before scope extraction. If document collection fails, stop.
4. Spawn consolidator as a worker. Read only its short checklist and scope summary locally.
5. Ask user scope questions locally.
6. Spawn implementation workers by dependency:
   - parameters worker first
   - variables worker and tests worker in parallel after parameters
   - edge-case worker after variables/tests
7. Spawn requirements tracker. If gaps remain, spawn one gap-fixer worker and rerun tracker.
8. Spawn validator and CI workers in sequence, with specialist fixers only for escalations.
9. Spawn reporter and pusher only after validation passes or the user explicitly accepts a non-passing state.
10. In review-fix rounds, spawn vars and tests fixers in parallel but make them write separate checklist files. Merge those files locally after both finish.

## Ownership

- Parameter worker owns `policyengine_us/parameters/gov/states/{ST}/...`.
- Variable worker owns `policyengine_us/variables/gov/states/{ST}/...`.
- Test workers own `policyengine_us/tests/policy/baseline/gov/states/{ST}/...`.
- Reporter owns `/tmp/{PREFIX}-pr-description.md` and `/tmp/{PREFIX}-final-report.md`.
- Pusher owns changelog creation, format, commit, and push.

Workers must not edit outside their ownership without stating why and coordinating through the main agent.
