---
description: Orchestrates multi-agent workflow to backdate and quality-improve existing state program parameters
---

# Backdating $ARGUMENTS

Coordinate a multi-agent workflow to add historical date entries, fix reference quality, review formula correctness, and improve test coverage for an existing state program's parameters.

**READ THE PLAN**: Detailed agent prompts, lessons learned, and state-specific notes are in the memory file `state-tanf-backdate-plan.md`. This command is the executable orchestration layer.

**GLOBAL RULE — PDF Page Numbers**: Every PDF reference href MUST end with `#page=XX` (the file page number, NOT the printed page number). The ONLY exception is single-page PDFs. This rule applies to ALL agents in ALL phases — research, implementation, audit, and finalize. Include this instruction in every agent prompt that touches parameter YAML files.

## Arguments

`$ARGUMENTS` should contain:
- **State and program** (required) — e.g., `CT TFA`, `IN TANF`, `KY K-TAP`
- **Target year** (optional) — how far back to research, e.g., `1997`. Defaults to program inception.
- **Options**:
  - `--skip-review` — skip Phase 6 (built-in /review-program)
  - `--values-only` — skip reference/formula audit (Phase 2), only backdate parameter values
  - `--research-only` — stop after Phase 1 (research), produce impl spec but don't implement
  - `--600dpi` — render all PDFs at 600 DPI instead of 300 DPI (use for scanned docs, poor-quality PDFs, or dense tables that are hard to read at 300 DPI)

**Examples:**
```
/backdate-program CT TFA
/backdate-program IN TANF 2005
/backdate-program KY K-TAP --values-only
/backdate-program NE ADC --research-only
/backdate-program VA TANF --600dpi
```

---

## YOUR ROLE: ORCHESTRATOR ONLY

**CRITICAL — Context Window Protection:**
- You are an orchestrator. You do NOT read raw file contents, grep output, research findings, or PDF data.
- ALL information-gathering work is delegated to agents.
- You only read files marked "Short" in the handoff table (max 25 lines each).
- ALL data flows through files on disk (see Phase 1 consolidation).
- When spawning agents, point them to files on disk — do NOT paste data into prompts.

**You MUST NOT:**
- Read parameter YAML files or variable .py files
- Read research findings from task descriptions
- Read audit reports in full
- Paste file contents or research data into agent prompts

**You DO:**
- Parse arguments
- Create team and tasks
- Spawn agents (in parallel where possible)
- Read SHORT summary files (≤25 lines)
- Present checkpoints to user
- Shut down agents when done

---

## Phase 0: Parse Arguments & Inventory

### Step 0A: Parse Arguments

```
Parse $ARGUMENTS:
- STATE: state abbreviation (e.g., "ct", "in")
- STATE_FULL: full state name (e.g., "Connecticut")
- PROGRAM: program abbreviation (e.g., "tfa", "tanf")
- TARGET_YEAR: target year (default: program inception year, typically 1996-1997)
- OPTIONS: --skip-review, --values-only, --research-only, --600dpi
- DPI: 600 if --600dpi, else 300
```

### Step 0B: Issue + Inventory (SPAWN BOTH IN ONE MESSAGE)

These two agents have no dependency on each other. Spawn them in a **single message** so they run concurrently:

**Agent 1: issue-manager** — searches GitHub (network calls)

```
subagent_type: "complete:country-models:issue-manager"
name: "issue-manager"
run_in_background: true

"Find or create a GitHub issue and draft PR for backdating {STATE_FULL} {PROGRAM} parameters.

1. Search for existing issues related to '{STATE_FULL} {PROGRAM}' backdating.
   If none found, create one with title: 'Backdate {STATE_FULL} {PROGRAM} parameters to {TARGET_YEAR}'.
2. Search for existing PRs related to '{STATE_FULL} {PROGRAM}'.
   If none found, create a draft PR with an empty commit on a new branch.
3. Return both the issue number and PR number."
```

**Agent 2: inventory** — scans local files (disk reads)

Spawn a `general-purpose` agent (needs Write tool) to inventory existing files:

```
subagent_type: "general-purpose"
name: "inventory"
run_in_background: true

"Inventory {STATE} {PROGRAM} parameter and variable files. Write TWO files:

1. FULL inventory for agents: /tmp/{st}-{prog}-inventory.md
   - List of parameter YAML files (full paths)
   - Earliest date entry in each file
   - YAML structure pattern (family-size breakdown vs scalar vs scale)
   - List of variable .py files (full paths)
   - List of test .yaml files (full paths)
   No line limit — agents need the complete picture.

2. SHORT summary for orchestrator: /tmp/{st}-{prog}-inventory-summary.md (MAX 10 LINES)
   - Parameter files: {count}
   - Variable files: {count}
   - Test files: {count}
   - Earliest date found: {YYYY-MM-DD}
   - Program path: parameters/gov/states/{st}/{prog}/
   Numbers only — no file paths."
```

**After both agents complete**:

- Read ONLY `/tmp/{st}-{prog}-inventory-summary.md` (max 10 lines) — just counts and the program path
- Store from issue-manager:
  - **ISSUE_NUMBER** — referenced in commit messages, changelog, and final report
  - **PR_NUMBER** — used by `/review-program` in Phase 6, and by `pr-pusher` in Phase 7
  - **BRANCH** — the working branch for all implementation

These are used throughout the workflow:
- Review-fix loop commits: `"Review-fix round {N}: address critical issues (ref #{ISSUE_NUMBER})"`
- Phase 6: `/review-program {PR_NUMBER} --local --full`
- Phase 7: `pr-pusher` pushes to the branch, reporter writes PR description
- Final report: links to issue and PR

### Step 0C: Create Team

```
TeamCreate(team_name="{st}-{prog}-backdate")
```

### Step 0D: Create Tasks

Create all tasks upfront with dependencies. Adjust count based on inventory.

