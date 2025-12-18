---
description: Orchestrates multi-agent workflow to implement new government benefit programs
---

# Implementing $ARGUMENTS in PolicyEngine

Coordinate the multi-agent workflow to implement $ARGUMENTS as a complete, production-ready government benefit program.

## Program Type Detection

This workflow adapts based on the type of program being implemented:

**TANF/Benefit Programs** (e.g., state TANF, SNAP, WIC):
- Phase 4: test-creator creates both unit and integration tests
- Phase 7: Uses specialized @complete:country-models:program-reviewer agent in parallel validation
- Optional phases: May be skipped for simplified implementations

**Other Government Programs** (e.g., tax credits, deductions):
- Phase 4: test-creator creates both unit and integration tests
- Phase 7: Uses general @complete:country-models:implementation-validator agent in parallel validation
- Optional phases: Include based on production requirements

## Phase 0: Implementation Approach (TANF Programs Only)

**For TANF programs, detect implementation approach from $ARGUMENTS:**

**Auto-detect from user's request:**
- If $ARGUMENTS contains "simple" or "simplified" → Use **Simplified** approach
- If $ARGUMENTS contains "full" or "complete" → Use **Full** approach
- If unclear → Default to **Simplified** approach

**Simplified Implementation:**
- Use federal baseline for gross income, demographic eligibility, immigration eligibility
- Faster implementation
- Suitable for most states that follow federal definitions
- Only creates state-specific variables for: income limits, disregards, benefit amounts, final calculation

**Full Implementation:**
- Create state-specific income definitions, eligibility criteria
- More detailed implementation
- Required when state has unique income definitions or eligibility rules
- Creates all state-specific variables

**Record the detected approach and pass it to Phase 4 (rules-engineer).**

## Phase 1: Issue and PR Setup

Invoke @complete:country-models:issue-manager agent to:
- Search for existing issue or create new one for $ARGUMENTS
- Create branch with simple name: `<state-code>-<program>` (e.g., `or-tanf`, `ky-tanf`)
- Push to fork, then create draft PR to upstream using `--repo PolicyEngine/policyengine-us`
- Return issue number, PR URL, and branch name for tracking

## Phase 2: Variable Naming Convention
Invoke @complete:country-models:naming-coordinator agent to:
- Analyze existing naming patterns in the codebase
- Establish variable naming convention for $ARGUMENTS
- Analyze existing folder structure patterns in the codebase
- Post naming decisions and folder structure to GitHub issue for all agents to reference

**Quality Gate**: Naming convention and folder structure must be documented before proceeding to ensure consistency across parallel development.

## Phase 3: Document Collection

Invoke @complete:country-models:document-collector agent to gather official $ARGUMENTS documentation and save as `sources/working_references.md`.

**Agent behavior for PDFs:**
- Agent cannot read PDFs directly
- Agent MUST add all PDF links to `sources/working_references.md` under a "📄 PDFs for Future Reference" section
- Agent continues with HTML sources and proceeds with available information
- Do NOT stop the workflow for PDFs

**Example in sources/working_references.md:**
```markdown
## 📄 PDFs for Future Reference

The following PDFs contain additional information but could not be extracted:

1. **State Plan**
   - URL: https://state.gov/tanf-state-plan.pdf
   - Expected content: Benefit calculation methodology, page 10

2. **Policy Manual**
   - URL: https://state.gov/tanf-manual.pdf
   - Expected content: Income deduction details
```

**Quality Gate**: Documentation must include:
- Official program guidelines from HTML sources
- Income limits and benefit schedules
- Eligibility criteria and priority groups
- PDF links saved for future reference (if found)
- Continue to Phase 4 after documentation is complete

## Phase 4: Development

**IMPORTANT:** All agents create files only - they do NOT commit. pr-pusher in Phase 5 handles all commits.

### Step 4A: Create Parameters

**@complete:country-models:parameter-architect** → works in `parameters/` folder:
- Create complete parameter structure from documentation
- All thresholds, amounts, rates, income limits
- Include proper references with PDF page numbers
- Use bracket-style for age-based eligibility
- Verify person vs group level for all amounts

### Step 4B: Create Variables and Tests (Parallel)

Run both agents IN PARALLEL - they work on different folders so no conflicts.

