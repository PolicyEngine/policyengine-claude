---
name: us-household-analysis
description: Household-level impact analysis patterns for US policy reforms - define households, calculate tax/benefit changes, generate results.json
---

# US Household Analysis

Patterns for analyzing how US policy reforms affect specific household types. Use this skill when a blog post needs household-level case studies (e.g., "a single parent earning $50,000 sees a $252 increase").

## When to Use This Skill

- Blog posts showing how a reform affects representative households
- Calculators that let users enter their own household details
- Case studies comparing reform impacts across filing statuses, income levels, or family sizes
- Budget constraint / marginal tax rate analysis across an income range

For population-level microsimulation (deciles, poverty rates, aggregate budget impact), see blog-pipeline-skill instead.

---

## Household Structure

A US household in PolicyEngine has 6 entity groups. Every person must belong to one of each:

| Entity | Purpose | Key variables |
|--------|---------|---------------|
| `household` | Physical dwelling | `state_code_str`, `household_net_income` |
| `tax_unit` | IRS filing unit | `filing_status`, `income_tax`, `eitc`, `ctc` |
| `family` | Census family | `family_id` |
| `spm_unit` | Supplemental Poverty Measure unit | `snap`, `ssi`, `tanf` |
| `marital_unit` | Married/unmarried pair | `marital_unit_id` |
| `person` | Individual | `age`, `employment_income`, `income_tax` |

---

## Approach 1: Single Household (calculate_household_impact)

The simplest way to calculate one household's taxes and benefits.

```python
from policyengine.tax_benefit_models.us import (
    USHouseholdInput,
    calculate_household_impact,
)

# Single filer, no children, $50k income
household = USHouseholdInput(
    people=[
        {"age": 35, "employment_income": 50_000, "is_tax_unit_head": True}
    ],
    tax_unit={"filing_status": "SINGLE"},
    household={"state_code_str": "CA"},
    year=2026,
)
result = calculate_household_impact(household)

# Access results by entity
net_income = result.household["household_net_income"]
income_tax = result.tax_unit[0]["income_tax"]
eitc = result.tax_unit[0]["eitc"]
snap = result.spm_unit[0]["snap"]
```

### Common Household Types

**Single filer, no children:**
```python
USHouseholdInput(
    people=[
        {"age": 35, "employment_income": 50_000, "is_tax_unit_head": True}
    ],
    tax_unit={"filing_status": "SINGLE"},
    household={"state_code_str": "CA"},
    year=2026,
)
```

**Single parent, 2 children:**
```python
USHouseholdInput(
    people=[
        {"age": 35, "employment_income": 50_000, "is_tax_unit_head": True},
        {"age": 8, "is_tax_unit_dependent": True},
        {"age": 5, "is_tax_unit_dependent": True},
    ],
    tax_unit={"filing_status": "HEAD_OF_HOUSEHOLD"},
    household={"state_code_str": "TX"},
    year=2026,
)
```

**Married couple, 2 children:**
```python
USHouseholdInput(
    people=[
        {"age": 40, "employment_income": 80_000, "is_tax_unit_head": True},
        {"age": 38, "employment_income": 40_000, "is_tax_unit_spouse": True},
        {"age": 10, "is_tax_unit_dependent": True},
        {"age": 7, "is_tax_unit_dependent": True},
    ],
    tax_unit={"filing_status": "JOINT"},
    household={"state_code_str": "NY"},
    year=2026,
)
```

**Senior, retired:**
```python
USHouseholdInput(
    people=[
        {"age": 70, "social_security": 24_000, "is_tax_unit_head": True}
    ],
    tax_unit={"filing_status": "SINGLE"},
    household={"state_code_str": "FL"},
    year=2026,
)
```

---

## Approach 2: Situation Dict (Simulation)

The pattern used by existing analysis repos. More verbose but supports axes for income sweeps.

