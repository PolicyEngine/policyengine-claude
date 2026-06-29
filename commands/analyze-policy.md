# Analyze Policy

End-to-end policy analysis pipeline. Takes a reform (bill number, URL, or description), classifies whether it's modelable, finds prior PE scores, runs the microsim, compares to priors, and — if the run mismatches — diagnoses which calibration target is likely driving the gap.

The structured analogue of `/encode-policy-v2` for the analyst persona: less about implementing new programs, more about running impact analysis on a proposed reform and validating it against PolicyEngine's published baseline.

## Arguments
- `$ARGUMENTS` — One of:
  - State + bill number: `UT SB60`, `RI H7127`
  - Federal bill: `US HR1234` or `US S5678`
  - URL: a direct bill/proposal/order URL
  - Description: natural-language reform (`"ARPA-style federal CTC expansion: $3,600/$3,000, full refundability"`)

Flags:
- `--country {us|uk|ca}` (default `us`)
- `--year YYYY` (default current year)
- `--mode {api|local}` (default `api` for microsim execution)
- `--skip-microsim` (process-test mode — stops at Stage 5, predicts from prior anchor)
- `--auto-investigate` (if Stage 5 returns INVESTIGATE, auto-run top calibration hypothesis)
- `--write-report PATH` (default `/tmp/analyze-policy-{policy_id}.md`)
- `--log-to <dest>[,<dest>...]` (override auto-routing; see Phase 8). Examples: `--log-to archive`, `--log-to "archive,issue:policyengine-us-data"`, `--log-to draft:policyengine-analysis/posts/arpa-ctc.md`
- `--no-log` (skip Phase 8 entirely — write the `/tmp` report only)
- `--auto-confirm` (skip confirmation prompts before opening GitHub issues; only honor in non-interactive contexts)

## Workflow

```
┌──────────────────────────────────────────────────────────────────────┐
│  /analyze-policy <reform>                                            │
└──────────────────────────────────────────────────────────────────────┘
       │
       ▼
┌──────────────────┐         Stage 1: Understand
│ policy-text-     │  ───►   Fetch text, extract provisions
│ researcher       │
└──────────────────┘
       │ provisions[]
       ▼
┌──────────────────┐         Stage 2a: Map provisions to parameters
│ parameter-       │  ───►   YAML paths + reform-dict snippets + verdicts
│ locator          │
└──────────────────┘
       │ verdicts[]
       ▼
┌──────────────────┐         Stage 2b: Classify
│ reform-          │  ───►   parametric | structural | not-possible
│ classifier       │
└──────────────────┘
       │
       ├── structural ──► write backlog issue, STOP
       ├── not-possible ──► write rationale, STOP
       │
       ▼ parametric
┌──────────────────┐         Stage 3: Find anchors
│ prior-scores-    │  ───►   PE prior scores + fiscal notes + think-tanks
│ finder           │
└──────────────────┘
       │ anchors[]
       ▼
┌──────────────────┐         Stage 4: Run microsim
│ microsim-runner  │  ───►   Budget, poverty, distribution, geography
└──────────────────┘
       │ result            (or skip if --skip-microsim, predict from anchor)
       ▼
┌──────────────────┐         Stage 5: Compare
│ reform-          │  ───►   PASS | PASS-WITH-NOTES | INVESTIGATE
│ comparator       │
└──────────────────┘
       │
       ├── PASS ──► write report, EXIT
       │
       ├── PASS-WITH-NOTES (or near-INVESTIGATE on external benchmarks)
       │      │
       │      ▼ trigger Stage 5.5
       │   ┌──────────────────┐         Stage 5.5: Corroborate
       │   │ model-           │  ───►   Run external mirror-shape reforms
       │   │ corroborator     │         through our model; check agreement
       │   └──────────────────┘
       │      │
       │      ├── CORROBORATED ──► upgrade verdict to PASS-WITH-CORROBORATION
       │      ├── PARTIAL ─────► stay at PASS-WITH-NOTES
       │      └── FAILED ──────► escalate to INVESTIGATE
       │
       ▼ INVESTIGATE
┌──────────────────┐         Stage 6: Diagnose
│ calibration-     │  ───►   Ranked hypotheses + tests to run
│ diagnostics      │
└──────────────────┘
       │
       ▼
┌──────────────────┐
│ reform-describer │  ───►   Mechanical write-up (provisions table)
└──────────────────┘
       │
       ▼ final report at --write-report path
```

## Phase 1 — Understand the policy

Parse `$ARGUMENTS` to determine input type. Invoke `policy-text-researcher`:

```
policy-text-researcher input={
  state: <state>, bill_number: <bill>, |
  bill_url: <url>, |
  description: <description>
}
country=<country>
```

