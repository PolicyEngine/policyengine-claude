# Codex Workflow: fix-pr

## Purpose

Apply fixes to a PR based on `$review-program` findings, local review files, GitHub review comments, or CI failures.

## Arguments

Parse the text after `$fix-pr`:

- `PR_ARG`: optional PR number or search text
- `--local`: apply fixes locally only, skip push and GitHub comment

Examples:

```text
$fix-pr
$fix-pr 6390
$fix-pr "Arkansas"
$fix-pr 6390 --local
```

## Phase 0: Resolve PR and Mode

Clean stale files:

```bash
rm -f /tmp/fix-pr-*.md /tmp/fix-pr-diff.txt
```

Derive:

```bash
PREFIX=$(git branch --show-current | tr '/' '-')
PREFIX=${PREFIX:-fix-pr}
```

Resolve the PR:

- if `PR_ARG` is numeric, use it
- otherwise search with `gh pr list --search "$PR_ARG" --json number,title --jq '.[0].number'`
- if omitted, ask the user for a PR number or title

Check out the PR only after resolving it:

```bash
gh pr checkout $PR_NUMBER
```

If `--local` is not set, ask whether to push changes and post a summary to GitHub.

## Phase 1: Gather Context

Run:

```bash
gh pr view $PR_NUMBER --json title,body,author,baseRefName,headRefName
gh pr checks $PR_NUMBER
gh pr diff $PR_NUMBER > /tmp/fix-pr-diff.txt
```

Check for local review outputs:

```bash
ls /tmp/${PREFIX}-review-full-report.md 2>/dev/null && echo LOCAL_REVIEW=true || echo LOCAL_REVIEW=false
```

Write `/tmp/fix-pr-issues.md` in 50 lines or fewer by merging:

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

For ambiguous and research-needed issues, ask per issue. Extract evidence into `/tmp/fix-pr-research-{N}.md` when needed.

Write `/tmp/fix-pr-plan.md` with:

- confirmed fixes
- skipped issues and reasons
- fix order
- ownership by parameter, variable, test, CI, and verification work

Do not edit before this file exists.

## Phase 3: Apply Fixes

Fix only issues listed in `/tmp/fix-pr-plan.md`.

Dependency order:

1. Parameter fixes
   - references, legal values, YAML hierarchy, missing parameters
2. Variable fixes
   - formulas, hard-coded value replacement, entity level, naming, aggregation patterns
3. Test fixes
   - missing unit tests, boundary cases, wrong periods, non-functional tests
4. CI fixes
   - run focused tests and format

For tests, append new scenarios to existing test files when possible. Avoid inserting in the middle of YAML tests because it creates noisy renumbering.

Run focused tests:

```bash
policyengine-core test {test path} -c policyengine_us -v
```

This workflow currently assumes PolicyEngine-US; adapt the package argument for UK or Canada PRs.

Run `make format`.

Write `/tmp/fix-pr-ci-result.md` in 10 lines or fewer.

## Phase 4: Verify

Verify every fix in the plan:

- issue addressed
- no new hard-coded legal values
- new parameters have references
- formulas use correct patterns
- tests cover the expected behavior

Write `/tmp/fix-pr-verification.md` in 15 lines or fewer.

If verification finds issues, fix one more round and rerun focused checks. If still blocked, stop and report remaining issues.

## Phase 5: Push and Comment

Always remove development-only working references before staging:

```bash
rm -f sources/working_references.md
```

If `--local`, stop after format and verification.

Otherwise:

1. Rebase on the PR base branch.
2. Stage only intended files.
3. Commit with a terse message such as `Fix issues from review`.
4. Push.
5. Write `/tmp/fix-pr-comment.md` from actual fixes, skipped items, and verification results.
6. Post with:

```bash
gh pr comment $PR_NUMBER --body-file /tmp/fix-pr-comment.md
```

End with a concise fix summary: issues fixed, skipped, tests, pushed, and comment posted.