| Task | Description | Blocked By |
|------|-------------|-----------|
| `discover-sources` | Find all historical PDFs for {STATE} {PROGRAM} | — |
| `secondary-validation` | Download WRDTP/CRS/CBPP cross-check tables | — |
| `prep-pdf-1` | Download, render, and map first PDF | `discover-sources` |
| `prep-pdf-2` | Download, render, and map second PDF | `discover-sources` |
| `research-pdf-1-{a,b,...}` | Extract parameter values from first PDF (1-5 agents based on page count) | `prep-pdf-1` |
| `research-pdf-2-{a,b,...}` | Extract parameter values from second PDF (1-5 agents based on page count) | `prep-pdf-2` |
| `consolidate` | Merge findings into implementation spec | all research + secondary |
| `audit-references` | Validate all existing reference URLs and citations | `consolidate` |
| `audit-formulas` | Review variable formulas vs. regulations | `consolidate` |
| `impl-parameters` | Add date entries + fix references in parameter files | `audit-references`, `audit-formulas` |
| `impl-formulas` | Apply formula fixes (if user-approved) | `audit-formulas` |
| `impl-tests` | Add historical + boundary + dimension tests | `impl-parameters` |
| `impl-edge-cases` | Generate edge case tests | `impl-tests` |
| `validate-and-fix` | implementation-validator + ci-fixer + make format | `impl-edge-cases` |
| `review-fix-loop` | Review-fix loop: /review-program → fix → re-review until 0 critical (max 3 rounds) | `validate-and-fix` |
| `finalize` | Changelog, push, final report | `review` |

Skip `audit-references`, `audit-formulas`, `impl-formulas` if `--values-only`.
Stop after `consolidate` if `--research-only`.
Skip `review-fix-loop` if `--skip-review`.

### Step 0E: Spawn Research Agents

Spawn ALL research agents in a **single message** for maximum parallelism:

| Agent Name | Type | Starts On |
|------------|------|-----------|
| **discovery** | `complete:country-models:document-collector` | `discover-sources` (immediate) |
| **secondary-validator** | `general-purpose` | `secondary-validation` (immediate) |
| **prep-1** | `general-purpose` | Waits for discovery message |
| **prep-2** | `general-purpose` | Waits for discovery message |

**Research agents are spawned AFTER prep agents report page counts** — see "Large PDF Splitting" below.

**Agent type rationale:**
- `document-collector` is purpose-built for discovering regulatory sources (WebSearch, WebFetch, Bash for curl/pdftotext). It writes to `sources/working_references.md`.
- Prep agents need Bash (pdftoppm, pdfinfo) + Read + SendMessage — `general-purpose` is required for PDF rendering.
- Research agents need Read (PNG screenshots) + Read (YAML files) + SendMessage — `general-purpose` is required for PDF reading.
- Secondary validator needs WebSearch + WebFetch for WRDTP/CBPP — `general-purpose` works.

Agents communicate directly via `SendMessage` — you do NOT relay.

```
discovery → finds PDF URL → messages prep-1: "Download and render: [URL]"
prep-1 → downloads, renders at {DPI} DPI → messages Main Claude: "Ready: {path}, {page_count} pages"
Main Claude → reads page count → spawns research agents with page-range assignments
research agents → extract values → update task with findings
```

**Agent prompts must include:**
- The inventory file path: `/tmp/{st}-{prog}-inventory.md`
- PDF rendering DPI: `{DPI}` (pass `pdftoppm -png -r {DPI}` to prep agents)
- HISTORICAL ERA AWARENESS: check for predecessor program values (AFDC→TANF, FSP→SNAP)
- Use Wayback Machine for archived sources
- Escalation rules: EXTERNAL DOCUMENT NEEDED, CROSS-REFERENCE NEEDED
- Continue working while waiting — never block on an escalation

**document-collector prompt additions:**
```
"In addition to your standard research workflow, also:
- Search for ALL historical state plan periods (not just the current one)
- Search Wayback Machine for archived versions of web-based sources
- Check ACF (federal) for approved state plans: site:acf.hhs.gov {State} {PROGRAM}
- When you find a PDF, message prep-{N}: 'Download and render: [URL] — [title]'
- Continue searching while prep agents work — don't block"
```

**Prep agent prompt additions:**
```
"After rendering, message Main Claude (NOT research agents) with:
- PDF file path
- Total page count
- Page offset (preliminary pages before content page 1)
- Screenshot path pattern
Main Claude will decide how many research agents to spawn based on page count."
```

### Large PDF Splitting for Research Agents

**Main Claude decides the research agent count** after each prep agent reports back. Each research agent should read **at most ~40 pages**.

| PDF page count | Research agents per PDF | Assignment |
|----------------|----------------------|------------|
| ≤40 | 1 | Full PDF |
| 41-80 | 2 | Split at midpoint |
| 81-120 | 3 | ~40 pages each |
| 121-160 | 4 | ~40 pages each |
| 161+ | 5 | ~32-40 pages each |

**Spawn all research agents for a PDF in a single message** for maximum parallelism. Each gets:
- Its assigned page range (e.g., pages 1-40, 41-80, 81-120)
- The SAME inventory file and parameter file list
- The SAME escalation rules (CROSS-REFERENCE NEEDED, EXTERNAL DOCUMENT NEEDED)
- Instructions to only extract values from their assigned pages

**Example**: A 150-page state plan → prep-1 reports 150 pages → Main Claude spawns 4 research agents:
```
research-1a: pages 1-38   (program overview, eligibility)
research-1b: pages 39-76  (income rules, deductions)
research-1c: pages 77-114 (benefit standards, payment tables)
research-1d: pages 115-150 (special provisions, appendices)
```

All 4 run in parallel. The consolidator (Phase 1) merges their findings.

---

## Phase 1: Consolidation & Checkpoint

### Consolidation (DELEGATED — biggest context saver)

**DO NOT read research findings.** Spawn a consolidation agent:

