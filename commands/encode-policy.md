---
description: Orchestrates multi-agent workflow to implement new government benefit programs
---

# Implementing $ARGUMENTS in PolicyEngine

Coordinate the multi-agent workflow to implement $ARGUMENTS as a complete, production-ready government benefit program.

## Program Type Detection

This workflow adapts based on the type of program being implemented:

**TANF/Benefit Programs** (e.g., state TANF, SNAP, WIC):
- Phase 4: test-creator creates both unit and integration tests
- Phase 7: Uses specialized @complete:country-models:tanf-program-reviewer agent in parallel validation
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

**Phase 3A: Initial Document Gathering**

Invoke @complete:country-models:document-collector agent to gather official $ARGUMENTS documentation, save as `sources/working_references.md`, and post to GitHub issue

**After agent completes:**
1. Check the agent's report for "📄 PDFs Requiring Extraction" section
2. **Decision Point:**
   - **If PDFs are CRITICAL** (State Plans with benefit formulas, calculation methodology):
     - Ask the user: "Please send me these PDF URLs so I can extract their content:"
     - List each PDF URL on a separate line
     - Wait for user to send the URLs (they will auto-extract)
     - Proceed to Phase 3B
   - **If PDFs are SUPPLEMENTARY** (additional reference, not essential):
     - Note them for future reference
     - Proceed directly to Phase 4 with current documentation

3. **If no PDFs listed:**
   - Skip to Phase 4 (documentation complete)

**Phase 3B: PDF Extraction & Complete Documentation** (Only if CRITICAL PDFs found)

1. After receiving extracted PDF content from user:
2. Relaunch @complete:country-models:document-collector agent with:
   - Original task description
   - Extracted PDF content included in prompt
   - Instruction: "You are in Phase 2 - integrate this PDF content with your HTML research"
3. Agent creates complete documentation

**Quality Gate**: Documentation must include:
- Official program guidelines or state plan
- Income limits and benefit schedules
- Eligibility criteria and priority groups
- Seasonal/temporal rules if applicable
- ✅ All critical PDFs extracted and integrated (if applicable)

## Phase 4: Development (Parallel on Same Branch)

Run both agents IN PARALLEL on branch `<state-code>-<program>` (e.g., `or-tanf`) - they work on different folders so no conflicts.

**IMPORTANT:** Both agents create files only - they do NOT commit. pr-pusher in Phase 5 handles all commits.

**@complete:country-models:test-creator** → works in `tests/` folder:
- Create comprehensive INTEGRATION tests from documentation
- Create UNIT tests for each variable that will have a formula
- Both test types created in ONE invocation
- Use only existing PolicyEngine variables
- Test realistic calculations based on documentation

**@complete:country-models:rules-engineer** → works in `variables/` + `parameters/` folders:
- **Implementation Approach:** [Pass the decision from Phase 0: "simplified" or "full"]
  - **If Simplified TANF:** Do NOT create state-specific gross income variables - use federal baseline (`tanf_gross_earned_income`, `tanf_gross_unearned_income`)
  - **If Full TANF:** Create complete state-specific income definitions as needed
- **Step 1:** Create all parameters first using embedded parameter-architect patterns
  - Complete parameter structure with all thresholds, amounts, rates
  - Include proper references from documentation
- **Step 2:** Implement variables using the parameters
  - Zero hard-coded values
  - Complete implementations only
  - Follow simplified/full approach from Phase 0

**Quality Requirements**:
- rules-engineer: ZERO hard-coded values, parameters created before variables
- test-creator: All tests (unit + integration) created together, based purely on documentation

## Phase 5: Pre-Push Validation
Invoke @complete:country-models:pr-pusher agent to:
- Ensure changelog entry exists
- Run formatters (black, isort)
- Fix any linting issues
- Run local tests for quick validation
- Push branch and report initial CI status

**Quality Gate**: Branch must be properly formatted with changelog before continuing.

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

## Phase 6: Validation

**Run validators to check implementation quality:**

**@complete:country-models:implementation-validator:**
- Check for hard-coded values in variables
- Verify placeholder or incomplete implementations
- Check federal/state parameter organization
- Assess test quality and coverage
- Identify performance and vectorization issues

**For TANF/Benefit Programs, also run @complete:country-models:tanf-program-reviewer:**
- Learn from PA TANF and OH OWF reference implementations first
- Validate code formulas against regulations
- Verify test coverage with manual calculations
- Check parameter structure and references
- Focus on: eligibility rules, income disregards, benefit formulas

**Quality Gate:** Review validator reports before proceeding

## Phase 7: Local Testing & Fixes
**CRITICAL: ALWAYS invoke @complete:country-models:ci-fixer agent - do NOT manually fix issues**

Invoke @complete:country-models:ci-fixer agent to:
- Run all tests locally: `policyengine-core test policyengine_us/tests/policy/baseline/gov/states/[STATE]/[PROGRAM] -c policyengine_us -v`
- Identify ALL failing tests
- For each failing test:
  - Read the test file to understand expected values
  - Read the actual test output to see what was calculated
  - Determine root cause: incorrect test expectations OR bug in implementation
  - Fix the issue:
    - If test expectations are wrong: update the test file with correct values
    - If implementation is wrong: fix the variable/parameter code
  - Re-run tests to verify fix
- Iterate until ALL tests pass locally
- **Reference Verification**
  - Verify all parameters have reference metadata
  - Verify all variables have reference fields
  - Keep `sources/` folder files for future reference
  - If references missing: Create todos for adding them
- Run `make format` before committing fixes
- Push final fixes to PR branch

**Success Metrics**:
- All tests pass locally (green output)
- All references embedded in code metadata
- `sources/` folder kept for future reference
- Code properly formatted
- Implementation complete and working
- Clean commit history

## Phase 8: Final Summary

After all tests pass and references are embedded:
- Update PR description with final implementation status
- Add summary of what was implemented
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

4. **Phase 4**: Development (Test + Implementation)
   - Pass simplified/full decision to rules-engineer
   - Run test-creator and rules-engineer in parallel (different folders)
   - Report results
   - **STOP - Wait for user to say "continue" or provide adjustments**

5. **Phase 5**: Pre-Push Validation
   - Complete the phase
   - Report results
   - **STOP - Wait for user to say "continue" or provide adjustments**

6. **Phase 6**: Validation
   - Run validators
   - Report results
   - **STOP - Wait for user to say "continue" or provide adjustments**

7. **Phase 7**: Local Testing & Fixes (Including Reference Verification)
   - Complete the phase
   - Report results
   - **STOP - Wait for user to say "continue" or provide adjustments**

8. **Phase 8**: Final Summary
   - Update PR description
   - Report final results (keep PR as draft)
   - **WORKFLOW COMPLETE**

**CRITICAL RULES**:
- Do NOT proceed to the next phase until user explicitly says to continue
- After each phase, summarize what was accomplished
- If user provides adjustments, incorporate them before continuing
- All 8 phases are REQUIRED - pausing doesn't mean skipping

If any agent fails, report the failure but DO NOT attempt to fix it yourself. Wait for user instructions.