```python
from policyengine_us import Simulation

situation = {
    "people": {
        "adult": {
            "age": {"2026": 35},
            "employment_income": {"2026": 50_000},
        },
        "child1": {"age": {"2026": 8}},
        "child2": {"age": {"2026": 5}},
    },
    "families": {
        "family": {"members": ["adult", "child1", "child2"]}
    },
    "tax_units": {
        "tax_unit": {"members": ["adult", "child1", "child2"]}
    },
    "spm_units": {
        "spm_unit": {"members": ["adult", "child1", "child2"]}
    },
    "marital_units": {
        "marital_unit": {"members": ["adult"]}
    },
    "households": {
        "household": {
            "members": ["adult", "child1", "child2"],
            "state_name": {"2026": "TX"},
        }
    },
}

sim = Simulation(situation=situation)
net_income = sim.calculate("household_net_income", "2026")
income_tax = sim.calculate("income_tax", "2026")
ctc = sim.calculate("ctc", "2026")
```

### Income Sweep with Axes

Calculate impacts across an income range in a single simulation (much faster than looping):

```python
situation = {
    "people": {
        "adult": {"age": {"2026": 35}},
        "child1": {"age": {"2026": 8}},
    },
    "families": {"family": {"members": ["adult", "child1"]}},
    "tax_units": {"tax_unit": {"members": ["adult", "child1"]}},
    "spm_units": {"spm_unit": {"members": ["adult", "child1"]}},
    "marital_units": {"marital_unit": {"members": ["adult"]}},
    "households": {
        "household": {
            "members": ["adult", "child1"],
            "state_name": {"2026": "CA"},
        }
    },
    "axes": [[{
        "name": "employment_income",
        "count": 501,
        "min": 0,
        "max": 250_000,
        "period": "2026",
    }]],
}

sim = Simulation(situation=situation)
incomes = sim.calculate("employment_income", "2026")
net_incomes = sim.calculate("household_net_income", "2026")
```

---

## Approach 3: Reform Comparison

Compare baseline vs reform for the same household.

### With calculate_household_impact

```python
from policyengine.core import Policy, Parameter, ParameterValue
from policyengine.tax_benefit_models.us import (
    USHouseholdInput,
    calculate_household_impact,
    us_latest,
)
import datetime

# Define reform
param = Parameter(
    name="gov.irs.credits.ctc.amount.base_amount",
    tax_benefit_model_version=us_latest,
    data_type=float,
)
pv = ParameterValue(
    parameter=param,
    start_date=datetime.date(2026, 1, 1),
    end_date=datetime.date(2026, 12, 31),
    value=5000,
)
policy = Policy(name="CTC Expansion", parameter_values=[pv])

household = USHouseholdInput(
    people=[
        {"age": 35, "employment_income": 50_000, "is_tax_unit_head": True},
        {"age": 8, "is_tax_unit_dependent": True},
    ],
    tax_unit={"filing_status": "HEAD_OF_HOUSEHOLD"},
    household={"state_code_str": "CA"},
    year=2026,
)

baseline = calculate_household_impact(household)
reform = calculate_household_impact(household, policy=policy)

change = reform.household["household_net_income"] - baseline.household["household_net_income"]
```

### With Simulation + Situation Dict

```python
reform_dict = {
    "gov.irs.credits.ctc.amount.base_amount": {
        "2026-01-01.2026-12-31": 5000
    }
}

sim_baseline = Simulation(situation=situation)
sim_reform = Simulation(situation=situation, reform=reform_dict)

baseline_net = sim_baseline.calculate("household_net_income", "2026")
reform_net = sim_reform.calculate("household_net_income", "2026")
change = reform_net - baseline_net
```

---

## Impact Types

### Net income change

The most common household impact. Shows the bottom-line dollar difference.

```python
baseline_net = baseline.household["household_net_income"]
reform_net = reform.household["household_net_income"]
change = reform_net - baseline_net
```

### Tax component breakdown

Show which specific taxes/credits change and by how much.

```python
components = {
    "Income tax": reform.tax_unit[0]["income_tax"] - baseline.tax_unit[0]["income_tax"],
    "Payroll tax": reform.tax_unit[0]["employee_payroll_tax"] - baseline.tax_unit[0]["employee_payroll_tax"],
    "EITC": reform.tax_unit[0]["eitc"] - baseline.tax_unit[0]["eitc"],
    "CTC": reform.tax_unit[0]["ctc"] - baseline.tax_unit[0]["ctc"],
    "SNAP": reform.spm_unit[0]["snap"] - baseline.spm_unit[0]["snap"],
}
```

