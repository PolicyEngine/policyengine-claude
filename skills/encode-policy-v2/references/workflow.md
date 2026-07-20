# Workflow: encode-policy-v2 (canonical)

This file is the single canonical definition of the encode-policy-v2 workflow. The
Claude Code command (`/encode-policy-v2`) and Codex skill (`$encode-policy-v2`) are thin
launchers over this document: each parses raw arguments, maps the semantic roles below
to its native delegation mechanism, and follows these phases exactly. Runtime-specific
agent names and question mechanics belong in the launchers, not here.

## Purpose and routing

Implement a new PolicyEngine-US state benefit program, or a new structural component of
an existing program, from official sources. The workflow researches the law, obtains
user approval for modeled scope, tracks every requirement through parameters, variables,
and tests, validates the implementation, prepares a draft PR, and performs an independent
review-fix loop.

Use `encode-reform` instead when the program already exists and the requested change is
purely parametric: changing a cap, rate, threshold, match, or other existing parameter.
Continue with encode-policy-v2 for a new program or a structural addition that requires
new formulas, eligibility gates, or a new deduction/credit/benefit family.

### Existing-program pre-flight

Before research, check the live PolicyEngine-US tree for the target program using a
read-only GitHub query against the expected state/program variable path (for example,
`gh api repos/PolicyEngine/policyengine-us/contents/{expected-path}`) and a local concept
search. If the program exists and the request appears purely parametric, explain that
`encode-reform` is the lighter workflow and ask:

- **Use encode-reform instead** (recommended): stop without changing anything.
- **Continue with encode-policy-v2**: record the structural reason in the run ledger.

Do not silently route or continue.

## Orchestration contract

The coordinator protects its context window and owns only orchestration:

- parse arguments, derive run identity, maintain the short run ledger, and run small
  structured commands;
- present user checkpoints and write the resulting scope decision;
- delegate research, implementation, testing, validation, reporting, and Git operations;
- read only handoff files the Handoff table marks `Coordinator may read? Yes`;
- never read full source research, the implementation specification, PDF text/images, or
  implementation files; never implement or fix program code directly;
- continue automatically between gates, stopping only at a user checkpoint or a blocked
  gate defined below.

Research roles may write `sources/working_references.md` and worktree-scoped runtime
artifacts before scope approval. They must not create a branch, issue, PR, commit, or
implementation file. The first GitHub write occurs only after the user approves scope.

**Completion contract.** A delegated role completes only after its required artifact or
result exists and is well formed. Its final response is one line:
`DONE — wrote {artifact} ({brief stat})`, or for identifier/Git roles,
`DONE — {identifiers or commit/push result}`. If a delegate stops without its required
output, retry once with the missing contract; then apply the phase's blocked behavior.

**Ownership contract.** No implementation role commits. Only initial-pusher,
review-round-pusher, and issue-manager — the latter solely for the Phase 2B branch
initialization (empty commit, push, PR reuse checkout) — may commit or push. Parallel
roles never write the same file.
All roles receive concrete `WORKTREE_ROOT`, `WORKTREE_ID`, `RUN_ROOT`, and `PREFIX` values
and stay inside the current worktree and their owned paths.

## Roles

