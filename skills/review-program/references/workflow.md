# Codex Workflow: review-program

## Purpose

Review any PolicyEngine PR without changing code. The review adapts to state programs, federal parameter changes, infrastructure, API, frontend, and mixed PRs.

## Arguments

Parse the text after `$review-program`:

- `PR_ARG`: first non-flag, non-URL argument
- `PDF_URL`: first URL argument, optional
- `--local`: show findings locally only
- `--local-diff`: review local branch diff and imply `--local`
- `--full`: audit the full program path, not just changed files
- `--skip-pdf`: skip PDF acquisition and audit
- `--600dpi`: render PDFs at 600 DPI
- `--resume`: reuse valid artifacts from an interrupted review
- `--incremental REPORT`: review changes and unresolved findings since a prior report

If posting mode is not specified, ask whether to post findings to GitHub.

## Phase 0: Worktree Namespace, Prefix, and Run State

Derive:

```bash
WORKTREE_ROOT=$(git rev-parse --show-toplevel)
WORKTREE_ID=$(printf '%s' "$WORKTREE_ROOT" | git hash-object --stdin | cut -c1-12)
RUN_ROOT="/tmp/policyengine-command-runs/$WORKTREE_ID"
mkdir -p "$RUN_ROOT"
PREFIX=$(git branch --show-current | tr '/' '-')
PREFIX=${PREFIX:-review-program}
```

Record the root/ID, arguments, PR/head SHA, source checksums, phase completion, and timings
in `{RUN_ROOT}/{PREFIX}-review-run-state.md`. The absolute worktree root—not `.git` or the
branch name—is the isolation boundary. Refuse artifacts recorded by another worktree.
Never switch/detach any worktree or read another worktree's uncommitted files. Standard
mode reviews fetched SHAs; `--local-diff` is scoped to `WORKTREE_ROOT`.

On a fresh review, clean only review artifacts inside `RUN_ROOT`. With `--resume`, preserve
and validate artifacts. With `--incremental`, first copy the supplied report to
`{RUN_ROOT}/{PREFIX}-review-prior-report.md` so the canonical report can be replaced.

`--resume` is also valid after a completed run whose PR head has since changed: the head
change invalidates analysis artifacts (diff, context, findings), which re-run in full,
while checksum-valid PDF downloads and rendered pages are reused.

```bash
if [ "$RESUME" != "true" ] && [ -z "$INCREMENTAL_REPORT" ]; then
  rm -f "$RUN_ROOT/${PREFIX}-review-"*.md \
    "$RUN_ROOT/${PREFIX}-review-pdf-"*.{pdf,txt,png} \
    "$RUN_ROOT/${PREFIX}-600dpi-"*.png \
    "$RUN_ROOT/${PREFIX}-ext-"*.{pdf,txt,png,md}
fi
```

Resolve the target PR before gathering context:

- if `PR_ARG` is numeric, use it directly
- if `PR_ARG` contains search text, resolve it with:

```bash
gh pr list --search "$PR_ARG" --json number,title --jq '.[0].number'
```

- if `PR_ARG` is omitted, ask the user for a PR number or title and wait for the answer

Ask for the PR, not the program. Infer the state and program from the selected PR's diff in
Phase 1. If search text returns no PR, report that clearly and ask the user for another PR
number or title.

## Phase 1: PR Context

Run small structured commands:

```bash
gh pr view $PR_NUMBER --json title,body,author,baseRefName,headRefName
gh pr checks $PR_NUMBER
```

Do not check out the PR. Fetch refs and compute an explicit merge-base from captured SHAs, not from remote-tracking refs:

```bash
BASE_BRANCH=$(gh pr view $PR_NUMBER --json baseRefName --jq '.baseRefName')
git fetch origin "$BASE_BRANCH"
BASE_SHA=$(git rev-parse FETCH_HEAD)
git fetch origin "pull/$PR_NUMBER/head"
PR_HEAD=$(git rev-parse FETCH_HEAD)
MERGE_BASE=$(git merge-base "$BASE_SHA" "$PR_HEAD")
BEHIND=$(git rev-list --count "$PR_HEAD..$BASE_SHA")
AHEAD=$(git rev-list --count "$BASE_SHA..$PR_HEAD")
git diff "$MERGE_BASE".."$PR_HEAD" > $RUN_ROOT/${PREFIX}-review-diff.txt
```

For `--local-diff`, use `HEAD` as `PR_HEAD` after fetching the base branch.

For `--incremental`, read the prior reviewed head SHA, prove it is an ancestor of
`PR_HEAD`, and diff `PRIOR_HEAD..PR_HEAD`. Fall back to the full merge-base diff when the
baseline or ancestry cannot be proven. Keep unresolved prior findings in scope.