### Effective marginal tax rate

How much of an additional dollar of earnings the household keeps.

```python
# Using axes for smooth marginal rate curve
situation_axes = {
    # ... household setup ...
    "axes": [[{
        "name": "employment_income",
        "count": 1001,
        "min": 0,
        "max": 200_000,
        "period": "2026",
    }]],
}

sim = Simulation(situation=situation_axes)
incomes = sim.calculate("employment_income", "2026")
net_incomes = sim.calculate("household_net_income", "2026")

# Marginal rate = 1 - (change in net income / change in gross income)
marginal_rates = 1 - np.diff(net_incomes) / np.diff(incomes)
```

### Benefit eligibility cliff

Show where benefits phase out sharply.

```python
sim = Simulation(situation=situation_axes)
incomes = sim.calculate("employment_income", "2026")
snap = sim.calculate("snap", "2026")
medicaid = sim.calculate("medicaid", "2026")
eitc = sim.calculate("eitc", "2026")

# Plot each benefit against income to show cliffs
```

---

## Charts for Household Posts

Produce these charts for household-level analysis. See blog-pipeline-skill for full Plotly styling details and additional chart types.

### Required charts

| Chart | What it shows | When to use |
|-------|---------------|-------------|
| **Net income curve** | Baseline vs reform net income across earnings range | Every household post |
| **Marginal tax rate curve** | Effective MTR across earnings range, baseline vs reform | Posts about tax rate changes or benefit cliffs |
| **Component breakdown bar** | Which taxes/credits drive the net income change | Posts where multiple programs interact |

### Optional charts (use when relevant)

| Chart | What it shows | When to use |
|-------|---------------|-------------|
| **Benefit cliff chart** | Individual benefit amounts (EITC, CTC, SNAP) vs income | Posts about benefit interactions or phase-outs |
| **State comparison bar** | Same household, different states | Posts about state-level variation |
| **Filing status comparison** | Same income, different filing statuses | Posts about marriage penalties or filing status effects |
| **Waterfall** | Tax component decomposition for one household | Posts breaking down a complex reform |

### Custom charts

For topic-specific visuals not listed above, follow these rules:
- Use PE brand colors: `TEAL = "#39C6C0"`, `BLUE = "#2C6496"`, `RED = "#DC2626"`
- Plotly with `template="plotly_white"`, `font=dict(family="Inter, sans-serif")`
- Save as PNG at 1200x600, scale=2
- Write alt text with chart type and 2-3 key data points
- Include in results.json under `"charts"` with `url`, `alt`, `source_line`, `source_url`

## Tables for Household Posts

### Required tables

| Table | Columns | When to use |
|-------|---------|-------------|
| **Household impact table** | Household type, Income, Filing status, Net income change | Every household post |
| **Component breakdown table** | Component (income tax, EITC, CTC, SNAP...), Baseline, Reform, Change | Posts where multiple programs interact |

### Optional tables

| Table | Columns | When to use |
|-------|---------|-------------|
| **Parameter comparison** | Parameter, Current law, Reform | Posts introducing the reform details |
| **State comparison** | State, Net income change, Key driver | Posts about state variation |
| **Income sweep summary** | Income level, Baseline net, Reform net, Change, MTR | Posts with detailed income range analysis |
| **Benefit eligibility** | Income level, EITC, CTC, SNAP, Medicaid, Total benefits | Posts about benefit cliffs |

### Custom tables

For topic-specific tables, follow these rules:
- Include in results.json with `headers`, `rows`, `source_line`, `source_url`
- Pre-format values as display strings ("$1,200", "12.4%")
- Use `{{table:name}}` in blog post markdown
- Keep under 15 rows

---

## Generating results.json for Household Analysis

Household analyses produce results.json with the same schema as microsimulation analyses, but values come from specific households rather than population aggregates. Use `tracked_value()` for automatic source line tracking and `ResultsJson` for schema validation.

