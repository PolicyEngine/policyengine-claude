---
description: Orchestrates multi-agent workflow to implement contributed policy reforms (proposed bills, policy experiments)
---

# Implementing Reform: $ARGUMENTS

Coordinate a multi-agent workflow to implement a contributed policy reform (proposed bill, policy experiment, or tax change) as a complete, production-ready reform in PolicyEngine US.

**GLOBAL RULE — PDF Page Numbers**: Every PDF reference href MUST end with `#page=XX` (the file page number, NOT the printed page number). The ONLY exception is single-page PDFs. This rule applies to ALL agents in ALL phases.

**GLOBAL RULE — Reform Skill**: Every implementation agent (param-architect, rules-engineer, test-creator, validator) MUST load `/policyengine-reform-patterns` in addition to their standard skills. This teaches the factory function pattern, `gov/contrib/` paths, `in_effect` toggle, `reforms:` test key, and registration in `reforms.py`.

## Arguments

`$ARGUMENTS` should contain:
- **State and bill** (required) — e.g., `MT HB 268`, `CT SB-100`, `SC H.4216`
- **Or federal reform** — e.g., `CRFB AGI Surtax`, `Streamlined EITC`
- **Options**:
  - `--skip-review` — skip Phase 4 review-fix loop
  - `--research-only` — stop after Phase 1, produce impl-spec but don't implement

**Examples:**
```
/encode-reform MT HB 268
/encode-reform CT SB-100
/encode-reform SC H.4216 --skip-review
/encode-reform CRFB AGI Surtax
/encode-reform KY HB 13 HB 152
```

---

## Constants

```
ST          = state code from $ARGUMENTS (e.g., "mt", "ct", "ky") or org name for federal (e.g., "crfb")
BILL_ID     = bill identifier (e.g., "hb268", "sb100", "h4216", "agi_surtax")
PREFIX      = /tmp/{ST}-{BILL_ID}
LESSONS_PATH = ~/.claude/projects/-Users-ziminghua-vscode-policyengine-us/memory/agent-lessons.md
```

---

## Context Window Protection

**YOU (the orchestrator) ONLY read SHORT summary files (marked "Short" in the table below).** All detailed data flows through disk files between agents. Never read full spec files — delegate that to agents.

### Disk File Handoff Table

| File | Writer | Reader | Size |
|------|--------|--------|------|
| `{PREFIX}-type-summary.md` | bill-analyzer | Orchestrator | Short ≤15 |
| `{PREFIX}-bill-analysis.md` | bill-analyzer | consolidator | Full |
| `{PREFIX}-bill.pdf` | bill-analyzer | prep-bill-pdf | Binary |
| `sources/working_references.md` | bill-researcher | consolidator | Full |
| `{PREFIX}-impl-spec.md` | consolidator | param-architect, rules-engineer, test-creator | Full |
| `{PREFIX}-impl-summary.md` | consolidator | Orchestrator | Short ≤20 |
| `{PREFIX}-checkpoint.md` | validator | Orchestrator | Short ≤15 |
| `{PREFIX}-test-results.md` | ci-fixer | Orchestrator | Short ≤10 |
| `{PREFIX}-audit-checkpoint.md` | quick-auditor | Orchestrator | Short ≤15 |
| `{PREFIX}-checklist.md` | review-fixer | next round fixer | Full |
| `{PREFIX}-final-report.md` | reporter | Orchestrator | Short ≤25 |
| `{PREFIX}-pr-description.md` | reporter | gh pr edit | Full |

---

## Phase 0: Parse, Detect Reform Type, Check Baseline Dependencies

### Step 0A: Analyze the bill

Spawn a **general-purpose** agent ("bill-analyzer"):

