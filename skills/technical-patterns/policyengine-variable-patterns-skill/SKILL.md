---
name: policyengine-variable-patterns
description: PolicyEngine variable patterns - variable creation, no hard-coding principle, federal/state separation, metadata standards
---

# PolicyEngine Variable Patterns

Essential patterns for creating PolicyEngine variables for government benefit programs.

## FIRST PRINCIPLE: Legal Code is the Source of Truth

**The law defines WHAT to implement. These patterns are just HOW to implement it.**

```
1. READ the legal code/policy manual FIRST
2. UNDERSTAND what the law actually says
3. IMPLEMENT exactly what the law requires
4. USE these patterns as tools to implement correctly
```

**Patterns are tools, not rules to blindly follow:**
- If the legal code says something different from common patterns → **FOLLOW THE LAW**
- If another state does it differently → **Check YOUR state's legal code**
- If a pattern doesn't fit the regulation → **Implement what the law says**

**Every implementation decision should trace back to a specific legal citation.**

---

## Modeling Time-Limited Rules

PolicyEngine supports modeling time-limited disregards. **DO implement these — DO NOT skip them.**

### Not Yet Modeled

Lifetime benefit limits (e.g., federal 60-month TANF limit) are not yet modeled in PolicyEngine. Don't implement these, but don't add comments claiming they're architecturally impossible — they may be added in the future.

### Pattern 1: Calendar Month — Time-Varying Disregard

Use when a disregard rate changes based on the month of the year. Uses `period.start.month` to get the calendar month (January=1, February=2, etc.).

```python
class state_tanf_countable_earned_income(Variable):
    def formula(spm_unit, period, parameters):
        p = parameters(period).gov.states.xx.tanf.income
        earned = spm_unit("tanf_gross_earned_income", period)

        month = period.start.month
        tlp_rate = p.time_limited_percentage.rate.calc(month)
        return earned * (1 - tlp_rate)
```

**Parameter structure** — bracket by month:
```yaml
# .../time_limited_percentage/rate.yaml
brackets:
  - threshold:
      1997-07-01: 1
    amount:
      1997-07-01: 0.5    # Months 1-6: 50%
  - threshold:
      1997-07-01: 7
    amount:
      1997-07-01: 0.35   # Months 7-9: 35%
  - threshold:
      1997-07-01: 10
    amount:
      1997-07-01: 0.25   # Months 10-12: 25%
```

### Pattern 2: `applicable_months` Split

Use when a state splits the year into periods with different disregard rates.

```python
class state_tanf_countable_earned_income(Variable):
    def formula(spm_unit, period, parameters):
        p = parameters(period).gov.states.xx.tanf.income
        # First 6 months: 100% disregard (if eligible)
        # Remaining 6 months: partial disregard
        full_disregard_months = p.full_disregard.applicable_months  # 6
        remaining_months = MONTHS_IN_YEAR - full_disregard_months
        # ... apply appropriate rate based on period
```

---

## Critical Principles

### 1. ZERO Hard-Coded Values
**Every numeric value MUST be parameterized**

```python
❌ FORBIDDEN:
return where(eligible, 1000, 0)     # Hard-coded 1000
age < 15                             # Hard-coded 15
benefit = income * 0.33              # Hard-coded 0.33
month >= 10 and month <= 3           # Hard-coded months

✅ REQUIRED:
return where(eligible, p.maximum_benefit, 0)
age < p.age_threshold.minor_child
benefit = income * p.benefit_rate
month >= p.season.start_month
```

**Acceptable literals:**
- `0`, `1`, `-1` for basic math
- `12` for month conversion (`/ 12`, `* 12`)
- Array indices when structure is known

### 2. No Placeholder Implementations
**Delete the file rather than leave placeholders**

```python
❌ NEVER:
def formula(entity, period, parameters):
    # TODO: Implement
    return 75  # Placeholder

✅ ALWAYS:
# Complete implementation or no file at all
```

### 3. Use `adds` or `add()` - NEVER Manual Addition

**CRITICAL: NEVER manually fetch variables and add them with `+`. Always use `adds` or `add()`.**

#### Rule 1: Pure sum → `adds` attribute (no formula)

```python
❌ WRONG - Writing a formula for simple sum:
class tx_tanf_gross_income(Variable):
    def formula(spm_unit, period, parameters):
        earned = spm_unit("tanf_gross_earned_income", period)
        unearned = spm_unit("tanf_gross_unearned_income", period)
        return earned + unearned  # DON'T DO THIS!

✅ CORRECT - Use adds, no formula needed:
class tx_tanf_gross_income(Variable):
    value_type = float
    entity = SPMUnit
    definition_period = MONTH
    adds = ["tanf_gross_earned_income", "tanf_gross_unearned_income"]
    # NO formula method - adds handles it automatically!
```

#### Rule 2: Sum + other operations → `add()` function

```python
❌ WRONG - Manual fetching and adding:
def formula(spm_unit, period, parameters):
    earned = spm_unit("tanf_gross_earned_income", period)
    unearned = spm_unit("tanf_gross_unearned_income", period)
    gross = earned + unearned  # DON'T manually add!
    return gross * p.rate

✅ CORRECT - Use add() function:
def formula(spm_unit, period, parameters):
    gross = add(spm_unit, period, ["tanf_gross_earned_income", "tanf_gross_unearned_income"])
    return gross * p.rate
```

