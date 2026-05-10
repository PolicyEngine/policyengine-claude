---
description: Rebase current branch onto main/master with interactive merge conflict resolution and post-rebase audit
---

# Rebasing current branch onto upstream

**IMPORTANT:** This command manages a full rebase workflow — updating the base branch, replaying commits, resolving conflicts interactively, and auditing the result.

## Step 1: Capture pre-rebase state

Before doing anything, snapshot the current state so we can audit afterwards.

```bash
# Record current branch
CURRENT_BRANCH=$(git branch --show-current)

if [[ "$CURRENT_BRANCH" == "main" || "$CURRENT_BRANCH" == "master" ]]; then
  echo "ERROR: You are on $CURRENT_BRANCH. Switch to a feature branch first."
  exit 1
fi

echo "Current branch: $CURRENT_BRANCH"
```

Capture the full pre-rebase commit list and diff summary — these are needed for the post-rebase audit in Step 5.

```bash
# Determine base branch
if git rev-parse --verify main >/dev/null 2>&1; then
  BASE_BRANCH="main"
elif git rev-parse --verify master >/dev/null 2>&1; then
  BASE_BRANCH="master"
else
  echo "ERROR: Neither main nor master branch exists locally."
  exit 1
fi

echo "Base branch: $BASE_BRANCH"

# Snapshot: commits on this branch since divergence
PRE_REBASE_COMMITS=$(git log --oneline "$BASE_BRANCH".."$CURRENT_BRANCH")
PRE_REBASE_COMMIT_COUNT=$(echo "$PRE_REBASE_COMMITS" | grep -c .)
PRE_REBASE_SHAS=$(git log --format='%H' "$BASE_BRANCH".."$CURRENT_BRANCH")

echo ""
echo "Commits to replay ($PRE_REBASE_COMMIT_COUNT):"
echo "$PRE_REBASE_COMMITS"

# Snapshot: full diff summary (files changed + insertions/deletions)
PRE_REBASE_DIFF_STAT=$(git diff --stat "$BASE_BRANCH"..."$CURRENT_BRANCH")
PRE_REBASE_DIFF_NUMSTAT=$(git diff --numstat "$BASE_BRANCH"..."$CURRENT_BRANCH")

echo ""
echo "Diff summary before rebase:"
echo "$PRE_REBASE_DIFF_STAT"
```

**Save** `PRE_REBASE_COMMITS`, `PRE_REBASE_COMMIT_COUNT`, `PRE_REBASE_SHAS`, `PRE_REBASE_DIFF_STAT`, and `PRE_REBASE_DIFF_NUMSTAT` — you will need all of these in Step 5.

## Step 2: Update base branch

```bash
git checkout "$BASE_BRANCH"
git pull origin "$BASE_BRANCH"
git checkout "$CURRENT_BRANCH"
```

If `git pull` fails (e.g. network issue), stop and report the error.

## Step 3: Start the rebase

```bash
git rebase "$BASE_BRANCH"
```

If the rebase completes with no conflicts, skip directly to **Step 5** (post-rebase audit).

## Step 4: Resolve conflicts (iterative)

When the rebase stops on a conflict, follow this loop **for every conflicting commit**:

### 4a. Identify the conflicting commit

```bash
# Which commit are we replaying?
CONFLICT_COMMIT=$(git rebase --show-current-patch | head -5)

# Which files conflict?
CONFLICTING_FILES=$(git diff --name-only --diff-filter=U)

echo "Conflict while replaying:"
echo "$CONFLICT_COMMIT"
echo ""
echo "Conflicting files:"
echo "$CONFLICTING_FILES"
```

### 4b. Analyze each conflicting file

For **every** file in `CONFLICTING_FILES`:

1. Read the file and find all conflict markers (`<<<<<<<`, `=======`, `>>>>>>>`).
2. For each conflict hunk, identify:
   - **Ours (HEAD):** what the base branch now has
   - **Theirs (incoming):** what the feature branch commit introduces
3. Determine the **intent** of both sides:
   - Was one side adding a feature? Fixing a bug? Refactoring?
   - Did both sides modify the same logic, or adjacent lines?
4. Decide on a resolution strategy:
   - **Accept ours** — the base branch change supersedes
   - **Accept theirs** — the feature branch change should be kept
   - **Merge both** — both changes are needed (explain how they combine)
   - **Rewrite** — neither version is correct after combining; propose new code

### 4c. Present the resolution plan to the user

For each conflicting file, present a clear summary using `AskUserQuestion`:

```
File: path/to/file.ts

Conflict 1 (lines X-Y):
  BASE (main) added: [description of what main introduced]
  FEATURE ($CURRENT_BRANCH) changed: [description of what the commit does]

  Suggested resolution: [Accept ours / Accept theirs / Merge both / Rewrite]
  Reasoning: [Why this resolution is correct]

  Proposed result:
  [Show the exact code that will replace the conflict block]
```

