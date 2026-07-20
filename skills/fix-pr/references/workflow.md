# Workflow: fix-pr (canonical)

This file is the single canonical definition of the fix-pr workflow. The Claude Code
command (`/fix-pr`) and the Codex skill (`$fix-pr`) are thin launchers over this
document: each parses arguments, maps the roles below to its native delegation
mechanism, and then follows these phases exactly. This document is surface-neutral —
"ask the user" means a blocking question on the active surface; "delegate role X" means
running that role's task through the surface's delegation mechanism (or executing it
directly, in order, when delegation is unavailable).

## Purpose

Apply fixes to a PolicyEngine PR based on review-program findings, GitHub review
comments, CI failures, or local review reports. Fixes are user-approved before any edit
and verified before any push.

## Orchestration contract

**The coordinator protects its context window.** It parses arguments, runs small
structured `gh` commands, saves the diff to disk unread, presents checkpoints to the
user, writes the fix plan, and delegates everything else. It reads ONLY the short files
in the handoff table; it never reads the diff, code files, or full review reports, and
it never edits code directly — fix roles make all code changes.

**Consent gates (hard rules).**

- No edit happens before the fix plan file exists and reflects the user's choices.
- Only issues listed in the fix plan are fixed; everything else is skipped.
- Nothing is pushed while a verification gate is red.

## Roles

| Role | Responsibility | Writes | Skills to load |
|---|---|---|---|
| context-gatherer | Merge local review files, PR comments/reviews, freshness, CI status into a classified issue inventory | `{RUN_ROOT}/{PREFIX}-fix-pr-issues.md` | — |
| evidence-extractor-{N} | Extract review-report evidence for one research-needed issue | `{RUN_ROOT}/{PREFIX}-fix-pr-research-{N}.md` | — |
| fix-parameters | Fix parameter, reference, and legal-value issues from the plan | parameter files | policyengine-model-development (references/parameters.md) |
| fix-variables | Fix formula, naming, entity, aggregation, and hard-coded-value issues from the plan | variable files | policyengine-model-development (references/variables.md, references/style.md) |
| fix-tests | Add or repair tests from the plan | test files | policyengine-model-development (references/tests.md) |
| fix-code | Fix ALL planned issues in a non-country-model PR (API/frontend/app) — replaces the three roles above | source and test files named in the plan | — |
| fix-ci | Run the targeted test funnel and fix evidenced failures | `{RUN_ROOT}/{PREFIX}-fix-pr-ci-result.md` | policyengine-model-development (references/tests.md, references/variables.md) — country-model PRs only |
| fix-verifier | Verify every fix-plan item was applied; catch new issues | `{RUN_ROOT}/{PREFIX}-fix-pr-verification.md` | policyengine-model-development (references/variables.md, references/parameters.md, references/style.md) |
| fix-pusher | Format once, stage intended files only, commit, rebase on the actual base, push | commit/push | policyengine-standards |
| comment-writer | Summarize actual fixes for GitHub from result files | `{RUN_ROOT}/{PREFIX}-fix-pr-comment.md` | — |

Ownership: fix-parameters owns parameter YAMLs named in the plan; fix-variables owns
variable Python files named in the plan; fix-tests owns test files named in the plan;
fix-code (non-country-model PRs) owns every file named in the plan;
fix-ci may edit files only to resolve failures arising from the planned fixes;
fix-pusher owns formatting, staging, commit, rebase, and push — and must never delete or
stage local research under `sources/`. No role commits except fix-pusher.

## Arguments

- `PR_ARG`: PR number or search text (optional — prompts if omitted)
- `--local`: apply fixes locally only; skip pushing and GitHub posting
- `--resume`: reuse valid context, plan, and evidence artifacts from an interrupted run
- `--full-validation`: run a broader package suite once after targeted PR tests pass

## Phase 0: Worktree namespace, PR, and mode

Derive the worktree-safe runtime root before resolving the PR:

