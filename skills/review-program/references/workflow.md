# Workflow: review-program (canonical)

This is the shared behavior for the Claude command and Codex skill. Launchers map roles
to runtime tools; they do not add review stages. Review PolicyEngine changes without
editing code. Default to two substantive reviewers: policy/sources and code/tests.

## Orchestration contract

The coordinator may read the diff, source index, code and findings. It resolves scope,
provides inputs, consolidates results and handles the user; no separate agents are needed
for context analysis, file listing, verification planning or report assembly. Reviewers
own investigation and validation of their findings. Use another reader only for a specific
material disagreement or uncertainty, not automatically for every flag or citation.

Do not edit tracked source, switch existing branches, commit, push or apply fixes. Use a
disposable detached snapshot and write reports, downloads, renders and diagnostic scripts
under `RUN_ROOT`. Run tools in read-only modes; put test caches outside the snapshot and
disable bytecode where practical. Only the coordinator may post a review, with the user's
existing authorization or an explicit posting decision after the report is ready.

A reviewer writes its assigned report and returns
`DONE — wrote {path} ({confirmed findings}; {material evidence gaps}; {elapsed})`.
Wait for completion notifications; do not infer completion merely from a file's existence.
Each reviewer appends `<UTC time> <stage>` to `{RUN_ROOT}/{PREFIX}-review-progress-{role}.log`
at every stage change and at least every two minutes of work; that log is the only file
the coordinator watches. The coordinator checks the other roles' logs whenever a sibling
completes and, while waiting, may watch a log's modification time with a bounded
file-watch; it never reads a partial report. Silence longer than five minutes means
send the role one "finalize now with what you have" message; silence for two more
minutes means stop the role, recover its usable work, and retry the missing task once or
complete it directly. A live progress update can justify continued analysis, not an
unbounded external call. If the work cannot be finished, consolidate a PARTIAL review
with the missing checks identified. Never keep waiting indefinitely for an optional
source search.

If delegation is unavailable, execute the roles directly with the same scope and outputs.
An encoding implementation still needs an independent review context; reuse raw sources,
not an implementer's conclusions as proof of correctness.

## Arguments

Parse flags and their values before identifying positional arguments.

- `PR_ARG`: PR number or search text. Ask if omitted; ask which PR if search is ambiguous.
- `PDF_URL`: optional official source URL; discover relevant sources if omitted.
- `--local`: display locally only; no GitHub posting.
- `--local-diff`: review committed changes through local `HEAD` without pushing;
  excludes staged, unstaged and untracked changes; implies `--local`.
- `--full`: explicitly audit the whole identified program, including unchanged behavior.
  For a multi-program PR, record the exact program paths. It does not mandate more agents
  or rendering all pages. Default scope is changed behavior and affected dependencies.
- `--skip-pdf`: omit PDF acquisition/inspection; keep code/tests and applicable non-PDF
  policy checks. Describe this limitation; never label PDF evidence verified.
- `--600dpi`: render selected pages at 600 DPI instead of 300; not the whole PDF.
- `--sources MANIFEST`: reuse original evidence from a same-worktree source manifest;
  see [source-cache.md](source-cache.md). Validate bytes before reuse.
- `--source-budget MINUTES`: total time budget for new external source acquisition in
  this review, default 5; nonnegative, 0 means use supplied/cache evidence only. This is
  not a deadline for code analysis or reading available sources.
- `--resume`: reuse validated artifacts of an interrupted or completed review.
- `--incremental REPORT`: review changes and unresolved findings since a previous report.
- `--prefix NAME`: artifact prefix override for callers such as encode-policy-v2.
  Require a nonempty filename component: no slashes, backslashes, glob characters or `..`.

## Phase 0: Identity and reuse

Derive the worktree namespace before any artifact operation:

```bash
WORKTREE_ROOT=$(git rev-parse --show-toplevel)
WORKTREE_ID=$(printf '%s' "$WORKTREE_ROOT" | git hash-object --stdin | cut -c1-12)
RUN_ROOT="/tmp/policyengine-command-runs/$WORKTREE_ID"
mkdir -p "$RUN_ROOT"
```

