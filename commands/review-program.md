---
description: Review any PR — code validation + PDF audit in one pass (read-only, no code changes)
---

# Reviewing PR: $ARGUMENTS

**READ-ONLY MODE**: This command analyzes the PR and posts a combined review to GitHub WITHOUT making any code changes. Use `/fix-pr` to apply fixes.

**Works for any PR type**: state programs, federal parameters, infrastructure, refactoring, API changes, etc. The review adapts based on what the PR changes — PDF audit only runs when source documents are relevant.

## YOUR ROLE: ORCHESTRATOR ONLY

**CRITICAL — Context Window Protection:**
- You are an orchestrator. You do NOT read diffs, code files, PDF data, or agent finding files.
- ALL information-gathering work is delegated to agents.
- You only read files marked as short summaries (≤30 lines each).
- ALL data flows through files on disk. Agent prompts reference file paths, never paste content.

**You MUST NOT:**
- Read the PR diff (`{RUN_ROOT}/{PREFIX}-review-diff.txt`)
- Read parameter YAML files or variable .py files
- Read PDF text files or PDF screenshots
- Read individual agent finding files (regulatory, references, code, tests, pdf-audit)
- Re-render PDFs at 600 DPI yourself
- Grep through diffs or code files

**You DO:**
- Parse arguments and resolve PR number
- Run `gh` commands for small structured JSON (pr view, pr checks)
- Save diff to disk for agents: `gh pr diff > {RUN_ROOT}/{PREFIX}-review-diff.txt`
- Read SHORT summary files only: context (≤25 lines), manifest (≤30 lines), summary (≤20 lines)
- Spawn agents (in parallel where possible)
- Post the final report using `gh pr comment --body-file`

## Agent Completion Contract

**Silent-finish prevention — every agent in this command obeys this contract.** Each agent prompt below includes a short reminder line that points back here. Do not strip these reminders.

**Agent side (applies to every agent spawned in this command):**
- After writing your output file(s), your task is COMPLETE.
- Your FINAL message MUST be a one-line confirmation:
  `DONE — wrote {RUN_ROOT}/{PREFIX}-...md ({brief stat, e.g., "5 findings", "no issues", "manifest written"})`
- Do NOT continue working after the output file is written.
- Do NOT go idle without returning the confirmation line — silent finishes block the orchestrator.

**Orchestrator side (Main Claude):**
- When you spawn background agents (`run_in_background: true`), the harness notifies you on completion. Wait for all notifications in a batch before reading output files.
- Do NOT sleep, poll, or proactively ask the user about agent progress.
- Fallback: if you have NOT received a completion notification for one agent in a parallel batch but the rest of the batch is done AND that agent's expected output file exists and is well-formed, treat it as stalled — read the file and proceed.

## Arguments

`$ARGUMENTS` should contain:
- **PR number or search text** (optional — prompts if omitted) — e.g., `7130` or `"Arkansas TANF"`
- **PDF URL** (optional) — link to the official source PDF. If omitted, auto-discovered.
- **Options**:
  - `--local` — show findings locally only, skip GitHub posting
  - `--local-diff` — implies `--local`; reads diff from `git diff` instead of `gh pr diff` (for reviewing unpushed work)
  - `--full` — audit ALL implemented parameters, not just PR diff
  - `--skip-pdf` — skip PDF acquisition and audit; run code validators only (for infrastructure/refactoring PRs with no source document)
  - `--600dpi` — render PDFs at 600 DPI instead of 300 DPI (for scanned docs or dense tables)
  - `--resume` — reuse valid artifacts from an interrupted review
  - `--incremental REPORT` — review changes and unresolved findings since a prior full
    report; reuse its source/PDF evidence when policy values and references are unchanged

**Examples:**
```
/review-program 7130
/review-program 7130 --full
/review-program 7130 --local
/review-program 7130 --local-diff --full
/review-program 7130 --skip-pdf
/review-program 7130 https://state.gov/manual.pdf
/review-program 7130 https://state.gov/manual.pdf --full --600dpi
/review-program 7130 --resume
/review-program 7130 --incremental {RUN_ROOT}/my-branch-review-full-report.md
```

---

## Phase 0: Parse Arguments & Ask Posting Mode

### Step 0: Resolve Worktree Namespace and File Prefix

Derive a stable namespace from the absolute worktree root, then add the branch prefix:
```bash
WORKTREE_ROOT=$(git rev-parse --show-toplevel)
WORKTREE_ID=$(printf '%s' "$WORKTREE_ROOT" | git hash-object --stdin | cut -c1-12)
RUN_ROOT="/tmp/policyengine-command-runs/$WORKTREE_ID"
mkdir -p "$RUN_ROOT"
PREFIX=$(git branch --show-current | tr '/' '-')
PREFIX=${PREFIX:-review-program}  # fallback if detached HEAD
```

All runtime files use `{RUN_ROOT}/{PREFIX}-...` paths. `WORKTREE_ROOT`, not the shared Git
common directory or branch name, is the isolation boundary. Record the root and ID in the
run state, substitute `{RUN_ROOT}` and `{WORKTREE_ID}` in every agent prompt, and never
fall back to process-global `/tmp/{PREFIX}-...` paths.

This command is read-only across the whole worktree set: never switch or detach any
worktree, and never read uncommitted files from a different worktree path. Standard mode
reviews fetched SHAs; `--local-diff` reviews only `WORKTREE_ROOT`.

### Step 0A: Parse Arguments & Initialize Run

First parse the arguments:

```
Parse $ARGUMENTS:
- PR_ARG: first non-flag, non-URL argument (number or search text)
- PDF_URL: first URL argument (may be empty — will auto-discover in Phase 2)
- LOCAL_ONLY: true if --local or --local-diff flag present
- LOCAL_DIFF: true if --local-diff flag present (implies LOCAL_ONLY)
- FULL_AUDIT: true if --full flag present
- SKIP_PDF: true if --skip-pdf flag present
- DPI: 600 if --600dpi, else 300
- RESUME: true if --resume
- INCREMENTAL_REPORT: path following --incremental, otherwise empty
```

Use `{RUN_ROOT}/{PREFIX}-review-run-state.md` to record `WORKTREE_ROOT`, `WORKTREE_ID`,
arguments, PR/head SHA, completed phases, artifact paths, source URL/checksums, and elapsed time. Before an incremental run,
copy the supplied report to `{RUN_ROOT}/{PREFIX}-review-prior-report.md` so the canonical output
path can be safely replaced.

On a fresh full review, clean prior report artifacts. With `--resume` or `--incremental`,
preserve artifacts and validate them against the run state. Refuse artifacts recorded by
another worktree. Invalidate an artifact and its
dependents when the PR head, source checksum, or review scope it depends on changed.

`--resume` is also valid after a *completed* run whose PR head has since changed (e.g.,
encode Phase 6 re-reviews after fixes): the head change invalidates the analysis
artifacts (diff, context, findings), which re-run in full, while checksum-valid PDF
downloads and rendered pages are reused. A completed ledger with an unchanged head means
there is nothing to redo — report that instead of re-reviewing.