| Role | Responsibility | Owned writes / output | Skills to load |
|---|---|---|---|
| document-collector | Discover official sources; download, extract, and render every PDF page; record failed fetches | `sources/working_references.md`, source artifacts, `{RUN_ROOT}/{PREFIX}-research-summary.md` | policyengine-us |
| user-document-processor | Process user-supplied files after an unreachable-source checkpoint | user source artifacts, append-only research notes | — |
| requirements-consolidator | Verify citations, find reference implementations/reusable variables, extract every requirement | impl spec, requirements checklist, scope summary | policyengine-us; policyengine-model-development (references/parameters.md, references/variables.md) |
| issue-manager | Find/create the issue, create/use the worktree-safe branch, push it, and open a draft PR | issue/PR/branch identifiers; GitHub state | policyengine-standards |
| parameter-implementer | Implement approved parameter and reference requirements | target program parameter YAML only | policyengine-us; policyengine-model-development (references/parameters.md, references/style.md) |
| variable-implementer | Implement approved formulas and publish the exact variable contract | target program variable Python; implementation manifest | policyengine-us; policyengine-model-development (references/variables.md, references/parameters.md, references/vectorization.md, references/periods-and-aggregation.md, references/style.md) |
| test-creator | Create unit, integration, and edge-case YAML tests from the final variable contract | target program tests; test manifest | policyengine-model-development (references/tests.md, references/periods-and-aggregation.md, references/variables.md) |
| requirements-tracker | Map every approved requirement to parameter, variable, and test coverage | `{RUN_ROOT}/{PREFIX}-coverage-report.md` | policyengine-model-development (references/parameters.md, references/variables.md, references/tests.md) |
| gap-fixer | Implement only requirements reported missing by the tracker | target program parameters, variables, or tests | policyengine-us; policyengine-model-development (all relevant references) |
| implementation-validator | Run cross-file structural validation; fix mechanical issues and escalate judgment calls | target program mechanical fixes; validator report | policyengine-model-development (references/parameters.md, references/variables.md, references/style.md) |
| validator-escalation-fixer | Fix only judgmental items in the validator's escalation section | target program parameters/variables; validator post-fix note | policyengine-us; policyengine-model-development (relevant references) |
| ci-fixer | Run the targeted test funnel, classify failures, and make evidence-backed repairs | target program files/tests; CI status | policyengine-model-development (references/tests.md, references/variables.md, references/parameters.md, references/periods-and-aggregation.md, references/vectorization.md, references/style.md) |
| quick-auditor | Audit the final diff for shortcuts, policy changes, and missing coverage | `{RUN_ROOT}/{PREFIX}-checkpoint.md` | policyengine-model-development (relevant references) |
| audit-fixer | Fix only findings assigned from the quick audit, by original ownership | target program files/tests | policyengine-model-development (relevant references) |
| initial-pusher | Create the changelog, format once, stage approved paths, commit once, and push while keeping the PR draft | changelog and Git state | policyengine-standards |
| reporter | Build the PR body and short final report from verified artifacts | PR description, final report | policyengine-writing; policyengine-standards |
| review-fixer-vars | Fix critical review findings in parameter and variable files only | target parameter/variable files; per-round vars checklist | policyengine-us; policyengine-model-development (parameters, variables, vectorization, periods/aggregation, style) |
| review-fixer-tests | Fix critical review findings in test files only | target test files; per-round tests checklist | policyengine-model-development (tests, periods/aggregation, variables) |
| review-ci-fixer | Run the bounded post-review test funnel and report status | target files/tests; CI status | policyengine-model-development (relevant references) |
| review-round-pusher | Merge per-fixer checklists, stage only reviewed paths, commit, and push one review-fix round | shared checklist and Git state | policyengine-standards |

Every role that writes or reviews parameter references must enforce this rule: a PDF href
ends in `#page=XX` using the PDF file page number, not the printed page number. A
single-page PDF is the only exception.

## Arguments

- `STATE`: state name, for example `Rhode Island` or `Oregon`
- `PROGRAM`: program name/type, for example `CCAP`, `TANF`, or `LIHEAP`
- `--skip-review`: skip Phase 6 only
- `--research-only`: stop after the Phase 2 scope decision; make no GitHub writes
- `--600dpi`: render every PDF page at 600 DPI instead of 300
- `--resume`: reuse artifacts only after validating their recorded inputs
- `--from-phase N`: resume at phase N after validating all prerequisites; implies resume
- `--full-validation`: run one broader state/package suite after program tests pass

If `STATE` or `PROGRAM` is missing, ask for the missing value before continuing. Derive:

- `ST`: lowercase state abbreviation
- `PROG`: lowercase program abbreviation
- `BRANCH` and `PREFIX`: `{ST}-{PROG}`
- `DPI`: 600 when requested, otherwise 300
- `RESUME`: true for `--resume` or `--from-phase`
- `FROM_PHASE`: requested phase, otherwise the first incomplete valid phase

## Phase 0: Setup and source acquisition

### 0A. Worktree identity and guard

Derive the worktree namespace before any runtime-artifact operation:

```bash
WORKTREE_ROOT=$(git rev-parse --show-toplevel)
WORKTREE_ID=$(printf '%s' "$WORKTREE_ROOT" | git hash-object --stdin | cut -c1-12)
RUN_ROOT="/tmp/policyengine-command-runs/$WORKTREE_ID"
mkdir -p "$RUN_ROOT"
```