Resolve the repository and PR identity before choosing a prefix. Unless explicitly
overridden, use `PREFIX="pr-$PR_NUMBER"`; two PRs reviewed from the same branch must
not overwrite each other's artifacts. Validate an explicit prefix before using it.
Set `REVIEW_SKILL_ROOT` to the absolute installed review-program skill directory so
the helper paths below work from any checkout.

Pass concrete `WORKTREE_ROOT`, `WORKTREE_ID`, `RUN_ROOT`, `PREFIX` and, after Phase 1,
`SNAPSHOT` to reviewers. Never share another worktree's uncommitted files or run state.
Do not run concurrent reviews with the same worktree/prefix; choose a distinct prefix.

Use `{RUN_ROOT}/{PREFIX}-review-run-state.md` to record repository/PR identity, args,
base/head/merge-base SHAs, scope, source-manifest path/checksums, completed roles, the
current output-file list, timings, snapshot path and any missing checks. Resolve current
inputs in Phase 1 before accepting cached findings. Reuse a completed review only when
all those inputs (including source budget, full/PDF flags and DPI) still match and both
reports are valid. A matching head alone is insufficient.

An unchanged PARTIAL run retains its gaps; do not relabel it COMPLETE or repeat blocked
source searches without new evidence or an expanded budget. Resume only affected checks.

On fresh or invalidated analysis, exclude old findings from the current output-file list;
only current validated artifacts may enter consolidation. Preserve original sources,
extracts and renders. Never delete the source cache just to start a new review. For an
incremental run, copy the supplied report to `{RUN_ROOT}/{PREFIX}-review-prior-report.md`
before replacing the normal report. Do not overwrite that copy with itself on resume.

Resolve `BASE_REPO` explicitly in fork checkouts (`gh repo set-default --view` or an
explicit `--repo OWNER/REPO`). Scope all PR reads and eventual comments to that repository.
Search returns candidate numbers/titles, not just the first result. Respect organization
routing from the active workspace. An omitted posting decision need not delay review;
local-only flags always prohibit posting.

## Phase 1: Capture the reviewed code and scope

Read PR metadata and CI status with structured `gh` output. Failing, pending, absent or
unavailable checks are distinct states; do not confuse an unsuccessful `gh pr checks`
exit with failure to resolve the PR. Associate CI with its checked head SHA; if the remote
head changes during review, state which commit the results describe.

Fetch from the base repository URL, not `origin` (which may be a fork). The resolved PR
URL identifies the base repository authoritatively:

```bash
set -euo pipefail
: "${BASE_REPO:?resolve OWNER/REPO in Phase 0 before capture}"
: "${PR_NUMBER:?resolve the PR number in Phase 0 before capture}"
bounded() {
  python3 "$REVIEW_SKILL_ROOT/scripts/run_bounded.py" --seconds 60 "$@"
}
PR_URL=$(bounded gh pr view "$PR_NUMBER" --repo "$BASE_REPO" --json url --jq '.url')
BASE_REPO_URL=${PR_URL%/pull/*}
BASE_BRANCH=$(bounded gh pr view "$PR_NUMBER" --repo "$BASE_REPO" --json baseRefName --jq '.baseRefName')
bounded git -C "$WORKTREE_ROOT" fetch "$BASE_REPO_URL" "$BASE_BRANCH"
BASE_SHA=$(git -C "$WORKTREE_ROOT" rev-parse FETCH_HEAD)
if [ "${LOCAL_DIFF:-false}" = "true" ]; then
  PR_HEAD=$(git -C "$WORKTREE_ROOT" rev-parse HEAD)
else
  bounded git -C "$WORKTREE_ROOT" fetch "$BASE_REPO_URL" "pull/$PR_NUMBER/head"
  PR_HEAD=$(git -C "$WORKTREE_ROOT" rev-parse FETCH_HEAD)
fi
MERGE_BASE=$(git -C "$WORKTREE_ROOT" merge-base "$BASE_SHA" "$PR_HEAD")
BEHIND=$(git -C "$WORKTREE_ROOT" rev-list --count "$PR_HEAD..$BASE_SHA")
AHEAD=$(git -C "$WORKTREE_ROOT" rev-list --count "$BASE_SHA..$PR_HEAD")
git -C "$WORKTREE_ROOT" diff "$MERGE_BASE".."$PR_HEAD" > "$RUN_ROOT/${PREFIX}-review-diff.txt"
```

