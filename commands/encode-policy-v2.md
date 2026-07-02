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

## When to use vs `/encode-reform`

Rule of thumb:

| The target program... | Command |
|---|---|
| Does NOT exist in PolicyEngine yet (new state credit, new benefit, new deduction family) | `/encode-policy-v2` (this command) |
| Exists in PolicyEngine and you're changing PARAMETERS (raise a cap, add a phase-out, change a match rate) | `/encode-reform` |
| Exists but you're adding a NEW STRUCTURAL COMPONENT (new phase-out rule, new eligibility gate that requires a formula edit) | `/encode-policy-v2` (structural additions to existing programs are treated as new-program work) |

### Pre-flight — check whether the program already exists

Before Phase 1 kicks off, `/encode-policy-v2` should run:

```bash
gh api "repos/PolicyEngine/policyengine-{country}/contents/policyengine_{country}/variables/gov/states/{state}/tax/income/credits/{program}" 2>/dev/null
```

If the directory exists AND the reform is purely parametric, print:

```
The {program} exists in policyengine-{country}. If you're changing parameters
(caps, rates, thresholds), use /encode-reform instead — it's the lighter-weight
workflow for existing-program reforms. This command is for adding a new program
or a new structural component.

Continue anyway? (y/N)
```

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

## Standard agent boilerplate

- **Lessons** — each spawn prompt below contains a literal `LESSONS_PATH: {LESSONS_PATH}` line. Each agent file's "Lessons from past sessions" section tells the agent to read it (plus `lessons/agent-lessons.md` repo-relative). Don't strip the line — it's load-bearing.
- **Do not commit** — every implementation agent's definition already says "DO NOT commit; pr-pusher handles all commits." Don't restate in prompts.

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
  - **Failed fetches**: list any URLs that returned 403, redirected, or timed out (with a brief description of what they likely contain)

RULES:
- PDF hrefs include #page=XX (file page number, NOT printed page number)
"
```

### Step 0D: Collect Setup Results

After both agents complete:
- Store ISSUE_NUMBER, PR_NUMBER, BRANCH from issue-manager
- Read ONLY `/tmp/{PREFIX}-research-summary.md` (max 20 lines)
- Report brief status to user

**Stop here if document-collector failed** — cannot proceed without documentation.

### Step 0E: Unreachable Reference Checkpoint (USER CHECKPOINT)

After document-collector completes, check its research summary for any references that **failed to fetch** (403, redirect, timeout, connection refused). State agency websites (e.g., NH DHHS, many .gov sites) commonly block automated access while working fine in a browser.

**If unreachable references exist**, present them to the user using `AskUserQuestion`:

```
AskUserQuestion:
  Question: "The document collector could not access these references automatically. Please check them in your browser — if any contain useful data (rate tables, cost share schedules, policy changes), download them and send the file paths."
  Header: "References"
  Options:
    - "I'll download and send files" — wait for user to provide file paths, then re-run document-collector or have a general-purpose agent extract text/screenshots from the user-provided PDFs into sources/working_references.md
    - "Skip these, proceed with what we have" — continue to Phase 1 with available documentation only
    - "Let me check first" — pause and wait for user to investigate
```

**Common unreachable reference types** (look for these in the collector's failed-fetch list):
- State agency rate schedules (e.g., BCDHSC Form 2533 for rates, Form 2532 for cost share)
- Supervisory Release (SR) announcements (policy change documents)
- Policy manual sections (FAM topics)
- Provider enrollment/billing pages

**If user provides files**, process them before proceeding:
1. Copy to `/tmp/{PREFIX}-user-doc-{N}.pdf`
2. Extract text: `pdftotext /tmp/{PREFIX}-user-doc-{N}.pdf /tmp/{PREFIX}-user-doc-{N}.txt`
3. Render screenshots: `pdftoppm -png -r {DPI} /tmp/{PREFIX}-user-doc-{N}.pdf /tmp/{PREFIX}-user-doc-{N}-page`
4. Have a general-purpose agent append the new content to `sources/working_references.md`

**If no unreachable references**, skip this step and proceed to Phase 1.

---

## Phase 1: Consolidation & Requirements Extraction

Spawn a consolidator agent to read the full documentation and produce structured specs.

```
subagent_type: "general-purpose"
team_name: "{PREFIX}-encode"
name: "consolidator"

