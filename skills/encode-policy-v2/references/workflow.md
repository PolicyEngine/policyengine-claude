# Workflow: encode-policy-v2 (canonical)

The command and skill share this workflow. Launchers map roles to runtime tools; they
must not add stages, audits, test suites or approval prompts.

## Purpose and routing

Implement a new PolicyEngine-US state benefit program or a structural component from
primary sources, with an explicit modeled scope, source-grounded tests and independent
review. Check the target code and related concepts before researching a new program.
For a purely parametric change to existing behavior, recommend `encode-reform`; follow
an existing routing decision, or ask if the user's intended structural change is unclear.

## Orchestration and ownership

The coordinator owns research, requirements, scope, coverage/structural checks, test
execution, Git operations and reporting. It may read code, source extracts, manifests
and full findings when needed. Read relevant sections and keep bulky command output in
logs; do not impose a summary-only restriction that requires another agent for each read.

Use two substantive implementation roles when delegation is available and authorized:

| Role | Responsibility and owned writes | Skills/references |
|---|---|---|
| implementer | Parameters and variables together; exact implementation manifest; fixes in those paths | policyengine-us; policyengine-model-development parameters, variables, vectorization, periods/aggregation |
| test-author | Source-derived unit, integration and boundary tests; exact test manifest; test fixes | policyengine-model-development tests, periods/aggregation; relevant primary evidence |

Before substantive model work, the coordinator and every model worker must satisfy the
[model-development loading contract](../../policyengine-model-development/references/agent-loading.md).
Include it in each dispatch. Require `SKILLS_READY` evidence from each worker, record it
in existing run state/manifests, and check the actual changes against the loaded rules
in the existing coverage/structural gates. A `SKILLS_BLOCKED` worker does not write model
code or tests. Fresh review contexts must load their skills independently too.

Keep each role's context across its implementation and repair work. The test-author can
read the approved rules and plan cases while the implementer works; it finalizes tests
against the published variable contract. Exchange contract changes directly where the
runtime permits, otherwise through the coordinator. Parallel writers never own the same
file. Do not split parameter and variable implementation into successive agents, or
create default tracker, structural-validator, CI-fixer, quick-auditor, reporter or pusher
agents. A specific difficult problem may justify a bounded specialist; state what it
will resolve and avoid a duplicate audit. Role count follows independent work and runtime
capacity, not numbers of files, sources or PDF pages.

When delegation is unavailable, the coordinator implements these roles directly. The
independent review still needs a fresh review context. Only the coordinator commits,
pushes or writes GitHub state. Workers never stage files, format the whole repository,
sync/install dependencies, or edit unowned files. The coordinator formats owned paths
once before validation and again only after subsequent edits require it.

Each worker writes its required artifact and returns
`DONE — wrote {artifact} ({status}; {elapsed})`. Each worker appends `<UTC time> <stage>`
to `{RUN_ROOT}/{PREFIX}-encode-progress-{role}.log` at stage changes and at least every
two minutes, and logs before starting a long generation step (for example a large
parameter table) so a silent write is not mistaken for a stall; that log is the only
file the coordinator watches. Workers do the assigned work themselves: no helper,
explorer, verifier or nested worker agents, whose contexts would lack the loaded skills.
Use bounded waits and actual tool capabilities; do not require
particular team/message/monitor tools. Yield for completion notifications; never use
five-minute shell sleeps. If polling is necessary, use interruptible waits of at most
60 seconds and resume on completion. After five minutes without observable progress,
request a bounded recovery/final report and stop a still-silent worker within two more
minutes. Recover its files, retry the missing task once, then report the remaining gap.
Do not equate a file's existence with role completion. The coordinator handles routine
bookkeeping itself instead of restarting a worker merely to copy text or compute totals.

## Arguments

- `STATE PROGRAM`: state and program name; ask only for missing/ambiguous identity.
- `--research-only`: stop after requirements and the scope decision; no GitHub writes.
- `--local`: keep implementation, tests, commits and review local; create no issue/PR,
  push or online comment. Leave the implementation worktree for inspection.
- `--skip-review`: skip independent review explicitly, not validation.
- `--sources MANIFEST`: reuse same-worktree source evidence after integrity checks.
- `--source-budget MINUTES`: total new external source-acquisition window for research,
  default 10; nonnegative, 0 uses only supplied/cache evidence. Not an analysis deadline.
