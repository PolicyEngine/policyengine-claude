---
description: Orchestrates multi-agent workflow to implement new government benefit programs
---

# Implementing $ARGUMENTS in PolicyEngine

Coordinate the multi-agent workflow to implement $ARGUMENTS as a complete, production-ready government benefit program.

## Program Type Detection

This workflow adapts based on the type of program being implemented:

**TANF/Benefit Programs** (e.g., state TANF, SNAP, WIC):
- Phase 4: test-creator creates both unit and integration tests
- Phase 7: Uses specialized @complete:tanf-program-reviewer agent in parallel validation
- Optional phases: May be skipped for simplified implementations

**Other Government Programs** (e.g., tax credits, deductions):
- Phase 4: test-creator creates both unit and integration tests
- Phase 7: Uses general @complete:rules-reviewer agent in parallel validation
- Optional phases: Include based on production requirements

## Phase 1: Issue and PR Setup

Invoke @complete:issue-manager agent to:
- Search for existing issue or create new one for $ARGUMENTS
- Create draft PR immediately in PolicyEngine/policyengine-us repository (NOT personal fork)
- Return issue number and PR URL for tracking

## Phase 2: Variable Naming Convention
Invoke @complete:naming-coordinator agent to:
- Analyze existing naming patterns in the codebase
- Establish variable naming convention for $ARGUMENTS
- Analyze existing folder structure patterns in the codebase
- Post naming decisions and folder structure to GitHub issue for all agents to reference

**Quality Gate**: Naming convention and folder structure must be documented before proceeding to ensure consistency across parallel development.

## Phase 3: Document Collection

**Phase 3A: Initial Document Gathering**

Invoke @complete:document-collector agent to gather official $ARGUMENTS documentation, save as `working_references.md` in the repository, and post to GitHub issue

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
2. Relaunch @complete:document-collector agent with:
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

## Phase 4: Parallel Development (SIMULTANEOUS)
After documentation is ready, invoke BOTH agents IN PARALLEL:

**@complete:test-creator (single invocation):**
- Create comprehensive INTEGRATION tests from documentation
- Create UNIT tests for each variable that will have a formula
- Both test types created in ONE invocation
- Use only existing PolicyEngine variables
- Test realistic calculations based on documentation

**@complete:rules-engineer (two-step process):**
- **Step 1:** Create all parameters first using embedded parameter-architect patterns
  - Complete parameter structure with all thresholds, amounts, rates
  - Include proper references from documentation
- **Step 2:** Implement variables using the parameters
  - Zero hard-coded values
  - Complete implementations only
  - Document two-step process in commit messages

**CRITICAL**: These must run simultaneously in separate conversations to maintain isolation. Neither can see the other's work.

**Quality Requirements**:
- rules-engineer: ZERO hard-coded values, parameters created before variables
- test-creator: All tests (unit + integration) created together, based purely on documentation

## Phase 5: Branch Integration
Invoke @complete:integration-agent to:
- Merge test and implementation branches
- Fix basic integration issues (entity mismatches, naming)
- Discard uv.lock changes (always)
- Prepare unified codebase for validation

**Note:** Test verification happens in Phase 6, not Phase 5. This phase just merges code and fixes basic conflicts.

**Why Critical**: The next phases need to work on integrated code to catch real issues.

## Phase 6: Pre-Push Validation
Invoke @complete:pr-pusher agent to:
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
   - @complete:cross-program-validator: Check interactions with other benefits
   - Prevents benefit cliffs and unintended interactions

2. **Documentation Enhancement**
   - @complete:documentation-enricher: Add examples and regulatory citations
   - Improves maintainability and compliance verification

3. **Performance Optimization**
   - @complete:performance-optimizer: Vectorize and optimize calculations
   - Ensures scalability for large-scale simulations

**Decision Criteria:**
- **Simplified/Experimental TANF**: Skip these optional phases
- **Production TANF**: Include based on specific requirements
- **Full Production Deployment**: Include all enhancements

## Phase 7: Parallel Validation (SIMULTANEOUS)

**Run ALL validators IN PARALLEL for maximum efficiency:**

### Invoke simultaneously:

**@complete:implementation-validator:**
- Check for hard-coded values in variables
- Verify placeholder or incomplete implementations
- Check federal/state parameter organization
- Assess test quality and coverage
- Identify performance and vectorization issues

**Choose ONE based on program type:**

**For TANF/Benefit Programs → @complete:tanf-program-reviewer:**
- Learn from PA TANF and OH OWF reference implementations first
- Validate code formulas against regulations
- Verify test coverage with manual calculations
- Check parameter structure and references
- Focus on: eligibility rules, income disregards, benefit formulas

**For Other Programs → @complete:rules-reviewer:**
- Validate implementation against documentation
- Check for compliance with PolicyEngine standards
- Verify parameterization and test coverage

**Output:** Each validator provides independent report
**Time Savings:** ~50% reduction (parallel vs sequential validation)
**Quality Gate:** Review all validator reports before proceeding

## Phase 8: Local Testing & Fixes
**CRITICAL: ALWAYS invoke @complete:ci-fixer agent - do NOT manually fix issues**

Invoke @complete:ci-fixer agent to:
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
- **NEW: Reference Verification**
  - Verify all parameters have reference metadata
  - Verify all variables have reference fields
  - If all references embedded: Delete `working_references.md` with commit message "Clean up working references - all citations now in metadata"
  - If references missing: Create todos for adding them
- Run `make format` before committing fixes
- Push final fixes to PR branch

**Success Metrics**:
- All tests pass locally (green output)
- All references embedded in code metadata
- `working_references.md` deleted after embedding
- Code properly formatted
- Implementation complete and working
- Clean commit history

## Phase 9: Final Review & PR Ready

After all tests pass and references are embedded:
- Mark PR as ready for review (remove draft status)
- Update PR description with final implementation status
- Add summary of what was implemented
- Tag appropriate reviewers if needed
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

4. **Phase 4**: Parallel Development (Test + Implementation)
   - Complete the phase
   - Report results
   - **STOP - Wait for user to say "continue" or provide adjustments**

5. **Phase 5**: Branch Integration
   - Complete the phase
   - Report results
   - **STOP - Wait for user to say "continue" or provide adjustments**

6. **Phase 6**: Pre-Push Validation
   - Complete the phase
   - Report results
   - **STOP - Wait for user to say "continue" or provide adjustments**

7. **Phase 7**: Parallel Validation (All Validators Simultaneously)
   - Complete the phase
   - Report results from all validators
   - **STOP - Wait for user to say "continue" or provide adjustments**

8. **Phase 8**: Local Testing & Fixes (Including Reference Verification)
   - Complete the phase
   - Report results
   - **STOP - Wait for user to say "continue" or provide adjustments**

9. **Phase 9**: Final Review & PR Ready
   - Complete the phase
   - Report final results
   - **WORKFLOW COMPLETE**

**CRITICAL RULES**:
- Do NOT proceed to the next phase until user explicitly says to continue
- After each phase, summarize what was accomplished
- If user provides adjustments, incorporate them before continuing
- All 9 phases are REQUIRED - pausing doesn't mean skipping

If any agent fails, report the failure but DO NOT attempt to fix it yourself. Wait for user instructions.