```bash
WORKTREE_ROOT=$(git rev-parse --show-toplevel)
WORKTREE_ID=$(printf '%s' "$WORKTREE_ROOT" | git hash-object --stdin | cut -c1-12)
RUN_ROOT="/tmp/policyengine-command-runs/$WORKTREE_ID"
mkdir -p "$RUN_ROOT"
```

The absolute worktree root — not the shared Git common directory or the branch name — is
the isolation boundary. Pass concrete `RUN_ROOT`, `WORKTREE_ID`, and `PREFIX` values to
every delegate; no delegate may use process-global `/tmp/fix-pr-*` or
`/tmp/{PREFIX}-...` paths.

Resolve the PR: numeric argument → use directly; search text → resolve with
`gh pr list --search "$PR_ARG" --json number,title --jq '.[0].number'`; omitted → ask
the user for a PR number or title. If a search matches nothing, report that and re-ask.

**Worktree guard before checkout.** Inspect `git worktree list --porcelain` and the
PR's `headRefName`:

- If the PR branch is the current branch, continue in this worktree.
- If it is checked out in another worktree, STOP and report that worktree path. Never
  use `--ignore-other-worktrees`, never mutate another worktree's checkout.
- Otherwise `gh pr checkout $PR_NUMBER` in the current worktree.

All edits, tests, staging, commits, and pushes run from `WORKTREE_ROOT`. Capture the
remote identities needed for a guarded push **before any edits**:

```bash
gh pr view "$PR_NUMBER" \
  --json url,baseRefName,headRefName,headRefOid,headRepository,headRepositoryOwner
```

Derive `BASE_REPO_URL` from `PR_URL%/pull/*` (and `BASE_REPO` — its `owner/name`
path — for repo-scoped `gh` calls), and derive `HEAD_REPO`, `HEAD_REPO_URL`,
`HEAD_BRANCH`, and `EXPECTED_HEAD_SHA` from that response. In push mode,
verify the authenticated user has push permission on `HEAD_REPO`; otherwise stop before
editing. Never substitute the base repository or a convenient named remote for the PR's
actual head repository.

After checkout (or branch match), derive the prefix and initialize state:

```bash
PREFIX=$(git branch --show-current | tr '/' '-')
PREFIX=${PREFIX:-fix-pr}
if [ "$RESUME" != "true" ]; then
  rm -f "$RUN_ROOT/${PREFIX}-fix-pr-"*.md "$RUN_ROOT/${PREFIX}-fix-pr-diff.txt"
fi
```

Record `WORKTREE_ROOT`, `WORKTREE_ID`, PR/head SHA, arguments, input hashes, completed
phases, artifact paths, test commands, and elapsed time in
`{RUN_ROOT}/{PREFIX}-fix-pr-run-state.md`. A resume may reuse an artifact only when its
PR number/head SHA and input hashes still match; invalidate dependents when the diff or
selected fix scope changed; refuse artifacts recorded by another worktree.

**Posting mode**: if `--local`, run local-only. Otherwise ask the user whether to push
changes and post a summary to GitHub when complete (default: push and post).

## Phase 1: Gather context

Run small structured commands only:

```bash
gh pr view $PR_NUMBER --json title,body,author,baseRefName,headRefName
gh pr checks $PR_NUMBER
gh pr diff $PR_NUMBER > {RUN_ROOT}/{PREFIX}-fix-pr-diff.txt
```

Check for a local review-program report from a prior run. A prior review may have used
a different artifact prefix — review-program derives its prefix from the branch checked
out when it ran, or from an explicit `--prefix` — so discover candidates by glob and
select by head SHA:

```bash
LOCAL_REVIEW=false
for R in "$RUN_ROOT"/*-review-full-report.md; do
  [ -e "$R" ] || continue
  if grep -q "Reviewed head SHA.*$EXPECTED_HEAD_SHA" "$R"; then
    LOCAL_REVIEW=true; LOCAL_REPORT="$R"; break
  fi
done
```

Only a report whose recorded `Reviewed head SHA` matches the current PR head is current;
treat any other report as historical context and use current review comments and the
diff as authoritative. Pass the concrete `LOCAL_REPORT` path (when set) to the
context-gatherer and evidence extractors.

