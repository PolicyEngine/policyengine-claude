# Variables

A variable is one `Variable` subclass in its own file under `variables/gov/...`. It declares
metadata and either a `formula` or an `adds`/`subtracts` list. The law is the source of truth —
these are the mechanics for encoding it faithfully.

## Anatomy

```python
from policyengine_us.model_api import *


class il_tanf_countable_earned_income(Variable):
    value_type = float          # float | int | bool | str | Enum | date
    entity = SPMUnit            # Person | TaxUnit | SPMUnit | Family | MaritalUnit | Household
    definition_period = MONTH   # YEAR | MONTH | ETERNITY
    label = "Illinois TANF countable earned income"
    unit = USD
    reference = "https://www.law.cornell.edu/regulations/illinois/..."
    defined_for = StateCode.IL

    def formula(spm_unit, period, parameters):
        p = parameters(period).gov.states.il.dhs.tanf.income
        earned = spm_unit("tanf_gross_earned_income", period)
        return earned * (1 - p.earned_income_disregard_rate)
```

Metadata rules:
- Use **`reference`**, never a `documentation` field. Full clickable URL; for PDFs add `#page=XX`.
- **Multiple references use a tuple `()`, not a list `[]`** (a list is a different, wrong type here):
  ```python
  reference = (
      "https://oregon.public.law/rules/oar_461-155-0030",
      "https://oregon.gov/dhs/tanf-manual.pdf#page=23",
  )
  ```
  (Verified: tuple `reference` is used in policyengine-us, e.g. `variables/input/sstb_self_employment_income.py`.)

## `adds`/`subtracts` XOR `formula`

A variable is **either** a pure composition **or** a formula — never both (they drift out of sync).

```python
# Pure sum: adds attribute, NO formula. Handles entity aggregation automatically.
class tanf_gross_income(Variable):
    adds = ["tanf_gross_earned_income", "tanf_gross_unearned_income"]

# Pass-through + net-out: adds AND subtracts, still no formula.
class household_net_income(Variable):
    adds = ["household_gross_income"]
    subtracts = ["income_tax", "employee_pension_contributions"]

# Anything else (max_, where, a rate): a formula, using add() to sum inside it.
def formula(spm_unit, period, parameters):
    gross = add(spm_unit, period, ["tanf_gross_earned_income", "tanf_gross_unearned_income"])
    return max_(gross - deductions, 0)
```

Decision: only a sum → `adds`. Sum plus any other operation → `add()` in a formula. See
references/periods-and-aggregation.md for `add()` mechanics. Never manually fetch members and
`+` them.

## `defined_for` scoping

