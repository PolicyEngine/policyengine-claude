---
name: uk-household-analysis
description: Household-level impact analysis patterns for UK policy reforms - define households, calculate tax/benefit changes, generate results.json
---

# UK Household Analysis

Patterns for analyzing how UK policy reforms affect specific household types. Use this skill when a blog post needs household-level case studies (e.g., "a single parent earning £30,000 sees a £520 increase in Universal Credit").

## When to Use This Skill

- Blog posts showing how a reform affects representative households
- Calculators that let users enter their own household details
- Case studies comparing reform impacts across family types, income levels, or regions
- Budget constraint / marginal tax rate analysis across an income range

For population-level microsimulation (deciles, poverty rates, aggregate budget impact), see blog-pipeline-skill instead.

---

## Household Structure

A UK household in PolicyEngine has 3 entity groups. Simpler than US — no tax units or SPM units.

| Entity | Purpose | Key variables |
|--------|---------|---------------|
| `household` | Physical dwelling | `region`, `rent`, `council_tax`, `tenure_type`, `hbai_household_net_income` |
| `benunit` | Benefit unit (means-testing unit) | `universal_credit`, `child_benefit`, `would_claim_uc` |
| `person` | Individual | `age`, `employment_income`, `income_tax`, `national_insurance` |

### Benefit Unit vs Household

A household can contain multiple benefit units. A benefit unit is typically:
- A single adult, or
- A couple (married or cohabiting), plus
- Any dependent children

This matters for means-tested benefits like Universal Credit, which are assessed per benefit unit, not per household.

### The `would_claim_*` Flags

UK benefits are not automatic. You must set `would_claim_*` flags to `True` for benefits to be calculated:

| Flag | Benefit | Default |
|------|---------|---------|
| `would_claim_uc` | Universal Credit | False |
| `would_claim_child_benefit` | Child Benefit | False |
| `would_claim_WTC` | Working Tax Credit (legacy) | False |
| `would_claim_CTC` | Child Tax Credit (legacy) | False |
| `would_claim_HB` | Housing Benefit (legacy) | False |
| `would_claim_IS` | Income Support (legacy) | False |
| `would_claim_JSA` | Jobseeker's Allowance | False |
| `would_claim_PC` | Pension Credit | False |

**✅ Correct — benefits will be calculated:**
```python
benunit={"would_claim_uc": True, "would_claim_child_benefit": True}
```

**❌ Wrong — benefits will be zero even if eligible:**
```python
benunit={}  # No would_claim flags set
```

---

## Approach 1: Single Household (calculate_household_impact)

```python
from policyengine.tax_benefit_models.uk import (
    UKHouseholdInput,
    calculate_household_impact,
)

# Single adult earning £35,000
household = UKHouseholdInput(
    people=[{"age": 30, "employment_income": 35_000}],
    household={
        "region": "NORTH_WEST",
        "tenure_type": "RENT_PRIVATELY",
        "rent": 9_600,       # £800/month
        "council_tax": 1_400,
    },
    benunit={
        "would_claim_uc": True,
    },
    year=2026,
)
result = calculate_household_impact(household)

net_income = result.household["hbai_household_net_income"]
income_tax = result.person[0]["income_tax"]
ni = result.person[0]["national_insurance"]
uc = result.benunit[0]["universal_credit"]
```

### Common Household Types

**Single adult, no children, renting:**
```python
UKHouseholdInput(
    people=[{"age": 30, "employment_income": 35_000}],
    household={
        "region": "LONDON",
        "tenure_type": "RENT_PRIVATELY",
        "rent": 15_600,      # £1,300/month
        "council_tax": 1_800,
    },
    benunit={"would_claim_uc": True},
    year=2026,
)
```

**Single parent, 2 children, renting:**
```python
UKHouseholdInput(
    people=[
        {"age": 35, "employment_income": 25_000},
        {"age": 8},
        {"age": 5},
    ],
    household={
        "region": "NORTH_WEST",
        "tenure_type": "RENT_PRIVATELY",
        "rent": 7_200,       # £600/month
        "council_tax": 1_200,
    },
    benunit={
        "would_claim_uc": True,
        "would_claim_child_benefit": True,
    },
    year=2026,
)
```

