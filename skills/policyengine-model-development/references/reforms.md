# Contributed reforms

A contributed reform encodes a proposed bill or policy experiment. It differs structurally from
baseline law: it's **optional** (toggled by an `in_effect` parameter, off by default), its variables
live **inside a factory-function closure** under `reforms/`, and it's registered in one central
file. Where these rules conflict with the baseline conventions elsewhere in this skill, **the reform
rules win** — the table at the end lists every conflict.

Rule of thumb: a bill number (HB/SB/AB), a proposal, or an experiment → reform under `gov/contrib/`.
Enacted law (including enacted local taxes under `gov/local/`) → baseline.

## File layout

```
policyengine_us/
├── parameters/gov/contrib/states/{st}/{bill}/
│   ├── in_effect.yaml           # boolean toggle (REQUIRED)
│   ├── amount.yaml, rates.yaml, phaseout/threshold.yaml, ...
├── reforms/states/{st}/{bill}/
│   ├── {reform_name}.py         # factory functions + variable definitions
│   └── __init__.py              # exports
├── reforms/reforms.py           # central registration
├── tests/policy/contrib/states/{st}/{bill}/{reform_name}.yaml
└── changelog.d/{branch}.added.md
```
Federal/org reforms drop `states/{st}` (`gov/contrib/crfb/surtax/`, `reforms/crfb/agi_surtax.py`).
Two bills touching the same variables → separate parameter folders and test files, one shared
Python file, precedence via nested `where()`.

## The `in_effect` toggle

