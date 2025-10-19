---
description: Create PR as draft, wait for CI to pass, then mark ready for review (solves the "I'll check back later" problem)
---

# Creating PR with CI Verification

**IMPORTANT:** This command solves the common problem where Claude creates a PR, says "I'll wait for CI", then gives up. This command ACTUALLY waits for CI completion.

## Workflow

This command will:
1. ✅ Create PR as draft
2. ✅ Wait for CI checks to complete (actually wait, not give up)
3. ✅ Mark as ready for review if CI passes
4. ✅ Report failures with links if CI fails

## Step 1: Determine Current Branch and Changes

```bash
# Get current branch
CURRENT_BRANCH=$(git branch --show-current)

# Get base branch (usually main or master)
BASE_BRANCH=$(git remote show origin | grep 'HEAD branch' | cut -d' ' -f5)

# Verify we're not on main/master
if [[ "$CURRENT_BRANCH" == "main" || "$CURRENT_BRANCH" == "master" ]]; then
  echo "ERROR: Cannot create PR from main/master branch"
  echo "Create a feature branch first: git checkout -b feature-name"
  exit 1
fi

# Check if branch is pushed
git rev-parse --verify origin/$CURRENT_BRANCH > /dev/null 2>&1
if [ $? -ne 0 ]; then
  echo "Branch not pushed yet. Pushing now..."
  git push -u origin $CURRENT_BRANCH
fi
```

## Step 2: Gather PR Context

Run in parallel to gather information:

```bash
# 1. Git status
git status

# 2. Diff since divergence from base
git diff ${BASE_BRANCH}...HEAD

# 3. Commit history for this branch
git log ${BASE_BRANCH}..HEAD --oneline

# 4. Check if PR already exists
gh pr view --json number,state,isDraft 2>/dev/null
```

**If PR already exists:**
```bash
EXISTING_PR=$(gh pr view --json number --jq '.number')
echo "PR #$EXISTING_PR already exists for this branch"
echo "Use /review-pr $EXISTING_PR or /fix-pr $EXISTING_PR instead"
exit 0
```

## Step 3: Create PR Title and Body

Based on the changes (read from git diff and commit history):

**Title:** Concise summary of changes (50 chars max)

**Body format:**
```markdown
## Summary
- Bullet point 1
- Bullet point 2

## Changes
- Specific change 1
- Specific change 2

## Testing
- Test approach
- Verification steps

## Checklist
- [ ] Tests pass locally
- [ ] Code formatted (make format)
- [ ] Changelog entry created (if applicable)

---

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

## Step 4: Create PR as Draft

**CRITICAL:** Always create as draft initially.

```bash
# Create PR as draft
gh pr create \
  --title "PR Title Here" \
  --body "$(cat <<'EOF'
PR body here
EOF
)" \
  --draft

# Get PR number
PR_NUMBER=$(gh pr view --json number --jq '.number')
echo "Created draft PR #$PR_NUMBER"
echo "URL: $(gh pr view --json url --jq '.url')"
```

## Step 5: Wait for CI Checks (DO NOT GIVE UP!)

**This is where Claude usually fails. DO NOT say "I'll check back later".**

**Instead, ACTUALLY wait using a polling loop with NO timeout:**

```bash
echo "Waiting for CI checks to complete..."
echo "Typical CI times by repository:"
echo "  - policyengine-app: 3-6 minutes"
echo "  - policyengine-uk: 9-12 minutes"
echo "  - policyengine-api: 30 minutes"
echo "  - policyengine-us: 60-75 minutes (longest)"
echo ""
echo "I will poll every 15 seconds until all checks complete. No time limit."

POLL_INTERVAL=15  # Check every 15 seconds
ELAPSED=0

while true; do
  # Get check status
  CHECKS_JSON=$(gh pr checks $PR_NUMBER --json name,status,conclusion)

  # Count checks
  TOTAL=$(echo "$CHECKS_JSON" | jq '. | length')

  if [ "$TOTAL" -eq 0 ]; then
    echo "No CI checks found yet. Waiting for checks to start..."
    sleep $POLL_INTERVAL
    ELAPSED=$((ELAPSED + POLL_INTERVAL))
    continue
  fi

  # Count by status
  COMPLETED=$(echo "$CHECKS_JSON" | jq '[.[] | select(.status == "COMPLETED")] | length')
  FAILED=$(echo "$CHECKS_JSON" | jq '[.[] | select(.conclusion == "FAILURE")] | length')

  echo "[$ELAPSED s] CI Checks: $COMPLETED/$TOTAL completed, $FAILED failed"

  # If all completed
  if [ "$COMPLETED" -eq "$TOTAL" ]; then
    if [ "$FAILED" -eq 0 ]; then
      echo "✅ All CI checks passed after $ELAPSED seconds!"
      break
    else
      echo "❌ Some CI checks failed after $ELAPSED seconds."
      # Show failures
      gh pr checks $PR_NUMBER
      break
    fi
  fi

  # Continue waiting (no timeout!)
  sleep $POLL_INTERVAL
  ELAPSED=$((ELAPSED + POLL_INTERVAL))