**Couple, 2 children, homeowner:**
```python
UKHouseholdInput(
    people=[
        {"age": 40, "employment_income": 50_000},
        {"age": 38, "employment_income": 25_000},
        {"age": 10},
        {"age": 7},
    ],
    household={
        "region": "SOUTH_EAST",
        "tenure_type": "OWNER_OCCUPIED",
        "rent": 0,
        "council_tax": 2_400,
    },
    benunit={
        "would_claim_child_benefit": True,
    },
    year=2026,
)
```

**Pensioner, renting:**
```python
UKHouseholdInput(
    people=[{"age": 70, "state_pension": 10_600}],
    household={
        "region": "WEST_MIDLANDS",
        "tenure_type": "RENT_PRIVATELY",
        "rent": 6_000,
        "council_tax": 1_200,
    },
    benunit={
        "would_claim_PC": True,
    },
    year=2026,
)
```

**Disabled adult claiming UC with LCWRA:**
```python
UKHouseholdInput(
    people=[
        {
            "age": 45,
            "employment_income": 10_000,
            "is_disabled_for_benefits": True,
            "uc_limited_capability_for_WRA": True,
        }
    ],
    household={
        "region": "NORTH_EAST",
        "tenure_type": "RENT_PRIVATELY",
        "rent": 6_000,
        "council_tax": 1_000,
    },
    benunit={"would_claim_uc": True},
    year=2026,
)
```

---

## Approach 2: Situation Dict (Simulation)

The pattern used by existing UK analysis repos.

```python
from policyengine_uk import Simulation

situation = {
    "people": {
        "adult": {
            "age": {"2026": 35},
            "employment_income": {"2026": 30_000},
        },
        "child1": {"age": {"2026": 8}},
        "child2": {"age": {"2026": 5}},
    },
    "benunits": {
        "benunit": {
            "members": ["adult", "child1", "child2"],
            "would_claim_uc": {"2026": True},
            "would_claim_child_benefit": {"2026": True},
        }
    },
    "households": {
        "household": {
            "members": ["adult", "child1", "child2"],
            "region": {"2026": "NORTH_WEST"},
            "tenure_type": {"2026": "RENT_PRIVATELY"},
            "rent": {"2026": 7_200},
            "council_tax": {"2026": 1_200},
        }
    },
}

sim = Simulation(situation=situation)
net_income = sim.calculate("hbai_household_net_income", "2026")
income_tax = sim.calculate("income_tax", "2026")
uc = sim.calculate("universal_credit", "2026")
child_benefit = sim.calculate("child_benefit", "2026")
```

### Income Sweep with Axes

```python
situation = {
    "people": {
        "adult": {"age": {"2026": 35}},
        "child1": {"age": {"2026": 8}},
    },
    "benunits": {
        "benunit": {
            "members": ["adult", "child1"],
            "would_claim_uc": {"2026": True},
            "would_claim_child_benefit": {"2026": True},
        }
    },
    "households": {
        "household": {
            "members": ["adult", "child1"],
            "region": {"2026": "LONDON"},
            "tenure_type": {"2026": "RENT_PRIVATELY"},
            "rent": {"2026": 12_000},
            "council_tax": {"2026": 1_600},
        }
    },
    "axes": [[{
        "name": "employment_income",
        "count": 501,
        "min": 0,
        "max": 100_000,
        "period": "2026",
    }]],
}

sim = Simulation(situation=situation)
incomes = sim.calculate("employment_income", "2026")
net_incomes = sim.calculate("hbai_household_net_income", "2026")
```

---

## Approach 3: Reform Comparison

### With calculate_household_impact

