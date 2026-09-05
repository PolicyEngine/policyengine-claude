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
