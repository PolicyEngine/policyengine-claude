---
name: publish-analysis
description: End-to-end blog post pipeline - from research question to published, distributed post with traceable numbers and validated results
arguments:
  - name: topic
    description: Research question, reform description, or bill reference (e.g., "SALT cap repeal" or "HR 1234")
    required: true
  - name: country
    description: Country code (us or uk)
    default: "us"
  - name: year
    description: Analysis year
    default: "2026"
---

# Publish Analysis: $ARGUMENTS

Generate a complete, validated, SEO-optimized blog post from a policy reform — every number traceable to code, validated against external estimates, zero hard-coded values.

## Prerequisites

Load these skills before starting:
- `blog-pipeline` — results.json schema, template syntax, chart/table catalogs
- `policyengine-writing-skill` — neutral tone, active voice, PE style
- `us-household-analysis` or `uk-household-analysis` — depending on country
- `content-generation-skill` — social images and copy

---

## Workflow Overview

```
┌──────────────────────────────────────────────────────────────────────────┐
│                    /publish-analysis {TOPIC}                             │
└──────────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
                ┌───────────────────────────────┐
                │  PHASE 0: PRE-FLIGHT          │
                │  Check for existing analysis   │
                └───────────────────────────────┘
                                │
                                ▼
                ┌───────────────────────────────┐
                │  PHASE 1: PARALLEL RESEARCH   │
                │  (Task agents)                │
                └───────────────────────────────┘
                                │
          ┌─────────────────────┴─────────────────────────┐
          │                                               │
          ▼                                               ▼
┌───────────────────┐                         ┌───────────────────┐
│  reform-definer   │                         │  estimate-finder  │
│  (define reform,  │                         │  (CBO, JCT, Tax   │
│   map parameters) │                         │   Foundation etc.) │
└─────────┬─────────┘                         └─────────┬─────────┘
          └─────────────────┬───────────────────────────┘
                            │
                            ▼
            ┌───────────────────────────────┐
            │  CHECKPOINT #1: REVIEW        │
            │  Reform definition +          │
            │  external estimates           │
            └───────────────────────────────┘
                            │
                            ▼
            ┌───────────────────────────────┐
            │  PHASE 2: ANALYSIS            │
            │  analysis-writer agent        │
            │  (analysis.py + results.json) │
            └───────────────────────────────┘
                            │
                            ▼
            ┌───────────────────────────────┐
            │  PHASE 2b: CHART SANITY       │
            │  Household sweep chart —      │
            │  does shape match intent?     │
            └───────────────────────────────┘
                            │
                            ▼
            ┌───────────────────────────────┐
            │  CHECKPOINT #2: REVIEW        │
            │  PE results vs external       │
            │  estimates + chart shape       │
            └───────────────────────────────┘
                            │
                            ▼
            ┌───────────────────────────────┐
            │  PHASE 3: BLOG POST           │
            │  blog-writer agent            │
            │  (markdown with {{}} refs)    │
            └───────────────────────────────┘
                            │
                            ▼
            ┌───────────────────────────────┐
            │  PHASE 4: VALIDATION          │
            │  pipeline-validator agent     │
            │  (9 automated checks)         │
            └───────────────────────────────┘
                            │
                            ▼
            ┌───────────────────────────────┐
            │  CHECKPOINT #3: REVIEW        │
            │  Full post + validation       │
            │  report before PR             │
            └───────────────────────────────┘
                            │
                            ▼
            ┌───────────────────────────────┐
            │  PHASE 5: PR + DISTRIBUTE     │
            │  Draft PR (in_review)         │
            │  Merge = publish              │
            └───────────────────────────────┘
                            │
                            ▼
                      ┌───────────┐
                      │   DONE!   │
                      └───────────┘
```

---

## Key Rules