Ask the user:
- "Approve this resolution plan?" with options: "Yes, apply all", "Let me modify", "Skip this file (I'll fix manually)"

### 4d. Apply the approved resolution

For each file the user approved:

1. Edit the file to replace the conflict markers with the resolved code.
2. Verify no conflict markers remain in the file:
   ```bash
   grep -n '<<<<<<<\|=======\|>>>>>>>' path/to/file.ts
   ```
3. Stage the resolved file:
   ```bash
   git add path/to/file.ts
   ```

For files the user chose to fix manually, leave them and remind the user to `git add` them when done.

### 4e. Continue the rebase

Once all conflicting files for this commit are resolved and staged:

```bash
git rebase --continue
```

If the rebase stops again on the **next** commit, go back to **Step 4a**. Repeat until the rebase completes or the user aborts.

### 4f. Abort escape hatch

At any point during conflict resolution, if the user wants to bail out:

```bash
git rebase --abort
```

This restores the branch to its exact pre-rebase state.

## Step 5: Post-rebase audit

After the rebase completes successfully, perform a thorough audit comparing pre-rebase and post-rebase state.

### 5a. Check for dropped commits

```bash
POST_REBASE_COMMITS=$(git log --oneline "$BASE_BRANCH".."$CURRENT_BRANCH")
POST_REBASE_COMMIT_COUNT=$(echo "$POST_REBASE_COMMITS" | grep -c .)

echo "Commits before rebase: $PRE_REBASE_COMMIT_COUNT"
echo "Commits after rebase:  $POST_REBASE_COMMIT_COUNT"
```

If the counts differ, investigate:
- Were any commits dropped because they became empty (already applied on main)?
- Were any commits squashed unexpectedly?

For each pre-rebase SHA, check if its changes are represented in the post-rebase history:

```bash
# For each original commit, check if its patch is present
for SHA in $PRE_REBASE_SHAS; do
  SUBJECT=$(git log --format='%s' -1 "$SHA")
  # Search for matching subject in post-rebase history
  if git log --oneline "$BASE_BRANCH".."$CURRENT_BRANCH" | grep -qF "$SUBJECT"; then
    echo "OK: $SUBJECT"
  else
    echo "MISSING: $SUBJECT (was $SHA)"
  fi
done
```

### 5b. Check for lost changes (path-level diff comparison)

Compare the net effect of the branch before and after rebase:

```bash
POST_REBASE_DIFF_NUMSTAT=$(git diff --numstat "$BASE_BRANCH"..."$CURRENT_BRANCH")
```

Compare each file's insertions/deletions between pre and post. Flag files where:
- A file that was modified pre-rebase is no longer modified post-rebase (change was lost)
- A file has significantly fewer insertions post-rebase (partial change loss)
- A new file appeared in the diff that wasn't there before (unintended inclusion)

### 5c. Check for files that moved or were renamed on main

```bash
# Files that were renamed on main since the branch diverged
git diff --diff-filter=R --name-status "$BASE_BRANCH"@{upstream}..HEAD
```

If the branch was modifying a file that main renamed, the changes may have been silently dropped during rebase (no conflict, just lost). Flag these.

### 5d. Check for common rebase hazards

1. **Import breakage**: If main restructured modules/imports, the rebased code may reference old paths.
2. **Duplicate logic**: If main added similar functionality, the rebased commits may now duplicate it.
3. **Test conflicts**: If main changed test infrastructure, rebased tests may not run.

Run a quick scan:
```bash
# Check for any remaining conflict markers in tracked files
git grep -l '<<<<<<<' || echo "No conflict markers found"

# Check if the branch compiles / has obvious syntax errors (if applicable)
# This is repo-specific — check for package.json, Makefile, etc.
```

### 5e. Report to the user

Present a structured assessment:

```
## Rebase audit report

### Commits
- Before: N commits
- After:  M commits
- Dropped: [list any missing commits and why]

### Changes
- Files modified before: X
- Files modified after:  Y
- [List any files where changes were lost or significantly altered]

### Risks
- [HIGH/MEDIUM/LOW]: [Description of each risk found]
  - e.g., HIGH: path/to/file.ts was renamed on main but your branch modified the old path — changes may be lost
  - e.g., MEDIUM: main added similar validation logic in validators.ts — check for duplication
  - e.g., LOW: 2 commits became empty and were dropped (already on main)

### Recommendation
- [Summary: is the rebase clean, or should the user inspect specific files?]
```

If no issues are found, say so clearly:

```
Rebase completed cleanly. All N commits replayed successfully.
No dropped commits, no lost changes, no path conflicts detected.
```
