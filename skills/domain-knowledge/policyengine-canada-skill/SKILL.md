---
name: policyengine-canada
description: |
  ALWAYS LOAD THIS SKILL FIRST before writing any PolicyEngine-Canada code.
  Contains Canadian federal and provincial tax/benefit rules for household calculations.
  IMPORTANT: PolicyEngine-Canada does NOT have representative population microdata.
  Do NOT attempt microsimulation or population-level estimates for Canada.
  Only provide household-level analysis (single-family impacts, eligibility, benefit amounts).
  Triggers: "what would", "how much would a", "benefit be", "eligible for", "qualify for",
  "single parent", "married couple", "family of", "household of", "if they earn",
  "earning $", "making $", "calculate benefits", "calculate taxes", "benefit for a",
  "what would I get", "what is the maximum", "what is the rate", "income limit",
  "benefit amount", "maximum benefit", "compare provinces",
  "CCB", "Canada Child Benefit", "GST credit", "HST credit", "GST/HST",
  "OAS", "Old Age Security", "GIS", "Guaranteed Income Supplement",
  "CWB", "Canada Workers Benefit", "EI", "Employment Insurance",
  "CPP", "Canada Pension Plan", "RRSP", "TFSA",
  "Ontario Child Benefit", "OCB", "Ontario Trillium Benefit", "OTB",
  "BC Climate Action", "Alberta Child Benefit", "Quebec",
  "CRA", "Canada Revenue Agency", "Canadian", "Canada",
  "Ontario", "British Columbia", "Alberta", "Saskatchewan", "Manitoba",
  "Nova Scotia", "New Brunswick", "PEI", "Newfoundland", "Yukon", "NWT", "Nunavut",
  "provincial tax", "federal tax Canada".
---

# PolicyEngine-Canada

> **IMPORTANT: Always use the current year (2026) in calculations, not 2024 or 2025.**

## No Microsimulation for Canada

**PolicyEngine-Canada does NOT have representative population microdata.** The only available
dataset is a tiny template with 3 synthetic people. This means:

- **Do NOT** use `Microsimulation()` from `policyengine_canada` for population-level estimates
- **Do NOT** attempt to calculate aggregate costs, revenue impacts, or poverty rates for Canada
- **Only provide household-level analysis**: calculate impacts for specific families using `Simulation`
- If the user asks "what would X cost nationally" or "how many families would benefit", explain
  that population-level estimates are not currently available for Canada and offer a household
  example instead

### What you CAN do

- Calculate benefits/taxes for a specific household (income, province, family composition)
- Compare baseline vs. reform for a single family
- Show how benefits change across an income range
- Compare provinces for a given household

---

PolicyEngine-Canada models the Canadian federal and provincial tax and benefit system.

**What it models:**

**Federal taxes:**
- Federal income tax (5 brackets)
- Canada Pension Plan (CPP/CPP2) contributions
- Employment Insurance (EI) premiums

**Federal benefits:**
- Canada Child Benefit (CCB)
- GST/HST Credit
- Canada Workers Benefit (CWB)
- Old Age Security (OAS)
- Guaranteed Income Supplement (GIS)
- Climate Action Incentive Payment (CAIP)

**Provincial programs (varies by province):**
- Provincial income tax (all provinces and territories)
- Ontario Child Benefit (OCB)
- Ontario Trillium Benefit (OTB)
- BC Climate Action Tax Credit
- Alberta Child and Family Benefit
- Quebec-specific programs (QST, QPP, etc.)

**See full list:** https://policyengine.org/ca/parameters

---

## Key Federal Programs — Rules Reference

### Canada Child Benefit (CCB) — 2025–2026

The CCB is a tax-free monthly payment to eligible families with children under 18.

**Maximum amounts (July 2025 – June 2026):**
- Under 6: **$7,997**/child/year ($666.41/month)
- Ages 6–17: **$6,748**/child/year ($562.33/month)

**Phase-out structure:**
The CCB is reduced based on adjusted family net income (AFNI) using two thresholds.

**Threshold 1: $37,487**
| Number of children | Reduction rate (AFNI $37,487–$79,845) |
|---|---|
| 1 child | 7.0% |
| 2 children | 13.5% |
| 3 children | 19.0% |
| 4+ children | 23.0% |

**Threshold 2: $79,845**
| Number of children | Reduction rate (AFNI above $79,845) |
|---|---|
| 1 child | 3.2% |
| 2 children | 5.7% |
| 3 children | 8.0% |
| 4+ children | 9.5% |