```
You are analyzing a proposed bill/reform for PolicyEngine implementation.

TASK:
1. Parse $ARGUMENTS to extract: state, bill number(s), reform topic
2. Determine reform type (A-F from the reform patterns skill):
   - A: New refundable credit
   - B: Rate/bracket override
   - C: Comprehensive tax reform (multiple overrides)
   - D: Enhanced existing credit
   - E: Repeal/neutralize
   - F: Federal-level reform
3. Identify whether this is state-level (gov/contrib/states/{st}/{bill}/) or federal (gov/contrib/{topic}/)
4. If $ARGUMENTS contains multiple bills (e.g., "KY HB 13 HB 152"), note they share a reform Python file

Check baseline dependencies:
5. For each variable the reform will likely READ or OVERRIDE, grep the codebase:
   - `grep -r "class {variable_name}" policyengine_us/variables/`
   - If ANY required baseline variable is missing, list it
6. Check if a reform for this bill already exists:
   - `ls policyengine_us/parameters/gov/contrib/states/{st}/{bill_id}/` (or contrib/{topic}/)
   - `ls policyengine_us/reforms/states/{st}/{bill_id}/` (or reforms/{topic}/)

Write TWO files:
- {PREFIX}-type-summary.md (≤15 lines): reform type (A-F), state/federal, bill numbers, parameter path, reform path, missing baseline deps (if any), existing files (if any)
- {PREFIX}-bill-analysis.md (full): detailed analysis with all findings

If there's a bill URL in $ARGUMENTS, also download the PDF:
- curl -sL {url} -o {PREFIX}-bill.pdf
- Verify with `file {PREFIX}-bill.pdf` that it's actually a PDF

LEARN FROM PAST SESSIONS (read if exists, skip if not):
- {LESSONS_PATH}
```

### Step 0B: Issue and PR setup (concurrent with 0A)

Invoke @complete:country-models:issue-manager agent to:
- Search for existing issue or create new one for `$ARGUMENTS`
- Create branch: `{st}-{bill_id}` (e.g., `mt-hb268`, `crfb-agi-surtax`)
- Push to fork, then create draft PR to upstream using `--repo PolicyEngine/policyengine-us`
- Return issue number, PR URL, and branch name

### After Phase 0

Read `{PREFIX}-type-summary.md` (SHORT file).

**STOP CONDITIONS:**
- If missing baseline dependencies are listed → Report to user and STOP. Do NOT attempt to implement missing baseline variables.
- If reform already exists → Report to user and ask whether to update or abort.

Record: `REFORM_TYPE`, `PARAM_PATH`, `REFORM_PATH`, `BILL_NUMBERS`.

---

## Phase 1: Research Bill Text and Extract Provisions

### Step 1A: Research bill sources

Invoke @complete:country-models:document-collector agent ("bill-researcher"):

```
Research the bill/reform: $ARGUMENTS

Find and download:
1. Official bill text (legislature website)
2. Bill analysis/fiscal notes (if available)
3. Any committee reports or amendments
4. Related existing law being modified

Save all findings to sources/working_references.md with:
- Bill title and number
- Sponsor(s)
- Status (introduced, passed committee, enacted, etc.)
- Effective date (if specified)
- Full text URLs
- PDF downloads with pdftotext extraction

For each PDF: curl -sL {url} -o /tmp/doc.pdf && file /tmp/doc.pdf && pdftotext /tmp/doc.pdf /tmp/doc.txt

GLOBAL RULE: Every PDF reference must include #page=XX in href.
```

### Step 1B: Prep bill PDF for research (if PDF exists)

If `{PREFIX}-bill.pdf` exists from Phase 0, spawn a **general-purpose** agent ("prep-bill-pdf"):

```
Render the bill PDF at 300 DPI for research agents to read as screenshots.

1. Count pages: pdfinfo {PREFIX}-bill.pdf | grep Pages
2. Render ALL pages: pdftoppm -r 300 -png {PREFIX}-bill.pdf {PREFIX}-bill-page
3. Verify: ls {PREFIX}-bill-page-*.png | wc -l
4. Write a manifest: {PREFIX}-bill-pages.txt listing all PNG paths, one per line
```