**Decision rule:**
- Is it ONLY a sum? → `adds = [...]` (no formula)
- Sum + other operations? → `add()` function inside formula

**See policyengine-aggregation-skill for detailed patterns.**

---

## Variable Implementation Standards

### Variable Metadata Format

Follow established patterns:
```python
class il_tanf_countable_earned_income(Variable):
    value_type = float
    entity = SPMUnit
    definition_period = MONTH
    label = "Illinois TANF countable earned income"
    unit = USD
    reference = "https://www.law.cornell.edu/regulations/illinois/..."
    defined_for = StateCode.IL

    # Use adds for simple sums
    adds = ["il_tanf_earned_income_after_disregard"]
```

**Key rules:**
- ✅ Use full URL in `reference` (clickable)
- ✅ For PDF links, include page number: `#page=XX`
- ✅ For multiple references, use TUPLE `()` not list `[]`
- ❌ **Don't use `documentation` field** - use `reference` instead
- ❌ Don't use statute citations without URLs

**❌ WRONG - Don't use documentation field:**
```python
class some_variable(Variable):
    documentation = "This is the wrong field"  # DON'T USE THIS
```

**✅ CORRECT - Use reference field:**
```python
class some_variable(Variable):
    reference = "https://example.gov/rules.pdf#page=10"  # USE THIS
```

### Scoping `defined_for` to the Right Level

`defined_for` controls which entities run the formula. Use the most specific scope that fits:

```python
# ❌ TOO BROAD — calculates rates for all RI residents (adults, ineligible children)
class ri_ccap_licensed_center_rate(Variable):
    entity = Person
    defined_for = StateCode.RI

# ✅ CORRECT — only calculates rates for children eligible for CCAP
class ri_ccap_licensed_center_rate(Variable):
    entity = Person
    defined_for = "ri_ccap_eligible_child"
```

