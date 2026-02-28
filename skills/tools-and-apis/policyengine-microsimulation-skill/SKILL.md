---
name: policyengine-microsimulation
description: |
  ALWAYS USE THIS SKILL for PolicyEngine microsimulation, population-level analysis, winners/losers calculations.
  Triggers: "microsimulation", "share who would lose/gain", "policy impact", "national average", "weighted analysis",
  "cost", "revenue impact", "budgetary", "estimate the cost", "federal revenues", "tax revenue", "budget score",
  "how much would it cost", "how much would the policy cost", "total cost of", "aggregate impact",
  "cost to the government", "revenue loss", "fiscal impact",
  "poverty impact", "child poverty", "deep poverty", "poverty rate", "poverty reduction",
  "how many people lifted out of poverty", "SPM poverty", "distributional impact",
  "state tax", "state-level", "California", "New York",
  "UBI", "universal basic income", "flat tax", "standard deduction",
  "winners and losers", "winners", "losers",
  "inequality", "Gini", "decile",
  "SALT", "marginal tax rate", "effective tax rate".
  NOT for single-household calculations like "what would my benefit be" — use policyengine-us or policyengine-uk for those.
  Use this skill's code pattern, but explore the codebase to find specific parameter paths if needed.
---

# PolicyEngine Microsimulation

## Documentation References

- **Microsimulation API**: https://policyengine.github.io/policyengine-us/usage/microsimulation.html
- **Parameter Discovery**: https://policyengine.github.io/policyengine-us/usage/parameter-discovery.html
- **Reform.from_dict()**: https://policyengine.github.io/policyengine-core/usage/reforms.html

## CRITICAL: Use calc() with MicroSeries - No Manual Weights Ever

**MicroSeries handles all weighting automatically. Never access .weights or do manual weight math.**

### NEVER strip weights with .values

`calc()` and `calculate()` return MicroSeries with embedded weights. Calling `.values` strips them and returns a plain numpy array where `.mean()` is **unweighted**.

```python
# ❌ WRONG - .values strips weights, .mean() is UNWEIGHTED
result = sim.calc("household_net_income", period=2026).values
wrong_mean = result.mean()  # Unweighted!

# ❌ WRONG - same problem with .to_numpy()
result = sim.calc("household_net_income", period=2026).to_numpy()

# ✅ CORRECT - keep as MicroSeries, all operations are weighted
result = sim.calc("household_net_income", period=2026)
correct_mean = result.mean()  # Weighted automatically!
```

### Correct patterns

```python
# ✅ CORRECT - MicroSeries handles everything
change = reformed.calc('household_net_income', period=2026, map_to='person') - \
         baseline.calc('household_net_income', period=2026, map_to='person')
loser_share = (change < 0).mean()  # Weighted automatically!

# ❌ WRONG - never access .weights or do manual math
loser_share = change.weights[change.values < 0].sum() / change.weights.sum()
```

## Quick start

```python
from policyengine_us import Microsimulation
from policyengine_core.reforms import Reform

baseline = Microsimulation()
reform = Reform.from_dict({
    'gov.irs.credits.ctc.amount.base[0].amount': {'2026-01-01.2100-12-31': 3000}
}, 'policyengine_us')
reformed = Microsimulation(reform=reform)

# calc() returns MicroSeries - all operations are weighted automatically
baseline_income = baseline.calc('household_net_income', period=2026, map_to='person')
reformed_income = reformed.calc('household_net_income', period=2026, map_to='person')
change = reformed_income - baseline_income

# Weighted stats - no manual weight handling needed!
print(f"Average impact: ${change.mean():,.0f}")
print(f"Total cost: ${change.sum()/1e9:,.1f}B")
print(f"Share losing: {(change < 0).mean():.1%}")
```

## API methods

- `Microsimulation.calc()` (US) — returns MicroSeries (weighted). Use this for all US microsimulation.
- `Microsimulation.calculate()` (UK) — returns MicroSeries (weighted). Use this for all UK microsimulation.
- Both return MicroSeries with automatic weighting. Use `.sum()`, `.mean()`, arithmetic operators.

## Creating reforms

### US (policyengine_us.Microsimulation)
```python
from policyengine_us import Microsimulation
from policyengine_core.reforms import Reform

reform = Reform.from_dict({
    'gov.irs.credits.ctc.amount.base[0].amount': {'2026-01-01.2100-12-31': 3600},
}, 'policyengine_us')

baseline = Microsimulation()
reformed = Microsimulation(reform=reform)
```