**@complete:country-models:test-creator** → works in `tests/` folder:
- Create comprehensive INTEGRATION tests from documentation
- Create UNIT tests for each variable that will have a formula
- Both test types created in ONE invocation
- Use only existing PolicyEngine variables
- Test realistic calculations based on documentation

**@complete:country-models:rules-engineer** → works in `variables/` folder:
- **Implementation Approach:** [Pass the decision from Phase 0: "simplified" or "full"]
  - **If Simplified TANF:** Do NOT create state-specific gross income variables - use federal baseline (`tanf_gross_earned_income`, `tanf_gross_unearned_income`)
  - **If Full TANF:** Create complete state-specific income definitions as needed
- Use the parameters created in Step 4A
- Zero hard-coded values - reference parameters only
- Use `adds` for pure sums, `add()` for sum + operations
- Verify person vs group entity level

**Quality Requirements**:
- parameter-architect: Complete parameters with references before variables
- rules-engineer: ZERO hard-coded values, use parameters from Step 4A
- test-creator: All tests (unit + integration) created together, based purely on documentation

## Phase 5: Format and Push
Invoke @complete:country-models:pr-pusher agent to:
- Ensure changelog entry exists
- Run `make format`
- Push branch

Testing is handled in Phase 7 by ci-fixer.

## Optional Enhancement Phases

**These phases are OPTIONAL and should be considered based on implementation type:**

### For Production-Ready Implementations:
The following enhancements may be applied to ensure production quality:

1. **Cross-Program Validation**
   - @complete:country-models:cross-program-validator: Check interactions with other benefits
   - Prevents benefit cliffs and unintended interactions

2. **Documentation Enhancement**
   - @complete:country-models:documentation-enricher: Add examples and regulatory citations
   - Improves maintainability and compliance verification

3. **Performance Optimization**
   - @complete:country-models:performance-optimizer: Vectorize and optimize calculations
   - Ensures scalability for large-scale simulations

**Decision Criteria:**
- **Simplified/Experimental TANF**: Skip these optional phases
- **Production TANF**: Include based on specific requirements
- **Full Production Deployment**: Include all enhancements

## Phase 6: Validate & Fix

**Run sequentially: validator finds issues → ci-fixer implements fixes**

### Step 6A: Implementation Validator

Invoke @complete:country-models:implementation-validator to check (in order):

**1. Parameters:**
- Description present and follows template
- References have `title` and `href`
- PDF links include `#page=XX` (file page number)
- Title includes full subsection
- Bracket-style for age-based eligibility

**2. Variables:**
- Uses `adds` for pure sums (no formula)
- Uses `add()` for sum + operations (not manual `a + b`)
- Uses `add() > 0` instead of `spm_unit.any()`
- Reference uses tuple `()` not list `[]`
- No `documentation` field (use `reference`)
- Correct entity level (Person vs SPMUnit)

**3. Tests:**
- Every variable with `formula` has a test file
- Variables with `adds` don't need tests

**Validator outputs structured fixes for ci-fixer to implement.**

### Step 6B: CI Fixer

Invoke @complete:country-models:ci-fixer to:

1. **Implement pattern fixes** from validator output
2. **Run tests LOCALLY** (do NOT wait for GitHub CI):
   ```bash
   policyengine-core test policyengine_us/tests/policy/baseline/gov/states/[STATE]/[AGENCY]/[PROGRAM] -c policyengine_us -v
   ```
3. **Fix test failures** based on documentation
   - Do NOT create wrapper variables just because test inputs don't match
   - Fix test inputs to match what federal baseline expects
4. **Iterate** until all tests pass locally
5. **Run `make format`**
6. **Push** once everything passes

## Phase 7: Regulatory Review

Invoke @complete:country-models:program-reviewer:

1. **Research regulations FIRST** (before looking at code)
2. **Compare implementation to regulations**
3. **Report any discrepancies** between code and legal requirements
4. **Update PR description** with comprehensive documentation:
   - Summary with issue link
   - Regulatory authority section
   - Income eligibility tests (with sources)
   - Income deductions & exemptions (with sources)
   - Income standards table
   - Benefit calculation formula (with sources)
   - Files added
   - Test coverage

## Phase 8: Final Summary

After regulatory review passes:
- Verify PR description is complete with all references
- Report completion to user
- **Keep PR as draft** - user will mark ready when they choose
- **WORKFLOW COMPLETE**

## Anti-Patterns This Workflow Prevents