```python
from policyengine.core import Policy, Parameter, ParameterValue
from policyengine.tax_benefit_models.uk import (
    UKHouseholdInput,
    calculate_household_impact,
    uk_latest,
)
import datetime

# Reform: increase UC standard allowance
param = Parameter(
    name="gov.dwp.universal_credit.standard_allowance.amount.single.over_25",
    tax_benefit_model_version=uk_latest,
    data_type=float,
)
pv = ParameterValue(
    parameter=param,
    start_date=datetime.date(2026, 1, 1),
    end_date=datetime.date(2026, 12, 31),
    value=500,  # Monthly amount
)
policy = Policy(name="UC Increase", parameter_values=[pv])

household = UKHouseholdInput(
    people=[{"age": 30, "employment_income": 15_000}],
    household={
        "region": "NORTH_WEST",
        "tenure_type": "RENT_PRIVATELY",
        "rent": 7_200,
        "council_tax": 1_000,
    },
    benunit={"would_claim_uc": True},
    year=2026,
)

baseline = calculate_household_impact(household)
reform = calculate_household_impact(household, policy=policy)

change = (
    reform.household["hbai_household_net_income"]
    - baseline.household["hbai_household_net_income"]
)
```

### With Simulation + Situation Dict

```python
reform_dict = {
    "gov.dwp.universal_credit.standard_allowance.amount.single.over_25": {
        "2026-01-01.2026-12-31": 500
    }
}

sim_baseline = Simulation(situation=situation)
sim_reform = Simulation(situation=situation, reform=reform_dict)

baseline_net = sim_baseline.calculate("hbai_household_net_income", "2026")
reform_net = sim_reform.calculate("hbai_household_net_income", "2026")
change = reform_net - baseline_net
```

---

## Impact Types

### Net income change

```python
baseline_net = baseline.household["hbai_household_net_income"]
reform_net = reform.household["hbai_household_net_income"]
change = reform_net - baseline_net
```

### Tax and benefit component breakdown

```python
components = {
    "Income tax": reform.person[0]["income_tax"] - baseline.person[0]["income_tax"],
    "National Insurance": reform.person[0]["national_insurance"] - baseline.person[0]["national_insurance"],
    "Universal Credit": reform.benunit[0]["universal_credit"] - baseline.benunit[0]["universal_credit"],
    "Child Benefit": reform.benunit[0]["child_benefit"] - baseline.benunit[0]["child_benefit"],
    "Council Tax Benefit": reform.benunit[0].get("council_tax_benefit", 0) - baseline.benunit[0].get("council_tax_benefit", 0),
}
```

### Effective marginal tax rate

```python
sim = Simulation(situation=situation_with_axes)
incomes = sim.calculate("employment_income", "2026")
net_incomes = sim.calculate("hbai_household_net_income", "2026")

marginal_rates = 1 - np.diff(net_incomes) / np.diff(incomes)
```

### UC taper and benefit withdrawal

Universal Credit tapers at 55p per £1 of net earnings above the work allowance. This creates effective marginal rates above the statutory tax rate.

```python
sim = Simulation(situation=situation_with_axes)
incomes = sim.calculate("employment_income", "2026")
uc = sim.calculate("universal_credit", "2026")

# Show where UC phases out
import plotly.graph_objects as go
fig = go.Figure()
fig.add_trace(go.Scatter(x=incomes, y=uc, name="Universal Credit"))
fig.update_layout(
    xaxis_title="Employment income (£)",
    yaxis_title="Universal Credit (£/year)",
)
```

---

## UK Regions

The `region` field affects housing costs, council tax, and some benefit rates.

| Region code | Region |
|-------------|--------|
| `NORTH_EAST` | North East |
| `NORTH_WEST` | North West |
| `YORKSHIRE` | Yorkshire and the Humber |
| `EAST_MIDLANDS` | East Midlands |
| `WEST_MIDLANDS` | West Midlands |
| `EAST_OF_ENGLAND` | East of England |
| `LONDON` | London |
| `SOUTH_EAST` | South East |
| `SOUTH_WEST` | South West |
| `WALES` | Wales |
| `SCOTLAND` | Scotland |
| `NORTHERN_IRELAND` | Northern Ireland |

Scotland has different income tax rates. Northern Ireland has some separate benefit provisions.

---

## Charts for UK Household Posts

Produce these charts for household-level analysis. See blog-pipeline-skill for full Plotly styling details and additional chart types.

### Required charts

| Chart | What it shows | When to use |
|-------|---------------|-------------|
| **Net income curve** | Baseline vs reform net income across earnings range | Every household post |
| **UC taper chart** | Universal Credit amount vs earnings, showing work allowance and 55% taper | Posts about UC changes |
| **Component breakdown bar** | Which taxes/benefits drive the net income change (income tax, NI, UC, child benefit) | Posts where multiple programs interact |

