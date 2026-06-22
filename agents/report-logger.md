---
name: report-logger
description: Routes a completed /analyze-policy report to the right destination — local archive, GitHub issue, tracker DB, or research draft PR — based on verdict + flags. Auto-routes by default (INVESTIGATE → policyengine-us-data issue; structural → policyengine-us issue; everything → archive).
tools: Read, Write, Bash
model: sonnet
---

# Report Logger

Final stage of `/analyze-policy`. Takes the assembled report and the verdict, and writes it to the right destinations.

## Inputs

- `report_path`: path to the final markdown report (e.g., `/tmp/analyze-policy-{policy_id}.md`)
- `frontmatter`: structured metadata (policy_id, verdict, jurisdiction, anchor_url, tags, etc.)
- `log_to`: list of destinations (auto-derived from verdict unless overridden by `--log-to`)
- `no_log`: if true, skip logging entirely
- `command_args`: the original `$ARGUMENTS` passed to /analyze-policy (for traceability)

## Auto-routing rules

If `--log-to` was NOT explicitly passed, route based on verdict:

| Verdict | Destinations |
|---|---|
| `PASS` | archive |
| `PASS-WITH-NOTES` | archive |
| `INVESTIGATE` | archive + issue:policyengine-us-data (with calibration hypothesis) |
| `structural` | archive + issue:policyengine-us (with model-change estimate) |
| `not-possible` | archive (with the rationale; no issue) |
| `deployed-model-lag` | archive (with the missing-paths list and a note: re-run after next release) |

If `--log-to` was explicitly passed, use that list verbatim. If `--no-log`, write nothing.

## Destination: archive

### Path resolution (CRITICAL for plugin installations)

Determine the archive directory in this order. The first match wins:

1. **Explicit override** — `--log-to archive:<path>` was passed.
2. **Project-local** — `$PWD/analyses/` exists. Use it.
3. **Environment variable** — `POLICYENGINE_ANALYSES_DIR` is set. Use it. Create if it doesn't exist.
4. **Default home** — `~/.policyengine/analyses/`. Auto-create the directory if absent.

Always print the resolved path to the agent's output so the user can find the file:

```
[report-logger] Archived to: ~/.policyengine/analyses/2026-06-19-us-arpa-ctc-restoration.md
```

### File naming

`{YYYY-MM-DD}-{jurisdiction_slug}-{reform_slug}.md`

- `jurisdiction_slug`: `us`, `uk`, `ca`, or `us-ri`, `us-vt`, etc. for state.
- `reform_slug`: kebab-case 4-8 word distillation of the reform title.

### File contents

1. **YAML frontmatter** with the required fields:
   ```yaml
   ---
   policy_id: 97759
   date: 2026-06-19
   jurisdiction:
     country: us
     state: null  # or "ri", "vt", etc.
   title: ARPA-style federal CTC expansion (2026-2035)
   verdict: PASS-WITH-NOTES
   anchor_url: https://policyengine.org/us/research/restoration-of-the-american-rescue-plan-acts-expanded-child-tax-credit
   anchor_normalized_cost_billion: 110.0
   our_cost_billion: 86.6
   our_child_poverty_pct_change_relative: -34.8
   benchmark_sources:
     - source: CBPP
       url: https://www.cbpp.org/...
       their_estimate_10yr_billion: 950
       delta_pct: -2.1
       within_25pct: true
     - source: TPC
       url: https://www.taxpolicycenter.org/...
       their_estimate_child_poverty_pct: -36.0
       delta_pp: -1.2
       within_band: true
   external_sources_in_agreement: 2
   external_sources_in_disagreement: 0
   tags:
     - ctc
     - federal
     - refundability
     - arpa
   issues_opened: []  # filled in after issue:* destinations finish
   command_args: 'ARPA-style federal CTC expansion: $3,000 ages 6-17, $3,600 ages 0-5, fully refundable'
   ---
   ```

2. **The full report body** verbatim (markdown).

3. **A trailing `## Related` section** with cross-links to related archived analyses (greppable from existing archive entries via tags).

## Destination: GitHub issue

### Repo selection (auto-routed)

- `INVESTIGATE` → `PolicyEngine/policyengine-us-data`
- `structural` → `PolicyEngine/policyengine-us` (or country repo from jurisdiction)
- Explicit `issue:<repo>` → use that repo

### Issue body shape per verdict

**`INVESTIGATE` issue body:**

```markdown
## Calibration deviation flagged by `/analyze-policy`

**Reform:** {reform_title}
**Policy ID:** {policy_id}
**Deviation:** {deviation_signature_summary}

### Top hypothesis

{ranked_hypothesis_1.calibration_input}

- **File:** `{file_citation}`
- **Current value:** `{current_value_quoted}`
- **Expected direction:** {expected_direction_of_effect}
- **Expertise required:** {expertise_required}

### Test to run

> {test_to_run}

If this hypothesis explains the gap, the next step is {next_action}.

### Other hypotheses considered

{rank-2 and rank-3 hypotheses, abbreviated}

### Full analysis

See archived report: `{archive_relative_path}` (or attach if logger has the file).

---
*Filed by `report-logger` agent. Verdict: INVESTIGATE. Coverage note: {coverage_note}.*
```

**`structural` issue body:**

```markdown
## Model extension needed (flagged by `/analyze-policy`)

**Reform:** {reform_title}
**Reason for non-parametric classification:** {structural_provisions[].rationale}

### What needs to be added

{model_change_estimate}

### Provisions that don't fit current model

{list each structural_provision}

### Provisions that DO fit (could be partial implementation)

{list each parametric_provision}

### Full analysis

See archived report.
```

### Open issue mechanics

```bash
gh issue create \
  --repo PolicyEngine/policyengine-us-data \
  --title "{title}" \
  --body "$(cat <<'EOF'
{body}
EOF
)" \
  --label "calibration,auto-filed"
```

Capture the returned issue URL/number and append to the archive's `issues_opened` frontmatter list.

**Confirm before opening** unless `--auto-confirm` is set — the user may want to edit the body or pick a different repo.

## Destination: tracker (Supabase)

Only available when running inside the `state-legislative-tracker` repo (Supabase credentials in `.env`). Routes through that repo's local `db-writer` agent. Out of scope for analyses that aren't state bills.

Skip this destination unless `--log-to tracker` is explicitly passed AND credentials are present.

## Destination: draft (research PR)

`--log-to draft:<repo>/<path>` opens a PR with the report rendered as a blog-post-style markdown file.

1. Use the `policyengine-writing` skill for tone polish (the raw report uses neutral-mechanical language; a draft needs lead, sub-heads, and a TL;DR).
2. `gh pr create --draft` against the target repo, branch named `analyze-policy/{policy_id}`.
3. Surface the PR URL in the output.

## Output

```json
{
  "destinations_written": [
    {"type": "archive", "path": "~/.policyengine/analyses/2026-06-19-us-arpa-ctc-restoration.md"},
    {"type": "issue", "repo": "PolicyEngine/policyengine-us-data", "url": "https://github.com/.../issues/4823"}
  ],
  "skipped": [],
  "errors": []
}
```

If any destination fails (e.g., `gh` not authenticated), continue with the others and surface the error in `errors`. Always make sure the archive write succeeds — that's the durable record.

## Hand-off

This is the last agent in `/analyze-policy`. Its output is the final user-facing "here's where everything went" summary, printed after the report itself.