The absolute worktree root—not the Git common directory, repository name, or branch—is
the isolation boundary. Inspect `git worktree list --porcelain` before any branch
operation. If `BRANCH` belongs to another worktree, stop and report its path; never force
checkout it, use `--ignore-other-worktrees`, edit through that path, or share its
artifacts.

### 0B. Fresh/resume ledger

Use `{RUN_ROOT}/{PREFIX}-encode-run-state.md` as a short phase ledger. Record:

- worktree root/ID, arguments, derived values, branch, current HEAD, issue/PR identifiers;
- source URL/checksum/DPI, spec/scope hashes, completed phases, artifacts, test manifest;
- elapsed time per phase, repair/review rounds, explicit user decisions, blocked items.

On a fresh run, remove only this workflow's `PREFIX`-owned encode artifacts from
`RUN_ROOT`; do not delete matching downloaded sources/renderings that the ledger proves
reusable. On resume, require matching worktree, state, program, branch, and dependency
hashes. `--from-phase N` also requires every prerequisite artifact. When any input
changed, invalidate that phase and all dependents. Never reuse an artifact merely because
its path exists.

### 0C. Collect official documentation

Delegate document-collector. It must:

1. Discover the official program name and sufficient official authority for every known
   eligibility rule, income test, deduction/exemption, benefit formula, demographic or
   immigration rule, resource rule, payment standard, copayment, provider rate, and work
   requirement.
2. Download up to the relevant complete source set to
   `{RUN_ROOT}/{PREFIX}-source-{N}.pdf`; record URL and checksum.
3. Extract searchable text to `{RUN_ROOT}/{PREFIX}-source-{N}.txt` when possible.
4. Render **every page of every collected PDF**:
   `pdftoppm -png -r {DPI} ...`. Extracted text aids search but never replaces visual
   rendering. Reuse rendering only when checksum and DPI match and the complete expected
   page sequence exists.
5. Save full research to `sources/working_references.md` and write the short research
   summary (maximum 20 lines): program name, source URLs, counts of eligibility and
   deduction/exemption rules, benefit calculation type, complexity, and every failed
   fetch with reason and likely contents.

The coordinator reads only the short research summary. If collection fails entirely,
stop; requirements cannot be extracted without documentation.

### 0D. Unreachable-reference checkpoint

If an official reference failed with a block, redirect, timeout, or connection error,
show each source and ask the user to choose:

- **I will provide downloaded files**: wait for paths, then delegate
  user-document-processor to copy each file into `RUN_ROOT`, extract text, render every
  page at `DPI`, and append verified content to the research notes.
- **Proceed with available sources**: record the evidence limitation and continue.
- **Let me investigate first**: pause without invalidating artifacts.

Skip this checkpoint only when no relevant source failed.

## Phase 1: Consolidation and requirements extraction

Delegate requirements-consolidator to read the full research and repository reference
implementations. It must:

1. Search broadly by program concepts, not only the target acronym; identify all matching
   state implementations and study the three to five most relevant variable and parameter
   examples.
2. Search the live codebase for reusable variables and parameters for income, household
   composition, age, hours, provider/care concepts, and other inputs. Do not recreate
   generic concepts as bare inputs.
3. Verify every statute/manual section, definition, and PDF page citation against the
   acquired text and rendered pages before downstream roles copy it.
4. Write:
   - `{RUN_ROOT}/{PREFIX}-impl-spec.md` (**Full**): every requirement numbered
     `REQ-001...`, tagged `ELIGIBILITY`, `INCOME`, `BENEFIT`, `EXEMPTION`,
     `DEMOGRAPHIC`, `IMMIGRATION`, `RESOURCE`, or `NOT-MODELED`; verified citations;
     reusable variables; all reference implementations, noting for each requirement
     whether the selected reference implementation covers it; suggested
     parameter/variable structure; income-source list for `sources.yaml`; and TANF
     approach recommendation when relevant.
   - `{RUN_ROOT}/{PREFIX}-requirements-checklist.md` (**Short**, maximum 40 lines): total
     and one cited line per requirement.
   - `{RUN_ROOT}/{PREFIX}-scope-summary.md` (**Short**, maximum 15 lines): program/type,
     requirement count, complexity, best reference implementation, suggested approach,
     and each modeling decision the user must make.