### Step 1C: Consolidate into implementation spec

After 1A (and 1B if applicable) complete, spawn a **general-purpose** agent ("consolidator"):

```
Load skills: /policyengine-reform-patterns

You are creating the implementation specification for a policy reform.

READ these files:
- {PREFIX}-bill-analysis.md (from bill-analyzer)
- sources/working_references.md (from bill-researcher)
- {PREFIX}-bill-page-*.png (if they exist — read the rendered bill pages)

Create {PREFIX}-impl-spec.md with these sections:

## Parameter Plan
List every parameter to create under {PARAM_PATH}/:
- in_effect.yaml (always first)
- Each parameter: filename, description, values, metadata, reference
- For brackets: show the bracket structure
- For filing-status breakdowns: show the breakdown structure

## Variable Plan
List every variable to define in the reform Python file:
- Variable name, entity, value_type, label, unit, definition_period
- Formula logic (pseudocode)
- Whether it's NEW, OVERRIDE, or NEUTRALIZE
- If NEW credit: note that modify_parameters() is needed

## Registration Plan
- Import path for reforms.py
- Factory function names
- Module-level bypass instance name

## Test Plan
- List test cases with expected inputs/outputs
- Cover: eligibility, ineligibility, phase-out, filing statuses, edge cases
- Include reforms: key path and in_effect: true

Also create {PREFIX}-impl-summary.md (≤20 lines) with:
- Reform type (A-F)
- Number of parameters to create
- Number of variables (new/override/neutralize)
- Whether modify_parameters needed
- Key filing status variations
- Effective date

LEARN FROM PAST SESSIONS: {LESSONS_PATH}
```

### After Phase 1

Read `{PREFIX}-impl-summary.md` (SHORT file).

**If `--research-only` flag**: Report findings and STOP.

---

## Phase 2: Create Parameters, Reform Code, Tests, Validate

**This phase is SEQUENTIAL** — parameters must exist before reform code, reform code before tests.

### Step 2A: Create Parameters

Invoke @complete:country-models:parameter-architect:

```
Load skills: /policyengine-reform-patterns, /policyengine-parameter-patterns

READ: {PREFIX}-impl-spec.md (Parameter Plan section)

Create all parameters under policyengine_us/parameters/{PARAM_PATH}/:
- Start with in_effect.yaml (default: false, date: 0000-01-01)
- Then all policy parameters per the spec

Reform-specific rules:
- Path: gov/contrib/states/{st}/{bill_id}/ (or gov/contrib/{topic}/ for federal)
- in_effect.yaml is REQUIRED as the first file
- All references must cite the bill text with #page=XX
- Use 0000-01-01 for in_effect, actual effective dates for policy params

GLOBAL RULE: Every PDF reference href MUST end with #page=XX.
LEARN FROM PAST SESSIONS: {LESSONS_PATH}
```

### Step 2B: Create Reform Code

Invoke @complete:country-models:rules-engineer:

```
Load skills: /policyengine-reform-patterns, /policyengine-variable-patterns, /policyengine-code-style

READ: {PREFIX}-impl-spec.md (Variable Plan and Registration Plan sections)

Create the reform Python file at policyengine_us/reforms/{REFORM_PATH}/:

1. Create {reform_name}.py following the TWO-FUNCTION FACTORY PATTERN:
   - Inner function create_xx(): defines variables + Reform class
   - Outer function create_xx_reform(parameters, period, bypass): 5-year lookahead
   - Module-level bypass=True instance

2. Create __init__.py with proper exports

3. Register in policyengine_us/reforms/reforms.py:
   - Add import at top
   - Add instantiation in create_structural_reforms_from_parameters()
   - Add to reforms list
   - Add to combined_reform.apply() with None guard

4. If reform type A (new credit): include modify_parameters() to add to credit list

CRITICAL RULES:
- ALL numeric values from parameters (ZERO hard-coded values)
- Variables defined INSIDE the factory function closure
- Use defined_for = StateCode.XX for state reforms
- Use where() for dual calculation patterns
- Follow existing reform code style (study 2-3 existing reforms first)

LEARN FROM PAST SESSIONS: {LESSONS_PATH}
```

