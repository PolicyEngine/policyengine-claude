---
description: Apply fixes to a PR based on /review-program findings or PR review comments
---

# Fixing PR: $ARGUMENTS

Apply fixes to PR issues identified by `/review-program` or GitHub review comments.

## Arguments

`$ARGUMENTS` should contain:
- **PR number or title** (optional) — e.g., `6390` or `"Arkansas TANF"`. If omitted, prompts.
- **Options**:
  - `--local` — apply fixes locally only, skip GitHub posting and pushing
  - `--resume` — reuse valid context, plan, and evidence artifacts from an interrupted run
  - `--full-validation` — run a broader package suite after targeted PR tests pass

**Examples:**
```bash
/fix-pr              # Fix PR for current branch (prompts for everything)
/fix-pr 6390         # Fix PR #6390
/fix-pr "Arkansas"   # Search for PR by title
/fix-pr --local      # Fix current branch's PR, keep changes local
/fix-pr 6390 --local # Fix PR #6390, keep changes local
/fix-pr 6390 --resume
```

---

## YOUR ROLE: COORDINATOR ONLY

**CRITICAL — Context Window Protection:**
- You are a coordinator. You do NOT read diffs, code files, or full review reports.
- ALL information-gathering work is delegated to agents.
- You only read files marked "Short" in the handoff table (max 50 lines each).
- ALL data flows through files on disk. Agent prompts reference file paths, never paste content.

**You MUST NOT:**
- Read the PR diff (`{RUN_ROOT}/{PREFIX}-fix-pr-diff.txt`)
- Read parameter YAML files or variable .py files
- Read full review reports directly
- Use Edit/Write directly — agents handle all code changes

**You DO:**
- Parse arguments
- Run `gh` commands for small structured JSON
- Save diff to disk for agents
- Read SHORT summary files only
- Present checkpoints to user via `AskUserQuestion`
- Spawn agents for all fixes

---

## Phase 0: Parse Arguments & Setup

### Step 0A: Parse Arguments & Resolve Worktree Root

**Derive the worktree namespace first** so concurrent worktrees cannot read, delete, or
overwrite each other's files:
```bash
WORKTREE_ROOT=$(git rev-parse --show-toplevel)
WORKTREE_ID=$(printf '%s' "$WORKTREE_ROOT" | git hash-object --stdin | cut -c1-12)
RUN_ROOT="/tmp/policyengine-command-runs/$WORKTREE_ID"
mkdir -p "$RUN_ROOT"
```

`WORKTREE_ROOT`, not the shared Git common directory or branch name, is the isolation
boundary. Substitute `{RUN_ROOT}` in every agent prompt and never use process-global
`/tmp/fix-pr-*` or `/tmp/{PREFIX}-...` files.

Before checkout, inspect `git worktree list --porcelain` and the PR's `headRefName`:

- If the PR branch is the current branch, continue in this worktree.
- If it is checked out in another worktree, stop and report that worktree path; do not
  mutate it from here and do not use `--ignore-other-worktrees`.
- Otherwise, `gh pr checkout $PR_NUMBER` in the current worktree, recompute `PREFIX` from
  the checked-out branch, and continue.

All edits, tests, staging, commits, and pushes must run from `WORKTREE_ROOT`. Never stage
or edit files through another worktree path.

```
Parse $ARGUMENTS:
- PR_ARG: first non-flag argument (number or search text)
- LOCAL_ONLY: true if --local flag present
- RESUME: true if --resume
- FULL_VALIDATION: true if --full-validation
```

### Step 0B: Determine Which PR to Fix

```bash
if [[ "$PR_ARG" =~ ^[0-9]+$ ]]; then
    PR_NUMBER=$PR_ARG
else
    PR_NUMBER=$(gh pr list --search "$PR_ARG" --json number,title --jq '.[0].number')
    if [ -z "$PR_NUMBER" ]; then
        echo "No PR found matching: $PR_ARG"
        exit 1
    fi
fi
```

**If no PR argument provided**: Use `AskUserQuestion`:

```
AskUserQuestion:
  Question: "Which PR would you like to fix?"
  Options:
    - "Enter PR number (e.g., 6390)"
    - "Enter PR name/title (e.g., 'Arkansas TANF')"
```

After resolving the PR, follow the worktree check above. Check it out here only when no
other worktree owns the head branch. Then derive the final prefix and initialize state:

