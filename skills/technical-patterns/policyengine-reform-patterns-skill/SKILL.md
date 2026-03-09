---
name: policyengine-reform-patterns
description: PolicyEngine reform patterns - factory functions, contrib parameters, in_effect toggles, registration, and test keys for contributed policy reforms
---

# PolicyEngine Reform Patterns

Comprehensive patterns for implementing policy reforms (proposed legislation, contributed tax/benefit changes) in policyengine-us. Reforms differ from baseline policy in that they are **optional** — toggled on/off via parameters — and live under `contrib/` paths.

**Baseline skills cover the foundational YAML/Python/test syntax. This skill covers the reform-specific layer on top.**

---

## Precedence: Where Reform Rules Override Baseline Rules

**When implementing a reform, this skill takes precedence over baseline skills wherever they conflict.** The baseline skills (parameter-patterns, variable-patterns, code-organization, code-style, review-patterns) are written for enacted-law variables under `variables/`. Reforms have fundamentally different structure. The table below lists every known conflict:

### Variables & Code Organization

| # | Baseline Rule (from skill) | Reform Override | Why |
|---|---|---|---|
| 1 | **One variable per file** in separate `.py` files under `variables/` (code-organization, review-patterns) | **All variables in ONE `.py` file** inside the factory function closure under `reforms/` | Reform variables must be defined inside the closure so the Reform class can reference them. Splitting into separate files breaks the factory pattern. |
| 2 | **Folder structure** — variables organized into `eligibility/`, `income/`, `deductions/` subfolders (code-organization) | **No subfolder tree** — single `.py` file + `__init__.py` in `reforms/states/{st}/{bill}/` | The reform's "organization" is sections within the single file, not a folder hierarchy. |
| 3 | **Variables go in** `variables/gov/states/{st}/...` (code-organization) | **Reform variables go in** `reforms/states/{st}/{bill}/` or `reforms/{org}/{topic}/` | Reform variables are NOT standalone — they're part of the reform module. |

### Parameters

| # | Baseline Rule (from skill) | Reform Override | Why |
|---|---|---|---|
| 4 | **Exact dates from sources** — never use arbitrary dates like `2000-01-01` (parameter-patterns) | **`in_effect.yaml` MUST use `0000-01-01: false`** | This sentinel date means "false for all time until explicitly enabled." It's the only parameter that uses this pattern. All other reform parameters (amounts, rates, thresholds) still use exact dates from sources. |
| 5 | **Description format**: `[State] [verb] [category] to [this X] under the [Full Program Name] program.` (parameter-patterns) | **`in_effect.yaml` uses**: `[State] [Bill Number] [short description] applies if this is true.` Other reform params (amounts, rates) still follow baseline description rules. | The `in_effect` parameter describes a toggle, not a policy value. Only `in_effect.yaml` deviates — all other reform parameters follow baseline description format. |
| 6 | **Label format**: `[State] [PROGRAM] [description]` (parameter-patterns) | **`in_effect.yaml` label**: `[ST] [Bill] [short name] in effect`. Other reform params still follow baseline label rules. | Same rationale — only `in_effect.yaml` deviates. |

### Tests

| # | Baseline Rule (from skill) | Reform Override | Why |
|---|---|---|---|
| 7 | **Test path**: `tests/policy/baseline/gov/states/...` (testing-patterns) | **Reform test path**: `tests/policy/contrib/states/{st}/{bill}/` or `tests/policy/contrib/{org}/{topic}/` | Different directory tree for contributed reforms. |
| 8 | **No `reforms:` key** — tests run against baseline automatically (testing-patterns) | **Every test MUST have `reforms:` key** with full dotted import path to the module-level bypass instance (e.g., `reforms: policyengine_us.reforms.states.mt.hb268.mt_hb268_reform`) | Without this key, the test runs against baseline code and the reform variables don't exist. |
| 9 | **No parameter toggles** in test input section (testing-patterns) | **Every test MUST set `gov.contrib.{...}.in_effect: true`** in the input section | The reform is off by default (`0000-01-01: false`). Tests must explicitly enable it or the reform logic won't execute. |
| 10 | **Error margin**: `absolute_error_margin: 0.1` — "never use 1" (testing-patterns) | **Reform tests commonly use `absolute_error_margin: 1`** | Reform calculations often involve larger numbers (tax amounts, credits) where $1 tolerance is appropriate. Use `0.1` only when testing boolean-like outputs. |
| 11 | **Person names**: always `person1`, `person2` — never descriptive (testing-patterns) | **Reform tests may use** `person1`/`child1` to clarify tax unit structure | Reform tests often need to distinguish adults from dependents for filing status and credit eligibility. `child1` is acceptable when it clarifies the test setup. Follow whichever convention the existing reform tests in the codebase use. |