The coordinator reads only the checklist and scope summary. A missing or unverified
requirements artifact blocks Phase 2.

## Phase 2: Scope checkpoint and draft setup

### 2A. Present and decide scope

Show the short overview and requirements grouped by tag. Ask one decision at a time:

1. **Overall scope**: implement every simulatable requirement (recommended), or review
   groups/items to exclude. `NOT-MODELED` requirements remain tracked but excluded.
2. For each questionable group: include all (recommended unless the evidence suggests
   otherwise), skip all, or decide individually.
3. Ask each program-specific decision separately, such as provider-rate tables now versus
   follow-up, simplified versus full TANF, or mapping versus creating/skipping income
   concepts without an exact existing variable.

Do not make these modeling decisions for the user. Write the answers to
`{RUN_ROOT}/{PREFIX}-scope-decision.md` (**Short**) with:

- every in-scope requirement;
- every excluded requirement and reason;
- key decisions and any user notes.

If `--research-only`, stop here and report the research, specification, checklist, and
scope-decision paths. Do not create an issue, branch, PR, commit, or push.

### 2B. Create implementation issue, branch, and draft PR

After scope approval, resolve the repository targets first and record them in the
ledger: `BASE_REPO` is the intended upstream (`PolicyEngine/policyengine-us`) with its
Git `BASE_REPO_URL`; `PUSH_REPO` and `PUSH_REPO_URL` are the user's writable repository
or fork, derived from the checkout's push remote (for example
`git remote get-url --push origin`). Verify that the base target is
`PolicyEngine/policyengine-us` and the push target is that repository or the user's
corresponding fork. Pass these values, with the concrete worktree/run values and the
proposed `BRANCH`, to issue-manager in every delegation.

Delegate issue-manager in discovery mode (`MODE=discover`), which makes no GitHub or Git
writes. It searches for **both** an existing issue and PR before either is created. If
it returns `DECISION_NEEDED`, show all candidate numbers, titles, status, activity, and
short scope; ask the issue and PR reuse/create decisions one at a time. Do not select
among competing existing work automatically. If it returns `NO_CANDIDATES`, treat both
decisions as create-new without asking. Then re-delegate issue-manager in execution mode
(`MODE=execute`) with both explicit decisions.

The execution delegation applies both decisions as one plan: reuse or create the issue, then
reuse or create the PR. Reusing an issue must not suppress creation of a requested new PR;
reusing a PR must not create a duplicate. For a new PR, create the issue first when
needed; in this worktree only, create `BRANCH`, make the empty initialization commit
required to establish a remote branch without staging research or implementation files,
push explicitly to the user's verified fork/repository URL, and create a draft PR
targeting the resolved upstream default branch. For a reused PR, check out its exact head
repository/branch only after verifying push access and the worktree guard. Record
`ISSUE_NUMBER`, `PR_NUMBER`, `PR_URL`, branch, head/base repositories and SHAs, and whether
each resource was reused or created in the ledger. Failure is blocking.

## Phase 3: Implementation and requirement coverage

Execute roles in dependency order. Each role reads the full impl spec and approved scope
directly from disk; the coordinator does not paraphrase implementation guidance.

### 3A. Parameters

Delegate parameter-implementer. It must study the selected reference implementation,
reuse existing generic parameters/variables, put values in the correct jurisdiction
hierarchy, place income-source lists in `sources.yaml` rather than inline additions,
store a rate when law defines a percentage, and implement every approved value-based
requirement with verified subsection and PDF-page references.

### 3B. Variables and implementation manifest

After parameters exist, delegate variable-implementer. It must use the Phase 3A parameter
tree, reuse existing generic variables, keep legal values in parameters, choose entities
and periods from the law, use vectorized formulas, use `adds` for pure sums and `add()`
inside formulas that combine sums with other operations, and implement every approved
logic requirement.

It writes `{RUN_ROOT}/{PREFIX}-implementation-manifest.md` (maximum 60 lines) listing for
every formula variable: exact name/path, entity, definition period, inputs, parameters,
requirements covered, and intended test file. It must verify every listed variable exists.

### 3C. Tests