**Delegate context gathering** (role: context-gatherer). It reads the saved diff, the
local review files if present, and GitHub review data via:

```bash
gh pr view $PR_NUMBER --json reviews --jq '.reviews[] | {author: .author.login, state: .state, submittedAt: .submittedAt, body: .body}'
gh pr view $PR_NUMBER --json comments --jq '.comments[] | {author: .author.login, createdAt: .createdAt, body: .body}'
gh pr view $PR_NUMBER --json commits --jq '.commits[-1].committedDate'
# Inline review comments — the usual carrier of actionable feedback; NOT included in
# either query above (--json comments is issue comments, --json reviews is summaries)
gh api "repos/$BASE_REPO/pulls/$PR_NUMBER/comments" --paginate \
  --jq '.[] | {author: .user.login, path: .path, line: .line, createdAt: .created_at, body: .body}'
# Thread resolution state — only exposed via GraphQL reviewThreads
gh api graphql -F owner="${BASE_REPO%/*}" -F repo="${BASE_REPO#*/}" -F pr="$PR_NUMBER" -f query='
  query($owner: String!, $repo: String!, $pr: Int!) {
    repository(owner: $owner, name: $repo) { pullRequest(number: $pr) {
      reviewThreads(first: 100) { nodes {
        isResolved isOutdated path
        comments(first: 1) { nodes { body author { login } createdAt } } } } } } }'
```

**Comment freshness** — classify each comment/review against the last commit timestamp:

- posted AFTER the last commit → CURRENT (valid)
- posted BEFORE the last commit: thread resolved on GitHub (`isResolved` from the
  reviewThreads query) → RESOLVED (skip); the
  flagged file was modified after the comment (check
  `git log --oneline --after='{comment_date}' -- '{file_path}'`) → POSSIBLY-FIXED;
  otherwise → STALE-BUT-OPEN (still valid, flag for the user)
- ignore reviews with state DISMISSED
- include ALL comments from all authors and all three sources (review summaries, issue
  comments, inline review comments) — a reviewer may leave several separate issues

Merge local-review findings and valid PR comments (deduplicate, preferring the more
detailed version) and classify each issue:

- CLEAR: obviously fixable (missing reference, formatting, hard-coded value)
- AMBIGUOUS: might be by design (regulatory mismatch, unusual pattern choice)
- RESEARCH-NEEDED: requires review-report evidence before deciding

Write `{RUN_ROOT}/{PREFIX}-fix-pr-issues.md` (≤50 lines): source summary (local report
found?; comment counts by freshness class), the PR's repository type — `country-model`
(parameter YAML / model variables / policy tests dominate the diff) or
`api/frontend/app` (everything else) — issues grouped Critical / Should Address /
Suggestions with `[CLASSIFICATION]` and `[POSSIBLY-FIXED]` tags and sources, and a
totals summary. The coordinator reads only this file.

If there are no issues at all, report "nothing to fix" and stop. If there is no local
report AND no PR comments, report "no review findings found — run the review-program
workflow first?" and stop.

## Phase 2: Fix plan (USER CHECKPOINT)

Present a brief overview (critical/should/suggestion/possibly-fixed counts), then walk
through decisions:

1. **Fix scope** — ask: Critical only (recommended when criticals exist) / Critical +
   Should Address (recommended otherwise) / All including Suggestions / review each
   issue individually.
2. **Possibly-fixed issues** in scope — ask each: already fixed, skip (recommended) /
   still an issue, fix / not sure, check it.
3. **Per-issue review** (only if chosen) — present each issue with context; options vary
   by classification: CLEAR → fix / skip; AMBIGUOUS → fix / by design / needs research;
   RESEARCH-NEEDED → research first / fix with the suggested value / not an issue.