**Summary for agents loading both baseline + reform skills:**
- If working on a **reform** (file under `reforms/` or params under `gov/contrib/`): follow this skill's rules
- If working on **baseline policy** (file under `variables/` or params under `gov/states/`): follow baseline skill rules
- **When in doubt**: check the parameter path — `gov/contrib/` = reform rules apply

---

## 1. When Is It a Reform vs Baseline?

| Type | Description | Parameter path | Variable location | Toggle |
|------|-------------|----------------|-------------------|--------|
| **Baseline** | Enacted law (current statute) | `gov/states/{st}/...` or `gov/irs/...` | `variables/gov/states/{st}/...` | None — always active |
| **Contributed reform** | Proposed bill or policy experiment | `gov/contrib/states/{st}/{bill}/...` or `gov/contrib/{org}/{topic}/...` | `reforms/states/{st}/{bill}/...` or `reforms/{topic}/...` | `in_effect` parameter |
| **Enacted local tax** | Enacted sub-state law | `gov/local/{st}/{jurisdiction}/...` | `variables/gov/local/{st}/{jurisdiction}/...` | None — always active |

**Rule of thumb:** If it's a bill number (HB, SB, AB, A0xxxx), a proposal, or a policy experiment, it's a contributed reform.

---

## 2. File Structure

Every contributed reform follows this layout:

```
policyengine_us/
├── parameters/gov/contrib/states/{st}/{bill_id}/
│   ├── in_effect.yaml              # Boolean toggle (REQUIRED)
│   ├── amount.yaml                 # Policy amounts
│   ├── age_limit.yaml              # Eligibility thresholds
│   ├── rates.yaml                  # Rate brackets (or rates/ folder)
│   └── phaseout/                   # Phase-out sub-parameters
│       ├── threshold.yaml          # Often with filing_status breakdown
│       ├── rate.yaml
│       └── ...
│
├── reforms/states/{st}/{bill_id}/
│   ├── {reform_name}.py            # Factory function + variable definitions
│   └── __init__.py                 # Exports
│
├── reforms/reforms.py              # Registration (import + call factory)
│
├── tests/policy/contrib/states/{st}/{bill_id}/
│   └── {reform_name}.yaml          # YAML test cases
│
└── changelog.d/{branch-name}.added.md  # Changelog fragment
```

### Federal / org-specific reforms

Federal reforms and organization-specific proposals (not state-specific) use a path without `states/{st}`:

```
parameters/gov/contrib/{org}/{topic}/...      # e.g., gov/contrib/crfb/surtax/
reforms/{org}/{topic}/...                     # e.g., reforms/crfb/agi_surtax.py
tests/policy/contrib/{org}/{topic}/...        # e.g., tests/policy/contrib/crfb/agi_surtax.yaml
```

### Multiple reforms in one PR

When two related bills modify the same variables (e.g., KY HB 13 and HB 152 both change income tax brackets):
- **Separate parameter folders** per bill (`gov/contrib/states/ky/hb13/`, `gov/contrib/states/ky/hb152/`)
- **Single reform Python file** with shared calculation logic
- **Separate test files** per bill
- **Precedence logic** using nested `where()`: `where(hb13_active, hb13_result, where(hb152_active, hb152_result, baseline))`

---

## 3. The `in_effect` Parameter (Required for Every Reform)

Every reform MUST have an `in_effect.yaml` toggle:

```yaml
description: >-
  [State] [Bill Number] [short description] applies if this is true.
values:
  0000-01-01: false

metadata:
  unit: bool
  period: year
  label: "[ST] [Bill] [short name] in effect"
  reference:
    - title: "[Bill Number] - [Title]"
      href: "https://legislature.gov/bills/..."
```

**Key rules:**
- Default value is ALWAYS `false` (reform is off by default)
- Date `0000-01-01` means "false for all time until explicitly enabled"
- Tests set it to `true` in their input section

### Nested `in_effect` toggles (sub-feature pattern)

