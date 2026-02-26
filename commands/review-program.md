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
- Read the PR diff (`/tmp/review-program-diff.txt`)
- Read parameter YAML files or variable .py files
- Read PDF text files or PDF screenshots
- Read individual agent finding files (regulatory, references, code, tests, pdf-audit)
- Re-render PDFs at 600 DPI yourself
- Grep through diffs or code files

**You DO:**
- Parse arguments and resolve PR number
- Run `gh` commands for small structured JSON (pr view, pr checks)
- Save diff to disk for agents: `gh pr diff > /tmp/review-program-diff.txt`
- Read SHORT summary files only: context (≤25 lines), manifest (≤30 lines), summary (≤20 lines)
- Spawn agents (in parallel where possible)
- Post the final report using `gh pr comment --body-file`

## Arguments

`$ARGUMENTS` should contain:
- **PR number** (required) — e.g., `7130`
- **PDF URL** (optional) — link to the official source PDF. If omitted, auto-discovered.
- **Options**:
  - `--local` — show findings locally only, skip GitHub posting
  - `--local-diff` — implies `--local`; reads diff from `git diff` instead of `gh pr diff` (for reviewing unpushed work)
  - `--full` — audit ALL implemented parameters, not just PR diff
  - `--skip-pdf` — skip PDF acquisition and audit; run code validators only (for infrastructure/refactoring PRs with no source document)
  - `--600dpi` — render PDFs at 600 DPI instead of 300 DPI (for scanned docs or dense tables)

**Examples:**
```
/review-program 7130
/review-program 7130 --full
/review-program 7130 --local
/review-program 7130 --local-diff --full
/review-program 7130 --skip-pdf
/review-program 7130 https://state.gov/manual.pdf
/review-program 7130 https://state.gov/manual.pdf --full --600dpi
```

---

## Phase 0: Parse Arguments & Ask Posting Mode

### Step 0A: Parse Arguments & Clean Up

**Clean up leftover files from previous runs** (prevents stale data from confusing agents):
```bash
rm -f /tmp/review-program-*.md /tmp/review-pdf-*.{pdf,txt,png} /tmp/review-600dpi-*.png /tmp/review-ext-*.{pdf,txt,png,md}
```

```
Parse $ARGUMENTS:
- PR_ARG: first non-flag, non-URL argument (number or search text)
- PDF_URL: first URL argument (may be empty — will auto-discover in Phase 2)
- LOCAL_ONLY: true if --local or --local-diff flag present
- LOCAL_DIFF: true if --local-diff flag present (implies LOCAL_ONLY)
- FULL_AUDIT: true if --full flag present
- SKIP_PDF: true if --skip-pdf flag present
- DPI: 600 if --600dpi, else 300
```

**Resolve PR number:**
```bash
# If argument is a number, use it directly
if [[ "$PR_ARG" =~ ^[0-9]+$ ]]; then
    PR_NUMBER=$PR_ARG
# Otherwise, search for PR by description/title
else
    PR_NUMBER=$(gh pr list --search "$PR_ARG" --json number,title --jq '.[0].number')
    if [ -z "$PR_NUMBER" ]; then
        echo "No PR found matching: $PR_ARG"
        exit 1
    fi
fi
```

**If no PR argument provided**: Use `AskUserQuestion` to ask for the PR number or title.

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
```

**Save diff to disk** (method depends on `--local-diff`):

```bash
# Standard mode: read from GitHub remote
gh pr diff $PR_NUMBER > /tmp/review-program-diff.txt

# --local-diff mode: read from local commits (no push required)
BASE_BRANCH=$(gh pr view $PR_NUMBER --json baseRefName --jq '.baseRefName')
git diff "$BASE_BRANCH"...HEAD > /tmp/review-program-diff.txt
```

**Main Claude does NOT read the diff file.** It only saves it to disk for agents.

### Step 1B: Delegate diff analysis to agent (PARALLEL with Phase 2)

Spawn a `general-purpose` agent to analyze the diff and write a short context file.
Must be `general-purpose` (not Explore) because it needs the Write tool to save the summary to disk.

```
subagent_type: "general-purpose"
name: "context-analyzer"
run_in_background: true

"Analyze the PR diff at /tmp/review-program-diff.txt and write a context summary.

