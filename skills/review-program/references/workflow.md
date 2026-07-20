# Workflow: review-program (canonical)

This file is the single canonical definition of the review-program workflow. The Claude
Code command (`/review-program`) and the Codex skill (`$review-program`) are thin
launchers over this document: each parses arguments, maps the roles below to its native
delegation mechanism, and then follows these phases exactly. This document is
surface-neutral — it never names runtime-specific tools or agent types. "Ask the user"
means a blocking question on the active surface; "delegate role X" means running that
role's task through the surface's delegation mechanism (or executing it directly, in
order, when delegation is unavailable).

## Purpose

Review any PolicyEngine PR without changing code. The review adapts to state programs,
federal parameter changes, infrastructure, API, frontend, and mixed PRs. PDF audit runs
only when source documents are relevant.

## Orchestration contract

**The coordinator protects its context window.** All information-gathering work is
delegated. The coordinator:

- parses arguments, resolves the PR, and runs small structured `gh` commands;
- saves the diff to disk for delegates — and never reads it;
- reads ONLY short summary files: context (≤25 lines), manifest (≤30 lines),
  full-audit file list (≤30 lines), run state (≤30 lines), verification queue
  (≤30 lines), summary (≤20 lines);
- never reads parameter YAMLs, variable `.py` files, PDF text or screenshots, or any
  individual finding file — those flow between delegates via disk;
- posts the final report from disk without loading it (local display mode is the one
  exception, at the very end).

**Completion contract (every delegated role).** After writing its output file(s), the
role's task is COMPLETE. Its final message is one line:
`DONE — wrote {file} ({brief stat})`. No further work after the output is written; no
silent finishes. Coordinator side: wait for delegate completions in a batch; never poll
or sleep. If one delegate in a batch has not reported but its expected output file exists
and is well-formed, treat it as stalled — read the file and proceed.

**Read-only contract.** No role edits repository source files or changes any branch or
worktree. Delegates may write only their assigned `{RUN_ROOT}/{PREFIX}-review-...` report
files and downloaded/rendered source artifacts.

## Roles

| Role | Responsibility | Writes | Skills to load |
|---|---|---|---|
| context-analyzer | Analyze the saved diff; classify PR scope, files, topics | `{RUN_ROOT}/{PREFIX}-review-context.md` | — |
| pdf-collector | Find/download official PDFs, extract text, render every page, build manifest | `{RUN_ROOT}/{PREFIX}-review-pdf-manifest.md` | — |
| file-lister | List full-audit files when `--full` | `{RUN_ROOT}/{PREFIX}-review-full-filelist.md` | — |
| regulatory-reviewer | Research regulations independently; compare implementation to law | `{RUN_ROOT}/{PREFIX}-review-regulatory.md` | policyengine-model-development (references/variables.md, references/parameters.md); policyengine-us |
| reference-checker | Validate reference presence, format, corroboration, page numbers | `{RUN_ROOT}/{PREFIX}-review-references.md` | policyengine-model-development (references/parameters.md) |
| code-validator | Audit code patterns (read-only; ten categories) | `{RUN_ROOT}/{PREFIX}-review-code.md` | policyengine-model-development (references/parameters.md, references/variables.md, references/style.md, references/periods-and-aggregation.md) |
| edge-case-checker | Audit test coverage for missing boundaries and scenarios | `{RUN_ROOT}/{PREFIX}-review-tests.md` | policyengine-model-development (references/tests.md, references/periods-and-aggregation.md) |
| pdf-audit-{topic} | Compare repo values against assigned PDF pages only | `{RUN_ROOT}/{PREFIX}-review-pdf-{topic}.md` | policyengine-model-development (references/parameters.md, references/periods-and-aggregation.md) |
| verifier-xref-{N} | Verify one cross-referenced page flagged by an auditor | `{RUN_ROOT}/{PREFIX}-review-xref-{N}.md` | — |
| verifier-ext-{N} | Find and verify one external PDF flagged by an auditor | `{RUN_ROOT}/{PREFIX}-review-ext-{N}.md` | — |
| verifier-codepath-{N} | Trace whether one mismatched parameter is reachable in the target year | `{RUN_ROOT}/{PREFIX}-review-codepath-{N}.md` | policyengine-model-development (references/variables.md, references/parameters.md, references/periods-and-aggregation.md, references/style.md) |
| verifier-mismatch-{N} | Visually verify one surviving mismatch at 600 DPI | `{RUN_ROOT}/{PREFIX}-review-mismatch-{N}.md` | policyengine-model-development (references/parameters.md, references/periods-and-aggregation.md) |
| verifier-pages | Verify every `#page=XX` reference the PR adds | `{RUN_ROOT}/{PREFIX}-review-pages.md` | — |
| verification-planner | Read every Phase 4 report; write the bounded verification queue the coordinator routes Phase 5 from | `{RUN_ROOT}/{PREFIX}-review-verification-queue.md` | — |
| consolidator | Merge, deduplicate, classify all findings; write full report + summary | `{RUN_ROOT}/{PREFIX}-review-full-report.md`, `{RUN_ROOT}/{PREFIX}-review-summary.md` | — |