"Read sources/working_references.md and produce structured implementation specs for {STATE} {PROGRAM}.

STEP 1: Study reference implementations (search BROADLY).
States use different names for the same program type — do NOT search only by the target
program's acronym. Instead, derive 2-3 concept keywords from what the program does
(e.g., a child care subsidy program → search 'child', 'care', 'provider').

Search with MULTIPLE globs using concept keywords:
  Glob 'policyengine_us/variables/gov/states/*/*/*{keyword1}*/*.py'
  Glob 'policyengine_us/variables/gov/states/*/*/*{keyword2}*/*.py'

Identify ALL matching state implementations. Read 3-5 variable files and 3-5 parameter
files from the BEST reference implementation — pick the one with the most similar structure
to the target program (e.g., if target has multi-dimensional rates, pick a reference that
has enum-keyed rate lookups, not a simpler eligibility-only impl).
List ALL discovered implementations in the impl-spec so downstream agents can study them.

STEP 2: Discover existing reusable variables.
For each key concept in the program (income, hours, age, household size, childcare, etc.),
Grep the codebase for related variables:
  Grep 'class.*{concept}.*Variable' policyengine_us/variables/
For example, a childcare program should search for 'childcare', 'hours', 'provider', 'care'.
List all discovered variables in the impl-spec under '## Existing Variables to Reuse' so
downstream agents know what's already available and don't recreate them as bare inputs.

STEP 3: Verify citations against PDF text.
You already have the full documentation loaded. Before writing the impl-spec, cross-check
every section citation (statute number, manual section, definition number) against the
actual PDF text. Search the extracted text for the exact section/definition heading.
If a citation doesn't match (e.g., text says 'Definition 18' but you wrote 'Definition 19'),
correct it NOW — downstream agents will copy these citations verbatim into parameter files.

STEP 4: Write THREE files:

FILE 1: /tmp/{PREFIX}-impl-spec.md (FULL — for implementation agents)
- Every requirement from documentation, numbered (REQ-001, REQ-002, ...)
- Each requirement tagged: ELIGIBILITY, INCOME, BENEFIT, EXEMPTION, DEMOGRAPHIC, IMMIGRATION, RESOURCE, etc.
- Suggested variable and parameter structure (based on reference impl patterns)
- Existing variables to reuse (from Step 2 discovery — variable name, entity, description)
- Income sources list (for sources.yaml parameter, NOT inline adds)
- Reference implementation paths to study
- For TANF: note simplified vs full approach recommendation
- For each requirement: cite the source (statute, manual section, page) — verified against PDF text in Step 2

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
subagent_type: "complete:country-models:rules-engineer"
team_name: "{PREFIX}-encode"
name: "create-parameters"

"Create parameters for {STATE} {PROGRAM}.
Read the implementation spec at /tmp/{PREFIX}-impl-spec.md.
Read the scope decision at /tmp/{PREFIX}-scope-decision.md.
Study the reference implementation listed in the impl spec.
LESSONS_PATH: {LESSONS_PATH}

