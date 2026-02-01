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

## Phase 2: Document Collection & Specification

Invoke @complete:country-models:document-collector agent to:
- Research and gather official $ARGUMENTS documentation
- **Discover the state's official program name** during research
- Save all documentation to `sources/working_references.md`

**Agent behavior for PDFs:**
- Agent cannot read PDFs directly
- Agent MUST add all PDF links to `sources/working_references.md` under a "📄 PDFs for Future Reference" section
- Agent continues with HTML sources and proceeds with available information
- Do NOT stop the workflow for PDFs

**Example in sources/working_references.md:**
```markdown
## Official Program Name

**Federal Program**: [Federal program name]
**State's Official Name**: [State's official name]
**Abbreviation**: [Abbreviation]
**Source**: [Legal citation]

**Variable Prefix**: `[state]_[abbreviation]`

---

## 📄 PDFs for Future Reference

The following PDFs contain additional information but could not be extracted:

1. **State Plan**
   - URL: https://state.gov/program-state-plan.pdf
   - Expected content: Benefit calculation methodology, page 10
```

**Quality Gate**: Documentation must include:
- **Official program name discovered through research**
- Official program guidelines from HTML sources
- Income limits and benefit schedules
- Eligibility criteria and priority groups
- PDF links saved for future reference (if found)

### Regulatory Checkpoint 1: Specification Review

Before proceeding to development, verify the specification is complete:

| Check | Question |
|-------|----------|
| Program structure | Are all eligibility types documented (income, categorical, demographic, immigration)? |
| Benefit calculation | Is the formula documented with all components? |
| Deductions | Are all deductions and disregards listed? |
| Sources | Does every rule have an authoritative source? |
| Completeness | Are there any "TBD" or missing sections? |

**If issues found**: Fix specification before proceeding to Phase 3.

## Phase 3: Development

**IMPORTANT:** All agents create files only - they do NOT commit. pr-pusher in Phase 6 handles all commits.

**Naming Convention:** All agents load **policyengine-code-organization-skill** and use the variable prefix from `sources/working_references.md`.

### Step 3A: Create Parameters

**@complete:country-models:parameter-architect** → works in `parameters/` folder:
- Create complete parameter structure from documentation
- All thresholds, amounts, rates, income limits
- Include proper references with PDF page numbers
- Use bracket-style for age-based eligibility
- Verify person vs group level for all amounts

#### Regulatory Checkpoint 2: Parameter Value Verification

Before proceeding to variables, verify parameters are accurate:

| Check | Question |
|-------|----------|
| Values | Does each parameter value match its source document? |
| References | Does each reference have detailed section (e.g., `42 USC 8624(b)(2)(B)`)? |
| PDF pages | Do PDF references include `#page=XX`? |
| Jurisdiction | Are federal values in federal folder, state in state folder? |
| Completeness | Are all values from specification covered? |

**If issues found**: Fix parameters before proceeding to Step 3B.

### Step 3B: Create Variables and Tests (Parallel)

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

### Step 3C: Generate Edge Case Tests

**@complete:country-models:edge-case-generator** → works in `tests/` folder:
- Analyze variables created by rules-engineer
- Generate edge case tests (boundary conditions, zero values, maximums)
- Add to existing test files

#### Regulatory Checkpoint 3: Implementation Logic Review

After variables are created, verify implementation matches regulations:

| Check | Question |
|-------|----------|
| Logic | Does the eligibility logic match the specification? |
| Calculations | Does benefit calculation match the documented formula? |
| Edge cases | Are special rules (exemptions, exceptions) implemented? |
| Dependencies | Are federal baselines used correctly (for simplified TANF)? |
| Completeness | Are all program components from specification implemented? |

**If issues found**: Fix variables before proceeding to Phase 4.

**Quality Requirements**:
- parameter-architect: Complete parameters with references before variables
- rules-engineer: ZERO hard-coded values, use parameters from Step 3A
- test-creator: All tests (unit + integration) created together, based purely on documentation
- edge-case-generator: Edge cases based on actual variable implementations

## Phase 4: Organization Check & Fix

Invoke @complete:country-models:implementation-validator to check and fix organization issues:

**1. Naming Conventions:**
- Variable names follow prefix from `working_references.md`
- Parameter names follow conventions
- Test file names match variable names

**2. Folder Structure:**
- Files grouped logically by aspect (income, eligibility, etc.)
- No subfolder for single files
- Final output at program root

**3. Parameter Formatting:**
- Description present and follows template
- References have `title` and `href`
- PDF links include `#page=XX` (file page number)
- Title includes full subsection
- Bracket-style for age-based eligibility

**4. Variable Code Style (comprehensive check):**

