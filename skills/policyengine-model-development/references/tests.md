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

## Choosing test periods

Case-level `period:` supports a year (`2024`) or any month (`2024-07`, for example).
For a non-January month case, explicitly key YEAR-defined inputs by year. MONTH-defined
inputs and outputs can use scalars at the case month. Match every input to its variable's
definition period; a parsing error for an annual scalar is not a ban on monthly cases.

```yaml
- name: Case 1, annual earnings expressed in a July test.
  period: 2024-07
  input:
    employment_income:
      2024: 12_000
  output:
    employment_income: 1_000
```

For a mid-year policy change, test the actual months before and after its effective date.
Do not move the case to next January or backdate the parameter to accommodate the test.
Check which period the formula uses for parameter lookup: an annual formula evaluated
at the year's start differs from a monthly formula evaluated in July.

### Asserting a specific month

An alternative is a whole-year case with the **output** keyed by month. This can
assert both sides of a boundary in one case:

```yaml
- name: Case 41, PA waiver starts in September 2024.
  period: 2024
  input:
    state_code: PA
    county_fips: "42005"
  output:
    is_in_snap_abawd_waived_area:
      2024-08: false
      2024-09: true
```

Any month works here. Annual inputs can remain scalars; supply monthly inputs with
period keys when their values vary through the year. This is useful whenever a MONTH-defined variable changes mid-year — a benefit standard that
re-bases in April, a waiver that starts in September, a rate that changes on a state's own schedule.
Asserting the months on either side of the change is what proves the boundary is where you think it
is; a single January case would pass just as happily if the change were ignored entirely.

Reach for a hand-built `Simulation` in a Python test only when you need something the YAML runner
genuinely cannot express. A mid-year boundary is not that — writing one is a sign this pattern was
overlooked.

Failures name the month, so a broken expectation is easy to place:

```
tanf_non_cash_gross_income_limit@2026-04: [2660.] differs from 9999.0 with an absolute margin > 0.01
```

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
- For every `single_amount` lookup: a case at **exactly $0** of the looked-up input and one
  **exactly at a band top** (e.g. $3,000 for a "$0–3,000" band). These are the two inputs where a
  wrong keying convention, or `right=True` over a `0` first threshold, silently returns 0.
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