```bash
PREFIX=$(git branch --show-current | tr '/' '-')
PREFIX=${PREFIX:-fix-pr}
if [ "$RESUME" != "true" ]; then
  rm -f "$RUN_ROOT/${PREFIX}-fix-pr-"*.md "$RUN_ROOT/${PREFIX}-fix-pr-diff.txt"
fi
```

Use `{RUN_ROOT}/{PREFIX}-fix-pr-run-state.md` to record `WORKTREE_ROOT`, `WORKTREE_ID`, the
PR/head SHA, arguments, completed phases, artifact paths, test commands, and elapsed time.
A resume may reuse an artifact only when its PR number/head SHA and input hashes still
match. Invalidate dependent artifacts when the diff or selected fix scope changed. Refuse
artifacts recorded by a different worktree.

### Step 0C: Determine Posting Mode

**If `--local` flag**: Skip prompt, proceed in local-only mode.

**If no flag**: Use `AskUserQuestion`:

```
AskUserQuestion:
  Question: "Push changes and post summary to GitHub when complete?"
  Options:
    - "Yes, push and post to GitHub" (default)
    - "No, keep changes local only"
```

---

## Phase 1: Gather Context

Main Claude runs small structured commands only:

```bash
gh pr view $PR_NUMBER --json title,body,author,baseRefName,headRefName
gh pr checks $PR_NUMBER
gh pr diff $PR_NUMBER > {RUN_ROOT}/{PREFIX}-fix-pr-diff.txt
```

**Main Claude does NOT read the diff file.** It saves it to disk for the context agent.

Check for local `/review-program` files from a previous run:

```bash
ls $RUN_ROOT/${PREFIX}-review-full-report.md 2>/dev/null && echo "LOCAL_REVIEW=true" || echo "LOCAL_REVIEW=false"
```

Reuse a local review only when its `Reviewed head SHA` matches the PR head. Otherwise,
treat it as historical context and use current review comments/diff as authoritative.

### Step 1A: Delegate context gathering

```
subagent_type: "general-purpose"
name: "context-gatherer"

"Analyze PR #{PR_NUMBER} to identify issues that need fixing.

READ:
- {RUN_ROOT}/{PREFIX}-fix-pr-diff.txt (the PR diff)

SOURCES — check both, use whichever has findings (or both):

1. LOCAL REVIEW FILES (from a /review-program run in this session):
   - {RUN_ROOT}/{PREFIX}-review-full-report.md (if it exists)
   - {RUN_ROOT}/{PREFIX}-review-summary.md (if it exists)

2. PR COMMENTS AND REVIEWS (from GitHub):
   Run these commands to get review data:
   - gh pr view {PR_NUMBER} --json reviews --jq '.reviews[] | {author: .author.login, state: .state, submittedAt: .submittedAt, body: .body}'
   - gh pr view {PR_NUMBER} --json comments --jq '.comments[] | {author: .author.login, createdAt: .createdAt, body: .body}'
   - gh pr view {PR_NUMBER} --json commits --jq '.commits[-1].committedDate'

COMMENT FRESHNESS — determine which PR comments are still valid:

1. Get the last commit timestamp from the commits query above.
2. For each comment/review:
   a. If posted AFTER last commit → CURRENT (all valid)
   b. If posted BEFORE last commit → check staleness:
      - Thread resolved on GitHub? → RESOLVED (skip)
      - The flagged file/line was modified in a commit after the comment?
        Check with: git log --oneline --after='{comment_date}' -- '{file_path}'
        If modified → POSSIBLY-FIXED
      - Otherwise → STALE-BUT-OPEN (still valid, flag for user)
3. Ignore reviews with state DISMISSED.
4. Include ALL comments from all authors — do not deduplicate by author.
   (A reviewer may leave multiple separate comments on different issues.)

TASK:
1. Merge findings from local review files AND valid PR comments (deduplicate
   if the same issue appears in both — prefer the more detailed version)
2. For each issue, classify:
   - CLEAR: obviously fixable (missing reference, formatting, hard-coded value)
   - AMBIGUOUS: might be by design or needs verification (regulatory mismatch,
     value discrepancy, unusual pattern choice)
   - RESEARCH-NEEDED: requires checking the review report evidence before deciding

3. Write {RUN_ROOT}/{PREFIX}-fix-pr-issues.md (max 50 lines):

   ## Issues for PR #{PR_NUMBER}

   ### Source Summary
   - Local /review-program report: {found / not found}
   - PR comments: {N} from {authors}
     - {X} current (after last commit on {date})
     - {Y} stale-but-open (before last commit, file not modified since)
     - {Z} possibly-fixed (before last commit, file modified since)
     - {W} resolved (skipped)

   ### Critical ({N})
   - [CLEAR] Missing reference in {file} — no citation (source: review-program)
   - [AMBIGUOUS] Regulatory mismatch in {file} — code uses 200% FPL, review says 185% (source: @author, Mar 3)
   - [RESEARCH-NEEDED] Value mismatch: repo=$500, PDF=$485 in {file} (source: review-program)
   - [CLEAR] [POSSIBLY-FIXED] Hard-coded value in {file} (source: @author, Feb 28 — file modified Mar 1)

   ### Should Address ({M})
   - [CLEAR] Pattern violation in {file} — use add() not manual sum (source: review-program)
   - [CLEAR] Missing boundary test for {variable} (source: @author, Mar 3)

   ### Suggestions ({P})
   - [CLEAR] Add docstring to {variable} (source: review-program)

   ### Summary
   - Total: {N+M+P}
   - Clear: {count}, Ambiguous: {count}, Research needed: {count}
   - Possibly already fixed: {count}"
```