A reform can have sub-features with their own `in_effect` toggles. The main reform can be active while a sub-feature is independently toggled:

```
gov/contrib/crfb/surtax/
├── in_effect.yaml              # Main reform toggle
├── rate/
│   ├── single.yaml             # Rate brackets for single filers
│   └── joint.yaml              # Rate brackets for joint filers
└── increased_base/
    ├── in_effect.yaml          # Sub-feature toggle (independent)
    └── sources.yaml            # Variable list for expanded base
```

In the formula, check both toggles:
```python
def formula(tax_unit, period, parameters):
    p = parameters(period).gov.contrib.crfb.surtax
    # Main reform logic always runs (gated by outer factory function)
    agi = tax_unit("adjusted_gross_income", period)

    # Sub-feature: only if its own in_effect is true
    if p.increased_base.in_effect:
        additional = add(tax_unit, period, p.increased_base.sources)
        agi = agi + additional

    return p.rate.single.calc(agi)
```

---

## 4. Factory Function Pattern (The Core Reform Mechanism)

Every reform Python file follows this two-function pattern:

```python
from policyengine_core.model_api import *
from policyengine_us.model_api import *
from policyengine_core.periods import period as period_


def create_xx_reform() -> Reform:
    """Inner factory: defines variables and returns the Reform class."""

    class some_variable(Variable):
        value_type = float
        entity = TaxUnit
        label = "Description"
        unit = USD
        definition_period = YEAR
        reference = "https://legislature.gov/bills/..."
        defined_for = StateCode.XX

        def formula(tax_unit, period, parameters):
            p = parameters(period).gov.contrib.states.xx.bill_id
            # ... calculation logic using p.amount, p.threshold, etc.
            return result

    class reform(Reform):
        def apply(self):
            self.update_variable(some_variable)

    return reform


def create_xx_reform_reform(parameters, period, bypass: bool = False):
    """Outer factory: checks in_effect parameter before creating reform."""
    if bypass:
        return create_xx_reform()

    p = parameters.gov.contrib.states.xx.bill_id
    reform_active = False
    current_period = period_(period)

    for _ in range(5):
        if p(current_period).in_effect:
            reform_active = True
            break
        current_period = current_period.offset(1, "year")

    if reform_active:
        return create_xx_reform()
    return None


# Module-level instance for direct test/import use
xx_reform = create_xx_reform_reform(None, None, bypass=True)
```

### The 5-year lookahead

The outer function scans 5 years forward from the simulation period. This ensures reforms set to activate in a future year (e.g., `2027-01-01: true`) are still loaded when simulating 2026.

### The `bypass=True` module-level instance

```python
xx_reform = create_xx_reform_reform(None, None, bypass=True)
```

This creates a reform object that bypasses parameter checks — used for:
- Direct import in test YAML (`reforms: path.to.module.xx_reform`)
- Web interface access

### Alternative: `in_effect` check inside formula

For simpler reforms, some implementations check `in_effect` inside the formula instead of the outer function. This avoids the 5-year lookahead complexity but means the reform class is always loaded:

```python
def create_mi_surtax() -> Reform:
    class mi_surtax(Variable):
        defined_for = StateCode.MI
        def formula(tax_unit, period, parameters):
            p = parameters(period).gov.contrib.states.mi.surtax
            in_effect = p.in_effect
            surtax = p.rate.joint.calc(taxable_income)
            return where(in_effect, surtax, 0)

    class reform(Reform):
        def apply(self):
            self.update_variable(mi_surtax)
    return reform

def create_mi_surtax_reform(parameters, period, bypass: bool = False):
    return create_mi_surtax()  # Always return — in_effect checked in formula

mi_surtax = create_mi_surtax_reform(None, None, bypass=True)
```

**Prefer the standard 5-year lookahead pattern.** Use the in-formula check only when you need the reform to always be structurally present (e.g., the variable must exist for other variables to reference it).

---

## 5. Variable Definitions Inside Reforms

Reform variables are defined **inside the factory function closure**, NOT as standalone files in `variables/`.

### New variable (adds a credit/tax that doesn't exist in baseline)

```python
class mt_newborn_credit(Variable):
    value_type = float
    entity = TaxUnit
    label = "Montana newborn credit"
    unit = USD
    definition_period = YEAR
    reference = "https://leg.mt.gov/bills/..."
    defined_for = StateCode.MT  # Or: defined_for = "eligibility_variable"

    def formula(tax_unit, period, parameters):
        p = parameters(period).gov.contrib.states.mt.newborn_credit
        # ... calculation
        return max_(base_credit - reduction, 0)
```