```bash
if [ "$RESUME" != "true" ] && [ -z "$INCREMENTAL_REPORT" ]; then
  rm -f {RUN_ROOT}/{PREFIX}-review-*.md {RUN_ROOT}/{PREFIX}-review-pdf-*.{pdf,txt,png} {RUN_ROOT}/{PREFIX}-600dpi-*.png {RUN_ROOT}/{PREFIX}-ext-*.{pdf,txt,png,md}
fi
if [ -n "$INCREMENTAL_REPORT" ]; then
  cp "$INCREMENTAL_REPORT" {RUN_ROOT}/{PREFIX}-review-prior-report.md
fi
```

TeamCreate(`{WORKTREE_ID}-{PREFIX}-review`)

**Resolve PR number:**
```bash
# If argument is a number, use it directly
if [[ "$PR_ARG" =~ ^[0-9]+$ ]]; then
    PR_NUMBER=$PR_ARG
# Otherwise, search for PR by description/title
else
    PR_NUMBER=$(gh pr list --search "$PR_ARG" --json number,title --jq '.[0].number')
fi
```

**If the search returns no PR**: report that clearly and ask the user for another PR
number or title — do not guess or stop.

**If no PR argument provided**: Use `AskUserQuestion` to ask for the PR number or title.
Ask for the PR, not the program — the state and program are inferred from the selected
PR's diff in Phase 1.

### Step 0B: Determine Posting Mode

**If `--local` flag**: Skip prompt, proceed in local-only mode.

**If no flag**: Use `AskUserQuestion`:
```
Question: "Post review findings to GitHub when complete?"
Options:
  - "Yes, post to GitHub" (default)
  - "No, show locally only"
```

---

## Phase 1: Gather PR Context + CI Status

### Step 1A: Main Claude runs small structured commands only

```bash
gh pr view $PR_NUMBER --json title,body,author,baseRefName,headRefName
gh pr checks $PR_NUMBER
BASE_BRANCH=$(gh pr view $PR_NUMBER --json baseRefName --jq '.baseRefName')
```

**Check branch staleness against base** — required so the review is strictly scoped to what the PR actually changed.

**READ-ONLY CONTRACT: `/review-program` MUST NOT change the user's working tree or checked-out branch.** Do NOT use `gh pr checkout`, `git checkout`, `git switch`, or any command that mutates HEAD. Compute everything against fetched refs.

**Both modes resolve to two SHAs — `BASE_SHA` and `PR_HEAD` — and use those directly.** Do NOT compute against `origin/$BASE_BRANCH`: that ref may not be updated by `git fetch origin <branch>` if the user has a non-standard remote config, a shallow clone, or recent `--no-write-fetch-head` operations. Capturing the SHA from `FETCH_HEAD` immediately after each fetch is robust regardless of remote-tracking state.

#### Standard mode (PR exists on GitHub)

```bash
# Fail loudly if either fetch fails — a silent failure would scope the review to
# stale local refs or the wrong HEAD.
set -e
git fetch origin "$BASE_BRANCH"
BASE_SHA=$(git rev-parse FETCH_HEAD)
git fetch origin "pull/$PR_NUMBER/head"
PR_HEAD=$(git rev-parse FETCH_HEAD)
set +e

MERGE_BASE=$(git merge-base "$BASE_SHA" "$PR_HEAD")
BEHIND=$(git rev-list --count "$PR_HEAD..$BASE_SHA")
AHEAD=$(git rev-list --count "$BASE_SHA..$PR_HEAD")

echo "PR is $AHEAD commit(s) ahead, $BEHIND commit(s) behind $BASE_BRANCH"
echo "BASE_SHA: $BASE_SHA   PR_HEAD: $PR_HEAD   MERGE_BASE: $MERGE_BASE"
```

#### `--local-diff` mode (review the user's local branch without pushing)

In this mode the currently checked-out branch is the PR head — the user opted in via `--local-diff`. Still do NOT switch branches; use `HEAD` as-is.

```bash
set -e
git fetch origin "$BASE_BRANCH"
BASE_SHA=$(git rev-parse FETCH_HEAD)
set +e

PR_HEAD=$(git rev-parse HEAD)
MERGE_BASE=$(git merge-base "$BASE_SHA" "$PR_HEAD")
BEHIND=$(git rev-list --count "$PR_HEAD..$BASE_SHA")
AHEAD=$(git rev-list --count "$BASE_SHA..$PR_HEAD")
```

**Save diff to disk — always use explicit merge-base** so the diff contains ONLY what the PR actually changed (no stale-branch artifacts):

```bash
# Standard mode: diff from merge-base to the fetched PR head (no working-tree change)
git diff "$MERGE_BASE".."$PR_HEAD" > {RUN_ROOT}/{PREFIX}-review-diff.txt

# --local-diff mode: same approach; PR_HEAD == HEAD here
```

**Incremental mode:** read the prior reviewed head SHA from
`{RUN_ROOT}/{PREFIX}-review-prior-report.md`. Verify it is an ancestor of `PR_HEAD`, then write
only `git diff "$PRIOR_HEAD".."$PR_HEAD"` to the diff file. If it is not an ancestor, or
the prior report lacks its head SHA, fall back to a full merge-base diff and explain why.
The unresolved findings in the prior report remain in scope even when their original file
did not change. Track them by their stable finding IDs (C1/A1/S1…) from the prior report.

If `git fetch` failed above, STOP and surface the error to the user. Do not continue with a possibly-stale or wrong-HEAD diff.

**Main Claude does NOT read the diff file.** It only saves it to disk for agents.

### Step 1A.5: Staleness Notice (friendly reminder — not blocking)

**If `BEHIND > 0`**, print a one-line friendly reminder to the user and continue automatically. Do NOT ask a question or block the review:

```
⚠ Friendly reminder: PR branch is {BEHIND} commit(s) behind {BASE_BRANCH}. Consider rebasing soon (`git pull --rebase origin {BASE_BRANCH}`). This review is scoped strictly to the PR's actual changes (merge-base diff), so the staleness will NOT cause false-positive findings here.
```

The staleness count is recorded for the final report (under a "Branch Status" note, not as a critical issue).

**If `BEHIND == 0`**: skip this step silently.

### Step 1B: Delegate diff analysis to agent (PARALLEL with Phase 2)

Spawn a `general-purpose` agent to analyze the diff and write a short context file.
Must be `general-purpose` (not Explore) because it needs the Write tool to save the summary to disk.