Read ONLY `{RUN_ROOT}/{PREFIX}-fix-pr-issues.md` (max 50 lines).

---

## Phase 2: Fix Plan Checkpoint (USER CHECKPOINT)

Present a brief overview from the issues file:

```
## PR #{PR_NUMBER} — Issues Found

**Critical**: {N} issues
**Should Address**: {M} issues
**Suggestions**: {P} issues
**Possibly already fixed**: {K} issues
```

Then walk through decisions using `AskUserQuestion`:

### Step 2A: Fix scope

```
AskUserQuestion:
  Question: "Which issue categories should I fix?"
  Options:
    - "Critical only" (recommended if Critical > 0)
    - "Critical + Should Address" (recommended if Critical == 0)
    - "All including Suggestions"
    - "Let me review each issue"
```

### Step 2B: Possibly-fixed issues (only if any exist)

For each `POSSIBLY-FIXED` issue within the chosen scope:

```
AskUserQuestion:
  Question: "[POSSIBLY-FIXED] {issue description}"
  Description: "Flagged by @{author} on {date}, but {file} was modified on {later_date}."
  Options:
    - "Already fixed — skip" (recommended)
    - "Still an issue — fix it"
    - "Not sure — check it"
```

### Step 2C: Per-issue review (only if user chose "Let me review each issue")

For each issue in scope, present it with context. Options vary by classification:

**CLEAR issues** (e.g., missing reference, formatting violation):

```
AskUserQuestion:
  Question: "[Critical] Missing reference in {file}"
  Description: "Parameter has no citation — needs a regulatory source link"
  Options:
    - "Fix" (default)
    - "Skip"
```

**AMBIGUOUS issues** (e.g., regulatory mismatch, unusual pattern):

```
AskUserQuestion:
  Question: "[Critical] Regulatory mismatch in {file}"
  Description: "Code uses 200% FPL threshold but regulation says 185% FPL. This could be intentional if the state has a transitional rate or waiver."
  Options:
    - "Fix — code should match regulation"
    - "Not an issue — this is by design"
    - "Needs research — check review report for evidence"
```

**RESEARCH-NEEDED issues** (e.g., value discrepancy, ambiguous regulation):

```
AskUserQuestion:
  Question: "[Critical] Value mismatch: repo=$500, PDF=$485 in {file}"
  Description: "Could be an uprating difference, a different edition of the source, or a genuine error."
  Options:
    - "Research first — check review report for evidence"
    - "Fix — use the PDF value"
    - "Not an issue — repo value is correct"
```

### Step 2D: Evidence extraction (for issues needing research)

For issues where the user chose "Research first" or "Needs research": extract evidence from the review report. Spawn one per issue — they run **in parallel**:

```
subagent_type: "general-purpose"
name: "evidence-extractor-{N}"
run_in_background: true

"Extract evidence for a specific issue from the review report.

ISSUE: {description} in {file}
QUESTION: {what needs to be determined}

READ (check both, use whichever exists):
- {RUN_ROOT}/{PREFIX}-review-full-report.md (local review-program output)
- PR comments via: gh pr view {PR_NUMBER} --comments

Find the section(s) related to this issue and extract:
- The regulation citation and what it says
- The code-path verification result (if any)
- The visual verification result (if any)
- The reviewer's assessment

Write to {RUN_ROOT}/{PREFIX}-fix-pr-research-{N}.md (max 15 lines):
- Source: {regulation citation}
- Evidence from review: {what the report found}
- Verdict: CONFIRMED BUG / BY DESIGN / AMBIGUOUS
- Recommended action: fix (describe how) / leave as-is / needs human judgment"
```

After all extractors complete, read each `{RUN_ROOT}/{PREFIX}-fix-pr-research-{N}.md` and re-ask:

```
AskUserQuestion:
  Question: "Research result for: {issue description}"
  Description: "{Brief summary of findings — verdict and evidence}"
  Options:
    - "{Recommended action from research}" (recommended)
    - "{Alternative action}"
    - "Skip — I'll handle this manually"
```

### Step 2E: Write fix plan to disk

After all decisions are made, write `{RUN_ROOT}/{PREFIX}-fix-pr-plan.md`:

```markdown
## Fix Plan for PR #{PR_NUMBER}

### Confirmed Fixes
- [2A] {file}: Missing reference — rules-engineer
- [2B] {file}: Regulatory mismatch — rules-engineer
- [2B] {file}: Hard-coded value — rules-engineer (depends on 2A)
- [2C] {variable}: Missing boundary test — edge-case-generator

### Skipped
- {file}: Regulatory mismatch — user marked "by design"
- {file}: Hard-coded value — already fixed (POSSIBLY-FIXED confirmed)

### Fix Order
1. Parameter fixes: {count} issues → rules-engineer
2. Variable fixes: {count} issues → rules-engineer (after parameters)
3. Test fixes: {count} issues → edge-case-generator (after variables)
4. CI fixes: run after all above → ci-fixer
```

---

## Phase 3: Apply Fixes

**Only fix issues listed in `{RUN_ROOT}/{PREFIX}-fix-pr-plan.md`.** Skip anything excluded.

**Fix in dependency order**: Parameters → Variables → Tests → CI.

### Step 3A: Parameter Fixes

Skip if no parameter issues in the fix plan.

```
subagent_type: "complete:country-models:rules-engineer"
name: "fix-parameters"

"Fix parameter issues for PR #{PR_NUMBER}.
Read the fix plan at {RUN_ROOT}/{PREFIX}-fix-pr-plan.md — fix ONLY the issues assigned to you.

Load skills: /policyengine-parameter-patterns.

For reference issues:
- Add detailed section numbers (e.g., 42 USC 8624(b)(2)(B))
- Add #page=XX for PDF links (file page, NOT printed page)

For new parameters:
- Create in proper hierarchy (federal vs state)
- Include references for every new parameter value

DO NOT commit — Phase 4 handles all commits."
```

### Step 3B: Variable Fixes

Skip if no variable issues in the fix plan. **Depends on Step 3A** — wait for parameter fixes to complete if new parameters were created.

```
subagent_type: "complete:country-models:rules-engineer"
name: "fix-variables"

"Fix variable issues for PR #{PR_NUMBER}.
Read the fix plan at {RUN_ROOT}/{PREFIX}-fix-pr-plan.md — fix ONLY the issues assigned to you.

Load skills: /policyengine-variable-patterns, /policyengine-code-style.

If Step 3A created new parameters, read them from disk before refactoring.
Use proper parameter access patterns.

DO NOT commit — Phase 4 handles all commits."
```

### Step 3C: Test Fixes

Skip if no test issues in the fix plan. **Depends on Step 3B** — tests should reflect the fixed variable behavior.

```
subagent_type: "complete:country-models:edge-case-generator"
name: "fix-tests"

"Add missing tests for PR #{PR_NUMBER}.
Read the fix plan at {RUN_ROOT}/{PREFIX}-fix-pr-plan.md — fix ONLY the issues assigned to you.

Load skills: /policyengine-testing-patterns.

Always append new cases at the bottom of existing test files.
Never insert in the middle — this renumbers existing cases and creates noisy diffs.

DO NOT commit — Phase 4 handles all commits."
```

### Step 3D: CI Fixes

Run **after Steps 3A-3C** to catch failures from the fixes themselves.