### Override variable (replaces an existing baseline variable)

```python
class sc_income_tax_before_non_refundable_credits(Variable):
    value_type = float
    entity = TaxUnit
    label = "South Carolina income tax before non-refundable credits"
    unit = USD
    definition_period = YEAR
    defined_for = StateCode.SC

    def formula(tax_unit, period, parameters):
        p = parameters(period).gov.contrib.states.sc.h4216
        taxable_income = tax_unit("sc_taxable_income", period)
        return p.rates.calc(taxable_income)
```

When overriding, use `self.update_variable()` in the Reform class — PolicyEngine replaces the baseline formula with yours.

### Dual calculation pattern (reform vs baseline, select by eligibility)

When a reform applies only to qualifying taxpayers and others use baseline:

```python
class ct_income_tax_after_personal_credits(Variable):
    defined_for = StateCode.CT

    def formula(tax_unit, period, parameters):
        p_reform = parameters(period).gov.contrib.states.ct.sb100
        p_baseline = parameters(period).gov.states.ct.tax.income

        # Calculate both
        reform_tax = p_reform.rates.single.calc(taxable_income)
        baseline_tax = p_baseline.rates.calc(taxable_income)

        # Select based on eligibility
        qualifies = agi < p_reform.income_threshold[filing_status]
        return where(qualifies, reform_tax, baseline_tax)
```

### Neutralizing variables (zeroing out a baseline variable)

Used in repeal-style reforms:

```python
class reform(Reform):
    def apply(self):
        self.neutralize_variable("al_dependent_exemption")  # Sets to 0
        self.update_variable(ga_exemptions)  # Replace with reform version
```

### Dual-class entity tracking (eligible vs ineligible members)

When a reform needs to track which members of a group qualify and which don't:

```python
class some_reform_eligible_count(Variable):
    value_type = int
    entity = TaxUnit

    def formula(tax_unit, period, parameters):
        p = parameters(period).gov.contrib.states.xx.bill
        age = tax_unit.members("age", period)
        eligible = age < p.age_limit
        return tax_unit.sum(eligible)

class some_reform_credit(Variable):
    value_type = float
    entity = TaxUnit

    def formula(tax_unit, period, parameters):
        p = parameters(period).gov.contrib.states.xx.bill
        eligible_count = tax_unit("some_reform_eligible_count", period)
        ineligible_count = tax_unit("tax_unit_size", period) - eligible_count
        # Different amounts for eligible vs ineligible members
        return eligible_count * p.amount.eligible + ineligible_count * p.amount.ineligible
```

---

## 6. Parameter Integration (`modify_parameters`)

When a reform creates a **new credit**, you must inject it into the state's existing credit list so the tax system recognizes it.

```python
def create_mt_newborn_credit() -> Reform:

    class mt_newborn_credit(Variable):
        # ... variable definition ...

    def modify_parameters(parameters):
        # Get existing refundable credits list for the state
        reform_credits = parameters.gov.states.mt.tax.income.credits.refundable
        current_credits = reform_credits("2027-01-01")  # Get current list

        # Append the new credit variable name
        updated_credits = current_credits + ["mt_newborn_credit"]

        # Update for the reform's effective period
        reform_credits.update(
            start=instant("2027-01-01"),
            stop=instant("2100-12-31"),
            value=updated_credits,
        )
        return parameters

    class reform(Reform):
        def apply(self):
            self.update_variable(mt_newborn_credit)
            self.modify_parameters(modify_parameters)

    return reform
```

### Modifying parameter source lists

Some reforms modify a parameter that holds a list of variable names (e.g., income sources). This uses the same `modify_parameters` pattern:

```python
def modify_parameters(parameters):
    # Example: modifying SALT deduction sources
    parameters.gov.irs.deductions.itemized.salt_and_real_estate.sources.update(
        start=instant("2025-01-01"),
        stop=instant("2036-12-31"),
        value=["real_estate_taxes"],  # Replace list with just property taxes
    )
    return parameters
```

**When to use `modify_parameters`:**
- Adding a new refundable credit (must be in `credits.refundable` list)
- Adding a new non-refundable credit (must be in `credits.non_refundable` list)
- Adding a new tax (must be in relevant tax list)
- Modifying an income source list