```
subagent_type: "general-purpose"
team_name: "{WORKTREE_ID}-{PREFIX}-review"
name: "context-analyzer"
run_in_background: true

"Analyze the PR diff at {RUN_ROOT}/{PREFIX}-review-diff.txt and write a context summary.

CONTEXT: The diff at {RUN_ROOT}/{PREFIX}-review-diff.txt is the merge-base diff — it contains
ONLY what this PR actually changed (no stale-branch artifacts). Trust the file list you
derive from this diff as the AUTHORITATIVE scope. Do not include files that exist in the
branch but are not in this diff.

TASK:
1. Read {RUN_ROOT}/{PREFIX}-review-diff.txt
2. Write {RUN_ROOT}/{PREFIX}-review-context.md (MAX 25 LINES):

   ## PR Context
   - Scope: {state program / federal parameter / infrastructure / API / frontend / other}
   - State: {abbreviation} ({full name}) — or 'N/A' if not state-specific
   - Program area: {tax / TANF / SNAP / Medicaid / etc.} — or 'N/A'
   - Year: {year being updated} — or 'N/A'
   - PR type: {new program / bug fix / enhancement / parameter update / refactor / infrastructure}
   - CI status: {from gh pr checks output if available}
   - Branch staleness: {AHEAD} ahead, {BEHIND} behind {BASE_BRANCH} (from orchestrator)
   - Has source documents: {yes / no} — true if YAML refs contain PDF URLs or PR body links to docs
   ## Files Changed (PR scope — DO NOT add files outside this list)
   - Parameters: {list of YAML file paths from diff, or 'none'}
   - Variables: {list of .py file paths from diff, or 'none'}
   - Tests: {list of test file paths from diff, or 'none'}
   - Other: {list of other changed files in diff, if any}
   ## Topics
   - {topic 1}: {file paths}
   - {topic 2}: {file paths}
   ## PDF References Found
   - {any PDF URLs found in PR body or YAML reference fields, or 'none'}

Keep it CONCISE — paths and classifications only. Max 25 lines.

Completion: after writing {RUN_ROOT}/{PREFIX}-review-context.md, return `DONE — wrote {RUN_ROOT}/{PREFIX}-review-context.md` as your final message."
```

### Step 1C: Read context summary

After the context-analyzer completes, read ONLY `{RUN_ROOT}/{PREFIX}-review-context.md` (max 25 lines). This gives you:
- Scope and PR type — determines which agents to spawn
- State, program, year for agent prompts (if applicable)
- File lists for agent assignments
- Topics for Phase 3 splitting
- PDF URLs found (passed to pdf-collector)
- Whether source documents exist (determines PDF phase)

**Scope-based agent selection:**
- **State/federal program PRs**: Run all code validators + PDF audit (if source docs exist)
- **Infrastructure/API/frontend PRs**: Run code validators only (skip PDF phase via `--skip-pdf` logic). Regulatory accuracy and reference validators are skipped since there are no parameters.
- **Mixed PRs**: Run all agents but only assign program-related files to regulatory/reference validators

---

## Phase 2: PDF Acquisition

**Skip this phase if `--skip-pdf` OR if context summary says `Has source documents: no` and `Scope: infrastructure/API/frontend`.** Write a manifest stub instead:
```bash
echo "## PDF Manifest\n### No PDF (skipped)\n- Reason: {--skip-pdf flag / no source documents for this PR type}; code-only review" > {RUN_ROOT}/{PREFIX}-review-pdf-manifest.md
```

**Incremental reuse:** if the prior report's source manifest exists and the incremental
diff does not change parameter values, formulas, reference links, or source documents,
reuse the manifest and skip acquisition/audit. Code and test validators still run on the
incremental files. If any of those semantic inputs changed, reacquire only changed or
missing sources.

**Otherwise, PDF acquisition runs.** This is delegated entirely to the document-collector agent to protect Main Claude's context window.

### Spawn PDF Collector

```
subagent_type: "complete:country-models:document-collector"
team_name: "{WORKTREE_ID}-{PREFIX}-review"
name: "pdf-collector"
run_in_background: true
```

**Prompt:**
```
"You are finding official source PDFs for a program review.

STATE: {State} ({st})
PROGRAM AREA: {program area from Phase 1}
YEAR: {year from Phase 1}
USER-PROVIDED PDF URL: {PDF_URL or 'none — auto-discover'}

TASK:
1. If a PDF URL was provided, download and validate it
2. If no URL provided:
   a. Check PR description and YAML references (read {RUN_ROOT}/{PREFIX}-review-diff.txt)
   b. WebSearch for the official source document
   c. Download and validate (correct state, year, document type)
3. For EACH PDF found (up to 5):
   a. Download: curl -L -o {RUN_ROOT}/{PREFIX}-review-pdf-{N}.pdf 'URL'
   b. Get page count: pdfinfo {RUN_ROOT}/{PREFIX}-review-pdf-{N}.pdf | grep Pages
   c. Extract text: pdftotext {RUN_ROOT}/{PREFIX}-review-pdf-{N}.pdf {RUN_ROOT}/{PREFIX}-review-pdf-{N}.txt
   d. Render every page at {DPI} DPI: `pdftoppm -png -r {DPI} {RUN_ROOT}/{PREFIX}-review-pdf-{N}.pdf {RUN_ROOT}/{PREFIX}-review-pdf-{N}-page`
   e. Verify the rendered page count matches the PDF page count
   f. Determine page offset (cover/TOC pages before content page 1)
4. Check for supplementary documents referenced by the main booklet
5. Write manifest to {RUN_ROOT}/{PREFIX}-review-pdf-manifest.md (MAX 30 LINES):

   ## PDF Manifest
   ### PDF 1: [title]
   - URL: [url]
   - Path: {RUN_ROOT}/{PREFIX}-review-pdf-1.pdf
   - Pages: [count], offset: [N] preliminary pages
   - Text: {RUN_ROOT}/{PREFIX}-review-pdf-1.txt
   - Screenshots: {RUN_ROOT}/{PREFIX}-review-pdf-1-page-{NN}.png
   - Topics covered: [list of topics and page ranges]
   ### PDF 2: [title] (if applicable)
   ...
   ### No PDF Found (if applicable)
   - Reason: [why no source was found]

If no PDF is found, write that in the manifest and the review will continue with code-only validators.

Completion: after writing {RUN_ROOT}/{PREFIX}-review-pdf-manifest.md, return `DONE — wrote {RUN_ROOT}/{PREFIX}-review-pdf-manifest.md` as your final message."
```

### Read Manifest

After the pdf-collector completes, read ONLY `{RUN_ROOT}/{PREFIX}-review-pdf-manifest.md` (max 30 lines). This tells you:
- Which PDFs were found (if any)
- **Total page count per PDF** — used in Phase 3 to decide how many audit agents to spawn
- File paths for agent prompts
- Topic-to-page mappings for Phase 3

---

## Phase 3: Map Files to Topics & Plan Agent Split

Using the context summary (from Phase 1) and the PDF manifest (from Phase 2), plan the parallel agent split. **Main Claude reads only these two short files** — no diff, no code, no PDFs.

### Identify repo files to review

**If `--full` flag**: The context-analyzer noted the state/program path. Spawn a quick `general-purpose` agent (needs Write tool) to list all files under that path and write to `{RUN_ROOT}/{PREFIX}-review-full-filelist.md` (max 30 lines). Read only that file.