```
subagent_type: "complete:country-models:ci-fixer"
name: "fix-ci"

"Run tests for PR #{PR_NUMBER} and fix any failures.
Load skills: /policyengine-testing-patterns, /policyengine-variable-patterns.

Build a test manifest from the files changed by this PR and the files touched in Steps
3A-3C. Then use this funnel:
1. Run all exact affected test files together without `-v`.
2. Classify all failures before editing; batch independent mechanical fixes.
3. Rerun only failed files/cases, using `-n <case>` when available.
4. Use `-v -d 2` only for an unresolved numeric/formula failure; deepen the trace only
   if depth 2 does not expose the bad intermediate variable.
5. After targeted tests pass, run the program directory once without `-v`.
6. If `--full-validation`, run the broader package suite once. Never repeat it inside
   the repair loop.

Use at most 3 targeted repair cycles. Never change a policy expectation merely to make a
test pass; resolve semantic disagreements against the cited evidence and approved fix
plan. Do not run `make format` here; Phase 4 formats once.

Write SHORT result to {RUN_ROOT}/{PREFIX}-fix-pr-ci-result.md (max 15 lines):
- Tests: PASS / FAIL (N failures)
- Fixes applied: {list}
- Commands/test counts: {summary}
- Targeted reruns: {count}
- Elapsed: {duration}"
```

Read ONLY `{RUN_ROOT}/{PREFIX}-fix-pr-ci-result.md` (max 15 lines).

**If ci-fixer fails after 3 iterations**: Stop and report to user.

---

## Phase 4: Verify & Push

### Step 4A: Quick Audit

Spawn a verification agent to check the fixes didn't introduce new problems:

```
subagent_type: "complete:country-models:implementation-validator"
name: "fix-verifier"

"Verify fixes for PR #{PR_NUMBER} were applied correctly.
Read the fix plan at {RUN_ROOT}/{PREFIX}-fix-pr-plan.md.
Load skills: /policyengine-variable-patterns, /policyengine-parameter-patterns,
  /policyengine-code-style.

Check:
- Each issue in the fix plan was actually addressed
- No new hard-coded values introduced
- All new parameters have references
- Patterns are correct (adds, add(), entity levels)

Write SHORT report to {RUN_ROOT}/{PREFIX}-fix-pr-verification.md (max 15 lines):
- Issues fixed: {count} / {total in plan}
- New issues introduced: {count, if any}
- Verdict: CLEAN / HAS-ISSUES"
```

Read ONLY `{RUN_ROOT}/{PREFIX}-fix-pr-verification.md` (max 15 lines).

**If HAS-ISSUES**: Route each finding to the owning parameter, variable, or test fixer,
then rerun the verifier. If it still fails after one targeted round, stop and report the
blocked gate; do not push known-bad fixes.

### Step 4B: Cleanup & Push

**Local-source safety** (always, regardless of local/push mode):

```bash
# sources/ contains local research. Never delete or stage it.
git status --short -- sources/working_references.md
```

**If user chose local-only mode**: Run `make format`, then skip to Phase 5.

**If user chose to push to GitHub**:

```
subagent_type: "complete:country-models:pr-pusher"
name: "fix-pusher"

"Push fixes for PR #{PR_NUMBER}:
- Run make format once
- If formatting changes executable files, rerun only their affected tests
- git add only files in the approved fix plan plus formatting/changelog changes
- Ensure sources/working_references.md and other local research are NOT staged
- git commit -m 'Fix issues from review: {brief summary of what was fixed}'
- Resolve the actual base branch with gh pr view, fetch it from upstream, and rebase the
  new commit on upstream/{base}. Never guess main/master. If the rebase changes program
  files or has conflicts, rerun the targeted test manifest after resolving.
- git push"
```

### Step 4C: Post Summary Comment

**If user chose local-only mode**: Skip.

**If user chose to push to GitHub**: Spawn an agent to write the comment based on actual fixes applied:

```
subagent_type: "general-purpose"
name: "comment-writer"

"Write a GitHub PR comment summarizing fixes applied to PR #{PR_NUMBER}.

READ:
- {RUN_ROOT}/{PREFIX}-fix-pr-plan.md (what was planned)
- {RUN_ROOT}/{PREFIX}-fix-pr-ci-result.md (test results)
- {RUN_ROOT}/{PREFIX}-fix-pr-verification.md (verification results)

Write {RUN_ROOT}/{PREFIX}-fix-pr-comment.md:

## Fixes Applied

### Critical Issues Fixed
- {issue}: {how it was fixed}

### Should-Address Issues Fixed
- {issue}: {how it was fixed}

### Skipped (by user decision)
- {issue}: {reason}

### Verification
- Tests: {pass/fail}
- Validator: {clean/issues}
- Format: done

Only include sections that have entries."
```

