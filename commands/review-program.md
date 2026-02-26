---
description: Review a program PR — code validation + PDF audit in one pass (read-only, no code changes)
---

# Reviewing Program PR: $ARGUMENTS

**READ-ONLY MODE**: This command analyzes the PR and posts a combined review to GitHub WITHOUT making any code changes. Use `/fix-pr` to apply fixes.

## Arguments

`$ARGUMENTS` should contain:
- **PR number** (required) — e.g., `7130`
- **PDF URL** (optional) — link to the official source PDF. If omitted, auto-discovered.
- **Options**:
  - `--local` — show findings locally only, skip GitHub posting
  - `--full` — audit ALL implemented parameters, not just PR diff
  - `--600dpi` — render PDFs at 600 DPI instead of 300 DPI (for scanned docs or dense tables)

**Examples:**
```
/review-program 7130
/review-program 7130 --full
/review-program 7130 --local
/review-program 7130 https://state.gov/manual.pdf
/review-program 7130 https://state.gov/manual.pdf --full --600dpi
```

---

## Phase 0: Parse Arguments & Ask Posting Mode

### Step 0A: Parse Arguments

```
Parse $ARGUMENTS:
- PR_ARG: first non-flag, non-URL argument (number or search text)
- PDF_URL: first URL argument (may be empty — will auto-discover in Phase 2)
- LOCAL_ONLY: true if --local flag present
- FULL_AUDIT: true if --full flag present
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

Main Claude runs these directly (small structured data, no context risk):

```bash
gh pr view $PR_NUMBER --json title,body,author,baseRefName,headRefName
gh pr checks $PR_NUMBER
gh pr diff $PR_NUMBER > /tmp/review-program-diff.txt
```

From the diff, identify:
- **PR type**: New program, bug fix, enhancement, parameter update, or refactor
- **CI status**: Passing, failing, or pending
- **State abbreviation** from file paths (e.g., `parameters/gov/states/{st}/`)
- **Program area** — tax, TANF, SNAP, etc.
- **Tax/program year** being updated
- **Files changed**: parameter YAMLs, variable Python files, tests
- **Topics covered**: rates, deductions, credits, eligibility, benefits, etc.

Also check for existing PDF references in the PR:

```bash
# Check PR description for PDF links
gh pr view $PR_NUMBER --json body --jq '.body' | grep -oE 'https?://[^ )]*.pdf[^ )]*'

# Check YAML files in the diff for reference fields
grep -i 'reference\|source\|\.pdf\|\.gov' /tmp/review-program-diff.txt | head -20
```

---

## Phase 2: PDF Acquisition (ALWAYS ON)

**PDF acquisition always runs.** This is delegated entirely to the document-collector agent to protect Main Claude's context window.

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

Using the PR diff (from Phase 1) and the PDF manifest (from Phase 2), plan the parallel agent split.

### Identify repo files to review

**If `--full` flag**: Scan the full repo tree for the state/program:
```
parameters/gov/states/{st}/{program}/
variables/gov/states/{st}/{program}/
```

**If no `--full` flag**: Use only files from the PR diff.

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
- **Code validators** (4 plugin agents) — work on the repo code
- **PDF audit agents** (2-5 general-purpose agents) — work on PDF screenshots

### Group A: Code Validators

#### Validator 1: Regulatory Accuracy (Critical)

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

After all Phase 4 agents complete, handle flags and verify mismatches.

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

### Step 5C: Verify ALL Reported Mismatches (CRITICAL)

**Never trust agent-reported mismatches without verification.** For each mismatch from PDF audit agents:

1. **Re-render at 600 DPI** for the disputed page:
   ```bash
   pdftoppm -png -r 600 -f PAGE -l PAGE /tmp/review-pdf-{N}.pdf /tmp/review-600dpi-{page}
   ```

2. **Cross-reference with extracted text** — check `/tmp/review-pdf-{N}.txt` to confirm or deny

3. **Check for false positives** — agents commonly misread values in dense tables

4. **Check uprating math** — if a parameter uses uprating, manually compute: `last_value x (new_index / old_index)`

5. **Check for logic gaps** — the value may be correct but the formula may not enforce all rules

**Error margin**: Differences should never exceed 1. Flag any difference > 0.3.

### Step 5D: Verify Reference Page Numbers

If the PR adds PDF references (`#page=XX`), verify every anchor points to the correct PDF page.

**Common Pitfall: Instruction Page vs PDF Page**
Authors often use the printed page number instead of the PDF file page number. These differ by the page offset identified in Phase 2.

For each file with a reference:
1. Read the YAML to get the `#page=XX` value
2. Read the corresponding screenshot to check if the referenced value is on that page
3. If wrong, find the correct page

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

TASK:
1. Merge all findings, removing duplicates
2. If multiple validators flag the same issue, combine into one with highest priority
3. Classify each finding:
   - CRITICAL (Must Fix): regulatory mismatches, value mismatches (verified at 600 DPI),
     hard-coded values, missing/non-corroborating references, CI failures, incorrect formulas
   - SHOULD ADDRESS: code pattern violations, missing edge case tests, naming conventions,
     period usage errors, formatting issues (params & vars)
   - SUGGESTIONS: documentation improvements, performance optimizations, code style

4. Write FULL report to /tmp/review-program-full-report.md (for archival/posting)
5. Write SHORT summary to /tmp/review-program-summary.md (MAX 20 LINES):
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

### Step 7A: Read Full Report for Posting

Read `/tmp/review-program-full-report.md` to get the complete report content.