TASK:
1. Read /tmp/review-program-diff.txt
2. Write /tmp/review-program-context.md (MAX 25 LINES):

   ## PR Context
   - Scope: {state program / federal parameter / infrastructure / API / frontend / other}
   - State: {abbreviation} ({full name}) — or 'N/A' if not state-specific
   - Program area: {tax / TANF / SNAP / Medicaid / etc.} — or 'N/A'
   - Year: {year being updated} — or 'N/A'
   - PR type: {new program / bug fix / enhancement / parameter update / refactor / infrastructure}
   - CI status: {from gh pr checks output if available}
   - Has source documents: {yes / no} — true if YAML refs contain PDF URLs or PR body links to docs
   ## Files Changed
   - Parameters: {list of YAML file paths, or 'none'}
   - Variables: {list of .py file paths, or 'none'}
   - Tests: {list of test file paths, or 'none'}
   - Other: {list of other changed files, if any}
   ## Topics
   - {topic 1}: {file paths}
   - {topic 2}: {file paths}
   ## PDF References Found
   - {any PDF URLs found in PR body or YAML reference fields, or 'none'}

Keep it CONCISE — paths and classifications only. Max 25 lines."
```

### Step 1C: Read context summary

After the context-analyzer completes, read ONLY `/tmp/review-program-context.md` (max 25 lines). This gives you:
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
echo "## PDF Manifest\n### No PDF (skipped)\n- Reason: {--skip-pdf flag / no source documents for this PR type}; code-only review" > /tmp/review-program-pdf-manifest.md
```

**Otherwise, PDF acquisition runs.** This is delegated entirely to the document-collector agent to protect Main Claude's context window.

### Spawn PDF Collector

```
subagent_type: "complete:country-models:document-collector"
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
   a. Check PR description and YAML references (read /tmp/review-program-diff.txt)
   b. WebSearch for the official source document
   c. Download and validate (correct state, year, document type)
3. For EACH PDF found (up to 5):
   a. Download: curl -L -o /tmp/review-pdf-{N}.pdf 'URL'
   b. Get page count: pdfinfo /tmp/review-pdf-{N}.pdf | grep Pages
   c. Extract text: pdftotext /tmp/review-pdf-{N}.pdf /tmp/review-pdf-{N}.txt
   d. Render at {DPI} DPI: pdftoppm -png -r {DPI} /tmp/review-pdf-{N}.pdf /tmp/review-pdf-{N}-page
   e. Determine page offset (cover/TOC pages before content page 1)
4. Check for supplementary documents referenced by the main booklet
5. Write manifest to /tmp/review-program-pdf-manifest.md (MAX 30 LINES):

   ## PDF Manifest
   ### PDF 1: [title]
   - URL: [url]
   - Path: /tmp/review-pdf-1.pdf
   - Pages: [count], offset: [N] preliminary pages
   - Text: /tmp/review-pdf-1.txt
   - Screenshots: /tmp/review-pdf-1-page-{NN}.png
   - Topics covered: [list of topics and page ranges]
   ### PDF 2: [title] (if applicable)
   ...
   ### No PDF Found (if applicable)
   - Reason: [why no source was found]

If no PDF is found, write that in the manifest and the review will continue with code-only validators."
```

### Read Manifest

After the pdf-collector completes, read ONLY `/tmp/review-program-pdf-manifest.md` (max 30 lines). This tells you:
- Which PDFs were found (if any)
- **Total page count per PDF** — used in Phase 3 to decide how many audit agents to spawn
- File paths for agent prompts
- Topic-to-page mappings for Phase 3

---

## Phase 3: Map Files to Topics & Plan Agent Split

Using the context summary (from Phase 1) and the PDF manifest (from Phase 2), plan the parallel agent split. **Main Claude reads only these two short files** — no diff, no code, no PDFs.

### Identify repo files to review

**If `--full` flag**: The context-analyzer noted the state/program path. Spawn a quick `general-purpose` agent (needs Write tool) to list all files under that path and write to `/tmp/review-program-full-filelist.md` (max 30 lines). Read only that file.

**If no `--full` flag**: Use the file lists from `/tmp/review-program-context.md`.

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

---

## Phase 4: Parallel Execution

Spawn ALL agents in a **single message** for maximum parallelism. Two groups run simultaneously:
- **Code validators** (2-4 plugin agents, depending on scope) — work on the repo code
- **PDF audit agents** (2-5 general-purpose agents, if PDF available) — work on PDF screenshots