**If no `--full` flag**: Use the file lists from `{RUN_ROOT}/{PREFIX}-review-context.md`.

### Plan agent topic split

Map changed files to audit topics and assign PDF page ranges:

| Agent Topic | Repo Files | PDF Pages |
|-------------|-----------|-----------|
| Eligibility & Income | `eligibility/`, `income/` | pp. X-Y from PDF N |
| Benefits & Standards | `benefits/`, `standards/` | pp. A-B from PDF N |
| Rates & Brackets (tax) | `rates/` | pp. C-D from PDF N |
| Credits (tax) | `credits/` | pp. E-F from PDF N |
| Deductions (tax) | `deductions/` | pp. G-H from PDF N |

### Large PDF splitting rule

**Main Claude decides agent count** using ONLY the page count from the manifest (a single number — no PDF content is read). Each PDF audit agent should read **at most ~40 pages**. Split by topic first, then by page count:

| Total PDF pages | Min agents | Splitting strategy |
|-----------------|------------|-------------------|
| ≤40 | 1-2 | Split by topic only |
| 41-80 | 2-3 | Split by topic; subdivide any topic >40 pages |
| 81-150 | 3-4 | Split by topic; subdivide large topics into ~30-40 page chunks |
| 151+ | 4-5 | Split by topic AND by page range within topics |

**Example**: A 200-page tax instruction booklet with 3 topics (deductions pp.10-60, rates pp.61-90, credits pp.91-180):
- Agent 1: Deductions pp.10-60 (50 pages → split further)
  - Agent 1a: Deductions pp.10-35
  - Agent 1b: Deductions pp.36-60
- Agent 2: Rates pp.61-90 (30 pages, fine as-is)
- Agent 3: Credits pp.91-180 (90 pages → split further)
  - Agent 3a: Credits pp.91-135
  - Agent 3b: Credits pp.136-180

This yields 5 agents, all running in parallel, none overloaded.

When subdividing a topic, each sub-agent gets:
- Its page range from the same PDF
- The SAME repo file list (so both can cross-reference the same parameters)
- Instructions to only report on values found within their page range

Before spawning PDF audit agents, verify that the complete rendered page sequence exists.
Reuse it only when the PDF checksum and DPI match the manifest. If any page is missing or
stale, rerender the full PDF. Audit agents still read only their assigned ranges to bound
context, but every page remains available for cross-reference and citation verification.

---

## Phase 4: Parallel Execution

Spawn ALL agents in a **single message** for maximum parallelism. Two groups run simultaneously:
- **Code validators** (2-4 plugin agents, depending on scope) — work on the repo code
- **PDF audit agents** (2-5 general-purpose agents, if PDF available) — work on PDF screenshots

**Scope-based agent selection:**
- **Program PRs** (state or federal): All 4 code validators + PDF audit agents
- **Infrastructure/API/frontend PRs**: Only Validator 3 (code patterns) + Validator 4 (test coverage). Skip Validator 1 (regulatory) and Validator 2 (references) since there are no parameters.
- **Mixed PRs**: All 4 validators, but Validators 1-2 only review parameter/variable files

**Incremental mode:** validators receive the incremental file list plus unresolved prior
findings. Do not reopen findings already recorded as resolved unless a changed file could
regress them. Run PDF audit agents only for changed parameter/formula/reference topics;
reuse prior verified findings for untouched topics.

### Group A: Code Validators

#### Validator 1: Regulatory Accuracy (Critical)

**Skip for infrastructure/API/frontend PRs.**

```
subagent_type: "complete:country-models:program-reviewer"
team_name: "{WORKTREE_ID}-{PREFIX}-review"
name: "regulatory-reviewer"
run_in_background: true
```

**Prompt:**
```
"Review {State} {PROGRAM} PR #{PR_NUMBER} for regulatory accuracy.
Load skills: /policyengine-variable-patterns, /policyengine-parameter-patterns.
- Research regulations FIRST (independent of code)
- Compare implementation to legal requirements
- Identify discrepancies between code and law
- Flag missing program components
- Check for reinvented variables: PolicyEngine-US has hundreds of existing variables for
  common concepts (fpg, smi, tanf_fpg, is_tanf_enrolled, ssi, tanf_gross_earned_income,
  snap_gross_income, etc.). If the PR creates a new variable for a concept that already
  exists in the codebase, flag it as CRITICAL — the PR should reuse the existing variable.
  Grep the codebase to verify before flagging.
- Write findings to {RUN_ROOT}/{PREFIX}-review-regulatory.md

KEY QUESTION: Does this implementation correctly reflect the law?

Files to review: {list from Phase 3}
PDF text available at: {paths from manifest, for cross-reference only}

Completion: after writing {RUN_ROOT}/{PREFIX}-review-regulatory.md, return `DONE — wrote {RUN_ROOT}/{PREFIX}-review-regulatory.md` as your final message."
```

#### Validator 2: Reference Quality (Critical)

**Skip for infrastructure/API/frontend PRs.**

```
subagent_type: "complete:reference-validator"
team_name: "{WORKTREE_ID}-{PREFIX}-review"
name: "reference-checker"
run_in_background: true
```

**Prompt:**
```
"Validate references in {State} {PROGRAM} PR #{PR_NUMBER}.
Load skills: /policyengine-parameter-patterns.
- Find parameters missing references
- Check reference format (page numbers, detailed sections)
- Verify references corroborate values
- Check jurisdiction match (federal vs state sources)
- Verify #page=XX is the FILE page number, not the printed page number
  (use PDF page offset from manifest to check)
- Flag session law refs that should cite permanent statutes
- Write findings to {RUN_ROOT}/{PREFIX}-review-references.md

KEY QUESTION: Can every value be traced to an authoritative source?

Files to review: {list from Phase 3}
PDF manifest: {RUN_ROOT}/{PREFIX}-review-pdf-manifest.md

Completion: after writing {RUN_ROOT}/{PREFIX}-review-references.md, return `DONE — wrote {RUN_ROOT}/{PREFIX}-review-references.md` as your final message."
```

#### Validator 3: Code Patterns (Critical + Should)

```
subagent_type: "complete:country-models:implementation-validator"
team_name: "{WORKTREE_ID}-{PREFIX}-review"
name: "code-validator"
run_in_background: true
```