Load skills: /policyengine-parameter-patterns, /policyengine-variable-patterns,
  /policyengine-code-organization.

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
"
```

### Step 3B: Create Variables and Tests (Parallel)

**ORCHESTRATOR RULE: Always spawn BOTH agents below (variables + tests), even if a previous agent created files outside its scope.** Each agent is specialized for its task. If a previous agent went out of scope and created files that aren't its responsibility, the specialized agent will overwrite or improve them. Never skip an agent because "the files already exist."

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
LESSONS_PATH: {LESSONS_PATH}

Load skills: /policyengine-variable-patterns, /policyengine-parameter-patterns,
  /policyengine-vectorization, /policyengine-aggregation, /policyengine-period-patterns,
  /policyengine-code-style, /policyengine-code-organization.

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
"
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
LESSONS_PATH: {LESSONS_PATH}

Load skills: /policyengine-testing-patterns, /policyengine-period-patterns,
  /policyengine-aggregation, /policyengine-variable-patterns, /policyengine-code-organization.

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
"
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
LESSONS_PATH: {LESSONS_PATH}

Load skills: /policyengine-testing-patterns, /policyengine-variable-patterns.

OUTPUT LOCATION — IMPORTANT:
- Edge case scenarios MUST be APPENDED to the existing test files created in Step 3B,
  located at policyengine_us/tests/policy/baseline/gov/states/{ST}/...
- Find the existing unit test file for each variable and add edge case scenarios to it.
- Find the existing integration test file and add edge case scenarios to it.
- DO NOT create new files (no separate edge_cases.yaml, no test_edge_cases.yaml, etc.).
- If no existing test file covers the variable in question, flag it — do not silently
  create a new file.

Focus on:
- Income at threshold boundaries (threshold-1, threshold, threshold+1)
- Zero income, maximum income
- Family size at min/max
- Negative income with zero deductions
"
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
LESSONS_PATH: {LESSONS_PATH}

Load skills: /policyengine-variable-patterns, /policyengine-parameter-patterns,
  /policyengine-code-style, /policyengine-code-organization.

TASK: Implement ONLY the requirements listed under 'MISSING' in the coverage report.
Do not modify existing variables or parameters — only add what's missing.

REUSE EXISTING VARIABLES: Before creating any non-program-specific variable, Grep the
codebase first. PolicyEngine-US likely already has it.
"
```

After gap-fixer completes, re-run the requirements-tracker (same prompt as above) to verify all gaps are filled. If gaps remain after one fix round, report to user and proceed.

---

## Phase 4: Validation & Fix

### Step 4A: Implementation Validator (cross-file structural)

```
subagent_type: "complete:country-models:implementation-validator"
team_name: "{PREFIX}-encode"
name: "implementation-validator"

"Validate {STATE} {PROGRAM} for cross-file structural issues, fix mechanical issues yourself,
and escalate judgmental ones.

MODE: Mode A — structural validation. Run Phases 1–3 only. Do NOT run Phase 4
(code-pattern audit) — that's `/review-program` Validator 3's job, not this step's.

Scope (3 phases only):
- Phase 1: YAML structural integrity (orphaned values after metadata:, breakdown enum
  mismatches, duplicate keys, effective-date placement)
- Phase 2: Cross-reference linkage (orphan parameters, missing param references, empty
  directories, orphan files)
- Phase 3: Federal/State jurisdiction placement (federal-sourced values in /gov/{agency}/,
  state-sourced in /gov/states/{state}/, defined_for present on state variables)

LESSONS_PATH: {LESSONS_PATH}

Load skills: /policyengine-parameter-patterns, /policyengine-variable-patterns,
  /policyengine-code-organization.

Per-file rules (description format, reference format, period format, hard-coded values,
naming, adds/add(), wrappers) are NOT your scope in Mode A — they are self-checked by
rules-engineer and test-creator at write time, and re-checked by /review-program Mode B
later. Note such issues in 'Notes for review' but do NOT make them blocking.

Fix MECHANICAL issues yourself (orphan dirs, breakdown enum renames, YAML block moves,
git mv for placement, adding defined_for). Escalate JUDGMENTAL issues (orphan parameter
needing variable, missing param ref with no obvious typo) to rules-engineer.

Write your report to /tmp/{PREFIX}-validator-report.md with three sections:
1. FIXED — what you fixed and where
2. ESCALATED — issues for rules-engineer with proposed fix, OR 'NONE' if no escalations
3. Notes for review — per-file issues observed in passing (description format, naming,
   hard-coded values); these are NOT blocking — /review-program Mode B handles them.
"
```

### Step 4A-fix: Handle Validator Escalations

