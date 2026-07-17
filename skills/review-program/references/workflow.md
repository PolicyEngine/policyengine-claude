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

If posting mode is not specified, ask whether to post findings to GitHub.

## Phase 0: Prefix and Cleanup

Derive:

```bash
PREFIX=$(git branch --show-current | tr '/' '-')
PREFIX=${PREFIX:-review-program}
```

Clean stale files:

```bash
rm -f /tmp/${PREFIX}-review-*.md /tmp/${PREFIX}-review-pdf-*.{pdf,txt,png} /tmp/${PREFIX}-600dpi-*.png /tmp/${PREFIX}-ext-*.{pdf,txt,png,md}
```

Resolve the PR number directly if numeric, otherwise with:

```bash
gh pr list --search "$PR_ARG" --json number,title --jq '.[0].number'
```

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
git diff "$MERGE_BASE".."$PR_HEAD" > /tmp/${PREFIX}-review-diff.txt
```

For `--local-diff`, use `HEAD` as `PR_HEAD` after fetching the base branch.

Write `/tmp/{PREFIX}-review-context.md` in 25 lines or fewer with:

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
- render pages with `pdftoppm -png -r {DPI}`
- determine page offsets
- write `/tmp/{PREFIX}-review-pdf-manifest.md` in 30 lines or fewer

If no PDF is found, continue with code-only validators.

## Phase 3: Review Scope

If `--full`, list all files under the relevant state/program path and write `/tmp/{PREFIX}-review-full-filelist.md` in 30 lines or fewer.

Otherwise use the changed files from `/tmp/{PREFIX}-review-context.md`.

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

- `/tmp/{PREFIX}-review-regulatory.md`
- `/tmp/{PREFIX}-review-references.md`
- `/tmp/{PREFIX}-review-code.md`
- `/tmp/{PREFIX}-review-tests.md`
- `/tmp/{PREFIX}-review-pdf-{topic}.md`

## Phase 5: Verification

Do not trust reported PDF mismatches until verified.

For each mismatch:

1. Trace parameter usage and code path for the target year.
2. Reject mismatches from unused, disabled, or deprecated code paths.
3. Re-render disputed pages at 600 DPI.
4. Cross-check extracted text.
5. Verify `#page=XX` references use file page numbers.

Write verification files under `/tmp/{PREFIX}-review-codepath-*`, `/tmp/{PREFIX}-review-mismatch-*`, and `/tmp/{PREFIX}-review-pages.md`.

## Phase 6: Consolidation

Write:

- `/tmp/{PREFIX}-review-full-report.md`
- `/tmp/{PREFIX}-review-summary.md` in 20 lines or fewer

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
gh pr comment $PR_NUMBER --body-file /tmp/${PREFIX}-review-full-report.md
```

End with a short summary and mention that fixes can be applied with `$fix-pr {PR_NUMBER}`.