### Optional charts (use when relevant)

| Chart | What it shows | When to use |
|-------|---------------|-------------|
| **Marginal tax rate curve** | Effective MTR showing income tax + NI + UC taper interaction | Posts about taper rates or benefit withdrawal |
| **Regional comparison bar** | Same household across regions (London vs North West vs Scotland) | Posts about regional variation |
| **Scotland vs England comparison** | Same income, different tax systems | Posts about Scottish tax rate changes |
| **Benefit cliff chart** | Individual benefit amounts (UC, child benefit, housing element) vs income | Posts about benefit interactions |
| **Revenue impact time series** | Annual cost across fiscal years (2026-27 to 2030-31) | Posts with multi-year budget windows |

### Custom charts

For topic-specific visuals not listed above, follow these rules:
- Use PE brand colors: `TEAL = "#39C6C0"`, `BLUE = "#2C6496"`, `RED = "#DC2626"`
- Plotly with `template="plotly_white"`, `font=dict(family="Inter, sans-serif")`
- Save as PNG at 1200x600, scale=2
- Format currency as £ throughout (not $ or GBP)
- Write alt text with chart type and 2-3 key data points
- Include in results.json under `"charts"` with `url`, `alt`, `source_line`, `source_url`

## Tables for UK Household Posts

### Required tables

| Table | Columns | When to use |
|-------|---------|-------------|
| **Household impact table** | Household type, Income, Tenure, Region, Net income change | Every household post |
| **Component breakdown table** | Component (income tax, NI, UC, child benefit...), Baseline, Reform, Change | Posts where multiple programs interact |

### Optional tables

| Table | Columns | When to use |
|-------|---------|-------------|
| **Parameter comparison** | Parameter, Current law, Reform | Posts introducing the reform details |
| **Regional comparison** | Region, Net income change, Key driver | Posts about regional variation |
| **Scotland vs England** | Metric, Scotland, England, Difference | Posts about devolved tax rates |
| **UC calculation walkthrough** | Step (standard allowance, child elements, housing, earnings deduction, taper), Amount | Posts explaining UC mechanics |
| **Revenue impact by year** | Fiscal year, Static cost (£B), Dynamic cost (£B) | Posts with multi-year analysis |
| **Poverty and inequality** | Metric (AHC poverty, BHC poverty, child poverty, Gini), Baseline, Reform, Change | Posts with distributional analysis |

### Custom tables

For topic-specific tables, follow these rules:
- Include in results.json with `headers`, `rows`, `source_line`, `source_url`
- Pre-format values as display strings ("£1,200", "12.4%")
- Use `{{table:name}}` in blog post markdown
- Keep under 15 rows

---

## Generating results.json for Household Analysis

```python
import json, inspect

REPO = "PolicyEngine/uc-increase-analysis"

households = {
    "single_renter": {"income": 15_000, "children": 0, "rent": 7_200},
    "single_parent_2": {"income": 25_000, "children": 2, "rent": 7_200},
    "couple_2_owner": {"income": 75_000, "children": 2, "rent": 0},
}

results = {
    "metadata": {
        "title": "UC Standard Allowance Increase",
        "repo": REPO,
        "country_id": "uk",
        "year": 2026,
    },
    "values": {},
    "tables": {},
    "charts": {},
}

rows = []
for name, params in households.items():
    # ... calculate baseline and reform ...
    line = inspect.currentframe().f_lineno
    change = reform_net - baseline_net

    results["values"][f"{name}_change"] = {
        "value": float(change),
        "display": f"£{abs(change):,.0f}",
        "source_line": line,
        "source_url": f"https://github.com/{REPO}/blob/main/analysis.py#L{line}",
    }
    rows.append([name, f"£{params['income']:,}", f"£{change:,.0f}"])

line = inspect.currentframe().f_lineno
results["tables"]["household_impacts"] = {
    "title": "Household impact by family type",
    "headers": ["Household", "Income", "Net income change"],
    "rows": rows,
    "source_line": line,
    "source_url": f"https://github.com/{REPO}/blob/main/analysis.py#L{line}",
}

with open("results.json", "w") as f:
    json.dump(results, f, indent=2)
```

---

