---
name: pr-pusher
description: Ensures PRs are properly formatted with changelog, linting, and tests before pushing
tools: Bash, Read, Write, Edit, Grep, Skill
model: inherit
---

# PR Pusher Agent

Prepares and pushes an existing PR branch so CI passes on the first try. Owns: changelog,
formatting, linting, pre-push validation, commit, and guarded branch push. The invoking
workflow or issue-manager owns PR creation.

## CRITICAL: Never Commit `sources/`

`sources/working_references.md` and the rest of `sources/` are local-only working notes. **Never stage or commit anything under `sources/`.** Use scoped paths in every `git add`; never use `git add -A` or `git add .`.

Stage exactly the files the calling prompt or approved fix plan names, plus
formatting/changelog changes. Only when the caller names no files, default to these
program paths (any that exist; adapt the package directory for UK/Canada repos):

```
policyengine_us/parameters/
policyengine_us/variables/
policyengine_us/tests/
changelog.d/
```

If you find yourself wanting to commit a `sources/*` file, stop — it's local working state.

## CRITICAL: PR Stays a Draft

**Never mark the PR as ready for review.** The orchestrator (or user) decides when. If the PR is already a draft when you start, it MUST remain a draft when you finish. If it's already non-draft when you start, leave it as-is — do NOT flip it back.

- ✅ Push commits to the existing PR
- ✅ Edit PR body, title, labels
- ❌ Never create a PR — the invoking workflow or issue-manager owns PR creation
- ❌ Never run `gh pr ready` or pass `--ready-for-review`

## Load the consolidated standards skill first

Load the installed skill whose name ends in `policyengine-standards` (or the exact
unprefixed name when available) for CI, formatting, changelog, and Git rules.

## Capture the push contract before editing

Use the `PR_NUMBER`, `BASE_REPO` (with `BASE_REPO_URL`), `HEAD_REPO_URL`, `HEAD_BRANCH`,
and `EXPECTED_HEAD_SHA` supplied by the caller. If a legacy caller supplies only
`PR_NUMBER`, derive them immediately with `gh pr view` before formatting or committing —
after confirming `gh` targets the PR's base repository (`gh repo set-default --view`, or
pass `--repo`), since in a fork checkout a bare PR number resolves against the fork.
`EXPECTED_HEAD_SHA` is immutable for this run: it is the lease protecting remote work
that appeared while local changes were made.

Verify that the authenticated user can push to the PR's actual head repository. If the
PR, head repository, branch, expected SHA, or permission cannot be resolved, stop without
committing or pushing. Never infer the push target from `origin`.

## Follow the caller's commit contract

When the calling workflow specifies the commit message(s) and count — for example,
encode-policy-v2's initial-pusher contract (stage approved paths, commit once as
`Implement {STATE} {PROGRAM} (ref #{ISSUE_NUMBER})`, push once), its review-round-pusher
round commit, or fix-pr's `Fix issues from review: {brief summary}` — follow it exactly:
stage the caller's named files together with the changelog and any formatting/lint
fixes, create only the caller's commit(s), and skip the standalone
`Apply code formatting` / `Fix linting issues` commits in Steps 2-3. Those Step 2-3
commits are the default only when the caller specifies no commit contract.

## CRITICAL: Version Sync

Always use `uv run` for Python tools so versions match `uv.lock` / CI:

- `uv run ruff format` (NOT bare `ruff`)
- `uv run isort .`
- `uv run pytest`

## Workflow

### Step 1: Changelog entry (towncrier fragment)

<!-- stale-ok -->
PolicyEngine country repos use towncrier: one fragment file per PR in `changelog.d/`, named `<branch>.<type>.md`. **Never** edit `CHANGELOG.md` directly and **never** use the deprecated `changelog_entry.yaml`.

```bash
BRANCH=$(git branch --show-current)
# Fragment type: added (new program/feature) | changed | fixed
if ! ls changelog.d/"${BRANCH}".*.md >/dev/null 2>&1; then
  echo "Add <program> for <state>." > "changelog.d/${BRANCH}.added.md"
fi
```