**When NOT needed:**
- Overriding an existing variable (the variable name is already in the list)
- Rate changes or threshold changes (parameters only, no new variables)

---

## 7. Parameter-Driven Source Lists

For reforms that compute values from a configurable set of income sources, define the list as a parameter:

```yaml
# gov/contrib/crfb/surtax/increased_base/sources.yaml
description: >-
  The CRFB surtax increased base includes income from these sources.
values:
  2025-01-01:
    - traditional_401k_contributions
    - roth_401k_contributions
    - traditional_ira_contributions
    - roth_ira_contributions
    - health_savings_account_contributions
    - student_loan_interest
    - taxable_social_security
    - tax_exempt_foreign_earned_income
    - tax_exempt_interest_income
    - health_insurance_premiums

metadata:
  label: CRFB surtax increased AGI base sources
  period: year
```

In the formula, use `add()` to sum the listed variables:

```python
from policyengine_us.model_api import *

def formula(tax_unit, period, parameters):
    p = parameters(period).gov.contrib.crfb.surtax
    agi = tax_unit("adjusted_gross_income", period)

    # If sub-feature is active, add the configurable sources
    if p.increased_base.in_effect:
        additional_sources = add(tax_unit, period, p.increased_base.sources)
        agi = agi + additional_sources

    filing_status = tax_unit("filing_status", period)
    joint = filing_status == filing_status.possible_values.JOINT
    return where(
        joint,
        p.rate.joint.calc(agi),
        p.rate.single.calc(agi),
    )
```

**When to use this pattern:**
- Reform taxes or credits based on a sum of specific income types
- The set of included sources may change (future amendments)
- The bill text explicitly lists which income components are included

---

## 8. Registration in `reforms.py`

Every reform must be imported and registered in `policyengine_us/reforms/reforms.py`:

### Step 1: Import at the top

```python
from policyengine_us.reforms.states.mt.newborn_credit import (
    create_mt_newborn_credit_reform,
)
```

### Step 2: Instantiate in `create_structural_reforms_from_parameters()`

```python
def create_structural_reforms_from_parameters(parameters, period):
    # ... other reforms ...
    mt_newborn_credit = create_mt_newborn_credit_reform(parameters, period)
    # ...
```

### Step 3: Add to reforms list

```python
    reforms = [
        # ... other reforms ...
        mt_newborn_credit,
    ]

    # Filter out None (inactive reforms)
    reforms = tuple(filter(lambda x: x is not None, reforms))
```

### Step 4: Include in combined reform's `apply()`

```python
    class combined_reform(Reform):
        def apply(self):
            for reform in reforms:
                reform.apply(self)
```

**Note:** The exact registration pattern varies. Some codebases use `for reform in reforms: reform.apply(self)` while others list each explicitly with None guards. Match the existing style in the file.

---

## 9. Test Pattern

Reform tests use standard YAML format with two additions: the `reforms:` key and `in_effect: true`.

```yaml
- name: Single filer with newborn, income below threshold
  period: 2027
  absolute_error_margin: 1
  reforms: policyengine_us.reforms.states.mt.newborn_credit.mt_newborn_credit.mt_newborn_credit
  input:
    gov.contrib.states.mt.newborn_credit.in_effect: true
    people:
      person1:
        age: 30
        is_tax_unit_head: true
        employment_income: 50_000
      child1:
        age: 0
        is_tax_unit_dependent: true
    tax_units:
      tax_unit:
        members: [person1, child1]
        filing_status: SINGLE
    households:
      household:
        members: [person1, child1]
        state_code: MT
  output:
    mt_newborn_credit: 1_000
```

### Required test elements

| Element | Description |
|---------|-------------|
| `reforms:` | Full dotted path to the module-level reform instance |
| `gov.contrib.{...}.in_effect: true` | Enables the reform for this test |
| `state_code: XX` | Ensures `defined_for = StateCode.XX` passes |
| `absolute_error_margin: 1` | Standard tolerance for floating-point |

### The `reforms:` path

The path is the Python import path to the **module-level bypass instance**:

```
reforms: policyengine_us.reforms.states.{st}.{bill_id}.{module}.{instance_name}
```

Example: `policyengine_us.reforms.crfb.agi_surtax.agi_surtax_reform_object`

### Nested `in_effect` in tests

