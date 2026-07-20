# Codex Workflow: fix-pr

## Purpose

Apply fixes to a PR based on `$review-program` findings, local review files, GitHub review comments, or CI failures.

## Arguments

Parse the text after `$fix-pr`:

- `PR_ARG`: optional PR number or search text
- `--local`: apply fixes locally only, skip push and GitHub comment
- `--resume`: reuse valid artifacts from an interrupted run
- `--full-validation`: run a broader package suite once after targeted tests pass

Examples:

```text
$fix-pr
$fix-pr 6390
$fix-pr "Arkansas"
$fix-pr 6390 --local
```

## Phase 0: Worktree Namespace, PR, and Mode

Derive the worktree-safe runtime root before resolving the PR:

```bash
WORKTREE_ROOT=$(git rev-parse --show-toplevel)
WORKTREE_ID=$(printf '%s' "$WORKTREE_ROOT" | git hash-object --stdin | cut -c1-12)
RUN_ROOT="/tmp/policyengine-command-runs/$WORKTREE_ID"
mkdir -p "$RUN_ROOT"
```

The absolute worktree root—not `.git` or the branch name—is the isolation boundary.

Inspect `git worktree list --porcelain` before checkout. If the PR head branch is already
checked out in another worktree, stop and report its path; never use
`--ignore-other-worktrees` or mutate that checkout remotely. Otherwise check out the PR in
the current worktree, recompute `PREFIX`, and keep every edit/test/git operation within
`WORKTREE_ROOT`.

Resolve the PR:

- if `PR_ARG` is numeric, use it
- otherwise search with `gh pr list --search "$PR_ARG" --json number,title --jq '.[0].number'`
- if omitted, ask the user for a PR number or title

Check out the PR only after resolving it:

```bash
gh pr checkout $PR_NUMBER
```

Skip checkout when the current branch already matches. After checkout or match, derive
`PREFIX` from the current branch. Record the root/ID, PR/head SHA, arguments, input hashes,
phase completion, test commands, and timings in
`{RUN_ROOT}/{PREFIX}-fix-pr-run-state.md`. Refuse artifacts recorded by another worktree.
On a fresh run, clean only this command's artifacts inside `RUN_ROOT`; with `--resume`,
preserve and validate them.

If `--local` is not set, ask whether to push changes and post a summary to GitHub.

## Phase 1: Gather Context

Run:

```bash
gh pr view $PR_NUMBER --json title,body,author,baseRefName,headRefName
gh pr checks $PR_NUMBER
gh pr diff $PR_NUMBER > {RUN_ROOT}/{PREFIX}-fix-pr-diff.txt
```

Check for local review outputs:

```bash
ls $RUN_ROOT/${PREFIX}-review-full-report.md 2>/dev/null && echo LOCAL_REVIEW=true || echo LOCAL_REVIEW=false
```

Reuse the local review only when its reviewed head SHA matches the current PR head.

Write `{RUN_ROOT}/{PREFIX}-fix-pr-issues.md` in 50 lines or fewer by merging:

- local `$review-program` files if present
- PR comments
- PR reviews
- CI status

Classify each issue:

- `CLEAR`: obviously fixable, such as missing references, bad formatting, hard-coded values, or missing tests
- `AMBIGUOUS`: might be by design and needs user decision
- `RESEARCH-NEEDED`: requires checking evidence before deciding

Also mark freshness:

- `CURRENT`: posted after last commit
- `STALE-BUT-OPEN`: older comment, file not modified since
- `POSSIBLY-FIXED`: older comment and file changed since
- `RESOLVED`: skip

## Phase 2: Fix Plan Checkpoint

Show the user counts for critical, should-address, suggestions, and possibly-fixed issues.

Ask which categories to fix:

- critical only
- critical plus should-address
- all including suggestions
- review each issue

For ambiguous and research-needed issues, ask per issue. Extract evidence into `{RUN_ROOT}/{PREFIX}-fix-pr-research-{N}.md` when needed.

Write `{RUN_ROOT}/{PREFIX}-fix-pr-plan.md` with:

- confirmed fixes
- skipped issues and reasons
- fix order
- ownership by parameter, variable, test, CI, and verification work

Do not edit before this file exists.

## Phase 3: Apply Fixes

Fix only issues listed in `{RUN_ROOT}/{PREFIX}-fix-pr-plan.md`.

Dependency order:

1. Parameter fixes
   - references, legal values, YAML hierarchy, missing parameters
2. Variable fixes
   - formulas, hard-coded value replacement, entity level, naming, aggregation patterns
3. Test fixes
   - missing unit tests, boundary cases, wrong periods, non-functional tests
4. CI fixes
   - run the targeted-first test funnel

For tests, append new scenarios to existing test files when possible. Avoid inserting in the middle of YAML tests because it creates noisy renumbering.

Build an exact test manifest from the PR diff and files touched by fixers. Run all affected
tests without `-v`, classify all failures before editing, rerun only failed files/cases,
and use `-v -d 2` only for unresolved calculation failures. Use at most three targeted
repair cycles, then run the program directory once. Run the broader package suite once
only with `--full-validation`.

This workflow currently assumes PolicyEngine-US; adapt the package argument for UK or Canada PRs.

Do not format in the CI loop. Write `{RUN_ROOT}/{PREFIX}-fix-pr-ci-result.md` in 15 lines
or fewer with commands, test/rerun counts, fixes, and elapsed time.

## Phase 4: Verify

Verify every fix in the plan:

- issue addressed
- no new hard-coded legal values
- new parameters have references
- formulas use correct patterns
- tests cover the expected behavior

Write `{RUN_ROOT}/{PREFIX}-fix-pr-verification.md` in 15 lines or fewer.

If verification finds issues, route them to the owning fixer and rerun verification. If
still blocked after one targeted round, stop; do not push.

## Phase 5: Push and Comment

Never delete or stage `sources/working_references.md` or other local research.

If `--local`, stop after format and verification.

Otherwise:

1. Run `make format` once and rerun affected tests if executable files changed.
2. Stage only fix-plan and formatting/changelog files.
3. Commit with a terse message such as `Fix issues from review`.
4. Resolve the PR's actual base branch, fetch upstream, and rebase the commit without
   guessing `main` or `master`.
5. Push.
6. Write `{RUN_ROOT}/{PREFIX}-fix-pr-comment.md` from actual fixes, skipped items, and verification results.
7. Post with:

```bash
gh pr comment $PR_NUMBER --body-file {RUN_ROOT}/{PREFIX}-fix-pr-comment.md
```

End with a concise fix summary: issues fixed, skipped, tests, pushed, and comment posted.
