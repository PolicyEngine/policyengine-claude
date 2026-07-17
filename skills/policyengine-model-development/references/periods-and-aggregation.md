# Periods and aggregation

Two mechanics that trip up almost every new formula: how core auto-converts values between YEAR and
MONTH, and how sums cross entity levels.

## Definition periods

`definition_period` is `YEAR` (most variables), `MONTH` (monthly benefits/eligibility), or
`ETERNITY` (structural, never changes). US uses no `QUARTER`. When a formula reads a variable whose
period differs from its own, it must say which period it wants — that choice decides whether core
divides by 12.

## The ÷12 rule

Core stores YEAR values annually. Reading a YEAR variable **from a MONTH formula with `period`**
auto-divides it by 12. Reading it with **`period.this_year`** returns the annual value unchanged.

- **Flow variables** (income, FPG, dollar amounts) → use `period`. You *want* the monthly slice:
  `$24,000/yr → $2,000/mo`.
- **Stocks, counts, ages, booleans, enums** → use `period.this_year`. Dividing them by 12 is
  nonsense: `age/12`, `household_size/12`, `assets/12`.

```python
class monthly_tanf_eligible(Variable):
    definition_period = MONTH

    def formula(person, period, parameters):
        age = person("age", period.this_year)                 # actual age (no ÷12)
        assets = person("assets", period.this_year)           # point-in-time (no ÷12)
        monthly_income = person("employment_income", period)  # annual ÷12 → monthly
        p = parameters(period).gov.program
        return (age >= 18) & (assets <= p.asset_limit) & (monthly_income <= p.monthly_income_limit)
```

Decision tree:
```
Reading a YEAR variable from a MONTH formula?
├─ income / flow / dollar amount → period            (auto ÷12 to monthly)
└─ age / asset / count / bool / enum → period.this_year   (no conversion)
```

Two common mistakes:
- **Double-converting a flow:** `spm_unit("spm_unit_fpg", period.this_year) / MONTHS_IN_YEAR` is the
  same as just `spm_unit("spm_unit_fpg", period)`. Use `period` alone.
- **Forgetting `.this_year` on age:** `person("age", period)` from a MONTH formula gives `age/12`.

## Other period accessors

| Need | Use |
|---|---|
| YEAR variable from a MONTH formula | `person("age", period.this_year)` |
| MONTH variable from a YEAR formula | `person("monthly_rent", period.first_month)` |
| Year / month as integers | `period.start.year` / `period.start.month` |
| Parameters at a specific date | `parameters("2024-10-01").gov.hhs.fpg` |

Parameters always use the formula's own period — **never** `parameters(period.this_year)`. Use a
literal date string only when the rule keys off a specific date (e.g. FPG updates October 1):
```python
year, month = period.start.year, period.start.month
fpg_date = f"{year}-10-01" if month >= 10 else f"{year - 1}-10-01"
p_fpg = parameters(fpg_date).gov.hhs.fpg
```

## Aggregation: `adds` attribute vs `add()` function

Both sum a list of variables and **automatically aggregate across entity levels** (Person →
TaxUnit/SPMUnit/Household, etc.) — you never fetch members and `+` them by hand.

- **`adds` class attribute** — when the variable is *only* a sum, with no formula:
  ```python
  class tanf_gross_earned_income(Variable):
      entity = SPMUnit
      definition_period = MONTH
      adds = ["employment_income", "self_employment_income"]   # summed across members
  ```
  It also counts booleans (`adds = ["is_child"]` gives the number of children), and it can point at
  a **parameter that holds a list of variable names**:
  ```python
  class income_tax_refundable_credits(Variable):
      adds = "gov.irs.credits.refundable"   # parameter value is a YAML list of variable names
  ```

- **`add()` function** — inside a formula, when you need `max_`, `where`, a rate, or any other
  operation around the sum:
  ```python
  def formula(spm_unit, period, parameters):
      gross = add(spm_unit, period, ["employment_income", "self_employment_income"])
      return max_(gross, 0)
  ```

Only-a-sum → `adds`. Sum-plus-anything → `add()`. Using `add()` where `adds` would do is an
anti-pattern; so is writing a formula that just returns `add(...)`.

## Prefer `add(...) > 0` over `.any()`

To test whether *any* member has a boolean property, `add(...) > 0` is cleaner than materializing
members and calling `.any()`:
```python
# preferred
immigration_eligible = add(spm_unit, period, ["is_citizen_or_legal_immigrant"]) > 0
has_child = add(spm_unit, period, ["is_child"]) > 0

# more verbose, avoid
person = spm_unit.members
has_citizen = spm_unit.any(person("is_citizen_or_legal_immigrant", period))
```

And if an SPMUnit-level variable already exists, read it directly —
`spm_unit("is_demographic_tanf_eligible", period)` — rather than going down to `spm_unit.members`
and re-aggregating. Only drop to `.members` when you genuinely need per-person data to combine.

## The TANF countable-income shape

A recurring correctness trap: apply earned-income deductions to **earned income only**, floor with
`max_`, then add unearned (which usually has no deductions):
```
countable = max_(earned - earned_deductions, 0) + unearned
```
Not `max_(earned + unearned - deductions, 0)` — that lets deductions eat unearned income and can go
negative. Always confirm the exact order against the state's manual.