### UK (policyengine_uk.Microsimulation)
```python
from policyengine_uk import Microsimulation

# UK: pass reform dict directly — do NOT use Reform.from_dict()
reform = {
    'gov.hmrc.income_tax.allowances.personal_allowance.amount': {'2026-01-01.2100-12-31': 15000}
}

baseline = Microsimulation()
reformed = Microsimulation(reform=reform)
```

**IMPORTANT**: For UK, pass the dict directly to `Microsimulation(reform=dict)`. `Reform.from_dict()` works for US but causes errors in UK.

### Dataset argument
- **National**: Omit dataset argument entirely (default is correct)
- **State-level**: `Microsimulation(dataset='hf://policyengine/policyengine-us-data/states/NY.h5')`
- **Never** pass short strings like `dataset="cps_2024"` — use full HF URLs or omit

## Available Datasets (HuggingFace)

```python
# National (default)
sim = Microsimulation()

# State-level
sim = Microsimulation(dataset='hf://policyengine/policyengine-us-data/states/NY.h5')

# Congressional district - SEE policyengine-district-analysis skill for full examples
sim = Microsimulation(dataset='hf://policyengine/policyengine-us-data/districts/NY-17.h5')
```

**For congressional district analysis** (representative's constituents, district-level impacts), use the `policyengine-district-analysis` skill which has complete examples.

### Memory considerations

State-level datasets are large (~590MB each). Loading two Microsimulation objects simultaneously (baseline + reformed) requires ~2GB+ RAM. Options:
- **Preferred**: Use the national dataset (default) — it includes all states with proper weighting
- **If state-calibrated weights needed**: Compute baseline values first, delete the baseline object (`del baseline`), then create the reformed simulation

## Key MicroSeries Methods

MicroSeries (from [microdf](https://github.com/PolicyEngine/microdf)) handles all weighting automatically — see the `microdf` skill for full documentation.

```python
income = sim.calc('household_net_income', period=2026, map_to='person')

# Basic weighted statistics
income.mean()           # Weighted mean
income.sum()            # Weighted sum
income.median()         # Weighted median
(income > 50000).mean() # Weighted share meeting condition

# Inequality metrics (see microdf skill for more)
income.gini()           # Weighted Gini coefficient
```

### Inequality & Distributional Analysis

Use built-in MicroSeries methods — never reimplement Gini or other inequality metrics manually:

```python
baseline_income = baseline.calc('household_net_income', period=2026, map_to='person')
reformed_income = reformed.calc('household_net_income', period=2026, map_to='person')

# Gini coefficient change
print(f"Baseline Gini: {baseline_income.gini():.4f}")
print(f"Reform Gini:   {reformed_income.gini():.4f}")

# Poverty rate (boolean MicroSeries — .mean() gives weighted rate)
baseline_in_poverty = baseline.calc('person_in_poverty', period=2026, map_to='person')
print(f"SPM poverty rate: {baseline_in_poverty.mean():.1%}")

# Decile-level analysis
income.decile_rank()    # Assign decile ranks (1-10)
```

## Poverty analysis

### Overall and child poverty

Use `household_weight` (the only calibrated weight) with MicroSeries arithmetic for all poverty calculations. No `.values` or `np.sum()` needed.

```python
from policyengine_us import Microsimulation

baseline = Microsimulation()
reformed = Microsimulation(reform=reform)

YEAR = 2026

# Overall poverty rate — .mean() gives weighted rate automatically
baseline_in_poverty = baseline.calc('person_in_poverty', period=YEAR, map_to='person')
reform_in_poverty = reformed.calc('person_in_poverty', period=YEAR, map_to='person')
baseline_poverty_rate = baseline_in_poverty.mean()
reform_poverty_rate = reform_in_poverty.mean()
print(f"Poverty: {baseline_poverty_rate:.1%} → {reform_poverty_rate:.1%}")

# Child poverty rate — filter by is_child, then .mean()
is_child = baseline.calc('is_child', period=YEAR)
baseline_child_pov_rate = (baseline_in_poverty * is_child).sum() / is_child.sum()
reform_child_pov_rate = (reform_in_poverty * is_child).sum() / is_child.sum()
print(f"Child poverty: {baseline_child_pov_rate:.1%} → {reform_child_pov_rate:.1%}")

# People lifted out of poverty
total_people = baseline_in_poverty.sum() / baseline_in_poverty.mean()  # total weighted pop
people_lifted = (baseline_poverty_rate - reform_poverty_rate) * total_people
children_lifted = (baseline_child_pov_rate - reform_child_pov_rate) * is_child.sum()
```

> **WARNING: Never subtract boolean MicroSeries directly.** NumPy 2.4+ raises `TypeError` on boolean subtraction (`True - False`). Use `.mean()` to get float rates first, then subtract:
> ```python
> # ❌ DON'T: diff = baseline_in_poverty - reform_in_poverty  # TypeError in numpy 2.4+
> # ✅ DO: compute rates with .mean(), then subtract floats
> baseline_rate = baseline_in_poverty.mean()
> reform_rate = reform_in_poverty.mean()
> reduction_pp = baseline_rate - reform_rate
> ```

### Deep poverty

`in_deep_poverty` is at the SPM unit level. Use `household_weight` mapped to the appropriate entity level:

```python
# Deep poverty — person-level via map_to
baseline_in_deep_poverty = baseline.calc('in_deep_poverty', period=YEAR, map_to='person')
reform_in_deep_poverty = reformed.calc('in_deep_poverty', period=YEAR, map_to='person')

baseline_deep_rate = baseline_in_deep_poverty.mean()
reform_deep_rate = reform_in_deep_poverty.mean()
print(f"Deep poverty: {baseline_deep_rate:.1%} → {reform_deep_rate:.1%}")

# Deep child poverty rate
is_child = baseline.calc('is_child', period=YEAR)
baseline_deep_child_rate = (baseline_in_deep_poverty * is_child).sum() / is_child.sum()
reform_deep_child_rate = (reform_in_deep_poverty * is_child).sum() / is_child.sum()
print(f"Deep child poverty: {baseline_deep_child_rate:.1%} → {reform_deep_child_rate:.1%}")
```

### Subgroup analysis note

MicroSeries arithmetic handles subgroup analysis — you should rarely need `.values`. Multiply by a boolean MicroSeries to filter (e.g., `pov * is_child * pw`) and use `.sum()` / `.mean()` directly.

## UK microsimulation

### Key differences from US

- **UK uses `.calculate()`, NOT `.calc()`** — `policyengine_uk.Microsimulation` does NOT have a `.calc()` method at all. Always use `.calculate()`.
- **UK reform**: Pass a plain dict directly to `Microsimulation(reform=dict)`. Do NOT use `Reform.from_dict()` — it causes errors with UK.
- **UK poverty variables**: `in_poverty_bhc` (before housing costs) and `in_poverty_ahc` (after housing costs) — both at **household** level. UK poverty analysis typically reports both BHC and AHC rates; always note which measure you are using.
- **UK entity structure**: `household` (not SPM unit), `benunit` (benefit unit), `person`. Use `household_weight` and `household_count_people` for person-weighted rates.

### Example: UK personal allowance reform with poverty analysis

```python
from policyengine_uk import Microsimulation

reform = {'gov.hmrc.income_tax.allowances.personal_allowance.amount': {'2026-01-01.2100-12-31': 15000}}

baseline = Microsimulation()
reformed = Microsimulation(reform=reform)

# Cost
baseline_income = baseline.calculate('household_net_income', period=2026)
reform_income = reformed.calculate('household_net_income', period=2026)
cost = (reform_income - baseline_income).sum()

# Poverty (BHC) — map to person level for .mean()
baseline_in_poverty = baseline.calculate('in_poverty_bhc', period=2026, map_to='person')
reform_in_poverty = reformed.calculate('in_poverty_bhc', period=2026, map_to='person')
baseline_rate = baseline_in_poverty.mean()
reform_rate = reform_in_poverty.mean()

print(f"Cost: £{cost / 1e9:,.1f}B")
print(f"Poverty (BHC): {baseline_rate:.1%} → {reform_rate:.1%}")
```

## CRITICAL: Budgetary impact calculation

### Start with a BOTEC range before running code, and flag if the point estimate diverges

### Use `household_net_income` for total cost

**The budgetary cost of a reform is the change in `household_net_income`, NOT the change in the
directly-modified program variable.** A reform that changes one program (e.g., CTC) can have
cascading effects on other taxes and benefits through interactions (refundability, phase-outs,
benefit clawbacks). Summing only the program-specific variable will undercount the true cost.

This matches the pattern used in the PolicyEngine API (`policyengine-api/endpoints/economy/compare.py`).

```python
# Total budgetary cost = change in household_net_income
baseline_hni = baseline.calc('household_net_income', period=YEAR).sum()
reformed_hni = reformed.calc('household_net_income', period=YEAR).sum()
total_cost = (reformed_hni - baseline_hni) / 1e9
print(f"Total budgetary cost: ${total_cost:,.1f}B")

# Break out by federal taxes, state/local taxes, and benefits
federal_tax_cost = (baseline.calc('income_tax', period=YEAR).sum() -
                    reformed.calc('income_tax', period=YEAR).sum()) / 1e9
state_tax_cost = (baseline.calc('state_income_tax', period=YEAR).sum() -
                  reformed.calc('state_income_tax', period=YEAR).sum()) / 1e9
benefit_cost = (reformed.calc('household_benefits', period=YEAR).sum() -
                baseline.calc('household_benefits', period=YEAR).sum()) / 1e9

print(f"Federal income tax revenue loss: ${federal_tax_cost:,.1f}B")
print(f"State/local tax revenue loss: ${state_tax_cost:,.1f}B")
print(f"Benefit spending increase: ${benefit_cost:,.1f}B")
```

**Why not sum the program variable directly?** Example: making the CTC fully refundable
shifts credits from non-refundable to refundable, changing `income_tax` by much more than
the `ctc` variable itself changes. The `household_net_income` change captures the full effect.

### Per-program decomposition

Individual program changes are still useful for understanding *where* the cost comes from,
but they don't substitute for the total `household_net_income` cost above.

```python
programs = ["income_tax", "ctc", "eitc", "snap", "ssi", "household_benefits"]
for prog in programs:
    b = baseline.calc(prog, period=YEAR).sum()
    r = reformed.calc(prog, period=YEAR).sum()
    if abs(r - b) > 1e6:
        print(f"{prog}: ${(r - b) / 1e9:+.1f}B")
```

## Current law context

**Always check baseline parameter values before interpreting reform impacts.** Tax law changes frequently (TCJA, OBBBA, etc.). Use `CountryTaxBenefitSystem().parameters` to look up current-law values:

```python
from policyengine_us import CountryTaxBenefitSystem
p = CountryTaxBenefitSystem().parameters
print(p.gov.irs.credits.ctc.amount.base("2026-01-01"))
print(p.gov.irs.credits.ctc.refundable.fully_refundable("2026-01-01"))
```

## Finding parameter paths

```bash
grep -r "salt" policyengine_us/parameters/gov/irs/ --include="*.yaml"
```

**Parameter tree:** `gov.irs.deductions`, `gov.irs.credits`, `gov.states.{state}.tax`

**Patterns:** Filing status variants (SINGLE, JOINT, etc.), bracket syntax `[index]`, date format `'YYYY-MM-DD.YYYY-MM-DD'`

### CRITICAL: Bracket path syntax for scale parameters

When referencing bracket/scale parameters, the bracket index goes directly on the scale node — there is NO `.brackets` in the path.

```python
# ✅ Correct — bracket index on the scale node
'gov.irs.credits.ctc.amount.base[0].amount'
'gov.states.ca.tax.income.rates.single[8].rate'
'gov.states.ca.tax.income.rates.single[8].threshold'

# ❌ Wrong — ".brackets" does not exist in the path
'gov.irs.credits.ctc.amount.base.brackets[0].amount'
'gov.states.ca.tax.income.rates.single.brackets[8].rate'
```

The YAML file has a `brackets:` list, but the parameter tree flattens it. The index attaches to the node containing the brackets (the YAML filename without `.yaml`), not to a child called `brackets`.

To verify a path, inspect the parameter tree:
```python
from policyengine_us import CountryTaxBenefitSystem
p = CountryTaxBenefitSystem().parameters
print(p.gov.irs.credits.ctc.amount.base[0].amount("2026-01-01"))
```

### Two types of bracket parameters

1. **ParameterScale** (marginal rate schedules, single YAML with `brackets:` at root):
   - Path: `parent_node.scale_name[index].rate` or `.threshold`
   - Example: `gov.states.ca.tax.income.rates.single[8].rate`

2. **ParameterNode with indexed children** (folder-based, separate YAML files):
   - Path: `node_name[index].child_name`
   - Example: `gov.irs.credits.ctc.amount.base[0].amount`

Both use `[index]` syntax in Reform.from_dict() — the difference is in the YAML structure. Use `CountryTaxBenefitSystem().parameters` to navigate and verify paths.

## Common variables for microsimulation

### Weights
- `household_weight` — the only calibrated weight. Use `map_to='person'` or `map_to='spm_unit'` to project it to other entity levels.

### Person-level
- `person_in_poverty` — SPM poverty indicator (boolean)
- `is_child` — under 18
- `age`, `employment_income`

### Household-level
- `household_net_income` — net income after taxes/transfers
- `household_count_people` — number of people in household

### SPM unit-level
- `spm_unit_size`, `spm_unit_count_children`
- `in_poverty`, `in_deep_poverty`

### Tax/benefit variables
- `income_tax`, `ctc`, `eitc`, `snap`, `ssi`