**Child Disability Benefit (CDB) supplement:**
- Up to **$3,411**/year ($284.25/month) per child eligible for the Disability Tax Credit
- Reduced at 3.2% of AFNI above $79,845 (1 child), 5.7% (2+ children)

**CCB calculation formula:**
```
For each income range:
  CCB = sum(max_amount per child) - reduction

  If AFNI <= $37,487: no reduction
  If $37,487 < AFNI <= $79,845:
    reduction = rate_tier1 × (AFNI - $37,487)
  If AFNI > $79,845:
    reduction = rate_tier1 × ($79,845 - $37,487) + rate_tier2 × (AFNI - $79,845)
```

**Example calculation — 2 children (ages 3, 8), AFNI = $80,000:**
```
Max CCB = $7,997 (under 6) + $6,748 (6-17) = $14,745
Tier 1 reduction = 13.5% × ($79,845 - $37,487) = 13.5% × $42,358 = $5,718
Tier 2 reduction = 5.7% × ($80,000 - $79,845) = 5.7% × $155 = $9
Total reduction = $5,727
CCB = $14,745 - $5,727 = $9,018/year
```

### Federal Income Tax — 2026

**Tax brackets:**
| Taxable income | Rate |
|---|---|
| Up to $57,375 | 15% |
| $57,375 – $114,750 | 20.5% |
| $114,750 – $158,468 | 26% |
| $158,468 – $220,000 | 29% |
| Over $220,000 | 33% |

**Basic personal amount (BPA):** $16,129 (2026, indexed)

> Note: Bracket thresholds are indexed annually to inflation. Check CRA for exact 2026 values.

### GST/HST Credit — 2025–2026

Tax-free quarterly payment for low/modest-income individuals and families.

**Maximum amounts (July 2025 – June 2026):**
- Single: **$340**/year
- Married/common-law: **$340** + **$179** for spouse = **$519**
- Per child under 19: **$179**

**Phase-out:**
- Begins at family net income of **$44,530**
- Reduction rate: 5% of income above threshold

### Canada Workers Benefit (CWB) — 2026

Refundable tax credit for low-income workers.

**Single individuals:**
- Maximum: ~**$1,590**
- Phase-in: 27% of working income above $3,000
- Phase-out: 15% of net income above ~$24,975

**Families:**
- Maximum: ~**$2,739**
- Phase-in: 27% of working income above $3,000
- Phase-out: 15% of family net income above ~$28,494

**Disability supplement:**
- Additional ~**$784** for CWB-eligible individuals with the Disability Tax Credit

### Old Age Security (OAS) — 2026

Monthly pension for seniors 65+.

**Maximum amounts (Q1 2026):**
- Ages 65–74: ~**$727.67**/month ($8,732/year)
- Ages 75+: ~**$800.44**/month ($9,605/year)

**OAS recovery tax (clawback):**
- Threshold: ~**$90,997** net income
- Rate: 15% of income above threshold
- Full clawback at ~**$149,211** (65–74) or ~**$154,196** (75+)

### Guaranteed Income Supplement (GIS) — 2026

Monthly benefit for low-income OAS pensioners.

**Maximum amounts (Q1 2026):**
- Single: ~**$1,086.88**/month
- Spouse receives OAS: ~**$654.23**/month each

**Income test:**
- Reduced by 50% (or 75% for partial amounts) of income above exempted amounts
- Employment income exemption: first $5,000 fully exempt, next $10,000 at 50%

---

## Provincial Tax — Ontario (2026)

**Ontario income tax brackets:**
| Taxable income | Rate |
|---|---|
| Up to $52,886 | 5.05% |
| $52,886 – $105,775 | 9.15% |
| $105,775 – $150,000 | 11.16% |
| $150,000 – $220,000 | 12.16% |
| Over $220,000 | 13.16% |

**Ontario surtax:**
- 20% of basic provincial tax above $5,315
- Plus 36% of basic provincial tax above $6,802

### Ontario Child Benefit (OCB)

- Maximum: **$1,726.92**/child/year ($143.91/month) for July 2025 – June 2026
- Phase-out begins at family net income of **$24,045**
- Reduction rate: 8% per child of income above threshold

### Ontario Trillium Benefit (OTB)

