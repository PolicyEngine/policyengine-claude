---
description: Orchestrates multi-agent workflow to backdate and quality-improve existing state program parameters
---

# Backdating $ARGUMENTS

Coordinate a multi-agent workflow to add historical date entries, fix reference quality, review formula correctness, and improve test coverage for an existing state program's parameters.

**READ THE PLAN**: Detailed agent prompts, lessons learned, and state-specific notes are in the memory file `state-tanf-backdate-plan.md`. This command is the executable orchestration layer.

## Arguments

`$ARGUMENTS` should contain:
- **State and program** (required) — e.g., `CT TFA`, `IN TANF`, `KY K-TAP`
- **Target year** (optional) — how far back to research, e.g., `1997`. Defaults to program inception.
- **Options**:
  - `--skip-review` — skip Phase 6 (built-in review-pr / audit-state-tax)
  - `--values-only` — skip reference/formula audit (Phase 2), only backdate parameter values
  - `--research-only` — stop after Phase 1 (research), produce impl spec but don't implement

**Examples:**
```
/backdate-program CT TFA
/backdate-program IN TANF 2005
/backdate-program KY K-TAP --values-only
/backdate-program NE ADC --research-only
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
- OPTIONS: --skip-review, --values-only, --research-only
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
| `impl-standards` | Add date entries to family-size breakdown files | `audit-references`, `audit-formulas` |
| `impl-scalars` | Add date entries to scalar parameter files | `audit-references`, `audit-formulas` |
| `impl-formulas` | Apply formula fixes (if user-approved) | `audit-formulas` |
| `impl-tests` | Add historical + boundary + dimension tests | `impl-standards`, `impl-scalars` |
| `validate-and-fix` | implementation-validator + ci-fixer + make format | `impl-tests` |
| `review` | Run /review-pr --local and /audit-state-tax --local | `validate-and-fix` |
| `finalize` | Consolidate audit, fix mismatches, changelog, report | `review` |

Skip `audit-references`, `audit-formulas`, `impl-formulas` if `--values-only`.
Stop after `consolidate` if `--research-only`.
Skip `review` if `--skip-review`.

### Step 0E: Spawn Research Agents

Spawn ALL research agents in a **single message** for maximum parallelism:

| Agent Name | Type | Starts On |
|------------|------|-----------|
| **discovery** | `general-purpose` | `discover-sources` (immediate) |
| **secondary-validator** | `general-purpose` | `secondary-validation` (immediate) |
| **prep-1** | `general-purpose` | Waits for discovery message |
| **prep-2** | `general-purpose` | Waits for discovery message |
| **research-1** | `general-purpose` | Waits for prep-1 message |
| **research-2** | `general-purpose` | Waits for prep-2 message |

Agents communicate directly via `SendMessage` — you do NOT relay.

```
discovery → finds PDF URL → messages prep-1: "Download and render: [URL]"
prep-1 → downloads, renders 300 DPI → messages research-1: "Page map and paths"
research agents → extract values → update task with findings
```

**Agent prompts must include:**
- The inventory file path: `/tmp/{st}-{prog}-inventory.md`
- HISTORICAL ERA AWARENESS: check for predecessor program values (AFDC→TANF, FSP→SNAP)
- Use Wayback Machine for archived sources
- Escalation rules: EXTERNAL DOCUMENT NEEDED, CROSS-REFERENCE NEEDED
- Continue working while waiting — never block on an escalation

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
4. Merge into FINAL IMPLEMENTATION SPEC: /tmp/{st}-{prog}-impl-spec.md
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

### ref-auditor

```
subagent_type: "general-purpose", team_name: "{st}-{prog}-backdate", name: "ref-auditor"

"Audit reference quality for {STATE} {PROGRAM}.
Read inventory at /tmp/{st}-{prog}-inventory.md for file list.
For EACH parameter YAML: check URL liveness (curl -sI), statute specificity
(subsection level), reference title descriptiveness, session law vs permanent
statute, instruction page vs PDF page confusion, corroborating references,
historical state plan coverage. Write to /tmp/{st}-{prog}-ref-audit.md."
```

### formula-reviewer

```
subagent_type: "general-purpose", team_name: "{st}-{prog}-backdate", name: "formula-reviewer"

"Review {STATE} {PROGRAM} variable formulas for correctness.
Read inventory at /tmp/{st}-{prog}-inventory.md for file list.
Read impl spec at /tmp/{st}-{prog}-impl-spec.md for regulatory context.
Load skills: /policyengine-variable-patterns, /policyengine-code-style.
Check: unused parameters, zero-sentinel anti-patterns, redundant logic,
hardcoded values in comments, missing regulatory provisions, era handling.
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

**Two parallel agents:**

| Agent | Type | Scope |
|-------|------|-------|
| `impl-standards` | `general-purpose` | Family-size breakdown files |
| `impl-scalars` | `general-purpose` | Scalar parameter files |

Each agent:
1. Loads skills: `/policyengine-parameter-patterns`, `/policyengine-period-patterns`
2. Reads `/tmp/{st}-{prog}-impl-spec.md` (parameter values)
3. Reads `/tmp/{st}-{prog}-ref-audit.md` (reference fixes)
4. Adds date entries AND applies reference fixes
5. Rules: preserve YAML structure, chronological order, no duplicate values, descriptions one sentence, PDF hrefs include `#page=XX`

### Tier B/C: New Parameters & Formula Changes (if user-approved)

| Agent | Type | Scope |
|-------|------|-------|
| `impl-formulas` | `general-purpose` | Formula fixes from formula-audit |