**Prompt:**
```
"Validate code patterns in {State} {PROGRAM} PR #{PR_NUMBER}.

MODE: Mode B — code-pattern audit (READ-ONLY).
Run ONLY Phase 4 of the implementation-validator. Do NOT run Phases 1–3.
Do NOT edit any source files — report findings only.

Load skills: /policyengine-parameter-patterns, /policyengine-variable-patterns,
  /policyengine-code-organization, /policyengine-code-style, /policyengine-aggregation,
  /policyengine-period-patterns.

Scan every changed file in this PR for the ten Phase 4 categories:
1. Hard-coded values in formulas (CRITICAL)
2. Variable naming conventions + duplicate variables (CRITICAL if duplicate)
3. Aggregation patterns (adds, add(), add() > 0)
4. Period usage (incl. mid-year tests using next January, not effective month)
5. Reference format (variables: bare strings; parameters: title/href dicts with page in href)
6. Parameter formatting (description, label, values)
7. TODO / placeholder detection (CRITICAL)
8. Changelog fragment at changelog.d/<branch>.<type>.md (CRITICAL if missing)
9. Boolean toggle date alignment (CRITICAL)
10. Entity-level mismatches (CRITICAL)

Write findings to {RUN_ROOT}/{PREFIX}-review-code.md grouped by severity
(CRITICAL / SHOULD ADDRESS / SUGGESTION), each with file:line.

KEY QUESTION: Does the code follow PolicyEngine standards?

Files to review: {list from Phase 3}

Completion: after writing {RUN_ROOT}/{PREFIX}-review-code.md, return `DONE — wrote {RUN_ROOT}/{PREFIX}-review-code.md ({critical} CRITICAL, {should} SHOULD ADDRESS, {suggestion} SUGGESTION)` as your final message."
```

#### Validator 4: Test Coverage (Should)

```
subagent_type: "complete:country-models:edge-case-generator"
team_name: "{WORKTREE_ID}-{PREFIX}-review"
name: "edge-case-checker"
run_in_background: true
```

**Prompt:**
```
"Analyze test coverage for {State} {PROGRAM} PR #{PR_NUMBER}.
Load skills: /policyengine-testing-patterns, /policyengine-period-patterns.
- Identify missing boundary tests
- Find untested edge cases
- Check parameter combinations not tested
- Verify integration test exists
- Write findings to {RUN_ROOT}/{PREFIX}-review-tests.md

KEY QUESTION: Are the important scenarios tested?

Files to review: {list from Phase 3}

Completion: after writing {RUN_ROOT}/{PREFIX}-review-tests.md, return `DONE — wrote {RUN_ROOT}/{PREFIX}-review-tests.md` as your final message."
```

### Group B: PDF Audit Agents

**Skip this group if PDF manifest says "No PDF Found".**

Spawn 2-5 `general-purpose` agents, one per topic from Phase 3. Each agent gets assigned PDF pages and repo files.

```
subagent_type: "general-purpose"
team_name: "{WORKTREE_ID}-{PREFIX}-review"
name: "pdf-audit-{topic}"
run_in_background: true
```

**PDF Audit Agent Prompt Template:**
```
"You are auditing {State}'s {year} {program} parameters against the official source document.
Load skills: /policyengine-parameter-patterns, /policyengine-period-patterns.

TASK: Report only — do NOT edit any files.

1. Read the PDF page screenshots at {screenshot path pattern} for pages {X}-{Y}
   IMPORTANT: Only read your assigned pages ({X}-{Y}). Do NOT read pages outside your range.

2. Read all parameter files under: {list of YAML paths}

3. Read all variable files under: {list of Python paths}

4. For each parameter/variable, compare the repo value against the PDF:
   - Check numerical values (rates, thresholds, amounts, brackets)
   - Check effective dates ({year} vs earlier years)
   - Check filing status / family size variations
   - Check uprated values — if a parameter uses uprating, compute the uprated value
     and compare against the PDF. If they differ, flag it.
   - Note any 'New for {year}' changes

5. Report to {RUN_ROOT}/{PREFIX}-review-pdf-{topic}.md:
   a. MATCHES: Parameters that are correct (count + brief list)
   b. MISMATCHES: Parameters where repo differs from PDF (cite both values and PDF page)
   c. MISSING FROM REPO: Things in the PDF we don't model
   d. MISSING FROM PDF: Things in the repo not found in this PDF section

6. If the booklet says 'refer to page XX' and that page is OUTSIDE your assigned range:
   CROSS-REFERENCE NEEDED: page {XX} — need to verify [what value] for [which parameter].
   Repo value: [Y], reason: [why you need this page].

7. If a parameter file references another PDF, or the booklet says 'See [other publication]':
   EXTERNAL PDF NEEDED: '[Document name]' — need to verify [what value/table] for [which parameter].
   Expected value: [X], repo value: [Y], reason: [why you suspect a mismatch].

Do NOT read pages outside your assigned range.
Do NOT guess values you haven't seen. Flag it and move on.

Completion: after writing {RUN_ROOT}/{PREFIX}-review-pdf-{topic}.md, return `DONE — wrote {RUN_ROOT}/{PREFIX}-review-pdf-{topic}.md` as your final message."
```

---

## Phase 5: Verification

After all Phase 4 agents complete, handle flags and verify mismatches. Steps 5A-5B handle flags in parallel. Step 5C filters mismatches via code-path tracing. Step 5D visually confirms only surviving mismatches. Step 5E checks page numbers.

### Step 5A: Handle CROSS-REFERENCE NEEDED Flags

For each cross-reference flag from PDF audit agents, spawn a **verification agent**:

```
subagent_type: "general-purpose"
team_name: "{WORKTREE_ID}-{PREFIX}-review"
name: "verifier-xref-{N}"
run_in_background: true
```

**Prompt:**
```
"You are verifying a cross-reference for a program review.

TASK: Read a specific page and report what you find. Report only — do NOT edit any files.

WHAT TO VERIFY:
- Page to read: {screenshot path for page XX}
- Value in question: {from the flag}
- Repo value: {from the flag}
- Context: {from the flag}

STEPS:
1. Read the page screenshot at the path above
2. Find the specific value requested
3. Report to {RUN_ROOT}/{PREFIX}-review-xref-{N}.md:
   - The value you see on that page
   - What confirms it (table name, worksheet line, etc.)
   - PDF page number for citation: #page=XX

Completion: after writing {RUN_ROOT}/{PREFIX}-review-xref-{N}.md, return `DONE — wrote {RUN_ROOT}/{PREFIX}-review-xref-{N}.md` as your final message."
```

### Step 5B: Handle EXTERNAL PDF NEEDED Flags

For each external PDF flag, spawn a **verification agent**:

```
subagent_type: "general-purpose"
team_name: "{WORKTREE_ID}-{PREFIX}-review"
name: "verifier-ext-{N}"
run_in_background: true
```

**Prompt:**
```
"You are verifying a value from an external PDF for a program review.

TASK: Find, download, and verify the following. Report only — do NOT edit any files.

WHAT TO VERIFY:
- Document: {document name from the flag}
- State revenue/agency site: {e.g., state.gov/dss}
- Value in question: {from the flag}
- Repo value: {from the flag}
- Reason: {from the flag}

STEPS:
1. WebSearch for the document
2. Download: curl -L -o {RUN_ROOT}/{PREFIX}-ext-{N}.pdf 'URL'
3. Extract text: pdftotext {RUN_ROOT}/{PREFIX}-ext-{N}.pdf {RUN_ROOT}/{PREFIX}-ext-{N}.txt
4. Render at {DPI} DPI: pdftoppm -png -r {DPI} {RUN_ROOT}/{PREFIX}-ext-{N}.pdf {RUN_ROOT}/{PREFIX}-ext-{N}-page
5. Read text and/or screenshots to find the value
6. Report to {RUN_ROOT}/{PREFIX}-review-ext-{N}.md:
   - PDF URL (for reference link with #page=XX)
   - Correct value with exact PDF page number
   - Confirmation details

Completion: after writing {RUN_ROOT}/{PREFIX}-review-ext-{N}.md, return `DONE — wrote {RUN_ROOT}/{PREFIX}-review-ext-{N}.md` as your final message."
```