Every reform has one, defaulting off via the **`0000-01-01: false` sentinel** ("false for all time
until enabled") — the *one* place a placeholder date is correct:
```yaml
description: >-
  Montana HB 268 newborn credit applies if this is true.
values:
  0000-01-01: false
metadata:
  unit: bool
  period: year
  label: "MT HB 268 newborn credit in effect"
  reference:
    - title: "HB 268 — Title"
      href: "https://legislature.mt.gov/bills/..."
```
(Verified: `0000-01-01: false` in `parameters/gov/contrib/reconciliation/.../in_effect.yaml`.) A
reform may nest sub-feature `in_effect` toggles checked independently inside the formula
(`if p.increased_base.in_effect:`).

## The factory pattern

Two functions plus a module-level bypass instance. Reform variables are defined **inside** the inner
factory's closure (not as standalone files) so the `Reform` class can reference them.

```python
from policyengine_core.model_api import *
from policyengine_us.model_api import *
from policyengine_core.periods import period as period_


def create_mt_hb268() -> Reform:            # inner: defines variables, returns the Reform class
    class mt_newborn_credit(Variable):
        value_type = float
        entity = TaxUnit
        definition_period = YEAR
        label = "Montana newborn credit"
        unit = USD
        defined_for = StateCode.MT

        def formula(tax_unit, period, parameters):
            p = parameters(period).gov.contrib.states.mt.hb268
            return max_(p.amount - reduction, 0)

    class reform(Reform):
        def apply(self):
            self.update_variable(mt_newborn_credit)

    return reform


def create_mt_hb268_reform(parameters, period, bypass: bool = False):   # outer: gate on in_effect
    if bypass:
        return create_mt_hb268()
    p = parameters.gov.contrib.states.mt.hb268
    reform_active = False
    current_period = period_(period)
    for _ in range(5):                       # 5-year lookahead
        if p(current_period).in_effect:
            reform_active = True
            break
        current_period = current_period.offset(1, "year")
    return create_mt_hb268() if reform_active else None


mt_hb268 = create_mt_hb268_reform(None, None, bypass=True)   # module-level bypass instance
```

- **5-year lookahead:** the outer function scans 5 years forward so a reform set to activate in a
  future year is still loaded when simulating an earlier one. (Verified against
  `reforms/states/va/dependent_exemption/va_dependent_exemption_reform.py`: `for i in range(5): if
  p(current_period).in_effect: ... current_period = current_period.offset(1, "year")`.)
- **`bypass=True` instance:** the module-level object with parameter checks skipped — this is what
  test YAML imports and the web interface uses.
- **Simpler alternative:** for reforms that must always be structurally present, check `in_effect`
  *inside* the formula (`return where(p.in_effect, reform_value, 0)`) and have the outer function
  always return the reform. Prefer the 5-year lookahead otherwise.

## Kinds of variable change

```python
class reform(Reform):
    def apply(self):
        self.update_variable(mt_newborn_credit)      # new or override variable
        self.neutralize_variable("al_dependent_exemption")   # zero out a baseline variable (repeals)
```
- **New variable** — a credit/tax that doesn't exist in baseline. Must also be injected into the
  relevant list parameter (below).
- **Override** — same class name as a baseline variable; `update_variable` replaces its formula.
- **Dual calculation** — compute reform and baseline, `return where(qualifies, reform_tax,
  baseline_tax)` when a reform applies only to some filers.

## `modify_parameters` — register new credits/taxes

A **new** credit won't be summed unless its name is added to the state's credit list. Do that with a
`modify_parameters` function applied in `apply()`:
```python
def modify_parameters(parameters):
    node = parameters.gov.states.mt.tax.income.credits.refundable
    current = node("2027-01-01")
    node.update(start=instant("2027-01-01"), stop=instant("2100-12-31"),
                value=current + ["mt_newborn_credit"])
    return parameters

class reform(Reform):
    def apply(self):
        self.update_variable(mt_newborn_credit)
        self.modify_parameters(modify_parameters)
```
Needed when adding a refundable/non-refundable credit, a new tax, or modifying an income-source
list. **Not** needed for overrides (name already in the list) or pure rate/threshold changes. A
reform can also drive a computation off a parameter-defined source list
(`add(tax_unit, period, p.increased_base.sources)`).

## Registration in `reforms.py`

Every reform is wired into `create_structural_reforms_from_parameters(parameters, period)` in
`policyengine_us/reforms/reforms.py` (verified present, defined at that function). Four edits:
1. Import the outer factory at the top.
2. Instantiate inside the function: `mt_hb268 = create_mt_hb268_reform(parameters, period)`.
3. Add it to the `reforms = [...]` list.
4. The tail filters `None` and combines — matches the existing shape (verified):
   ```python
   reforms = tuple(filter(lambda x: x is not None, reforms))
   class combined_reform(Reform):
       def apply(self):
           for reform in reforms:
               reform.apply(self)
   return combined_reform
   ```

## Tests

Standard YAML plus two additions in **every** case: a `reforms:` key (dotted path to the
module-level bypass instance) and `gov.contrib.{...}.in_effect: true` in the input (the reform is
off by default). Reform tests commonly use `absolute_error_margin: 1` (dollar-scale credits).
```yaml
- name: Single filer with newborn below threshold.
  period: 2027
  absolute_error_margin: 1
  reforms: policyengine_us.reforms.states.mt.hb268.mt_hb268
  input:
    gov.contrib.states.mt.hb268.in_effect: true
    people:
      person1: {age: 30, is_tax_unit_head: true, employment_income: 50_000}
      child1: {age: 0, is_tax_unit_dependent: true}
    tax_units: {tax_unit: {members: [person1, child1], filing_status: SINGLE}}
    households: {household: {members: [person1, child1], state_code: MT}}
  output:
    mt_newborn_credit: 1_000
```
Cover eligibility, ineligibility, every filing status the bill distinguishes, phase-out boundaries,
edge cases, and — for `where(in_effect, ...)` reforms — the reform-off baseline. Test nested
sub-features on and off independently.

## Pitfalls

- **Circular dependency** when overriding a variable that feeds income tax which feeds back in — use
  an intermediate that breaks the cycle (`cdcc_potential`, not `cdcc`).
- **Forgetting `modify_parameters`** — a new credit silently never applies.
- **Forgetting the `None` filter** — inactive reforms return `None` and must be filtered before
  combining.
- **Hardcoded values** — same rule as baseline: every amount from a parameter.
- **`.brackets` in a path** — `p.rates.single[0].rate`, never `p.rates.single.brackets[0].rate`.
- Bill-specified rounding (`np.ceil`, `np.floor`, round-to-$10 `(x // 10) * 10`) and per-filing-
  status thresholds are easy to miss.

## Where reform rules override baseline

| Baseline convention (this skill) | Reform override |
|---|---|
| One variable per file under `variables/` | All reform variables in one `.py` inside the factory closure under `reforms/` |
| `eligibility/`, `income/` subfolder tree | Single `.py` + `__init__.py`; sections within the file |
| Never use placeholder dates | `in_effect.yaml` uses the `0000-01-01: false` sentinel (only this param) |
| Tests run against baseline, no `reforms:` key | Every test needs `reforms:` **and** `in_effect: true` |
| Booleans take no error margin | Reform tests commonly use `absolute_error_margin: 1` |
| People always `person1`/`person2` | `child1` acceptable when it clarifies tax-unit structure |

Everything else (parameter metadata, vectorization, the no-hardcoding rule) is identical to
baseline.