**Scope-based agent selection:**
- **Program PRs** (state or federal): All 4 code validators + PDF audit agents
- **Infrastructure/API/frontend PRs**: Only Validator 3 (code patterns) + Validator 4 (test coverage). Skip Validator 1 (regulatory) and Validator 2 (references) since there are no parameters.
- **Mixed PRs**: All 4 validators, but Validators 1-2 only review parameter/variable files

### Group A: Code Validators

#### Validator 1: Regulatory Accuracy (Critical)

**Skip for infrastructure/API/frontend PRs.**

```
subagent_type: "complete:country-models:program-reviewer"
name: "regulatory-reviewer"
run_in_background: true
```

**Prompt:**
```
"Review {State} {PROGRAM} PR #{PR_NUMBER} for regulatory accuracy.
- Research regulations FIRST (independent of code)
- Compare implementation to legal requirements
- Identify discrepancies between code and law
- Flag missing program components
- Write findings to /tmp/review-program-regulatory.md

KEY QUESTION: Does this implementation correctly reflect the law?

Files to review: {list from Phase 3}
PDF text available at: {paths from manifest, for cross-reference only}"
```

#### Validator 2: Reference Quality (Critical)

**Skip for infrastructure/API/frontend PRs.**

```
subagent_type: "complete:reference-validator"
name: "reference-checker"
run_in_background: true
```

**Prompt:**
```
"Validate references in {State} {PROGRAM} PR #{PR_NUMBER}.
- Find parameters missing references
- Check reference format (page numbers, detailed sections)
- Verify references corroborate values
- Check jurisdiction match (federal vs state sources)
- Verify #page=XX is the FILE page number, not the printed page number
  (use PDF page offset from manifest to check)
- Flag session law refs that should cite permanent statutes
- Write findings to /tmp/review-program-references.md

KEY QUESTION: Can every value be traced to an authoritative source?

Files to review: {list from Phase 3}
PDF manifest: /tmp/review-program-pdf-manifest.md"
```

#### Validator 3: Code Patterns (Critical + Should)

```
subagent_type: "complete:country-models:implementation-validator"
name: "code-validator"
run_in_background: true
```

**Prompt:**
```
"Validate code patterns in {State} {PROGRAM} PR #{PR_NUMBER}.
- Find hard-coded values in formulas
- Check variable naming conventions
- Verify correct patterns (adds, add(), add() > 0)
- Check period usage (period vs period.this_year)
- Identify entity-level issues
- Flag incomplete implementations (TODOs, stubs)
- Check parameter formatting (descriptions, labels, metadata)
- Check for changelog fragment: a file must exist at changelog.d/<branch>.<type>.md
  (types: added, changed, fixed, removed, breaking). Flag if missing.
- Write findings to /tmp/review-program-code.md

KEY QUESTION: Does the code follow PolicyEngine standards?

Files to review: {list from Phase 3}"
```

#### Validator 4: Test Coverage (Should)

```
subagent_type: "complete:country-models:edge-case-generator"
name: "edge-case-checker"
run_in_background: true
```

**Prompt:**
```
"Analyze test coverage for {State} {PROGRAM} PR #{PR_NUMBER}.
- Identify missing boundary tests
- Find untested edge cases
- Check parameter combinations not tested
- Verify integration test exists
- Write findings to /tmp/review-program-tests.md

KEY QUESTION: Are the important scenarios tested?

Files to review: {list from Phase 3}"
```

### Group B: PDF Audit Agents

**Skip this group if PDF manifest says "No PDF Found".**

Spawn 2-5 `general-purpose` agents, one per topic from Phase 3. Each agent gets assigned PDF pages and repo files.

```
subagent_type: "general-purpose"
name: "pdf-audit-{topic}"
run_in_background: true
```

**PDF Audit Agent Prompt Template:**
```
"You are auditing {State}'s {year} {program} parameters against the official source document.

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

5. Report to /tmp/review-program-pdf-{topic}.md:
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
Do NOT guess values you haven't seen. Flag it and move on."
```

---

## Phase 5: Verification

After all Phase 4 agents complete, handle flags and verify mismatches. Steps 5A-5B handle flags in parallel. Step 5C filters mismatches via code-path tracing. Step 5D visually confirms only surviving mismatches. Step 5E checks page numbers.

### Step 5A: Handle CROSS-REFERENCE NEEDED Flags

