---
description: Apply fixes to a PR based on review-pr findings or review comments
---

# Fixing PR: $ARGUMENTS

Apply fixes to PR issues identified by `/review-pr` or GitHub review comments.

## Determining Which PR to Fix

```bash
# If no arguments provided, use current branch's PR
if [ -z "$ARGUMENTS" ]; then
    CURRENT_BRANCH=$(git branch --show-current)
    PR_NUMBER=$(gh pr list --head "$CURRENT_BRANCH" --json number --jq '.[0].number')
    if [ -z "$PR_NUMBER" ]; then
        echo "No PR found for current branch $CURRENT_BRANCH"
        exit 1
    fi
# If argument is a number, use it directly
elif [[ "$ARGUMENTS" =~ ^[0-9]+$ ]]; then
    PR_NUMBER=$ARGUMENTS
# Otherwise, search for PR by description/title
else
    PR_NUMBER=$(gh pr list --search "$ARGUMENTS" --json number,title --jq '.[0].number')
    if [ -z "$PR_NUMBER" ]; then
        echo "No PR found matching: $ARGUMENTS"
        exit 1
    fi
fi

echo "Fixing PR #$PR_NUMBER"
gh pr checkout $PR_NUMBER
```

---

## Coordinator Role

**You are a coordinator, NOT an implementer.**

- ✅ Invoke agents with specific instructions
- ✅ Wait for agents to complete
- ✅ Verify fixes worked
- ❌ Never use Edit/Write directly
- ❌ Never write code yourself

---

## Phase 1: Gather Context

Collect information about issues to fix:

```bash
gh pr view $PR_NUMBER --comments
gh pr checks $PR_NUMBER
gh pr diff $PR_NUMBER
```

**Parse findings into categories:**

| Priority | Examples |
|----------|----------|
| 🔴 Critical | Hard-coded values, missing references, regulatory mismatch, CI failures |
| 🟡 Should | Pattern violations, missing tests, naming issues |
| 🟢 Suggestions | Documentation, performance |

**Create fix plan** listing each issue and which agent will fix it.

---

## Phase 2: Fix Critical Issues

**Fix in dependency order**: Parameters → Variables → Tests

### Step 2A: Fix Reference Issues

If references are missing or incorrect:

**Invoke parameter-architect**:
```
Fix reference issues in these parameter files:
- [file1]: Missing reference
- [file2]: Reference doesn't corroborate value (says X, should be Y)
- [file3]: Missing PDF page number

Requirements:
- Add detailed section numbers (e.g., 42 USC 8624(b)(2)(B))
- Add #page=XX for PDF links
- Ensure clicking link shows the value
```

### Step 2B: Fix Hard-Coded Values

If hard-coded values found in variables:

**Step 1 - Invoke parameter-architect**:
```
Create parameters for these hard-coded values:
- [file1:line]: value 65 (age threshold)
- [file2:line]: value 0.3 (rate)
- [file3:line]: value 2000 (income limit)

Create in proper hierarchy (federal vs state).
Include references for each value.
```

**Step 2 - Invoke rules-engineer**:
```
Refactor these variables to use the new parameters:
- [file1]: Replace hard-coded 65 with parameter
- [file2]: Replace hard-coded 0.3 with parameter
- [file3]: Replace hard-coded 2000 with parameter

Use proper parameter access pattern.
```

### Step 2C: Fix Regulatory Mismatches

If implementation doesn't match regulations:

**Invoke rules-engineer**:
```
Fix regulatory mismatch in [file]:
- Current: [what code does]
- Should be: [what regulation says]
- Source: [regulation citation]

Update the formula to match the regulation.
```

### Step 2D: Fix CI Failures

If CI is failing:

**Invoke ci-fixer**:
```
Fix CI failures for PR #$PR_NUMBER:
- Test failures: [list failing tests]
- Lint failures: [list lint issues]

Run tests locally, fix issues, iterate until passing.
```

---

