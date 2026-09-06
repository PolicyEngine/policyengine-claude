# Review automation

Read the relevant section when running diagnostics or consolidating reports. These
helpers are local-only: neither changes source nor posts a review.

## Report assembly

After role completion and deduplication, write `{PREFIX}-review-assembly.json` under
`RUN_ROOT`. Select exact Markdown headings from the completed role reports; the helper
copies their bodies, including nested headings and code, without rewriting findings.
Use a selector's optional `addendum` for complementary evidence or an adjudication note;
leave the original role report intact. Role-local labels avoid concurrent ID collisions.

```json
{
  "version": 1,
  "metadata": {
    "repository": "PolicyEngine/policyengine-us",
    "pr_number": 9379,
    "head": "captured head SHA",
    "merge_base": "captured merge-base SHA",
    "mode": "full",
    "scope": "changed behavior and affected dependencies",
    "worktree_root": "/absolute/original/worktree"
  },
  "status": "COMPLETE",
  "roles": [
    {"path": "pr-9379-review-code.md", "status": "DONE"},
    {"path": "pr-9379-review-policy.md", "status": "DONE"}
  ],
  "source_manifest": "pr-9379-review-sources.json",
  "findings": [
    {
      "severity": "critical",
      "status": "OPEN",
      "path": "pr-9379-review-code.md",
      "heading": "code-1 — Exact existing finding title"
    }
  ],
  "gaps": [],
  "notes": ["Observations that are neither defects nor gaps, for example a modeled default that masks the change."],
  "validation": "Actual tests, CI with checked head, source/render counts and limitations; link raw logs. Use NOT RUN when appropriate.",
  "timing": {"elapsed_seconds": 589.24, "setup_seconds": 29.57}
}
```

Replace example data with measured values; omit `timing` when not measured. When
present, `timing` uses the canonical keys from workflow Phase 6 (`setup_seconds`,
`scope_seconds`, `parallel_review_seconds`, `policy_role_seconds`, `code_role_seconds`,
`adjudication_seconds`, `consolidation_cleanup_seconds`, `elapsed_seconds`) and must
include `elapsed_seconds`. `notes` is optional, renders under a Notes heading, and never
affects status or severity. The summary begins with `Review status`, `Review severity`
and `Still-open critical count` lines for calling workflows. Keep
`validation` concise. The helper limits the summary to five finding titles and two gaps,
with counts and links to the full report; complete evidence and notes remain in the full
report. Paths are absolute or relative to
`RUN_ROOT`, including local links inside the selected Markdown. Both canonical reports
remain in that directory. Role status is `DONE` or `PARTIAL`; a failed role must have its
recovered report and missing checks recorded before assembly, not fabricated completion.

Finding severities: `critical`, `should_address`, `suggestion`. States: `OPEN`, `STILL OPEN`,
`RESOLVED`, `UNVERIFIED`, `WITHDRAWN`. Keep established IDs after severity changes.
For new findings, omit `id`: the helper assigns C/A/S IDs above every explicit and
`reserved_ids` value. On incremental runs, set `reserved_ids` to all IDs in the preserved
baseline, including resolved/withdrawn ones. Set `prior_reports` to the preserved baseline
paths and select unaffected findings directly from them with their existing `id` and
explicit current `status`; no copied carry-forward section is needed in a new role report.
The coordinator verifies baseline identity/ancestry and whether the diff affects each
carried finding before using these selectors. The helper does not infer that validity.
Resolved/withdrawn findings remain visible in the full report but leave the open counts.
Gaps, partial roles, or unverified findings force PARTIAL. Confirmed open criticals require
REQUEST_CHANGES; an unverified claim alone does not. Never infer source completeness from
an empty gap list or a successful assembly operation.
Use `gaps` only for unresolved required material checks. Use `notes` for optional coverage,
reused tests and other limitations; notes do not force PARTIAL. The result JSON preserves
total open `counts` for compatibility, but `confirmed_critical_ids` and
`confirmed_critical_count` exclude UNVERIFIED, RESOLVED and WITHDRAWN findings. Encoding
repair dispatch consumes those confirmed IDs. This classification reflects the reviewers'
evidence assessment; the helper cannot certify scenario premises or legal correctness.

```bash
python3 "$REVIEW_SKILL_ROOT/scripts/assemble_review.py" \
  --input "$RUN_ROOT/${PREFIX}-review-assembly.json" \
  --run-root "$RUN_ROOT" --prefix "$PREFIX"
```

Outputs: `{PREFIX}-review-full-report.md`, `{PREFIX}-review-summary.md`, and
`{PREFIX}-review-result.json` (derived status/counts and source integrity results).
The helper rejects duplicate IDs, incomplete role files, ambiguous/missing headings,
and paths outside this run directory. It rechecks source integrity locally and stops on
stale evidence; repair the manifest and reassess dependent findings before assembly.
Byte integrity does not validate policy.
It does not fetch sources, re-run tests, infer role completion or remove snapshots.
Rerunning after finalizing timing replaces only these three generated outputs; preserve
an incremental baseline first as required by Phase 0.

## Model diagnostics

Use the available country-model interpreter, with the captured snapshot on `PYTHONPATH`
and `PYTHONDONTWRITEBYTECODE=1`. Put the script/output under `RUN_ROOT`. Import
`review_diagnostics` from the installed skill's `scripts` directory. Import the model
once and batch related scenarios; the helper verifies its path is inside `SNAPSHOT`.

```python
import sys
from pathlib import Path

sys.path.insert(0, str(Path(REVIEW_SKILL_ROOT) / "scripts"))
from review_diagnostics import run_cases
import policyengine_us

cases = [{
    "name": "Continuing recipient — current formula",
    "period": "2026",
    "conditions": ["Document actual qualifying enrollment and policy conditions here."],
    "situation": {
        "people": {"person": {
            "age": 40,
            "ssi": {"2026": {"annual_total": 2238}}
        }},
        "households": {"household": {"members": ["person"], "state_code": "MO"}}
    },
    "outputs": {"ssi": "2026-01"}
}]
result = run_cases(policyengine_us, cases, snapshot=Path(SNAPSHOT),
                   output=Path(RUN_ROOT) / f"{PREFIX}-diagnostics.json")
assert result["errors"] == 0, "Inspect failed diagnostic setup/calculations"
```

The example illustrates period handling, not a complete policy scenario. Annual
variables accept scalars at the case's default period. Monthly variables require explicit
month keys or an explicit expansion under a year key: `annual_total` divides a numeric
total into twelve equal months; `monthly_value` repeats that value each month. For an
uneven receipt history, give actual monthly values. Ambiguous year inputs and overlapping
monthly schedules fail instead of silently overriding or guessing. Entity membership is
preserved; declare marital/tax units appropriate to the scenario yourself.

For regression isolation, optionally pass `controls={"prior_income_limit": PriorLimitReform}`
and select `"control": "prior_income_limit"` on that case. Construct the Reform from the
captured base formula in memory; the helper does not edit files or import arbitrary
control scripts. Use descriptive names for the exact formula being reverted.

The JSON records raw/normalized inputs, scenario conditions, named control, requested
output periods, errors and timings. `CALCULATED` means execution completed, not that a
case is legally plausible or its output correct. The caller still validates the scenario
and expected result with source evidence. One faulty case is retained as ERROR while
other cases run; never count it as a passing diagnostic. Timing begins after the caller's
model import; measure the whole command separately when benchmarking startup cost.