```python
from policyengine.results import (
    ResultsJson, ResultsMetadata, ValueEntry, TableEntry, tracked_value,
)

REPO = "PolicyEngine/ctc-expansion"

households = {
    "single_no_kids": {"filing": "SINGLE", "income": 50_000, "children": 0},
    "single_parent_2": {"filing": "HOH", "income": 50_000, "children": 2},
    "married_2": {"filing": "JOINT", "income": 100_000, "children": 2},
}

values = {}
rows = []
for name, params in households.items():
    # ... calculate baseline and reform ...
    change = reform_net - baseline_net

    # tracked_value() captures this line number automatically
    values[f"{name}_change"] = ValueEntry(**tracked_value(
        value=float(change),
        display=f"${abs(change):,.0f}",
        repo=REPO,
    ))
    rows.append([name, f"${params['income']:,}", f"${change:,.0f}"])

import inspect
table_line = inspect.currentframe().f_lineno
tables = {
    "household_impacts": TableEntry(
        title="Household impact by family type",
        headers=["Household", "Income", "Net income change"],
        rows=rows,
        source_line=table_line,
        source_url=f"https://github.com/{REPO}/blob/main/analysis.py#L{table_line}",
    ),
}

results = ResultsJson(
    metadata=ResultsMetadata(
        title="CTC Expansion Household Impacts",
        repo=REPO,
        country_id="us",
        year=2026,
    ),
    values=values,
    tables=tables,
)
results.write("results.json")
```

---

## Writing Household Case Studies

Follow policyengine-writing-skill for all blog post text.

**✅ Correct (specific, neutral, active):**
```
A single parent of two children earning $50,000 sees a $1,000 increase
in net income: $800 from the expanded CTC and $200 from lower income
tax withholding.
```

**❌ Wrong (vague, value judgment):**
```
Working families see significant benefits from the reform, with
substantial increases to their take-home pay.
```

**✅ Correct (shows calculation):**
```
A married couple with two children earning $100,000 receives $10,000
in CTC under the reform, compared to $4,000 under current law — a
$6,000 increase ($3,000 per child × 2 children).
```

**❌ Wrong (hides calculation):**
```
A married couple sees their CTC more than double under the reform.
```

---

## Common US Variables

| Variable | Entity | Description |
|----------|--------|-------------|
| `household_net_income` | household | Total income after taxes and benefits |
| `income_tax` | tax_unit | Federal income tax liability |
| `state_income_tax` | tax_unit | State income tax liability |
| `employee_payroll_tax` | tax_unit | Employee-side payroll taxes |
| `eitc` | tax_unit | Earned Income Tax Credit |
| `ctc` | tax_unit | Child Tax Credit |
| `snap` | spm_unit | SNAP (food stamps) benefits |
| `ssi` | spm_unit | Supplemental Security Income |
| `tanf` | spm_unit | Temporary Assistance for Needy Families |
| `medicaid` | person | Medicaid eligibility value |
| `employment_income` | person | Wages and salary |
| `self_employment_income` | person | Self-employment income |
| `social_security` | person | Social Security benefits |

---

## Checklist

Before publishing household analysis:

- [ ] All 6 entity groups defined for each household (household, tax_unit, family, spm_unit, marital_unit, person)
- [ ] Filing status matches household composition (SINGLE, JOINT, HEAD_OF_HOUSEHOLD)
- [ ] State specified via `state_code_str` or `state_name`
- [ ] Representative households cover relevant filing statuses and income ranges
- [ ] Baseline and reform both calculated for the same household
- [ ] Component breakdown shows which taxes/benefits drive the net change
- [ ] All values in results.json with `source_line` and `source_url`
- [ ] Blog text uses `{{}}` template references, not hard-coded numbers
- [ ] Neutral language — no value judgments on who "benefits" or "loses"
- [ ] Calculations shown explicitly (e.g., "$3,000 per child × 2 = $6,000")

---

## Resources

- blog-pipeline-skill — results.json schema, template syntax, chart generation
- policyengine-writing-skill — neutral tone, active voice, quantitative precision
- policyengine-analysis-skill — population-level patterns, Plotly charts
- policyengine-us-skill — US tax/benefit system domain knowledge