When testing sub-features with their own `in_effect` toggle, set both:

```yaml
  input:
    gov.contrib.crfb.surtax.in_effect: true
    gov.contrib.crfb.surtax.increased_base.in_effect: true
```

### Test coverage guidelines

Aim for comprehensive coverage across these categories:

1. **Basic eligibility** — income under threshold, eligible dependents
2. **Ineligibility** — income over threshold, wrong state, no qualifying members
3. **Filing status variations** — SINGLE, JOINT, HEAD_OF_HOUSEHOLD, SEPARATE, SURVIVING_SPOUSE
4. **Phase-out boundaries** — at start, mid-range, fully phased out
5. **Edge cases** — zero income, exactly at threshold, maximum benefit, minimum floor
6. **Nonrefundable cap** — credit limited to tax liability (if applicable)
7. **Multiple qualifying members** — multiple children, capped count
8. **Reform-off verification** — ensure baseline behavior when `in_effect: false` (for reforms that use `where(in_effect, reform_value, baseline_value)` pattern)
9. **Sub-feature toggles** — test with sub-feature on and off separately

### Test file location

```
tests/policy/contrib/states/{st}/{bill_id}/{reform_name}.yaml
```

For federal/org reforms:
```
tests/policy/contrib/{org}/{topic}/{reform_name}.yaml
```

---

## 10. `__init__.py` Exports

### Reform module init

```python
# reforms/states/{st}/{bill_id}/__init__.py
from .reform_name import create_xx_reform_reform, xx_reform
```

### State init (if first reform for this state)

```python
# reforms/states/{st}/__init__.py
from .bill_id import create_xx_reform_reform, xx_reform
```

---

## 11. Changelog Fragment

```bash
echo "Added [State] [Bill Number] [short description] reform." > changelog.d/{branch-name}.added.md
```

Use `.added` for new reforms, `.fixed` for fixes to existing reforms.

---

## 12. Common Reform Types and Patterns

### A. New refundable credit