1. **Zero hard-coded values** — every number in the blog post comes from results.json via `{{}}` templates
2. **Every number is traceable** — `source_line` and `source_url` point to the exact code
3. **All computation via analysis.py** — never compute impacts inline or with ad-hoc code
4. **Validate against external estimates** — compare PE results to CBO/JCT/fiscal notes/think tanks
5. **Human reviews at every gate** — 3 explicit checkpoints, each requires approve/adjust/cancel
6. **Neutral language** — describe what policies do, not whether they are good or bad
7. **No iframes** — charts are static `<img>` from GitHub Pages with descriptive alt text
8. **Draft PR = in_review** — content is NOT published until PR is merged

---

## Phase 0: Pre-Flight Check

**BEFORE doing any research**, check if this analysis already exists:

1. Check if analysis directory already exists in analysis-notebooks repo
2. Check if a blog post with this topic exists in policyengine-app-v2 posts.json

**If found with published results**: Show existing analysis, ask if re-computation needed.
**If not found**: Proceed with Phase 1.

---

## Phase 1: Parallel Research

Spawn two Task agents in parallel:

### 1a. Reform Definition

```
Task: Define the reform for "{TOPIC}"

1. Identify what policy changes to analyze
2. Find the PE parameter paths for the reform
3. Confirm parameter paths exist in policyengine-us or policyengine-uk
4. Build the reform definition (parameter paths, values, effective dates)
5. Determine analysis type: microsimulation, household, or both

Return:
- Reform parameter paths and values
- Analysis type
- Effective dates
- Any parameters that don't exist yet (blockers)
```

### 1b. External Estimate Finder

```
Task: Find external estimates for "{TOPIC}"

Search for existing analyses of this reform:
- CBO/JCT scores (for federal bills)
- State fiscal notes (for state bills)
- Tax Foundation, ITEP, CBPP analyses
- Academic papers with revenue/distributional estimates
- Back-of-envelope calculation (ALWAYS required)

For each estimate found, capture:
- Source name and URL
- Revenue/cost estimate
- Time period and methodology
- How comparable to PE's approach

Return structured estimates for validation.
```

Wait for both to complete, then combine results.

---

## Checkpoint #1: Reform Definition Review

Present the reform definition AND external estimates for human approval:

```
═══════════════════════════════════════════════════════════════════════════
REFORM DEFINITION & EXTERNAL ESTIMATES REVIEW
═══════════════════════════════════════════════════════════════════════════

TOPIC: {topic}
COUNTRY: {country}
YEAR: {year}
ANALYSIS TYPE: {microsimulation / household / both}

REFORM PARAMETERS:
┌─────────────────────────────────────────────────────────────────────────┐
│ Parameter                    │ Current    │ Proposed                   │
│──────────────────────────────│────────────│────────────────────────────│
│ {parameter_path}             │ {baseline} │ {reform}                   │
└─────────────────────────────────────────────────────────────────────────┘

EXTERNAL ESTIMATES:
┌─────────────────────────────────────────────────────────────────────────┐
│ Source               │ Estimate      │ Period    │ Link                │
│──────────────────────│───────────────│───────────│─────────────────────│
│ CBO/JCT              │ -$15.2B       │ Annual    │ [link]              │
│ Tax Foundation        │ -$14.8B       │ Annual    │ [link]              │
│ Back-of-envelope      │ -$16.0B       │ Annual    │ (see calculation)   │
└─────────────────────────────────────────────────────────────────────────┘

BACK-OF-ENVELOPE CHECK:
> {Simple calculation showing expected order of magnitude}
> Example: 15M itemizers × avg $12k SALT deduction × 24% avg rate = ~$43B
> (Rough estimate — actual varies due to AMT interaction and cap level)

═══════════════════════════════════════════════════════════════════════════
```

Use `AskUserQuestion` to confirm:
- Does this reform definition look correct?
- Are the external estimates reasonable comparisons?
- Options: **Yes, proceed** / **No, adjust** / **Cancel**

**Do NOT proceed until the user explicitly approves.**

---

## Phase 2: Run Analysis

