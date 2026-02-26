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
  - `--skip-review` — skip Phase 6 (built-in review-pr / audit-state-tax)
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

### Step 0B: Inventory (DELEGATED)

Spawn an `Explore` agent to inventory existing files:

```
"Inventory {STATE} {PROGRAM} parameter and variable files. Write a summary to
/tmp/{st}-{prog}-inventory.md containing:
- List of parameter YAML files (full paths)
- Earliest date entry in each file
- YAML structure pattern (family-size breakdown vs scalar vs scale)
- List of variable .py files (full paths)
- List of test .yaml files (full paths)
Keep CONCISE — paths + earliest dates + structure type only. Max 40 lines."
```

Read ONLY the summary file after the agent completes.

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
| `research-pdf-1` | Extract parameter values from first PDF | `prep-pdf-1` |
| `research-pdf-2` | Extract parameter values from second PDF | `prep-pdf-2` |
| `consolidate` | Merge findings into implementation spec | all research + secondary |
| `audit-references` | Validate all existing reference URLs and citations | `consolidate` |
| `audit-formulas` | Review variable formulas vs. regulations | `consolidate` |
| `impl-parameters` | Add date entries + fix references in parameter files | `audit-references`, `audit-formulas` |
| `impl-formulas` | Apply formula fixes (if user-approved) | `audit-formulas` |
| `impl-tests` | Add historical + boundary + dimension tests | `impl-parameters` |
| `impl-edge-cases` | Generate edge case tests | `impl-tests` |
| `validate-and-fix` | implementation-validator + ci-fixer + make format | `impl-edge-cases` |
| `review` | Run /review-pr --local and /audit-state-tax --local | `validate-and-fix` |
| `finalize` | Changelog, push, final report | `review` |

Skip `audit-references`, `audit-formulas`, `impl-formulas` if `--values-only`.
Stop after `consolidate` if `--research-only`.
Skip `review` if `--skip-review`.

### Step 0E: Spawn Research Agents

Spawn ALL research agents in a **single message** for maximum parallelism:

| Agent Name | Type | Starts On |
|------------|------|-----------|
| **discovery** | `complete:country-models:document-collector` | `discover-sources` (immediate) |
| **secondary-validator** | `general-purpose` | `secondary-validation` (immediate) |
| **prep-1** | `general-purpose` | Waits for discovery message |
| **prep-2** | `general-purpose` | Waits for discovery message |
| **research-1** | `general-purpose` | Waits for prep-1 message |
| **research-2** | `general-purpose` | Waits for prep-2 message |

**Agent type rationale:**
- `document-collector` is purpose-built for discovering regulatory sources (WebSearch, WebFetch, Bash for curl/pdftotext). It writes to `sources/working_references.md`.
- Prep agents need Bash (pdftoppm, pdfinfo) + Read + SendMessage — `general-purpose` is required for PDF rendering.
- Research agents need Read (PNG screenshots) + Read (YAML files) + SendMessage — `general-purpose` is required for PDF reading.
- Secondary validator needs WebSearch + WebFetch for WRDTP/CBPP — `general-purpose` works.

Agents communicate directly via `SendMessage` — you do NOT relay.

```
discovery → finds PDF URL → messages prep-1: "Download and render: [URL]"
prep-1 → downloads, renders at {DPI} DPI → messages research-1: "Page map and paths"
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

RULES:
- Preserve existing YAML structure EXACTLY (indentation, key ordering, metadata)
- Add entries in chronological order (earliest first, before existing entries)
- NO DUPLICATE VALUES: if value unchanged, one entry at earliest date only
- Descriptions one sentence
- PDF hrefs include #page=XX (file page number, NOT printed page number)
- Fix all reference issues from ref-audit alongside value backdating
- Use federal fiscal year dates (YYYY-10-01) unless source specifies otherwise"
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

FIXES TO APPLY:
- Create in_effect boolean parameters (replacing zero-sentinels)
- Wire unused parameters into formulas
- Remove redundant logic
- Replace hardcoded numbers in comments with parameter/statute references
- All logic changes are parameter-driven — NEVER use year-checks (period.start.year)"
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

## Phase 6: Built-In Review

**Skip if `--skip-review`.**

This is the key integration — invoke the actual review commands which run their own specialized agents internally.

### Step 6A: Run /review-pr --local

Invoke the `review-pr` skill in local-only mode. This internally runs:
- **@complete:country-models:program-reviewer**: Researches regulations independently, compares to code
- **@complete:reference-validator**: Checks reference completeness and corroboration
- **@complete:country-models:implementation-validator**: Checks code patterns
- **@complete:country-models:edge-case-generator**: Identifies untested scenarios

### Step 6B: Run /audit-state-tax --local --full (if applicable)

Run this if the program has a single authoritative PDF source (e.g., DSS Standards Chart, state plan with payment tables). Skip if sources are scattered across many documents with no single definitive PDF.

### Step 6C: Fix NEW CRITICAL Issues

If the review found new critical issues not already addressed by Phases 2-5:

```
subagent_type: "complete:country-models:rules-engineer", name: "review-fixer"
"Fix the critical issues from the review.
Load appropriate skills. Apply fixes. Run make format."
```

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

### Step 7B: Final Report (DELEGATED)

Spawn a `general-purpose` agent to write the final report:

```
"Finalize {STATE} {PROGRAM} backdating report.
1. Read all findings from task list
2. Write SHORT final report (max 25 lines) to /tmp/{st}-{prog}-final-report.md:
   - Total parameters verified, date entries added
   - Reference fixes applied, formula improvements made
   - Review findings addressed
   - Remaining issues (if any)