Every role that reviews parameter files must know: PDF reference hrefs use the FILE page
number (`#page=XX`), never the printed page number; single-page PDFs are the only
exception.

## Arguments

- `PR_ARG`: first non-flag, non-URL argument — PR number or search text (optional;
  prompts if omitted)
- `PDF_URL`: first URL argument, optional — official source PDF; auto-discovered if
  omitted
- `--local`: show findings locally only, skip GitHub posting
- `--local-diff`: review the local branch diff without pushing; implies `--local`
- `--full`: audit ALL implemented parameters under the program path, not just the PR diff
- `--skip-pdf`: skip PDF acquisition and audit; code validators only
- `--600dpi`: render PDFs at 600 DPI instead of 300 (scanned docs, dense tables)
- `--resume`: reuse valid artifacts from an interrupted review
- `--incremental REPORT`: review changes and unresolved findings since a prior full
  report; reuse its source/PDF evidence when policy values and references are unchanged
- `--prefix NAME`: override the artifact filename prefix. Nesting workflows
  (encode-policy-v2, backdate-program) pass their own prefix so the
  `{RUN_ROOT}/{PREFIX}-review-...` paths their coordinators read are the paths this run
  writes, regardless of which branch is checked out when the review runs

## Phase 0: Worktree namespace, run state, PR resolution, posting mode

Derive the worktree-safe runtime root before any artifact operation:

```bash
WORKTREE_ROOT=$(git rev-parse --show-toplevel)
WORKTREE_ID=$(printf '%s' "$WORKTREE_ROOT" | git hash-object --stdin | cut -c1-12)
RUN_ROOT="/tmp/policyengine-command-runs/$WORKTREE_ID"
mkdir -p "$RUN_ROOT"
PREFIX=${ARG_PREFIX:-$(git branch --show-current | tr '/' '-')}
PREFIX=${PREFIX:-review-program}
```

`ARG_PREFIX` is the `--prefix` value when supplied; a caller that overrides the prefix
owns its uniqueness within this worktree's `RUN_ROOT`.

All runtime files use `{RUN_ROOT}/{PREFIX}-...` paths. The absolute worktree root — not
the shared Git common directory or the branch name — is the isolation boundary. Pass the
concrete `RUN_ROOT`, `WORKTREE_ID`, and `PREFIX` values (and, from Phase 1 on,
`SNAPSHOT`) to every delegate; no delegate may read or write process-global
`/tmp/{PREFIX}-...` paths.

This workflow is read-only across the whole worktree set: never switch or detach any
existing worktree, and never read another worktree's uncommitted files. The one
exception is the run's own disposable `PR_HEAD` snapshot worktree (created in Phase 1
under `RUN_ROOT`, removed in Phase 7), which exists so delegates read the PR's actual
file contents. Standard mode reviews fetched SHAs; `--local-diff` is scoped to
`WORKTREE_ROOT`.

Record `WORKTREE_ROOT`, `WORKTREE_ID`, arguments, PR/head SHA, source checksums, phase
completion, and timings in `{RUN_ROOT}/{PREFIX}-review-run-state.md`. Refuse artifacts
recorded by another worktree. Invalidate an artifact and its dependents when the PR head,
source checksum, or review scope it depends on changed.

On a fresh full review, clean only review artifacts inside `RUN_ROOT`. With `--resume`,
preserve and validate artifacts. With `--incremental`, first copy the supplied report to
`{RUN_ROOT}/{PREFIX}-review-prior-report.md` so the canonical output path can be replaced.

`--resume` is also valid after a completed run whose PR head has since changed: the head
change invalidates analysis artifacts (diff, context, findings), which re-run in full,
while checksum-valid PDF downloads and rendered pages are reused. A completed ledger with
an unchanged head means there is nothing to redo — report that instead of re-reviewing.

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

