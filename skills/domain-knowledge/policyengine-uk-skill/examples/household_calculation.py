"""
Example: Household calculation using the new policyengine API.

This example shows how to calculate taxes and benefits for a single household
using UKHouseholdInput and calculate_household_impact().
"""

from policyengine.tax_benefit_models.uk import (
    UKHouseholdInput,
    calculate_household_impact,
)

# Single person earning £50,000 in London
household = UKHouseholdInput(
    people=[
        {"age": 35, "employment_income": 50_000},
    ],
    household={"region": "LONDON"},
    year=2026,
)

result = calculate_household_impact(household)

print("=== Single Person (£50k income) ===")
print(f"Income tax: £{result.person[0]['income_tax']:,.0f}")
print(f"National Insurance: £{result.person[0]['national_insurance']:,.0f}")
print(f"Net income: £{result.household['hbai_household_net_income']:,.0f}")

# Family with two children claiming Universal Credit
family = UKHouseholdInput(
    people=[
        {"age": 35, "employment_income": 25_000},
        {"age": 33},
        {"age": 8},
        {"age": 5},
    ],
    benunit={"would_claim_uc": True},
    household={"region": "NORTH_WEST", "rent": 12_000},
    year=2026,
)

family_result = calculate_household_impact(family)

print("\n=== Family with 2 Children (£25k income, claiming UC) ===")
print(f"Income tax: £{family_result.person[0]['income_tax']:,.0f}")
print(f"Universal Credit: £{family_result.benunit[0]['universal_credit']:,.0f}")
print(f"Child Benefit: £{family_result.benunit[0]['child_benefit']:,.0f}")
print(f"Net income: £{family_result.household['hbai_household_net_income']:,.0f}")