For each cross-reference flag from PDF audit agents, spawn a **verification agent**:

```
subagent_type: "general-purpose"
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
3. Report to /tmp/review-program-xref-{N}.md:
   - The value you see on that page
   - What confirms it (table name, worksheet line, etc.)
   - PDF page number for citation: #page=XX"
```

### Step 5B: Handle EXTERNAL PDF NEEDED Flags

For each external PDF flag, spawn a **verification agent**:

```
subagent_type: "general-purpose"
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
2. Download: curl -L -o /tmp/review-ext-{N}.pdf 'URL'
3. Extract text: pdftotext /tmp/review-ext-{N}.pdf /tmp/review-ext-{N}.txt
4. Render at {DPI} DPI: pdftoppm -png -r {DPI} /tmp/review-ext-{N}.pdf /tmp/review-ext-{N}-page
5. Read text and/or screenshots to find the value
6. Report to /tmp/review-program-ext-{N}.md:
   - PDF URL (for reference link with #page=XX)
   - Correct value with exact PDF page number
   - Confirmation details"
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
name: "verifier-codepath-{N}"
run_in_background: true
```

**Prompt:**
```
"You are a code-path verifier for a program review. An audit agent reported a MISMATCH
and you must determine if it's a real issue or a false positive.

REPORTED MISMATCH:
- Parameter: {parameter name and file path}
- Repo value: {value from audit agent report}
- Agent-reported PDF value: {value from audit agent report}
- Audit agent's reasoning: {summary from their report file /tmp/review-program-pdf-{topic}.md}
- Target year: {year from Phase 1}

YOUR TASK:
1. Read the audit agent's report at /tmp/review-program-pdf-{topic}.md to understand
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

Report to /tmp/review-program-codepath-{N}.md:
- Verdict: {CONFIRMED / REJECTED / INCONCLUSIVE}
- Parameter: {name}
- Code path trace: {top-level variable → ... → this parameter}
- Reasoning: {detailed explanation}
- If REJECTED: what code path evidence disproves the mismatch"
```

**Spawn ALL code-path verifiers in a single message for parallelism.** Wait for all to complete before proceeding.

**After all verifiers complete:**
- **CONFIRMED** mismatches → proceed to Step 5D (600 DPI visual verification)
- **REJECTED** mismatches → excluded from Step 5D, but noted as "investigated and cleared" in the consolidator input
- **INCONCLUSIVE** mismatches → proceed to Step 5D (treat as potentially real)

Main Claude reads ONLY the verdict line from each `/tmp/review-program-codepath-{N}.md` (first line). It does NOT read the full reasoning — that's for the consolidator.

### Step 5D: Visual Verification of Confirmed Mismatches (600 DPI)

**Only process mismatches that were CONFIRMED or INCONCLUSIVE in Step 5C.** Skip REJECTED mismatches entirely.

For each surviving mismatch, spawn a **visual verification agent**:

```
subagent_type: "general-purpose"
name: "verifier-mismatch-{N}"
run_in_background: true
```

**Prompt:**
```
"You are visually verifying a reported mismatch that has passed code-path verification.

MISMATCH TO VERIFY:
- Parameter: {param name}
- Repo value: {from audit agent}
- Agent-reported PDF value: {from audit agent}
- Code-path verdict: {CONFIRMED or INCONCLUSIVE, from Step 5C}
- PDF page: {from audit agent}
- PDF file: /tmp/review-pdf-{N}.pdf
- Text file: /tmp/review-pdf-{N}.txt

STEPS:
1. Re-render the disputed page at 600 DPI:
   pdftoppm -png -r 600 -f {PAGE} -l {PAGE} /tmp/review-pdf-{N}.pdf /tmp/review-600dpi-mismatch-{N}
2. Read the 600 DPI screenshot carefully
3. Cross-reference with extracted text: read /tmp/review-pdf-{N}.txt and search for the value
4. Check for false positives — agents commonly misread values in dense tables
5. If the parameter uses uprating, compute: last_value x (new_index / old_index)
6. Check for logic gaps — the value may be correct but the formula may not enforce all rules

Report to /tmp/review-program-mismatch-{N}.md:
- CONFIRMED MISMATCH: repo={X}, PDF={Y}, page=#page={NN} — or
- FALSE POSITIVE: agent misread, actual value is {Z}
- Evidence: what you see on the 600 DPI screenshot and in extracted text

Error margin: flag any difference > 0.3."
```