4. **Evidence extraction** — for issues marked research-first, delegate one
   evidence-extractor-{N} per issue, all concurrently. Each reads the local review
   report and/or PR comments, extracts the regulation citation, code-path and visual
   verification results, and the reviewer's assessment, and writes
   `{RUN_ROOT}/{PREFIX}-fix-pr-research-{N}.md` (≤15 lines) ending in a verdict
   (CONFIRMED BUG / BY DESIGN / AMBIGUOUS) and recommended action. Read each short
   result and re-ask the user, offering: the recommended action from the research
   (first, marked recommended), the alternative action when the evidence supports one,
   and `Skip — I'll handle this manually`.
5. **Write the fix plan** to `{RUN_ROOT}/{PREFIX}-fix-pr-plan.md`: confirmed fixes with
   assigned roles, skipped issues with reasons, and the fix order
   (parameters → variables → tests → CI; fix-code → CI for non-country-model PRs). Do
   not edit before this file exists.

## Phase 3: Apply fixes

Fix ONLY issues listed in the plan, in dependency order. Skip any step with no assigned
issues.

**Repository-type dispatch.** The role split and skill loads below apply to
country-model PRs. When the issue inventory classifies the PR as `api/frontend/app`,
assign every planned fix to a single fix-code role (steps 1-3 collapse into one; it
loads no model skills and follows the target repository's own conventions), and fix-ci
replaces the policyengine-core funnel with the repository's native test command —
discovered from its CI workflow, Makefile, or package.json — under the same cycle
budget, classification-before-editing, and no-expectation-changes rules.

1. **Parameter fixes** (role: fix-parameters). References get detailed subsections
   (e.g., 42 USC 8624(b)(2)(B)) and `#page=XX` file-page anchors for PDF links; new
   parameters go in the proper federal/state hierarchy with a reference for every value.
2. **Variable fixes** (role: fix-variables) — after parameters when new parameters were
   created; read them from disk and use proper parameter-access patterns.
3. **Test fixes** (role: fix-tests) — after variables. Append new scenarios at the
   bottom of existing test files; never insert in the middle (it renumbers cases and
   creates noisy diffs).
4. **CI fixes** (role: fix-ci) — after all of the above. Build an exact test manifest
   from the PR diff plus the files touched in steps 1-3, then run the funnel:
   1. run all affected test files together without `-v`
      (`policyengine-core test <files> -c policyengine_us`; adapt the package for
      UK/Canada PRs)
   2. classify every failure before editing; batch independent mechanical fixes
   3. rerun only failed files/cases, using `-n <case>` when available
   4. add `-v -d 2` only for an unresolved numeric/formula failure; deepen the trace
      only if depth 2 does not expose the bad intermediate variable
   5. after targeted tests pass, run the program directory once without `-v`
   6. with `--full-validation`, run the broader package suite once — never inside the
      repair loop

   At most 3 targeted repair cycles. Never change a policy expectation merely to make a
   test pass — resolve semantic disagreements against the cited evidence and the
   approved plan. Do not format here; Phase 4 formats once. Write
   `{RUN_ROOT}/{PREFIX}-fix-pr-ci-result.md` (≤15 lines): PASS/FAIL with counts,
   fixes applied, commands/test counts, targeted reruns, elapsed time. If still failing
   after 3 cycles, stop and report to the user.

## Phase 4: Verify and push

**Verification gate** (role: fix-verifier). Check every plan item was actually
addressed; no new hard-coded values; new parameters have references; patterns correct
(`adds`, `add()`, entity levels). Write `{RUN_ROOT}/{PREFIX}-fix-pr-verification.md`
(≤15 lines): fixed count / plan total, new issues, verdict CLEAN or HAS-ISSUES.

If HAS-ISSUES: route each finding back to its owning fix role, then rerun the verifier.
If it still fails after one targeted round, STOP and report the blocked gate — never
push known-bad fixes.

**Local research safety** (always): `sources/` contains local research — never delete
or stage it (`git status --short -- sources/working_references.md` to confirm).

**Local-only mode**: run `make format`, then skip to Phase 5.

**Push mode** (role: fix-pusher):

- run `make format` once; if formatting changed executable files, rerun only their
  affected tests
- stage ONLY files in the approved fix plan plus formatting/changelog changes; confirm
  `sources/` is not staged
- commit: `Fix issues from review: {brief summary}`
- resolve the PR's actual base branch with `gh pr view`, fetch it from the PR's base
  repository by URL (`PR_URL%/pull/*` — not a named remote, which may be a fork), and
  rebase the commit on it — never guess main/master; if the rebase changes program files
  or hits conflicts, rerun the targeted test manifest after resolving
- query `HEAD_REPO_URL` for `refs/heads/HEAD_BRANCH`; if its SHA no longer equals the
  pre-edit `EXPECTED_HEAD_SHA`, stop as stale and do not overwrite the newer remote work
- push `HEAD` explicitly to the PR's head repository/branch with
  `--force-with-lease=refs/heads/HEAD_BRANCH:EXPECTED_HEAD_SHA`; never use a plain
  `git push`, an implicit upstream, or `origin` after rebasing

Then delegate the summary comment (role: comment-writer): read the plan, CI result, and
verification files; write `{RUN_ROOT}/{PREFIX}-fix-pr-comment.md` with sections (only
those with entries) — Critical fixed, Should-Address fixed, Skipped (by user decision),
Verification (tests / validator / format). Post it:

```bash
gh pr comment $PR_NUMBER --body-file {RUN_ROOT}/{PREFIX}-fix-pr-comment.md
```

## Phase 5: Summary

Present: issues fixed X / total found; skipped (by design / already fixed / user
skipped); tests pass/fail; pushed yes/no; comment posted yes/no. Record test counts,
reruns, and elapsed time in the run-state file.

## Issue type → role

| Issue type | Phase 3 step | Role |
|---|---|---|
| Missing or malformed reference | 1 | fix-parameters |
| Hard-coded value (create the parameter) | 1 | fix-parameters |
| Hard-coded value (use the parameter) | 2 | fix-variables |
| Regulatory mismatch | 2 | fix-variables |
| Pattern violation (`adds`, `add()`) / naming / entity | 2 | fix-variables |
| Missing test | 3 | fix-tests |
| CI failure | 4 | fix-ci |
| Format issue | Phase 4 | fix-pusher |
| Any issue in a non-country-model PR | 1-3 | fix-code |

## Handoff artifacts

| File | Written by | Read by | Size |
|---|---|---|---|
| `{RUN_ROOT}/{PREFIX}-fix-pr-diff.txt` | coordinator (`gh pr diff`) | context-gatherer | Full |
| `{RUN_ROOT}/{PREFIX}-fix-pr-issues.md` | context-gatherer | coordinator | ≤50 lines |
| `{RUN_ROOT}/{PREFIX}-fix-pr-plan.md` | coordinator | all fix roles, verifier | Short |
| `{RUN_ROOT}/{PREFIX}-fix-pr-research-{N}.md` | evidence-extractor-{N} | coordinator | ≤15 lines |
| `{RUN_ROOT}/{PREFIX}-fix-pr-ci-result.md` | fix-ci | coordinator, comment-writer | ≤15 lines |
| `{RUN_ROOT}/{PREFIX}-fix-pr-verification.md` | fix-verifier | coordinator, comment-writer | ≤15 lines |
| `{RUN_ROOT}/{PREFIX}-fix-pr-comment.md` | comment-writer | `gh pr comment --body-file` | Full |
| `{RUN_ROOT}/{PREFIX}-fix-pr-run-state.md` | coordinator | coordinator | ≤30 lines |
| `{RUN_ROOT}/*-review-full-report.md` (head-SHA-matched `LOCAL_REPORT`) | prior review-program run | context-gatherer, evidence-extractor | Full |

The coordinator reads only the Short files — never the Full ones.

## Error handling

| Situation | Action |
|---|---|
| Test failure, lint error | fix-ci handles within its cycle budget |
| A fix role crashes | report which role failed; ask the user |
| fix-ci still failing after 3 cycles | stop; report remaining failures |
| Verification gate red after one retry round | stop; do not push |
| Empty issue inventory | report "nothing to fix" and exit |
| No review data at all | suggest running the review-program workflow first |