### Step 5C: Code-Path Verification of Mismatches (CRITICAL)

**Never trust agent-reported mismatches without verification.** Agents commonly produce false positives because:
- The parameter is only used in a deprecated code path (e.g., pre-2023)
- The value is automatically inherited from a federal variable
- The parameter interacts with other parameters in a way the audit agent didn't trace
- A boolean flag (`in_effect`, `flat_applies`) disables the code path for the target year

**For each MISMATCH** reported by PDF audit agents, spawn a **code-path verifier**:

```
subagent_type: "general-purpose"
team_name: "{WORKTREE_ID}-{PREFIX}-review"
name: "verifier-codepath-{N}"
run_in_background: true
```

**Prompt:**
```
"You are a code-path verifier for a program review. An audit agent reported a MISMATCH
and you must determine if it's a real issue or a false positive.
Load skills: /policyengine-variable-patterns, /policyengine-parameter-patterns,
  /policyengine-period-patterns, /policyengine-code-style.

REPORTED MISMATCH:
- Parameter: {parameter name and file path}
- Repo value: {value from audit agent report}
- Agent-reported PDF value: {value from audit agent report}
- Audit agent's reasoning: {summary from their report file {RUN_ROOT}/{PREFIX}-review-pdf-{topic}.md}
- Target year: {year from Phase 1}

YOUR TASK:
1. Read the audit agent's report at {RUN_ROOT}/{PREFIX}-review-pdf-{topic}.md to understand
   their full reasoning for this mismatch
2. Read the parameter file to confirm the repo value
3. Grep for ALL usages of this parameter across the codebase
4. For each variable that references this parameter, trace the call chain:
   - Is it called from the {year}+ code path?
   - Or only from a deprecated/disabled path?
   - Is the code path gated by an in_effect or flat_applies boolean that is
     false for {year}?
5. Check if the parameter's value actually affects the target year's computation
   by following the execution flow from the top-level variable down to this parameter
6. Check if the value might be correct due to interaction with other parameters
   (e.g., a flag that disables the feature, a separate variable that overrides it,
   an uprating mechanism that transforms the stored value)

VERDICT must be one of:
- CONFIRMED: The mismatch is real — parameter IS used in {year} calculations and the value
  differs from the PDF. Include the code path trace showing how the parameter is reached.
- REJECTED: The parameter does NOT affect {year} calculations — explain why
  (e.g., gated by in_effect=false, only used in pre-{year} branch, overridden by another param)
- INCONCLUSIVE: Unable to fully determine — explain what's unclear

Report to {RUN_ROOT}/{PREFIX}-review-codepath-{N}.md:
- Verdict: {CONFIRMED / REJECTED / INCONCLUSIVE}
- Parameter: {name}
- Code path trace: {top-level variable → ... → this parameter}
- Reasoning: {detailed explanation}
- If REJECTED: what code path evidence disproves the mismatch

Completion: after writing {RUN_ROOT}/{PREFIX}-review-codepath-{N}.md, return `DONE — wrote {RUN_ROOT}/{PREFIX}-review-codepath-{N}.md (verdict: CONFIRMED/REJECTED/INCONCLUSIVE)` as your final message."
```

**Spawn ALL code-path verifiers in a single message for parallelism.** Wait for all to complete before proceeding.

**After all verifiers complete:**
- **CONFIRMED** mismatches → proceed to Step 5D (600 DPI visual verification)
- **REJECTED** mismatches → excluded from Step 5D, but noted as "investigated and cleared" in the consolidator input
- **INCONCLUSIVE** mismatches → proceed to Step 5D (treat as potentially real)

Main Claude reads ONLY the verdict line from each `{RUN_ROOT}/{PREFIX}-review-codepath-{N}.md` (first line). It does NOT read the full reasoning — that's for the consolidator.

### Step 5D: Visual Verification of Confirmed Mismatches (600 DPI)

**Only process mismatches that were CONFIRMED or INCONCLUSIVE in Step 5C.** Skip REJECTED mismatches entirely.

For each surviving mismatch, spawn a **visual verification agent**:

```
subagent_type: "general-purpose"
team_name: "{WORKTREE_ID}-{PREFIX}-review"
name: "verifier-mismatch-{N}"
run_in_background: true
```

**Prompt:**
```
"You are visually verifying a reported mismatch that has passed code-path verification.
Load skills: /policyengine-parameter-patterns, /policyengine-period-patterns.

MISMATCH TO VERIFY:
- Parameter: {param name}
- Repo value: {from audit agent}
- Agent-reported PDF value: {from audit agent}
- Code-path verdict: {CONFIRMED or INCONCLUSIVE, from Step 5C}
- PDF page: {from audit agent}
- PDF file: {RUN_ROOT}/{PREFIX}-review-pdf-{N}.pdf
- Text file: {RUN_ROOT}/{PREFIX}-review-pdf-{N}.txt

STEPS:
1. Re-render the disputed page at 600 DPI:
   pdftoppm -png -r 600 -f {PAGE} -l {PAGE} {RUN_ROOT}/{PREFIX}-review-pdf-{N}.pdf {RUN_ROOT}/{PREFIX}-600dpi-mismatch-{N}
2. Read the 600 DPI screenshot carefully
3. Cross-reference with extracted text: read {RUN_ROOT}/{PREFIX}-review-pdf-{N}.txt and search for the value
4. Check for false positives — agents commonly misread values in dense tables
5. If the parameter uses uprating, compute: last_value x (new_index / old_index)
6. Check for logic gaps — the value may be correct but the formula may not enforce all rules

Report to {RUN_ROOT}/{PREFIX}-review-mismatch-{N}.md:
- CONFIRMED MISMATCH: repo={X}, PDF={Y}, page=#page={NN} — or
- FALSE POSITIVE: agent misread, actual value is {Z}
- Evidence: what you see on the 600 DPI screenshot and in extracted text

Error margin: flag any difference > 0.3.

Completion: after writing {RUN_ROOT}/{PREFIX}-review-mismatch-{N}.md, return `DONE — wrote {RUN_ROOT}/{PREFIX}-review-mismatch-{N}.md (verdict: CONFIRMED/FALSE POSITIVE)` as your final message."
```

Spawn ALL visual verifiers in a single message for parallelism.

### Step 5E: Verify Reference Page Numbers (DELEGATED)