### Step 2C: Create Tests

Invoke @complete:country-models:test-creator:

```
Load skills: /policyengine-reform-patterns, /policyengine-testing-patterns

READ: {PREFIX}-impl-spec.md (Test Plan section)

Create test file at policyengine_us/tests/policy/contrib/{test_path}/{reform_name}.yaml

EVERY test case MUST include:
- reforms: {full.dotted.path.to.module_level_instance}
- gov.contrib.{param_path}.in_effect: true
- state_code: {ST} (for state reforms)
- absolute_error_margin: 1

Coverage requirements:
1. Basic eligibility (income under threshold, eligible members)
2. Ineligibility (income over threshold, wrong state, no qualifying members)
3. Filing status variations (SINGLE, JOINT, HEAD_OF_HOUSEHOLD at minimum)
4. Phase-out boundaries (at start, mid-range, fully phased out)
5. Edge cases (zero income, exactly at threshold, maximum benefit)
6. If applicable: nonrefundable cap, multiple qualifying members

LEARN FROM PAST SESSIONS: {LESSONS_PATH}
```

### Step 2D: Validate

Invoke @complete:country-models:implementation-validator:

```
Load skills: /policyengine-reform-patterns, /policyengine-code-style, /policyengine-code-organization

Validate the reform implementation. Check this reform-specific checklist:

1. [ ] in_effect.yaml exists with default false and date 0000-01-01
2. [ ] All parameters under correct gov/contrib/ path
3. [ ] Factory function pattern: inner create_xx() + outer create_xx_reform()
4. [ ] 5-year lookahead in outer function
5. [ ] Module-level bypass=True instance exported
6. [ ] Registered in reforms.py (import, instantiate, list, combined apply)
7. [ ] If new credit: modify_parameters() present
8. [ ] Tests have reforms: key and in_effect: true
9. [ ] No hard-coded values in variable formulas
10. [ ] defined_for = StateCode.XX present (for state reforms)

Also check standard code quality:
- Parameter metadata complete (unit, period, label, reference)
- Variable patterns correct (adds vs add(), entity levels)
- Code style (black formatting, import ordering)
- Reference format (title with full section, href with #page=XX)

Write {PREFIX}-checkpoint.md (≤15 lines):
- PASS/FAIL for each of the 10 reform checks
- List of any issues found
- List of files created/modified

LEARN FROM PAST SESSIONS: {LESSONS_PATH}
```

### After Phase 2

Read `{PREFIX}-checkpoint.md` (SHORT file).

If issues found, delegate fixes to the appropriate agent (param-architect for parameter issues, rules-engineer for code issues, test-creator for test issues).

---

## Phase 3: Run Tests, Fix, Quick Audit, Push

### Step 3A: Run tests and fix

Invoke @complete:country-models:ci-fixer:

```
Run the reform tests locally:

policyengine-core test policyengine_us/tests/policy/contrib/{test_path}/ -c policyengine_us -v

If tests fail:
1. Read the error output carefully
2. Fix the ROOT CAUSE (do NOT hardcode values to pass tests)
3. Re-run tests
4. Iterate until all pass (max 5 attempts)

If a fix requires parameter changes: fix parameters directly
If a fix requires formula changes: fix the reform .py file directly
If a fix requires test changes: fix only if the test expectation was wrong

Write {PREFIX}-test-results.md (≤10 lines):
- Number of tests: X passed, Y failed
- If failures: brief description of each
- PASS or FAIL overall
```

### Step 3B: Quick audit (concurrent with push prep)

Spawn a **general-purpose** agent ("quick-auditor"):