After the implementation manifest exists, delegate one test-creator so ordinary,
integration, and edge cases have a single owner. It must use only verified existing
inputs and the exact variable contract, read `sources/working_references.md` for the
documented calculation examples that ground its scenarios, and create:

- unit cases for every formula variable;
- five to seven integration scenarios with inline calculation explanations;
- relevant threshold-minus-one/threshold/threshold-plus-one, zero/maximum income,
  family-size, rounding/capping, and missing/negative input cases;
- realistic periods (`YYYY` or `YYYY-01`) and values grounded in documentation.

Write `{RUN_ROOT}/{PREFIX}-test-manifest.md` with exact changed test files and case names.
All later test commands derive from this manifest; no guessed directory or placeholder is
allowed.

Automatic integration into `household_state_benefits.yaml` remains disabled. Do not edit
it unless the user separately approves enabling that integration.

### 3D. Requirements coverage gate

Delegate requirements-tracker to cross-reference every in-scope requirement against the
actual target parameters, variables, and tests. Write the coverage report (maximum 40
lines) with `Covered`, `MISSING`, and totals.

If requirements are missing, delegate one gap-fixer round limited to the `MISSING` list,
then rerun the tracker. Do not create duplicate components to avoid editing an existing
one. If gaps remain after the single repair round, show them to the user and record the
incomplete coverage in the ledger; do not describe coverage as complete.

## Phase 4: Validation and bounded repair

### 4A. Structural validator

Delegate implementation-validator in structural mode only:

- YAML integrity: misplaced metadata/value blocks, breakdown/enum mismatch, duplicate
  keys, and effective-date placement;
- cross-reference linkage: orphan parameters/files/directories and missing references;
- federal/state jurisdiction placement and required `defined_for` declarations.

It may fix mechanical issues. It records per-file style/formula observations as nonblocking
notes for the later independent review, and places judgmental issues in `ESCALATED`.
Write `{RUN_ROOT}/{PREFIX}-validator-report.md` with `FIXED`, `ESCALATED`, and
`Notes for review` sections.

If escalations exist, delegate validator-escalation-fixer for those items only, append a
post-fix section, then rerun a cheap targeted structural check on the changed files. Do not
continue until escalations are `NONE`; otherwise stop at a blocked gate.

### 4B. Targeted CI funnel

Delegate ci-fixer. It reads the implementation spec, approved scope, and exact test
manifest; it opens full research only when policy evidence is needed to adjudicate a
failure. It must:

1. Run every changed test file together without verbose output.
2. Classify all failures before editing: mechanical, implementation defect, test defect,
   or policy ambiguity; batch independent mechanical fixes.
3. Rerun only failed files/cases. Use a named-case filter when supported.
4. Add diagnostic verbosity and depth 2 only for a still-unresolved numeric/formula
   failure; increase depth only when necessary.
5. After targeted tests pass, run the exact program test directory once without verbose
   output.
6. With `--full-validation`, run the broader state/package suite once after the program
   directory passes; never repeat it inside the repair loop.

Use at most four targeted repair cycles. If the same failure survives two consecutive
cycles, mark it blocked instead of rerunning the same command. Resolve calculation
disagreements against the approved spec and cited source; never change an expected result
merely to make tests green. Do not format in this phase.

Write `{RUN_ROOT}/{PREFIX}-ci-fixer-status.md` (**Short**) with `STATUS: PASS` or
`STATUS: BLOCKED`, commands, counts, reruns, elapsed time, and remaining root causes.

On `BLOCKED`, show the failures and ask:

- **Pause for manual guidance**: wait, then rerun affected cases after guidance.
- **Proceed anyway**: record explicit consent and require a `Known failing tests` section
  in the PR body.
- **Abort**: stop with resumable artifacts.

Never push a known failure without the explicit proceed decision.

### 4C. Quick diff audit

Delegate quick-auditor to inspect the final diff for hard-coded values added to satisfy
tests, year-check conditionals, altered parameter values, and gaps from the coverage
report. It writes `{RUN_ROOT}/{PREFIX}-checkpoint.md` (**Short**, maximum 15 lines) with
`PASS` or `FAIL` and exact findings.

On failure, route each item once to the appropriate audit-fixer by original ownership and
rerun the audit. A second failure is a blocked gate; do not push.

## Phase 5: Finalize the draft PR

### 5A. Changelog, format, initial commit, and push

