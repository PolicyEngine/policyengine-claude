# Claude Code launcher: fix-pr

Read this file only when executing the fix-pr workflow in Claude Code. The canonical
workflow is [workflow.md](workflow.md) — read it first; this file maps its abstract
operations onto Claude Code mechanics and adds nothing else.

## Mechanics

- **"Ask the user"** → `AskUserQuestion` (posting mode, missing PR argument, the
  Phase 2 fix-plan checkpoint questions, and the per-issue and research re-ask
  questions — use the canonical option sets, marking the canonical recommendation
  first).
- **"Delegate role X"** → spawn an agent with the type from the table below and a
  prompt containing: the role's task spec from the canonical workflow, the concrete
  `RUN_ROOT`/`WORKTREE_ID`/`PREFIX` values, the file paths it reads and writes, and —
  for fix roles — "fix ONLY the issues assigned to you in the fix plan" plus "DO NOT
  commit; fix-pusher handles all commits". Include `Load skills:` lines naming the
  role's skills from the canonical Roles table.
- **Guarded push** → pass fix-pusher the captured `PR_NUMBER`, `BASE_REPO_URL`,
  `HEAD_REPO_URL`, `HEAD_BRANCH`, and pre-edit `EXPECTED_HEAD_SHA`. It fetches the base
  branch from `BASE_REPO_URL` for the canonical rebase, must compare the live remote head
  to that SHA after rebasing, and uses the canonical explicit `--force-with-lease` push.
- **Namespacing** → plugin agents and skills are namespaced by the *installed plugin*
  (e.g. `complete:country-models:rules-engineer` under the complete bundle, but a
  different prefix under other bundles). Resolve every agent and skill name in this
  file against the session's available lists by suffix match — never assume a specific
  plugin prefix. If a specialized agent is not installed, fall back to
  `general-purpose` and put the role's full task spec and skills in the prompt.
- **"Concurrently"** (evidence extractors) → spawn all in a single message with
  `run_in_background: true`; wait for the batch.
- **Coordinator context protection** → you are the coordinator in the canonical
  orchestration contract: read ONLY the short handoff files it lists; never read the
  diff, code files, or full review reports; never use Edit/Write on repository files
  yourself.

## Role → agent type

Agent names below are unprefixed; resolve them per the namespacing rule above.

| Canonical role | Agent |
|---|---|
| context-gatherer | `general-purpose` |
| evidence-extractor-{N} | `general-purpose` |
| fix-parameters | `rules-engineer` |
| fix-variables | `rules-engineer` |
| fix-tests | `edge-case-generator` |
| fix-code (non-country-model PRs) | `general-purpose` |
| fix-ci | `ci-fixer` |
| fix-verifier | `implementation-validator` |
| fix-pusher | `pr-pusher` |
| comment-writer | `general-purpose` |
