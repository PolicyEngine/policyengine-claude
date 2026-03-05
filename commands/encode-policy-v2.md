---
description: Orchestrates multi-agent workflow to implement new government benefit programs (v2 — agent teams, user checkpoint, requirements tracking)
---

# Implementing $ARGUMENTS in PolicyEngine (v2)

Coordinate a multi-agent workflow to implement $ARGUMENTS as a complete, production-ready government benefit program.

**Design Principles:**
1. Pure orchestration — Main Claude never reads full files, only short summaries
2. Agent teams — TeamCreate/TaskCreate with dependencies
3. Branch-name prefix — all /tmp/ files use {PREFIX}- prefix
4. No orchestrator scoping — user approves scope at checkpoint
5. No orchestrator implementation guidance — agents read specs from disk + reference implementations
6. Independent regulatory verification — review-fix loop, not self-evaluation
7. Lessons learned — extract and persist after every run
8. Completeness tracking — every documented requirement tracked through to implementation

**GLOBAL RULE — PDF Page Numbers**: Every PDF reference href MUST end with `#page=XX` (the file page number, NOT the printed page number). The ONLY exception is single-page PDFs. This rule applies to ALL agents in ALL phases. Include this instruction in every agent prompt that touches parameter YAML files.

---

## Phase 0: Parse Arguments & Setup

### Step 0A: Parse Arguments

```
Parse $ARGUMENTS:
- STATE: state name (e.g., "Rhode Island", "Oregon")
- PROGRAM: program type (e.g., "CCAP", "TANF", "LIHEAP")
- OPTIONS:
  - --skip-review — skip Phase 6 (review-fix loop)
  - --research-only — stop after Phase 2 (scope review), produce spec but don't implement
  - --600dpi — render all PDFs at 600 DPI instead of 300 DPI
```

Derive:
- `ST` = state abbreviation lowercase (e.g., `ri`, `or`)
- `PROG` = program abbreviation lowercase (e.g., `ccap`, `tanf`)
- `BRANCH` = `{ST}-{PROG}` (e.g., `ri-ccap`)
- `PREFIX` = `{BRANCH}` (used for all /tmp/ files)
- `DPI` = 600 if `--600dpi`, else 300

**Resolve LESSONS_PATH** (used in all implementation agent prompts):
```bash
LESSONS_PATH=$(ls -d ~/.claude/projects/*/memory 2>/dev/null | head -1)/agent-lessons.md
```
Pass `{LESSONS_PATH}` to all agent prompts that include "LEARN FROM PAST SESSIONS".

### Step 0B: Clean Up & Create Team

```bash
rm -f /tmp/${PREFIX}-*.md
```

TeamCreate(`{PREFIX}-encode`)

### Step 0C: Spawn Setup Agents (Parallel)

Spawn both in parallel — they work on independent tasks:

**Agent 1: Issue Manager**

```
subagent_type: "complete:country-models:issue-manager"
team_name: "{PREFIX}-encode"
name: "issue-manager"
run_in_background: true

"Find or create a GitHub issue and draft PR for {STATE} {PROGRAM}.
- Search for existing issues/PRs first
- Create branch: {BRANCH}
- Push to fork, create draft PR to upstream using --repo PolicyEngine/policyengine-us
- Return: ISSUE_NUMBER, PR_NUMBER, PR_URL, BRANCH"
```

**Agent 2: Document Collector**

```
subagent_type: "complete:country-models:document-collector"
team_name: "{PREFIX}-encode"
name: "document-collector"
run_in_background: true

"Research {STATE} {PROGRAM} and gather all official documentation.
- Discover the state's official program name
- Download and extract PDFs with curl + pdftotext
- Render PDF screenshots at {DPI} DPI: pdftoppm -png -r {DPI} /tmp/doc.pdf /tmp/doc-page
- Save all documentation to sources/working_references.md
- Write SHORT research summary (max 20 lines) to /tmp/{PREFIX}-research-summary.md:
  - Official program name
  - Key sources found (with URLs)
  - Number of eligibility tests identified
  - Number of income deductions/exemptions found
  - Benefit calculation type (flat, formula, tiered)
  - Complexity hint (simple/complex)

RULES:
- PDF hrefs include #page=XX (file page number, NOT printed page number)
- DO NOT commit — pr-pusher handles all commits"
```

### Step 0D: Collect Setup Results

After both agents complete:
- Store ISSUE_NUMBER, PR_NUMBER, BRANCH from issue-manager
- Read ONLY `/tmp/{PREFIX}-research-summary.md` (max 20 lines)
- Report brief status to user