- `--600dpi`: render only necessary PDF pages at 600 DPI instead of 300.
- `--resume`, `--from-phase N`: reuse only matching inputs; the latter implies resume.
- `--full-validation`: add one broader state/package suite after affected tests pass.

Derive `ST` and `PROG` as lowercase abbreviations, `PREFIX={ST}-{PROG}`, and a worktree-safe
branch name. Honor user-supplied paths/branches. Keep research and runtime evidence out of
commits. Existing scope and publication decisions persist; do not ask for them again.

## Phase 0: Capture identity and collect evidence

### 0A. Worktree and run state

```bash
WORKTREE_ROOT=$(git rev-parse --show-toplevel)
WORKTREE_ID=$(printf '%s' "$WORKTREE_ROOT" | git hash-object --stdin | cut -c1-12)
RUN_ROOT="/tmp/policyengine-command-runs/$WORKTREE_ID"
mkdir -p "$RUN_ROOT"
```

Record `BASE_REPO=PolicyEngine/policyengine-us`, its URL and default branch (from the base
repository's metadata, not the local clone's branch name), current HEAD,
worktree root/ID, args, workflow revision/diff, branch and publication mode in
`{RUN_ROOT}/{PREFIX}-encode-run-state.md`. Inspect status and worktree ownership before
branch operations. Never force-checkout another worktree's branch, move its files, or
stage unrelated changes. Use a new worktree when requested or needed for isolation.

Record source/spec/scope hashes, owned files, validation inputs/environment, completed
phases, decisions and remaining gaps. Read the old state before starting fresh; preserve
valid evidence and prior reports instead of deleting every matching artifact. Resume
requires matching identity and dependencies. Invalidate changed steps and dependents,
not unaffected research. A workflow-contract change requires reassessing old completion
markers; legacy role names alone do not establish that the new gates passed.

Use the review-program skill's `scripts/run_bounded.py` for networked Git/GitHub commands
with a 60-second deadline and for test-runner invocations with a 540-second deadline,
below the runtime's tool timeout so the wrapper's exit status is always recorded.
Resolve that installed skill directory as `REVIEW_SKILL_ROOT`.
A failed fetch/read is not an empty result; retry a transient setup failure once, then
report the blocker. Scope GitHub reads/writes explicitly to `BASE_REPO`.

### 0B. Research and requirements in one context

The coordinator gathers the primary rules and builds the implementation specification
in the same context. For a genuinely large independent research component, a bounded
research worker may return requirements and evidence together; do not follow it with a
second mandatory citation/requirements agent reading the same documents again.

Reuse valid supplied/cache documents before acquisition. Record originals, checksums,
extracts and actual renders in `{PREFIX}-sources.json` under RUN_ROOT using the
[shared evidence contract](../../review-program/references/source-cache.md). Write useful
research notes to `sources/working_references.md` or a program-specific local note and
record its exact path; never overwrite another program's notes. No branch/issue/PR or
implementation is needed for research-only work.

Acquire missing relevant sources in bounded parallel batches. Start one acquisition
clock at the first external search/fetch; every call gets at most 60 seconds or the
remaining budget. Allow at most two targeted search batches per material gap and two
fetch attempts per URL. Switch a blocked route to a primary publication of record when
available; a bot-check response is not evidence. Stop optional acquisition at the budget
and report unresolved claims. Do not invent rules or infer correctness from failed URLs.

Read text first with headings, definitions, exceptions and cross-references. Inspect
relevant tables, scans, footnotes and ambiguous layouts visually, rendering selected
pages with `pdftoppm -f N -l N -png -r DPI`. No whole-PDF screenshot requirement. Verify
physical page locators before citing PDFs; PDF hrefs use `#page=XX`, except single-page
files. Seek further sources only for unsupported requirements or genuine conflicts.

A failed URL is not itself a user checkpoint when another authoritative document
establishes the rule. If material rules remain unsupported, present the specific gaps
and options together: user-provided evidence, an expanded acquisition budget, a clearly
limited scope, or pause. Proceed only with supported requirements and an approved scope;
complete research failure blocks implementation.

## Phase 1: Requirements and proposed scope

Search the model by concepts, not only the target acronym. Inspect the closest relevant
implementation and additional examples only where it leaves a design question unresolved;
there is no quota of three to five complete programs to read. Identify reusable income,
household, age, work, immigration and other inputs before proposing new ones.

Write these artifacts once from the research:

- `{PREFIX}-impl-spec.md`: numbered `REQ-001...` requirements, source/page evidence and
  effective dates, reusable variables/parameters, proposed entities/periods and file
  structure, and unresolved modeling decisions. Tag requirements by eligibility, income,
  benefit, exemption, demographic, immigration, resource or not-modeled as appropriate.
- `{PREFIX}-requirements-checklist.md`: requirement IDs and concise descriptions; do not
  truncate requirements to satisfy a line-count target.
- `{PREFIX}-scope-summary.md`: brief proposed coverage, limitations and decisions needed.
- `{PREFIX}-research-summary.md`: primary sources, supported rule groups and material gaps.

These are different views of the same requirements, not separate investigations. The
coordinator may consult the original evidence rather than spawning a verifier to read it.

## Phase 2: Scope and branch setup

### 2A. Scope decision

Apply explicit choices already provided. Present remaining material modeling decisions
as one batch with a concrete proposed scope: which requirements can be simulated, which
are excluded and why. Ask follow-ups only when an answer introduces a new decision.
Do not silently choose simplified policy or omit a requested component. Record approved
requirements, exclusions, conditions and reasons in `{PREFIX}-scope-decision.md`.

Approval is a decision, not a required extra conversation turn. A user who says to run
the proposed local benchmark, or says "continue" after its scope is stated, has authorized
that work. Record that instruction and proceed. Ask only when a material choice remains;
routine entity/file design and the existence of a scope artifact do not require another
confirmation. State the modeled year, components and limitations early so the user can
correct them while independent research continues. An unanswered material question is
still unanswered; elapsed time never supplies approval.

With `--research-only`, stop with those artifacts and no implementation/GitHub writes.
Without approved scope, do not implement or publish. Local exploratory research may
continue while an unanswered scope decision is pending.

### 2B. Branch and existing work

For local mode, create/use the approved local branch and record no issue/PR. Otherwise,
search for both existing issues and PRs, with structured bounded reads, before creating
anything. Ask about competing candidates together; honor a previously specified issue
or PR. No candidates means no reuse decision is needed.

Record the upstream base and verified writable head repository/branch. For an existing
PR, capture its head SHA before local edits and check push access and worktree ownership.
For new work, branch locally from the resolved base; do not create an empty initialization
commit or push an empty draft PR. Save issue/PR creation decisions for Phase 5, when an
actual implementation and reviewable PR body exist. No GitHub writes before approved
scope, or at all in `--local` mode.

## Phase 3: Implement and author tests

### 3A. Implementation owner

Pass the implementer the approved spec, sources, concrete worktree/run values and exact
owned paths. It implements parameters and variables together: jurisdiction hierarchy,
existing generic concepts, `sources.yaml` income lists, legal values in parameters,
source-correct dates/entities/periods, vectorized formulas, `adds` for pure sums and
`add()` when sums participate in other formula operations.

Publish `{PREFIX}-implementation-manifest.md`: exact variable names/paths, entities,
periods, inputs/parameters and requirement IDs. Verify names exist. Tell the test-author
when the contract is stable and explicitly identify later changes. Do not make it infer
names from an informal coordinator summary.

Whenever the coordinator briefs both owners on the same behavior, for initial work or a
repair, it states each behavioral contract once in one shared contract block copied
verbatim into both briefs: which variable owns which computation, where a deduction,
cap or gate applies, and which public variables stay unchanged. Check that block against
the existing helper contracts before sending it; two briefs written separately are how
the owners end up building and testing different placements.

### 3B. Test owner

The test-author reads the approved evidence and contract, and owns unit, boundary and
integration tests together. Derive expected amounts from source rules, not observed
implementation output. Cover distinct formulas and policy branches, especially excluded
populations, effective dates, assessment units and final benefits. Use as many scenarios
as these require; do not impose a fixed five-to-seven integration-test quota or every
possible household composition. A shared end-to-end case can cover several requirements.

