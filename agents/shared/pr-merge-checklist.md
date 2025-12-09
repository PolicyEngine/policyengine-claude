# PR Merge Checklist

When asked to "action", "merge", or "complete" a PR, follow this checklist BEFORE merging:

## Pre-Merge Validation

### 1. Check Review Status
```bash
gh pr view $PR_NUMBER --json reviews,reviewDecision
```

**CRITICAL**: Do NOT merge if:
- There are unresolved review comments (use `/fix-pr` instead)
- Review decision is "CHANGES_REQUESTED"
- Review decision is "REVIEW_REQUIRED" (unless explicitly told to override)

### 2. Check CI Status
```bash
gh pr checks $PR_NUMBER
```

**CRITICAL**: Do NOT merge if:
- Any required checks are failing
- Checks are still running (wait for completion)

### 3. Review Comment Analysis
If there ARE review comments, parse them to determine if they require action:

```bash
gh pr view $PR_NUMBER --json comments,reviews
```

For each review comment:
- **Requesting changes?** → Use `/fix-pr` to address them
- **Approved with optional suggestions?** → Can merge if author wants
- **Discussion/questions only?** → Can merge if resolved

## Decision Tree

```
"Can you action this PR?"
  ↓
Are there review comments? → YES → Run `/fix-pr $PR_NUMBER` instead
  ↓ NO
Are CI checks passing? → NO → Fix CI first, then merge
  ↓ YES
Merge the PR ✓
```

## Common Mistakes to Avoid

❌ **WRONG**: Immediately merging when seeing "action this"
✅ **RIGHT**: Check review comments and CI status first

❌ **WRONG**: Ignoring review comments that request changes
✅ **RIGHT**: Use `/fix-pr` to address all review feedback

❌ **WRONG**: Merging a PR with failing CI
✅ **RIGHT**: Fix CI failures before merging

## Example Workflow

```bash
# User says: "@policyengine can you action this"

# Step 1: Check for reviews
gh pr view $PR_NUMBER --json reviews,comments --jq '.reviews'

# Step 2: If reviews found with changes requested
echo "Found unresolved review comments. Running /fix-pr instead..."
# Use /fix-pr to address them

# Step 3: If no reviews or approved
gh pr checks $PR_NUMBER
# If passing, proceed to merge

# Step 4: Merge
gh pr merge $PR_NUMBER --squash
```

## When to Use /fix-pr vs Direct Merge

| Situation | Action |
|-----------|--------|
| No reviews, CI passing | Direct merge ✓ |
| Reviews approved, CI passing | Direct merge ✓ |
| Review comments with changes requested | Use `/fix-pr` |
| Review comments unresolved | Use `/fix-pr` |
| CI failing | Fix CI, then merge |
| Discussion ongoing | Ask user for clarification |

## Remember

The `/fix-pr` command exists specifically to handle review comments and validation issues. Use it when there's ANY indication that the PR needs improvements before merging.

**Default assumption**: If review comments exist, they should be addressed before merging unless explicitly told otherwise.