**Stop here if document-collector failed** — cannot proceed without documentation.

---

## Phase 1: Consolidation & Requirements Extraction

Spawn a consolidator agent to read the full documentation and produce structured specs.

```
subagent_type: "general-purpose"
team_name: "{PREFIX}-encode"
name: "consolidator"

"Read sources/working_references.md and produce structured implementation specs for {STATE} {PROGRAM}.

STEP 1: Study reference implementation.
Find a similar program in the codebase (e.g., CO CCAP for RI CCAP, DC TANF for OR TANF).
Search with: Glob 'policyengine_us/variables/gov/states/*/[agency]/{prog}/*.py'
Read 3-5 variable files and 3-5 parameter files from the reference implementation.

STEP 2: Write THREE files:

FILE 1: /tmp/{PREFIX}-impl-spec.md (FULL — for implementation agents)
- Every requirement from documentation, numbered (REQ-001, REQ-002, ...)
- Each requirement tagged: ELIGIBILITY, INCOME, BENEFIT, EXEMPTION, DEMOGRAPHIC, IMMIGRATION, RESOURCE, etc.
- Suggested variable and parameter structure (based on reference impl patterns)
- Income sources list (for sources.yaml parameter, NOT inline adds)
- Reference implementation paths to study
- For TANF: note simplified vs full approach recommendation
- For each requirement: cite the source (statute, manual section, page)

FILE 2: /tmp/{PREFIX}-requirements-checklist.md (SHORT — for orchestrator, max 40 lines)
- One line per requirement:
  REQ-001: [TAG] Description (source)
  REQ-002: [TAG] Description (source)
  ...
- Total count at top

FILE 3: /tmp/{PREFIX}-scope-summary.md (SHORT — for user checkpoint, max 15 lines)
- Program name and type
- Total requirements found: N
- Complexity assessment: simple (<=5 REQs) / complex (>5 REQs)
- Reference implementation: [path]
- Suggested approach (simplified/full for TANF)
- Key decision points (if any)

RULES:
- Number EVERY requirement — nothing gets lost
- Requirements include: eligibility criteria, income tests, deductions, exemptions,
  benefit calculations, demographic rules, immigration rules, resource limits,
  payment standards, co-payments, provider rates, work requirements (note as
  'not modeled' but still track)
- Tag requirements that are NOT simulatable (e.g., work activity hours) as [NOT-MODELED]
- For each requirement, note whether the reference implementation has it"
```

After consolidator completes, read ONLY:
- `/tmp/{PREFIX}-requirements-checklist.md` (max 40 lines)
- `/tmp/{PREFIX}-scope-summary.md` (max 15 lines)

---

## Phase 2: Scope Review (USER CHECKPOINT)

This phase walks the user through scope decisions one at a time using `AskUserQuestion` with structured options. Do NOT dump all requirements at once.

### Step 2A: Show Summary

Display a brief overview (from scope-summary.md):

```
## {STATE} {PROGRAM} — Scope Review

**Complexity**: {Simple/Complex} ({N} requirements)
**Reference impl**: {path}
```

Then list requirements grouped by tag. Example:

```
### Requirements Found ({N} total):

**Eligibility** ({X})
  REQ-001: Income <= 261% FPL (entry) — OAR 461-155-0180
  REQ-002: Income <= 300% FPL (transitional) — OAR 461-155-0180

**Benefit Calculation** ({X})
  REQ-006: Co-payment 0%/2%/5%/7% by FPL tier — OAR 461-155-0150
  REQ-007: Co-payment capped at 7% of income — 45 CFR 98.45

**Not Modeled** ({X})
  REQ-009: 20 hrs/week work activity requirement — OAR 461-135-0400
```

### Step 2B: Key Decisions (One at a Time)

For each key decision point identified in the scope summary, ask the user ONE question at a time using `AskUserQuestion`.

**Decision 1: Overall scope**

```
AskUserQuestion:
  Question: "Implement all {N} simulatable requirements? ({M} NOT-MODELED items will be excluded automatically)"
  Options:
    - "Yes, implement all" (default/recommended)
    - "Let me pick which to skip"
```

If user picks "Let me pick which to skip", present each questionable requirement group:

```
AskUserQuestion:
  Question: "Include {TAG} requirements?"
  Description: |
    REQ-XXX: {description}
    REQ-YYY: {description}
  Options:
    - "Yes, include all" (default)
    - "Skip these"
    - "Let me pick individually"
```

**Decision 2+: Program-specific complexity decisions**

