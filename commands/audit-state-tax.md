---
description: Audit a state income tax PR's parameter values against official PDF sources (read-only, no code changes)
---

# Auditing State Tax PR: $ARGUMENTS

**READ-ONLY MODE**: This command audits parameter values in a state income tax PR against official PDF sources and posts findings to GitHub. It does NOT make code changes.

## Arguments

`$ARGUMENTS` should contain:
- **PR number** (required) — e.g., `7130`
- **PDF URL** (optional) — link to the state's official tax form instructions or tax guide. If omitted, the command will auto-discover the source.
- **Options**:
  - `--local` — show findings locally only, skip GitHub posting
  - `--full` — audit ALL implemented parameters (not just PR changes) against the PDF

**Examples:**
```
/audit-state-tax 7130
/audit-state-tax 7130 --full
/audit-state-tax 7130 --local
/audit-state-tax 7130 https://oregon.gov/.../form-or-40-inst_2025.pdf
/audit-state-tax 7130 https://oregon.gov/.../form-or-40-inst_2025.pdf --full
```

---

## Phase 0: Parse Arguments & Setup

```
Parse $ARGUMENTS:
- PR_NUMBER: first numeric argument
- PDF_URL: first URL argument (may be empty — will auto-discover in Phase 1.5)
- LOCAL_ONLY: true if --local flag present
- FULL_AUDIT: true if --full flag present
```

### Determine Posting Mode

**If `--local` flag**: Skip prompt, proceed in local-only mode.

**If no flag**: Use `AskUserQuestion`:
```
Question: "Post audit findings to GitHub when complete?"
Options:
  - "Yes, post to GitHub" (default)
  - "No, show locally only"
```

---

## Phase 1: Gather PR Context

Collect information about the PR without switching branches:

```bash
gh pr view $PR_NUMBER --json title,body,author,baseRefName,headRefName
gh pr diff $PR_NUMBER > /tmp/state-tax-pr-diff.txt
```

From the diff, identify:
- **State abbreviation** (e.g., `or`, `md`) from file paths like `parameters/gov/states/{st}/tax/`
- **Tax year** being updated
- **Files changed**: parameter YAMLs, variable Python files, tests
- **What topics are covered**: rates, deductions, credits, exemptions, etc.

---

## Phase 1.5: Auto-Discover PDF Source (if no URL provided)

**Skip this phase if the user provided a PDF URL.**

### Step 1: Check the PR for source links

Scan the PR body and YAML parameter files in the diff for existing PDF references:
```bash
# Check PR description for PDF links
gh pr view $PR_NUMBER --json body --jq '.body' | grep -oE 'https?://[^ )]*.pdf[^ )]*'

# Check YAML files in the diff for reference fields
gh pr diff $PR_NUMBER | grep -i 'reference\|source\|\.pdf\|\.gov'
```

If a clear official source PDF URL is found (e.g., a `.gov` domain tax instruction booklet), use it and skip to Phase 2.

### Step 2: Search for the official instruction booklet

Using the **state abbreviation** and **tax year** from Phase 1:

```
Map state abbreviation to:
- STATE_FULL_NAME (e.g., "or" → "Oregon")
- STATE_REVENUE_SITE (e.g., "or" → "oregon.gov/dor")
```

Search in order of priority:
1. **WebSearch**: `"{State full name} {year} income tax instruction booklet site:{state}.gov filetype:pdf"`
2. **WebSearch**: `"{State full name} {year} resident income tax form instructions site:{state}.gov"`
3. **WebSearch**: `"{State full name} {year} tax guide publication site:{state}.gov"` (some states publish a comprehensive guide, e.g., OR-17)
4. **WebFetch** the state revenue department's main tax forms page to find download links

### Step 3: Validate the PDF

Before proceeding, confirm the discovered PDF is correct:
- Download it: `curl -L -o /tmp/{state}-audit-source.pdf "URL"`
- Check page count: `pdfinfo /tmp/{state}-audit-source.pdf | grep Pages`
- Extract first page text: `pdftotext -f 1 -l 2 /tmp/{state}-audit-source.pdf -`
- Verify it matches the expected state, tax year, and document type (instruction booklet, not just a blank form)

If the PDF looks wrong (e.g., wrong year, wrong state, just a form without instructions), try the next search result.

### Step 4: Check for supplementary documents