If the PR adds PDF references (`#page=XX`), delegate page number verification to an agent.

```
subagent_type: "general-purpose"
team_name: "{WORKTREE_ID}-{PREFIX}-review"
name: "verifier-pages"
run_in_background: true
```

**Prompt:**
```
"You are verifying PDF page number references for a program review.

TASK: Check that every #page=XX reference in the PR points to the correct PDF page.

Common Pitfall: Authors often use the PRINTED page number instead of the PDF FILE page number.
These differ by the page offset (preliminary pages before content page 1).
PDF page offset: {offset from manifest}
PDF manifest: {RUN_ROOT}/{PREFIX}-review-pdf-manifest.md (contains screenshot path patterns and PDF file paths)

STEPS:
1. Read {RUN_ROOT}/{PREFIX}-review-pdf-manifest.md to get screenshot path patterns
2. Read the PR diff at {RUN_ROOT}/{PREFIX}-review-diff.txt
3. Extract all #page=XX references from YAML files
4. For each reference, read the PDF screenshot at that page number
5. Verify the referenced value actually appears on that page
6. If wrong, find the correct page by searching nearby pages

Report to {RUN_ROOT}/{PREFIX}-review-pages.md:
- CORRECT: {file} #page=XX — confirmed, [value] found on page
- WRONG: {file} #page=XX — should be #page=YY, [value] is actually on page YY

Completion: after writing {RUN_ROOT}/{PREFIX}-review-pages.md, return `DONE — wrote {RUN_ROOT}/{PREFIX}-review-pages.md` as your final message."
```

---

## Phase 6: Consolidation

Delegate consolidation to a single agent to protect Main Claude's context.

```
subagent_type: "general-purpose"
team_name: "{WORKTREE_ID}-{PREFIX}-review"
name: "consolidator"
run_in_background: false
```

**Prompt:**
```
"Consolidate all findings from a program review into a single report.

READ these files:
- {RUN_ROOT}/{PREFIX}-review-regulatory.md (regulatory accuracy)
- {RUN_ROOT}/{PREFIX}-review-references.md (reference quality)
- {RUN_ROOT}/{PREFIX}-review-code.md (code patterns)
- {RUN_ROOT}/{PREFIX}-review-tests.md (test coverage)
- {RUN_ROOT}/{PREFIX}-review-pdf-*.md (PDF audit results — all matching files)
- {RUN_ROOT}/{PREFIX}-review-xref-*.md (cross-reference verifications, if any)
- {RUN_ROOT}/{PREFIX}-review-ext-*.md (external PDF verifications, if any)
- {RUN_ROOT}/{PREFIX}-review-codepath-*.md (code-path verification verdicts, if any)
- {RUN_ROOT}/{PREFIX}-review-mismatch-*.md (600 DPI visual verifications, if any)
- {RUN_ROOT}/{PREFIX}-review-pages.md (page number verifications, if exists)
- {RUN_ROOT}/{PREFIX}-review-context.md (PR context: state, year, CI status)
- {RUN_ROOT}/{PREFIX}-review-run-state.md (run metrics: elapsed time, agents spawned,
  pages rendered, cache hits — source for the summary's Run metrics line)
- {RUN_ROOT}/{PREFIX}-review-prior-report.md (incremental mode only: prior findings and
  their IDs)

TASK:
1. Merge all findings, removing duplicates
2. If multiple validators flag the same issue, combine into one with highest priority
3. For mismatches: only include those that passed BOTH code-path verification (Step 5C)
   AND visual verification (Step 5D). Note REJECTED mismatches as 'investigated and cleared'.
4. Classify each finding:
   - CRITICAL (Must Fix): regulatory mismatches, value mismatches (code-path confirmed + 600 DPI verified),
     hard-coded values, missing/non-corroborating references, incorrect section citations
     (reference title cites wrong section/subsection), CI failures, incorrect formulas,
     formula variables with zero test coverage (no unit test at all),
     non-functional tests (e.g., absolute_error_margin >= 1 on boolean outputs)
   - SHOULD ADDRESS: code pattern violations, missing edge case tests for already-tested variables,
     naming conventions, period usage errors, formatting issues (params & vars),
     missing rounding/flooring/capping when the formula is otherwise structurally correct
     (e.g., regulation says "round to nearest dollar" but formula returns the unrounded value)
   - SUGGESTIONS: documentation improvements, performance optimizations, code style

   ROUNDING RULE: If the implementation matches the regulation in structure but is missing
   a rounding, flooring, or capping step, classify as SHOULD ADDRESS — NOT CRITICAL. This
   is a refinement, not a fundamentally wrong formula. (Exception: if a test case proves
   the missing step produces a wrong output that crosses an eligibility threshold or
   changes a categorical outcome, upgrade to CRITICAL.)

   MICROSIM DEFAULT RULE: For default values that affect population-level outputs
   (enum defaults, bare-input defaults of 0 that zero out the program), REPORT the
   direction and magnitude of the bias but do NOT prescribe a specific default
   ("change to NONE", "change to 0", etc.) — prescriptions create cross-review
   inconsistency. Valid remedies to suggest: (a) populate the variable in the dataset;
   (b) document the limitation; (c) accept if quantified and small. Classify SHOULD
   ADDRESS by default; upgrade to CRITICAL only if the bias flips eligibility for a
   meaningful population share or materially shifts aggregate program cost.

5. Write FULL report to {RUN_ROOT}/{PREFIX}-review-full-report.md (for archival/posting).
   Its Source Documents section MUST include `Reviewed head SHA: {PR_HEAD}` and
   `Mode: full` or `Mode: incremental from {PRIOR_HEAD}` so a later incremental run can
   prove its baseline.
   Assign each finding a stable ID: C1, C2… (Critical), A1, A2… (Should Address),
   S1, S2… (Suggestions). In incremental mode, carry over the prior report's IDs
   unchanged and mark each prior finding RESOLVED or STILL OPEN; number new findings
   after the highest prior ID. IDs are how incremental reviews track unresolved
   findings across rounds.
6. Write SHORT summary to {RUN_ROOT}/{PREFIX}-review-summary.md (MAX 20 LINES):
   - Critical count + one-line descriptions
   - Should count
   - Suggestion count
   - PDF audit: N values confirmed correct, M mismatches, K unmodeled items
   - Recommended severity: APPROVE / COMMENT / REQUEST_CHANGES
   - Run metrics: elapsed time, agents spawned, pages rendered, and cache hits

BRANCH STATUS NOTE: If {RUN_ROOT}/{PREFIX}-review-context.md shows Y commits behind base
(Y > 0), include a `### Branch Status` section just below 'Source Documents': "⚠ PR
branch is Y commit(s) behind {base}. Consider rebasing before merging. Review was
scoped to PR's actual changes — staleness did not affect findings." If Y == 0, omit
entirely. NEVER classify staleness as a finding — purely informational.

