# Evaluating workflow changes on real PRs

For maintainers changing review-program, not for reviewers during an ordinary run.
The acceptance evidence for review behavior is a real PR run. Python tests are a separate
check of the helpers: commit isolation, subprocess termination, evidence integrity, and
the report status consumed by encode-policy-v2. They cannot establish policy accuracy.

## Run and assess

Choose a real PR that exercises the behavior being changed. Record the repository,
captured head and merge base, workflow revision (and local diff if uncommitted), source
cache state/budget, and available model environment. Keep reviews local unless posting
is explicitly authorized. A changed remote PR head is a different benchmark input.

Run the actual workflow through review, consolidation and cleanup. Give reviewers the
PR and primary evidence, without prior findings or expected answers. For an agent-based
evaluation, use a fresh context. An artifact replay measures helper performance only;
it does not count as a new workflow review.

After completion, assess the findings against the code, primary sources and plausible
inputs. Record:

- Confirmed defects and material misses, including the final affected result.
- False positives, withdrawn findings and unsupported assumptions.
- Evidence gaps and checks not executed, even when no defects were found.
- End-to-end time and where it went: overlapping reviewer work, source acquisition,
  test execution/startup, duplicated work, consolidation and cleanup.

Keep raw reports and timings under RUN_ROOT. Record corrections alongside the original
result so a fast run with an invalid finding is not presented as a success. A passing
test suite or a previous review is not the expected-policy oracle. Known findings are
useful checks, not proof that every remaining defect has been found.

Compare workflow versions on the same captured code with comparable environment and
cache conditions before claiming a speed improvement. Assess the changed behavior,
not a fixed number of PRs or a growing mandatory scenario matrix. If no such run has
been completed, label the behavior/runtime effect **not yet benchmarked**.

## Existing real-run evidence

These are historical observations, not a controlled before/after comparison. They used
different PRs and workflow revisions. Preserve their original local reports when reusing
them; do not supply this evaluator table to a reviewer as an answer key.

| PR / captured head | What the experiment established | Recorded active runtime |
|---|---|---|
| PolicyEngine/policyengine-us #9393 / `4a94246b54496ff79588d2c1ea1cf5064f058122` | Intermediate retirement eligibility did not reach the final subtraction; exact indexed-cap evidence remained a gap. | 10m56s |
| PolicyEngine/policyengine-us #9345 / `857d7c76e5074961cce13bb04462f84fb6b263ee` | The SSI cash-cessation finding was withdrawn: its inputs did not establish that disability ceased. This is a false-positive example, not a defect to rediscover. | 10m36s, excluding later correction |
| PolicyEngine/policyengine-us #9379 / `e1b168d7d1ef3ffc52442ec511cef11765751afe` | Final eligibility checks found the omitted student exclusion and mismatched couple income unit despite passing changed tests. | 9m49s |

Reassembling #9379's saved report in approximately 0.05s validated the assembler's
mechanics. It did not measure the time to choose findings or establish their correctness.
The current local orchestration edits need their own real-run evidence.

## MO LIHEAP workflow correction, September 2026

The local encoding benchmark at `8a084efa3d948585786a4e13b368ac594942548c`
used the PR #88 workflow plus local-diff and skill-loading changes. Its two reviews
took approximately 30m21s and 26m06s after subtracting long event gaps correlated with
machine sleep (actual wall times 78m09s and 42m39s). Individual reviewers took 9–14
minutes; setup, staggered dispatch and roughly nine minutes of post-reviewer work
accounted for the rest. These adjusted times are estimates, not active-compute measurements.

The run exposed duplicate skill/command entrypoints, verbose report reconciliation,
unverified applicant premises counted as critical, and ordinary limitations classified
as missing required checks. The subsequent workflow correction has this bounded evidence:

- A fresh native Claude entrypoint smoke test loaded both real skills and their canonical
  paths in 23.8s, with no compatibility stub or recursive invocation.
- Replaying the existing MO reports through the assembler took 0.05–0.08s and produced
  a 20-line summary while preserving full evidence. Marking C3 UNVERIFIED excluded it
  from `confirmed_critical_ids` without dropping it from total open findings.
- A fresh context loaded review-program and model-development and evaluated C3 from
  the existing claim, primary-source excerpt and recorded diagnostic inputs/outputs.
  In 76.1s it rejected automatic repair because the applicant premise was unestablished.
  It also volunteered unsupported side remarks about the senior branch and proposed
  fallback. Those remarks were rejected, and the adjudication instruction was narrowed
  afterwards. An earlier packet accidentally omitted relevant evidence and is excluded
  from acceptance evidence.

These checks validate entrypoint resolution, assembly mechanics and one bounded
scenario decision. They do **not** establish full-review accuracy, successful parallel
dispatch under load, or a new end-to-end runtime. The final narrowed adjudication wording
and overall latency still need the next real-PR benchmark. Do not report replay time as
review time or this scenario check as a third MO review.

## MO LIHEAP v3 integrated run