Some states split tax information across multiple documents. After finding the main booklet, check:
- Does the booklet reference other publications? (e.g., OR-40 instructions reference OR-17 guide)
- Are there separate rate schedules, tax tables, or credit worksheets?
- Note these for later — they'll be fetched by verification agents if needed during Phase 5.

---

## Phase 2: Download & Prepare PDF

**If PDF was already downloaded and validated in Phase 1.5**, skip the download step.

```bash
# Download PDF (skip if already done in Phase 1.5)
curl -L -o /tmp/{state}-audit-source.pdf "$PDF_URL"

# Extract text for cross-referencing
pdftotext /tmp/{state}-audit-source.pdf /tmp/{state}-audit-source.txt

# Render all pages at 300 DPI for agent reading
pdftoppm -png -r 300 /tmp/{state}-audit-source.pdf /tmp/{state}-audit-page

# Get page count
pdfinfo /tmp/{state}-audit-source.pdf | grep Pages
```

**Determine PDF page offset** — read the first few pages to count preliminary pages (cover, TOC, intro) before instruction page 1. This offset is critical for verifying `#page=XX` references.

---

## Phase 3: Map Files to Topics & Pages

### Identify repo files to audit

**If `--full` flag**: Scan the full repo tree for this state:
```
parameters/gov/states/{st}/tax/income/
variables/gov/states/{st}/tax/income/
```

**If no `--full` flag**: Use only files from the PR diff.

### Identify PDF page ranges per topic

Read the extracted text to identify major sections and page boundaries. Map each topic to its page range:

| Topic | Example page range | What to look for |
|-------|-------------------|------------------|
| Standard deduction | pp. 15-17 | Filing status amounts, aged/blind additions |
| Tax rates & brackets | pp. 17-18, 30-32 | Rate schedules, tax computation charts |
| Credits (CTC, EITC, etc.) | pp. 19-25 | Credit amounts, match rates, AGI limits |
| Subtractions | pp. 8-14 | Federal tax caps, pension exclusions |
| Exemptions | pp. 6-8 | Personal/dependent amounts |

### Split into agent topics

Split audit work by **tax topic**, not by page number. Typical split:

| Agent | Topic | Repo files | PDF pages |
|-------|-------|-----------|-----------|
| 1 | Deductions & Subtractions | `deductions/`, `subtractions/` | {pages} |
| 2 | Tax Rates & Brackets | `rates/` | {pages} |
| 3 | Credits | `credits/` | {pages} |

Fewer agents if the state has fewer provisions. More if it has complex local taxes or many credits. Aim for 2-5 agents.

---

## Phase 4: Spawn Audit Agents

Spawn all audit agents in parallel using `run_in_background: true` with `subagent_type: general-purpose`.

### Audit Agent Prompt Template

Each agent gets this prompt, customized with its assigned pages and files:

```
You are auditing {State}'s {year} tax parameters against the official instruction booklet.

TASK: Report only - do NOT edit any files.

1. Read the PDF page screenshots at /tmp/{state}-audit-page-{NN}.png for pages {X}-{Y}
   IMPORTANT: Only read your assigned pages ({X}-{Y}). Do NOT read pages outside your range.

2. Read all parameter files under: {list of YAML paths}

3. Read all variable files under: {list of Python paths}

4. For each parameter/variable, compare the repo value against the PDF:
   - Check numerical values (rates, thresholds, amounts, brackets)
   - Check effective dates ({year} vs earlier years)
   - Check filing status variations
   - Check uprated values - if a parameter uses uprating, compute the uprated value
     and compare against the PDF. If they differ, flag it.
   - Note any "New for {year}" changes

5. Report:
   a. MATCHES: Parameters that are correct
   b. MISMATCHES: Parameters where repo differs from PDF (cite both values and PDF page)
   c. MISSING FROM REPO: Things in the PDF we don't model
   d. MISSING FROM PDF: Things in the repo not found in this PDF section

6. If the booklet says "refer to page XX" and that page is OUTSIDE your assigned range:
   CROSS-REFERENCE NEEDED: page {XX} - need to verify [what value] for [which parameter].
   Repo value: [Y], reason: [why you need this page].

7. If a parameter file references another PDF, or the booklet says "See [other publication]":
   EXTERNAL PDF NEEDED: "[Document name]" - need to verify [what value/table] for [which parameter].
   Expected value: [X], repo value: [Y], reason: [why you suspect a mismatch].

Do NOT read pages outside your assigned range.
Do NOT guess values you haven't seen. Flag it and move on.
```

---

## Phase 5: Collect Results & Handle Flags

### Collect all agent reports

