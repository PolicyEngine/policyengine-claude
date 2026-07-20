# Codex Workflow: encode-policy-v2

## Purpose

Implement a new PolicyEngine-US state benefit program from official sources with a scope checkpoint, requirement tracking, tests, validation, and draft PR preparation.

## Arguments

Parse the text after `$encode-policy-v2`:

- `STATE`: state name, such as `Rhode Island` or `Oregon`
- `PROGRAM`: program type, such as `CCAP`, `TANF`, or `LIHEAP`
- `--skip-review`: skip the final review/fix loop
- `--research-only`: stop after scope review
- `--600dpi`: render PDFs at 600 DPI instead of 300 DPI
- `--resume`: reuse valid artifacts from an interrupted run
- `--from-phase N`: resume from a phase after validating prerequisites
- `--full-validation`: run the broader state/package suite once after program tests pass

Derive:

- `ST`: lowercase state abbreviation
- `PROG`: lowercase program abbreviation
- `BRANCH`: `{ST}-{PROG}`
- `PREFIX`: `{BRANCH}`
- `DPI`: `600` if requested, otherwise `300`
- `RESUME`: true for `--resume` or `--from-phase`

Derive a worktree-safe runtime root before any artifact operation:

```bash
WORKTREE_ROOT=$(git rev-parse --show-toplevel)
WORKTREE_ID=$(printf '%s' "$WORKTREE_ROOT" | git hash-object --stdin | cut -c1-12)
RUN_ROOT="/tmp/policyengine-command-runs/$WORKTREE_ID"
mkdir -p "$RUN_ROOT"
```

Record `WORKTREE_ROOT` and `WORKTREE_ID` in
`{RUN_ROOT}/{PREFIX}-encode-run-state.md`. The absolute worktree root—not the Git common
directory or branch name—is the isolation boundary. Refuse to resume artifacts recorded
by another worktree.

Before creating or checking out `{BRANCH}`, inspect `git worktree list --porcelain`.
Never use `--ignore-other-worktrees` or edit another worktree. If the branch is already
owned elsewhere, stop and report that path.

## Phase 0: Setup

On a fresh run, clean only encode artifacts inside `RUN_ROOT`. With `--resume`, preserve
and validate phase artifacts, invalidating dependent phases when their inputs changed.

Keep setup read-only. Defer the GitHub issue, branch, and draft PR until after the user
approves scope; skip those writes entirely for `--research-only`.

Collect official documentation:

- Discover the official program name.
- Download each PDF to `{RUN_ROOT}/{PREFIX}-source-{N}.pdf`.
- Extract text to `{RUN_ROOT}/{PREFIX}-source-{N}.txt` with `pdftotext` where possible.
- Render every page of every collected PDF with
  `pdftoppm -png -r {DPI} {RUN_ROOT}/{PREFIX}-source-{N}.pdf {RUN_ROOT}/{PREFIX}-source-{N}-page`.
  Extracted text helps search but does not replace visual rendering. Reuse pages only
  when the PDF checksum and DPI match and the complete expected page sequence exists.
- Save research detail to `sources/working_references.md`.
- Write `{RUN_ROOT}/{PREFIX}-research-summary.md` in 20 lines or fewer with sources found, failed fetches, major eligibility tests, income deductions, and benefit calculation type.

If important agency references failed to fetch, ask the user to provide downloaded files or confirm proceeding with available sources.

## Phase 1: Requirements Extraction

Read `sources/working_references.md` and write three handoff files:

- `{RUN_ROOT}/{PREFIX}-impl-spec.md`: full implementation spec
- `{RUN_ROOT}/{PREFIX}-requirements-checklist.md`: one line per requirement, max 40 lines
- `{RUN_ROOT}/{PREFIX}-scope-summary.md`: user-facing scope summary, max 15 lines

The implementation spec must include:

- numbered requirements: `REQ-001`, `REQ-002`, etc.
- tags such as `ELIGIBILITY`, `INCOME`, `BENEFIT`, `EXEMPTION`, `DEMOGRAPHIC`, `IMMIGRATION`, `RESOURCE`, and `NOT-MODELED`
- citations verified against source text
- existing PolicyEngine variables to reuse
- reference implementation paths
- suggested parameter and variable structure
- income source lists for `sources.yaml`, not inline `adds`

Search broadly for reference implementations. Do not search only the target acronym. Use concept keywords such as `child`, `care`, `provider`, `energy`, `heating`, `cash`, or `assistance`.

## Phase 2: Scope Checkpoint

Show the user the short scope summary and grouped requirements. Ask decisions one at a time:

- implement all simulatable requirements or skip selected groups
- defer complex pieces such as provider rates when appropriate
- choose simplified or full approach for TANF-like programs
- decide how to map income types with no exact PolicyEngine variable

Write `{RUN_ROOT}/{PREFIX}-scope-decision.md` with in-scope requirements, excluded requirements, key decisions, and user notes.

If `--research-only` is set, stop after writing the scope decision and summarize the outputs.

Otherwise, search for an existing issue/PR, create or use branch `{BRANCH}`, and create a
draft PR for the approved scope.

## Phase 3: Implementation

Implement in dependency order.

1. Parameters
   - Use `$policyengine-parameter-patterns`, `$policyengine-variable-patterns`, and `$policyengine-code-organization`.
   - Put values in the correct jurisdiction hierarchy.
   - Add detailed references with `#page=XX`.
   - Use rates when law defines rates.
   - Put income source lists in `sources.yaml`.

2. Variables
   - Use `$policyengine-variable-patterns`, `$policyengine-vectorization`, `$policyengine-aggregation`, `$policyengine-period-patterns`, `$policyengine-code-style`, and `$policyengine-code-organization`.
   - Reuse existing variables before creating new ones.
   - Use parameters for all legal values.
   - Verify person, tax unit, SPM unit, and household entity levels.
   - Write `{RUN_ROOT}/{PREFIX}-implementation-manifest.md` with exact variable names,
     paths, entities, periods, inputs, parameters, and requirements covered.

3. Tests
   - Start only after the implementation manifest exists.
   - Use `$policyengine-testing-patterns` and `$policyengine-period-patterns`.
   - Add unit tests for formula variables.
   - Add 5 to 7 integration scenarios with calculation comments.
   - Include edge cases at thresholds, zero income, family-size boundaries, and negative income/deduction cases.
   - Write `{RUN_ROOT}/{PREFIX}-test-manifest.md` with exact changed test files and cases.

After implementation, write `{RUN_ROOT}/{PREFIX}-coverage-report.md` showing each in-scope requirement and its parameter, variable, and test coverage.

If requirements are missing, fix them once and rerun the coverage check.

## Phase 4: Validation

Run local validation before pushing:

- structural check for YAML integrity, parameter references, orphan directories, jurisdiction placement, and `defined_for`
- focused tests driven by the exact test manifest. The CI fixer should use `$policyengine-testing-patterns`, `$policyengine-variable-patterns`, `$policyengine-parameter-patterns`, `$policyengine-period-patterns`, `$policyengine-code-style`, `$policyengine-aggregation`, `$policyengine-vectorization`, and `$policyengine-code-organization`.

- run affected test files together without `-v`
- classify all failures before editing and batch independent mechanical fixes
- rerun only failed files/cases; use `-v -d 2` only for unresolved formula failures
- use at most four targeted repair cycles
- run the program directory once after targeted tests pass
- run a broader suite once only with `--full-validation`
- write `{RUN_ROOT}/{PREFIX}-ci-fixer-status.md` with `STATUS: PASS` or `STATUS: BLOCKED`
- if blocked, list each remaining failure, root cause, and why it is blocked
- quick diff audit for hard-coded values, year conditionals, altered parameters, and missing coverage

If CI is blocked, stop and ask the user whether to pause for manual fixes, proceed to the
draft PR with a "Known failing tests" section, or abort (artifacts stay resumable). Never
push a knowingly failing implementation without that explicit consent. Enforce quick-audit
failures through one targeted fix/recheck and do not push if the gate remains red.

## Phase 5: Draft PR Preparation

Format once, create a changelog fragment, commit once, push once, and keep the PR as draft.
Write a PR body from actual handoff files:

- summary and issue link
- regulatory authority
- income eligibility tests
- income deductions and exemptions
- standards and benefit calculation
- requirements coverage table
- not-modeled requirements
- files added

Write `{RUN_ROOT}/{PREFIX}-final-report.md` in 25 lines or fewer and show it to the user.

## Phase 6: Review-Fix Loop

Skip this phase only with `--skip-review`.

Run `$review-program {PR_NUMBER} --local --full` once, inspect the short summary, and fix
critical issues. Follow with `$review-program --incremental REPORT` for mechanical/test
fixes. Run another full review only when fixes changed policy semantics, parameter values,
references, or sources. Use at most three total review rounds.

When review-fix rounds spawn parallel parameter/variable and test fixers, each fixer writes its own checklist file, such as `{RUN_ROOT}/{PREFIX}-checklist-vars-r1.md` and `{RUN_ROOT}/{PREFIX}-checklist-tests-r1.md`. The orchestrator concatenates those files into `{RUN_ROOT}/{PREFIX}-checklist.md` after both finish. Do not let parallel fixers append to the same checklist file directly.
