# Period Patterns Skill Updated

## Update Summary

Successfully added critical clarification about auto-conversion behavior to the `policyengine-period-patterns-skill`.

## What Was Added

### New Section 4: Understanding Auto-Conversion

Added comprehensive explanation of when to use `period` vs `period.this_year` based on whether auto-conversion (dividing by 12) is desired.

### Key Concepts Clarified

1. **The Key Question**: "Should the value be divided by 12?"
   - YES → Use `period` (let auto-conversion happen)
   - NO → Use `period.this_year` (prevent auto-conversion)

2. **Flow vs Stock Variables**:
   - **Flow variables** (income): Auto-conversion makes sense
   - **Stock variables** (age, assets, counts): Auto-conversion breaks things

3. **Decision Tree**: Clear flowchart for choosing the right approach

4. **Complete Example**: Shows all patterns in one realistic scenario

5. **Quick Reference Table**:
   - Income (flow) → Use `period` ✅
   - Age, Assets, Counts, Booleans → Use `period.this_year` ✅

### Rule of Thumb Added

**"If dividing by 12 makes the value meaningless → use `period.this_year`"**

## Examples Provided

- **Age**: 30 years ÷ 12 = 2.5 "monthly age" ❌
- **Assets**: $12,000 ÷ 12 = $1,000 "monthly assets" ❌
- **Household size**: 4 people ÷ 12 = 0.33 people ❌
- **Income**: $24,000/year ÷ 12 = $2,000/month ✅

## Impact

This clarification resolves a common source of confusion about PolicyEngine's auto-conversion behavior. Developers now have clear guidance on:

- When auto-conversion is helpful (income flows)
- When auto-conversion is harmful (demographics, assets, counts)
- How to prevent unwanted conversion (use `period.this_year`)

## Location in Skill

Added as Section 4 (right after Common Patterns as requested), with subsequent sections renumbered (5→6, 6→7, etc.)

This makes the period patterns skill more complete and prevents common bugs where developers accidentally divide age, assets, or household size by 12.