Ask for the PR, not the program. Infer the state and program from the selected PR's diff
in Phase 1. If search text returns no PR, report that clearly and ask the user for
another PR number or title — do not guess or stop.

In fork-based checkouts, make sure `gh` targets the PR's base repository (confirm with
`gh repo set-default --view`, or pass `--repo OWNER/REPO`) so PR numbers and searches
resolve against the right repo, not the fork.

**Posting mode**: if `--local` or `--local-diff` is set, run local-only. Otherwise ask
the user whether to post findings to GitHub when complete (default: post).

## Phase 1: PR context

Run small structured commands only:

```bash
gh pr view $PR_NUMBER --json title,body,author,baseRefName,headRefName
gh pr checks $PR_NUMBER
```

**Never check out the PR.** Fetch refs and compute an explicit merge-base from captured
SHAs. Fetch from the PR's base repository by URL — not from a named remote: in
fork-based checkouts `origin` is often the fork, where `pull/N/head` refs do not exist
and the base branch may be stale. The PR URL identifies the base repository
authoritatively:

```bash
PR_URL=$(gh pr view "$PR_NUMBER" --json url --jq '.url')
BASE_REPO_URL=${PR_URL%/pull/*}
BASE_BRANCH=$(gh pr view "$PR_NUMBER" --json baseRefName --jq '.baseRefName')
git fetch "$BASE_REPO_URL" "$BASE_BRANCH"
BASE_SHA=$(git rev-parse FETCH_HEAD)
git fetch "$BASE_REPO_URL" "pull/$PR_NUMBER/head"
PR_HEAD=$(git rev-parse FETCH_HEAD)
MERGE_BASE=$(git merge-base "$BASE_SHA" "$PR_HEAD")
BEHIND=$(git rev-list --count "$PR_HEAD..$BASE_SHA")
AHEAD=$(git rev-list --count "$BASE_SHA..$PR_HEAD")
git diff "$MERGE_BASE".."$PR_HEAD" > $RUN_ROOT/${PREFIX}-review-diff.txt
```

If a fetch fails, STOP and surface the error — never continue with a possibly-stale or
wrong-HEAD diff.

**Materialize the PR's file contents.** The current checkout need not be at `PR_HEAD`,
and delegates must never audit whatever branch happens to be checked out. After the
fetch, create a disposable read-only snapshot unless the checkout already matches:

```bash
SNAPSHOT="$WORKTREE_ROOT"
if [ "$(git rev-parse HEAD)" != "$PR_HEAD" ]; then
  SNAPSHOT="$RUN_ROOT/${PREFIX}-pr-snapshot"
  # clear any stale snapshot from an interrupted run before creating
  git worktree remove --force "$SNAPSHOT" 2>/dev/null || rm -rf "$SNAPSHOT"
  git worktree add --detach "$SNAPSHOT" "$PR_HEAD"
fi
```

Pass the concrete `SNAPSHOT` value to every delegate; every role that reads repository
files (validators, PDF auditors, code-path verifiers, file-lister) reads them under
`SNAPSHOT`, never under a path it chose itself. The snapshot is read-only: no role
edits, commits, or branches in it. Record its creation in the run state and remove it
in Phase 7.

For `--local-diff`, use `HEAD` as `PR_HEAD` after fetching the base branch — same
merge-base approach, no branch switch, and `SNAPSHOT` stays `WORKTREE_ROOT`.

For `--incremental`, read the prior reviewed head SHA from the prior report, prove it is
an ancestor of `PR_HEAD`, and diff `PRIOR_HEAD..PR_HEAD` instead. If ancestry cannot be
proven or the prior report lacks its head SHA, fall back to the full merge-base diff and
say why. Unresolved prior findings remain in scope even when their original file did not
change — track them by their stable finding IDs (C1/A1/S1…) from the prior report.

**Staleness notice**: if `BEHIND > 0`, print a one-line friendly reminder that the branch
is behind base and could be rebased — then continue automatically. The review is scoped
to the merge-base diff, so staleness cannot cause false positives. Record the count for
the report's Branch Status note; never classify staleness as a finding.