```
subagent_type: "general-purpose", team_name: "{st}-{prog}-backdate", name: "consolidator"

"Merge all research findings for {STATE} {PROGRAM} backdating.
1. Read ALL task findings from task list (TaskList + TaskGet)
2. Read inventory at /tmp/{st}-{prog}-inventory.md
3. Read existing parameter YAML files listed in inventory
4. Read sources/working_references.md from document-collector
5. Merge into FINAL IMPLEMENTATION SPEC: /tmp/{st}-{prog}-impl-spec.md
   - For EACH parameter file: exact date entries to add, with values + PDF citations
   - Reconcile conflicts (later documents supersede earlier)
   - Reconcile secondary source discrepancies (primary sources win)
   - Categorize: Tier A (YAML backdating), Tier B (new params), Tier C (formula changes)
   - Flag duplicate values (same value at multiple dates — only keep earliest)
5. Write SHORT summary (max 20 lines): /tmp/{st}-{prog}-impl-summary.md"
```

### Regulatory Checkpoint 1

Read ONLY `/tmp/{st}-{prog}-impl-summary.md`. Present to user:
- Number of files affected, date entries to add
- Any Tier B/C items (require user confirmation before proceeding)
- Source gaps or unresolved conflicts
- **Stop here if `--research-only`**

---

## Phase 2: Reference & Formula Audit

**Skip this phase if `--values-only`.**

Spawn two agents in parallel:

### Reference Auditor

```
subagent_type: "complete:reference-validator",
  team_name: "{st}-{prog}-backdate", name: "ref-auditor"
```

The `reference-validator` agent is purpose-built for this — it validates that all parameters have proper references that corroborate values. It checks: missing references, format (page numbers, detailed sections), value corroboration, and jurisdiction match.

**Additional instructions beyond its defaults:**
```
"Also check these backdate-specific reference issues:
1. URL LIVENESS: Test every href with curl -sI. Record broken/redirected URLs.
2. STATUTE SPECIFICITY: Must cite specific subsection, not parent section.
   BAD: '§ 17b-112'  GOOD: '§ 17b-112(c)'
3. REFERENCE TITLE DESCRIPTIVENESS: Title must distinguish what this ref is FOR.
   BAD: 'State Plan 2024-2026'  GOOD: 'State Plan 2024-2026, High Earnings Provision'
4. SESSION LAW vs PERMANENT STATUTE: Flag session law refs (Public Act, SB, HB)
   that should cite permanent statutes instead.
5. INSTRUCTION PAGE vs PDF PAGE: Verify #page=XX is the file page, not the printed
   page number. Render the page and confirm content matches.
6. HISTORICAL PLAN COVERAGE: Check for refs to ALL relevant plan periods.
Write findings to /tmp/{st}-{prog}-ref-audit.md."
```

### Formula Reviewer

```
subagent_type: "complete:country-models:program-reviewer",
  team_name: "{st}-{prog}-backdate", name: "formula-reviewer"
```

The `program-reviewer` agent is purpose-built for this — it researches regulations FIRST (independently of code), then validates code against legal requirements. This catches formula gaps and missing provisions.

**Additional instructions beyond its defaults:**
```
"Focus on these backdate-specific formula issues:
1. UNUSED PARAMETERS: Check every parameter YAML — is each one used in a formula?
   A parameter that exists but is never read means the feature is unimplemented.
2. ZERO-SENTINEL ANTI-PATTERN: Flag params where value=0 means 'not in effect'.
   Should be an explicit in_effect boolean parameter instead.
3. REDUNDANT LOGIC: Flag mathematically unnecessary operations.
4. HARDCODED COMMENTS: Flag comments with specific numbers (e.g., '92%', '171% FPG').
5. ERA HANDLING: Verify formula uses parameter-driven branching, NOT year-checks.
Read impl spec at /tmp/{st}-{prog}-impl-spec.md for regulatory context.
Write findings to /tmp/{st}-{prog}-formula-audit.md.
Write SHORT summary (max 15 lines) to /tmp/{st}-{prog}-phase2-summary.md."
```

### Regulatory Checkpoint 2

Read ONLY `/tmp/{st}-{prog}-phase2-summary.md`. Present to user:
- Broken URLs, generic refs, missing subsections count
- Unused parameters, zero-sentinels, missing provisions count
- **Formula fixes require user confirmation** before implementation

---

## Phase 3: Implementation

Spawn implementation agents in parallel. Each reads specs from disk — NOT from your prompt.

### Tier A: Parameter Backdating (most common)

```
subagent_type: "complete:country-models:parameter-architect",
  team_name: "{st}-{prog}-backdate", name: "impl-parameters"
```

The `parameter-architect` agent designs and modifies parameter structures with proper federal/state separation and zero hard-coding. It has Read, Write, Edit, MultiEdit, Grep, Glob, Skill access.

**Instructions:**
```
"Add historical date entries to {STATE} {PROGRAM} parameter files AND apply reference fixes.
Load skills: /policyengine-parameter-patterns, /policyengine-period-patterns.
Read impl spec at /tmp/{st}-{prog}-impl-spec.md (parameter values to add).
Read ref audit at /tmp/{st}-{prog}-ref-audit.md (reference fixes to apply).

LEARN FROM PAST SESSIONS (read if they exist — skip if not found):
- ~/.claude/projects/{project-slug}/memory/agent-lessons.md
- ~/.claude/plugins/marketplaces/policyengine-claude/lessons/agent-lessons.md
These contain real mistakes from past runs. Do NOT repeat them.

RULES:
- Preserve existing YAML structure EXACTLY (indentation, key ordering, metadata)
- Add entries in chronological order (earliest first, before existing entries)
- NO DUPLICATE VALUES: if value unchanged, one entry at earliest date only
- Descriptions one sentence
- PDF hrefs include #page=XX (file page number, NOT printed page number)
- Fix all reference issues from ref-audit alongside value backdating
- Use federal fiscal year dates (YYYY-10-01) unless source specifies otherwise

PATTERNS FOR NEW PARAMETERS (Tier B):
When the impl spec calls for a NEW parameter that didn't exist before, follow these patterns.
Study existing files in the same program first to match naming and structure.

Pattern 1 — in_effect boolean (provision that starts/ends at a specific date):
  Create a new YAML file at the appropriate subfolder with in_effect.yaml:
  ```yaml
  # e.g., payment/high_earnings/in_effect.yaml
  description: {State} uses this indicator to determine whether {provision} applies under {program}.
  values:
    {start-date}: false    # before provision existed
    {effective-date}: true  # when it took effect
  metadata:
    unit: bool
    period: month
    label: {State} {program} {provision} in effect
    reference:
      - title: {specific regulation}
        href: {url}#page={XX}
  ```
  Companion value parameters go alongside (e.g., high_earnings/rate.yaml, high_earnings/reduction_rate.yaml).

Pattern 2 — regional in_effect (provision that varies by region, then stops):
  Create a boolean parameter controlling the regional/non-regional split:
  ```yaml
  # e.g., payment/regional_in_effect.yaml
  description: {State} uses this indicator to determine whether regional payment standards apply under {program}.
  values:
    {start-date}: true     # regional standards active
    {end-date}: false       # switched to flat statewide standard
  metadata:
    unit: bool
    period: month
    label: {State} {program} regional payment standards in effect
    reference:
      - title: {specific regulation}
        href: {url}#page={XX}
  ```
  Regional value parameters go in subfolder: regional/region_a/amount.yaml, regional/region_b/amount.yaml, etc.
  Flat statewide parameter at: amount.yaml (same level as regional_in_effect.yaml)."
```