Use the same 60-second wrapper for other networked `gh`/`git` reads, including PR
discovery and CI queries. Exit 124 means timeout, not a valid empty response; record
the failed step and elapsed time. Retry a transient setup failure at most once, then
report that capture is blocked. Execute capture and snapshot blocks in the same shell,
or explicitly pass their captured values to the next call; shell variables do not
persist between tool calls.

Set `LOCAL_DIFF=true` only for `--local-diff`; `--local` changes posting mode only.
Every step must stop on failure, including a missing merge-base. Never use stale
`FETCH_HEAD` or diff files after a failed fetch. For local-diff, report the exclusion of
uncommitted files; remote CI is not local validation unless its checked SHA matches.

**Materialize the PR's file contents.** Always isolate the captured commit, even when
local `HEAD` matches it: matching SHAs do not prove the working files are clean.

```bash
set -euo pipefail
SNAPSHOT=$(mktemp -d "$RUN_ROOT/${PREFIX}-pr-snapshot.XXXXXX")
if ! git -C "$WORKTREE_ROOT" worktree add --detach "$SNAPSHOT" "$PR_HEAD"; then
  rmdir "$SNAPSHOT" 2>/dev/null || true
  exit 1
fi
```

Record the exact created path immediately. Every repository read and test uses
`SNAPSHOT`. Do not reuse or delete another invocation's snapshot.

For incremental review, verify the prior report identifies this repository/PR, records its
reviewed head, and that head is an ancestor of `PR_HEAD`. Otherwise use the full merge-base
diff and explain why. With a valid baseline, use `PRIOR_HEAD..PR_HEAD`, plus unresolved
prior findings and dependencies affected by those changes. Value, formula or citation
changes invalidate evidence for the affected behavior; they do not require a whole-program
restart. If the impact cannot be bounded, expand scope explicitly. Preserve prior IDs.
If `--full` expands beyond the prior verified scope, review that additional scope too.

Dispatch the reviewers as soon as the snapshot exists; do not hold them for a scope
brief. Each reviewer derives scope from the diff, PR body and snapshot itself. The
coordinator then reads the diff and records a concise scope brief in the run state:
changed paths, program/year, affected behavior, needed sources, selected roles and at
most five concrete questions to verify (for example a helper's tie-breaking semantics,
a gate that might not apply, a downstream consumer). Send those questions to the running
reviewers as one follow-up message; keep the brief under a minute of coordinator time.
Unchanged code may be read to trace impact. Newly activated parameter values and formulas
are in scope. Unrelated historical values and already-dead code are not audit targets
unless `--full` was requested; note an incidental issue for follow-up without researching
it further. Being behind base is informational, never a finding by itself.

## Phase 2: Source handoff

Give the policy reviewer the supplied source manifest, URLs from changed references and
relevant PR-body citations. Raw source bytes/extracts may come from an encoding run;
reviewers independently interpret them. The same URL with different `#page` fragments
is one PDF, not several downloads; preserve HTML hash routes that identify content.
Reuse existing material before fetching anything.
The code reviewer can start immediately; it does not wait for source collection.

Without `--sources`, first try the source manifest recorded in a valid incremental
baseline or the existing `{RUN_ROOT}/{PREFIX}-review-sources.json`. Reuse only manifests
inside this worktree's evidence directories; don't follow arbitrary paths from a report.
If none is valid, start an empty manifest and acquire the necessary sources.

The policy reviewer is the sole writer of
`{RUN_ROOT}/{PREFIX}-review-sources.json`, following [source-cache.md](source-cache.md).
Validate originals by checksum and derivatives by their recorded hashes. A stale/missing
extract or page only invalidates that derivative: regenerate it from the valid original.
A changed original invalidates its extracts/pages and dependent conclusions.