If the scope summary identifies key decision points (e.g., provider rates, simplified vs full approach), ask each as a separate question:

```
AskUserQuestion:
  Question: "{Decision description}"
  Description: "{Brief context — e.g., 'Provider rates have ~240 rate cells. Implementing now adds complexity.'}"
  Options:
    - "{Option A}" (recommended if applicable)
    - "{Option B}"
    - "{Option C if needed}"
```

Examples of program-specific decisions:
- "Provider rates have ~240 rate cells — implement now or defer?"
  - "Defer to follow-up PR" (recommended)
  - "Implement now"
- "TANF approach — simplified or full?"
  - "Simplified (eligibility + benefit amount)" (recommended)
  - "Full (all components)"
- "13 income types have no PE equivalent — how to handle?"
  - "Map to closest existing variables" (recommended)
  - "Create new variables for each"
  - "Skip unmappable income types"

### Step 2C: Write Scope Decision

After all questions are answered, write the decision to `/tmp/{PREFIX}-scope-decision.md`:

```markdown
## Scope Decision for {STATE} {PROGRAM}

### In Scope
REQ-001: [ELIGIBILITY] Income <= 261% FPL (entry)
REQ-002: [ELIGIBILITY] Income <= 300% FPL (transitional)
...

### Excluded
REQ-009: [NOT-MODELED] 20 hrs/week work activity — Reason: not simulatable
REQ-010: [BENEFIT] Provider payment rates — Reason: user deferred

### Key Decisions
- Provider rates: deferred to follow-up PR
- Income variable gaps: map to closest existing variables

### User Notes
{any additional guidance from user}
```

**Stop here if `--research-only`.**

---

## Phase 3: Implementation

Create tasks with dependencies. Agents read specs from disk — orchestrator does NOT tell them HOW to implement.

### Step 3A: Create Parameters

```
subagent_type: "complete:country-models:parameter-architect"
team_name: "{PREFIX}-encode"
name: "create-parameters"

"Create parameters for {STATE} {PROGRAM}.
Read the implementation spec at /tmp/{PREFIX}-impl-spec.md.
Read the scope decision at /tmp/{PREFIX}-scope-decision.md.
Study the reference implementation listed in the impl spec.
Load skills: /policyengine-parameter-patterns, /policyengine-variable-patterns,
  /policyengine-code-organization.

LEARN FROM PAST SESSIONS (read if they exist — skip if not found):
- {LESSONS_PATH}
- lessons/agent-lessons.md

REUSE EXISTING VARIABLES AND PARAMETERS:
PolicyEngine-US has hundreds of existing variables for common concepts (fpg, smi,
tanf_fpg, is_tanf_enrolled, ssi, tanf_gross_earned_income, snap_gross_income, etc.).
Before creating ANY non-program-specific parameter or variable, Grep the codebase to
check if it already exists. Only create new ones for state-program-specific concepts.

RULES:
- Income source lists go in sources.yaml parameters, NOT inline adds
- Follow patterns from the reference implementation
- DO NOT skip any in-scope requirement (check against scope decision)
- Every value must have a reference with subsection and #page=XX for PDFs
- Store rates (not dollar amounts) when the legal code defines a percentage
- DO NOT commit — pr-pusher handles all commits"
```

### Step 3B: Create Variables and Tests (Parallel)

After parameters are complete, spawn both in parallel — they work on different folders.

**Agent: Rules Engineer**

```
subagent_type: "complete:country-models:rules-engineer"
team_name: "{PREFIX}-encode"
name: "create-variables"

"Create variables for {STATE} {PROGRAM}.
Read the implementation spec at /tmp/{PREFIX}-impl-spec.md.
Read the scope decision at /tmp/{PREFIX}-scope-decision.md.
Study the reference implementation listed in the impl spec.
Load skills: /policyengine-variable-patterns, /policyengine-parameter-patterns,
  /policyengine-vectorization, /policyengine-aggregation, /policyengine-period-patterns,
  /policyengine-code-style, /policyengine-code-organization.

LEARN FROM PAST SESSIONS (read if they exist — skip if not found):
- {LESSONS_PATH}
- lessons/agent-lessons.md

REUSE EXISTING VARIABLES AND PARAMETERS:
PolicyEngine-US has hundreds of existing variables for common concepts (fpg, smi,
tanf_fpg, is_tanf_enrolled, ssi, tanf_gross_earned_income, snap_gross_income, etc.).
Before creating ANY non-program-specific variable, Grep the codebase to check if it
already exists. Only create new ones for state-program-specific concepts.

RULES:
- Use the parameters created in Step 3A — read them from disk
- Zero hard-coded values — reference parameters only
- Income source lists go in sources.yaml parameters, NOT inline adds
- Use adds for pure sums, add() for sum + operations
- Verify person vs group entity level from the legal code
- Follow patterns from the reference implementation
- DO NOT skip any in-scope requirement (check against scope decision)
- DO NOT commit — pr-pusher handles all commits"
```