**Delegate context analysis** (role: context-analyzer), in parallel with Phase 2 when a
PDF URL is already known. The context-analyzer reads the saved diff — which is
authoritative scope; files outside it do not exist for this review — and writes
`{RUN_ROOT}/{PREFIX}-review-context.md` (≤25 lines): PR scope/type; state, program, year
(or N/A); CI status and branch staleness — both supplied by the coordinator in the
delegation from its `gh pr checks` output and AHEAD/BEHIND counts, since the delegate
cannot derive them from the diff; changed parameter/variable/test/other file lists;
topics; PDF references found in the PR body or YAML `reference:` fields; whether source
documents exist.

The coordinator reads only that context file, which determines delegate selection:

- **State/federal program PRs**: all four validators + PDF audit (if source docs exist)
- **Infrastructure/API/frontend PRs**: code-validator + edge-case-checker only; skip
  regulatory-reviewer and reference-checker (no parameters), skip the PDF phase
- **Mixed PRs**: all four validators, but regulatory/reference roles review only the
  parameter/variable files

## Phase 2: PDF acquisition

Skip when `--skip-pdf` is set, or when the context says no source documents and the
scope is infrastructure/API/frontend — write a one-line manifest stub saying so instead.

**Incremental reuse**: if the prior report's source manifest exists and the incremental
diff does not change parameter values, formulas, reference links, or source documents,
reuse the manifest and skip acquisition and audit (code and test validators still run).
If any of those semantic inputs changed, reacquire only changed or missing sources.

Otherwise delegate acquisition (role: pdf-collector):

1. Use the user-provided PDF URL if given; otherwise discover sources from the PR body,
   YAML references in the saved diff, and official agency sites (web search).
2. For each PDF found (up to 5):
   - download to `{RUN_ROOT}/{PREFIX}-review-pdf-{N}.pdf`
   - page count: `pdfinfo … | grep Pages`
   - extract text to `{RUN_ROOT}/{PREFIX}-review-pdf-{N}.txt` with `pdftotext`
   - render every page:
     `pdftoppm -png -r {DPI} {RUN_ROOT}/{PREFIX}-review-pdf-{N}.pdf {RUN_ROOT}/{PREFIX}-review-pdf-{N}-page`
   - verify the rendered page count matches the PDF page count
   - reuse an existing rendering only when the PDF checksum and DPI match and the
     complete expected page sequence exists
   - determine the page offset (cover/TOC pages before content page 1)
3. Check for supplementary documents referenced by the main booklet.
4. Write `{RUN_ROOT}/{PREFIX}-review-pdf-manifest.md` (≤30 lines): per PDF — title, URL,
   path, page count and offset, text path, screenshot pattern, topics covered with page
   ranges. If no PDF was found, say so; the review continues code-only.

The coordinator reads only the manifest (page counts drive Phase 3 splitting).

## Phase 3: Map files to topics and plan the audit split

Inputs: the context summary and the PDF manifest — nothing else.

**Files in scope**: with `--full`, delegate a quick file listing (role: file-lister) of
everything under the state/program path into
`{RUN_ROOT}/{PREFIX}-review-full-filelist.md` (≤30 lines). Without `--full`, use the
changed-file lists from the context summary. In incremental mode, scope is the
incremental file list plus unresolved prior findings; run PDF auditors only for changed
semantic topics and reuse prior verified findings for untouched topics. Do not reopen
findings already recorded as resolved unless a changed file could regress them.

Map files and PDF page ranges to topics (eligibility & income, benefits & standards,
rates & brackets, credits, deductions, tests, infrastructure).

**Splitting rule**: each PDF audit role reads at most ~40 pages. Split by topic first,
then subdivide any topic over 40 pages into page-range chunks:

| Total PDF pages | Audit roles | Strategy |
|---|---|---|
| ≤40 | 1-2 | topic split only |
| 41-80 | 2-3 | topic split; subdivide any topic >40 pages |
| 81-150 | 3-4 | subdivide large topics into ~30-40 page chunks |
| 151+ | 4-5 | split by topic AND page range within topics |

Subdivided roles get their own page range, the SAME repo file list, and instructions to
report only values found within their range.

Before spawning PDF audit roles, verify the complete rendered page sequence exists; reuse
it only when the PDF checksum and DPI match the manifest, rerendering the full PDF if any
page is missing or stale. Audit roles read only their assigned ranges to bound context,
but every page stays available for cross-reference and citation verification.

## Phase 4: Parallel validation

Delegate ALL applicable roles concurrently — code validators and PDF audit roles run at
the same time. Selection follows the Phase 1 scope rules.

