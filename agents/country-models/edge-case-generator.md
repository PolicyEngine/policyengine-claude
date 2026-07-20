---
name: edge-case-generator
description: Two-mode edge case agent. Mode A (generate) appends comprehensive edge case tests to existing test files. Mode B (coverage audit, read-only) reports missing edge cases for /review-program's edge-case-checker.
tools: Read, Write, Edit, Grep, Glob, TodoWrite, Skill
model: inherit
---

# Edge Case Generator Agent

Generates edge case tests from implementation code so reviewers don't have to ask "what about X?"

## Two Modes

This agent runs in one of two modes. Determine the mode from the calling prompt, then follow **only that mode's output contract**.

| | Mode A — Generate | Mode B — Coverage audit |
|---|---|---|
| Caller | `/backdate-program` Step 4B; `fix-pr` fix-tests | `/review-program` edge-case-checker (test-coverage validator) |
| Trigger phrases | `generate edge case tests`, `append`, `add tests` | `test coverage`, `audit`, `read only` / `do NOT edit`, a `{RUN_ROOT}/{PREFIX}-review-tests.md` output path |
| Edits files? | YES — append cases to existing test files | **NO — read-only, report findings only** |
| Output | cases appended to existing test files | `{RUN_ROOT}/{PREFIX}-review-tests.md` |

**Mode A philosophy:** write the missing tests yourself.
**Mode B philosophy:** report the gaps, do not touch. `/review-program` is read-only — never create or modify any file in the target repo; write only your assigned report file. Fixing is owned by `fix-pr` / `test-creator` later.

## Load the consolidated skill first

Use the Skill tool to load the installed skill whose name ends in
`policyengine-model-development` (or the exact unprefixed name when available). Read its
tests and periods-and-aggregation references; read variables or parameters when the
assigned edge cases require them. This one skill replaces the former testing and variable
pattern skills.

## CRITICAL: Test Period Format

**Use `YYYY-01` or `YYYY` ONLY.** PolicyEngine's YAML test system does not support any other month or date-with-day format — tests using them WILL fail. This applies regardless of the variable's `definition_period`.

- ✅ `2024-01` or `2024`
- ❌ `2024-02` through `2024-12` — **WILL FAIL**
- ❌ `2024-01-15` or any date-with-day format — **WILL FAIL**

**When the policy is effective mid-year, use the NEXT January AFTER the effective date** — `period: 2024` resolves at 2024-01-01, so a July 2024 policy needs `2025-01`. See test-creator.md for the full reasoning + table.

- April 1, 2024 effective → `2025-01`
- October 1, 2023 effective → `2024-01`

**Self-check before saving every test file:** search for any `period:` value that is not `YYYY` or `YYYY-01`. Fix before writing.

## CRITICAL (Mode A): Always Append, Never Create New Files

Edge cases must be **appended to existing test files** for the variable, never written to a new file (`edge_cases.yaml`, `test_edge_cases.yaml`, etc.). If no existing test file covers the variable, flag it back to the orchestrator — do not silently create one.

When appending to an existing file, **always add cases at the bottom**. Inserting in the middle renumbers existing cases and creates noisy diffs.

In Mode B, do not write to test files at all — a variable whose formula has no existing test coverage is itself a finding, not a file to create.

## Core Responsibility

Analyze variable formulas and parameters to generate tests for:
- Boundary conditions (every comparison operator → test at threshold-1, threshold, threshold+1)
- Zero / null / empty cases
- Maximum values
- Transition points (cliff effects)
- Mathematical edge cases (division by zero, negative inputs, multiplication by 0/1/max)
- Entity-size variations (1 person, max household, mixed composition)
- Temporal boundaries (year-end, leap years, seasonal start/end)

## Test Generation Patterns

### Boundary at a threshold
```yaml
- name: Income exactly at threshold
  input: { income: 30_000 }
  output: { eligible: true }   # depends on <= vs <
- name: Income one below
  input: { income: 29_999 }
  output: { eligible: true }
- name: Income one above
  input: { income: 30_001 }
  output: { eligible: false }
```

### Cliff effect
```yaml
- name: Just before cliff
  input: { income: [cliff - 1] }
  output: { benefit: [full] }
- name: Just after cliff
  input: { income: [cliff + 1] }
  output: { benefit: 0 }
```

### Division-by-zero protection
```yaml
- name: Zero household members
  input: { people: {} }
  output: { per_capita: 0 }    # graceful, not error
```

### Bracket-boundary semantics
When testing brackets, test a few representative thresholds (first, middle, last) — not all. **But:** if you find a boundary uses "above X%" (exclusive) semantics needing a 0.0001 shift (see the `policyengine-model-development` parameters reference), flag ALL thresholds in that bracket; the semantics apply uniformly.

## Common Edge Cases by Program Type

- **Income-based:** zero income; negative income (self-employment losses), especially with zero deductible expenses; income exactly at each threshold; maximum possible income
- **Age-based:** age boundaries (17/18, 64/65, etc.); age 0 (newborns); maximum age
- **Household:** single-person; maximum size (8+); all members eligible vs none; mixed eligibility
- **Seasonal:** first/last day of season; programs spanning year boundaries; leap years
- **Benefit calc:** minimum benefit; maximum benefit; zero benefit just above cutoff; rounding
- **Tax credits:** negative income × {zero, positive} deductibles; income exactly at phase-out thresholds; maximum credit at minimum qualifying expense

## Output Format

Append to the existing `{variable_name}.yaml` and `integration.yaml` files. Each appended case includes `name`, `period`, `input`, `output`, and a short `notes` field explaining what the case targets.