**Agent: Test Creator**

```
subagent_type: "complete:country-models:test-creator"
team_name: "{PREFIX}-encode"
name: "create-tests"

"Create tests for {STATE} {PROGRAM}.
Read the implementation spec at /tmp/{PREFIX}-impl-spec.md.
Read the scope decision at /tmp/{PREFIX}-scope-decision.md.
Read sources/working_references.md for calculation examples.
Load skills: /policyengine-testing-patterns, /policyengine-period-patterns,
  /policyengine-aggregation, /policyengine-variable-patterns, /policyengine-code-organization.

LEARN FROM PAST SESSIONS (read if they exist — skip if not found):
- {LESSONS_PATH}
- lessons/agent-lessons.md

REUSE EXISTING VARIABLES:
PolicyEngine-US has hundreds of existing variables. Use only real, existing variables
for test inputs. Grep the codebase to verify variable names before using them in tests.

RULES:
- Create UNIT tests for each variable that will have a formula
- Create INTEGRATION tests (5-7 scenarios) with inline calculation comments
- Use only existing PolicyEngine variables
- Period format: 2024-01 or 2024 only
- Test realistic values from documentation
- DO NOT skip any in-scope requirement (check against scope decision)
- DO NOT commit — pr-pusher handles all commits"
```

### Step 3C: Generate Edge Case Tests

After both variables and tests are complete:

```
subagent_type: "complete:country-models:edge-case-generator"
team_name: "{PREFIX}-encode"
name: "create-edge-cases"

"Generate edge case tests for {STATE} {PROGRAM}.
Read the scope decision at /tmp/{PREFIX}-scope-decision.md.
Analyze variables and parameters in the program folder.
Load skills: /policyengine-testing-patterns, /policyengine-variable-patterns.

LEARN FROM PAST SESSIONS (read if they exist — skip if not found):
- {LESSONS_PATH}
- lessons/agent-lessons.md

Focus on:
- Income at threshold boundaries (threshold-1, threshold, threshold+1)
- Zero income, maximum income
- Family size at min/max
- Negative income with zero deductions
- DO NOT commit — pr-pusher handles all commits"
```

### Step 3D: Integration into Benefits System (DISABLED)

<!-- DISABLED: Re-enable when ready to auto-integrate into household benefits.
After variables are created, Main Claude adds the main benefit variable to `policyengine_us/parameters/gov/household/household_state_benefits.yaml`:
- Add to ALL date entries in the file
- Add with a comment indicating the state

This is a small edit the orchestrator handles directly.
-->

**Currently disabled.** Integration into `household_state_benefits.yaml` will be done manually or in a future iteration.

### Step 3E: Requirements Coverage Check

After all implementation agents complete, spawn a requirements-tracker:

```
subagent_type: "general-purpose"
team_name: "{PREFIX}-encode"
name: "requirements-tracker"

"Cross-reference the scope decision against the implemented code for {STATE} {PROGRAM}.

READ:
- /tmp/{PREFIX}-scope-decision.md (what should be implemented)
- All parameter YAML files in the program folder
- All variable .py files in the program folder
- All test files in the program folder

FOR EACH in-scope requirement, verify it has:
- A parameter (if value-based)
- A variable (if logic-based)
- A test case

Write /tmp/{PREFIX}-coverage-report.md (max 40 lines):

## Requirements Coverage Report

### Covered
- REQ-001: param: entry_rate.yaml, var: ri_ccap_income_eligible.py, test: case 1
- REQ-002: param: transitional_rate.yaml, var: ri_ccap_income_eligible.py, test: case 2
...

### MISSING (action required)
- REQ-005: MISSING — no citizenship check in ri_ccap_child_eligible.py
- REQ-008: MISSING — no RI Works exemption in ri_ccap_co_payment.py
...

### Summary
- Total in-scope: N
- Covered: X
- Missing: Y"
```

Read ONLY `/tmp/{PREFIX}-coverage-report.md` (max 40 lines).

**If missing requirements > 0**: Spawn a gap-fixer to implement the missing requirements, then re-run the requirements-tracker:

```
subagent_type: "complete:country-models:rules-engineer"
team_name: "{PREFIX}-encode"
name: "gap-fixer"

"Implement MISSING requirements for {STATE} {PROGRAM}.
Read the coverage report at /tmp/{PREFIX}-coverage-report.md.
Read the implementation spec at /tmp/{PREFIX}-impl-spec.md.
Read the scope decision at /tmp/{PREFIX}-scope-decision.md.
Study existing variables and parameters already created for this program.
Load skills: /policyengine-variable-patterns, /policyengine-parameter-patterns,
  /policyengine-code-style, /policyengine-code-organization.

TASK: Implement ONLY the requirements listed under 'MISSING' in the coverage report.
Do not modify existing variables or parameters — only add what's missing.

REUSE EXISTING VARIABLES: Before creating any non-program-specific variable, Grep the
codebase first. PolicyEngine-US likely already has it.

LEARN FROM PAST SESSIONS (read if they exist — skip if not found):
- {LESSONS_PATH}
- lessons/agent-lessons.md

DO NOT commit — pr-pusher handles all commits."
```

After gap-fixer completes, re-run the requirements-tracker (same prompt as above) to verify all gaps are filled. If gaps remain after one fix round, report to user and proceed.

---

## Phase 4: Validation & Fix

### Step 4A: Implementation Validator

```
subagent_type: "complete:country-models:implementation-validator"
team_name: "{PREFIX}-encode"
name: "implementation-validator"

"Validate and fix {STATE} {PROGRAM} implementation for PolicyEngine standards compliance.
Load skills: /policyengine-variable-patterns, /policyengine-parameter-patterns,
  /policyengine-code-style, /policyengine-period-patterns, /policyengine-vectorization,
  /policyengine-aggregation, /policyengine-review-patterns, /policyengine-code-organization.

LEARN FROM PAST SESSIONS (read if they exist — skip if not found):
- {LESSONS_PATH}
- lessons/agent-lessons.md

Check AND fix: naming conventions, folder structure, parameter formatting, variable code style,
hard-coded values, adds vs add(), reference format, entity levels, period handling.
Fix all issues directly — do not just report them."
```

### Step 4B: CI Fixer

```
subagent_type: "complete:country-models:ci-fixer"
team_name: "{PREFIX}-encode"
name: "ci-fixer"

"Run tests for {STATE} {PROGRAM}, fix failures, iterate until all pass.
Load skills: /policyengine-testing-patterns, /policyengine-variable-patterns,
  /policyengine-code-style, /policyengine-period-patterns.
Read sources/working_references.md for policy rules.

LEARN FROM PAST SESSIONS (read if they exist — skip if not found):
- {LESSONS_PATH}
- lessons/agent-lessons.md

Run: policyengine-core test policyengine_us/tests/policy/baseline/gov/states/{ST}/... -c policyengine_us -v
Fix failures based on documentation. Iterate until pass.
After tests pass, run make format."
```

### Step 4C: Quick Audit

```
subagent_type: "general-purpose"
team_name: "{PREFIX}-encode"
name: "quick-auditor"

"Review git diff of changes for {STATE} {PROGRAM}. Check for:
- Hard-coded values added to pass tests
- Year-check conditionals (period.start.year)
- Altered parameter values
- Missing coverage from /tmp/{PREFIX}-coverage-report.md
Write SHORT report (max 15 lines) to /tmp/{PREFIX}-checkpoint.md: PASS/FAIL + issues."
```

Read ONLY `/tmp/{PREFIX}-checkpoint.md`.

### Step 4D: Push to Remote

```bash
git add policyengine_us/parameters/gov/states/{ST}/ policyengine_us/variables/gov/states/{ST}/ policyengine_us/tests/policy/baseline/gov/states/{ST}/
git commit -m "Implement {STATE} {PROGRAM} (ref #{ISSUE_NUMBER})"
git push
```

---

## Phase 5: Format, Push & PR Description

### Step 5A: Push & Changelog

```
subagent_type: "complete:country-models:pr-pusher"
team_name: "{PREFIX}-encode"
name: "pr-pusher"

"Ensure {STATE} {PROGRAM} PR is ready:
- Create changelog fragment in changelog.d/ (towncrier format)
- Run make format
- Push branch"
```

### Step 5B: PR Description