1. **Hard-coded values**: Rules-engineer enforces parameterization
2. **Incomplete implementations**: Validator catches before PR
3. **Federal/state mixing**: Proper parameter organization enforced
4. **Non-existent variables in tests**: Test creator uses only real variables
5. **Missing edge cases**: Edge-case-generator covers all boundaries
6. **Benefit cliffs**: Cross-program-validator identifies interactions
7. **Poor documentation**: Documentation-enricher adds examples
8. **Performance issues**: Performance-optimizer ensures vectorization
9. **Review delays**: Most issues caught and fixed automatically

## Error Handling

### Error Categories

| Category | Example | Action |
|----------|---------|--------|
| **Recoverable** | Test failure, lint error | ci-fixer handles automatically |
| **Delegation** | Policy logic wrong | ci-fixer delegates to specialist agent |
| **Blocking** | GitHub API down, branch conflict | Stop and report to user |

### Error Handling by Phase

- **Phase 1-3 (Setup):** If agent fails, report error and STOP. Do not attempt to fix.
- **Phase 4 (Development):** If agent fails, report which agent failed and wait for user.
- **Phase 5-6 (Validation):** Validation failures are expected - continue to Phase 7.
- **Phase 7 (Fixes):** ci-fixer handles all fixes. If ci-fixer fails 3 times, report and STOP.

### Escalation Path

1. Agent encounters error → Log and attempt fix if recoverable
2. Fix fails → ci-fixer delegates to specialist agent (rules-engineer, test-creator, etc.)
3. Delegation fails → Report to user and STOP
4. Never proceed to next phase with unresolved blocking errors

## Execution Instructions

**YOUR ROLE**: You are an orchestrator ONLY. You must:
1. Invoke agents using the Task tool
2. Wait for their completion
3. Check quality gates
4. **PAUSE and wait for user confirmation before proceeding to next phase**

**YOU MUST NOT**:
- Write any code yourself
- Fix any issues manually
- Run tests directly
- Edit files

**Execution Flow (ONE PHASE AT A TIME)**:

Execute each phase sequentially and **STOP after each phase** to wait for user instructions:

0. **Phase 0**: Implementation Approach (TANF Programs Only)
   - Auto-detect from $ARGUMENTS ("simple"/"simplified" vs. "full"/"complete")
   - Default to Simplified if unclear
   - Inform user of detected approach
   - **STOP - Wait for user to say "continue" or provide adjustments**

1. **Phase 1**: Issue and PR Setup
   - Complete the phase
   - Report results
   - **STOP - Wait for user to say "continue" or provide adjustments**

2. **Phase 2**: Variable Naming Convention
   - Complete the phase
   - Report results
   - **STOP - Wait for user to say "continue" or provide adjustments**

3. **Phase 3**: Document Collection
   - Complete the phase
   - Report results
   - **STOP - Wait for user to say "continue" or provide adjustments**

4. **Phase 4**: Development
   - **Step 4A:** Run parameter-architect to create parameters
   - **Step 4B:** Run test-creator and rules-engineer in parallel (different folders)
   - Pass simplified/full decision to rules-engineer
   - Report results
   - **STOP - Wait for user to say "continue" or provide adjustments**

5. **Phase 5**: Format and Push
   - Ensure changelog, run `make format`, push branch
   - Report results
   - **STOP - Wait for user to say "continue" or provide adjustments**

6. **Phase 6**: Validate & Fix
   - **Step 6A:** Run implementation-validator (parameters → variables → tests)
   - **Step 6B:** Run ci-fixer (implement fixes, run tests locally, iterate until pass)
   - Report results
   - **STOP - Wait for user to say "continue" or provide adjustments**

7. **Phase 7**: Regulatory Review
   - Run program-reviewer (research regulations first, compare to code)
   - Update PR description with comprehensive documentation
   - Report results
   - **STOP - Wait for user to say "continue" or provide adjustments**

8. **Phase 8**: Final Summary
   - Verify PR description complete
   - Report completion (keep PR as draft)
   - **WORKFLOW COMPLETE**

**CRITICAL RULES**:
- Do NOT proceed to the next phase until user explicitly says to continue
- After each phase, summarize what was accomplished
- If user provides adjustments, incorporate them before continuing
- All 8 phases are REQUIRED - pausing doesn't mean skipping

If any agent fails, report the failure but DO NOT attempt to fix it yourself. Wait for user instructions.