Wait for all audit agents to complete. Collect their findings.

### Handle CROSS-REFERENCE NEEDED flags

For each cross-reference flag, spawn a **verification agent** with a focused prompt:

```
You are verifying a cross-reference for a state tax audit.

TASK: Read a specific page and report what you find. Report only - do NOT edit any files.

WHAT TO VERIFY:
- Page to read: /tmp/{state}-audit-page-{XX}.png
- Value in question: {what the audit agent asked for}
- Repo value: {from the flag}
- Context: {from the flag}

STEPS:
1. Read the page screenshot at the path above
2. Find the specific value requested
3. Report:
   - The value you see on that page
   - What confirms it (table name, worksheet line, etc.)
   - PDF page number for citation: #page=XX
```

### Handle EXTERNAL PDF NEEDED flags

For each external PDF flag, spawn a **verification agent** with a focused prompt:

```
You are verifying a value from an external PDF for a state tax audit.

TASK: Find, download, and verify the following. Report only - do NOT edit any files.

WHAT TO VERIFY:
- Document: {document name from the flag}
- State revenue site: {e.g., oregon.gov/dor}
- Value in question: {from the flag}
- Repo value: {from the flag}
- Expected value: {from the flag}
- Reason for suspicion: {from the flag}

STEPS:
1. WebSearch for the document: "{document name} {year} site:{state revenue site}"
2. Download: curl -L -o /tmp/{filename}.pdf "URL"
3. Extract text: pdftotext /tmp/{filename}.pdf /tmp/{filename}.txt
4. Render at 300 DPI: pdftoppm -png -r 300 /tmp/{filename}.pdf /tmp/{filename}-page
5. Read the text and/or page screenshots to find the value
6. Report:
   - PDF URL (for reference link with #page=XX)
   - Correct value with exact PDF page number
   - What you see on that page that confirms it
```

---

## Phase 5.5: Verify Mismatches via Agent Discussion

**Never trust agent-reported mismatches without verification.** Agents commonly produce false positives — a parameter value may look wrong in isolation but be correct because:
- The parameter is only used in a deprecated code path (e.g., pre-2023)
- The value is automatically inherited from a federal variable
- The parameter interacts with other parameters in a way the audit agent didn't trace

For each MISMATCH reported by an audit agent, spawn a **verification team** where a verifier agent and the original audit agent discuss the finding.

### Step 1: Create a verification team

For each mismatch (or group of related mismatches from the same audit agent):

```
TeamCreate(team_name="verify-mismatch-{N}")
```

### Step 2: Spawn the verifier agent

Spawn a new `general-purpose` agent as a teammate with this prompt:

```
You are a code-path verifier for a state tax audit. An audit agent reported
a MISMATCH and you must determine if it's a real issue or a false positive.

REPORTED MISMATCH:
- Parameter: {parameter name and file path}
- Repo value: {value}
- Expected value: {value from source}
- Audit agent's reasoning: {summary from their report}

YOUR TASK:
1. Grep for ALL usages of this parameter across the codebase
2. For each variable that references it, trace the call chain:
   - Is it called from the {year}+ code path?
   - Or only from a deprecated/disabled path?
3. Check if the parameter's value actually affects the target tax year's
   computation by following the execution flow from the top-level tax
   variable (e.g., ia_income_tax) down to this parameter
4. Check if the value might be correct due to interaction with other
   parameters (e.g., a flag that disables the feature, a separate
   variable that overrides it)

After your analysis, message the audit agent with your findings and
any questions. Discuss until you reach a verdict.

VERDICT must be one of:
- CONFIRMED: The mismatch is real and affects {year} calculations
- REJECTED: The parameter doesn't affect {year} (explain why)
- INCONCLUSIVE: Unable to determine (explain what's unclear)

Report your verdict with full reasoning.
```

### Step 3: Resume the original audit agent as a teammate

Resume the audit agent that reported the mismatch using `resume: {agent_id}`:

```
A verifier agent is checking your mismatch finding for [{parameter}].
They may message you with questions about your reasoning.
Answer their questions based on your earlier analysis.
If they present evidence that the parameter isn't used in the {year}
code path, acknowledge it. If you have evidence it IS used, explain
the code path.
```

### Step 4: Let them discuss

Allow up to 3-4 message round-trips. The verifier traces code, the audit agent defends or concedes.

### Step 5: Collect verdicts

