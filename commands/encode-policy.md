---
description: Orchestrates multi-agent workflow to implement new government benefit programs
---

# Implementing $ARGUMENTS in PolicyEngine

Coordinate the multi-agent workflow to implement $ARGUMENTS as a complete, production-ready government benefit program.

## Experimental Mode Detection

**If $ARGUMENTS contains "experiment"** (case-insensitive):
- This is an experimental implementation for workflow testing
- Use simplified Phase 1 (skip @issue-manager agent)
- Create branch from current branch instead of master
- Create draft PR with current branch as base

## Phase 1: Issue and PR Setup

### For Experimental Implementations (when $ARGUMENTS contains "experiment"):

**Simplified workflow:**
1. Extract program name from $ARGUMENTS (remove "experiment" keyword)
2. Create new branch from current branch:
   - Branch name: `[state-abbreviation]-tanf-experiment` (e.g., `ct-tanf-experiment`)
3. Create draft PR:
   - Base branch: Current branch (e.g., `claude-experiments`)
   - Title: `[State] TANF implementation experiment`
   - Body: Simple description noting this is experimental workflow testing
4. Skip GitHub issue creation
5. Proceed to Phase 2

### For Production Implementations:

Invoke @issue-manager agent to:
- Search for existing issue or create new one for $ARGUMENTS
- Create draft PR immediately for early visibility
- Return issue number and PR URL for tracking

## Phase 2: Variable Naming Convention
Invoke @naming-coordinator agent to:
- Analyze existing naming patterns in the codebase
- Establish variable naming convention for $ARGUMENTS
- **For production:** Post naming decisions to GitHub issue for all agents to reference
- **For experiments:** Post naming decisions to PR description or save to a local file

**Quality Gate**: Naming convention must be documented before proceeding to ensure consistency across parallel development.

## Phase 3: Document Collection

**Phase 3A: Initial Document Gathering**

Invoke @document-collector agent to gather official $ARGUMENTS documentation:
- **For production:** Post to GitHub issue
- **For experiments:** Save as `working_references.md` in the repository

**After agent completes:**
1. Check the agent's report for "📄 PDFs Requiring Extraction" section
2. **If PDFs are listed:**
   - Ask the user: "Please send me these PDF URLs so I can extract their content:"
   - List each PDF URL on a separate line
   - Wait for user to send the URLs (they will auto-extract)
   - Proceed to Phase 3B

3. **If no PDFs listed:**
   - Skip to Phase 4 (documentation complete)

**Phase 3B: PDF Extraction & Complete Documentation** (Only if PDFs were found)

1. After receiving extracted PDF content from user:
2. Relaunch @document-collector agent with:
   - Original task description
   - Extracted PDF content included in prompt
   - Instruction: "You are in Phase 2 - integrate this PDF content with your HTML research"
3. Agent creates complete documentation

**Quality Gate**: Documentation must include:
- Official program guidelines or state plan
- Income limits and benefit schedules
- Eligibility criteria and priority groups
- Seasonal/temporal rules if applicable
- ✅ All critical PDFs extracted and integrated

## Phase 4: Parallel Development (SIMULTANEOUS)
After documentation is ready, invoke BOTH agents IN PARALLEL:
- @test-creator: Create integration tests from documentation only
- @rules-engineer: Implement rules from documentation (will internally use @parameter-architect if needed)

**CRITICAL**: These must run simultaneously in separate conversations to maintain isolation. Neither can see the other's work.

**Quality Requirements**:
- rules-engineer: ZERO hard-coded values, complete implementations only
- test-creator: Use only existing PolicyEngine variables, test realistic calculations

## Phase 5: Branch Integration
Invoke @integration-agent to:
- Merge test and implementation branches
- Fix basic integration issues (entity mismatches, naming)
- Discard uv.lock changes (always)
- Prepare unified codebase for validation

**Note:** Test verification happens in Phase 6, not Phase 5. This phase just merges code and fixes basic conflicts.

**Why Critical**: The next phases need to work on integrated code to catch real issues.

## Phase 6: Pre-Push Validation
Invoke @pr-pusher agent to:
- Ensure changelog entry exists
- Run formatters (black, isort)
- Fix any linting issues
- Run local tests for quick validation
- Push branch and report initial CI status

**Quality Gate**: Branch must be properly formatted and have changelog before continuing.

## Phase 7: Unit Test Creation

**For simplified TANF implementations:** Create unit tests with edge cases

Invoke @test-creator to:
- Create unit test files for each variable with formula (follow DC TANF pattern)
- Test file name matches variable name (e.g., `ct_tanf_income_eligible.yaml`)
- Include edge cases in unit tests (boundary conditions at thresholds)
- Remove excessive edge cases from integration.yaml (keep integration tests realistic)
- Organize tests in folder structure matching variables
- Commit unit tests

**Quality Requirements**:
- One unit test file per variable with formula
- Edge cases in unit tests, not integration tests
- Integration tests only test realistic end-to-end scenarios

---

**OPTIONAL (for production implementations only):**

### Step 2: Cross-Program Validation (SKIP for simplified TANF)
- @cross-program-validator: Check interactions with other benefits

### Step 3: Documentation Enhancement (SKIP for simplified TANF)
- @documentation-enricher: Add examples and regulatory citations

### Step 4: Performance Optimization (SKIP for simplified TANF)
- @performance-optimizer: Vectorize and optimize calculations

**Note:** For experimental/simplified TANF implementations, only edge case testing is required. The other steps are optional enhancements for production implementations.

## Phase 8: Implementation Validation
Invoke @implementation-validator agent to check for:
- Hard-coded values in variables
- Placeholder or incomplete implementations
- Federal/state parameter organization
- Test quality and coverage
- Performance and vectorization issues

**Quality Gate**: Must pass ALL critical validations before proceeding

## Phase 9: Review
Invoke @rules-reviewer to validate the complete implementation against documentation.

**Review Criteria**:
- Accuracy to source documents
- Complete coverage of all rules
- Proper parameter usage
- Edge case handling
- **Folder structure optimization:** Review and optimize folder organization for clarity and consistency

## Phase 10: Local Testing & Fixes
**CRITICAL: ALWAYS invoke @ci-fixer agent - do NOT manually fix issues**

Invoke @ci-fixer agent to:
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
- Run `make format` before committing fixes
- Push final fixes to PR branch

**Success Metrics**:
- All tests pass locally (green output)
- Code properly formatted
- Implementation complete and working
- Clean commit history

**Note:** For experimental implementations, CI monitoring is optional. Focus on local test success.


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

4. **Phase 4**: Parallel Development
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

7. **Phase 7**: Required Fixes and Validations (SEQUENTIAL)
   - Complete the phase
   - Report results
   - **STOP - Wait for user to say "continue" or provide adjustments**

8. **Phase 8**: Implementation Validation
   - Complete the phase
   - Report results
   - **STOP - Wait for user to say "continue" or provide adjustments**

9. **Phase 9**: Review
   - Complete the phase
   - Report results
   - **STOP - Wait for user to say "continue" or provide adjustments**

10. **Phase 10**: Local Testing & CI Finalization
    - Complete the phase
    - Report final results
    - **WORKFLOW COMPLETE**

**CRITICAL RULES**:
- Do NOT proceed to the next phase until user explicitly says to continue
- After each phase, summarize what was accomplished
- If user provides adjustments, incorporate them before continuing
- All 10 phases are still REQUIRED - pausing doesn't mean skipping

If any agent fails, report the failure but DO NOT attempt to fix it yourself. Wait for user instructions.