```
subagent_type: "general-purpose"
team_name: "{PREFIX}-encode"
name: "reporter"

"Write PR description for {STATE} {PROGRAM}.

READ:
- /tmp/{PREFIX}-scope-decision.md (scope)
- /tmp/{PREFIX}-coverage-report.md (requirements coverage)
- /tmp/{PREFIX}-research-summary.md (sources)
- /tmp/{PREFIX}-impl-spec.md (regulatory details)
- sources/working_references.md (references)

Write /tmp/{PREFIX}-pr-description.md:

## Summary
Implements {STATE_FULL} {PROGRAM_FULL} in PolicyEngine.
Closes #{ISSUE_NUMBER}

## Regulatory Authority
- [Source 1](URL#page=XX)
- [Source 2](URL#page=XX)

## Income Eligibility Tests
{Each test with source citation}

## Income Deductions & Exemptions
{Each deduction with source citation}

## Income Standards
| Family Size | Payment Standard |
|-------------|-----------------|
| 1 | $XXX |
| 2 | $XXX |
...

## Benefit Calculation
{Formula and rules with sources}

## Requirements Coverage
| REQ | Description | Param | Variable | Test |
|-----|-------------|-------|----------|------|
{From coverage report}

## Not Modeled
{Excluded requirements with reasons}

## Files Added
{Tree structure of new files}

Also write SHORT final report (max 25 lines) to /tmp/{PREFIX}-final-report.md:
- Total requirements: N implemented, M excluded
- Files: X parameters, Y variables, Z tests
- Coverage: XX%
- Issue #{ISSUE_NUMBER}, PR #{PR_NUMBER}"
```

After reporter completes:

```bash
gh pr edit $PR_NUMBER --body-file /tmp/{PREFIX}-pr-description.md
```

Read ONLY `/tmp/{PREFIX}-final-report.md`.

---

## Phase 6: Review-Fix Loop

**Skip if `--skip-review`.**

This phase runs `/review-program` and fixes critical issues in a loop until zero critical issues remain (or max iterations reached).

### Loop Structure

```
ROUND = 1
MAX_ROUNDS = 3

while ROUND <= MAX_ROUNDS:
    1. Run /review-program $PR_NUMBER --local --full
    2. Read /tmp/review-program-summary.md → count critical issues
    3. If critical == 0 → EXIT LOOP (success)
    4. If ROUND == MAX_ROUNDS → EXIT LOOP (escalate to user)
    5. If ROUND == 2 → ask user before attempting round 3
    6. Fix critical issues
    7. Run make format + tests
    8. Commit + push fixes
    9. ROUND += 1
```

### Step 6A: Run /review-program (Round N)

Invoke the `review-program` skill in local-only mode with `--full`:

```
Skill: review-program
Arguments: $PR_NUMBER --local --full [--600dpi if DPI == 600]
```

If the user passed `--600dpi`, include it here so PDF audit uses high resolution.

### Step 6B: Check Results

Read `/tmp/review-program-summary.md` (max 20 lines).

**If critical == 0**: Report to user and exit loop.

**If critical > 0 and ROUND < MAX_ROUNDS**: Proceed to Step 6C.

**If critical > 0 and ROUND == 2**: Ask user before round 3:
```
"Review found {N} critical issues after 2 fix rounds. Attempt a 3rd round?"
Options: "Yes, try one more round" / "No, stop and show remaining issues"
```

**If critical > 0 and ROUND == MAX_ROUNDS (3)**: Exit loop, report remaining issues.

### Step 6C: Fix Critical Issues

```
subagent_type: "complete:country-models:rules-engineer"
team_name: "{PREFIX}-encode"
name: "review-fixer-{ROUND}"

"Fix the critical issues from the /review-program review (round {ROUND}).
Read the full review report at /tmp/review-program-full-report.md.
Focus ONLY on items marked CRITICAL — do not change anything else.
Load skills: /policyengine-variable-patterns, /policyengine-code-style,
  /policyengine-parameter-patterns, /policyengine-period-patterns, /policyengine-vectorization.
Apply fixes. Run make format.

REUSE EXISTING VARIABLES: Before creating any non-program-specific variable, Grep the
codebase first. PolicyEngine-US likely already has it (fpg, smi, tanf_fpg, ssi, etc.).

LEARN FROM PAST SESSIONS (read if they exist — skip if not found):
- {LESSONS_PATH}
- lessons/agent-lessons.md

LEARN FROM PREVIOUS ROUNDS:
If /tmp/{PREFIX}-checklist.md exists, read it FIRST. It contains issues
found and fixed in previous rounds. Do NOT reintroduce any of those patterns.

AFTER fixing, APPEND your fixes to /tmp/{PREFIX}-checklist.md:
Format each line as:
- [ROUND {ROUND}] [{CATEGORY}] {file}:{line} — {what was wrong} → {what you changed}

Categories: HARD-CODED, WRONG-PERIOD, MISSING-REF, BAD-REF, DEDUCTION-ORDER,
UNUSED-PARAM, WRONG-ENTITY, NAMING, FORMULA-LOGIC, TEST-GAP, OTHER"
```