After the team reaches consensus:
- **CONFIRMED** mismatches proceed to Phase 6 for 600 DPI visual verification
- **REJECTED** mismatches are excluded from the final report (but noted as "investigated and cleared")
- **INCONCLUSIVE** mismatches proceed to Phase 6 for manual verification

Shut down the verification team after collecting the verdict.

---

## Phase 6: Verify Confirmed Mismatches

For each mismatch that was **CONFIRMED** or **INCONCLUSIVE** in Phase 5.5:

1. **Re-render at 600 DPI** for the disputed page:
   ```bash
   pdftoppm -png -r 600 -f PAGE -l PAGE /tmp/{state}-audit-source.pdf /tmp/{state}-audit-600dpi
   ```

2. **Cross-reference with extracted text** — check `/tmp/{state}-audit-source.txt` to confirm or deny what the agent read

3. **Check for false positives** — agents commonly misread values in dense tables

4. **Check uprating math** — if a parameter uses uprating, manually compute:
   `last_value x (new_index / old_index)`. If the uprated value doesn't match the PDF, an explicit value entry is needed.

5. **Check for logic gaps** — the value may be correct but the formula may not enforce all rules (e.g., a hard AGI cap that the code doesn't implement)

**Error margin**: Differences should never exceed 1. Use 0.1 or 0.3 as acceptable tolerance.

---

## Phase 7: Verify Reference Page Numbers

If the PR adds PDF references (`#page=XX`), verify every anchor points to the correct PDF page.

### Common Pitfall: Instruction Page vs PDF Page
Authors often use the **instruction page number** (printed at bottom of page) instead of the **PDF page number**. These differ by the number of preliminary pages.

For each file with a reference:
1. Read the YAML to get the `#page=XX` value
2. Read `/tmp/{state}-audit-page-{XX}.png` to check if the referenced value is actually on that page
3. If wrong, find the correct page

---

## Phase 8: Post Findings

### Compile all findings into a single report

**If user chose local-only mode**: Display findings locally and stop.

**If user chose to post to GitHub**: Post as PR comment.

### PR Comment Structure

```bash
gh pr comment $PR_NUMBER --body "## State Tax Parameter Audit

### Source
- **PDF**: [Document title](URL)
- **Tax year**: {year}
- **Scope**: {PR changes only / Full audit of all implemented parameters}

### Parameter Value Issues

| File | Parameter | Repo Value | PDF Value | PDF Page | Status |
|------|-----------|-----------|-----------|----------|--------|
| path/to/file.yaml | description | $X | $Y | [p.NN](URL#page=NN) | MISMATCH |

### Reference Page Corrections

| File | Current Page | Correct Page | Confirmation |
|------|-------------|-------------|--------------|
| path/to/file.yaml | #page=X | **#page=Y** | What's on that page |

### Confirmed Correct
- {count} parameter values verified against PDF
- {summary of what matched}

### Pre-existing Issues (not from this PR)
{Any issues found that predate the PR}

### Unmodeled Items
{Provisions in the PDF not implemented in the repo — for reference only}
"
```

---

## Key Rules

1. **READ-ONLY**: Never edit files. Never switch branches. This is an audit.
2. **300 DPI minimum**: Always render PDFs at 300 DPI. Use 600 DPI for mismatch verification.
3. **Verify all mismatches via discussion**: Every mismatch must go through Phase 5.5 (agent discussion) before Phase 6 (visual verification). Never include a mismatch in the final report without both code-path verification AND visual confirmation.
4. **Agents stay in scope**: Agents only read their assigned pages. Cross-references and external PDFs get separate verification agents.
5. **Always cite pages**: Every finding must include a `#page=XX` citation.
6. **Error margin <= 1**: Flag any difference > 0.3 between repo and PDF values.
7. **Context preservation**: Never read large PDFs in the main context. Always delegate to agents.
8. **Trace code paths**: A parameter mismatch is only real if the parameter is actually used in the target tax year's computation. Always verify the parameter is reachable from the top-level tax variable.

---

## Pre-Flight Checklist

Before starting:
- [ ] I will NOT make any code changes
- [ ] I will NOT switch branches
- [ ] I will render PDF at 300 DPI minimum
- [ ] I will verify all mismatches via Phase 5.5 agent discussion before reporting
- [ ] I will verify confirmed mismatches at 600 DPI in Phase 6
- [ ] I will spawn verification agents for cross-references and external PDFs
- [ ] I will include #page=XX citations for all findings
- [ ] I will be constructive and actionable in the PR comment

Start by parsing arguments, then proceed through all phases.