`defined_for` restricts which entities run the formula (others get the default, usually 0/false).
Use the most specific scope that fits:
- SPMUnit benefit variable → `defined_for = "state_program_eligible"` (the eligibility variable).
- Person-level rate/amount within a program → `defined_for = "state_program_eligible_child"`.
- An eligibility variable itself → `defined_for = StateCode.XX` (it can't depend on eligibility).

Scoping too broadly wastes computation and muddies intent; scoping to the eligibility variable
also prevents the formula from firing on irrelevant households.

## Naming

`{state}_{program}_{component}`, using the state's **official** program name and the terminology
from the source. `ca_calworks_eligible` (not `ca_tanf_` — California calls it CalWORKs);
`az_liheap_income_eligible`; `az_liheap_maximum_benefit`. Federal programs drop the state prefix
(`snap`, `snap_gross_income`). Standard suffixes: `_eligible`, `_income_eligible`,
`_resource_eligible`, `_countable_income`, `_countable_earned_income`, `_maximum_benefit`,
`_gross_income`. Final benefit = the bare `{prefix}`.

Don't create a state variable that just returns a federal one — use the federal variable directly.
Only create it if there is state-specific logic, **or** the same intermediate is reused in 2+
places (DRY extraction).

## Verified gotchas

- **`age` is a float.** Age-boundary parameters can be fractional (`1.5` = 18 months). Don't
  assume integer ages. (Verified: `age.py` has `value_type = float`.)
- **`monthly_age` returns years, not months.** It exists to undo core's auto-÷12: its formula is
  `person("age", period) * MONTHS_IN_YEAR`. For a true month count use
  `person("age", period.this_year) * MONTHS_IN_YEAR`. (Verified against `monthly_age.py`.)
- **`is_ssi_eligible` has NO income test.** It checks only aged/blind/disabled status, the
  resource test, and immigration status (the variable's own label says "without income test").
  Income enters separately. To test whether someone *actually receives* SSI, use
  `uncapped_ssi > 0`. A state SSP must check **both** categorical eligibility and receipt:
  ```python
  categorically_eligible = person("is_ssi_eligible", period)
  receives_ssi = person("uncapped_ssi", period) > 0
  eligible = categorically_eligible & receives_ssi
  ```
  (Verified against `variables/gov/ssa/ssi/is_ssi_eligible.py`.)
- **"Eligible except for income" trap.** When a program covers people who would qualify for an
  upstream program *but for income*, gating on the upstream `is_x_eligible` (which bakes in an
  income test) excludes the whole target population. Build a separate income-test-free
  eligibility variable.
- **Verify boundary operators** against the statute: `<` ("less than") vs `<=` ("at or below").
  The wrong one silently misclassifies people exactly at the threshold.
- **Child status uses age, not tax dependency.** For benefit eligibility use `age < 18`, not
  `is_tax_unit_dependent` (dependents include elderly parents and exclude non-dependent minors).
- **Exempting a recipient exempts their income.** If a program exempts SSI recipients, their
  income must also be excluded from countable income — not just their headcount.

## Enums

When enum labels describe numeric ranges ("30+ hrs/week"), the variable must be a **formula** that
derives the category from a numeric input via a `single_amount` bracket parameter — not a bare
input the user picks. Give each rate-table dimension (provider type, age group, star rating) its
own Enum variable so the lookup is plain indexing: `p.licensed_center[time][star][age]`. Put the
NONE/default value **last** in the Enum. In `select()`, list every category explicitly and set
`default` to match the Enum's `default_value` — don't hide a real category in the default.

## Federal aggregators: discover programs by directory, not keyword

A federal variable that sums state programs (e.g. `tanf` sums every state's TANF) must be built by
**enumerating state directories**, not grepping for the program name. State names diverge wildly:
`fl_tca`, `mn_mfip`, `ct_tfa`, `ar_tea`, `la_fitap`, `oh_owf`, `wy_power`, `ky_ktap`, `tn_ff` — a
keyword search for "tanf" misses ~11 programs. Instead: list `variables/gov/states/`, and for each
of the 51 jurisdictions find the top-level SPMUnit benefit variable (it has `defined_for`), and add
it to the list. Register new programs in the relevant `programs.yaml` or they won't surface in the
metadata API / coverage page.

## Dependency cycles

Wiring a state program into a federal aggregator can create circular dependencies. Known cycles and
fixes:
- **Housing:** state benefit → `housing_cost` → `rent` → `housing_assistance` → `hud_annual_income`
  → benefit. Use `pre_subsidy_rent` + components instead of `housing_cost`.
- **Childcare:** benefit → `childcare_expenses` → subsidy → SNAP → benefit. Use
  `spm_unit_pre_subsidy_childcare_expenses` instead of `childcare_expenses`.
- **Entity-broadcast bug:** mixing Person- and SPMUnit-level arrays in `where()` passes scalar unit
  tests but fails vectorized microsim. Broadcast with `spm_unit.project(...)`.

After adding programs, **run the microsimulation test** (`uv run pytest
policyengine_us/tests/microsimulation/`) — it catches cycles and entity mismatches that scalar unit
tests miss.

## Time-varying rules and the three toggle patterns

PolicyEngine models time-limited disregards (e.g. a rate that changes by calendar month via
`period.start.month` into a monthly bracket parameter). It does **not** yet model lifetime benefit
limits (e.g. the 60-month TANF clock) — skip those, but don't add comments claiming they're
impossible.

When a rule's *structure* changes at a date, the parameter side carries a boolean and the variable
branches on it with a **Python `if`** (the boolean is a scalar parameter — the whole population
takes one path per period; this is the one place `if` is correct, not `where`). This is the single
home for all three variants — the parameter-side YAML for each is in references/parameters.md.

| Pattern | Variable-side branch | Use case |
|---|---|---|
| `flat_applies` | `if p.rate.flat_applies:` chooses access method (`* p.flat` vs `p.incremental.calc(x)`) | Structure changes: flat rate → marginal brackets |
| `in_effect` | `if p.provision.in_effect:` gates an entire logic block (with its own sub-params) | A provision starts/ends at a date |
| `regional_in_effect` | `if p.regional_in_effect:` switches regional enum lookup vs flat amount | Regional ↔ statewide transition |

```python
# flat_applies — WA capital gains: flat 7% (2022) → tiered from 2025.
def formula(tax_unit, period, parameters):
    p = parameters(period).gov.states.wa.tax.income.capital_gains
    taxable_ltcg = ...
    if p.rate.flat_applies:
        return taxable_ltcg * p.rate.flat
    return p.rate.incremental.calc(taxable_ltcg)
```
(Verified: `variables/gov/states/wa/tax/income/wa_capital_gains_tax.py` uses `if p.rate.flat_applies:`.)

Inside a gated block, `where()`/`select()` still handle per-entity branching. Adding a *new bracket*
to an existing scale needs **no** variable change (`.calc()` is unchanged) — see the `.inf` pattern
in references/parameters.md.