The next local run used workflow `2e35b26` and implementation head
`71731ce7625ebff39aad0982900b57745712de3c`. Its first encode-to-review interval was
**30m50s** from caller phase markers. Policy and code roles took 10m05s and 13m30s
concurrently; the review coordinator's post-role adjudication span was 11m13s, including
an operator pause/resume to correct its missing model-development load. The coordinator
also investigated historical sources; the encoder then verified findings again before
dispatching fixes. The report's earlier ~28-minute figure omitted part of the caller
handoff and was recorded before cleanup finished. Use final runtime markers instead.

This was an interrupted benchmark, with two earlier CLI lifecycle failures outside that
review interval. It does not demonstrate unattended completion or a speed improvement.
The resulting simplification removes routine coordinator revalidation and encoder
re-adjudication, retaining targeted resolution of concrete conflicts. Its end-to-end
runtime was subsequently measured below; packaging tests cannot establish that it meets
the 10–15 minute target.

## MO LIHEAP v4 bounded handoff

The same initial implementation head and ten original sources, without prior findings,
were reviewed using `2e35b26` plus the local ownership/formatting changes (patch SHA256
`82abf245d7051b8c15d6135b1089cdf883adae426697c2aa9adbbaeb50a66b07`). The actual
encode Phase 6 invocation stopped after accepting the first review, before repairs.
Caller review time was **28m29s**; the entire CLI invocation took **31m25s**. Policy and
code Agent lifetimes were 9m38s and 15m43s concurrently. Marked adjudication took 4m13s,
assembly/cleanup 2m10s, and subsequent reporting/return/acceptance another 2m05s.

All four model-working contexts returned their own model-development Skill bodies.
The run was uninterrupted, but still missed the timing target. The code reviewer lost
the first 107-case suite's exit status through shell backgrounding, then repeated the
unchanged suite solely to capture it. The coordinator sent two concrete conflicts to the
original policy reviewer, but subsequently reopened code and a source page beyond those
questions. The no-routine-revalidation instruction was therefore not fully followed.

The result was PARTIAL with three confirmed critical IDs; these dispositions have no
independent correctness score. V3 required operator recovery, V4 used a fresh native
session, and machine load was uncontrolled. The elapsed difference is not a controlled
speed gain. This run establishes remaining overhead, not a solved performance problem.

## MO LIHEAP v5 two-review gate

The next frozen candidate removed the adapter's contradictory requirement to reopen
every critical's evidence, shortened reviewer prompts, replaced diagnostic quotas with
coverage-driven checks, and retained subprocess exit status. On the same initial head,
the first caller review interval was **18m39s**; complete CLI wall time was **21m31s**.
Policy/code Agent lifetimes were 8m33s/10m57s concurrently. One named clarification took
1m26s overall and assembly/cleanup took 2m17s. The 107-case suite ran once successfully;
an unsupported command separator was corrected before that execution.

The workflow stopped after zero returned confirmed criticals, exercising the early-stop
condition rather than forcing two reviews. However, a finding described wrong eligibility
and payment while assigning noncritical severity because of the small population. That
is inconsistent with the severity rubric and undermines the repair gate. The subsequent
severity clarification was not in this candidate. First-round timing is established;
review quality and the conditional second-round runtime still require validation.

## MO LIHEAP v6 interrupted two-round benchmark

Workflow `2e35b26` plus the frozen local patch (SHA256
`607240a5fd1dbd0b4d0250e7aa2a121f2e4337a00c7e364dd187968c9caa3114`) ran the actual
Phase 6 with conditional repair on the same initial head `71731ce7`. Round 1 took
**21m30s** from caller dispatch to accepted result (reviewers 13m47s concurrently; one
two-question clarification 1m56s) and returned PARTIAL with two confirmed criticals. The
repair batch took **23m42s**: the implementer finished in 4m14s, but the two repair briefs
placed the child-support deduction in different variables, so three test cases failed, the
coordinator ruled, the test author relocated them and re-ran every file, and the program
suite executed about three times over. Roughly 13 of those 24 minutes were runner time,
including one per-file loop killed by the default two-minute tool limit. The incremental
round 2 was interrupted after 11m54s when its code reviewer spawned an Explore agent for
dependency tracing without a model-development load. The two-round timing objective is
therefore not established. The `review-worker` and `model-worker` profiles, the shared
contract block and the single-self-check test rule were added afterwards and have no
native run yet.

## Kansas LIEAP local encode run

The same workflow revision ran end to end in `--local` mode on a new program (Kansas
LIEAP: 15 variables, 11 parameters including two 320-cell benefit matrices, 131 tests).
Total wall time was **66m00s**, active time 59m00s after excluding a 7m00s user wait on
four batched scope questions: setup 1.7 min, research 6.8 (network window 4.6), spec and
scope 1.8, implementation 16.1 concurrent with test authoring 19.0, validation with two
repair batches 8.7 (three runner invocations, 2.6 min), commit 0.1, and review 22.1 from
dispatch to accepted result (reviewers 15.2 concurrently). The review returned COMPLETE
with zero confirmed criticals, so no second round ran. All five model-working contexts had
transcript-verified Skill loads. Both coordinators received a compatibility stub from an
older session registry and read the canonical files instead, and the nested review
coordinator lost about two minutes to two rejected named dispatches before omitting the
`name` parameter. Neither reviewer delegated. This establishes a complete local encode
under the workflow, not a controlled comparison with the MO runs, which used a different
program, model and machine state.