Check ALL variable code against **policyengine-code-style-skill** and **policyengine-variable-patterns-skill**:
- Aggregation patterns (`adds` vs `add()`)
- Entity levels (Person vs SPMUnit)
- Reference format (tuple not list)
- Vectorization requirements
- No wrapper variables
- No hard-coded values
- Proper period handling
- Every line of variable code

**Fix any issues found before proceeding.**

## Phase 5: Run Tests & Fix

Invoke @complete:country-models:ci-fixer to:

1. **Run tests LOCALLY** (do NOT wait for GitHub CI):
   ```bash
   policyengine-core test policyengine_us/tests/policy/baseline/gov/states/[STATE]/[AGENCY]/[PROGRAM] -c policyengine_us -v
   ```
2. **Fix test failures** based on documentation
   - Do NOT create wrapper variables just because test inputs don't match
   - Fix test inputs to match what federal baseline expects
3. **Iterate** until all tests pass locally

## Phase 6: Format and Push

Invoke @complete:country-models:pr-pusher agent to:
- Ensure changelog entry exists
- Run `make format`
- Push branch

## Phase 7: Final Review & PR Description

Since regulatory accuracy has been verified throughout (Checkpoints 1-3), this phase focuses on final verification and documentation.

### Step 7A: Reference Validation

Invoke @complete:country-models:reference-validator to:
- Find parameters missing references
- Check reference format (page numbers, detailed sections)
- Verify references corroborate parameter values
- Check jurisdiction match (federal vs state sources)

**Fix any reference issues before proceeding to Step 7B.**

### Step 7B: Regulatory Review

Invoke @complete:country-models:program-reviewer:

1. **Final regulatory spot-check** - Quick verification that implementation matches regulations
2. **Update PR description** with comprehensive documentation:
   - Summary with issue link
   - Regulatory authority section
   - Income eligibility tests (with sources)
   - Income deductions & exemptions (with sources)
   - Income standards table
   - Benefit calculation formula (with sources)
   - Files added
   - Test coverage

**Note**: Major regulatory issues should have been caught in Checkpoints 1-3. If significant discrepancies are found here, it indicates earlier checkpoints were not thorough enough.

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

- **Phase 1-2 (Setup):** If agent fails, report error and STOP. Do not attempt to fix.
- **Phase 3 (Development):** If agent fails, report which agent failed and wait for user.
- **Phase 4 (Organization):** Fix issues found; if unfixable, report and continue.
- **Phase 5 (Tests):** ci-fixer handles test fixes. If ci-fixer fails 3 times, report and STOP.
- **Phase 6-8:** Continue unless blocking error.

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
4. Proceed to the next phase automatically

**YOU MUST NOT**:
- Write any code yourself
- Fix any issues manually
- Run tests directly
- Edit files

**Execution Flow (CONTINUOUS)**:

Execute all phases sequentially without stopping:

0. **Phase 0**: Implementation Approach (TANF Programs Only)
   - Auto-detect from $ARGUMENTS ("simple"/"simplified" vs. "full"/"complete")
   - Default to Simplified if unclear
   - Inform user of detected approach

1. **Phase 1**: Issue and PR Setup
   - Complete the phase
   - Report results briefly

2. **Phase 2**: Document Collection
   - Research and gather official documentation
   - Discover official program name during research
   - Save to `sources/working_references.md`

3. **Phase 3**: Development
   - **Step 3A:** Run parameter-architect to create parameters
   - **Step 3B:** Run test-creator and rules-engineer in parallel (different folders)
   - **Step 3C:** Run edge-case-generator to add edge case tests
   - All agents use variable prefix from `sources/working_references.md`
   - Pass simplified/full decision to rules-engineer

4. **Phase 4**: Organization Check & Fix
   - Check naming conventions, folder structure, formatting, code style
   - Fix any issues found

5. **Phase 5**: Run Tests & Fix
   - Run tests locally, fix failures, iterate until pass

6. **Phase 6**: Format and Push
   - Ensure changelog, run `make format`, push branch

7. **Phase 7**: Reference Validation & Regulatory Review
   - **Step 7A:** Run reference-validator (check all parameters have proper references)
   - **Step 7B:** Run program-reviewer (research regulations first, compare to code)
   - Update PR description with comprehensive documentation

8. **Phase 8**: Final Summary
   - Verify PR description complete
   - Report completion (keep PR as draft)
   - **WORKFLOW COMPLETE**

**CRITICAL RULES**:
- Run all phases continuously without waiting for user input
- If an agent fails, attempt recovery through ci-fixer; only stop if unrecoverable
- All 8 phases are REQUIRED
- Report final summary at the end