### 2a. Create Analysis Directory

Create a directory in the analysis-notebooks repo:

```
{topic-slug}/
  analysis.py          # Full simulation + results.json generation
  results.json         # Generated by analysis.py
  charts/              # Generated PNGs
  requirements.txt     # policyengine, plotly, kaleido
  README.md            # How to reproduce
```

### 2b. Spawn analysis-writer Agent

```
Task: analysis-writer

Write and run analysis.py for the following reform:

- Reform: {approved reform definition from Checkpoint #1}
- Country: {country}
- Year: {year}
- Parameter paths: {approved parameter paths}
- Analysis type: {microsimulation / household / both}
- Output directory: {topic-slug}/
- Repo slug: PolicyEngine/{repo-name}

CRITICAL: Use tracked_value() for every value. Use ResultsJson to validate.
Use format_fig() for chart styling. ALL computation in analysis.py — no inline.
```

### 2c. Chart Sanity Check

After analysis.py completes, generate a household-level earnings sweep chart to verify the reform's shape:

**Quick sanity check**: Does the benefit curve match the reform's intent?
- Tax rate cut → linearly increasing benefit with income
- CTC expansion → flat benefit up to income limit, then phase-out
- EITC expansion → triangle shape (phase-in, plateau, phase-out)
- SALT cap change → benefit concentrated at high incomes
- UBI → flat benefit, then clawed back via taxes

**If the chart looks wrong**: Investigate before proceeding — likely a parameter mapping error.

---

## Checkpoint #2: Results Validation

Compare PE results against external estimates. This is the most important validation step.

```
═══════════════════════════════════════════════════════════════════════════
RESULTS VALIDATION
═══════════════════════════════════════════════════════════════════════════

PE RESULTS:
  Budget impact:       {budget_impact}
  Poverty change:      {poverty_change}
  Winners:             {winners_pct}
  Losers:              {losers_pct}
  Top decile avg:      {top_decile_avg}
  Bottom decile avg:   {bottom_decile_avg}

CHART SANITY CHECK:
  Household sweep shape: {matches intent? describe}

VALIDATION — PE vs EXTERNAL:
┌─────────────────────────────────────────────────────────────────────────┐
│ Source               │ Estimate  │ vs PE      │ Difference │ Verdict   │
│──────────────────────│───────────│────────────│────────────│───────────│
│ PE (PolicyEngine)    │ -$14.1B   │ —          │ —          │ —         │
│ CBO/JCT              │ -$15.2B   │ -7.2%      │ < 10%      │ Excellent │
│ Tax Foundation        │ -$14.8B   │ -4.7%      │ < 10%      │ Excellent │
│ Back-of-envelope      │ -$16.0B   │ -11.9%     │ 10-25%     │ Acceptable│
└─────────────────────────────────────────────────────────────────────────┘

THRESHOLDS:
  < 10%   → Excellent match
  10-25%  → Acceptable (note methodology differences)
  25-50%  → Review needed (re-check parameters)
  > 50%   → Likely error (stop and investigate)

DISCREPANCY EXPLANATION:
  {1-2 sentences explaining likely sources of difference — e.g., PE uses
   Enhanced CPS microdata vs CBO's proprietary tax model, static vs dynamic
   scoring, different base year assumptions}

═══════════════════════════════════════════════════════════════════════════
```

Use `AskUserQuestion`:
- Results look correct? External comparison acceptable?
- Options: **Yes, proceed to blog post** / **Re-run with adjusted parameters** / **Cancel**

**If difference > 50%**: Do NOT offer "proceed" option. Force investigation.

**Do NOT proceed until the user explicitly approves.**

---

## Phase 3: Write Blog Post

Spawn blog-writer agent:

```
Task: blog-writer

Write a blog post for the following analysis:

- results.json path: {topic-slug}/results.json
- Reform description: {approved reform description}
- Country: {country}
- Output path: {topic-slug}/post.md
- External estimates: {sources from Checkpoint #1 — for methodology section}

RULES:
- Every number must be a {{}} reference — zero hard-coded values
- Neutral tone, active voice, sentence case headings
- Methodology section must cite PE model version, dataset, and year
- Methodology section must note comparison to external estimates
- Include link to analysis repo code
```

---

## Phase 4: Automated Validation

Spawn pipeline-validator agent:

```
Task: pipeline-validator

Validate the full pipeline output:

- results.json path: {topic-slug}/results.json
- Blog post path: {topic-slug}/post.md
- Charts directory: {topic-slug}/charts/

Run all 9 checks and produce the validation report.
```

### Validation Checks (9 automated)

| # | Check | Blocker? |
|---|-------|----------|
| 1 | results.json schema (source_line, source_url, alt text, row widths) | Yes |
| 2 | Template references (every `{{}}` resolves, no orphans) | Yes |
| 3 | No hard-coded numbers (no raw `$` or `%` outside `{{}}`) | Yes |
| 4 | Neutral language (no value judgments) | Warning |
| 5 | Active voice (no passive constructions) | Warning |
| 6 | Sentence case headings | Warning |
| 7 | Chart accessibility (alt text with chart type + 2-3 data points) | Yes |
| 8 | Source traceability (source_url contains repo, ends with #L{line}) | Yes |
| 9 | Post structure (H1 title, key findings, methodology, repo link) | Yes |

**Blockers must pass before proceeding. Warnings should be fixed but don't block.**

---

## Checkpoint #3: Final Review Before PR

Present the complete post + validation report for human approval:

```
═══════════════════════════════════════════════════════════════════════════
FINAL REVIEW BEFORE PR
═══════════════════════════════════════════════════════════════════════════

VALIDATION REPORT:
  results.json schema:    ✅
  Template references:    ✅ (14 resolved, 0 missing, 0 orphaned)
  Hard-coded numbers:     ✅ (0 found)
  Neutral language:       ✅ (0 issues)
  Active voice:           ✅ (0 passive)
  Sentence case:          ✅
  Chart accessibility:    ✅ (3 charts checked)
  Source traceability:    ✅ (14 values checked)
  Post structure:         ✅

  Result: 9/9 checks passed. Ready for PR.

EXTERNAL VALIDATION:
  PE vs CBO/JCT:          -7.2% (Excellent)
  PE vs Tax Foundation:    -4.7% (Excellent)
  PE vs back-of-envelope:  -11.9% (Acceptable)

POST SUMMARY:
  Title: {title}
  Key findings: {3 bullet points}
  Charts: {N} charts with alt text
  Tables: {N} tables
  Values: {N} traceable values
  Word count: {N}

═══════════════════════════════════════════════════════════════════════════
```

Use `AskUserQuestion`:
- Ready to create PR?
- Options: **Yes, create draft PR** / **No, needs edits** / **Cancel**

**Do NOT proceed until the user explicitly approves.**

---

## Phase 5: Create PR + Distribute

### 5a. Create Analysis PR

```bash
cd {analysis-directory}
git add .
git commit -m "Add {topic} analysis with results.json and charts"
git push origin main
```

### 5b. Create Blog Post PR

Create a draft PR in policyengine-app-v2 that adds:
1. Blog post markdown in `articles/`
2. posts.json entry with `analysis_repo` field

PR body must include:

```markdown
## Blog Post: {title}

**Analysis repo**: [PolicyEngine/{repo}](https://github.com/PolicyEngine/{repo})

### Reform
| Parameter | Current | Proposed |
|-----------|---------|----------|
| {param}   | {base}  | {reform} |

### External validation
| Source | Estimate | vs PE | Verdict |
|--------|----------|-------|---------|
| PE (PolicyEngine) | {pe_estimate} | — | — |
| {source} | {estimate} | {diff}% | {verdict} |
| Back-of-envelope | {estimate} | {diff}% | {verdict} |

### Key results
| Metric | Value |
|--------|-------|
| Budget impact | {budget_impact} |
| Poverty change | {poverty_change} |
| Winners | {winners_pct} |

### Validation
Pipeline validator: {N}/9 checks passed.

---
*Generated by `/publish-analysis` — PolicyEngine Claude Plugin*
```

**The blog post is NOT published until the PR is merged.** The resolve-posts build step runs on deploy, fetches results.json, and resolves all `{{}}` templates.

### 5c. Distribution Checklist

After merge and deploy:

- [ ] Post to Twitter/X with key finding + image
- [ ] Post to LinkedIn with key finding + image
- [ ] Send to newsletter list (if applicable)
- [ ] Direct outreach to bill sponsors (if bill analysis)
- [ ] Pitch to relevant journalists
- [ ] Log in CRM
- [ ] Confirm GA4 events firing

---

## Final Output

```
═══════════════════════════════════════════════════════════════════════════
COMPLETE: {TOPIC}
═══════════════════════════════════════════════════════════════════════════

ANALYSIS:
  ✓ analysis.py written and executed
  ✓ results.json validated (Pydantic schema)
  ✓ {N} charts generated with alt text
  ✓ {N} values with source line tracking

VALIDATION:
  ✓ Pipeline validator: 9/9 checks passed
  ✓ PE vs external: {best_match}% ({verdict})
  ✓ Chart sanity check: shape matches intent
  ✓ Human approved at 3 checkpoints

PRs:
  Analysis: {analysis_pr_url}
  Blog post: {blog_pr_url}

NEXT STEPS:
  1. Review both PRs
  2. Merge blog post PR to publish
  3. Run distribution checklist

═══════════════════════════════════════════════════════════════════════════
```

---

## Error Handling

| Problem | Cause | Fix |
|---------|-------|-----|
| Dataset not found | HDF5 file not available locally | Download from HuggingFace: `hf://policyengine/policyengine-us-data/enhanced_cps_2024.h5` |
| Memory issues | Microsimulation loads ~60k households | Ensure 8GB+ RAM available |
| PE vs external > 50% | Parameter mapping error or methodological mismatch | **Stop.** Re-check parameter paths, compare baseline assumptions, verify reform encoding |
| PE vs external 25-50% | Moderate discrepancy | Note in methodology section. Check for known differences (static vs dynamic, different base year) |
| Chart shape wrong | Parameter mapping error | Return to Checkpoint #1, fix parameters, re-run |
| Unresolvable `{{ref}}` | Key mismatch between markdown and results.json | Fix spelling or add missing key to results.json |
| Stale source lines | Code changed after generating results.json | Re-run analysis.py to regenerate |
| Validator blockers | Schema or reference errors | Fix before proceeding — do NOT skip |

---

## Key Principle: All Computation via analysis.py

**NEVER compute impacts inline or with ad-hoc code.** All computation goes through analysis.py because:

1. **Reproducibility** — anyone can re-run the same script
2. **Auditability** — every value traceable to a specific line
3. **Schema consistency** — ResultsJson validates output
4. **Source tracking** — tracked_value() captures line numbers automatically

The agents research and generate the reform definition. analysis.py does computation. The blog post is a presentation layer only.

---

## Agents Used

| Agent | Purpose | Phase |
|-------|---------|-------|
| analysis-writer | Write and run analysis.py, produce results.json | 2 |
| blog-writer | Write blog post with {{}} template refs | 3 |
| pipeline-validator | 9 automated checks on schema, refs, language | 4 |

## Scripts & Tools

| Tool | Purpose |
|------|---------|
| `policyengine.py` | Local microsimulation (not API) |
| `policyengine.results.tracked_value()` | Auto-capture source line numbers |
| `policyengine.results.ResultsJson` | Pydantic schema validation |
| `policyengine.utils.plotting.format_fig()` | PE brand chart styling |

---

Start by checking for existing analysis (Phase 0), then proceed through all phases. Never skip a checkpoint.
