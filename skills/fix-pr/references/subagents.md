# Codex Subagent Plan: fix-pr

Use this plan when Codex subagent use is available and authorized.

Codex does not have Claude's named agent types. Simulate each fixer by spawning a `worker`. Tell every worker that it is not alone in the codebase, must not revert edits by others, and must edit only files in its ownership scope.

Subagents can use PolicyEngine skills, but the orchestrator should name them explicitly in each subagent prompt. Do not assume a worker will infer the right skills from the parent context.

## Role Mapping

| Claude role | Codex role | Responsibility | Output |
|---|---|---|---|
| context-gatherer | worker | Merge local review files, PR comments, review freshness, and CI status | `{RUN_ROOT}/{PREFIX}-fix-pr-issues.md` |
| evidence-extractor | worker | Extract evidence for ambiguous issues | `{RUN_ROOT}/{PREFIX}-fix-pr-research-{N}.md` |
| fix-parameters | worker | Fix parameter/reference/legal value issues | parameter files |
| fix-variables | worker | Fix formula, naming, entity, aggregation, and hard-coded value issues | variable files |
| fix-tests | worker | Add or repair tests | test files |
| fix-ci | worker | Run targeted tests and fix evidenced failures | `{RUN_ROOT}/{PREFIX}-fix-pr-ci-result.md` |
| fix-verifier | worker | Verify the fix plan was fully applied | `{RUN_ROOT}/{PREFIX}-fix-pr-verification.md` |
| fix-pusher | worker | Stage, commit, and push intended fixes | commit/push |
| comment-writer | worker | Summarize actual fixes for GitHub | `{RUN_ROOT}/{PREFIX}-fix-pr-comment.md` |

## Skills to Pass to Workers

Include these lines in subagent prompts as relevant:

- Parameter fixer: "Use `$policyengine-parameter-patterns`, `$policyengine-variable-patterns`, and `$policyengine-code-organization`."
- Variable fixer: "Use `$policyengine-variable-patterns`, `$policyengine-parameter-patterns`, `$policyengine-code-style`, `$policyengine-aggregation`, and `$policyengine-period-patterns`."
- Test fixer: "Use `$policyengine-testing-patterns`, `$policyengine-period-patterns`, and `$policyengine-variable-patterns`."
- CI fixer: "Use `$policyengine-testing-patterns`, `$policyengine-variable-patterns`, `$policyengine-period-patterns`, and `$policyengine-code-style`."
- Verification worker: "Use `$policyengine-parameter-patterns`, `$policyengine-variable-patterns`, `$policyengine-code-style`, and `$policyengine-review-patterns`."

## Delegation Pattern

1. Do blocking setup locally: derive the worktree-safe `RUN_ROOT`, parse arguments,
   resolve PR, determine local/push mode, check out the PR, and save the diff.
2. Spawn context-gatherer. Read only `{RUN_ROOT}/{PREFIX}-fix-pr-issues.md`.
3. Ask user fix-scope questions locally and write `{RUN_ROOT}/{PREFIX}-fix-pr-plan.md`.
4. Spawn evidence-extractor workers in parallel for research-needed issues; read their short outputs and ask follow-up decisions.
5. Apply fixes in dependency order:
   - parameter worker
   - variable worker after parameter worker
   - test worker after variable worker
   - CI worker after all code/test changes
6. Spawn verifier. If it reports issues, run one targeted fixer round and recheck.
7. If not local-only, spawn pusher and comment-writer after verification.

Pass concrete `RUN_ROOT`, `WORKTREE_ID`, and `PREFIX` values to every worker. No worker may
read or write process-global `/tmp/fix-pr-*` or `/tmp/{PREFIX}-...` paths.

## Ownership

- Parameter fixer owns parameter YAML files identified in `{RUN_ROOT}/{PREFIX}-fix-pr-plan.md`.
- Variable fixer owns variable Python files identified in `{RUN_ROOT}/{PREFIX}-fix-pr-plan.md`.
- Test fixer owns test files identified in `{RUN_ROOT}/{PREFIX}-fix-pr-plan.md`, including YAML tests and any Python test files.
- CI fixer may edit files only to resolve failures from the planned fixes.
- Pusher owns only formatting, intended staging, commit, rebase, and push. It must not
  delete or stage local research under `sources/`.
