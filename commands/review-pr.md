---
description: Review an existing PR and post findings to GitHub (read-only, no code changes)
---

# Reviewing PR: $ARGUMENTS

**READ-ONLY MODE**: This command analyzes the PR and posts a review to GitHub WITHOUT making any code changes. Use `/fix-pr` to apply fixes.

## Options

- `--local` - Show findings locally only, skip GitHub posting

## Step 1: Determine Posting Mode

**If `--local` flag is provided**: Skip prompt, proceed in local-only mode.

**If no flag provided**: Use `AskUserQuestion` to prompt BEFORE starting review:

```
Question: "Would you like to post this review to GitHub when complete?"
Options:
  - "Yes, post to GitHub" (default)
  - "No, show locally only"
```

Store the user's choice and proceed with the review.

---

## Step 2: Determine Which PR to Review

```bash
# Parse arguments for --local flag
LOCAL_ONLY=false
PR_ARG=""
for arg in $ARGUMENTS; do
    if [ "$arg" = "--local" ]; then
        LOCAL_ONLY=true
    else
        PR_ARG="$arg"
    fi
done

# If no PR argument provided, use current branch's PR
if [ -z "$PR_ARG" ]; then
    CURRENT_BRANCH=$(git branch --show-current)
    PR_NUMBER=$(gh pr list --head "$CURRENT_BRANCH" --json number --jq '.[0].number')
    if [ -z "$PR_NUMBER" ]; then
        echo "No PR found for current branch $CURRENT_BRANCH"
        exit 1
    fi
# If argument is a number, use it directly
elif [[ "$PR_ARG" =~ ^[0-9]+$ ]]; then
    PR_NUMBER=$PR_ARG
# Otherwise, search for PR by description/title
else
    PR_NUMBER=$(gh pr list --search "$PR_ARG" --json number,title --jq '.[0].number')
    if [ -z "$PR_NUMBER" ]; then
        echo "No PR found matching: $PR_ARG"
        exit 1
    fi
fi

echo "Reviewing PR #$PR_NUMBER"
if [ "$LOCAL_ONLY" = true ]; then
    echo "Mode: Local only (will not post to GitHub)"
fi
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

**If user chose local-only mode**: Display findings locally and skip GitHub posting.

**If user chose to post to GitHub**: Continue with posting.

### Check for Existing Reviews (if posting)

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

### Post the Review (if user confirms)

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
/review-pr              # Review PR for current branch (prompts before posting)
/review-pr 6390         # Review PR #6390 (prompts before posting)
/review-pr "Arkansas"   # Search for PR by title (prompts before posting)
/review-pr --local      # Review current branch's PR, show locally only
/review-pr 6390 --local # Review PR #6390, show locally only
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
- [ ] I will ask user about posting mode FIRST (unless --local flag used)
- [ ] I will NOT make any code changes
- [ ] I will run all 4 validators
- [ ] I will prioritize findings (Critical > Should > Suggestions)
- [ ] I will be constructive and actionable

Start by asking the user about posting mode, then proceed through the phases.