done
```

**Important:** No timeout means we actually wait as long as needed. Population simulations can take 30+ minutes.

## Step 6: Mark Ready for Review (If CI Passed)

```bash
if [ "$FAILED" -eq 0 ] && [ "$COMPLETED" -eq "$TOTAL" ]; then
  echo "Marking PR as ready for review..."
  gh pr ready $PR_NUMBER

  echo ""
  echo "✅ PR #$PR_NUMBER is ready for review!"
  echo "URL: $(gh pr view $PR_NUMBER --json url --jq '.url')"
  echo ""
  echo "All CI checks passed:"
  gh pr checks $PR_NUMBER
else
  echo ""
  echo "⚠️ PR remains as draft due to CI issues."
  echo "URL: $(gh pr view $PR_NUMBER --json url --jq '.url')"
  echo ""
  echo "CI status:"
  gh pr checks $PR_NUMBER
  echo ""
  echo "To fix and retry:"
  echo "1. Fix the failing checks"
  echo "2. Push changes: git push"
  echo "3. Run this command again to re-check CI"
fi
```


## Key Differences from Default Behavior

**Old way (Claude gives up):**
```
Claude: "I've created the PR. CI will take a while, I'll check back later..."
[Chat ends, Claude never checks back]
User: Has to manually check CI and mark ready
```

**New way (this command actually waits):**
```
Claude: "I've created the PR as draft. Now waiting for CI..."
[Actually polls CI status every 15 seconds]
Claude: "CI passed! Marking as ready for review."
[PR is ready, user doesn't have to do anything]
```

## Error Handling

**If CI fails:**
```bash
echo "❌ CI checks failed. Here are the failures:"
gh pr checks $PR_NUMBER

echo ""
echo "Common fixes:"
echo "- Linting errors: make format && git push"
echo "- Test failures: See logs at PR URL"
echo "- Use /fix-pr $PR_NUMBER to attempt automated fixes"
```

**If no CI configured:**
```bash
if [ "$TOTAL" -eq 0 ] && [ $ELAPSED -gt 60 ]; then
  echo "⚠️ No CI checks detected after 60 seconds."
  echo "Repository may not have CI configured."
  echo "Marking PR as ready for manual review."
  gh pr ready $PR_NUMBER
fi
```

## Usage Examples

**Basic:**
```bash
# Make changes, commit
git add .
git commit -m "Add feature"

# Create PR (command waits for CI)
/create-pr
```

**With custom title:**
```bash
# Command can accept optional arguments
/create-pr "Add California EITC implementation"
```

**Checking existing PR:**
```bash
# If PR exists, command tells you and suggests alternatives
/create-pr
# Output: "PR #123 exists. Use /review-pr 123 or /fix-pr 123"
```

## Integration with Other Commands

**After /encode-policy or /fix-pr:**
```bash
# These commands might push code
# Use /create-pr to create PR and wait for CI
/create-pr
```

**After fixing CI issues:**
```bash
# Fix issues locally
make format
git add .
git commit -m "Fix linting"
git push

# Command will detect existing PR and re-check CI
/create-pr  # "PR #123 exists, checking CI status..."
```

## CI Duration Expectations

**By repository (based on actual data):**
- **policyengine-app:** 3-6 minutes (fast)
- **policyengine-uk:** 9-12 minutes (medium)
- **policyengine-api:** ~30 minutes (slow)
- **policyengine-us:** 60-75 minutes (very slow - population simulations)

**The command has no timeout** - it will wait as long as needed, even for policyengine-us's 75-minute CI runs.

## Why This Works

**Problem:** Claude's internal timeout or context leads it to give up

**Solution:**
1. ✅ Explicit polling loop (Claude sees the code will wait)
2. ✅ Clear status updates (Claude knows it's still working)
3. ✅ Timeout is explicit (Claude knows how long to wait)
4. ✅ Fallback handling (What to do if timeout occurs)

**Key insight:** By having the command contain the waiting logic in bash, Claude executes it and actually waits instead of just saying "I'll wait."

## Notes

**This command is essential for:**
- Automated PR workflows
- CI-dependent merges
- Team workflows requiring CI validation
- Reducing manual PR management

**Use this instead of:**
- Manual `gh pr create` followed by manual CI checking
- Asking Claude to "wait for CI" (which it can't do reliably)
- Creating ready PRs before CI passes