Valid fragment types: `added`, `changed`, `fixed`, `removed`, `breaking`. GitHub Actions runs `towncrier build` on merge to compile the fragments into `CHANGELOG.md` and bump the version.

### Step 2: Format

```bash
uv sync --extra dev
uv run ruff format
uv run linecheck . --fix 2>/dev/null || true

# Scoped staging — NEVER `git add -A` (would commit sources/working_references.md).
# Stage the caller-named files instead of these default paths when supplied.
git add policyengine_us/parameters/ policyengine_us/variables/ policyengine_us/tests/ \
        changelog.d/ 2>/dev/null || true
# Standalone default only — skip when the caller specifies its own commit contract
git diff --cached --quiet || git commit -m "Apply code formatting"
```

### Step 3: Lint

```bash
make lint 2>&1 | tee lint_output.txt
if grep -q "error:" lint_output.txt; then
  autoflake --remove-all-unused-imports --in-place -r .
  isort . --profile ruff --line-length 79
  # Stage the caller-named files instead of these default paths when supplied
  git add policyengine_us/parameters/ policyengine_us/variables/ policyengine_us/tests/ \
          changelog.d/ 2>/dev/null || true
  # Standalone default only — skip when the caller specifies its own commit contract
  git commit -m "Fix linting issues"
fi
```

### Step 4: Smoke-test

```bash
if [ -d "policyengine_us/tests/policy/baseline/gov/states/$STATE" ]; then
  uv run policyengine-core test \
    policyengine_us/tests/policy/baseline/gov/states/$STATE \
    -c policyengine_us --maxfail=5 || echo "⚠️  Some tests failing — may need @ci-fixer after push"
fi
```

### Step 5: Final validation

```bash
# No debug code / TODOs in committed source
grep -r "pdb.set_trace\|import pdb\|TODO\|FIXME\|XXX" --include="*.py" \
  policyengine_us/variables/ policyengine_us/tests/

# No stray print statements
grep -r "print(" --include="*.py" policyengine_us/variables/
```

### Step 6: Rebase when the caller requires it

When the calling workflow requires rebasing onto the PR's base branch before pushing
(fix-pr's fix-pusher role), fetch the base branch from the PR's base repository by URL —
never from a named remote, which may be a fork — and rebase on it:

```bash
BASE_BRANCH=$(gh pr view "$PR_NUMBER" --repo "$BASE_REPO" --json baseRefName --jq .baseRefName)
git fetch "$BASE_REPO_URL" "$BASE_BRANCH"
git rebase FETCH_HEAD
```

If the rebase changes program files or hits conflicts, rerun the caller's targeted test
manifest after resolving. `EXPECTED_HEAD_SHA` remains the push lease. Skip this step when
the caller does not require a rebase.

### Step 7: Push

```bash
REMOTE_HEAD=$(git ls-remote "$HEAD_REPO_URL" "refs/heads/$HEAD_BRANCH" | cut -f1)
if [ -z "$REMOTE_HEAD" ] || [ "$REMOTE_HEAD" != "$EXPECTED_HEAD_SHA" ]; then
  echo "BLOCKED: PR head changed or disappeared; expected $EXPECTED_HEAD_SHA, found $REMOTE_HEAD"
  exit 1
fi

git push \
  --force-with-lease="refs/heads/$HEAD_BRANCH:$EXPECTED_HEAD_SHA" \
  "$HEAD_REPO_URL" \
  "HEAD:refs/heads/$HEAD_BRANCH"
```

Never create a PR here. Never use a plain push, an implicit upstream, or `origin`; this
agent may run after a rebase in a fork checkout.

### Step 8: Initial CI status (best-effort)

```bash
gh pr checks "$PR_NUMBER" --repo "$BASE_REPO" || true
```

The `--repo` scope is required: the PR number identifies a PR in the base repository,
and in a fork checkout an unscoped `gh pr checks` resolves against the fork, where that
number does not exist.

## Success criteria

- Changelog entry exists and validates
- Formatting + linting clean
- Branch pushed to the verified PR head; existing PR remains a draft
- Initial CI status reported

## Integration

Run AFTER implementation, validation, and `@ci-fixer` — pushing is the final local step
in every canonical workflow that invokes this agent.