### Tier B/C: New Parameters & Formula Changes (if user-approved)

```
subagent_type: "complete:country-models:rules-engineer",
  team_name: "{st}-{prog}-backdate", name: "impl-formulas"
```

The `rules-engineer` agent implements government benefit program rules with zero hard-coded values and complete parameterization. It has the full tool set (Read, Write, Edit, MultiEdit, Grep, Glob, Bash, Skill).

**Instructions:**
```
"Apply formula fixes for {STATE} {PROGRAM} identified in the formula audit.
Load skills: /policyengine-variable-patterns, /policyengine-code-style,
  /policyengine-parameter-patterns, /policyengine-period-patterns, /policyengine-vectorization.
Read formula audit at /tmp/{st}-{prog}-formula-audit.md.

LEARN FROM PAST SESSIONS (read if they exist — skip if not found):
- ~/.claude/projects/{project-slug}/memory/agent-lessons.md
- ~/.claude/plugins/marketplaces/policyengine-claude/lessons/agent-lessons.md
These contain real mistakes from past runs. Do NOT repeat them.

FIXES TO APPLY:
- Create in_effect boolean parameters (replacing zero-sentinels)
- Wire unused parameters into formulas
- Remove redundant logic
- Replace hardcoded numbers in comments with parameter/statute references
- All logic changes are parameter-driven — NEVER use year-checks (period.start.year)

VARIABLE PATTERNS FOR in_effect AND regional_in_effect:
Study existing variables in the same program first to match style.

Pattern 1 — Using in_effect for a provision that starts at a specific date:
  The parameter tree has: high_earnings/in_effect (bool), high_earnings/rate, high_earnings/reduction_rate.
  In the variable formula, use `if p.high_earnings.in_effect:` to gate the logic:
  ```python
  def formula(spm_unit, period, parameters):
      p = parameters(period).gov.states.{st}.{agency}.{prog}.payment
      raw_benefit = ...  # base calculation always runs
      # New provision gated by in_effect boolean
      if p.high_earnings.in_effect:
          threshold = p.high_earnings.rate * some_base
          applies = income >= threshold
          reduction = 1 - p.high_earnings.reduction_rate
          return where(applies, raw_benefit * reduction, raw_benefit)
      return raw_benefit
  ```
  The `if p.in_effect:` branch is NEVER entered for periods before the effective date.
  No year-checks needed — the parameter handles the time logic.

Pattern 2 — Using regional_in_effect for region-based variation:
  The parameter tree has: regional_in_effect (bool), regional/region_a/amount, regional/region_b/amount, amount (flat).
  In the variable formula, use `if p.regional_in_effect:` to switch between regional and flat:
  ```python
  def formula(spm_unit, period, parameters):
      p = parameters(period).gov.states.{st}.{agency}.{prog}.payment
      capped_size = min_(size, p.max_unit_size)
      if p.regional_in_effect:
          region = spm_unit.household('{st}_{prog}_region', period)
          region_a = region == region.possible_values.REGION_A
          region_c = region == region.possible_values.REGION_C
          return select(
              [region_a, region_c],
              [p.regional.region_a.amount[capped_size],
               p.regional.region_c.amount[capped_size]],
              default=p.regional.region_b.amount[capped_size],
          )
      return p.amount[capped_size]
  ```
  When regional_in_effect is false, it falls through to the flat amount.

CRITICAL: These patterns use `if p.some_bool:` (not `where()`). This works because
PolicyEngine parameter booleans are scalar per-period — they don't vary across entities.
Use `where()` for entity-level conditions (income >= threshold), `if p.flag:` for
period-level switches (provision in effect or not)."
```

---

## Phase 4: Tests

After implementation agents complete, spawn TWO test agents in sequence:

### Step 4A: Test Creator

```
subagent_type: "complete:country-models:test-creator",
  team_name: "{st}-{prog}-backdate", name: "test-creator"
```

The `test-creator` agent creates comprehensive integration tests ensuring realistic calculations. It has Read, Write, Edit, MultiEdit, Grep, Glob, Bash, Skill access.

**Instructions:**
```
"Add tests for {STATE} {PROGRAM} backdating.
Load skills: /policyengine-testing-patterns, /policyengine-period-patterns.
Read impl spec at /tmp/{st}-{prog}-impl-spec.md.
Read existing test files listed in /tmp/{st}-{prog}-inventory.md.

COVERAGE REQUIREMENTS:
1. Existing untested features: test EVERY parameter, not just newly backdated ones
2. Period transition boundaries: test in the period AFTER every value change date
3. All dimension values: test ALL regions/tiers/filing statuses, not just defaults
4. Integration tests at era boundaries: full pipeline (eligibility → income → benefit)

GOTCHAS:
- absolute_error_margin: 0.1 REQUIRED on every test case
- Test naming: 'Case N, description.' (numbered, comma, period)
- Period: Only YYYY-01 or YYYY (no YYYY-10, no full dates)"
```