Then post:

```bash
gh pr comment $PR_NUMBER --body-file {RUN_ROOT}/{PREFIX}-fix-pr-comment.md
```

---

## Phase 5: Summary

Present to user:

```
## Fix Summary for PR #{PR_NUMBER}

- Issues fixed: {X} / {total found}
- Skipped: {Y} (by design: {A}, already fixed: {B}, user skipped: {C})
- Tests: {pass/fail}
- Pushed: {yes/no}
- Comment posted: {yes/no}
```

---

## Issue Type → Agent Mapping

| Issue Type | Step | Agent (`complete:country-models:` prefix) |
|------------|------|-------|
| Missing reference | 3A | `rules-engineer` |
| Bad reference format | 3A | `rules-engineer` |
| Hard-coded value (create param) | 3A | `rules-engineer` |
| Hard-coded value (use param) | 3B | `rules-engineer` |
| Regulatory mismatch | 3B | `rules-engineer` |
| Pattern violation (adds, add()) | 3B | `rules-engineer` |
| Naming issue | 3B | `rules-engineer` |
| Missing test | 3C | `edge-case-generator` |
| CI failure | 3D | `ci-fixer` |
| Format issue | 4B | `pr-pusher` |

---

## Handoff Table

| File | Written By | Read By | Size |
|------|-----------|---------|------|
| `{RUN_ROOT}/{PREFIX}-fix-pr-diff.txt` | Main Claude (gh pr diff) | context-gatherer | Full |
| `{RUN_ROOT}/{PREFIX}-fix-pr-issues.md` | context-gatherer | Main Claude | Short (50 lines) |
| `{RUN_ROOT}/{PREFIX}-fix-pr-plan.md` | Main Claude | all fix agents, verifier | Short |
| `{RUN_ROOT}/{PREFIX}-fix-pr-research-{N}.md` | evidence-extractor-{N} | Main Claude | Short (15 lines) |
| `{RUN_ROOT}/{PREFIX}-fix-pr-ci-result.md` | ci-fixer | Main Claude, comment-writer | Short (15 lines) |
| `{RUN_ROOT}/{PREFIX}-fix-pr-verification.md` | fix-verifier | Main Claude, comment-writer | Short (15 lines) |
| `{RUN_ROOT}/{PREFIX}-fix-pr-comment.md` | comment-writer | gh pr comment --body-file | Full |
| `{RUN_ROOT}/{PREFIX}-fix-pr-run-state.md` | orchestrator | orchestrator | Short (30 lines) |
| `{RUN_ROOT}/{PREFIX}-review-full-report.md` | /review-program (prior run) | context-gatherer, evidence-extractor | Full |

**Main Claude reads ONLY "Short" files. Never read "Full" files.**

---

## Error Handling

| Category | Example | Action |
|----------|---------|--------|
| **Recoverable** | Test failure, lint error | ci-fixer handles automatically |
| **Agent failure** | fix-variables crashes | Report which agent failed, ask user |
| **CI stuck** | ci-fixer fails 3 iterations | Stop, report remaining failures to user |
| **No issues found** | Empty issues file | Report "nothing to fix" and exit |
| **No review data** | No local report AND no PR comments | Report "no review findings found — run /review-program first?" |

---

## Pre-Flight Checklist

Before starting:
- [ ] I will determine which PR FIRST, then ask posting mode
- [ ] I will preserve matching artifacts with --resume; otherwise clean only this PREFIX
- [ ] I will delegate ALL context gathering to agents
- [ ] I will read ONLY short summary files
- [ ] I will present issues to user via AskUserQuestion before fixing
- [ ] I will write the fix plan to disk before spawning fix agents
- [ ] I will invoke agents for ALL fixes — never use Edit/Write directly
- [ ] I will fix in dependency order (params → vars → tests → CI)
- [ ] I will verify fixes with implementation-validator after applying
- [ ] I will generate the PR comment from actual results, not a template
- [ ] I will record test counts, reruns, and elapsed time in the run-state file

Start by parsing arguments (Phase 0), then proceed through all phases.
