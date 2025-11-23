# Agents Updated for Code Style Skill

## Summary

Updated 3 agents to reference the new `policyengine-code-style-skill`, ensuring they apply formula optimization patterns when writing or reviewing code.

## Agents Updated

### 1. rules-engineer.md
**Role:** Implements government benefit program rules

**Updates:**
- Added code-style skill to Skills Used section
- Added guidance in Step 3 to:
  - Eliminate single-use intermediate variables
  - Use direct parameter access and returns
  - Combine boolean logic when possible

**Impact:** Will write cleaner, more efficient formulas from the start

### 2. rules-reviewer.md
**Role:** Reviews and validates PolicyEngine implementations

**Updates:**
- Added code-style skill to Skills Used section
- Added code style checks to Step 3 (Code Quality Check):
  - Check for unnecessary intermediate variables
  - Verify direct parameter access patterns
  - Ensure combined boolean logic where appropriate

**Impact:** Will catch code style issues during review, ensuring cleaner code gets merged

### 3. ci-fixer.md
**Role:** Fixes test failures and implementation issues

**Updates:**
- Added Skills Used section (previously had none)
- Included 5 relevant skills:
  - testing-patterns (for understanding tests)
  - implementation-patterns (for fixing variables)
  - vectorization (for avoiding crashes)
  - code-style (for clean fixes)
  - period-patterns (for period issues)

**Impact:** When fixing code, will apply optimization patterns to make formulas cleaner

## Why These Agents

These three agents are the primary code writers and reviewers:

1. **rules-engineer** - Creates the initial implementation
2. **ci-fixer** - Fixes issues and refactors code
3. **rules-reviewer** - Validates code quality

Other agents like **test-creator** and **parameter-architect** don't write formulas, so they don't need the code-style skill.

## Expected Benefits

With these updates, PolicyEngine code will be:
- **More consistent** - All agents follow same style guide
- **More efficient** - Fewer unnecessary variables
- **More readable** - Direct, streamlined logic
- **Better reviewed** - Style issues caught in review

## Integration Complete

The code-style skill is now fully integrated into the agent workflow:
1. **rules-engineer** writes clean code initially
2. **ci-fixer** maintains style when fixing
3. **rules-reviewer** enforces style standards

This creates a complete quality loop ensuring all PolicyEngine formulas follow the optimization patterns.