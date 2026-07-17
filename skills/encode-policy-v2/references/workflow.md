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

Derive:

- `ST`: lowercase state abbreviation
- `PROG`: lowercase program abbreviation
- `BRANCH`: `{ST}-{PROG}`
- `PREFIX`: `{BRANCH}`
- `DPI`: `600` if requested, otherwise `300`

## Phase 0: Setup

Clean stale handoff files:

```bash
rm -f /tmp/${PREFIX}-*.md
```

Find or create the GitHub issue and draft PR. Search existing issues and PRs before creating new ones. Create or use branch `{BRANCH}`.

Collect official documentation:

- Discover the official program name.
- Download official PDFs and pages.
- Extract text with `pdftotext` where possible.
- Render PDFs with `pdftoppm -png -r {DPI}`.
- Save research detail to `sources/working_references.md`.
- Write `/tmp/{PREFIX}-research-summary.md` in 20 lines or fewer with sources found, failed fetches, major eligibility tests, income deductions, and benefit calculation type.

If important agency references failed to fetch, ask the user to provide downloaded files or confirm proceeding with available sources.

## Phase 1: Requirements Extraction

Read `sources/working_references.md` and write three handoff files:

- `/tmp/{PREFIX}-impl-spec.md`: full implementation spec
- `/tmp/{PREFIX}-requirements-checklist.md`: one line per requirement, max 40 lines
- `/tmp/{PREFIX}-scope-summary.md`: user-facing scope summary, max 15 lines

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

Write `/tmp/{PREFIX}-scope-decision.md` with in-scope requirements, excluded requirements, key decisions, and user notes.

If `--research-only` is set, stop after writing the scope decision and summarize the outputs.

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

3. Tests
   - Use `$policyengine-testing-patterns` and `$policyengine-period-patterns`.
   - Add unit tests for formula variables.
   - Add 5 to 7 integration scenarios with calculation comments.
   - Include edge cases at thresholds, zero income, family-size boundaries, and negative income/deduction cases.

After implementation, write `/tmp/{PREFIX}-coverage-report.md` showing each in-scope requirement and its parameter, variable, and test coverage.

If requirements are missing, fix them once and rerun the coverage check.

## Phase 4: Validation

Run local validation before pushing:

- structural check for YAML integrity, parameter references, orphan directories, jurisdiction placement, and `defined_for`
- focused tests for the program path. The CI fixer owns the full loop: mechanical fixes, formula fixes, test expectation fixes, and missing parameter fixes. It should use `$policyengine-testing-patterns`, `$policyengine-variable-patterns`, `$policyengine-parameter-patterns`, `$policyengine-period-patterns`, `$policyengine-code-style`, `$policyengine-aggregation`, `$policyengine-vectorization`, and `$policyengine-code-organization`.

```bash
policyengine-core test policyengine_us/tests/policy/baseline/gov/states/{ST}/... -c policyengine_us -v
```

- iterate up to 8 times
- write `/tmp/{PREFIX}-ci-fixer-status.md` with `STATUS: PASS` or `STATUS: BLOCKED`
- if blocked, list each remaining failure, root cause, and why it is blocked
- `make format`
- quick diff audit for hard-coded values, year conditionals, altered parameters, and missing coverage

Continue to PR preparation even if CI is blocked, but the PR description must include a "Known failing tests" section from `/tmp/{PREFIX}-ci-fixer-status.md`.

## Phase 5: Draft PR Preparation

Create a changelog fragment, push the branch, and keep the PR as draft. Write a PR body from actual handoff files:

- summary and issue link
- regulatory authority
- income eligibility tests
- income deductions and exemptions
- standards and benefit calculation
- requirements coverage table
- not-modeled requirements
- files added

Write `/tmp/{PREFIX}-final-report.md` in 25 lines or fewer and show it to the user.

## Phase 6: Review-Fix Loop

Skip this phase only with `--skip-review`.

Run `$review-program {PR_NUMBER} --local --full`, inspect the short summary, and fix critical issues. Run up to three review/fix rounds. Stop early only when the review reports zero critical issues.

When review-fix rounds spawn parallel parameter/variable and test fixers, each fixer writes its own checklist file, such as `/tmp/{PREFIX}-checklist-vars-r1.md` and `/tmp/{PREFIX}-checklist-tests-r1.md`. The orchestrator concatenates those files into `/tmp/{PREFIX}-checklist.md` after both finish. Do not let parallel fixers append to the same checklist file directly.