Returns `provisions[]`. If empty (couldn't fetch text), STOP and report.

## Phase 2 — Classify modelability

For each provision in parallel, invoke `parameter-locator`. Collect verdicts. Then invoke `reform-classifier`:

```
reform-classifier
  provisions=<provisions>
  parameter_locator_verdicts=<verdicts>
  jurisdiction=<jurisdiction>
```

Branch on `classification`:
- **`not-possible`** — write `/tmp/{policy_id}-not-modelable.md` with rationale. EXIT.
- **`structural`** — write `/tmp/{policy_id}-structural-backlog.md` with the model-change estimate. Optionally open a GitHub issue against `policyengine-{country}` if `--open-issue`. EXIT.
- **`parametric`** — proceed.

Capture `reform_dict` from the classifier output.

## Phase 3 — Find anchor scores

Invoke `prior-scores-finder` (loads the `policyengine-prior-scores` skill internally):

```
prior-scores-finder
  reform=<provisions+description>
  jurisdiction=<jurisdiction>
```

Returns `anchors[]`. If empty, surface "novel reform — no PE prior found" in the final report. The comparison will rely on fiscal notes / think-tank scores.

## Phase 4 — Run the microsim

If `--skip-microsim` is set, **skip this phase** — Stage 5 will use the anchor as a predicted result. Otherwise invoke `microsim-runner`:

```
microsim-runner
  reform_dict=<reform_dict>
  jurisdiction=<jurisdiction>
  year=<year>
  mode=<mode>
```

Returns `result`. If `mode=local`, this may take 5-10 minutes per run.

## Phase 5 — Compare to anchor

Invoke `reform-comparator`:

```
reform-comparator
  microsim_result=<result>  // or null if --skip-microsim
  prior_anchor=<anchors[anchors.preferred_anchor_index]>
```

Returns `verdict`:
- **`PASS`** / **`PASS-WITH-NOTES`** — proceed to write-up.
- **`INVESTIGATE`** — invoke `calibration-diagnostics` with the deviation signature.

The comparator itself may invoke `model-corroborator` (Stage 5.5) at the end of its Step 2b if external benchmarks don't directly anchor the reform — see Phase 5.5 below.

## Phase 5.5 (conditional) — Model corroboration

Triggered automatically by `reform-comparator` Step 2c when Step 2b yields fewer than 2 external sources within ±25%. Invoke `model-corroborator`:

```
model-corroborator
  our_reform_dict=<reform_dict>
  our_jurisdiction=<jurisdiction>
  benchmark_sources=<thinktank_scores from prior-scores-finder>
  our_microsim_result=<result>
  our_baseline_policy_id=<typically 2 for US>
```

The corroborator picks 1-2 closest-shape externally-scored reforms, builds mirror reform-dicts (and a baseline policy if the external source uses a different baseline schedule like TCJA-extension), submits to the PE API, polls for completion (~6-10 min per mirror in parallel), and reports per-candidate agreement.

Outcomes:
- **`CORROBORATED`** (≥2 candidates within ±25%) — comparator upgrades verdict to `PASS-WITH-CORROBORATION`.
- **`PARTIAL-CORROBORATION`** (1 corroborated with explainable drift on others) — stay at PASS-WITH-NOTES.
- **`CORROBORATION-FAILED`** (0 candidates corroborated) — force escalation to INVESTIGATE.
- **`NO-CORROBORATION-POSSIBLE`** (no suitable candidates) — fall back to Step 2b verdict.

Skipped when `--skip-microsim` is set (no original-reform microsim to anchor against).

## Phase 6 (conditional) — Calibration diagnosis

Only if Stage 5 returned `INVESTIGATE`. Invoke `calibration-diagnostics`:

```
calibration-diagnostics
  deviation_signature=<comparator.deviation_signature>
  reform=<provisions+reform_dict>
  jurisdiction=<jurisdiction>
  anchor=<chosen anchor>
```

Returns ranked hypothesis list + recommended next test.

If `--auto-investigate` is set, automatically run the top hypothesis (e.g., perturb takeup rate, rerun microsim, recompute comparison). Otherwise just append to the report.

## Phase 8 — Log the report (NEW)

After Phase 7 has assembled the report at `--write-report PATH`, invoke `report-logger`:

```
report-logger
  report_path=<write-report path>
  frontmatter=<structured metadata from prior stages>
  log_to=<--log-to value, or empty for auto-routing>
  no_log=<--no-log flag>
  command_args=<original $ARGUMENTS>
```

**Destination routing — runtime prompt, context-aware** (when no `--log-to` and no `--no-log` and no `--auto-confirm`):

The logger detects the current repo, surfaces a shortlist tailored to the context, and asks the analyst to pick. Pre-selected defaults by verdict:

| Verdict | Pre-selected |
|---|---|
| `PASS` / `PASS-WITH-NOTES` / `PASS-WITH-CORROBORATION` | local archive only |
| `INVESTIGATE` | local archive + GH issue in `policyengine-{country}-data` |
| `structural` | local archive + GH issue in `policyengine-{country}` |
| `not-possible` / `deployed-model-lag` | local archive only |

Context-specific additions surfaced in the prompt:
- Inside `policyengine-app` repo → "Save as draft research post: `src/posts/articles/{slug}.md` + update `posts.json`"
- Inside any PE repo → corresponding `gh issue` option
- Always available → "Custom path / repo — type a destination spec"

All non-local destinations get a body preview before submission (skip with `--auto-confirm`).

**Archive path resolution** (matters for plugin installations):
1. Explicit `--log-to archive:<path>` wins
2. Else `$PWD/analyses/` if it exists
3. Else `$POLICYENGINE_ANALYSES_DIR` env var
4. Else `~/.policyengine/analyses/` (auto-created)

**Issue creation** opens a GitHub issue via `gh issue create` with a verdict-shaped body. Confirms before opening unless `--auto-confirm`. Issue numbers are appended to the archive's `issues_opened` frontmatter so the analysis archive is the source of truth for "what action items did this produce."

The Phase 8 step also prints the destination summary to the user as the final output:

```
[/analyze-policy] Run complete.
  Archive: ~/.policyengine/analyses/2026-06-19-us-arpa-ctc-restoration.md
  Issues opened: (none — verdict was PASS-WITH-NOTES)
  Run-id: 97759
```

## Phase 7 — Write report

Invoke `reform-describer` for the mechanical provisions write-up. Assemble the final report at `--write-report` PATH:

```markdown
# Analysis: <reform title>

## Reform
<reform-describer output: description + provisions table>

## Classification
**Verdict:** parametric (high confidence)
**Reform dict:** ```json {reform_dict} ```

## Prior anchors
| Prior | Year | Cost | Poverty Δ | URL |
|---|---|---|---|---|
| Restoration of ARPA CTC | 2023 | $100B/yr | -37% child | ... |

## Our microsim result
| Metric | Value |
|---|---|
| 10yr cost | $1,450B |
| Child poverty Δ | -34.1% |
| ... | ... |

## Comparison
**Verdict:** PASS
Headline metrics within tolerance band. See normalization notes.

## (if INVESTIGATE) Calibration diagnosis
**Top hypothesis:** Non-filer CTC takeup
**Test:** Set takeup=0.95 and rerun
**Open issues:** ...

## Methodology
- Microsim mode: api
- Year: 2026
- Dataset: Enhanced CPS
- Static analysis (no behavioral response)
```

## Stages can run independently

For debugging or partial-run scenarios:
- `--only-classify` — runs Phases 1-2 only.
- `--from-anchor` — skip Phases 1-2, accept a pre-built `reform_dict`, start at Phase 3.
- `--no-write-report` — return the structured JSON instead of writing markdown.

## Hand-off to the legislative tracker

The state-legislative-tracker's `/encode-bill` command is a superset of `/analyze-policy` that ALSO writes results to Supabase. Use `/encode-bill` instead when working inside that repo.

## Related commands

- `/encode-policy-v2` — implements a NEW benefit program (orchestrates rules-engineer, test-creator, etc.). `/analyze-policy` analyzes an existing-or-near-existing reform.
- `/review-program` — audits an existing PR.
- `/score-bill` — the legislative-tracker variant focused on bills.

## Skills loaded

This command loads (with their plugin paths for clarity):
- `policyengine-{country}` (US/UK/CA) at `skills/domain-knowledge/policyengine-{country}-skill/` — country model knowledge
- `policyengine-prior-scores` at `skills/domain-knowledge/policyengine-prior-scores-skill/` — anchor index
- `policyengine-calibration-diagnostics` at `skills/domain-knowledge/policyengine-calibration-diagnostics-skill/` — sensitivity registry
- `policyengine-microsimulation` at `skills/tools-and-apis/policyengine-microsimulation-skill/` — execution patterns
- `policyengine-research-lookup` at `skills/documentation/policyengine-research-lookup-skill/` — broader research discovery
- `policyengine-writing` at `skills/documentation/policyengine-writing-skill/` — style for the final report

## Agents invoked

1. `policy-text-researcher`
2. `parameter-locator` (per-provision, parallel)
3. `reform-classifier`
4. `prior-scores-finder`
5. `microsim-runner` (unless `--skip-microsim`)
6. `reform-comparator`
7. `model-corroborator` (Stage 5.5 — only when no exact-shape external comparator exists; skipped on `--skip-microsim`)
8. `calibration-diagnostics` (only if Stage 5 INVESTIGATE)
9. `reform-describer`
10. `report-logger` (unless `--no-log`)
