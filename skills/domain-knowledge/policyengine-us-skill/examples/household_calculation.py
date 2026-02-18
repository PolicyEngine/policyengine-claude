"""
Example: Household calculation using the new policyengine API.

This example shows how to calculate taxes and benefits for US households
using USHouseholdInput and calculate_household_impact().
"""

from policyengine.tax_benefit_models.us import (
    USHouseholdInput,
    calculate_household_impact,
)

# Single filer in California earning $60,000
household = USHouseholdInput(
    people=[
        {"age": 30, "employment_income": 60_000, "is_tax_unit_head": True},
    ],
    household={"state_code_str": "CA"},
    year=2026,
)

result = calculate_household_impact(household)

print("=== Single Filer ($60k income, CA) ===")
print(f"Income tax: ${result.tax_unit[0]['income_tax']:,.0f}")
print(f"State income tax: ${result.tax_unit[0]['state_income_tax']:,.0f}")
print(f"Net income: ${result.household['household_net_income']:,.0f}")

# Married couple with 2 children in New York
family = USHouseholdInput(
    people=[
        {"age": 35, "employment_income": 45_000, "is_tax_unit_head": True},
        {"age": 33, "employment_income": 0, "is_tax_unit_spouse": True},
        {"age": 8, "is_tax_unit_dependent": True},
        {"age": 5, "is_tax_unit_dependent": True},
    ],
    tax_unit={"filing_status": "JOINT"},
    household={"state_code_str": "NY"},
    year=2026,
)

family_result = calculate_household_impact(family)

print("\n=== Family with 2 Children ($45k income, NY) ===")
print(f"Income tax: ${family_result.tax_unit[0]['income_tax']:,.0f}")
print(f"EITC: ${family_result.tax_unit[0]['eitc']:,.0f}")
print(f"CTC: ${family_result.tax_unit[0]['ctc']:,.0f}")
print(f"SNAP: ${family_result.spm_unit[0]['snap']:,.0f}")
print(f"Net income: ${family_result.household['household_net_income']:,.0f}")