SEVERITY RULES:
- APPROVE: No critical issues, minor suggestions only
- COMMENT: Has issues but not blocking (educational)
- REQUEST_CHANGES: Has critical issues that must be fixed

Completion: after writing both {RUN_ROOT}/{PREFIX}-review-full-report.md and {RUN_ROOT}/{PREFIX}-review-summary.md, return `DONE — wrote full report + summary ({critical}/{should}/{suggestion} findings)` as your final message."
```

After the consolidator completes, read ONLY `{RUN_ROOT}/{PREFIX}-review-summary.md` (max 20 lines).

---

## Phase 7: Post / Display Findings

**Main Claude does NOT read the full report into context.** The consolidator writes a ready-to-post file; Main Claude just pipes it to `gh`.

### Step 7A: Display or Post

**If user chose local-only mode**: Main Claude reads `{RUN_ROOT}/{PREFIX}-review-full-report.md` and presents it directly in the conversation. The short summary (`{RUN_ROOT}/{PREFIX}-review-summary.md`) has already been read in Phase 6 — at this point all heavy lifting is done and presenting the full report is the final step, so reading it into Main Claude's context is acceptable.

**If user chose to post to GitHub**: Post using `--body-file` (no need to read the file into context):

```bash
# Post the report — Main Claude never reads this file
gh pr comment $PR_NUMBER --body-file {RUN_ROOT}/{PREFIX}-review-full-report.md
```

### Expected Report Format (written by consolidator)

The consolidator writes `{RUN_ROOT}/{PREFIX}-review-full-report.md` in this structure:

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
...

### Should Address
1. **[A1] Pattern violation**: Use `add()` instead of manual sum — [file:line]
...

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
To auto-fix issues: `/fix-pr {PR_NUMBER}`
```

### CI Failures

The context-analyzer (Phase 1) captures CI status. The consolidator includes CI failures in the Critical section based on what validators report.

---

## Context Protection Rules

**Main Claude reads ONLY these short files (phases 0–6):**
- `{RUN_ROOT}/{PREFIX}-review-context.md` (≤25 lines) — context-analyzer
- `{RUN_ROOT}/{PREFIX}-review-pdf-manifest.md` (≤30 lines) — pdf-collector
- `{RUN_ROOT}/{PREFIX}-review-full-filelist.md` (≤30 lines) — Explore agent, only if `--full`
- `{RUN_ROOT}/{PREFIX}-review-summary.md` (≤20 lines) — consolidator
- `{RUN_ROOT}/{PREFIX}-review-run-state.md` (≤30 lines) — phase ledger and timings

Phase 7 (final): Main Claude reads `{RUN_ROOT}/{PREFIX}-review-full-report.md` in local mode to present it. GitHub mode posts the file via `--body-file` without reading.

**Main Claude MUST NOT read** the PR diff, PDF text files, PDF screenshots, parameter YAMLs, variable `.py` files, or any individual agent finding file (regulatory, references, code, tests, pdf-audit, codepath, mismatch, pages). Agent prompts reference file paths — never paste content.

---

## Agent Summary

| Phase | Agent | Plugin Type | Why This Agent |
|-------|-------|-------------|----------------|
| 1 | context-analyzer | `general-purpose` | Analyzes diff, writes short context summary (needs Write tool) |
| 2 | pdf-collector | `complete:country-models:document-collector` | Purpose-built for regulatory source discovery |
| 3 | file-lister (if `--full`) | `general-purpose` | Lists all files for full audit scope (needs Write tool) |
| 4 | regulatory-reviewer | `complete:country-models:program-reviewer` | Researches regulations independently, compares to code |
| 4 | reference-checker | `complete:reference-validator` | Reference quality, corroboration, #page= verification |
| 4 | code-validator | `complete:country-models:implementation-validator` | Code patterns, naming, hard-coded values |
| 4 | edge-case-checker | `complete:country-models:edge-case-generator` | Missing boundary tests, untested scenarios |
| 4 | pdf-audit-{topic} x2-5 | `general-purpose` | Need Bash (pdftoppm) + Read (PNG screenshots) |
| 5A-B | verifier-xref/ext-{N} | `general-purpose` | Cross-ref resolution, external PDF verification |
| 5C | verifier-codepath-{N} | `general-purpose` | Code-path tracing to filter false positive mismatches |
| 5D | verifier-mismatch-{N} | `general-purpose` | 600 DPI re-render of CONFIRMED/INCONCLUSIVE mismatches |
| 5E | verifier-pages | `general-purpose` | Page number verification (instruction vs file page) |
| 6 | consolidator | `general-purpose` | Merges all findings, deduplicates, classifies priority |
| 7 | _(none — Main Claude presents the full report directly in local mode, or posts via `gh --body-file` in GitHub mode)_ | — | — |

**5 plugin agents + 4-13 general-purpose agents.**
Main Claude reads short summaries (≤30 lines) during phases 0-6, then reads the full report in Phase 7 (local mode only).

---

## Global Rules

1. **READ-ONLY**: Never edit files. Never switch branches. This is a review.
2. **PDF by default**: pdf-collector runs unless `--skip-pdf` flag is used. If no PDF found (or skipped), manifest says so and Phase 4 runs code validators only.
3. **Render every page**: Render every collected PDF completely at the requested DPI (300
   by default, 600 with `--600dpi`). Cache by PDF checksum + DPI and verify the complete
   page sequence before reuse. At the default DPI, rerender disputed pages at 600 DPI for
   mismatch verification.
4. **Two-stage mismatch verification**: Every mismatch must pass BOTH code-path verification (Step 5C — is the parameter reachable in the target year?) AND visual verification (Step 5D — 600 DPI + text cross-reference). Never include a mismatch in the final report without both checks.
5. **Trace code paths**: A parameter mismatch is only real if the parameter is actually used in the target year's computation. Always verify the parameter is reachable from the top-level variable — check for `in_effect` gates, deprecated branches, and overriding parameters.
6. **Agents stay in scope**: Agents only read their assigned pages. Cross-references and external PDFs get separate verification agents.
7. **Always cite pages**: Every finding must include a `#page=XX` citation (file page, NOT printed page). Exception: single-page PDFs.
8. **Error margin <= 1**: Flag any difference > 0.3 between repo and PDF values.
9. **Context preservation**: Never read large PDFs in Main Claude's context. Always delegate to agents.
10. **Multiple PDFs supported**: Collector downloads up to 5. Manifest maps PDF-to-topic. Audit agents read from whichever PDF covers their topic.
11. **No PDF gracefully handled**: Skip PDF audit agents, run code-only validators, note in report.
12. **Changelog**: Every PR needs a towncrier fragment in `changelog.d/<branch>.<type>.md`.
13. **Incremental integrity**: An incremental report must record its reviewed head SHA.
    Fall back to a full review when ancestry or cached source integrity cannot be proven.
14. **Metrics**: Record phase durations, agents spawned, pages rendered, cache hits, and
    full versus incremental scope in the run-state file and final summary.


Start by parsing arguments, then proceed through all phases.