**Guidelines:**
- **SPMUnit-level benefit variables** → `defined_for = "state_program_eligible"` (the main eligibility variable)
- **Person-level variables within a program** (rates, per-child amounts) → `defined_for = "state_program_eligible_child"` or the person-level eligibility variable
- **Eligibility check variables themselves** → `defined_for = StateCode.XX` (they determine eligibility, so they can't depend on it)

This avoids unnecessary computation and makes the variable's scope clear from its definition.

**Reference format:**
```python
# Single reference:
reference = "https://oregon.gov/dhs/tanf-manual.pdf#page=23"

# Multiple references - use TUPLE ():
reference = (
    "https://oregon.public.law/rules/oar_461-155-0030",
    "https://oregon.gov/dhs/tanf-manual.pdf#page=23",
)

# ❌ WRONG - Don't use list []:
reference = [
    "https://...",
    "https://...",
]
```

### When to Use `adds` vs `formula`

**CRITICAL: Never use both `adds`/`subtracts` AND a custom `formula` in the same variable!**

This causes bugs when the two get out of sync. Choose one approach:

```python
❌ FORBIDDEN - Mixing compositional and formula:
class household_net_income(Variable):
    subtracts = ["employee_pension_contributions"]  # ❌ Has subtracts

    def formula(household, period):  # ❌ AND has formula
        gross = household("household_gross_income", period)
        tax = household("income_tax", period)
        # BUG: Forgot to subtract employee_pension_contributions!
        return gross - tax
```

**Use `adds`/`subtracts` when:**
- Just summing variables
- Passing through a single variable
- No transformations needed

```python
✅ BEST - Pure compositional:
class tanf_gross_income(Variable):
    adds = ["employment_income", "self_employment_income"]

✅ BEST - Compositional with subtracts:
class household_net_income(Variable):
    adds = ["household_gross_income"]
    subtracts = ["income_tax", "employee_pension_contributions"]
```

**Use `formula` when:**
- Applying transformations
- Conditional logic
- Calculations needed

```python
✅ CORRECT - Pure formula:
def formula(entity, period, parameters):
    income = add(entity, period, ["income1", "income2"])
    return max_(0, income)  # Need max_
```

---

## TANF Countable Income Pattern

### Critical: Verify Calculation Order from Legal Code

**MOST IMPORTANT:** Always check the state's legal code or policy manual for the exact calculation order. The pattern below is typical but not universal.

**The Typical Pattern:**
1. Apply deductions/disregards to **earned income only**
2. Use `max_()` to prevent negative earned income
3. Add unearned income (which typically has no deductions)

**This pattern is based on how MOST TANF programs work, but you MUST verify with the specific state's legal code.**

### ❌ WRONG - Applying deductions to total income

```python
def formula(spm_unit, period, parameters):
    gross_earned = spm_unit("tanf_gross_earned_income", period)
    unearned = spm_unit("tanf_gross_unearned_income", period)
    deductions = spm_unit("tanf_earned_income_deductions", period)

    # ❌ WRONG: Deductions applied to total income
    total_income = gross_earned + unearned
    countable = total_income - deductions

    return max_(countable, 0)
```

**Why this is wrong:**
- Deductions should ONLY reduce earned income
- Unearned income (SSI, child support, etc.) is not subject to work expense deductions
- This incorrectly reduces unearned income when earned income is low

**Example error:**
- Earned: $100, Unearned: $500, Deductions: $200
- Wrong result: `max_($100 + $500 - $200, 0) = $400` (reduces unearned!)
- Correct result: `max_($100 - $200, 0) + $500 = $500`

### ✅ CORRECT - Apply deductions to earned only, then add unearned

```python
def formula(spm_unit, period, parameters):
    gross_earned = spm_unit("tanf_gross_earned_income", period)
    unearned = spm_unit("tanf_gross_unearned_income", period)
    deductions = spm_unit("tanf_earned_income_deductions", period)

    # ✅ CORRECT: Deductions applied to earned only, then add unearned
    return max_(gross_earned - deductions, 0) + unearned
```

### Pattern Variations

**With multiple deduction steps:**
```python
def formula(spm_unit, period, parameters):
    p = parameters(period).gov.states.xx.tanf.income
    gross_earned = spm_unit("tanf_gross_earned_income", period)
    unearned = spm_unit("tanf_gross_unearned_income", period)

    # Step 1: Apply work expense deduction
    work_expense = min_(gross_earned * p.work_expense_rate, p.work_expense_max)
    after_work_expense = max_(gross_earned - work_expense, 0)

    # Step 2: Apply earnings disregard
    earnings_disregard = after_work_expense * p.disregard_rate
    countable_earned = max_(after_work_expense - earnings_disregard, 0)

    # Step 3: Add unearned (no deductions applied)
    return countable_earned + unearned
```

**With disregard percentage (simplified):**
```python
def formula(spm_unit, period, parameters):
    p = parameters(period).gov.states.xx.tanf.income
    gross_earned = spm_unit("tanf_gross_earned_income", period)
    unearned = spm_unit("tanf_gross_unearned_income", period)

    # Apply disregard to earned (keep 33% = disregard 67%)
    countable_earned = gross_earned * (1 - p.earned_disregard_rate)

    return max_(countable_earned, 0) + unearned
```

### When Unearned Income HAS Deductions

Some states DO have unearned income deductions (rare). Handle separately:

```python
def formula(spm_unit, period, parameters):
    gross_earned = spm_unit("tanf_gross_earned_income", period)
    gross_unearned = spm_unit("tanf_gross_unearned_income", period)
    earned_deductions = spm_unit("tanf_earned_income_deductions", period)
    unearned_deductions = spm_unit("tanf_unearned_income_deductions", period)

    # Apply each type of deduction to its respective income type
    countable_earned = max_(gross_earned - earned_deductions, 0)
    countable_unearned = max_(gross_unearned - unearned_deductions, 0)

    return countable_earned + countable_unearned
```

### Quick Reference

**Standard TANF pattern:**
```
Countable Income = max_(Earned - Earned Deductions, 0) + Unearned
```

**NOT:**
```
❌ max_(Earned + Unearned - Deductions, 0)
❌ max_(Earned - Deductions + Unearned, 0)  # Can go negative
```

---

## Federal/State Separation

### Federal Parameters
Location: `/parameters/gov/{agency}/`
- Base formulas and methodologies
- National standards
- Required elements

### State Parameters
Location: `/parameters/gov/states/{state}/`
- State-specific thresholds
- Implementation choices
- Scale factors

```yaml
# Federal: parameters/gov/hhs/fpg/base.yaml
first_person: 14_580

# State: parameters/gov/states/ca/scale_factor.yaml
fpg_multiplier: 2.0  # 200% of FPG
```

### State Income Tax Conformity to Federal Rules

**CRITICAL: State income taxes should reference federal income sources and limits, not redefine them**

Most state income taxes start with federal definitions and then make specific adjustments. When implementing state income tax:

**✅ CORRECT - Reference federal income sources:**
```python
class ms_agi(Variable):
    """Mississippi adjusted gross income"""
    value_type = float
    entity = TaxUnit
    definition_period = YEAR
    label = "Mississippi adjusted gross income"
    unit = USD

    def formula(tax_unit, period, parameters):
        # Start with federal AGI, which already includes
        # federal capital loss limits and other federal rules
        federal_agi = tax_unit("adjusted_gross_income", period)

        # Apply Mississippi-specific additions/subtractions
        ms_additions = tax_unit("ms_additions_to_agi", period)
        ms_subtractions = tax_unit("ms_subtractions_from_agi", period)

        return federal_agi + ms_additions - ms_subtractions
```

**❌ WRONG - Redefining income sources:**
```python
# DON'T create state-specific parameters like:
# parameters/gov/states/ms/tax/income/income_sources.yaml
# containing:
#   - capital_gains
#   - long_term_capital_gains
#   - short_term_capital_gains

# This bypasses federal limits like the $3,000 capital loss deduction limit
```

**Why this matters:**
- Federal income tax applies capital loss limits before reporting AGI
- State income taxes that start from federal AGI automatically inherit these limits
- Creating separate state income source parameters bypasses federal rules
- Results in incorrect calculations (e.g., unlimited capital loss deductions)

**Common state conformity patterns:**
1. **Full conformity** - State AGI = Federal AGI (rare)
2. **Rolling conformity** - State follows current federal rules
3. **Static conformity** - State follows federal rules as of a specific date
4. **Selective conformity** - State follows federal but with specific modifications

**Implementation approach:**
- Always start with federal income sources/AGI/taxable income as the base
- Use state parameters only for state-specific additions, subtractions, or modifications
- Reference federal variables: `adjusted_gross_income`, `taxable_income`, etc.
- Don't recreate federal income aggregation logic at the state level

**Example - Mississippi specifics:**
```python
class ms_additions_to_agi(Variable):
    """Mississippi additions to federal AGI"""
    # Add state-specific income items not in federal AGI
    adds = [
        "ms_state_bond_interest",
        "ms_other_additions"
    ]

class ms_subtractions_from_agi(Variable):
    """Mississippi subtractions from federal AGI"""
    # Subtract state-specific deductions
    adds = [
        "ms_retirement_income_exclusion",
        "ms_other_subtractions"
    ]
```

---

## Code Reuse Patterns

### Avoid Duplication - Create Intermediate Variables

**❌ ANTI-PATTERN: Copy-pasting calculations**
```python
# File 1: calculates income after deduction
def formula(household, period, parameters):
    gross = add(household, period, ["income"])
    deduction = p.deduction * household.nb_persons()
    return max_(gross - deduction, 0)

# File 2: DUPLICATES same calculation
def formula(household, period, parameters):
    gross = add(household, period, ["income"])  # Copy-pasted
    deduction = p.deduction * household.nb_persons()  # Copy-pasted
    after_deduction = max_(gross - deduction, 0)  # Copy-pasted
    return after_deduction < p.threshold
```

**✅ CORRECT: Reuse existing variables**
```python
# File 2: reuses calculation
def formula(household, period, parameters):
    countable_income = household("program_countable_income", period)
    return countable_income < p.threshold
```

**When to create intermediate variables:**
- Same calculation in 2+ places
- Logic exceeds 5 lines
- Reference implementations have similar variable

---

## Federal Aggregator Variables (Summing State Programs)

### CRITICAL: Discover Programs by Enumerating State Directories

When building or modifying a federal-level variable that sums state programs (like `tanf`, which sums all state TANF programs), **never search by keyword or naming pattern**. State programs use wildly different names that don't match any single pattern.

**Example — TANF program names across states:**
- Standard: `al_tanf`, `ca_tanf`, `ny_tanf` (28 states)
- Non-standard: `fl_tca`, `mn_mfip`, `ia_fip`, `ct_tfa`, `md_tca`, `mi_fip`
- Completely unique: `ar_tea`, `id_tafi`, `la_fitap`, `ma_tafdc`, `ne_adc`, `oh_owf`, `ut_fep`, `wy_power`, `ky_ktap`, `nh_fanf`, `tn_ff`

None of the "completely unique" names contain "tanf". A keyword search for "tanf" misses 11 programs.

**Correct discovery method:**
1. List ALL state directories: `ls policyengine_us/variables/gov/states/`
2. For EACH of the 51 jurisdictions (50 states + DC), check non-tax subdirectories for the program type
3. Look for the top-level benefit variable (entity=SPMUnit, has `defined_for`)
4. Add it to the aggregator list

**Quick command to find all state TANF-like top-level variables:**
```bash
# Search for SPMUnit variables under state welfare/human services directories
grep -rl "entity = SPMUnit" policyengine_us/variables/gov/states/*/  \
  --include="*.py" | \
  xargs grep -l "defined_for" | \
  # Then manually check which are TANF top-level benefit variables
```

### Cycle Checks When Wiring Up State Programs

Adding a state program to a federal aggregator can create circular dependencies. Common cycles:

1. **Housing cost cycle**: State TANF → `housing_cost` → `rent` → `housing_assistance` → `hud_annual_income` → TANF
   - Fix: Use `pre_subsidy_rent` + other housing components instead of `housing_cost`

2. **Childcare cycle**: State TANF → `childcare_expenses` → childcare subsidies → SNAP → TANF
   - Fix: Use `spm_unit_pre_subsidy_childcare_expenses` instead of `childcare_expenses`

3. **Entity broadcast bugs**: Person-level and SPMUnit-level arrays mixed in `where()` — passes unit tests (scalar) but fails microsim (vectorized)
   - Fix: Use `spm_unit.project(spm_unit_var)` to broadcast to person level

**After adding programs, always run the microsimulation test** — it catches cycles and entity mismatches that unit tests miss.

---

## TANF-Specific Patterns

### Study Reference Implementations First

**MANDATORY before implementing any TANF:**
- DC TANF: `/variables/gov/states/dc/dhs/tanf/`
- IL TANF: `/variables/gov/states/il/dhs/tanf/`
- TX TANF: `/variables/gov/states/tx/hhs/tanf/`

**Learn from them:**
1. Variable organization
2. Naming conventions
3. Code reuse patterns
4. When to use `adds` vs `formula`

### Standard TANF Structure
```
tanf/
├── eligibility/
│   ├── demographic_eligible.py
│   ├── income_eligible.py
│   └── eligible.py
├── income/
│   ├── earned/
│   ├── unearned/
│   └── countable_income.py
└── [state]_tanf.py
```

### Simplified TANF Rules

For simplified implementations:

**DON'T create state-specific versions of:**
- Demographic eligibility (use federal)
- Immigration eligibility (use federal)
- Income sources (use federal baseline)

```python
❌ DON'T CREATE:
ca_tanf_demographic_eligible_person.py
ca_tanf_gross_earned_income.py
parameters/.../income/sources/earned.yaml

✅ DO USE:
# Federal demographic eligibility
is_demographic_tanf_eligible
# Federal income aggregation
tanf_gross_earned_income
```

### Avoiding Unnecessary Wrapper Variables (CRITICAL)

**Golden Rule: Only create a state variable if you're adding state-specific logic to it!**

#### Understand WHY Variables Exist, Not Just WHAT

When studying reference implementations:
1. **Note which variables they have**
2. **READ THE CODE inside each variable**
3. **Ask: "Does this variable have state-specific logic?"**
4. **If it just returns federal baseline → DON'T copy it**

#### Variable Creation Decision Tree

Before creating ANY state-specific variable, ask:
1. Does federal baseline already calculate this?
2. Does my state do it DIFFERENTLY than federal?
3. Can I write the difference in 1+ lines of state-specific logic?
4. **Will this calculation be used in 2+ other variables?** (Code reuse exception)

**Decision:**
- If YES/NO/NO/NO → **DON'T create the variable**, use federal directly
- If YES/YES/YES/NO → **CREATE the variable** with state logic
- If YES/NO/NO/YES → **CREATE as intermediate variable** for code reuse (see exception below)

#### EXCEPTION: Code Reuse Justifies Intermediate Variables

**Even without state-specific logic, create a variable if the SAME calculation is used in multiple places.**

❌ **Bad - Duplicating calculation across variables:**
```python
# Variable 1 - Income eligibility
class mo_tanf_income_eligible(Variable):
    def formula(spm_unit, period, parameters):
        # Duplicated calculation
        gross = add(spm_unit, period, ["tanf_gross_earned_income", "tanf_gross_unearned_income"])
        return gross <= p.income_limit

# Variable 2 - Countable income
class mo_tanf_countable_income(Variable):
    def formula(spm_unit, period, parameters):
        # SAME calculation repeated!
        gross = add(spm_unit, period, ["tanf_gross_earned_income", "tanf_gross_unearned_income"])
        deductions = spm_unit("mo_tanf_deductions", period)
        return max_(gross - deductions, 0)

# Variable 3 - Need standard
class mo_tanf_need_standard(Variable):
    def formula(spm_unit, period, parameters):
        # SAME calculation AGAIN!
        gross = add(spm_unit, period, ["tanf_gross_earned_income", "tanf_gross_unearned_income"])
        return where(gross < p.threshold, p.high, p.low)
```

✅ **Good - Extract into reusable intermediate variable:**
```python
# Intermediate variable - used in multiple places
class mo_tanf_gross_income(Variable):
    adds = ["tanf_gross_earned_income", "tanf_gross_unearned_income"]

# Variable 1 - Reuses intermediate
class mo_tanf_income_eligible(Variable):
    def formula(spm_unit, period, parameters):
        gross = spm_unit("mo_tanf_gross_income", period)  # Reuse
        return gross <= p.income_limit

# Variable 2 - Reuses intermediate
class mo_tanf_countable_income(Variable):
    def formula(spm_unit, period, parameters):
        gross = spm_unit("mo_tanf_gross_income", period)  # Reuse
        deductions = spm_unit("mo_tanf_deductions", period)
        return max_(gross - deductions, 0)

# Variable 3 - Reuses intermediate
class mo_tanf_need_standard(Variable):
    def formula(spm_unit, period, parameters):
        gross = spm_unit("mo_tanf_gross_income", period)  # Reuse
        return where(gross < p.threshold, p.high, p.low)
```

**When to create intermediate variables for reuse:**
- ✅ Same calculation appears in 2+ variables
- ✅ Represents a meaningful concept (e.g., "gross income", "net resources")
- ✅ Simplifies maintenance (change once vs many places)
- ✅ Follows DRY (Don't Repeat Yourself) principle

**When NOT to create (still a wrapper):**
- ❌ Only used in ONE place
- ❌ Just passes through another variable unchanged
- ❌ Adds indirection without code reuse benefit

#### Red Flags for Unnecessary Wrapper Variables

```python
❌ INVALID - Pure wrapper, no state logic:
class in_tanf_assistance_unit_size(Variable):
    def formula(spm_unit, period):
        return spm_unit("spm_unit_size", period)  # Just returns federal

❌ INVALID - Aggregation without transformation:
class in_tanf_countable_unearned_income(Variable):
    def formula(tax_unit, period):
        return tax_unit.sum(person("tanf_gross_unearned_income", period))

❌ INVALID - Pass-through with no modification:
class in_tanf_gross_income(Variable):
    def formula(entity, period):
        return entity("tanf_gross_income", period)
```

#### Examples of VALID State Variables

```python
✅ VALID - Has state-specific disregard:
class in_tanf_countable_earned_income(Variable):
    def formula(spm_unit, period, parameters):
        p = parameters(period).gov.states.in.tanf.income
        earned = spm_unit("tanf_gross_earned_income", period)
        return earned * (1 - p.earned_income_disregard_rate)  # STATE LOGIC

✅ VALID - Uses state-specific limits:
class in_tanf_income_eligible(Variable):
    def formula(spm_unit, period, parameters):
        p = parameters(period).gov.states.in.tanf
        income = spm_unit("tanf_countable_income", period)
        size = spm_unit("spm_unit_size", period.this_year)
        limit = p.income_limit[min_(size, p.max_household_size)]  # STATE PARAMS
        return income <= limit

✅ VALID - IL has different counting rules:
class il_tanf_assistance_unit_size(Variable):
    adds = [
        "il_tanf_payment_eligible_child",  # STATE-SPECIFIC
        "il_tanf_payment_eligible_parent",  # STATE-SPECIFIC
    ]
```

### Enum Variables with Numeric Ranges Must Have Formulas

**When an enum's labels describe numeric ranges (e.g., "30+ hours/week", "20-29 hours/week"), it MUST be a formula variable, not a bare input.** The numeric breakpoints should be a bracket parameter, and the formula should derive the category from an existing numeric input variable.

**❌ WRONG — bare input enum, user picks manually:**
```python
class program_time_category(Variable):
    value_type = Enum
    possible_values = TimeCategory  # "30+ hrs", "20-29 hrs", etc.
    default_value = TimeCategory.FULL_TIME
    # No formula — user must select
```

**✅ CORRECT — derived from a numeric input via bracket parameter:**
```yaml
# time_category.yaml — single_amount bracket maps numeric input to category index
brackets:
  - threshold:
      2024-01-01: 0
    amount:
      2024-01-01: 4  # QUARTER_TIME
  - threshold:
      2024-01-01: 10
    amount:
      2024-01-01: 3  # HALF_TIME
  - threshold:
      2024-01-01: 20
    amount:
      2024-01-01: 2  # THREE_QUARTER_TIME
  - threshold:
      2024-01-01: 30
    amount:
      2024-01-01: 1  # FULL_TIME
```
```python
class program_time_category(Variable):
    value_type = Enum
    possible_values = TimeCategory
    default_value = TimeCategory.FULL_TIME

    def formula(person, period, parameters):
        hours = person("childcare_hours_per_week", period)
        p = parameters(period).gov.states.xx.agency.program
        return p.time_category.calc(hours)
```

Before creating any enum variable, check:
1. Do the labels describe numeric ranges or thresholds?
2. Does an existing input variable provide the numeric value? (Grep the codebase)
3. If yes to both → use a bracket parameter + formula, not a bare input

### Rate Table Dimensions: One Enum Variable Per Dimension

**When a rate table has multiple dimensions (provider type, age group, star rating, authorization level), create a separate Enum variable for each dimension.** This enables simple Enum bracket indexing in the rate lookup variable.

**Pattern:**
```python
# Each dimension is its own Enum variable:
provider_type = person("ri_ccap_provider_type", period)
time_category = person("ri_ccap_time_category", period)
star_rating = person("ri_ccap_star_rating", period)
age_group = person("ri_ccap_center_age_group", period)

# Rate lookup is just Enum indexing:
rate = p.licensed_center[time_category][star_rating][age_group]
```

**When dimensions differ by category, use separate Enums:**
- Licensed centers have 4 age groups (Infant, Toddler, Preschool, School Age)
- Family child care has 3 age groups (Infant/Toddler, Preschool, School Age)
- → Create `ri_ccap_center_age_group` and `ri_ccap_family_age_group`

**When quality ratings differ by provider type:**
- Licensed centers/family use star ratings (1-5)
- License-exempt uses step ratings (1-4)
- → Create `ri_ccap_star_rating` and `ri_ccap_step_rating` as separate Enums

**Use Enum (not int) for constrained categories:**
```python
# ❌ BAD — star rating as int (what values are valid? unclear)
class ri_ccap_star_rating(Variable):
    value_type = int

# ✅ GOOD — star rating as Enum (self-documenting, validated)
class RICCAPStarRating(Enum):
    STAR_1 = "1 Star"
    STAR_2 = "2 Stars"
    STAR_3 = "3 Stars"
    STAR_4 = "4 Stars"
    STAR_5 = "5 Stars"
```

**If you need helper functions in a rate lookup, your parameter structure is too granular.** Restructure the parameter files to use Enum breakdowns (see parameter-patterns skill) so the variable is just `select()` + indexing.

**Reference implementation:** MA CCFA reimbursement — `ma_ccfa_center_based_early_education_reimbursement.py` is 3 lines: get region, get age category, index into parameter.

#### State Variables to AVOID Creating

For TANF implementations:

**❌ DON'T create these (use federal directly):**
- `state_tanf_assistance_unit_size` (unless different counting rules like IL)
- `state_tanf_countable_unearned_income` (unless state has disregards)
- `state_tanf_gross_income` (just use federal baseline)
- Any variable that's just `return entity("federal_variable", period)`

**✅ DO create these (when state has unique rules):**
- `state_tanf_countable_earned_income` (if unique disregard %)
- `state_tanf_income_eligible` (state income limits)
- `state_tanf_maximum_benefit` (state payment standards)
- `state_tanf` (final benefit calculation)

### Demographic Eligibility Pattern

**Option 1: Use Federal (Simplified)**
```python
class ca_tanf_eligible(Variable):
    def formula(spm_unit, period, parameters):
        # Use federal variable
        has_eligible = spm_unit.any(
            spm_unit.members("is_demographic_tanf_eligible", period)
        )
        return has_eligible & income_eligible
```

**Option 2: State-Specific (Different thresholds)**
```python
class ca_tanf_demographic_eligible_person(Variable):
    def formula(person, period, parameters):
        p = parameters(period).gov.states.ca.tanf
        age = person("age", period.this_year)  # NOT monthly_age

        age_limit = where(
            person("is_full_time_student", period),
            p.age_threshold.student,
            p.age_threshold.minor_child
        )
        return age < age_limit
```

---

## Common Implementation Patterns

### Income Eligibility
```python
class program_income_eligible(Variable):
    value_type = bool
    entity = SPMUnit
    definition_period = MONTH

    def formula(spm_unit, period, parameters):
        p = parameters(period).gov.states.xx.program
        income = spm_unit("program_countable_income", period)
        size = spm_unit("spm_unit_size", period.this_year)

        # Get threshold from parameters
        threshold = p.income_limit[min_(size, p.max_household_size)]
        return income <= threshold
```

### Benefit Calculation
```python
class program_benefit(Variable):
    value_type = float
    entity = SPMUnit
    definition_period = MONTH
    unit = USD

    def formula(spm_unit, period, parameters):
        p = parameters(period).gov.states.xx.program
        eligible = spm_unit("program_eligible", period)

        # Calculate benefit amount
        base = p.benefit_schedule.base_amount
        adjustment = p.benefit_schedule.adjustment_rate
        size = spm_unit("spm_unit_size", period.this_year)

        amount = base + (size - 1) * adjustment
        return where(eligible, amount, 0)
```

### Using Scale Parameters
```python
def formula(entity, period, parameters):
    p = parameters(period).gov.states.az.program
    federal_p = parameters(period).gov.hhs.fpg

    # Federal base with state scale
    size = entity("household_size", period.this_year)
    fpg = federal_p.first_person + federal_p.additional * (size - 1)
    state_scale = p.income_limit_scale  # Often exists
    income_limit = fpg * state_scale
```

### Handling Parameter Structure Transitions

**When a parameter changes structure over time** (e.g., flat rate → marginal brackets), the parameter side uses a boolean toggle with separate files (see parameter patterns skill). The variable must branch on that toggle.

**Pattern: Use `if p.toggle:` to select the right parameter access method:**

```python
class wa_capital_gains_tax(Variable):
    value_type = float
    entity = TaxUnit
    definition_period = YEAR
    unit = USD
    defined_for = StateCode.WA

    def formula(tax_unit, period, parameters):
        p = parameters(period).gov.states.wa.tax.income.capital_gains
        taxable_ltcg = ...  # calculation

        # Toggle between flat and bracket-based calculation
        if p.rate.flat_applies:
            return taxable_ltcg * p.rate.flat
        return p.rate.incremental.calc(taxable_ltcg)
```

**Why `if` (not `where`) is correct here:**
- `p.rate.flat_applies` is a **parameter** (scalar boolean at a given instant), not a per-entity variable
- Python `if` is appropriate because the entire population uses the same rate structure in a given year
- `where()` is for per-entity branching (e.g., different treatment by filing status)

**When to use this pattern:**
- ✅ A flat rate became a marginal bracket schedule at a specific date
- ✅ A single value became a lookup table at a specific date
- ✅ Any parameter whose access method (`.calc()` vs `*`) changes by period

**When NOT to use this pattern:**
- ❌ The parameter structure is the same across all periods (just access it normally)
- ❌ The branching depends on a per-entity condition like income or age (use `where()` instead)
- ❌ A new bracket was added to an existing scale using `.inf` (no variable changes needed — `.calc()` works as before; see parameter patterns skill)

### Gating Provisions with `in_effect` Boolean

**When a provision starts or ends at a specific date**, use `if p.provision.in_effect:` to gate the entire logic block. The parameter side has an `in_effect.yaml` boolean (see parameter patterns skill). The variable wraps the provision's logic in a plain `if` block.

**Real-world example — CT TFA high-earnings reduction (new in 2024):**

```python
class ct_tfa(Variable):
    value_type = float
    entity = SPMUnit
    definition_period = MONTH
    unit = USD
    defined_for = "ct_tfa_eligible"

    def formula(spm_unit, period, parameters):
        p = parameters(period).gov.states.ct.dss.tfa.payment
        payment_standard = spm_unit("ct_tfa_payment_standard", period)
        countable_unearned_income = spm_unit(
            "ct_tfa_countable_unearned_income", period
        )
        raw_benefit = max_(payment_standard - countable_unearned_income, 0)

        # Per CGS § 17b-112(d), high earners have their benefit reduced.
        # This provision did not exist before 2024.
        if p.high_earnings.in_effect:
            gross_earnings = add(
                spm_unit, period, ["tanf_gross_earned_income"]
            )
            fpg = spm_unit("tanf_fpg", period)
            high_income_threshold = p.high_earnings.rate * fpg
            high_income = gross_earnings >= high_income_threshold
            reduction_multiplier = 1 - p.high_earnings.reduction_rate
            return where(
                high_income,
                raw_benefit * reduction_multiplier,
                raw_benefit,
            )
        return raw_benefit
```

**Key points:**
- `if p.high_earnings.in_effect:` uses Python `if` because it's a **parameter** (scalar boolean), not a per-entity variable
- The `if` block is NEVER entered for periods before the effective date (2024)
- Inside the `if` block, `where()` IS used for per-entity branching (some households have high income, others don't)
- The provision's sub-parameters (`rate`, `reduction_rate`) are only accessed inside the guarded block

**When to use this pattern:**
- ✅ A new provision is added by legislation at a specific date
- ✅ An existing provision is repealed at a specific date
- ✅ The provision gates an entire block of logic with its own sub-parameters

**When NOT to use this pattern:**
- ❌ The branching depends on a per-entity condition (use `where()` instead)
- ❌ The parameter structure changes (use `flat_applies` pattern above)

### Regional Variation with `regional_in_effect` Boolean

**When a program transitions between regional and statewide payment standards**, use `if p.regional_in_effect:` to switch between regional enum lookup and flat parameter access.

**Real-world example — CT TFA payment standard (regional before 2022, flat after):**

```python
class ct_tfa_payment_standard(Variable):
    value_type = float
    entity = SPMUnit
    definition_period = MONTH
    unit = USD
    defined_for = StateCode.CT

    def formula(spm_unit, period, parameters):
        p = parameters(period).gov.states.ct.dss.tfa.payment
        size = spm_unit("spm_unit_size", period.this_year)
        capped_size = min_(size, p.max_unit_size)

        if p.regional_in_effect:
            region = spm_unit.household("ct_tfa_region", period)
            region_a = region == region.possible_values.REGION_A
            region_c = region == region.possible_values.REGION_C
            return select(
                [region_a, region_c],
                [
                    p.regional.region_a.amount[capped_size],
                    p.regional.region_c.amount[capped_size],
                ],
                default=p.regional.region_b.amount[capped_size],
            )

        return p.amount[capped_size]
```

**Key points:**
- `if p.regional_in_effect:` uses Python `if` — scalar parameter boolean
- Inside the `if` block, `select()` handles per-entity branching by region enum
- The `default` parameter in `select()` handles regions not explicitly listed
- When `regional_in_effect` is `false`, falls through to the flat `p.amount[capped_size]`
- Region enum variable (`ct_tfa_region`) is only accessed when regional variation is active

**When to use this pattern:**
- ✅ Program transitions from regional to statewide standards (or vice versa)
- ✅ Regional lookup uses an enum variable with `select()`
- ✅ The flat and regional parameter trees have different structures

**When NOT to use this pattern:**
- ❌ Regional variation always applies (just use regional parameters directly)
- ❌ The variation is by household characteristic, not geography (use `where()`)

### Choosing Between Boolean Toggle Patterns (Summary)

All three patterns use `if p.boolean:` branching on a scalar parameter. Here's when to use each:

| Pattern | Parameter Side | Variable Side | Use Case |
|---|---|---|---|
| `flat_applies` | Folder with flat + bracket + toggle | `if p.flat_applies:` switches access method | Structure changes (flat → brackets) |
| `in_effect` | Single `in_effect.yaml` + sibling params | `if p.provision.in_effect:` gates logic block | Provision starts/ends at date |
| `regional_in_effect` | Single boolean + regional/ folder + flat | `if p.regional_in_effect:` switches lookup | Regional ↔ statewide transition |

**Common rule:** All use Python `if` (not `where`) because parameters are scalar booleans at a given instant — the entire population uses the same code path for a given period.

See **policyengine-parameter-patterns** skill for the parameter-side implementation of each pattern.

---

## Parameter-to-Variable Mapping Requirements

### Every Parameter Must Have a Variable

**CRITICAL: Complete implementation means every parameter is used!**

When you create parameters, you MUST create corresponding variables:

| Parameter Type | Required Variable(s) |
|---------------|---------------------|
| resources/limit | `state_program_resources_eligible` |
| income/limit | `state_program_income_eligible` |
| min_work_hours or activity_requirements | `state_program_activity_eligible` |
| payment_standard | `state_program_maximum_benefit` |
| income/disregard | `state_program_countable_earned_income` |
| categorical/requirements | `state_program_categorically_eligible` |

### Complete Eligibility Formula

The main eligibility variable MUST combine ALL checks:

```python
class state_program_eligible(Variable):
    def formula(spm_unit, period, parameters):
        income_eligible = spm_unit("state_program_income_eligible", period)
        resources_eligible = spm_unit("state_program_resources_eligible", period)  # DON'T FORGET!
        categorical = spm_unit("state_program_categorically_eligible", period)

        return income_eligible & resources_eligible & categorical
```

**Common Implementation Failures:**
- ❌ Created resource limit parameter but no resource_eligible variable
- ❌ Created min_work_hours parameter but no activity_eligible variable
- ❌ Main eligible variable only checks income, ignores resources/work/immigration
- ❌ Parameters created but never referenced in any formula
- ❌ Spec lists requirements (work hours, citizenship) but no variables implement them

---

## Childcare Subsidy Benefit Calculation

Childcare subsidy programs (CCAP, CCFA, etc.) share a common pattern: the benefit is capped at actual childcare expenses, not just the provider reimbursement rate.

PolicyEngine has an existing federal variable `pre_subsidy_childcare_expenses` (Person, YEAR) that represents what families actually pay for childcare. **Always use this variable** — don't calculate the benefit from provider rates alone.

```python
# ❌ BAD — subsidy based only on provider rate (ignores actual expenses)
class ri_ccap(Variable):
    def formula(spm_unit, period, parameters):
        total_weekly_rate = spm_unit.sum(weekly_rate * is_eligible_child)
        return max_(total_weekly_rate - family_share, 0)

# ✅ GOOD — subsidy capped at actual expenses (matches MA CCFA, CO CCAP pattern)
class ri_ccap(Variable):
    def formula(spm_unit, period, parameters):
        actual_expenses = spm_unit(
            "spm_unit_pre_subsidy_childcare_expenses", period.this_year
        )
        copay = spm_unit("ri_ccap_family_share", period)
        max_reimbursement = add(spm_unit, period, ["ri_ccap_weekly_provider_rate"])
        uncapped_benefit = max_(actual_expenses - copay, 0)
        return min_(uncapped_benefit, max_reimbursement)
```

The subsidy is the lesser of:
1. Actual expenses minus co-payment
2. Maximum reimbursement (provider rate based on type, quality, age, time)

---

