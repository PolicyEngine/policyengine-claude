---
name: policyengine-user-guide
description: |
  Using the PolicyEngine web app (policyengine.org) to analyze how tax and benefit reforms affect
  a household or the whole population — the household calculator, the policy editor, and
  society-wide impact charts. For people using the site, not building it.
  Triggers: "how to use PolicyEngine", "household calculator", "build a reform on the website",
  "policyengine.org walkthrough", "web app guide", "share a reform link", "read the impact charts".
metadata:
  category: process
---

# PolicyEngine user guide

Help someone use policyengine.org to compute how a policy affects a specific household or the
population. The app has three stable surfaces: a **household calculator**, a **policy editor**,
and **society-wide impact** results. Exact labels and layout evolve — describe the flow by these
concepts rather than memorized button text.

## What PolicyEngine does

PolicyEngine computes the impact of tax and benefit policy on households and society. Users can
calculate their own taxes and benefits, design a custom reform, see population-wide impacts, and
share a reform by link. It is a nonpartisan nonprofit; the site is free.

Countries: United States (`policyengine.org/us`), United Kingdom (`/uk`), and Canada (`/ca`).

## Household calculator

The household flow answers "how does this policy affect *this* household?"

1. **Describe the household.** Enter the people (ages, marital status, dependents), their income
   by type (employment, self-employment, capital gains, pensions, benefits received), the
   location (US state or UK region, plus any local options the model supports), and any
   deductions/expenses the model uses (e.g. charitable giving, mortgage interest, SALT, medical).
2. **Read the results.** Net income after taxes and benefits, broken into total tax, total
   benefits, and effective and marginal tax rates, with charts of net income and marginal rate
   across an earnings range.
3. **Apply a reform.** Layer a policy reform on top to compare baseline vs. reform for the same
   household.

## Policy editor

The policy flow answers "what does this reform do to the population?"

1. **Pick parameters to change.** Browse the parameter tree by government department and program
   (e.g. IRS credits, SNAP, Universal Credit), select a parameter, and set a new value or
   schedule. Verify the parameter's current baseline before changing it — post-OBBBA US law
   differs from older summaries (e.g. the CTC baseline is $2,200 in 2026, not $2,000).
2. **Run the society-wide impact.** The app computes the reform against microdata and returns:
   - **Budgetary impact** — total cost or revenue, broken down by program.
   - **Poverty impact** — change in poverty rate, by age group and for deep poverty.
   - **Distributional impact** — average change and winners/losers by income decile.
   - **Inequality impact** — Gini index and top-income shares.

## Sharing a reform

Every reform gets a shareable URL. The link encodes the reform, the region (national, state, or
district), and the year of analysis, so a recipient opens the same scenario. Charts can be
downloaded as images to drop into a post or deck.

## Reading the results

- **Supplemental Poverty Measure (SPM):** the Census Bureau's alternative measure that accounts
  for taxes, benefits, and living costs — more comprehensive than the Official Poverty Measure.
- **Gini coefficient:** income inequality on a 0 (perfect equality) to 1 (perfect inequality)
  scale; lower means more equal.
- **Income deciles:** the population split into ten equal groups by income (decile 1 = lowest).
- **Winners and losers:** shares whose net income rises or falls by more than a set threshold.
- **Chart types:** bar charts compare across groups (deciles, states); line charts show
  relationships (income vs. impact); waterfall charts decompose the budgetary impact.

## Common tasks

- **Effect on my household:** household calculator → enter details → apply the reform → compare.
- **Cost of a reform:** policy editor → build the reform → budgetary impact.
- **Poverty effect:** policy editor → build the reform → poverty impact.
- **Who benefits:** policy editor → build the reform → distributional impact (winners/losers by
  decile).
- **Compare two reforms:** build reform A, save its link, build reform B, compare their impacts.

## FAQ

- **How accurate is it?** Household calculations apply statutory tax and benefit rules and match
  official calculators for individual households. Population estimates use microsimulation on
  survey microdata calibrated to administrative totals.
- **Can I file my taxes with it?** No — it is for policy analysis, not tax filing. Use IRS.gov or
  professional software to file.
- **What programs are modeled?** US: federal income/payroll/capital-gains tax, EITC, CTC/ACTC,
  SNAP, WIC, ACA subsidies, Social Security, SSI, TANF, and state income taxes; UK: income tax,
  National Insurance, Universal Credit, Child Benefit, State Pension, Pension Credit, Council Tax
  Support. See `policyengine.org/us/parameters` and `/uk/parameters` for the full list.
- **How do I report a wrong result?** Note the household inputs and the household URL, and file an
  issue on the relevant country model repo (e.g. `github.com/PolicyEngine/policyengine-us`). For
  app bugs, file on `github.com/PolicyEngine/policyengine-app-v2`.

## Beyond the web app

- **Programmatic analysis (Python):** see the **policyengine** skill — household calculations and
  population microsimulation with the canonical `policyengine` package.
- **Contributing to a country model:** see **policyengine-model-development**.
- **Building the site or embeddable tools:** see **policyengine-app** and **policyengine-tools**.

## Resources

- Website: https://policyengine.org
- Research/blog: https://policyengine.org/us/research and `/uk/research`
- GitHub: https://github.com/PolicyEngine
- Contact: hello@policyengine.org