Delegate initial-pusher only after the coverage status, structural gate, CI decision, and
quick audit are recorded. It must:

- create the repository's towncrier changelog fragment;
- run formatting once, then rerun only exact affected tests if formatting changes
  executable files;
- stage only approved program parameters, variables, tests, and the changelog;
- confirm local research under `sources/` is not staged;
- commit once as `Implement {STATE} {PROGRAM} (ref #{ISSUE_NUMBER})` and push once.

The PR remains draft. Never mark it ready in this workflow.

### 5B. PR description and short report

Delegate reporter to read the scope, coverage, research summary, impl spec, CI status, and
working references. It writes:

- `{RUN_ROOT}/{PREFIX}-pr-description.md` (**Full**) with Summary/issue link,
  Regulatory Authority, Income Eligibility Tests, Income Deductions and Exemptions,
  Income Standards, Benefit Calculation, Requirements Coverage, Not Modeled, Historical
  Notes, and Files Added. Include `Known failing tests` only after an explicitly accepted
  blocked CI result.
- `{RUN_ROOT}/{PREFIX}-final-report.md` (**Short**, maximum 25 lines) with requirement and
  file counts, coverage, test status, issue, and PR.

Update the draft PR body from the file without loading it into coordinator context. The
coordinator reads only the final report.

## Phase 6: Independent review-fix loop

Skip only with `--skip-review`. Use the canonical `review-program` workflow; do not embed
or improvise a second review methodology here.

### Round 1: full review

Run `review-program` with arguments
`PR_NUMBER --local --full --prefix {PREFIX} [--600dpi when DPI is 600]`. Pass
`--prefix {PREFIX}` on every review invocation: a reused PR's head branch need not equal
`{ST}-{PROG}`, and without the override review-program derives its artifact prefix from
the checked-out branch — writing paths other than the Handoff table entries this phase
reads. Read only `{RUN_ROOT}/{PREFIX}-review-summary.md`.

- If the count of still-open critical findings is zero, Phase 6 completes.
- Otherwise delegate review-fixer-vars and review-fixer-tests concurrently. Each reads
  the full report but edits only its owned file class and writes its own
  `{PREFIX}-checklist-{vars|tests}-r1.md`; neither appends to the shared checklist.

Every review fixer first checks the approved scope. It skips and records findings that
conflict with an intentional scope choice, reads the impl spec only for policy values or
formula changes, searches for reusable variables before adding anything generic, does not
format, and writes one line per action in this form:
`- [ROUND N] [SCOPE] [{CATEGORY}] {file}:{line} — {problem} → {change}`. Use `VARS` or
`TESTS` scope. Parameter/variable categories are `HARD-CODED`, `WRONG-PERIOD`,
`MISSING-REF`, `BAD-REF`, `DEDUCTION-ORDER`, `UNUSED-PARAM`, `WRONG-ENTITY`, `NAMING`,
`FORMULA-LOGIC`, or `OTHER`; test categories are `TEST-GAP`, `WRONG-PERIOD`,
`WRONG-EXPECTATION`, `NON-FUNCTIONAL-TEST`, or `OTHER`. A role with nothing in scope writes
one `NO-ISSUES` line.

After both finish, delegate review-ci-fixer to run at most three targeted repair cycles,
one program-directory confirmation, and one format pass. `PARTIAL` is permitted because
the mandatory follow-up review adjudicates remaining findings. Then delegate
review-round-pusher to merge both round files into the shared checklist, stage only the
program paths, commit `Review-fix round 1: address critical issues from review-program`,
and push.

A follow-up review after a fix is mandatory.

### Round 2: verification review

For mechanical/test-only fixes, run with
`PR_NUMBER --local --incremental {RUN_ROOT}/{PREFIX}-review-full-report.md --prefix {PREFIX} [--600dpi]`
so unchanged source/PDF evidence is reused. When a fix changed policy semantics,
parameter values, references, or sources, instead run
`PR_NUMBER --local --full --resume --prefix {PREFIX} [--600dpi]`. Read only the new
short summary.

- If still-open critical findings are zero, Phase 6 completes.
- Otherwise ask whether to attempt one final fix round or stop and show the remaining
  issues. Do not choose automatically.

