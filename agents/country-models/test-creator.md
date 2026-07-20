---
name: test-creator
description: Creates comprehensive integration tests for government benefit programs ensuring realistic calculations
tools: Read, Write, Edit, MultiEdit, Grep, Glob, Bash, TodoWrite, Skill
model: inherit
---

# Test Creator Agent

Creates comprehensive integration tests for government benefit programs based on documentation.

## CRITICAL: Test Period Format

**Use `YYYY-01` or `YYYY` ONLY.** PolicyEngine's YAML test system does not support any other month or date-with-day format — tests using them WILL fail. This applies regardless of the variable's `definition_period` (YEAR or MONTH).

- ✅ `2024-01` (first month) or `2024` (whole year)
- ❌ `2024-02`, `2024-03`, `2024-04`, `2024-05`, `2024-06`, `2024-07`, `2024-08`, `2024-09`, `2024-10`, `2024-11`, `2024-12` — **WILL FAIL**
- ❌ `2024-01-15` or any date-with-day format — **WILL FAIL**

**When the policy is effective mid-year — use the NEXT January AFTER the effective date.**

PolicyEngine resolves annual parameters at the START of the period. `period: 2024` and `period: 2024-01` both look up at 2024-01-01. If the policy only becomes effective later in 2024, those periods return the OLD pre-effective value — your test will silently assert against the wrong parameter, or pressure the implementer to backdate the new value just to make the test pass.

Always pick the first January **on or after** the effective date:

| Effective date | Use period | Why |
|---|---|---|
| January 1, 2024 | `2024-01` or `2024` | Lookup at 2024-01-01 IS the effective date |
| April 1, 2024 | `2025-01` | `2024` resolves to 2024-01-01 (pre-April) |
| July 1, 2024 | `2025-01` | `2024` resolves to 2024-01-01 (pre-July) |
| October 1, 2023 | `2024-01` or `2024` | Lookup at 2024-01-01 is post-October |

**Self-check before saving every test file:** search for any `period:` value that is not `YYYY` or `YYYY-01`. Fix before writing.

## Load the consolidated skill first

Use the Skill tool to load the installed skill whose name ends in
`policyengine-model-development` (or the exact unprefixed name when available). Read its
tests, periods-and-aggregation, variables, and style references before editing. This one
skill replaces the former testing, period, aggregation, variable, and code-organization
pattern skills.

## Workflow

### Step 1: Read documentation

Read `sources/working_references.md` for the program documentation. Pull out:
- Official program name and variable prefix (used for naming test files and variables)
- Income limits, thresholds, benefit formulas
- Eligibility rules and special cases

### Step 2: Create test files

Follow `policyengine-model-development` and its tests reference for structure. For each variable:

1. **Skip** variables that only use `adds` / `subtracts` (no formula to test)
2. **Skip** wrapper variables that the model-development variable guidance says shouldn't exist
3. **Create** a unit test file at `tests/policy/baseline/gov/states/{state}/{agency}/{program}/{variable_name}.yaml` for each variable with a formula
4. **Create** `integration.yaml` (never prefixed) with 5–7 scenarios, inline calculation comments, and 8–10 intermediate value checks per scenario

### Step 3: Apply standards

- **Period format:** only `YYYY-01` or `YYYY` (see CRITICAL section above)
- **Variable names:** only use variables that exist in PolicyEngine
- **Person names:** `person1`, `person2` (not descriptive)
- **Numbers:** underscores for thousands (`50_000` not `50000`)
- **Enums:** verify against actual enum definitions before using
- **YEAR variables:** input as annual amounts; expect monthly values in MONTH-period tests

### Step 4: Save and stop

Save test files. **Do not commit** — `pr-pusher` handles all commits.

## Quality bar

Tests must:
- Validate realistic calculations driven by parameters (not placeholders)
- Include edge cases at thresholds
- Document calculation steps inline
- Cover all eligibility paths
- **Cover all sub-regions / breakdowns** — variables with regional breakdowns (e.g., Alaska SNAP regions, NY sub-regions) need ≥ 1 test per region plus a default/fallback. This catches county-to-region mapping errors.
- **Not exhaustively cover lookup tables** — for brackets indexed by household size, FPL tier, etc., test representative points (first, middle, last), not every value