### Step 4B: Edge Case Generator

```
subagent_type: "complete:country-models:edge-case-generator",
  team_name: "{st}-{prog}-backdate", name: "edge-case-gen"
```

The `edge-case-generator` analyzes the variables and parameters to automatically generate comprehensive edge case tests (boundary conditions, zero values, maximums).

**Instructions:**
```
"Generate edge case tests for {STATE} {PROGRAM}.
Analyze variables and parameters in the program folder.
Focus on:
- Income just above/below thresholds
- Family size at min/max boundaries
- Zero income, maximum income
- Interaction between features (e.g., housing subsidy + high earner reduction)"
```

---

## Phase 5: Validation & Fix

### Step 5A: Implementation Validator

```
subagent_type: "complete:country-models:implementation-validator"
```

Checks naming conventions, folder structure, parameter formatting, variable code style, and compliance with PolicyEngine standards.

### Step 5B: CI Fixer

```
subagent_type: "complete:country-models:ci-fixer"
"Run tests for {STATE} {PROGRAM}, fix failures, iterate until all pass.
After tests pass, run make format as a final step."
```

### Quick Audit (context-safe)

Spawn an Explore agent to check ci-fixer's work:

```
"Review git diff of changes. Check for: hard-coded values to pass tests,
year-check conditionals (period.start.year), altered parameter values.
Write SHORT report (max 15 lines) to /tmp/{st}-{prog}-checkpoint.md: PASS/FAIL + issues."
```

Read ONLY the checkpoint file.

---

## Phase 6: Review-Fix Loop

**Skip if `--skip-review`.**

This phase runs `/review-program` and fixes critical issues in a loop until zero critical issues remain (or max iterations reached).

### Loop Structure

```
ROUND = 1
MAX_ROUNDS = 3

while ROUND <= MAX_ROUNDS:
    1. Run /review-program --local --full
    2. Read summary → count critical issues
    3. If critical == 0 → EXIT LOOP (success)
    4. If ROUND == MAX_ROUNDS → EXIT LOOP (escalate to user)
    5. If ROUND == 2 → ask user before attempting round 3
    6. Fix critical issues
    7. Run make format + tests
    8. Commit + push fixes (so next round's gh pr diff sees them)
    9. ROUND += 1
```

### Why commit + push is required between rounds

`/review-program` reads the PR code via `gh pr diff $PR_NUMBER`, which fetches the diff from the **GitHub remote API**. Local-only commits are invisible to `gh pr diff`. Therefore each fix round must **commit AND push** so the next review round sees the updated code.

```
Round 1 review → finds issues in commit A (already on remote)
Round 1 fix    → commit B + push (fixes from round 1)
Round 2 review → gh pr diff now includes commit B → reviews the fixed code
Round 2 fix    → commit C + push (fixes from round 2, if any)
Round 3 review → gh pr diff includes commits B+C → final check
Phase 7        → final push (changelog, any remaining changes)
```

### Step 6A: Run /review-program --local --full (Round N)

Invoke the `review-program` skill in local-only mode with `--full`. On **round 1**, this runs the full review:
- **PDF acquisition** (always on): `complete:country-models:document-collector` discovers and renders source PDFs
- **Regulatory accuracy**: `complete:country-models:program-reviewer` researches regulations independently, compares to code
- **Reference quality**: `complete:reference-validator` checks reference completeness and corroboration
- **Code patterns**: `complete:country-models:implementation-validator` checks code patterns
- **Test coverage**: `complete:country-models:edge-case-generator` identifies untested scenarios
- **PDF audit**: 2-5 `general-purpose` agents audit parameter values against PDF screenshots
- **Mismatch verification**: 600 DPI re-render + text cross-reference for every reported mismatch

**Note on round 2+**: The `/review-program` command always runs a full review — it has no "incremental" mode. This is by design: fixes can introduce new issues, and PDF audit agents need to re-verify values that may have changed. The cost of a redundant re-check is low compared to missing a regression.

### Step 6B: Check Results

Read `/tmp/review-program-summary.md` (max 20 lines). Check:
- **Critical issue count** — the number that matters
- **Recommended severity** — APPROVE means zero critical issues

**If critical == 0**: Report to user and exit loop.

**If critical > 0 and ROUND < MAX_ROUNDS**: Proceed to Step 6C.

**If critical > 0 and ROUND == 2**: Use `AskUserQuestion` before round 3:

```
Question: "Review found {N} critical issues after 2 fix rounds. Attempt a 3rd round?"
Options:
  - "Yes, try one more round"
  - "No, stop and show remaining issues"
```

If user says no, exit loop and include remaining issues in the final report.

**If critical > 0 and ROUND == MAX_ROUNDS (3)**: Exit loop. Report remaining issues to user:

```
"After {MAX_ROUNDS} review-fix rounds, {N} critical issues remain:
{one-line summary of each from the summary file}
These will be noted in the final report for manual resolution."
```

### Step 6C: Fix Critical Issues

Spawn a fixer agent to address the critical issues found in this round:

```
subagent_type: "complete:country-models:rules-engineer",
  team_name: "{st}-{prog}-backdate", name: "review-fixer-{ROUND}"

"Fix the critical issues from the /review-program review (round {ROUND}).
Read the full review report at /tmp/review-program-full-report.md.
Focus ONLY on items marked CRITICAL — do not change anything else.
Load appropriate skills. Apply fixes. Run make format.

LEARN FROM PREVIOUS ROUNDS:
If /tmp/{st}-{prog}-checklist.md exists, read it FIRST. It contains issues
found and fixed in previous rounds. Do NOT reintroduce any of those patterns.

AFTER fixing, APPEND your fixes to /tmp/{st}-{prog}-checklist.md:
Format each line as:
- [ROUND {ROUND}] [{CATEGORY}] {file}:{line} — {what was wrong} → {what you changed}

Categories: HARD-CODED, WRONG-PERIOD, MISSING-REF, BAD-REF, DEDUCTION-ORDER,
UNUSED-PARAM, WRONG-ENTITY, NAMING, FORMULA-LOGIC, TEST-GAP, OTHER"
```