Spawn ALL visual verifiers in a single message for parallelism.

### Step 5E: Verify Reference Page Numbers (DELEGATED)

If the PR adds PDF references (`#page=XX`), delegate page number verification to an agent.

```
subagent_type: "general-purpose"
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
PDF manifest: /tmp/review-program-pdf-manifest.md (contains screenshot path patterns and PDF file paths)

STEPS:
1. Read /tmp/review-program-pdf-manifest.md to get screenshot path patterns
2. Read the PR diff at /tmp/review-program-diff.txt
3. Extract all #page=XX references from YAML files
4. For each reference, read the PDF screenshot at that page number
5. Verify the referenced value actually appears on that page
6. If wrong, find the correct page by searching nearby pages

Report to /tmp/review-program-pages.md:
- CORRECT: {file} #page=XX — confirmed, [value] found on page
- WRONG: {file} #page=XX — should be #page=YY, [value] is actually on page YY"
```

---

## Phase 6: Consolidation

Delegate consolidation to a single agent to protect Main Claude's context.

```
subagent_type: "general-purpose"
name: "consolidator"
run_in_background: false
```

**Prompt:**
```
"Consolidate all findings from a program review into a single report.

READ these files:
- /tmp/review-program-regulatory.md (regulatory accuracy)
- /tmp/review-program-references.md (reference quality)
- /tmp/review-program-code.md (code patterns)
- /tmp/review-program-tests.md (test coverage)
- /tmp/review-program-pdf-*.md (PDF audit results — all matching files)
- /tmp/review-program-xref-*.md (cross-reference verifications, if any)
- /tmp/review-program-ext-*.md (external PDF verifications, if any)
- /tmp/review-program-codepath-*.md (code-path verification verdicts, if any)
- /tmp/review-program-mismatch-*.md (600 DPI visual verifications, if any)
- /tmp/review-program-pages.md (page number verifications, if exists)
- /tmp/review-program-context.md (PR context: state, year, CI status)

TASK:
1. Merge all findings, removing duplicates
2. If multiple validators flag the same issue, combine into one with highest priority
3. For mismatches: only include those that passed BOTH code-path verification (Step 5C)
   AND visual verification (Step 5D). Note REJECTED mismatches as 'investigated and cleared'.
4. Classify each finding:
   - CRITICAL (Must Fix): regulatory mismatches, value mismatches (code-path confirmed + 600 DPI verified),
     hard-coded values, missing/non-corroborating references, CI failures, incorrect formulas
   - SHOULD ADDRESS: code pattern violations, missing edge case tests, naming conventions,
     period usage errors, formatting issues (params & vars)
   - SUGGESTIONS: documentation improvements, performance optimizations, code style

5. Write FULL report to /tmp/review-program-full-report.md (for archival/posting)
6. Write SHORT summary to /tmp/review-program-summary.md (MAX 20 LINES):
   - Critical count + one-line descriptions
   - Should count
   - Suggestion count
   - PDF audit: N values confirmed correct, M mismatches, K unmodeled items
   - Recommended severity: APPROVE / COMMENT / REQUEST_CHANGES

SEVERITY RULES:
- APPROVE: No critical issues, minor suggestions only
- COMMENT: Has issues but not blocking (educational)
- REQUEST_CHANGES: Has critical issues that must be fixed"
```

After the consolidator completes, read ONLY `/tmp/review-program-summary.md` (max 20 lines).

---

## Phase 7: Post / Display Findings

**Main Claude does NOT read the full report into context.** The consolidator writes a ready-to-post file; Main Claude just pipes it to `gh`.

### Step 7A: Display or Post

**If user chose local-only mode**: Spawn a `general-purpose` agent to read and summarize the full report for display:

```
subagent_type: "general-purpose"
name: "display-agent"

"Read /tmp/review-program-full-report.md and present it to the user.
Format it clearly with markdown sections. Include all findings."
```

Main Claude shows the agent's summary to the user.

**If user chose to post to GitHub**: Post using `--body-file` (no need to read the file into context):

```bash
# Post the report — Main Claude never reads this file
gh pr comment $PR_NUMBER --body-file /tmp/review-program-full-report.md
```

### Expected Report Format (written by consolidator)

The consolidator writes `/tmp/review-program-full-report.md` in this structure:

```
## Program Review

### Source Documents
- **PDF**: [Document title](URL#page=1) ({page count} pages)
- **Year**: {year}
- **Scope**: {PR changes only / Full audit}

### Critical (Must Fix)
1. **Regulatory mismatch**: [Description] — [file:line] — PDF [p.NN](URL#page=NN)
2. **Value mismatch**: [Param] repo: X, PDF: Y — [file:line] — PDF [p.NN](URL#page=NN)
...

### Should Address
1. **Pattern violation**: Use `add()` instead of manual sum — [file:line]
...

### Suggestions
1. Consider adding calculation example in docstring

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

**Main Claude reads ONLY these short files:**
- `/tmp/review-program-context.md` (max 25 lines) — from context-analyzer
- `/tmp/review-program-pdf-manifest.md` (max 30 lines) — from pdf-collector
- `/tmp/review-program-full-filelist.md` (max 30 lines) — from Explore agent, only if `--full`
- `/tmp/review-program-summary.md` (max 20 lines) — from consolidator

**All other data flows through files on disk.** Agent prompts reference file paths, never paste content.

**Main Claude MUST NOT read:**
- The PR diff (`/tmp/review-program-diff.txt`)
- PDF text files (`/tmp/review-pdf-*.txt`)
- PDF screenshots (`/tmp/review-pdf-*-page-*.png`, `/tmp/review-600dpi-*.png`)
- Parameter YAML files or variable .py files
- Individual agent finding files (regulatory, references, code, tests, pdf-audit, codepath, mismatch, pages)
- The full report (`/tmp/review-program-full-report.md`) — posted via `--body-file`

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
| 7 | display-agent (if local) | `general-purpose` | Reads and presents full report to user |

**5 plugin agents + 5-14 general-purpose agents.**
Main Claude only reads short summaries (≤30 lines) and runs `gh` commands.

---

## Global Rules

1. **READ-ONLY**: Never edit files. Never switch branches. This is a review.
2. **PDF by default**: pdf-collector runs unless `--skip-pdf` flag is used. If no PDF found (or skipped), manifest says so and Phase 4 runs code validators only.
3. **300 DPI minimum**: Always render PDFs at 300 DPI. Use 600 DPI for mismatch verification (or if `--600dpi` flag).
4. **Two-stage mismatch verification**: Every mismatch must pass BOTH code-path verification (Step 5C — is the parameter reachable in the target year?) AND visual verification (Step 5D — 600 DPI + text cross-reference). Never include a mismatch in the final report without both checks.
5. **Trace code paths**: A parameter mismatch is only real if the parameter is actually used in the target year's computation. Always verify the parameter is reachable from the top-level variable — check for `in_effect` gates, deprecated branches, and overriding parameters.
6. **Agents stay in scope**: Agents only read their assigned pages. Cross-references and external PDFs get separate verification agents.
7. **Always cite pages**: Every finding must include a `#page=XX` citation (file page, NOT printed page). Exception: single-page PDFs.
8. **Error margin <= 1**: Flag any difference > 0.3 between repo and PDF values.
9. **Context preservation**: Never read large PDFs in Main Claude's context. Always delegate to agents.
10. **Multiple PDFs supported**: Collector downloads up to 5. Manifest maps PDF-to-topic. Audit agents read from whichever PDF covers their topic.
11. **No PDF gracefully handled**: Skip PDF audit agents, run code-only validators, note in report.
12. **Changelog**: Every PR needs a towncrier fragment in `changelog.d/<branch>.<type>.md`.

---

## Pre-Flight Checklist

Before starting:
- [ ] I will ask posting mode FIRST (unless --local or --local-diff flag used)
- [ ] I will NOT make any code changes
- [ ] I will NOT switch branches
- [ ] I will use `git diff` for --local-diff, `gh pr diff` otherwise
- [ ] I will spawn pdf-collector in Phase 2 (unless --skip-pdf)
- [ ] I will render PDFs at {DPI} DPI minimum (if PDF phase runs)
- [ ] I will verify all mismatches via Step 5C code-path tracing before visual verification
- [ ] I will verify confirmed/inconclusive mismatches at 600 DPI in Step 5D
- [ ] I will spawn verification agents for cross-references and external PDFs
- [ ] I will include #page=XX citations for all findings
- [ ] I will read ONLY short summary files — never raw PDFs or full agent reports
- [ ] I will be constructive and actionable

Start by parsing arguments, then proceed through all phases.