Use plausible demographics/incomes and actual entity memberships. Do not force an
eligibility flag when the test is meant to establish its derivation. Follow the model's
period conventions. For exploratory Python cases use the
[period-aware diagnostic helper](../../review-program/references/automation.md#model-diagnostics)
when helpful; a calculated result is not proof of correct policy or plausible inputs.

Write `{PREFIX}-test-manifest.md` with exact test paths/case names and requirement IDs,
including directly affected existing regression tests. Do not change partner contract
expectations just to make tests pass. Integration into `household_state_benefits.yaml`
requires an explicit scope decision; do not silently enable it.

Pin expectations only on the public variables named in the shared contract block, at
the level where that block places each rule. If a case fails because the rule sits in a
different variable than the brief said, report `CONTRACT MISMATCH` with the case names
to the coordinator and stop; do not rerun the set, relocate cases or change values
unprompted. The coordinator rules once and the affected owner applies the ruling.

### 3C. Coverage gate

The coordinator reconciles requirements against actual implementation/test paths and
writes `{PREFIX}-coverage-report.md` with covered/missing IDs. Reuse the manifests and
inspect discrepancies; no separate tracker agent. Send missing items to their existing
owner in one bounded repair batch, then recheck those items. Missing in-scope coverage
blocks completion until implemented or explicitly excluded by the user. Never label it
complete just because every planned file exists.

## Phase 4: Validate and repair changed behavior

The coordinator owns validation. Create the changelog and format owned files before
checks. Use the existing model environment; confirm imports target this worktree. Set up
missing dependencies once only when required and authorized; workers do not each sync.

### 4A. Structural checks

Check YAML integrity, breakdowns, references, effective dates, parameter/variable linkage,
entities, jurisdiction and required `defined_for` against the changed implementation.
Reuse import/test failures as evidence rather than starting a second identical audit.
Write `{PREFIX}-validator-report.md` with PASS or unresolved items. The coordinator may
fix mechanical mistakes in coordination with owners; substantive policy decisions go to
the appropriate owner with source evidence. Do not stage cross-jurisdiction renames or
fix unrelated code. Recheck affected items after repair; unresolved structural errors block.

### 4B. One test owner and bounded repair

Run the exact changed and directly affected regression tests in one invocation, with
full output under RUN_ROOT; inspect summaries and failures. Prefer the program test
directory when it contains precisely the required set. Do not run all changed files and
then the same directory again solely to satisfy two stage names. Add an extra directory
pass only when it covers additional relevant tests. `--full-validation` adds one broader
state/package suite, not one per repair cycle.

The coordinator's invocation is the run of record. A worker may run its owned test files
at most once per task as a self-check before reporting DONE, in one bounded invocation;
it never loops over files one at a time, repeats an unchanged set to recover lost
output, or runs another owner's files. Every invocation uses the bounded helper with a
540-second deadline and the tool timeout at its maximum above it, writes combined output
to a log under RUN_ROOT, and reads back the summary line and failures. Do not pipe the runner through
`tail`, detach it, or rely on a default two-minute tool limit; each loses the exit status
and forces a repeat. Record the number of runner invocations and their total time in the
CI status so repeated runs stay visible.

Classify failures before editing: mechanical, implementation defect, test defect, policy
ambiguity or environment. Send the affected items to their existing owner; never change
expected values only to match output. Use at most two repair batches per validation phase;
a recurring failure without a new diagnosis is blocked. After a fix, run failed cases
and any affected previously passing regressions together. Add verbosity only for an
unresolved failure. A later discovery can justify another test invocation; batching is
not a reason to omit a necessary check.

Record `{PREFIX}-ci-fixer-status.md`: PASS/BLOCKED, exact commands/paths, counts, tested
HEAD plus working-file hashes, environment, elapsed time and unresolved causes. Reuse a
passing result while tested behavior, parameter dependencies, tests and environment match.
Formatting-only changes do not invalidate a passing test result, even when file hashes
change: record the formatter and updated hashes without rerunning tests. Behavior-changing
edits or conflict resolutions invalidate affected checks. Do not repeat unchanged successful
tests in the pusher or reporting step.

For unresolved test failures, present causes and options together: guidance, stop, or an
explicitly accepted known failure. Preserve such consent and describe accepted failures
in the PR body; never silently push red tests. Unavailable tests are NOT RUN, not PASS.

### 4C. Final diff check

The coordinator checks the final diff for test-specific hard-coding, arbitrary year
conditions, altered legal values, missing approved requirements and unrelated edits.
Reuse evidence already established; this is not another regulatory review. Record
`{PREFIX}-checkpoint.md` with PASS or exact issues. Route one repair batch to the existing
owners and recheck affected tests/structure. A repeated unresolved audit issue blocks.

## Phase 5: Save the reviewable implementation

The coordinator writes `{PREFIX}-pr-description.md` and `{PREFIX}-final-report.md` from
the verified scope, evidence, coverage and validation. Scale the description to the
implementation: behavior, authority, scope/limitations, validation and issue linkage.
Do not copy every artifact into another long report or launch a reporting agent.

Stage exact approved implementation/test/changelog paths; exclude research, runtime
artifacts and unrelated user files. Verify the staged diff. In publication mode,
create/reuse the approved issue now and add its reference to the prepared body and
commit message. Then commit one implementation commit. Formatting/checks already
completed in Phase 4 need not run again unless inputs changed.

In `--local` mode, keep the commit in this worktree and skip every GitHub write and push.
The commit supplies a stable snapshot for the local independent review in Phase 6. Keep
files/artifacts accessible for the user; no cleanup of the implementation worktree.

Otherwise, push the verified head branch explicitly. For existing remote work,
compare the live head with the pre-edit captured SHA; if it advanced, preserve that work
and reconcile before revalidating. Use normal fast-forward pushes for this workflow;
never overwrite another writer's commits. Create the draft PR only after the first real
implementation commit is pushed, or update the agreed existing PR. Record identifiers
and SHAs. GitHub failure is a blocked publication step, not a reason to repeat encoding.
Never mark the PR ready; a reused non-draft PR keeps its existing state.

## Phase 6: Independent review and targeted fixes

Skip only with `--skip-review`. Use the canonical `review-program` workflow in a fresh
review coordinator context; it dispatches its substantive reviewers under its own rules.
Supply raw source bytes/manifest and approved scope, not an instruction to accept the
implementer's policy conclusions. Pass concrete worktree/run values and enough free
worker capacity; don't inherit a summary-only restriction. Pass the resolved installed
`REVIEW_SKILL_ROOT` and workflow/adapter paths; the fresh coordinator loads the installed
skill and checks its returned body, rather than searching for the plugin or reinvoking a
same-named compatibility command.

Keep this handoff mechanical: installed skill paths, arguments, captured head, approved
scope, raw source manifest and runtime constraints. The review workflow supplies the
roles' tasks. Do not compose another audit checklist or turn every encoder assumption
into a mandatory review question. Pass a specific unresolved scope/source question when
one actually exists. The fresh review coordinator loads model-development before any
substantive country-model work, as do its reviewers.

- Published work: `PR_NUMBER --local --prefix PREFIX --sources MANIFEST`.
- Local-only work: `--local-diff --prefix PREFIX --sources MANIFEST` (no PR required).

Use `{PREFIX}-sources.json` initially and validated `{PREFIX}-review-sources.json` on
follow-ups. Pass `--600dpi` only when requested. The review has its own bounded acquisition
budget; source reuse should avoid reacquiring unchanged material. A PARTIAL review does
not automatically restart either research budget or become a successful encoding run.

Review-program owns the review decision. The encode coordinator checks that the returned
artifacts identify the intended head, include role completion/skill-load evidence, and
state COMPLETE or PARTIAL. Read the summary, result JSON and the selected findings to
route repairs; do not re-adjudicate them, fetch their sources again, rerun their
diagnostics, or add a verification pass before dispatch. Use `confirmed_critical_ids`
from `{PREFIX}-review-result.json` for repair dispatch, not `counts.critical` or the
total still-open count, which can include UNVERIFIED claims. For an older report without
that field, inspect finding states explicitly; missing metadata is not zero criticals.
Zero still-open critical findings plus
COMPLETE status completes this phase. PARTIAL/missing status leaves explicit pending
checks; do not fix UNVERIFIED claims as if they were established defects. Obtain evidence
or a specific skip decision before declaring completion. An invalid hypothetical scenario,
optional coverage or an untested suggested remedy is not a confirmed defect. If a required
question remains unresolved, report it without starting a speculative model repair or
repeating a full review. Do not widen the approved year/program scope to clear incidental
historical observations.

Do not start another fix/review round solely for noncritical findings. With zero confirmed
criticals, return the completed review result and any PARTIAL gaps; additional work needs
an explicit user request. The maximum round count is a ceiling, not a quota. Keep optional
improvements visible rather than automatically extending the encoding run to clear them.

Assign confirmed criticals to the existing implementer and/or test-author, only when that
owner has actual work. Keep writes disjoint and share changed contracts through the
Phase 3A shared contract block, copied verbatim into both repair briefs; when the
implementer's inspection changes a placement, it updates the implementation manifest and
the test-author finalizes placement-sensitive cases only after that update. Don't spawn
an empty fixer merely to write NO-ISSUES. Track finding IDs and actions in
`{PREFIX}-checklist-{vars,tests}-rN.md`, only for participating owners; the coordinator merges
these into `{PREFIX}-checklist.md`. Scope conflicts require an explicit decision, not a
silent policy expansion.

Pass each finding ID and its existing evidence to its fix owner without rewriting the
review into another proof or a speculative replacement design. The owner inspects the
affected code to implement the repair. If that reveals a concrete contradiction in the
finding, return that ID and evidence to the review owner for one targeted resolution;
neither the encoder nor fixer starts another general review. Test planning can overlap
the repair when the changed contract is already specified.

After the first repair batch, format changed owned paths, run the affected test set and
structural checks once, update coverage/status/body, and commit a review-fix round. Apply
the Phase 4 failure gate; push only in publication mode. Follow-up review is mandatory:
use the same local/published identity with `--incremental {PREFIX}-review-full-report.md`,
which review-program preserves before replacing outputs. Recheck fixes, dependencies
and unresolved findings, not every already-reviewed rule.

Maximum: two reviews and one intervening review-fix batch. Round 2 runs only after
round 1 has confirmed criticals and those findings receive repairs; it checks the repaired
head incrementally. If confirmed criticals or required evidence gaps remain after round 2,
stop and report them explicitly. Do not start a second fix batch or a third review, and do
not claim completion with unresolved blockers. Further work requires a new user request.
No new default CI-fixer, pusher or reporting workers during these rounds.

## Phase 7: Final status and benchmark

Always report implemented/excluded requirements, coverage, changed files, actual tests,
review status/findings, limitations, and artifact/worktree paths. Published mode includes
issue/draft PR links; local mode explicitly reports that nothing was posted or pushed.
Refresh the final report/PR body after repairs so it describes the final state.

`WORKFLOW COMPLETE` requires approved scope; complete in-scope coverage; clear structural
and diff gates; passed tests or explicitly accepted known failures; saved implementation;
final report; and completed or explicitly skipped independent review. Publication mode
also requires the intended issue/PR and successful push. A blocked step stays resumable
without reporting success. Never infer completion from artifact existence alone.

For benchmarks, append clock-generated `<UTC time> <phase> start|end` markers to
`{RUN_ROOT}/{PREFIX}-encode-timing.log` at every phase boundary, review dispatch and
accepted result, and around user waits; summarize them in
`{RUN_ROOT}/{PREFIX}-encode-timing.json` with these keys so runs stay comparable:
`setup_seconds`, `research_seconds` (with `acquisition_window_seconds`),
`spec_scope_seconds`, `user_wait_seconds`, `implementation_seconds`,
`test_authoring_seconds` (concurrent with implementation, never summed with it),
`validation_repair_seconds` (with `test_invocations` and `test_runner_seconds`),
`commit_seconds`, `review_round_N_seconds` (dispatch through accepted result),
`repair_round_N_seconds`, `total_wall_seconds` and `active_seconds` (wall minus user
waits and interruptions). Separate user waits and workflow development from active
encoding, and don't add overlapping role durations.
Record interpreter startup, actual test time, repeated calls, blocked fetches, fixes,
misses and withdrawn findings where observed. Report code/source hashes and environment
so comparisons use equivalent inputs. Real implementations establish workflow behavior;
helper tests and saved-report replays do not establish policy accuracy or speed gains.
For every review round, the caller records a clock timestamp immediately before dispatch
and another when it has checked the returned artifact identity/status and can route fixes.
Report this whole interval as review time, including dispatch, skill loading, reviewers,
consolidation, cleanup and return handoff. Reviewer-only time is a breakdown, never the
headline review duration. Preserve interruption/recovery intervals within that wall time
and identify them separately. Do not claim the integrated workflow is faster until an
actual encode-to-review invocation completes under the changed workflow.

## Artifact ownership

All `{PREFIX}-*` paths are under RUN_ROOT. The coordinator maintains the run state,
research/spec/scope, source manifest, coverage/validator/checkpoint/CI status, PR body,
final report, merged fix checklist and timing log/summary. The implementer owns the
implementation manifest; the test-author owns the test manifest; each worker owns its
own progress log. Fixers own only their per-round checklist.
Review-program owns its `review-*` artifacts and temporary review snapshot cleanup.
These artifact names preserve caller compatibility; legacy per-stage agent names are not
requirements to spawn separate workers. Never commit local research or remove another
run's evidence or worktree.