Write `{RUN_ROOT}/{PREFIX}-review-context.md` in 25 lines or fewer with:

- PR scope and type
- state, program, and year when applicable
- CI status
- branch staleness
- changed parameter, variable, test, and other files
- topics and any PDF references found

## Phase 2: PDF Acquisition

Skip when `--skip-pdf` is set or the PR is clearly code-only. Otherwise:

- use the user-provided PDF or discover source PDFs from PR body, YAML references, and official sites
- download up to five official PDFs
- extract text with `pdftotext`
- render every PDF page with `pdftoppm -png -r {DPI}`
- verify the rendered page count matches the PDF page count
- reuse rendering only when PDF checksum + DPI match and the full page sequence exists
- determine page offsets
- write `{RUN_ROOT}/{PREFIX}-review-pdf-manifest.md` in 30 lines or fewer

If no PDF is found, continue with code-only validators.

For incremental reviews, reuse cached sources and verified PDF findings only when changed
files do not alter parameter values, formulas, references, or sources and the checksums
still match. Otherwise reacquire only affected sources.

## Phase 3: Review Scope

If `--full`, list all files under the relevant state/program path and write `{RUN_ROOT}/{PREFIX}-review-full-filelist.md` in 30 lines or fewer.

Otherwise use the changed files from `{RUN_ROOT}/{PREFIX}-review-context.md`.

In incremental mode, include unresolved prior findings and run PDF auditors only for
changed semantic topics.

Map files and PDFs to topics such as:

- eligibility and income
- benefits and standards
- rates and brackets
- credits
- deductions
- tests
- infrastructure

For large PDFs, split audit work into page ranges of roughly 40 pages or fewer.

## Phase 4: Validators

Run validators appropriate to the PR scope.

Program PRs:

- regulatory accuracy
- reference quality
- code patterns
- test coverage
- PDF value audit when source PDFs exist

Infrastructure, API, or frontend PRs:

- code patterns
- test coverage
- skip regulatory and reference validators unless parameters are changed

Validator outputs:

- `{RUN_ROOT}/{PREFIX}-review-regulatory.md`
- `{RUN_ROOT}/{PREFIX}-review-references.md`
- `{RUN_ROOT}/{PREFIX}-review-code.md`
- `{RUN_ROOT}/{PREFIX}-review-tests.md`
- `{RUN_ROOT}/{PREFIX}-review-pdf-{topic}.md`

## Phase 5: Verification

Do not trust reported PDF mismatches until verified.

For each mismatch:

1. Trace parameter usage and code path for the target year.
2. Reject mismatches from unused, disabled, or deprecated code paths.
3. Re-render disputed pages at 600 DPI.
4. Cross-check extracted text.
5. Verify `#page=XX` references use file page numbers.

Write verification files under `{RUN_ROOT}/{PREFIX}-review-codepath-*`, `{RUN_ROOT}/{PREFIX}-review-mismatch-*`, and `{RUN_ROOT}/{PREFIX}-review-pages.md`.

## Phase 6: Consolidation

Write:

- `{RUN_ROOT}/{PREFIX}-review-full-report.md`
- `{RUN_ROOT}/{PREFIX}-review-summary.md` in 20 lines or fewer

Every full report must include the reviewed head SHA and `full` or `incremental from
{PRIOR_HEAD}` mode. Assign each finding a stable ID (C1/C2… Critical, A1… Should Address,
S1… Suggestions); incremental reviews carry prior IDs unchanged and mark each prior
finding resolved or still open. The summary includes elapsed time, agent count, rendered
pages, and cache hits, read from the run-state ledger.

Severity rules:

- `CRITICAL`: regulatory mismatches, confirmed value mismatches, hard-coded legal values, missing or non-corroborating references, wrong citations, CI failures, incorrect formulas, formula variables with no tests, non-functional tests.
- `SHOULD ADDRESS`: pattern violations, missing edge cases, naming issues, period issues, formatting issues, missing rounding/flooring/capping when the core formula is otherwise correct.
- `SUGGESTION`: documentation, readability, performance, and non-blocking improvements.

Recommended review severity:

- `APPROVE`: no critical issues and only minor suggestions
- `COMMENT`: issues exist but are not blocking
- `REQUEST_CHANGES`: critical issues exist

## Phase 7: Post or Display

If `--local`, show the full report in the conversation.

Otherwise post without loading the full report into context:

```bash
gh pr comment $PR_NUMBER --body-file $RUN_ROOT/${PREFIX}-review-full-report.md
```

End with a short summary and mention that fixes can be applied with `$fix-pr {PR_NUMBER}`.