**Examples:** MT newborn credit (#7513), CT refundable CTC (#7432), CT tax rebate (#7467), PA CTC (#7438)

Pattern:
1. Parameters: `in_effect`, `amount`, eligibility thresholds, optional phase-out
2. Variable: Calculates credit amount, gates with `defined_for`
3. `modify_parameters`: Adds variable name to state's `credits.refundable` list
4. Reform class: `update_variable()` + `modify_parameters()`

### B. Rate/bracket override

**Examples:** CT SB-100 (#7474), KY HB 13/152 (#7397)

Pattern:
1. Parameters: `in_effect`, new rate brackets (often per filing status)
2. Variable: Overrides existing tax calculation variable
3. Uses `.calc(taxable_income)` on bracket parameters
4. May use dual calculation + `where()` for income-based eligibility

### C. Comprehensive tax reform (multiple variable overrides)

**Examples:** SC H.4216 (#7494)

Pattern:
1. Parameters: `in_effect`, rates, new deduction amounts, credit caps
2. Multiple variables overridden (EITC, deductions, taxable income, tax calculation)
3. Single Reform class with multiple `update_variable()` calls
4. Comments explain why baseline deductions are excluded (avoiding double-counting)

### D. Enhanced existing credit

**Examples:** NY A06774 enhanced CDCC (#7428), CT HB-5009 property tax credit (#7478)

Pattern:
1. Parameters: `in_effect`, match rate or enhanced amounts, income threshold
2. Variable: Overrides existing credit variable
3. Uses `where(eligible_for_enhanced, enhanced_value, standard_value)`
4. Watch for **circular dependencies** — use intermediate variables like `cdcc_potential` instead of `cdcc` if the full variable depends on income tax

### E. Repeal/neutralize reform

**Examples:** Repeal state dependent exemptions (#7342)

Pattern:
1. `neutralize_variable()` zeros out targeted variables
2. `update_variable()` replaces others with reform-specific logic
3. Must handle parameter structure changes across time periods

### F. Federal-level reform

**Examples:** Streamlined EITC (#7110), CTC linear phase-out (#7110), CRFB AGI surtax (#7230)

Pattern:
- Same factory function pattern as state reforms
- Parameters under `gov/contrib/{org}/{topic}/` (no state prefix)
- No `defined_for = StateCode.XX` (applies nationally)
- May use parameter-driven source lists (see Section 7)
- May have nested `in_effect` toggles for sub-features (see Section 3)
- Otherwise identical mechanism

---

## 13. Common Pitfalls

### Circular dependencies
When overriding a variable that feeds into income tax calculation, and income tax feeds back into your variable. **Fix:** Use intermediate variables that break the cycle (e.g., `cdcc_potential` instead of `cdcc`).

### Forgetting `modify_parameters`
New credits that aren't added to the state's credit list won't appear in the tax calculation. Always check if the variable needs to be registered in a credit/tax list.

### Double-counting federal deductions
When a reform uses AGI as the tax base instead of federal taxable income, don't include `state_additions` that undo federal deductions — they're already excluded. Add comments explaining this.

### Hard-coded values in reform variables
Same rule as baseline: ALL numeric values must come from parameters. No `where(eligible, 1000, 0)` — use `where(eligible, p.amount, 0)`.

### Forgetting to filter `None` in reforms list
The `create_xx_reform()` returns `None` when inactive. The reforms list in `reforms.py` must filter these out before combining.

### Phase-out rounding
Check if the legislation specifies rounding rules. Common patterns:
- `np.ceil()` for ceiling (partial increments count as full)
- `np.floor()` for floor
- Round down to nearest $10: `(amount // 10) * 10`

### Incorrect bracket path syntax
When accessing bracket parameters in Python, the bracket index goes on the scale node directly, NOT on a `.brackets` sub-path:
```python
# ✅ Correct
p.rates.single[0].rate
p.rates.single.calc(taxable_income)

# ❌ Wrong
p.rates.single.brackets[0].rate
```

### Missing filing status handling
Many reforms have different thresholds or rates by filing status. Always check if the bill specifies different treatment for joint, single, HOH, etc.

---

## 14. Quick Reference: Reform Implementation Checklist

- [ ] Create `parameters/gov/contrib/states/{st}/{bill_id}/in_effect.yaml` (default: false)
- [ ] Create all policy parameters (amounts, thresholds, rates) with proper metadata and references
- [ ] Create `reforms/states/{st}/{bill_id}/{reform_name}.py` with:
  - [ ] Inner factory function (`create_xx()`) defining variables + Reform class
  - [ ] Outer factory function (`create_xx_reform()`) with 5-year lookahead
  - [ ] Module-level `bypass=True` instance
- [ ] Create `reforms/states/{st}/{bill_id}/__init__.py` with exports
- [ ] Register in `reforms/reforms.py` (import, instantiate, add to list, add to combined apply)
- [ ] If new credit: add `modify_parameters()` to inject into credit list
- [ ] Create `tests/policy/contrib/states/{st}/{bill_id}/{reform_name}.yaml`
  - [ ] Include `reforms:` key and `in_effect: true` in every test
  - [ ] Cover eligibility, ineligibility, phase-out, filing statuses, edge cases
  - [ ] If nested `in_effect`: test sub-features independently
- [ ] Create changelog fragment: `changelog.d/{branch-name}.added.md`
- [ ] Run `make format` before committing

---

## 15. Validator Checklist (Reform-Specific)

When validating a reform implementation, check ALL of the following:

| # | Check | What to verify |
|---|-------|----------------|
| 1 | `in_effect.yaml` exists | Default `false`, date `0000-01-01`, under correct `gov/contrib/` path |
| 2 | Parameter path correct | `gov/contrib/states/{st}/{bill}/` or `gov/contrib/{org}/{topic}/` |
| 3 | Factory pattern | Inner `create_xx()` returns Reform class, outer `create_xx_reform()` wraps with check |
| 4 | 5-year lookahead | Outer function scans 5 years forward (or uses in-formula check with justification) |
| 5 | Module-level instance | `xx_reform = create_xx_reform(None, None, bypass=True)` exported |
| 6 | Registration | Import + instantiate + list + combined apply in `reforms.py` |
| 7 | `modify_parameters` | Present if reform adds a NEW credit/tax to a list parameter |
| 8 | Test `reforms:` key | Every test has correct dotted import path to module-level instance |
| 9 | Test `in_effect: true` | Every test enables the reform via `gov.contrib.{...}.in_effect: true` |
| 10 | No hard-coded values | All amounts, rates, thresholds from parameters |
| 11 | `defined_for` | State reforms have `defined_for = StateCode.XX` |
| 12 | Filing status coverage | Tests cover at least SINGLE and JOINT |