```
Load skills: /policyengine-reform-patterns

Quick audit of the reform implementation. Read:
- All files under policyengine_us/parameters/{PARAM_PATH}/
- The reform Python file under policyengine_us/reforms/{REFORM_PATH}/
- The test file under policyengine_us/tests/policy/contrib/
- The registration in policyengine_us/reforms/reforms.py

Check for common reform pitfalls:
1. Circular dependencies (variable A reads variable B which reads A)
2. Forgotten modify_parameters (new credit not in credit list)
3. Double-counting (federal deductions applied twice)
4. Missing None filter in reforms list
5. Phase-out rounding (check if bill specifies rounding rules)
6. Hard-coded values in formulas
7. Missing filing status handling
8. Incorrect parameter access (check bracket path syntax)

Write {PREFIX}-audit-checkpoint.md (≤15 lines):
- Number of issues found by severity (critical/warning/info)
- Brief description of each issue
- CLEAN or ISSUES_FOUND overall

LEARN FROM PAST SESSIONS: {LESSONS_PATH}
```

### Step 3C: Format and push

After tests pass and audit completes, invoke @complete:country-models:pr-pusher:

```
Ensure the reform PR is ready:
1. Create changelog fragment: echo "Added {reform description}." > changelog.d/{branch-name}.added.md
2. Run make format
3. Stage all new/modified files
4. Commit with descriptive message
5. Push to remote

Do NOT push if tests failed. Check {PREFIX}-test-results.md first.
```

### After Phase 3

Read `{PREFIX}-test-results.md` and `{PREFIX}-audit-checkpoint.md` (both SHORT).

If audit found critical issues, fix before proceeding.

---

## Phase 4: Review-Fix Loop (Max 3 Rounds)

**Skip if `--skip-review` flag is set.**

**CRITICAL: Every round spawns completely fresh agents.** Do NOT resume agents from previous rounds. Each review and each fix must start with a new agent that reads the current state from disk files. This ensures no stale context carries over between rounds.

### For each round (1 to 3):

#### Step 4A: Run review (NEW agent)

Spawn a **new** invocation of skill `/review-program` — do NOT resume any previous review agent.

The review will analyze the reform against its regulatory sources by reading the current code on disk.

#### Step 4B: Count critical issues

Read the review output. Count issues marked as CRITICAL.

- If **0 critical issues** → Exit loop, proceed to Phase 5
- If **>0 critical issues** and round < 3 → Continue to Step 4C
- If **>0 critical issues** and round = 3 → Log remaining issues, proceed to Phase 5 anyway (include unresolved issues in final report)

#### Step 4C: Fix issues (NEW agent)

Invoke a **new** @complete:country-models:rules-engineer agent — do NOT resume the previous round's fixer:

```
Load skills: /policyengine-reform-patterns

Fix the critical issues found in the review. Read:
- {PREFIX}-checklist.md (the review findings from this round)
- The reform files that need fixing (read current state from disk)

Fix each critical issue. Do NOT fix warnings unless they're trivial.

After fixing, write updated {PREFIX}-checklist.md with status of each issue.

IMPORTANT: You are a fresh agent. Do not assume any prior context — read all files you need from disk.
```

#### Step 4D: Re-test and push (NEW agents)

Invoke a **new** @complete:country-models:ci-fixer to run tests again.
Then invoke a **new** @complete:country-models:pr-pusher to push (review reads from remote via `gh pr diff`).

**Do NOT resume ci-fixer or pr-pusher from previous rounds.**

---

## Phase 5: Finalize — Changelog, PR Description, Report, Shutdown

### Step 5A: Generate PR description and final report

Spawn a **general-purpose** agent ("reporter"):