This agent:
1. Loads skills: `/policyengine-variable-patterns`, `/policyengine-code-style`, `/policyengine-parameter-patterns`, `/policyengine-period-patterns`, `/policyengine-vectorization`
2. Reads `/tmp/{st}-{prog}-formula-audit.md`
3. Creates `in_effect` boolean parameters (replacing zero-sentinels)
4. Wires unused parameters into formulas
5. Removes redundant logic, hardcoded comments
6. **All logic changes are parameter-driven — NEVER use year-checks**

---

## Phase 4: Tests

After implementation agents complete:

```
subagent_type: "general-purpose", name: "test-agent"

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

---

## Phase 5: Validation & Fix

### Step 5A: Implementation Validator

```
subagent_type: "complete:country-models:implementation-validator"
```

### Step 5B: CI Fixer

```
subagent_type: "complete:country-models:ci-fixer"
"Run tests, fix failures, iterate until all pass. After tests pass, run make format."
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

This is the key integration — instead of custom audit agents replicating what review-pr and audit-state-tax already do well, invoke the actual commands.

### Step 6A: Run /review-pr --local

Invoke the review-pr command on the current branch's PR in local-only mode. This runs:
- **program-reviewer**: Researches regulations independently, compares to code
- **reference-validator**: Checks reference completeness and corroboration
- **implementation-validator**: Checks code patterns (adds, add(), periods, entities)
- **edge-case-generator**: Identifies untested scenarios

### Step 6B: Run /audit-state-tax --local --full (if applicable)

Run this if the program has a single authoritative PDF source (e.g., DSS Standards Chart, state plan with tables). Skip if sources are scattered across many documents.

### Step 6C: Consolidate Review Findings

Spawn a consolidation agent to merge review-pr and audit-state-tax findings:

```
"Read the review-pr and audit-state-tax output. Categorize findings into:
- ALREADY FIXED: issues that Phases 2-5 already addressed
- NEW CRITICAL: issues requiring code changes
- NEW SUGGESTIONS: minor improvements
Write SHORT report (max 20 lines) to /tmp/{st}-{prog}-review-summary.md."
```

### Step 6D: Fix NEW CRITICAL Issues

If the review found new critical issues, spawn a fix agent:

```
subagent_type: "general-purpose", name: "review-fixer"
"Fix the critical issues listed in /tmp/{st}-{prog}-review-summary.md.
Load appropriate skills. Apply fixes. Run make format."
```

---

## Phase 7: Finalize

### Step 7A: Final Report (DELEGATED)

```
subagent_type: "general-purpose", name: "finalizer"

"Finalize {STATE} {PROGRAM} backdating.
1. Read all findings from task list
2. Consolidate into report: MATCHES (count), MISMATCHES (detail), MISSING, reference fixes
3. Fix any remaining confirmed mismatches
4. Run make format
5. Create changelog fragment in changelog.d/
6. Write SHORT final report (max 25 lines) to /tmp/{st}-{prog}-final-report.md
7. Write FULL detailed report to /tmp/{st}-{prog}-full-audit.md (archival)"
```

### Step 7B: Present Summary

Read ONLY `/tmp/{st}-{prog}-final-report.md`. Present to user:
- Total parameters verified
- Date entries added
- Reference fixes applied
- Formula improvements made
- Remaining issues (if any)
- **WORKFLOW COMPLETE**

---

## Files on Disk (Handoff Mechanism)

| File | Written By | Read By | Size |
|------|-----------|---------|------|
| `/tmp/{st}-{prog}-inventory.md` | Explore (Phase 0) | Main Claude, agents | Short |
| `/tmp/{st}-{prog}-impl-spec.md` | Consolidator (Phase 1) | Impl agents, test agent | Full |
| `/tmp/{st}-{prog}-impl-summary.md` | Consolidator (Phase 1) | Main Claude | Short |
| `/tmp/{st}-{prog}-ref-audit.md` | ref-auditor (Phase 2) | Impl agents | Full |
| `/tmp/{st}-{prog}-formula-audit.md` | formula-reviewer (Phase 2) | Impl agents | Full |
| `/tmp/{st}-{prog}-phase2-summary.md` | formula-reviewer (Phase 2) | Main Claude | Short |
| `/tmp/{st}-{prog}-checkpoint.md` | Explore (Phase 5) | Main Claude | Short |
| `/tmp/{st}-{prog}-review-summary.md` | Consolidator (Phase 6) | Main Claude, fixer | Short |
| `/tmp/{st}-{prog}-final-report.md` | Finalizer (Phase 7) | Main Claude | Short |
| `/tmp/{st}-{prog}-full-audit.md` | Finalizer (Phase 7) | Archival only | Full |

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
2. **Broken reference URLs**: ref-auditor validates all hrefs
3. **Generic statute references**: ref-auditor checks subsection specificity
4. **Zero-sentinel anti-patterns**: formula-reviewer flags `rate: 0` → creates `in_effect` boolean
5. **Unused parameters**: formula-reviewer catches params not wired into formulas
6. **Hardcoded comments**: formula-reviewer flags specific numbers in comments
7. **Duplicate date entries**: Consolidator flags same value at multiple dates
8. **Session law URLs**: ref-auditor migrates to permanent statute URLs
9. **Untested existing features**: Test agent inventories ALL params for coverage
10. **Missing transition boundary tests**: Test agent adds tests after every value-change date
11. **Instruction page vs PDF page**: ref-auditor distinguishes file page from printed page