After implementation-validator completes, read `/tmp/{PREFIX}-validator-report.md`.

**If the ESCALATED section is 'NONE'**: proceed to Step 4B.

**If the ESCALATED section has items**: spawn rules-engineer to fix them:

```
subagent_type: "complete:country-models:rules-engineer"
team_name: "{PREFIX}-encode"
name: "validator-escalation-fixer"

"Fix the judgmental issues escalated by implementation-validator for {STATE} {PROGRAM}.
Read the validator report at /tmp/{PREFIX}-validator-report.md.
Focus ONLY on items under the ESCALATED section.
Read the implementation spec at /tmp/{PREFIX}-impl-spec.md for policy context.
Read the scope decision at /tmp/{PREFIX}-scope-decision.md.
LESSONS_PATH: {LESSONS_PATH}

Load skills: /policyengine-variable-patterns, /policyengine-parameter-patterns,
  /policyengine-code-organization.

After fixing, append a 'POST-FIX' section to /tmp/{PREFIX}-validator-report.md
listing what you changed.
"
```

After validator-escalation-fixer completes, proceed to Step 4B. (No re-run of the validator
unless you specifically suspect the fixer introduced new structural issues.)

### Step 4B: CI Fixer (owns the full test-passing loop)

```
subagent_type: "complete:country-models:ci-fixer"
team_name: "{PREFIX}-encode"
name: "ci-fixer"

"Run tests locally for {STATE} {PROGRAM} and make them pass. You OWN the full loop —
both mechanical fixes (test syntax, entity mismatch, period format) AND policy /
calculation fixes (wrong formula, wrong test expectation, missing parameter). There is
no downstream specialist dispatch step; do not classify-and-escalate.

LESSONS_PATH: {LESSONS_PATH}

Load skills: /policyengine-testing-patterns, /policyengine-variable-patterns,
  /policyengine-parameter-patterns, /policyengine-period-patterns, /policyengine-code-style,
  /policyengine-aggregation, /policyengine-vectorization, /policyengine-code-organization.

Read these for policy context:
- sources/working_references.md (primary policy source)
- /tmp/{PREFIX}-impl-spec.md (structured implementation spec)
- /tmp/{PREFIX}-scope-decision.md (user's scope choices — don't fix excluded items)

Run: policyengine-core test policyengine_us/tests/policy/baseline/gov/states/{ST}/... -c policyengine_us -v

Iterate up to the 8-iteration budget. If two consecutive iterations don't move a failure,
classify it BLOCKED. Apply make format when done.

Write status to /tmp/{PREFIX}-ci-fixer-status.md with STATUS: PASS or BLOCKED only
(no PARTIAL). For BLOCKED, list each remaining failure with root cause and why it's
blocked.
"
```

After ci-fixer completes, read `/tmp/{PREFIX}-ci-fixer-status.md`. **Proceed to Step 4C
regardless of STATUS** — BLOCKED failures continue downstream (they'll surface in CI,
and the PR description will note them). No user prompt, no halt.

If STATUS = BLOCKED, note the remaining-failure count for the PR description (Step 5B
reads the same status file and includes a "Known failing tests" section).

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

"Prepare {STATE} {PROGRAM} PR for review (but keep it as a draft):
- Create changelog fragment in changelog.d/ (towncrier format)
- Run make format
- Push branch