```
Create the final PR description and report for this reform.

Read:
- {PREFIX}-type-summary.md
- {PREFIX}-impl-summary.md
- {PREFIX}-checkpoint.md
- {PREFIX}-test-results.md
- {PREFIX}-audit-checkpoint.md
- sources/working_references.md
- The actual reform files created (parameters, Python, tests)

Write {PREFIX}-pr-description.md (full) with this structure:

## Summary
Implements [State] [Bill Number] [short description] as a contributed reform.
Closes #{issue_number}.

## Reform Type
[A-F]: [description]

## Parameters Created
- `gov/contrib/{path}/in_effect.yaml` — Boolean toggle (default: false)
- `gov/contrib/{path}/...` — [description of each parameter]

## Variables Defined
- `{variable_name}` — [NEW/OVERRIDE/NEUTRALIZE] — [description]

## Registration
- Registered in `reforms/reforms.py` with factory function pattern
- [If applicable: modify_parameters() adds to credit list]

## Test Coverage
- [N] test cases covering: [list categories]
- All filing statuses tested: [list]

## Regulatory Sources
- [Bill text URL]
- [Additional sources]

## Files Changed
- [list all new/modified files]

---

Also write {PREFIX}-final-report.md (≤25 lines):
- Reform: [state] [bill] — [type A-F]
- Parameters: [count] created under [path]
- Variables: [count] ([new/override/neutralize breakdown])
- Tests: [count] passing
- Review: [clean / N issues fixed]
- PR: [URL]
- Status: COMPLETE
```

### Step 5B: Update PR description

```bash
gh pr edit {PR_NUMBER} --body "$(cat {PREFIX}-pr-description.md)"
```

### After Phase 5

Read `{PREFIX}-final-report.md` (SHORT file). Report to user.

**Keep PR as draft** — user will mark ready when they choose.

**WORKFLOW COMPLETE.**

---

## Error Handling

| Category | Example | Action |
|----------|---------|--------|
| **Missing baseline deps** | Reform reads variable that doesn't exist | STOP in Phase 0, report to user |
| **Reform already exists** | Files found in contrib/ path | Ask user: update or abort |
| **Bill text unavailable** | Legislature website down | Continue with whatever sources found |
| **Test failures** | Reform logic incorrect | ci-fixer attempts fix (max 5 rounds) |
| **Audit critical issues** | Circular dependency found | Fix before push |
| **Review critical issues** | Regulatory mismatch | Fix in review-fix loop (max 3 rounds) |
| **Agent failure** | Agent errors out | Report and STOP |

### Escalation Path

1. Agent encounters error → Attempt fix if recoverable
2. Fix fails → Report to user and STOP
3. Never proceed to next phase with unresolved critical issues

---

## Execution Instructions

**YOUR ROLE**: You are an orchestrator ONLY. You must:
1. Invoke agents using the Agent tool
2. Wait for their completion
3. Read ONLY short summary files (≤25 lines)
4. Check quality gates
5. Proceed to the next phase automatically

**YOU MUST NOT**:
- Write any code yourself
- Fix any issues manually
- Run tests directly
- Edit reform files
- Read full spec files (delegate to agents)

**Execution Flow (CONTINUOUS)**:

Execute all phases sequentially without stopping (unless a STOP condition is hit).

0. **Phase 0**: Parse args, analyze bill, check baseline deps, create PR
   - If missing deps → STOP
   - If reform exists → Ask user

1. **Phase 1**: Research bill, prep PDF, consolidate into impl-spec
   - If `--research-only` → Report and STOP

2. **Phase 2**: Create parameters → reform code → tests → validate (SEQUENTIAL)
   - Fix any validation issues before proceeding

3. **Phase 3**: Run tests, quick audit, format and push
   - Fix any test failures or critical audit issues

4. **Phase 4**: Review-fix loop (max 3 rounds)
   - Skip if `--skip-review`
   - User approval required before round 3

5. **Phase 5**: PR description, final report, shutdown
   - Report completion to user

**CRITICAL RULES**:
- Run all phases continuously without waiting for user input (unless STOP condition)
- All implementation agents load `/policyengine-reform-patterns` skill
- Phase 2 is SEQUENTIAL (not parallel) — params → code → tests → validate
- Push ONLY after tests pass
- Keep PR as draft