**Validator: regulatory accuracy** (role: regulatory-reviewer — skip for
infra/API/frontend). Research the regulations FIRST, independent of the code; compare the
implementation to legal requirements; identify discrepancies and missing program
components. Check for reinvented variables: PolicyEngine-US has hundreds of existing
variables for common concepts (`fpg`, `smi`, `tanf_fpg`, `is_tanf_enrolled`, `ssi`,
`tanf_gross_earned_income`, `snap_gross_income`, …) — if the PR creates a new variable
for a concept that already exists, that is CRITICAL; grep the codebase to verify before
flagging. Key question: does this implementation correctly reflect the law?

**Validator: reference quality** (role: reference-checker — skip for
infra/API/frontend). Find parameters missing references; check format (page numbers,
detailed subsections); verify references corroborate the values; check jurisdiction match
(federal vs state sources); verify `#page=XX` is the FILE page number using the manifest
offset; flag session-law refs that should cite permanent statutes. Key question: can
every value be traced to an authoritative source?

**Validator: code patterns** (role: code-validator — always runs; READ-ONLY, report
only). Scan every in-scope file for the ten categories:

1. Hard-coded values in formulas (CRITICAL)
2. Variable naming conventions + duplicate variables (CRITICAL if duplicate)
3. Aggregation patterns (`adds`, `add()`, `add() > 0`)
4. Period usage (incl. mid-year tests using next January, not the effective month)
5. Reference format (variables: bare strings; parameters: title/href dicts, page in href)
6. Parameter formatting (description, label, values)
7. TODO / placeholder detection (CRITICAL)
8. Changelog fragment at `changelog.d/<branch>.<type>.md` (CRITICAL if missing)
9. Boolean toggle date alignment (CRITICAL)
10. Entity-level mismatches (CRITICAL)

Findings grouped by severity, each with file:line. Key question: does the code follow
PolicyEngine standards?

**Validator: test coverage** (role: edge-case-checker — always runs). Missing boundary
tests, untested edge cases, untested parameter combinations, missing integration test.
Key question: are the important scenarios tested?

**PDF audit** (roles: pdf-audit-{topic} — skip if the manifest says no PDF). Each role:
read ONLY your assigned page screenshots; read the in-scope parameter and variable
files; compare each repo value against the PDF — numerical values, effective dates,
filing-status/family-size variations, uprated values (compute and compare), "New for
{year}" changes. Report: MATCHES (count + list), MISMATCHES (cite both values and the
PDF page), MISSING FROM REPO, MISSING FROM PDF. Never guess a value you have not seen.
Two flag types for out-of-scope evidence:

- `CROSS-REFERENCE NEEDED: page {XX} — need to verify {value} for {parameter}; repo
  value {Y}; reason {…}` when the booklet points outside your range
- `EXTERNAL PDF NEEDED: '{document}' — need to verify {value/table} for {parameter};
  expected {X}, repo {Y}; reason {…}` when another publication is referenced

## Phase 5: Verification

Never trust a reported mismatch without verification. Common false positives: the
parameter only feeds a deprecated code path; the value is inherited from a federal
variable; parameter interactions the auditor did not trace; an `in_effect`/`flat_applies`
boolean disables the path for the target year.

**Routing without reading findings.** The coordinator never reads the Phase 4 report
files, so it cannot enumerate flags and mismatches itself. After Phase 4 completes,
delegate verification-planner: it reads every validator and PDF-audit report and writes
`{RUN_ROOT}/{PREFIX}-review-verification-queue.md` (≤30 lines) — one line per item to
verify, in one of these forms, or a single `NONE` line:

```
XREF | page {XX} | {parameter} | repo {value} | from {report file}
EXT | {document} | {parameter} | expected {X} / repo {Y} | from {report file}
MISMATCH | {parameter} | repo {X} vs PDF {Y} (p.{NN}) | from {report file}
```

The coordinator reads only this queue and spawns the 5A-5D verifiers from its lines.

- **5A** For each CROSS-REFERENCE NEEDED flag, delegate verifier-xref-{N}: read the
  flagged page's screenshot, find the value, report it with confirming context and
  `#page=XX`.
- **5B** For each EXTERNAL PDF NEEDED flag, delegate verifier-ext-{N}: find the document
  (web search), download/extract/render it under `{RUN_ROOT}/{PREFIX}-ext-{N}.*`, and
  report the correct value with URL and exact page.