If approved, repeat the parallel ownership split into round-2 per-fixer files. Review
fixers read the shared checklist to avoid reintroducing prior patterns. Run the bounded
review CI funnel, then merge, commit as review-fix round 2, and push through
review-round-pusher. A final review is mandatory.

### Round 3: final review

Choose incremental versus full/resumed review by the same semantic-change rule. Do not
perform another fix round:

- zero still-open critical findings: report success;
- remaining critical findings: report them for manual resolution and keep the PR draft.

There are at most three reviews and two review-fix commits.

## Phase 7: Final summary

Run even when Phase 6 was skipped. Show the user:

- implemented versus excluded requirement totals and coverage status;
- parameter, variable, and test files created;
- validation/test status and any explicitly accepted known failures;
- review rounds and remaining findings, when applicable;
- issue and draft PR links;
- that the user—not the workflow—decides when to mark the PR ready;
- `WORKFLOW COMPLETE` only when all applicable completion requirements below are met.

## Handoff table

| Artifact | Writer | Coordinator may read? | Size |
|---|---|---|---|
| `sources/working_references.md` | document-collector/user-document-processor | No | Full |
| `{RUN_ROOT}/{PREFIX}-research-summary.md` | document-collector | Yes | Short, 20 lines |
| `{RUN_ROOT}/{PREFIX}-impl-spec.md` | requirements-consolidator | No | Full |
| `{RUN_ROOT}/{PREFIX}-requirements-checklist.md` | requirements-consolidator | Yes | Short, 40 lines |
| `{RUN_ROOT}/{PREFIX}-scope-summary.md` | requirements-consolidator | Yes | Short, 15 lines |
| `{RUN_ROOT}/{PREFIX}-scope-decision.md` | coordinator | Yes | Short |
| `{RUN_ROOT}/{PREFIX}-implementation-manifest.md` | variable-implementer | No | Full, maximum 60 lines |
| `{RUN_ROOT}/{PREFIX}-test-manifest.md` | test-creator | No | Exact manifest |
| `{RUN_ROOT}/{PREFIX}-coverage-report.md` | requirements-tracker | Yes | Short, 40 lines |
| `{RUN_ROOT}/{PREFIX}-validator-report.md` | implementation-validator | Yes | Bounded report |
| `{RUN_ROOT}/{PREFIX}-ci-fixer-status.md` | CI roles | Yes | Short |
| `{RUN_ROOT}/{PREFIX}-checkpoint.md` | quick-auditor | Yes | Short, 15 lines |
| `{RUN_ROOT}/{PREFIX}-pr-description.md` | reporter | No | Full |
| `{RUN_ROOT}/{PREFIX}-final-report.md` | reporter | Yes | Short, 25 lines |
| `{RUN_ROOT}/{PREFIX}-review-full-report.md` | review-program | No | Full |
| `{RUN_ROOT}/{PREFIX}-review-summary.md` | review-program | Yes | Short, 20 lines |
| `{RUN_ROOT}/{PREFIX}-checklist-{vars,tests}-r{N}.md` | review fixers | No | Per-fixer |
| `{RUN_ROOT}/{PREFIX}-checklist.md` | review-round-pusher | No | Growing |
| `{RUN_ROOT}/{PREFIX}-encode-run-state.md` | coordinator | Yes | Short ledger |

## Completion and error rules

The workflow is complete only when:

- the user-approved scope decision exists;
- every in-scope requirement has a recorded coverage result;
- structural escalation is empty;
- CI passed, or the user explicitly accepted documented known failures;
- the quick audit passed;
- the initial implementation is committed and pushed to a draft PR;
- the PR body and final report exist;
- Phase 6 completed or was explicitly skipped;
- the Phase 7 summary was shown.

Error handling:

- source collection or requirements extraction failure: stop;
- branch owned by another worktree, wrong target repository, GitHub write failure: stop;
- implementation role failure: retry its output contract once, then report and wait;
- missing coverage: one targeted gap-fix/recheck, then report remaining gaps accurately;
- structural escalation: one targeted fix/recheck, then block;
- CI: bounded repair followed by the explicit user checkpoint above;
- quick audit: one targeted fix/recheck, then block;
- review loop: never exceed the stated round budgets.

Never proceed past a red blocking gate, fabricate a passed artifact, silently broaden
scope, stage local research, operate in another worktree, or mark the PR ready.