3. Write FULL detailed report to /tmp/{st}-{prog}-full-audit.md (archival)"
```

### Step 7C: Present Summary

Read ONLY `/tmp/{st}-{prog}-final-report.md`. Present to user:
- Total parameters verified
- Date entries added
- Reference fixes applied
- Formula improvements made
- Remaining issues (if any)
- **WORKFLOW COMPLETE**

---

## Agent Summary

| Phase | Agent | Plugin Type | Why This Agent |
|-------|-------|-------------|----------------|
| 0E | discovery | `complete:country-models:document-collector` | Purpose-built for finding regulatory sources |
| 0E | secondary-validator | `general-purpose` | Custom WRDTP/CBPP web research |
| 0E | prep-1, prep-2 | `general-purpose` | Need Bash for pdftoppm/pdfinfo rendering |
| 0E | research-1, research-2 | `general-purpose` | Need Read for PNG screenshots + YAML cross-ref |
| 1 | consolidator | `general-purpose` | Custom merge logic across all findings |
| 2 | ref-auditor | `complete:reference-validator` | Purpose-built for reference validation |
| 2 | formula-reviewer | `complete:country-models:program-reviewer` | Purpose-built for regulation-vs-code comparison |
| 3 | impl-parameters | `complete:country-models:parameter-architect` | Purpose-built for parameter YAML design |
| 3 | impl-formulas | `complete:country-models:rules-engineer` | Purpose-built for formula implementation |
| 4 | test-creator | `complete:country-models:test-creator` | Purpose-built for integration tests |
| 4 | edge-case-gen | `complete:country-models:edge-case-generator` | Purpose-built for boundary condition tests |
| 5A | validator | `complete:country-models:implementation-validator` | Purpose-built for code pattern checks |
| 5B | ci-fixer | `complete:country-models:ci-fixer` | Purpose-built for test fix iteration |
| 6 | review-pr | (invokes /review-pr skill) | Runs 4 validators internally |
| 6 | audit-state-tax | (invokes /audit-state-tax skill) | PDF-to-code value audit |
| 6 | review-fixer | `complete:country-models:rules-engineer` | Fix critical issues from review |
| 7A | pusher | `complete:country-models:pr-pusher` | Purpose-built for changelog + format + push |
| 7B | reporter | `general-purpose` | Custom report aggregation |

**10 plugin agents + 2 skills invoked + 6 general-purpose agents** (only where no plugin agent fits).

---

## Files on Disk (Handoff Mechanism)

| File | Written By | Read By | Size |
|------|-----------|---------|------|
| `/tmp/{st}-{prog}-inventory.md` | Explore (Phase 0) | Main Claude, agents | Short |
| `sources/working_references.md` | document-collector (Phase 0E) | Consolidator | Full |
| `/tmp/{st}-{prog}-impl-spec.md` | Consolidator (Phase 1) | Impl agents, test agents | Full |
| `/tmp/{st}-{prog}-impl-summary.md` | Consolidator (Phase 1) | Main Claude | Short |
| `/tmp/{st}-{prog}-ref-audit.md` | reference-validator (Phase 2) | parameter-architect | Full |
| `/tmp/{st}-{prog}-formula-audit.md` | program-reviewer (Phase 2) | rules-engineer | Full |
| `/tmp/{st}-{prog}-phase2-summary.md` | program-reviewer (Phase 2) | Main Claude | Short |
| `/tmp/{st}-{prog}-checkpoint.md` | Explore (Phase 5) | Main Claude | Short |
| `/tmp/{st}-{prog}-final-report.md` | Reporter (Phase 7) | Main Claude | Short |
| `/tmp/{st}-{prog}-full-audit.md` | Reporter (Phase 7) | Archival only | Full |

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