### Step 6D: Verify Fix & Commit

Run ci-fixer, then commit and push:

```
subagent_type: "complete:country-models:ci-fixer"
team_name: "{PREFIX}-encode"
name: "ci-fixer-{ROUND}"

"Run tests for {STATE} {PROGRAM} after review-fix round {ROUND}.
Fix any test failures introduced by the fixes. Run make format."
```

```bash
git add policyengine_us/parameters/gov/states/{ST}/ policyengine_us/variables/gov/states/{ST}/ policyengine_us/tests/policy/baseline/gov/states/{ST}/
git commit -m "Review-fix round {ROUND}: address critical issues from /review-program"
git push
```

Increment ROUND and go back to Step 6A.

---

## Phase 7: Lessons Learned

**This phase runs even if the review-fix loop was skipped.**

### Step 7A: Extract Lessons

```
subagent_type: "general-purpose"
team_name: "{PREFIX}-encode"
name: "lesson-extractor"

"Distill lessons learned from the {STATE} {PROGRAM} implementation session.

READ these files (skip any that don't exist):
- /tmp/{PREFIX}-checklist.md (review-fix checklist)
- /tmp/{PREFIX}-checkpoint.md (validation checkpoint)
- /tmp/{PREFIX}-coverage-report.md (requirements coverage)
- /tmp/review-program-summary.md (last review summary)

ALSO READ the persistent lessons file (if it exists):
- {LESSONS_PATH}

TASK:
1. Extract every issue that was found and fixed during this session
2. Generalize each fix into a one-line rule (remove file names, line numbers, state names)
3. Categorize each rule:
   - PARAMETER: structure, metadata, references, dates, descriptions
   - VARIABLE: hard-coding, periods, entities, formulas, branching
   - TEST: coverage, boundaries, periods, naming
   - REFERENCE: URLs, page numbers, specificity, liveness
   - FORMULA: deduction order, unused params, zero-sentinels, logic
   - WORKFLOW: agent coordination, scope gaps, missing requirements
4. Deduplicate against existing persistent lessons — only keep genuinely NEW rules
5. If no new lessons: write 'NO NEW LESSONS' to /tmp/{PREFIX}-new-lessons.md
6. If new lessons exist, write to /tmp/{PREFIX}-new-lessons.md (max 15 entries):

   ## New Lessons from {STATE} {PROGRAM} ({date})

   ### PARAMETER
   - {generalized rule}

   ### WORKFLOW
   - {generalized rule}

   (Only include categories that have new lessons.)"
```

### Step 7B: Persist Lessons

Read `/tmp/{PREFIX}-new-lessons.md`.

**If 'NO NEW LESSONS'**: Skip to final summary.

**If new lessons exist**: Persist to BOTH locations (local memory + repo):

```bash
# 1. Persist to local memory (survives across sessions even without repo)
LESSONS_FILE="$LESSONS_PATH"
if [ ! -f "$LESSONS_FILE" ]; then
    echo "# Agent Lessons Learned (Local)" > "$LESSONS_FILE"
    echo "" >> "$LESSONS_FILE"
fi
cat /tmp/${PREFIX}-new-lessons.md >> "$LESSONS_FILE"

# 2. Persist to repo (shared across all contributors)
LESSONS_PLUGIN="$(pwd)/lessons/agent-lessons.md"
if [ ! -f "$LESSONS_PLUGIN" ]; then
    echo "# Agent Lessons Learned" > "$LESSONS_PLUGIN"
    echo "" >> "$LESSONS_PLUGIN"
    echo "Accumulated from /encode-policy-v2 and /backdate-program runs across all contributors." >> "$LESSONS_PLUGIN"
    echo "Loaded by implementation agents on future runs." >> "$LESSONS_PLUGIN"
    echo "" >> "$LESSONS_PLUGIN"
fi
cat /tmp/${PREFIX}-new-lessons.md >> "$LESSONS_PLUGIN"
git add lessons/agent-lessons.md
git commit -m "Add lessons from ${STATE} ${PROGRAM} implementation"
git push
```

### Step 7C: Final Summary