For changed amounts, prioritize the cited source's exact year/table and official indexed-
limit bulletins or forms. If a general landing page lacks the amount, use the available
bounded search route for targeted official-domain queries: program + tax/benefit year +
amount, then year + indexed limits/bulletin if needed. Search results are discovery aids;
corroborate against the underlying primary document and its applicable year, units and
filing/household category. Prefer this to following adjacent generic or older guidance.
These searches consume the same two-batch limit and acquisition budget below; stop once
the fact is established. If no bounded search route is available or the budget expires,
record the missing check instead of treating the search as completed.

When an agency page is blocked, switch to the publication of record for that value (the
Federal Register or govinfo notice, the statute, the state register), not to several
neighboring URLs on the same host. An HTTP 200 response containing an access challenge
or bot check is not usable source evidence.

Read searchable text with physical page boundaries first. Use contents/headings and
cross-references to locate all provisions relevant to changed behavior, including
exceptions, effective dates and footnotes; do not stop at a matching number. Visually
inspect relevant tables, scans, footnotes or ambiguous text where layout affects meaning.
Render selected pages with `pdftoppm -f N -l N -png -r DPI`; escalate to 600 DPI when
legibility requires it. Text suffices for unambiguous prose. If a scan has no usable text,
inspect/OCR the relevant sections and expand as necessary; never claim unread provisions
were checked. There is no requirement to render every page or split agents by page count.
PDF citations use physical file pages (`#page=XX`), not printed numbers; inspect a cited
page when the locator or its evidence is uncertain. Single-page PDFs need no fragment.

Read extracts selectively: locate the relevant provisions with `grep -n` and read a
bounded window around each hit rather than printing whole documents into context; a
manual section rarely needs more than a few dozen lines. Reviewer context is finite, and
whole-document reads of two or three manuals can consume most of it.