- **5C** For each MISMATCH, delegate verifier-codepath-{N} (all concurrently): read the
  auditor's reasoning, confirm the repo value, grep ALL usages of the parameter, trace
  the call chain to determine whether the parameter affects the target year's
  computation (deprecated branches, `in_effect` gates, overrides, uprating transforms).
  Verdict: CONFIRMED (with the code-path trace) / REJECTED (with the disproving
  evidence) / INCONCLUSIVE. Each verifier's completion line carries its verdict —
  `DONE — wrote {file} ({verdict})` — so the coordinator routes 5D from completion
  messages without reading any report.
- **5D** For each CONFIRMED or INCONCLUSIVE mismatch (REJECTED ones are dropped and
  noted as "investigated and cleared"), delegate verifier-mismatch-{N} (all
  concurrently): re-render the disputed page at 600 DPI
  (`pdftoppm -png -r 600 -f {PAGE} -l {PAGE} …`), read it carefully, cross-check the
  extracted text, compute uprated values where applicable, and check for logic gaps (a
  correct value whose formula misses a rule). Verdict: CONFIRMED MISMATCH (repo/PDF
  values + page) or FALSE POSITIVE (what the auditor misread), carried in the DONE
  completion line as in 5C. Flag any difference greater than 0.3.
- **5E** If the PR adds `#page=XX` references, delegate verifier-pages: for every
  reference in the diff, read the screenshot at that page and verify the cited value
  actually appears there; if wrong, search nearby pages for the correct page. Common
  pitfall: printed page number used instead of file page number (offset from the
  manifest). Report CORRECT/WRONG per reference with the right page for each WRONG one.

## Phase 6: Consolidation

Delegate consolidation to a single role (consolidator) that reads every finding and
verification file, the context file, the run-state ledger (for metrics), and — in
incremental mode — the prior report. The coordinator reads none of them.

Rules:

1. Merge all findings; deduplicate; when several validators flag the same issue, combine
   at the highest priority.
2. Include a mismatch only if it passed BOTH code-path verification (5C) AND visual
   verification (5D). Note REJECTED mismatches as investigated and cleared.
3. Classify:
   - `CRITICAL (Must Fix)`: regulatory mismatches; value mismatches (code-path confirmed
     + 600 DPI verified); hard-coded legal values; missing or non-corroborating
     references; incorrect section citations; CI failures; incorrect formulas; formula
     variables with zero test coverage; non-functional tests (e.g.,
     `absolute_error_margin >= 1` on boolean outputs).
   - `SHOULD ADDRESS`: pattern violations; missing edge cases for already-tested
     variables; naming conventions; period usage; formatting; missing
     rounding/flooring/capping when the formula is otherwise structurally correct.
   - `SUGGESTION`: documentation, readability, performance, non-blocking improvements.
   - **Rounding rule**: a missing rounding/flooring/capping step in an otherwise correct
     structure is SHOULD ADDRESS, not CRITICAL — unless a test case proves the missing
     step flips an eligibility threshold or categorical outcome.
   - **Microsim default rule**: for defaults that bias population-level outputs (enum
     defaults, bare-input defaults of 0 that zero out a program), REPORT direction and
     magnitude but do NOT prescribe a specific default. Valid remedies: populate the
     variable in the dataset; document the limitation; accept if quantified and small.
     SHOULD ADDRESS by default; CRITICAL only if the bias flips eligibility for a
     meaningful population share or materially shifts aggregate cost.
4. Assign each finding a stable ID: C1, C2… (Critical), A1, A2… (Should Address), S1,
   S2… (Suggestions). Incremental reviews carry prior IDs unchanged, mark each prior
   finding RESOLVED or STILL OPEN, and number new findings after the highest prior ID.
5. Write the FULL report to `{RUN_ROOT}/{PREFIX}-review-full-report.md`. Its Source
   Documents section MUST include `Reviewed head SHA: {PR_HEAD}` (the template renders
   the label bold — consumers match the label and SHA tolerantly, never exact
   punctuation) and `Mode: full` or `Mode: incremental from {PRIOR_HEAD}` so a later
   incremental run can prove its baseline.
6. Write the SHORT summary to `{RUN_ROOT}/{PREFIX}-review-summary.md` (≤20 lines):
   critical count with one-line descriptions; should/suggestion counts; PDF audit tally
   (confirmed correct / mismatches / unmodeled); recommended severity; run metrics
   (elapsed time, delegates spawned, pages rendered, cache hits — from the run-state
   ledger).