Present to user:
- Total requirements implemented vs excluded
- Files created (parameters, variables, tests)
- Requirements coverage percentage
- Review-fix loop results (if ran)
- New lessons extracted (if any)
- Issue and PR links
- **Keep PR as draft** — user will mark ready when they choose
- **WORKFLOW COMPLETE**

---

## Handoff Table

| File | Written By | Read By | Size |
|------|-----------|---------|------|
| `sources/working_references.md` | document-collector | consolidator | Full |
| `/tmp/{PREFIX}-research-summary.md` | document-collector | Main Claude | Short (20 lines) |
| `/tmp/{PREFIX}-impl-spec.md` | consolidator | all impl agents | Full |
| `/tmp/{PREFIX}-requirements-checklist.md` | consolidator | Main Claude | Short (40 lines) |
| `/tmp/{PREFIX}-scope-summary.md` | consolidator | Main Claude | Short (15 lines) |
| `/tmp/{PREFIX}-scope-decision.md` | Main Claude | all impl agents | Short |
| `/tmp/{PREFIX}-coverage-report.md` | requirements-tracker | Main Claude, reporter | Short (40 lines) |
| `/tmp/{PREFIX}-checkpoint.md` | quick-auditor | Main Claude | Short (15 lines) |
| `/tmp/{PREFIX}-pr-description.md` | reporter | gh pr edit | Full |
| `/tmp/{PREFIX}-final-report.md` | reporter | Main Claude | Short (25 lines) |
| `/tmp/{PREFIX}-new-lessons.md` | lesson-extractor | Main Claude | Short |
| `/tmp/{PREFIX}-checklist.md` | review-fixer (append) | review-fixer (read) | Growing |

---

## Error Handling

### Error Categories

| Category | Example | Action |
|----------|---------|--------|
| **Recoverable** | Test failure, lint error | ci-fixer handles automatically |
| **Delegation** | Policy logic wrong | ci-fixer delegates to specialist agent |
| **Missing coverage** | Requirement not implemented | Spawn rules-engineer to fill gap |
| **Blocking** | GitHub API down, branch conflict | Stop and report to user |

### Error Handling by Phase

- **Phase 0 (Setup):** If agent fails, report error and STOP.
- **Phase 1 (Consolidation):** If consolidator fails, report and STOP.
- **Phase 2 (Scope):** User-driven — no error possible.
- **Phase 3 (Implementation):** If agent fails, report which agent failed and wait for user.
- **Phase 3E (Coverage):** If missing requirements, fix automatically then re-check.
- **Phase 4 (Validation):** ci-fixer handles fixes. If ci-fixer fails 3 times, report and STOP.
- **Phase 5-7:** Continue unless blocking error.

### Escalation Path

1. Agent encounters error — Log and attempt fix if recoverable
2. Fix fails — ci-fixer delegates to specialist agent
3. Delegation fails — Report to user and STOP
4. Never proceed to next phase with unresolved blocking errors

---

## Execution Instructions

**YOUR ROLE**: You are an orchestrator ONLY. You must:
1. Invoke agents using the Agent tool (with team_name for coordination)
2. Wait for their completion
3. Read ONLY short summary files (see Handoff Table — "Short" column)
4. Write scope-decision file based on user input
5. Proceed to the next phase automatically

**YOU MUST NOT:**
- Read full implementation files (sources/working_references.md, impl-spec, etc.)
- Write any code yourself
- Fix any issues manually
- Run tests directly
- Tell agents HOW to implement — they read specs and reference impls from disk

**Execution Flow (CONTINUOUS except at Phase 2 checkpoint):**

0. **Phase 0**: Parse, clean up, spawn issue-manager + document-collector in parallel
1. **Phase 1**: Spawn consolidator to produce impl-spec, requirements-checklist, scope-summary
2. **Phase 2**: **USER CHECKPOINT** — present requirements, wait for scope approval
3. **Phase 3**: Implementation (parameters → variables+tests in parallel → edge cases → coverage check)
4. **Phase 4**: Validation (validator → ci-fixer → quick-audit → push)
5. **Phase 5**: Format, push, PR description
6. **Phase 6**: Review-fix loop (up to 3 rounds of /review-program → fix → re-review)
7. **Phase 7**: Lessons learned, final summary, **WORKFLOW COMPLETE**

**CRITICAL RULES:**
- Run all phases continuously without waiting for user input (EXCEPT Phase 2)
- If an agent fails, attempt recovery through ci-fixer; only stop if unrecoverable
- All phases are REQUIRED (unless --skip-review or --research-only)
- Report final summary at the end
- Keep PR as draft — user marks ready when they choose