### Step 6D: Verify Fix & Commit

**6D-1: Run tests and fix failures:**

```
subagent_type: "complete:country-models:ci-fixer",
  team_name: "{st}-{prog}-backdate", name: "ci-fixer-{ROUND}"

"Run tests for {STATE} {PROGRAM} after review-fix round {ROUND}.
Fix any test failures introduced by the fixes. Run make format."
```

**6D-2: Commit and push fixes:**

After ci-fixer completes, Main Claude commits and pushes so the next round's `/review-program` (which uses `gh pr diff` from the remote) sees the updated code:

```bash
git add -A
git commit -m "Review-fix round {ROUND}: address critical issues from /review-program"
git push
```

**6D-3: Increment ROUND and go back to Step 6A.**

### Loop Summary

| Round | What happens | Exit condition |
|-------|-------------|---------------|
| 1 | Full /review-program → fix criticals → run tests | 0 critical issues |
| 2 | Full /review-program → fix criticals → run tests | 0 critical issues, or user declines round 3 |
| 3 | Full /review-program → report remaining issues | Always exits (max reached) |

**Typical outcome**: Most issues are caught and fixed in round 1. Round 2 catches regressions from round 1 fixes. Round 3 is rare — it's a safety net for complex programs with cascading dependencies.

---

## Phase 7: Finalize

### Step 7A: Push & Changelog

```
subagent_type: "complete:country-models:pr-pusher",
  team_name: "{st}-{prog}-backdate", name: "pusher"
```

The `pr-pusher` agent ensures PRs are properly formatted with changelog, linting, and tests before pushing. It handles:
- Creating changelog fragment in `changelog.d/` (see Changelog section below)
- Running `make format`
- Pushing the branch

**Changelog format (towncrier fragments):**
```bash
echo "Description of change." > changelog.d/<branch-name>.<type>.md
```
Types: `added` (minor bump), `changed` (patch), `fixed` (patch), `removed` (minor), `breaking` (major).
**DO NOT** edit `CHANGELOG.md` directly or use `changelog_entry.yaml` (deprecated).

### Step 7B: Final Report + PR Description (DELEGATED)

Spawn a `general-purpose` agent to write the final report AND the PR description:

```
subagent_type: "general-purpose",
  team_name: "{st}-{prog}-backdate", name: "reporter"

"Finalize {STATE} {PROGRAM} backdating report.
1. Read all findings from task list
2. Read the last /review-program summary at /tmp/review-program-summary.md
3. Read the impl spec summary at /tmp/{st}-{prog}-impl-summary.md
4. Write SHORT final report (max 25 lines) to /tmp/{st}-{prog}-final-report.md:
   - Total parameters verified, date entries added
   - Reference fixes applied, formula improvements made
   - Review-fix loop rounds completed, remaining issues (if any)
   - Issue #{ISSUE_NUMBER}, PR #{PR_NUMBER}
5. Write FULL detailed report to /tmp/{st}-{prog}-full-audit.md (archival)
6. Write PR description to /tmp/{st}-{prog}-pr-description.md using this format:

   ## Summary
   Backdates {STATE_FULL} {PROGRAM} parameters to {TARGET_YEAR} and improves code quality.
   Closes #{ISSUE_NUMBER}

   ## Changes
   - **Parameters backdated**: {count} files, {count} date entries added
   - **Reference fixes**: {count} (broken URLs, generic statutes, page corrections)
   - **Formula improvements**: {list if any}
   - **Tests added**: {count} new test cases

   ## Regulatory Sources
   - [Source 1 title](URL#page=XX)
   - [Source 2 title](URL#page=XX)

   ## Review Summary
   - Review-fix loop: {N} rounds, {0/N} critical issues remaining
   - {X} parameters verified against PDF, {Y} confirmed correct

   ## Needs Human Decision
   {Include this section ONLY if there are unresolved items. Omit entirely if none.}
   - [ ] {Unresolved critical issue from review-fix loop, with context}
   - [ ] {Source conflict: two PDFs disagree on value X — which is correct?}
   - [ ] {Missing source: no PDF found for date range YYYY-YYYY}
   - [ ] {Formula ambiguity: regulation is unclear about [specific rule]}
   - [ ] {Tier C change not implemented: [description] — needs user approval}

   ## Test Plan
   - [ ] All existing tests pass
   - [ ] New historical tests pass
   - [ ] Edge case tests pass
   - [ ] Microsimulation check (if applicable)"
```

### Step 7C: Update PR Description

After the reporter completes, Main Claude updates the PR description using `--body-file` (no need to read the file into context):

```bash
gh pr edit $PR_NUMBER --body-file /tmp/{st}-{prog}-pr-description.md
```

### Step 7D: Present Summary

Read ONLY `/tmp/{st}-{prog}-final-report.md`. Present to user:
- Total parameters verified
- Date entries added
- Reference fixes applied
- Formula improvements made
- Remaining issues (if any)

---

## Phase 8: Lessons Learned

After the workflow completes, distill session lessons into persistent storage and propose them to the plugin repo. **This phase runs even if the review-fix loop was skipped** — the implementation and validation phases may also have produced lessons.

### Step 8A: Extract Lessons (DELEGATED)

Spawn a `general-purpose` agent to distill session-specific fixes into generalized rules:

```
subagent_type: "general-purpose",
  team_name: "{st}-{prog}-backdate", name: "lesson-extractor"

"Distill lessons learned from the {STATE} {PROGRAM} backdating session.

READ these files:
- /tmp/{st}-{prog}-checklist.md (session checklist from review-fix loop, if exists)
- /tmp/{st}-{prog}-checkpoint.md (validation checkpoint, if exists)
- /tmp/review-program-summary.md (last review summary, if exists)

ALSO READ the persistent lessons file (if it exists):
- {persistent_lessons_path}

TASK:
1. Extract every issue that was found and fixed during this session
2. Generalize each fix into a one-line rule (remove file names, line numbers, state names)
3. Categorize each rule:
   - PARAMETER: structure, metadata, references, dates, descriptions
   - VARIABLE: hard-coding, periods, entities, formulas, branching
   - TEST: coverage, boundaries, periods, naming
   - REFERENCE: URLs, page numbers, specificity, liveness
   - FORMULA: deduction order, unused params, zero-sentinels, logic
4. Deduplicate against existing persistent lessons — only keep genuinely NEW rules
5. If no new lessons: write 'NO NEW LESSONS' to /tmp/{st}-{prog}-new-lessons.md
6. If new lessons exist, write to /tmp/{st}-{prog}-new-lessons.md:

   ## New Lessons from {STATE} {PROGRAM} ({date})

   ### PARAMETER
   - {generalized rule}

   ### VARIABLE
   - {generalized rule}

   ### TEST
   - {generalized rule}

   (Only include categories that have new lessons. Max 15 entries total.)

RULES FOR GENERALIZATION:
- Remove state names: 'ct_tfa.py hard-coded 0.75' → 'Never hard-code numeric values in formulas'
- Remove file paths: 'payment/amount.yaml missing #page=' → 'All PDF references must include #page=XX'
- Keep the principle: 'Used period instead of period.this_year' → 'Use period.this_year for annual variables like household size'
- Be specific enough to be actionable, general enough to apply across programs"
```

Where `{persistent_lessons_path}` is:
```
~/.claude/projects/{project-slug}/memory/agent-lessons.md
```
(Same directory as MEMORY.md — it persists across conversations for this project.)

### Step 8B: Persist Locally

After the lesson-extractor completes, read `/tmp/{st}-{prog}-new-lessons.md`.

**If 'NO NEW LESSONS'**: Skip to Step 8D.

**If new lessons exist**: Append them to the persistent local file:

```bash
# Create the file if it doesn't exist
LESSONS_FILE=~/.claude/projects/{project-slug}/memory/agent-lessons.md
if [ ! -f "$LESSONS_FILE" ]; then
    echo "# Agent Lessons Learned" > "$LESSONS_FILE"
    echo "" >> "$LESSONS_FILE"
    echo "Accumulated from /backdate-program runs. Loaded by implementation agents on future runs." >> "$LESSONS_FILE"
    echo "Max 50 entries — oldest get pruned when exceeded." >> "$LESSONS_FILE"
    echo "" >> "$LESSONS_FILE"
fi
cat /tmp/{st}-{prog}-new-lessons.md >> "$LESSONS_FILE"
```

**Pruning**: If the file exceeds 50 lesson entries (grep -c "^- " "$LESSONS_FILE"), remove the oldest entries (earliest section) to stay under the cap.

### Step 8C: Propose to Plugin Repo (PR)

Share lessons with all plugin users by proposing them to the policyengine-claude repo.

**Step 8C-1: Check for existing open lessons PR:**

```bash
PLUGIN_DIR=~/.claude/plugins/marketplaces/policyengine-claude
cd "$PLUGIN_DIR"

# Check for an open lessons PR
OPEN_PR=$(gh pr list --repo PolicyEngine/policyengine-claude \
  --search "Agent lessons" --state open --json number,headRefName \
  --jq '.[0]')
```

**Step 8C-2: Create or update the lessons file:**

```bash
LESSONS_PLUGIN="$PLUGIN_DIR/lessons/agent-lessons.md"

if [ -n "$OPEN_PR" ]; then
    # Existing open PR — checkout its branch and append
    BRANCH=$(echo "$OPEN_PR" | jq -r '.headRefName')
    git checkout "$BRANCH"
    git pull
else
    # No open PR — create a new branch
    BRANCH="lessons/update-$(date +%Y%m%d)"
    git checkout -b "$BRANCH"
    mkdir -p "$PLUGIN_DIR/lessons"
    if [ ! -f "$LESSONS_PLUGIN" ]; then
        echo "# Agent Lessons Learned" > "$LESSONS_PLUGIN"
        echo "" >> "$LESSONS_PLUGIN"
        echo "Accumulated from /backdate-program runs across all contributors." >> "$LESSONS_PLUGIN"
        echo "Loaded by implementation agents on future runs." >> "$LESSONS_PLUGIN"
        echo "" >> "$LESSONS_PLUGIN"
    fi
fi

# Append new lessons (the file was already deduplicated in Step 8A)
cat /tmp/{st}-{prog}-new-lessons.md >> "$LESSONS_PLUGIN"
```

**Step 8C-3: Commit and push:**

```bash
git add lessons/agent-lessons.md
git commit -m "Add lessons from {STATE} {PROGRAM} backdate session"
git push -u origin "$BRANCH"
```

**Step 8C-4: Create PR if none exists:**

```bash
if [ -z "$OPEN_PR" ]; then
    gh pr create \
      --repo PolicyEngine/policyengine-claude \
      --title "Agent lessons update" \
      --body "$(cat <<'EOF'
## Summary
Accumulated lessons learned from /backdate-program runs.

These are generalized rules distilled from real agent mistakes caught
during review-fix loops. Each entry has been verified (the issue was
real and the fix was confirmed).

## How to review
- Check that each rule is genuinely useful and not too specific
- Promote particularly good rules to skill files if warranted
- Remove any that are too obvious or already covered by skills

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
fi
```

**Step 8C-5: Return to the original branch:**

```bash
git checkout -  # Return to previous branch
```

### Step 8D: Shutdown Team & Report

```
TeamDelete()
```

Present to user:
- **WORKFLOW COMPLETE**
- New lessons learned: {count} (or "none — all patterns already known")
- Lessons PR: {link to open PR on policyengine-claude, if created/updated}

---

## Future Runs: Loading Lessons

On future `/backdate-program` runs, implementation agents should load accumulated lessons:

**In Phase 3 agent prompts (parameter-architect, rules-engineer)**, add:

```
"BEFORE STARTING, read the lessons file if it exists:
- Local: {persistent_lessons_path}
- Plugin: {plugin_dir}/lessons/agent-lessons.md (if present)
These are real mistakes from past sessions. Do NOT repeat them."
```