CRITICAL: The PR MUST remain a draft. Do NOT run `gh pr ready` or any flag that converts
the draft. The orchestrator (or user) marks ready later — never this agent."
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
- /tmp/{PREFIX}-ci-fixer-status.md (test status — if STATUS = BLOCKED, list the
  remaining failures in a 'Known failing tests' section near the bottom of the PR
  description so reviewers see what didn't pass and why)
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

## Known Failing Tests
{If /tmp/{PREFIX}-ci-fixer-status.md has STATUS: BLOCKED, list each remaining failure
with its root cause and why ci-fixer couldn't resolve it. Omit this section entirely
if STATUS: PASS.}

## Historical Notes
If the regulatory reviewer or document-collector noted historical changes to any parameter
values (e.g., threshold increases, rate changes), document what changed and when, with
source links. This helps reviewers understand why parameters only start at a recent date.

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

## Phase 6: Review-Fix (3 Mandatory Rounds)

**Skip if `--skip-review`.**

This phase runs 3 independent review rounds. Each review is done by a fresh `/review-program` invocation. After any fix, the next review is a **mandatory step** — the orchestrator has NO discretion to skip it. Only an actual review confirming critical == 0 can end the phase early.

---

### Round 1: Initial Review

#### Step 6.1A: Run /review-program

```
Skill: review-program
Arguments: $PR_NUMBER --local --full [--600dpi if DPI == 600]
```

#### Step 6.1B: Check Results

Read `/tmp/review-program-summary.md` (max 20 lines).

**If critical == 0**: Report to user. **Phase 6 complete — skip remaining rounds.**

**If critical > 0**: Proceed to Step 6.1C.

#### Common rules for all review-fix prompts (rounds 1–3)

Every review-fix spawn below references these rules. Include the section name in each prompt body; do not restate the rules per prompt.

**[REVIEW-FIX RULES]**
- Read `/tmp/{PREFIX}-scope-decision.md` first. For each review item, check whether the scope decision intentionally excluded it or chose a non-default value (e.g., "use 200% FPL because state has transitional rate"). If yes, do NOT fix — append `[SKIPPED-PER-SCOPE]` to your checklist line and move on.
- Read `/tmp/{PREFIX}-impl-spec.md` ONLY when the fix touches a parameter VALUE or a variable FORMULA. For formatting, references, hard-coded value swaps, naming, or structural fixes — skip it to save context.
- For round 2+: read `/tmp/{PREFIX}-checklist.md` first to see prior rounds' fixes; do not reintroduce earlier patterns. (Round 1 fixers do NOT read this file — it doesn't exist yet.)
- **REUSE EXISTING VARIABLES**: before creating any non-program-specific variable, Grep the codebase. PolicyEngine-US likely already has it (`fpg`, `smi`, `tanf_fpg`, `ssi`, etc.).
- Apply fixes via Edit/MultiEdit, then run `make format`.
- **WRITE your fix log to a PER-FIXER FILE** (not the shared checklist). The path is in your invocation prompt; it will be one of:
  - `/tmp/{PREFIX}-checklist-vars-r{N}.md` (rules-engineer)
  - `/tmp/{PREFIX}-checklist-tests-r{N}.md` (test-creator)
  Writing to your own file avoids race conditions with the parallel fixer. The orchestrator concatenates both files into the shared `/tmp/{PREFIX}-checklist.md` after you both complete.
- Format each line as:
  `- [ROUND N] [SCOPE] [{CATEGORY}] {file}:{line} — {what was wrong} → {what you changed}`
  - SCOPE = `VARS` (rules-engineer) or `TESTS` (test-creator)
  - Categories (vars/params): `HARD-CODED`, `WRONG-PERIOD`, `MISSING-REF`, `BAD-REF`, `DEDUCTION-ORDER`, `UNUSED-PARAM`, `WRONG-ENTITY`, `NAMING`, `FORMULA-LOGIC`, `OTHER`
  - Categories (tests): `TEST-GAP`, `WRONG-PERIOD`, `WRONG-EXPECTATION`, `NON-FUNCTIONAL-TEST`, `OTHER`
- If you have zero items in scope, write a single line `- [ROUND N] [SCOPE] NO-ISSUES — nothing to fix` to your per-fixer file and return DONE with 0 fixes.

#### Step 6.1C: Fix Critical Issues (parallel — split by ownership)

Spawn BOTH fixers in parallel. Each reads the same review report but only fixes items
in its own scope. If a fixer's scope has zero items, it returns DONE with 0 fixes.

**Fixer 1: rules-engineer (parameters and variables)**