## Phase 3: Fix Should-Address Issues

### Step 3A: Fix Pattern Violations

If code patterns are wrong:

**Invoke implementation-validator**:
```
Fix pattern violations in these files:
- [file1]: Use `add()` instead of manual sum
- [file2]: Use `adds` attribute instead of formula
- [file3]: Use `add() > 0` instead of `spm_unit.any()`
- [file4]: Reference should use tuple () not list []

Apply fixes following policyengine-code-style-skill patterns.
```

### Step 3B: Add Missing Tests

If tests are missing:

**Invoke edge-case-generator**:
```
Add missing tests for:
- [variable1]: Missing boundary test at threshold
- [variable2]: Missing zero income case
- [variable3]: Missing maximum household size case

Add to existing test files.
```

### Step 3C: Fix Naming Issues

If naming conventions violated:

**Invoke implementation-validator**:
```
Fix naming convention issues:
- [file1]: Variable should be {state}_{program}_{concept}
- [file2]: Parameter folder should be in states/{state}/

Rename files and update all references.
```

---

## Phase 4: Verify All Fixes

After all fixes applied, verify nothing is broken:

### Step 4A: Run Validators

**Invoke implementation-validator** (read-only check):
```
Verify all fixes were applied correctly:
- No remaining hard-coded values
- All patterns correct
- All naming conventions followed
```

**Invoke reference-validator** (read-only check):
```
Verify all references are correct:
- All parameters have references
- References corroborate values
- PDF pages included
```

### Step 4B: Run Tests Locally

```bash
# Run tests for the affected program
policyengine-core test policyengine_us/tests/policy/baseline/gov/states/[STATE]/[AGENCY]/[PROGRAM] -c policyengine_us -v
```

If tests fail, invoke **ci-fixer** to fix.

---

## Phase 5: Push Changes

### Step 5A: Format and Push

**Invoke pr-pusher**:
```
Push fixes to PR #$PR_NUMBER:
- Run make format
- Commit with message describing fixes
- Push to branch
```

### Step 5B: Post Summary Comment

```bash
gh pr comment $PR_NUMBER --body "## Fixes Applied

### 🔴 Critical Issues Fixed
- ✅ [Issue 1]: [How it was fixed]
- ✅ [Issue 2]: [How it was fixed]

### 🟡 Should-Address Issues Fixed
- ✅ [Issue 1]: [How it was fixed]
- ✅ [Issue 2]: [How it was fixed]

### Verification
- ✅ All validators pass
- ✅ All tests pass locally
- ✅ Code formatted

Ready for re-review."
```

---

## Issue Type → Agent Mapping

| Issue Type | Agent |
|------------|-------|
| Missing reference | parameter-architect |
| Bad reference format | parameter-architect |
| Hard-coded value (create param) | parameter-architect |
| Hard-coded value (use param) | rules-engineer |
| Regulatory mismatch | rules-engineer |
| Pattern violation | implementation-validator |
| Naming issue | implementation-validator |
| Missing test | edge-case-generator |
| CI failure | ci-fixer |
| Format issue | pr-pusher |

---

## Usage Examples

```bash
/fix-pr              # Fix PR for current branch
/fix-pr 6390         # Fix PR #6390
/fix-pr "Arkansas"   # Search for PR by title
```

---

## Fix Order (Important!)

Always fix in this order to avoid cascading issues:

```
1. Parameters (foundation)
   └─ References, values, structure

2. Variables (depend on parameters)
   └─ Hard-coded values, patterns, logic

3. Tests (depend on variables)
   └─ Missing tests, edge cases

4. Format & Push (last)
   └─ make format, commit, push
```

---

## Pre-Flight Checklist

Before starting:
- [ ] I will invoke agents for ALL fixes
- [ ] I will NOT use Edit/Write directly
- [ ] I will fix in dependency order (params → vars → tests)
- [ ] I will verify fixes with validators
- [ ] I will run tests before pushing

Start by gathering context, then proceed through the phases.