This applies to ALL implementation agents, not just fixers. Prevention is better than fixing.

---

## Agent Summary

| Phase | Agent | Plugin Type | Why This Agent |
|-------|-------|-------------|----------------|
| 0B | issue-manager | `complete:country-models:issue-manager` | Finds/creates tracking issue + draft PR |
| 0E | discovery | `complete:country-models:document-collector` | Purpose-built for finding regulatory sources |
| 0E | secondary-validator | `general-purpose` | Custom WRDTP/CBPP web research |
| 0E | prep-1, prep-2 | `general-purpose` | Need Bash for pdftoppm/pdfinfo rendering |
| 0E | research-{N}-{a,b,...} (1-5 per PDF) | `general-purpose` | Need Read for PNG screenshots + YAML cross-ref |
| 1 | consolidator | `general-purpose` | Custom merge logic across all findings |
| 2 | ref-auditor | `complete:reference-validator` | Purpose-built for reference validation |
| 2 | formula-reviewer | `complete:country-models:program-reviewer` | Purpose-built for regulation-vs-code comparison |
| 3 | impl-parameters | `complete:country-models:parameter-architect` | Purpose-built for parameter YAML design |
| 3 | impl-formulas | `complete:country-models:rules-engineer` | Purpose-built for formula implementation |
| 4 | test-creator | `complete:country-models:test-creator` | Purpose-built for integration tests |
| 4 | edge-case-gen | `complete:country-models:edge-case-generator` | Purpose-built for boundary condition tests |
| 5A | validator | `complete:country-models:implementation-validator` | Purpose-built for code pattern checks |
| 5B | ci-fixer | `complete:country-models:ci-fixer` | Purpose-built for test fix iteration |
| 6 | review-program x1-3 | (invokes /review-program skill) | Review-fix loop: runs until 0 critical issues or max 3 rounds |
| 6 | review-fixer-{N} x1-3 | `complete:country-models:rules-engineer` | Fix critical issues from each review round |
| 6 | ci-fixer-{N} x1-3 | `complete:country-models:ci-fixer` | Verify fixes don't break tests after each round |
| 7A | pusher | `complete:country-models:pr-pusher` | Purpose-built for changelog + format + push |
| 7B | reporter | `general-purpose` | Final report + PR description with unresolved items |
| 8A | lesson-extractor | `general-purpose` | Distills session fixes into generalized rules |

**11 plugin agents + 1 skill invoked + 7 general-purpose agents** (only where no plugin agent fits).

---

## Files on Disk (Handoff Mechanism)

| File | Written By | Read By | Size |
|------|-----------|---------|------|
| `/tmp/{st}-{prog}-inventory.md` | inventory (Phase 0) | Agents only | Full |
| `/tmp/{st}-{prog}-inventory-summary.md` | inventory (Phase 0) | Main Claude | Short (≤10 lines) |
| `sources/working_references.md` | document-collector (Phase 0E) | Consolidator | Full |
| `/tmp/{st}-{prog}-impl-spec.md` | Consolidator (Phase 1) | Impl agents, test agents | Full |
| `/tmp/{st}-{prog}-impl-summary.md` | Consolidator (Phase 1) | Main Claude | Short |
| `/tmp/{st}-{prog}-ref-audit.md` | reference-validator (Phase 2) | parameter-architect | Full |
| `/tmp/{st}-{prog}-formula-audit.md` | program-reviewer (Phase 2) | rules-engineer | Full |
| `/tmp/{st}-{prog}-phase2-summary.md` | program-reviewer (Phase 2) | Main Claude | Short |
| `/tmp/{st}-{prog}-checkpoint.md` | Explore (Phase 5) | Main Claude | Short |
| `/tmp/{st}-{prog}-final-report.md` | Reporter (Phase 7) | Main Claude | Short |
| `/tmp/{st}-{prog}-pr-description.md` | Reporter (Phase 7) | gh pr edit --body-file | Full |
| `/tmp/{st}-{prog}-full-audit.md` | Reporter (Phase 7) | Archival only | Full |
| `/tmp/{st}-{prog}-checklist.md` | review-fixer (Phase 6) | Fix agents (next round), lesson-extractor | Full |
| `/tmp/{st}-{prog}-new-lessons.md` | lesson-extractor (Phase 8) | Main Claude (read first line only) | Short |
| `~/.claude/projects/.../memory/agent-lessons.md` | Phase 8B | Phase 3 agents (future runs) | Short (≤50 entries) |
| `policyengine-claude/lessons/agent-lessons.md` | Phase 8C (PR) | All plugin users (future runs) | Short (≤50 entries) |

**Main Claude reads ONLY "Short" files. Never read "Full" files.**

---

## Error Handling

| Category | Example | Action |
|----------|---------|--------|
| **Recoverable** | Test failure, lint error | ci-fixer handles automatically |
| **Source gap** | No PDFs found for a date range | Flag to user, continue with available data |
| **Agent failure** | Agent times out or crashes | Report to user, suggest re-running that phase |
| **Blocking** | No historical sources exist at all | Stop and report to user |

---

## Anti-Patterns This Workflow Prevents

1. **Wrong effective dates from era conflation**: Research agents check for predecessor program values
2. **Broken reference URLs**: reference-validator validates all hrefs
3. **Generic statute references**: reference-validator checks subsection specificity
4. **Zero-sentinel anti-patterns**: program-reviewer flags `rate: 0` → rules-engineer creates `in_effect` boolean
5. **Unused parameters**: program-reviewer catches params not wired into formulas
6. **Hardcoded comments**: program-reviewer flags specific numbers in comments
7. **Duplicate date entries**: Consolidator flags same value at multiple dates
8. **Session law URLs**: reference-validator migrates to permanent statute URLs
9. **Untested existing features**: test-creator inventories ALL params for coverage
10. **Missing transition boundary tests**: test-creator adds tests after every value-change date
11. **Instruction page vs PDF page**: reference-validator distinguishes file page from printed page