7. **Branch status note**: if the context shows the branch behind base, add a
   `### Branch Status` section under Source Documents recommending a rebase and stating
   that staleness did not affect findings. Informational only — never a finding.

Recommended severity: `APPROVE` (no criticals, minor suggestions only), `COMMENT`
(issues, not blocking), `REQUEST_CHANGES` (criticals present).

### Report format

```
## Program Review

### Source Documents
- **PDF**: [Document title](URL#page=1) ({page count} pages)
- **Year**: {year}
- **Scope**: {PR changes only / Full audit}
- **Reviewed head SHA**: {PR_HEAD}
- **Mode**: {full / incremental from PRIOR_HEAD}

### Critical (Must Fix)
1. **[C1] Regulatory mismatch**: [Description] — [file:line] — PDF [p.NN](URL#page=NN)
2. **[C2] Value mismatch**: [Param] repo: X, PDF: Y — [file:line] — PDF [p.NN](URL#page=NN)

### Should Address
1. **[A1] Pattern violation**: Use `add()` instead of manual sum — [file:line]

### Suggestions
1. [S1] Consider adding calculation example in docstring

### PDF Audit Summary
| Category | Count |
|----------|-------|
| Confirmed correct | N |
| Mismatches (code-path confirmed + visually verified) | M |
| Mismatches rejected (code-path cleared) | R |
| Unmodeled items | K |
| Pre-existing issues | P |

### Validation Summary
| Check | Result |
|-------|--------|
| Regulatory Accuracy | X issues |
| Reference Quality | X issues |
| Code Patterns | X issues |
| Formatting (params & vars) | X issues |
| Test Coverage | X gaps |
| PDF Value Audit | X mismatches / Y confirmed |
| CI Status | Passing/Failing |

### Review Severity: {APPROVE / COMMENT / REQUEST_CHANGES}

### Next Steps
To auto-fix issues: run the fix-pr workflow for this PR.
```

## Phase 7: Post or display

Phase 6 consolidation is required before displaying or posting anything — the review is
incomplete until both the full report and the summary exist.

- **Local mode**: read the full report and present it in the conversation (the one
  permitted full-file read, after all delegation is done).
- **GitHub mode**: post without reading:

```bash
gh pr comment $PR_NUMBER --body-file $RUN_ROOT/${PREFIX}-review-full-report.md
```

Finally, if a snapshot worktree was created in Phase 1, remove it —
`git worktree remove --force "$SNAPSHOT"` — even when earlier phases failed. Report
artifacts under `RUN_ROOT` stay.

End with a short summary and mention that fixes can be applied with the fix-pr workflow.

## Global rules

1. **READ-ONLY**: never edit files, never switch branches or worktrees; the only
   worktree the run may create or remove is its own detached `PR_HEAD` snapshot under
   `RUN_ROOT`, and all repository file reads happen under `SNAPSHOT`.
2. **PDF by default**: acquisition runs unless `--skip-pdf`; no PDF found → code-only
   review, noted in the report.
3. **Render every page**: render collected PDFs completely at the requested DPI (300
   default, 600 with `--600dpi`); cache by checksum + DPI; verify the complete page
   sequence before reuse; re-render disputed pages at 600 DPI for verification.
4. **Two-stage mismatch verification**: every reported mismatch passes BOTH code-path
   (5C) and visual (5D) verification before it may appear in the report.
5. **Trace code paths**: a mismatch is real only if the parameter is reachable in the
   target year's computation.
6. **Delegates stay in scope**: assigned pages only; cross-references and external PDFs
   get their own verification roles.
7. **Always cite pages**: every finding includes `#page=XX` (file page); single-page
   PDFs excepted.
8. **Error margin**: flag any repo-vs-PDF difference greater than 0.3.
9. **Context protection**: large content never enters the coordinator's context.
10. **Multiple PDFs**: up to 5; the manifest maps PDFs to topics.
11. **Changelog**: every PR needs a towncrier fragment at
    `changelog.d/<branch>.<type>.md`.
12. **Incremental integrity**: an incremental report must record its reviewed head SHA;
    fall back to a full review when ancestry or cached source integrity cannot be
    proven.
13. **Metrics**: record phase durations, delegates spawned, pages rendered, cache hits,
    and full-vs-incremental scope in the run state and final summary.
