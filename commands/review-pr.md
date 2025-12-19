---
description: Review an existing PR and post findings to GitHub (read-only, no code changes)
---

# Reviewing PR: $ARGUMENTS

**READ-ONLY MODE**: This command analyzes the PR and posts a review to GitHub WITHOUT making any code changes. Use `/fix-pr` to apply fixes.

## Determining Which PR to Review

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

echo "Reviewing PR #$PR_NUMBER"
```

---

## Phase 1: Gather Context

Collect information about the PR:

```bash
gh pr view $PR_NUMBER --json title,body,author,baseRefName,headRefName
gh pr checks $PR_NUMBER
gh pr diff $PR_NUMBER
```

Document:
- **PR type**: New program, bug fix, enhancement, or refactor
- **CI status**: Passing, failing, or pending
- **Files changed**: Parameters, variables, tests
- **Existing comments**: Any prior review feedback

---

## Phase 2: Run Validators

Run 4 focused validators. Each reports issues but does NOT make changes.

### Check 1: Regulatory Accuracy (Critical)

Invoke **program-reviewer** to:
- Research regulations FIRST (independent of code)
- Compare implementation to legal requirements
- Identify discrepancies between code and law
- Flag missing program components

**Key question**: Does this implementation correctly reflect the law?

### Check 2: Reference Quality (Critical)

Invoke **reference-validator** to:
- Find parameters missing references
- Check reference format (page numbers, detailed sections)
- Verify references corroborate values
- Check jurisdiction match (federal vs state sources)

**Key question**: Can every value be traced to an authoritative source?

### Check 3: Code Patterns (Critical + Should)

Invoke **implementation-validator** to:
- Find hard-coded values in formulas
- Check variable naming conventions
- Verify correct patterns (`adds`, `add()`, `add() > 0`)
- Check period usage (`period` vs `period.this_year`)
- Identify entity-level issues
- Flag incomplete implementations (TODOs, stubs)

**Key question**: Does the code follow PolicyEngine standards?

### Check 4: Test Coverage (Should)

Invoke **edge-case-generator** to:
- Identify missing boundary tests
- Find untested edge cases
- Check parameter combinations not tested
- Verify integration test exists

**Key question**: Are the important scenarios tested?

---

## Phase 3: Compile Findings

Aggregate and prioritize all findings:

### Priority Levels

**Critical (Must Fix Before Merge):**
- Regulatory mismatches (code doesn't match law)
- Hard-coded values (can't update when law changes)
- Missing or non-corroborating references
- CI failures
- Incorrect implementations

**Should Address:**
- Code pattern violations
- Missing edge case tests
- Naming convention issues
- Period usage errors

**Suggestions:**
- Documentation improvements
- Performance optimizations
- Code style refinements

### Deduplication

If multiple validators flag the same issue, combine into one finding with the highest priority level.

---

## Phase 4: Post Review

### Check for Existing Reviews

Before posting, check if you have a prior review on this PR:

```bash
# Get current GitHub user
CURRENT_USER=$(gh api user --jq '.login')

# Check for existing reviews from current user
EXISTING=$(gh api "/repos/{owner}/{repo}/pulls/$PR_NUMBER/comments" \
  --jq "[.[] | select(.user.login == \"$CURRENT_USER\")] | length")

if [ "$EXISTING" -gt 0 ]; then
    echo "Found existing review comments - will post updated review"
fi
```

### Post the Review

Post a single, clear review:

```bash
gh pr comment $PR_NUMBER --body "## PR Review

### 🔴 Critical (Must Fix)

1. **Regulatory mismatch**: [Description with specific file:line]
2. **Hard-coded value**: [Value] in [file:line] - create parameter
3. **Reference issue**: [File] - [specific problem]

### 🟡 Should Address

1. **Pattern violation**: Use \`add()\` instead of manual sum in [file:line]
2. **Missing test**: Add edge case for [scenario]

### 🟢 Suggestions

1. Consider adding calculation example in docstring

---

### Validation Summary

| Check | Result |
|-------|--------|
| Regulatory Accuracy | X issues |
| Reference Quality | X issues |
| Code Patterns | X issues |
| Test Coverage | X gaps |
| CI Status | Passing/Failing |

### Next Steps

To auto-fix issues: \`/fix-pr $PR_NUMBER\`

Or address manually and re-request review."
```

### CI Failures

If CI is failing, add to the Critical section:

```bash
gh pr checks $PR_NUMBER --json name,conclusion \
  --jq '.[] | select(.conclusion == "failure") | "- **CI Failure**: " + .name'
```

---

## Review Severity

Based on findings, set the review type:

| Severity | When to Use |
|----------|-------------|
| **APPROVE** | No critical issues, minor suggestions only |
| **COMMENT** | Has issues but not blocking (educational) |
| **REQUEST_CHANGES** | Has critical issues that must be fixed |

---

## Usage Examples

```bash
/review-pr              # Review PR for current branch
/review-pr 6390         # Review PR #6390
/review-pr "Arkansas"   # Search for PR by title
```

---

## Critical Issues (Always Flag)

These MUST be fixed before merge:

1. **Regulatory mismatch** - Implementation doesn't match law
2. **Hard-coded values** - Numbers in formulas instead of parameters
3. **Missing references** - Can't verify where values came from
4. **Non-corroborating references** - Reference doesn't support value
5. **CI failures** - Tests or linting failing
6. **Incorrect formula** - Wrong calculation logic

---

## Pre-Flight Checklist

Before starting:
- [ ] I will NOT make any code changes
- [ ] I will run all 4 validators
- [ ] I will prioritize findings (Critical > Should > Suggestions)
- [ ] I will post a single clear review
- [ ] I will be constructive and actionable

Start by determining which PR to review, then proceed through the phases.