## Writing UK Household Case Studies

Follow policyengine-writing-skill for all blog post text.

**✅ Correct (specific, neutral, active):**
```
A single parent of two children earning £25,000 and renting privately
sees a £520 annual increase in Universal Credit, raising household
net income from £28,400 to £28,920.
```

**❌ Wrong (vague, value judgment):**
```
Working families on Universal Credit see welcome increases to their
income under the reform.
```

**✅ Correct (shows calculation):**
```
The UC standard allowance rises from £393 to £500 per month, a £107
monthly increase (£1,284 per year). After the 55% taper on her £15,000
net earnings above the work allowance, she retains £520 of the increase.
```

**❌ Wrong (hides calculation):**
```
Claimants receive a boost to their monthly Universal Credit payments.
```

**✅ Correct (acknowledges UK specifics):**
```
A Scottish taxpayer earning £50,000 pays income tax at Scotland's
intermediate rate of 21%, compared to 20% in England. The reform
increases their net income by £340, compared to £380 for an equivalent
English taxpayer.
```

**❌ Wrong (ignores devolution):**
```
All UK taxpayers earning £50,000 see the same impact from the reform.
```

---

## Common UK Variables

| Variable | Entity | Description |
|----------|--------|-------------|
| `hbai_household_net_income` | household | Household net income (HBAI definition) |
| `household_net_income` | household | Household net income |
| `income_tax` | person | Income tax liability |
| `national_insurance` | person | National Insurance contributions |
| `universal_credit` | benunit | Universal Credit entitlement |
| `child_benefit` | benunit | Child Benefit |
| `working_tax_credit` | benunit | Working Tax Credit (legacy) |
| `child_tax_credit` | benunit | Child Tax Credit (legacy) |
| `housing_benefit` | benunit | Housing Benefit (legacy) |
| `pension_credit` | benunit | Pension Credit |
| `council_tax_benefit` | benunit | Council Tax Reduction |
| `employment_income` | person | Employment income |
| `self_employment_income` | person | Self-employment income |
| `state_pension` | person | State Pension |

---

## UK vs US Differences

| Aspect | UK | US |
|--------|----|----|
| Entity groups | 3 (person, benunit, household) | 6 (person, marital_unit, family, tax_unit, spm_unit, household) |
| Benefits unit | Benefit unit (benunit) | SPM unit for benefits, tax unit for credits |
| Benefit claiming | Must set `would_claim_*` = True | Generally automatic |
| Net income variable | `hbai_household_net_income` | `household_net_income` |
| Currency | £ (GBP) | $ (USD) |
| Housing costs | `rent`, `council_tax`, `tenure_type` required | Not required for most analyses |
| Regional variation | `region` — Scotland has different tax rates | `state_code_str` — 50+ state tax systems |
| Key benefit | Universal Credit | EITC, CTC, SNAP |
| Key taper | UC taper (55% of net earnings) | EITC phase-out, benefit cliffs |

---

## Checklist

Before publishing UK household analysis:

- [ ] All 3 entity groups defined (person, benunit, household)
- [ ] `would_claim_*` flags set for all relevant benefits
- [ ] `region` specified (Scotland has different tax rates)
- [ ] `tenure_type`, `rent`, and `council_tax` set for housing-related benefits
- [ ] Representative households cover renters, homeowners, pensioners, and families with children
- [ ] Baseline and reform both calculated for the same household
- [ ] Component breakdown shows which taxes/benefits drive the net change
- [ ] All values in results.json with `source_line` and `source_url`
- [ ] Currency formatted as £ (not $ or GBP)
- [ ] Blog text uses `{{}}` template references, not hard-coded numbers
- [ ] Neutral language — no value judgments
- [ ] Scottish/devolved differences noted where relevant
- [ ] Calculations shown explicitly (e.g., "£107/month × 12 = £1,284/year, minus 55% taper...")

---

## Resources

- blog-pipeline-skill — results.json schema, template syntax, chart generation
- policyengine-writing-skill — neutral tone, active voice, quantitative precision
- policyengine-analysis-skill — population-level patterns, Plotly charts
- policyengine-uk-skill — UK tax/benefit system domain knowledge
- us-household-analysis-skill — US equivalent patterns for comparison