Start a shared acquisition timer at the first new external search/fetch. Fetch every
known URL in one parallel bounded batch before reading any of them. Within
`--source-budget`, use at most two targeted search batches per material evidence gap and
two fetch attempts per URL; the second attempt must use a different route (a browser
user agent, the agency's alternate host, or a read-only text proxy), never a repeat of
the same request. On repeated blocking, 429 or an unrecoverable error, stop
that route without backoff loops. Use an already-available authoritative alternative if
it establishes the fact. No optional second-source hunt for a confirmed fact; seek more
evidence when sources conflict, authority is insufficient or changed behavior remains
unsupported. Once the budget is exhausted, finish with available evidence and list
material gaps. Do not declare unsupported behavior correct or manufacture a defect.

Give each external call a deadline no greater than 60 seconds or the remaining source
budget, whichever is smaller. For shell downloads use the bounded helper and
`curl --connect-timeout 10 --max-time SECONDS`; use tool-native deadlines when available.
Do not use a browser/MCP acquisition route that cannot be bounded or interrupted.
Stop outstanding acquisition when its budget expires. Record timeouts as evidence gaps;
never wait through minute-long backoff sleeps or keep a reviewer alive for an optional URL.

## Phase 3: Assign substantive reviewers

| Role | Scope | Output | Skills/references |
|---|---|---|---|
| policy-reviewer | Policy logic, values/dates, references and source evidence | `{RUN_ROOT}/{PREFIX}-review-policy.md`, review source manifest | Relevant country skill; policyengine-model-development parameters/variables as needed |
| code-reviewer | Implementation correctness, relevant patterns, tests and regressions | `{RUN_ROOT}/{PREFIX}-review-code.md` | policyengine-model-development tests/periods/vectorization for country models; applicable repo skills for API/frontend/infrastructure |

For policy changes, run these two roles concurrently. For pure infrastructure/API/frontend,
run code-reviewer only. Mixed PRs get both with their respective scopes. Split further
when the diff has independent large components, or when a role's inputs would exceed
its context: as a working threshold, more than about 800 diff lines or more than ten
sources for one role. Split the policy reviewer by source group and the code reviewer
by variable group; state why, partition ownership and avoid reading the same whole
program in every role. Do not spawn nested reviewers.
Load only references needed for the actual task, not every model-development document;
read a reference's relevant section, not the whole reference set.
When policy review is inapplicable, the coordinator writes an empty version-1 source
manifest and records why source checking was not requested.

Pass the exact diff/snapshot paths, PR body, current/prior artifacts, source budget,
role contract, progress-log path and output paths; send the scope brief's questions as a
follow-up message once written (a runtime that cannot message a running role includes
the brief at dispatch instead, still capped at a minute). Caller role contracts take precedence over a specialized
agent's broader standalone routine; launchers should avoid such extra routines by default.

## Phase 4: Review and substantiate findings

Policy reviewer: establish the relevant rules from official sources, then compare the
changed implementation, dates and reachable values. Check exclusions and definitions,
not just arithmetic. Source reuse is not acceptance of the implementer's conclusions.
Combine value corroboration, citation checks and code-path verification in this role;
there is no separate PDF auditor, reference checker or mandatory citation verifier.

Code reviewer: inspect behavior, entity/period/vectorization correctness and meaningful
coverage. Trace suspicious cases through dependencies. Run the changed tests and the
directly relevant regression tests in one runner invocation (pass every path to the same
command; each invocation pays the model's import cost), writing full output to a log
under `RUN_ROOT` and reading back only the summary line and failures. Add a small
reproduction when useful. If the environment is unavailable, report tests NOT RUN; do
not install dependencies or repeat a broad suite just to produce a review. Existing CI
and local tests are separate evidence. Reuse a test result only for unchanged tested
inputs/dependencies/environment; retest after changes. Check the repository's actual
changelog/format conventions, not a universal country-model template in every repo.
An existing interpreter with the snapshot on `PYTHONPATH` is acceptable when `uv run`
would install/sync dependencies. Confirm imports resolve to the snapshot. Set
`PYTHONDONTWRITEBYTECODE=1` and direct pytest's cache to an assigned path under `RUN_ROOT`
(for example, `-o cache_dir="$RUN_ROOT/$PREFIX-review-pytest-cache"`).

When the diff changes who is eligible or how much they receive, the code reviewer checks
affected cases through to the final benefit, subtraction or tax result: at least one case
per household shape the changed tests use, plus one composition those tests do not cover
(for example a second tax unit in the same SPM unit, a non-parent adult, or a swapped
member order). Use actual demographic/income inputs rather than forcing the eligibility
flag or intermediate amount. An existing test can satisfy this when it exercises that complete path; otherwise
run a focused diagnostic in the available environment. Trace remaining age, entity and
aggregation gates, including a risk of double-counting an existing benefit. The policy
reviewer establishes that the scenario qualifies under the source; share one reproduction
and its evidence rather than running it twice. If execution is unavailable, record the
unexecuted check and the limits of the code trace. Passing intermediate tests alone does
not establish that the newly eligible population receives the benefit.

When a limit or assessment unit changes, compare the legal unit with both the income
aggregation and the final eligibility unit. A test described as separate filing must
actually use separate tax units. For newly added expected amounts, derive the calculation
from the specific source steps; an existing helper's output is not an independent oracle.
Distinguish an unchanged formula defect from a new test that codifies it.

For direct model diagnostics, batch cases in one process and use the optional
period-aware helper in [automation.md](automation.md#model-diagnostics). It records explicit
input periods and named in-memory controls. An annual total and a monthly amount are
different inputs; do not silently convert one into the other. Check setup errors before
using results, and report exploratory calculations separately from passing assertions.

Each reported defect needs: file:line, triggering case/year, expected versus observed
behavior, evidence, and why this diff introduces/exposes it (or why it is in requested
full-audit scope). A value mismatch must be source-supported and output-relevant. Reuse
facts already established by either reviewer; do not re-open a page or launch a task
just because an intermediate report contains a flag. Distinguish defects, optional
improvements, and evidence gaps. Missing coverage is not proof of incorrect behavior.

A reproduction must describe a plausible, internally consistent case and a source-backed
expected result. Restoring an old formula or forcing a flag can isolate a code change;
an output difference alone does not establish which outcome is correct. State material
unmodeled conditions explicitly; a change in benefit receipt does not by itself establish
a change in the underlying status that qualified the person (for example, an SSI payment
stopping does not show that a qualifying disability ended). Discard or correct invalid
scenarios before counting findings; do not add a default validation agent for this check.

Keep role reports ready for direct consolidation: status; findings with location,
trigger, expected/observed outcome, impact and source/reproduction links; material gaps;
and a short validation/timing block. A role's status is PARTIAL whenever its gap list is
non-empty: an uncorroborated value-bearing entry (a parameter value whose cited source
could not be fetched or read), a required check not executed, or a scenario it could not
validate. Never write COMPLETE above a non-empty gap list. Record commands, test counts, start/end times and
actual source/render counts once, with raw output in linked logs. Avoid full PR metadata,
source inventories, investigation narratives and repeated scenario tables in each report.
When both reviewers establish the same defect, share the finding text and add only the
other role's evidence or disagreement. Do not duplicate its missing integration test as
a separate finding. Finish once assigned checks are complete; a larger diff can justify
more findings, not repeated boilerplate or invented statistics.

## Phase 5: Resolve material uncertainty

The coordinator reads both reports and deduplicates before requesting any more work.
Before consolidation it opens the evidence artifact of every CRITICAL once (the
reproduction output or the quoted source lines) and confirms the trigger, the expected
result and its source are all present; a CRITICAL whose evidence is missing, inconsistent
or an output difference alone is marked UNVERIFIED, which keeps its severity and forces
PARTIAL. Return a specific unresolved question to its original reviewer when that
reviewer can answer from existing evidence. Use at most one additional independent adjudication batch
for materially conflicting findings or uncertain high-impact claims; batch related items
by topic, not one agent per value. It uses the remaining acquisition budget, not a reset.
Do not reconfirm findings with adequate source and code-path evidence, or investigate
incidental pre-existing issues to complete a review of changed behavior.

If material evidence or a required review check remains unavailable, record PARTIAL.
Produce the reports promptly with those gaps; a later explicitly expanded source budget
or supplied document can resume the affected checks. Don't retry until the user answers
or pretend a timeout is evidence of correctness. There is no blanket review wall-time
limit: substantial implementation analysis may take longer than source acquisition.

## Phase 6: Consolidation

The coordinator writes both canonical outputs (required for existing callers):
`{RUN_ROOT}/{PREFIX}-review-full-report.md` and
`{RUN_ROOT}/{PREFIX}-review-summary.md`. No separate consolidation agent.

Select the strongest existing finding sections, deduplicate and reconcile severity/status.
Attach complementary evidence to the selected section once where needed; the coordinator
can merge that text without restarting a reviewer. Use the bundled
[report assembler](automation.md#report-assembly) to copy the selected sections into both
canonical reports and derive counts/severity from one list; do not hand-write a new
consolidation script per PR. Its small input records shared metadata, role completion,
finding selectors, gaps, actual validation and measured timings once. Review the generated
result for substantive accuracy; the helper checks artifacts, not legal conclusions.
If the helper is unavailable, assemble the same outputs directly with these contracts.

Keep each finding self-contained; link detailed diagnostics rather than copying them.
Local artifact links supplement, not replace, the trigger, result and primary-source
citation. Keep the run state to phase/status updates and artifact pointers. Consolidation
should not trigger new research unless Phase 5 identified a material uncertainty.

Preserve stable finding IDs C1/C2, A1/A2 and S1/S2. Incremental reviews mark prior findings
RESOLVED, STILL OPEN or UNVERIFIED (retain their previous severity until adjudicated),
retain IDs even if severity changes, and give new IDs above prior maxima. Do not count
resolved findings as open. Missing evidence never silently resolves a prior defect.

Classify confirmed findings:

- **CRITICAL (Must Fix)**: wrong policy/formulas or values affecting modeled results,
  incorrect entities/periods, hard-coded legal values, missing/non-corroborating required
  references, incorrect citations, failing relevant checks, formula variables with no
  meaningful coverage, or non-functional tests. Require concrete support for the claim.
- **SHOULD ADDRESS**: missing boundary coverage on tested behavior, maintainability or
  repo-standard issues. Missing rounding/flooring/capping is normally here unless a
  demonstrated case changes eligibility/category or materially changes results.
- **SUGGESTION**: optional readability, documentation or performance improvements.

For population-sensitive input defaults, quantify the direction/impact where supported;
do not prescribe a default merely to suppress a discrepancy. Consider data population,
documented limitations or justified defaults. Critical only with material demonstrated
impact. Treat style preferences proportionately; do not inflate small nits into defects.
Unavailable source evidence is an evidence gap, distinct from a verified wrong reference.

The full report contains Source Documents, Critical, Should Address, Suggestions,
Evidence Gaps, Validation Summary and Review Severity. Include these metadata labels:

```text
Base repository: {BASE_REPO}
PR number: {PR_NUMBER}
Reviewed head SHA: {PR_HEAD}
Merge base SHA: {MERGE_BASE}
Mode: full | incremental from {PRIOR_HEAD}
Scope: changed behavior and affected dependencies | full audit of {paths}
Source manifest: {RUN_ROOT}/{PREFIX}-review-sources.json
Review status: COMPLETE | PARTIAL
```

`Mode: full` means a fresh merge-base review rather than an incremental baseline; the
separate `Scope` field records whether the user requested the broader `--full` audit.

COMPLETE means every requested material check has an evidence-backed result, not that
there are no defects. PARTIAL means a material source or required check remains unresolved.
Explicitly skipped PDF checks stay visible in scope/limitations. Include tests passed,
failed or NOT RUN, CI status at its checked SHA, source coverage, unresolved items and
measured elapsed/agent/render/cache counts. Never conflate code inspection with executed
tests or a lack of confirmed mismatches with complete source verification.

Severity: REQUEST_CHANGES for confirmed criticals; COMMENT for nonblocking issues or
PARTIAL reviews without confirmed criticals; APPROVE only for COMPLETE reviews with no
criticals and at most minor suggestions. The summary stays concise (target 20 lines) and
starts with three labeled lines that callers parse: `Review status: COMPLETE | PARTIAL`,
`Review severity: ...` and `Still-open critical count: N`; then other counts, material
gaps, actual validation, metrics and full report path. Report gaps even if the critical count is zero. Output-file
existence alone is not a clean-review gate for a calling encoding workflow.

For timed runs, record the canonical keys in the assembler's `timing` block so runs stay
comparable: `setup_seconds` (capture through snapshot), `scope_seconds`,
`parallel_review_seconds` (dispatch to last role completion), `policy_role_seconds`,
`code_role_seconds`, `adjudication_seconds`, `consolidation_cleanup_seconds` and
`elapsed_seconds`; distinguish setup, overlapping role wall time and consolidation/cleanup;
do not add concurrent role durations. Record CLI wall time separately from test-reported
time, and source acquisition window separately from time inside network calls. These
differences are not pure import or network-latency measurements. A few diagnosed cases
do not establish review recall; record confirmed misses or false positives without
claiming all defects were found. After cleanup, finalize timings and rerun the assembler
with the same selectors if needed; this is bookkeeping, not a new review pass.

When maintaining this workflow, use [real PR benchmarks](benchmark.md) to assess review
quality and runtime. Helper tests protect mechanical contracts only; their pass count
does not validate findings, source interpretation, scenario plausibility or efficiency.
Benchmarking is a maintainer activity, not an additional stage in every review.

## Phase 7: Display or post and clean up

Phase 6 consolidation is required before displaying or posting findings. Local flags
mean display only. Otherwise follow existing explicit posting authorization; if none
exists, present the completed report and ask whether to post it. Do not ask again when
the user already decided. Post from the report file, scoped to `BASE_REPO`:

```bash
gh pr comment "$PR_NUMBER" --repo "$BASE_REPO" --body-file "$RUN_ROOT/${PREFIX}-review-full-report.md"
```

Finally, on success or failure, remove only the exact snapshot recorded as created by this
invocation, after its reviewers have finished:

```bash
git -C "$WORKTREE_ROOT" worktree remove "$SNAPSHOT"
```

If removal fails, preserve the directory and report its path/error; no forced removal or
recursive-deletion fallback. Keep reports and valid evidence cached. End with status,
important findings/gaps and the report path; fixes belong to fix-pr or the encoding caller.