```
subagent_type: "complete:country-models:rules-engineer"
team_name: "{PREFIX}-encode"
name: "review-fixer-1-vars"
run_in_background: true

"Fix CRITICAL parameter/variable issues from the /review-program review (round 1).
Read /tmp/review-program-full-report.md. Focus ONLY on items in parameter (.yaml)
or variable (.py) files. SKIP test-file items — test-creator handles those in parallel.
LESSONS_PATH: {LESSONS_PATH}

Load skills: /policyengine-variable-patterns, /policyengine-code-style,
  /policyengine-parameter-patterns, /policyengine-period-patterns, /policyengine-vectorization.

Follow [REVIEW-FIX RULES] (see section above this step). Tag checklist lines with
SCOPE=VARS, ROUND=1. Write your fix log to /tmp/{PREFIX}-checklist-vars-r1.md
(NOT the shared checklist — that file is merged by the orchestrator after both
parallel fixers finish)."
```

**Fixer 2: test-creator (test files)**

```
subagent_type: "complete:country-models:test-creator"
team_name: "{PREFIX}-encode"
name: "review-fixer-1-tests"
run_in_background: true

"Fix CRITICAL test-file issues from the /review-program review (round 1).
Read /tmp/review-program-full-report.md. Focus ONLY on items in test (.yaml under tests/)
files. SKIP items in parameter or variable files — rules-engineer handles those in parallel.

Common critical test issues: missing unit tests for formula variables; non-functional
tests (e.g., absolute_error_margin >= 1 on boolean outputs); wrong period format (not
YYYY-01 or YYYY); wrong test expectations.

LESSONS_PATH: {LESSONS_PATH}

Load skills: /policyengine-testing-patterns, /policyengine-period-patterns,
  /policyengine-variable-patterns.

Follow [REVIEW-FIX RULES] (see section above this step). Tag checklist lines with
SCOPE=TESTS, ROUND=1. Write your fix log to /tmp/{PREFIX}-checklist-tests-r1.md
(NOT the shared checklist — that file is merged by the orchestrator after both
parallel fixers finish)."
```

Wait for both fixers to complete, then **merge their per-fixer files into the shared checklist** (orchestrator step):

```bash
# Concatenate round-1 per-fixer files into the canonical checklist.
# Use >> so round 2's merge later appends to (not overwrites) round 1's contents.
cat /tmp/{PREFIX}-checklist-vars-r1.md /tmp/{PREFIX}-checklist-tests-r1.md \
  >> /tmp/{PREFIX}-checklist.md 2>/dev/null
```

Then proceed to 6.1D.

#### Step 6.1D: Run Tests & Commit

```
subagent_type: "complete:country-models:ci-fixer"
team_name: "{PREFIX}-encode"
name: "ci-fixer-1"

"Run tests locally for {STATE} {PROGRAM} after review-fix round 1.
Apply your 5-iteration budget. Fix mechanical test failures directly; classify and
escalate policy/calculation issues in your status report.
Run make format after tests pass (or budget exhausted).

Write status to /tmp/{PREFIX}-ci-fixer-status.md with STATUS: PASS / PARTIAL / BLOCKED.

NOTE: PARTIAL status is acceptable here — round 2 will re-run /review-program and pick
up any remaining issues. Do NOT loop beyond your 5-iteration budget."
```

```bash
git add policyengine_us/parameters/gov/states/{ST}/ policyengine_us/variables/gov/states/{ST}/ policyengine_us/tests/policy/baseline/gov/states/{ST}/
git commit -m "Review-fix round 1: address critical issues from /review-program"
git push
```

**Proceed to Round 2. This is mandatory — do NOT skip.**

---

### Round 2: Verification Review

#### Step 6.2A: Run /review-program

```
Skill: review-program
Arguments: $PR_NUMBER --local --full [--600dpi if DPI == 600]
```

#### Step 6.2B: Check Results

Read `/tmp/review-program-summary.md` (max 20 lines).

**If critical == 0**: Report to user. **Phase 6 complete — skip Round 3.**

**If critical > 0**: Ask user before proceeding:

```
AskUserQuestion:
  Question: "Round 2 review found {N} critical issues after round 1 fixes. Attempt a 3rd round?"
  Options:
    - "Yes, try one more round"
    - "No, stop and show remaining issues"
```

If user says no → report remaining issues, **Phase 6 complete.**

If user says yes → proceed to Step 6.2C.

#### Step 6.2C: Fix Critical Issues (parallel — same split as Round 1)

Round 2 uses the same parallel split as Round 1 — `rules-engineer` for parameter/variable
fixes, `test-creator` for test-file fixes. If either has zero items, it returns DONE.

**Fixer 1: rules-engineer (vars/params)**

```
subagent_type: "complete:country-models:rules-engineer"
team_name: "{PREFIX}-encode"
name: "review-fixer-2-vars"
run_in_background: true

"Fix CRITICAL parameter/variable issues from the /review-program review (round 2).
Read /tmp/review-program-full-report.md. SKIP test-file items.
LESSONS_PATH: {LESSONS_PATH}

Load skills: /policyengine-variable-patterns, /policyengine-code-style,
  /policyengine-parameter-patterns, /policyengine-period-patterns, /policyengine-vectorization.

Follow [REVIEW-FIX RULES] (see section above 6.1C). Tag checklist lines with SCOPE=VARS,
ROUND=2. Write your fix log to /tmp/{PREFIX}-checklist-vars-r2.md (NOT the shared
checklist — orchestrator merges after both fixers complete)."
```

**Fixer 2: test-creator (tests)**

```
subagent_type: "complete:country-models:test-creator"
team_name: "{PREFIX}-encode"
name: "review-fixer-2-tests"
run_in_background: true

"Fix CRITICAL test-file issues from the /review-program review (round 2).
Read /tmp/review-program-full-report.md. SKIP parameter/variable items.
LESSONS_PATH: {LESSONS_PATH}

Load skills: /policyengine-testing-patterns, /policyengine-period-patterns,
  /policyengine-variable-patterns.

Follow [REVIEW-FIX RULES] (see section above 6.1C). Tag checklist lines with SCOPE=TESTS,
ROUND=2. Write your fix log to /tmp/{PREFIX}-checklist-tests-r2.md (NOT the shared
checklist — orchestrator merges after both fixers complete)."
```

Wait for both fixers to complete, then **merge their per-fixer files into the shared checklist**:

```bash
cat /tmp/{PREFIX}-checklist-vars-r2.md /tmp/{PREFIX}-checklist-tests-r2.md \
  >> /tmp/{PREFIX}-checklist.md 2>/dev/null
```

Wait for both fixers to complete before 6.2D.

#### Step 6.2D: Run Tests & Commit

```
subagent_type: "complete:country-models:ci-fixer"
team_name: "{PREFIX}-encode"
name: "ci-fixer-2"

"Run tests for {STATE} {PROGRAM} after review-fix round 2.
Fix any test failures introduced by the fixes. Run make format."
```

```bash
git add policyengine_us/parameters/gov/states/{ST}/ policyengine_us/variables/gov/states/{ST}/ policyengine_us/tests/policy/baseline/gov/states/{ST}/
git commit -m "Review-fix round 2: address critical issues from /review-program"
git push
```

**Proceed to Round 3. This is mandatory — do NOT skip.**

---

### Round 3: Final Review

#### Step 6.3A: Run /review-program

```
Skill: review-program
Arguments: $PR_NUMBER --local --full [--600dpi if DPI == 600]
```

#### Step 6.3B: Check Results

Read `/tmp/review-program-summary.md` (max 20 lines).

**If critical == 0**: Report to user. **Phase 6 complete.**

**If critical > 0**: Report remaining issues to user. No more fix rounds — escalate for manual resolution. **Phase 6 complete.**

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
| `/tmp/{PREFIX}-checklist-{vars,tests}-r{N}.md` | per-fixer (write) | orchestrator (merge) | One per fixer per round |
| `/tmp/{PREFIX}-checklist.md` | orchestrator (cat-merge) | review-fixer round 2+ (read) | Growing |

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
