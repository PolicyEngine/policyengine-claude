---
name: policyengine-policy-lookup
description: >
  Look up benefit amounts, tax rates, and policy parameter values using PolicyEngine.
  Use this skill when the user asks factual questions like "what is the TANF benefit",
  "how much SNAP does someone get", "maximum benefit amount", "what's the EITC for",
  "income tax for a family in [state]", or any "how much / what is / what does someone get"
  question about US taxes and benefits.
  Triggers: "what is the benefit", "how much", "max benefit", "benefit amount",
  "what would someone get", "TANF amount", "SNAP benefit", "EITC amount", "CTC amount",
  "income limit", "eligibility threshold", "poverty line", "tax rate", "marginal rate",
  "what taxes", "what benefits", "net income for", "look up", "current value of".
---

# Policy lookup with PolicyEngine

Use this skill to answer factual questions about US tax and benefit amounts.

**The approach: simulate a household and calculate the variable.**

PolicyEngine is a microsimulation model. The best way to answer "what is the TANF benefit for X?" is to create a household matching X and calculate the result.

## Quick pattern: answer "what benefit does this household get?"

```python
from policyengine_us import Simulation

# Example: single parent + 2 kids in CA, zero income -> max TANF
situation = {
    "people": {
        "parent": {"age": {2024: 30}, "employment_income": {2024: 0}},
        "child1": {"age": {2024: 5}},
        "child2": {"age": {2024: 8}},
    },
    "families": {"family": {"members": ["parent", "child1", "child2"]}},
    "marital_units": {"marital_unit": {"members": ["parent"]}},
    "tax_units": {"tax_unit": {"members": ["parent", "child1", "child2"]}},
    "spm_units": {"spm_unit": {"members": ["parent", "child1", "child2"]}},
    "households": {
        "household": {
            "members": ["parent", "child1", "child2"],
            "state_name": {2024: "CA"},
        }
    },
}

sim = Simulation(situation=situation)
tanf = sim.calculate("tanf", 2024)
snap = sim.calculate("snap", 2024)
print(f"TANF: ${tanf[0]:,.0f}/year (${tanf[0]/12:,.0f}/month)")
print(f"SNAP: ${snap[0]:,.0f}/year (${snap[0]/12:,.0f}/month)")
```

## Key program variable names

| Program | Variable name | Entity level |
|---------|--------------|-------------|
| TANF | `tanf` | spm_unit |
| SNAP (food stamps) | `snap` | spm_unit |
| Earned Income Tax Credit | `eitc` | tax_unit |
| Child Tax Credit | `ctc` | tax_unit |
| Federal income tax | `income_tax` | tax_unit |
| State income tax | `state_income_tax` | tax_unit |
| Payroll tax (FICA) | `payroll_tax` | tax_unit |
| SSI | `ssi` | spm_unit |
| WIC | `wic` | spm_unit |
| ACA premium tax credit | `premium_tax_credit` | tax_unit |
| Total benefits | `household_benefits` | spm_unit |
| Total taxes | `household_tax` | tax_unit |
| Net income | `household_net_income` | spm_unit |

## Getting the maximum benefit

To find the **maximum benefit** for a program, set income to 0 and other resources to 0. This gives the benefit at zero earnings, which is typically the maximum.

```python
# Max benefit = zero income household
situation["people"]["parent"]["employment_income"] = {2024: 0}
sim = Simulation(situation=situation)
max_benefit = sim.calculate("snap", 2024)[0]
```

## Comparing across states

```python
from policyengine_us import Simulation

states = ["CA", "NY", "TX", "FL", "IL", "PA"]
for state in states:
    situation["households"]["household"]["state_name"] = {2024: state}
    sim = Simulation(situation=situation)
    tanf = sim.calculate("tanf", 2024)[0]
    snap = sim.calculate("snap", 2024)[0]
    print(f"{state}: TANF=${tanf:,.0f}/yr, SNAP=${snap:,.0f}/yr")
```

## Important: state-specific TANF coverage

TANF is administered by states, and PolicyEngine models it at the state level. Not all states have full TANF implementations yet. States with dedicated TANF models include:

AZ, CA, CO, DC, IL, IN, MD, MO, NC, NJ, NY, OK, OR, PA, TX, WA

For states without a dedicated model, `tanf` may return 0. This doesn't mean the state has no TANF program — it means PolicyEngine hasn't implemented it yet. SNAP, EITC, CTC, and federal programs are available for all states.

## Varying family size

To find how benefits change with number of children:

```python
from policyengine_us import Simulation

for n_children in range(0, 5):
    members = ["parent"] + [f"child{i}" for i in range(n_children)]
    people = {"parent": {"age": {2024: 30}, "employment_income": {2024: 0}}}
    for i in range(n_children):
        people[f"child{i}"] = {"age": {2024: 5}}

    situation = {
        "people": people,
        "families": {"family": {"members": members}},
        "marital_units": {"marital_unit": {"members": ["parent"]}},
        "tax_units": {"tax_unit": {"members": members}},
        "spm_units": {"spm_unit": {"members": members}},
        "households": {
            "household": {"members": members, "state_name": {2024: "CA"}}
        },
    }

    sim = Simulation(situation=situation)
    snap = sim.calculate("snap", 2024)[0]
    tanf = sim.calculate("tanf", 2024)[0]
    print(f"{n_children} children: SNAP=${snap:,.0f}/yr, TANF=${tanf:,.0f}/yr")
```

## Discovering available variables

```python
from policyengine_us import CountryTaxBenefitSystem

system = CountryTaxBenefitSystem()

# Search for variables by keyword
for name, var in sorted(system.variables.items()):
    if "tanf" in name.lower():
        print(f"{name}: {var.label}")
```

## When this skill returns 0 or unexpected results

1. **Program not modeled for that state** — check the state coverage list above
2. **Income too high** — the household may not be eligible
3. **Missing household members** — some programs require children or specific ages
4. **Wrong variable name** — use the discovery pattern above to find the right variable
5. **Annual vs monthly** — PolicyEngine returns annual amounts; divide by 12 for monthly
