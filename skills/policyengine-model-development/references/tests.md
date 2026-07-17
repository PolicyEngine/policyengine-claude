# YAML tests

Every variable with logic gets a YAML test mirroring its path under
`tests/policy/baseline/gov/...`. Pure `adds`/`subtracts` compositions don't need one; anything with
`where`/`select`/`if`, a calculation, a deduction, or an eligibility determination does.

## Structure

```yaml
- name: Case 1, single parent with one child at income threshold.
  period: 2024-01
  input:
    people:
      person1: {age: 30, employment_income: 24_000}
      person2: {age: 8}
    spm_units:
      spm_unit: {members: [person1, person2]}
    households:
      household: {members: [person1, person2], state_code: TX}
  output:
    tx_tanf_income_eligible: true
```

Conventions: case names are `Case N, description.` (numbered, comma, trailing period); people are
`person1`, `person2` (never descriptive); numbers use underscores (`50_000`); output is unnested
(`tx_tanf: 250`, not `tx_tanf: {spm_unit: 250}`). **Append** new cases at the bottom — never insert
mid-file and renumber (noisy diffs).

## Period restrictions

Only two period formats are supported:
- `2024` — whole year
- `2024-01` — first month **only**

`2024-04`, `2024-10`, and full dates like `2024-01-01` all fail. For a mid-year policy change, test
with the first month of a year where it's fully active (e.g. `2025-01`).

## Error margins by output type

- **Boolean outputs** (eligibility, flags): **omit `absolute_error_margin` entirely** — booleans
  are exact. A margin of `1` makes `true` (1) and `false` (0) indistinguishable and voids the test.
- Currency: `absolute_error_margin: 0.01`.
- Rates/percentages: `absolute_error_margin: 0.001`.

## Period conversion (input vs output)

Input matches the **larger** of (variable period, test period); output matches the **test period**.

| Variable | Test period | Input value | Output value |
|---|---|---|---|
| YEAR | YEAR | yearly | yearly |
| YEAR | MONTH | **yearly** (always) | monthly (÷12) |
| MONTH | YEAR | yearly (÷12/mo) | yearly (sum of 12) |
| MONTH | MONTH | monthly | monthly |

```yaml
# YEAR variable, MONTH test: input stays yearly, output is monthly.
- name: Case 2, monthly test of a yearly variable.
  period: 2024-01
  input: {people: {person1: {employment_income: 12_000}}}   # yearly
  output: {employment_income: 1_000}                          # 12_000 / 12
```

## Enum outputs — verify the exact member name

Grep the Enum before using a value in a test; label text differs from the member name:
```python
class ImmigrationStatus(Enum):
    LEGAL_PERMANENT_RESIDENT = "Legal Permanent Resident"   # not PERMANENT_RESIDENT
```
```yaml
immigration_status: LEGAL_PERMANENT_RESIDENT
```

## Don't invent input variables

Test inputs must be real PolicyEngine variables. Grep the formula for the exact names it reads
(`employment_income_before_lsr`, not a similar upstream). These do **not** exist — never use them:
`heating_expense`, `utility_expense`, `utility_shut_off_notice`, `past_due_balance`,
`bulk_fuel_amount`, `weatherization_needed`.

## Coverage every program needs

- At least one **positive (non-zero) benefit** case — zero-only tests hide errors that cancel out.
- At least one **ineligible** case returning 0/false.
- The **exact threshold** edge (income/age/resource).
- A **negative countable-income** case proving the benefit stays capped (guards
  `max - (-N) = max + N`):
  ```yaml
  - name: Case N, negative income does not inflate benefit.
    period: 2025-01
    input:
      people:
        person1: {age: 30, self_employment_income: -60_000_000}
        person2: {age: 8}
      spm_units: {spm_unit: {members: [person1, person2]}}
      households: {household: {members: [person1, person2], state_code: XX}}
    output: {xx_tanf: 300}   # capped at the payment standard, not millions
  ```
- **Every value** of a multi-valued dimension (provider type, filing status) — one case each.
- TANF/cash: always include a child (childless single adults are demographically ineligible).
  Couple programs: an asymmetric-eligibility case (one member in, one out) to catch half-benefit
  `defined_for` bugs.
- Mid-year parameter change: test **both sides** of the boundary.

## Integration tests

One `integration.yaml` per program (**never** prefixed — not `program_integration.yaml`). 5–7
scenarios end-to-end, each with inline calculation comments and 8–10 checked intermediate values, so
a reviewer can follow the arithmetic.

## Running tests

```bash
uv run policyengine-core test <path/to/file.yaml> -c policyengine_us   # a YAML test file
uv run pytest policyengine_us/tests/policy/baseline/gov/...            # via pytest
uv run pytest policyengine_us/tests/microsimulation/                   # cycles + entity bugs
```
Always `uv run` — never bare `pytest`. When fixing a buggy parameter or formula, sweep **all** test
files referencing the affected variable; stale expected values silently mask regressions.