### Step 7B: Display or Post

**If user chose local-only mode**: Display the full report locally and stop.

**If user chose to post to GitHub**: Check for existing reviews, then post.

```bash
# Check for existing review comments from current user
CURRENT_USER=$(gh api user --jq '.login')
EXISTING=$(gh api "/repos/{owner}/{repo}/pulls/$PR_NUMBER/comments" \
  --jq "[.[] | select(.user.login == \"$CURRENT_USER\")] | length")
```

### PR Comment Structure

Post a single combined review:

```bash
gh pr comment $PR_NUMBER --body "## Program Review

### Source Documents
- **PDF**: [Document title](URL#page=1) ({page count} pages)
- **Year**: {year}
- **Scope**: {PR changes only / Full audit}

### Critical (Must Fix)

1. **Regulatory mismatch**: [Description] — [file:line] — PDF [p.NN](URL#page=NN)
2. **Value mismatch**: [Param] repo: X, PDF: Y — [file:line] — PDF [p.NN](URL#page=NN)
3. **Hard-coded value**: [Value] in [file:line] — create parameter
4. **Reference issue**: [File] — [specific problem]

### Should Address

1. **Pattern violation**: Use \`add()\` instead of manual sum — [file:line]
2. **Missing test**: Add edge case for [scenario]
3. **Formatting issue**: [file] — [description/label/values issue]

### Suggestions

1. Consider adding calculation example in docstring

### PDF Audit Summary

| Category | Count |
|----------|-------|
| Confirmed correct | N |
| Mismatches (verified) | M |
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

To auto-fix issues: \`/fix-pr $PR_NUMBER\`
"
```

### CI Failures

If CI is failing, add to the Critical section:

```bash
gh pr checks $PR_NUMBER --json name,conclusion \
  --jq '.[] | select(.conclusion == "failure") | "- **CI Failure**: " + .name'
```

---

## Context Protection Rules

**Main Claude reads ONLY these short files:**
- `/tmp/review-program-pdf-manifest.md` (max 30 lines) — from pdf-collector
- `/tmp/review-program-summary.md` (max 20 lines) — from consolidator
- `/tmp/review-program-full-report.md` — only at Phase 7 for posting

**All other data flows through files on disk.** Agent prompts reference file paths, never paste content.

**Main Claude MUST NOT read:**
- PDF text files (`/tmp/review-pdf-*.txt`)
- PDF screenshots (`/tmp/review-pdf-*-page-*.png`)
- Individual agent finding files (except through the consolidator)

---

## Agent Summary

| Phase | Agent | Plugin Type | Why This Agent |
|-------|-------|-------------|----------------|
| 2 | pdf-collector | `complete:country-models:document-collector` | Purpose-built for regulatory source discovery |
| 4 | regulatory-reviewer | `complete:country-models:program-reviewer` | Researches regulations independently, compares to code |
| 4 | reference-checker | `complete:reference-validator` | Reference quality, corroboration, #page= verification |
| 4 | code-validator | `complete:country-models:implementation-validator` | Code patterns, naming, hard-coded values |
| 4 | edge-case-checker | `complete:country-models:edge-case-generator` | Missing boundary tests, untested scenarios |
| 4 | pdf-audit-{topic} x2-5 | `general-purpose` | Need Bash (pdftoppm) + Read (PNG screenshots) |
| 5 | verifier-{N} (as needed) | `general-purpose` | Cross-ref resolution, 600 DPI re-render |
| 6 | consolidator | `general-purpose` | Merges all findings, deduplicates, classifies priority |

**5 plugin agents + 3-8 general-purpose agents** (only where no plugin agent fits).

---

## Global Rules

1. **READ-ONLY**: Never edit files. Never switch branches. This is a review.
2. **PDF always on**: pdf-collector always runs. If no PDF found, manifest says so and Phase 4 runs code validators only.
3. **300 DPI minimum**: Always render PDFs at 300 DPI. Use 600 DPI for mismatch verification (or if `--600dpi` flag).
4. **Verify all mismatches**: Never trust agent-reported mismatches without 600 DPI + text cross-reference.
5. **Agents stay in scope**: Agents only read their assigned pages. Cross-references and external PDFs get separate verification agents.
6. **Always cite pages**: Every finding must include a `#page=XX` citation (file page, NOT printed page). Exception: single-page PDFs.
7. **Error margin <= 1**: Flag any difference > 0.3 between repo and PDF values.
8. **Context preservation**: Never read large PDFs in Main Claude's context. Always delegate to agents.
9. **Multiple PDFs supported**: Collector downloads up to 5. Manifest maps PDF-to-topic. Audit agents read from whichever PDF covers their topic.
10. **No PDF gracefully handled**: Skip PDF audit agents, run code-only validators, note in report.
11. **Changelog**: Every PR needs a towncrier fragment in `changelog.d/<branch>.<type>.md`.

---

## Pre-Flight Checklist

Before starting:
- [ ] I will ask posting mode FIRST (unless --local flag used)
- [ ] I will NOT make any code changes
- [ ] I will NOT switch branches
- [ ] I will spawn pdf-collector in Phase 2 (ALWAYS)
- [ ] I will render PDFs at {DPI} DPI minimum
- [ ] I will verify all agent-reported mismatches at 600 DPI
- [ ] I will spawn verification agents for cross-references and external PDFs
- [ ] I will include #page=XX citations for all findings
- [ ] I will read ONLY short summary files — never raw PDFs or full agent reports
- [ ] I will be constructive and actionable

Start by parsing arguments, then proceed through all phases.