Combines three credits:
1. **Ontario Energy and Property Tax Credit** — up to $1,248 (seniors $1,421)
2. **Northern Ontario Energy Credit** — up to $180 (families $277)
3. **Ontario Sales Tax Credit** — up to $360/adult + $360/child

---

## Provincial Tax — Other Provinces

### British Columbia (2026)
| Taxable income | Rate |
|---|---|
| Up to $47,937 | 5.06% |
| $47,937 – $95,875 | 7.70% |
| $95,875 – $110,076 | 10.50% |
| $110,076 – $133,664 | 12.29% |
| $133,664 – $181,232 | 14.70% |
| Over $181,232 | 20.50% |

### Alberta (2026)
| Taxable income | Rate |
|---|---|
| Up to $148,269 | 10% |
| $148,269 – $177,922 | 12% |
| $177,922 – $237,230 | 13% |
| $237,230 – $355,845 | 14% |
| Over $355,845 | 15% |

### Quebec (2026)
| Taxable income | Rate |
|---|---|
| Up to $51,780 | 14% |
| $51,780 – $103,545 | 19% |
| $103,545 – $126,000 | 24% |
| Over $126,000 | 25.75% |

> Note: Quebec has its own tax system (Revenu Québec) with unique credits and deductions. QPP replaces CPP.

---

## CPP Contributions — 2026

**CPP (first ceiling):**
- Maximum pensionable earnings: ~**$71,300**
- Basic exemption: $3,500
- Employee rate: 5.95%
- Maximum employee contribution: ~$4,034

**CPP2 (second ceiling):**
- Second ceiling: ~**$81,200**
- Rate: 4% on earnings between first and second ceiling
- Maximum CPP2 contribution: ~$396

---

## EI Premiums — 2026

- Maximum insurable earnings: ~**$65,700**
- Employee premium rate: 1.64%
- Maximum employee premium: ~$1,077
- Quebec rate: 1.32% (due to QPIP)

---

## Household Analysis Patterns

### Answering "What would [reform] cost/mean for a family?"

1. **Identify the family**: income, province, number/ages of children
2. **Calculate baseline**: apply current rules to compute total benefits/taxes
3. **Calculate reform**: apply modified rules
4. **Report the difference**: reform minus baseline

### Example: Doubling the CCB for an Ontario family

**Family:** 2 parents, 2 children (ages 3, 8), AFNI $80,000, Ontario

**Baseline CCB:**
```
Max = $7,997 + $6,748 = $14,745
Reduction = 13.5% × ($79,845 - $37,487) + 5.7% × ($80,000 - $79,845)
         = $5,718 + $9 = $5,727
Baseline CCB = $14,745 - $5,727 = $9,018
```

**Doubled CCB:**
```
Max = $15,994 + $13,496 = $29,490
Reduction = 13.5% × ($79,845 - $37,487) + 5.7% × ($80,000 - $79,845)
         = $5,718 + $9 = $5,727
Doubled CCB = $29,490 - $5,727 = $23,763
```

**Additional benefit = $23,763 - $9,018 = $14,745/year**

> Key insight: When only the maximum amounts are doubled (not the phase-out rates), the additional benefit equals the original maximum for families whose benefits aren't fully phased out. The phase-out claws back the same dollar amount regardless of the benefit level.

---

## Common Pitfalls

### 1. CCB Uses Adjusted Family Net Income (AFNI)
AFNI is the combined net income (line 23600) of both spouses/partners. It is NOT individual income.

### 2. Benefits Use Previous Year's Income
CCB payments from July 2025 – June 2026 are based on **2024 tax year** income.

### 3. Provincial Programs Stack on Federal
Many provinces have their own child benefits on top of the federal CCB. Always check for provincial supplements.

### 4. Quebec Is Different
Quebec has its own pension plan (QPP), parental insurance (QPIP), and many unique credits. Don't assume federal rules apply.

### 5. Indexation
Most thresholds and amounts are indexed annually to CPI. Always verify the year-specific values.

---

## Additional Resources

- **CRA Benefits Calculator:** https://www.canada.ca/en/revenue-agency/services/child-family-benefits/child-family-benefits-calculator.html
- **PolicyEngine Canada:** https://policyengine.org/ca
- **Variable Explorer:** https://policyengine.org/ca/variables
- **Parameter Explorer:** https://policyengine.org/ca/parameters
- **GitHub:** https://github.com/PolicyEngine/policyengine-canada
