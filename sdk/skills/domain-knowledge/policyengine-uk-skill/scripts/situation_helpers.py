"""
Helper functions for creating PolicyEngine-UK inputs.

These utilities simplify the creation of household inputs for both:
1. New API: UKHouseholdInput for calculate_household_impact()
2. Legacy API: Situation dictionaries for policyengine_uk.Simulation
"""

CURRENT_YEAR = 2026

# UK ITL 1 regions
VALID_REGIONS = [
    "NORTH_EAST",
    "NORTH_WEST",
    "YORKSHIRE",
    "EAST_MIDLANDS",
    "WEST_MIDLANDS",
    "EAST_OF_ENGLAND",
    "LONDON",
    "SOUTH_EAST",
    "SOUTH_WEST",
    "WALES",
    "SCOTLAND",
    "NORTHERN_IRELAND"
]


# =============================================================================
# NEW API HELPERS (for UKHouseholdInput)
# =============================================================================

def create_uk_household_input(
    people,
    year=CURRENT_YEAR,
    region="LONDON",
    rent=0,
    would_claim_uc=True,
    **kwargs
):
    """
    Create a UKHouseholdInput-compatible dict for the new policyengine API.

    Args:
        people (list): List of person dicts, e.g., [{"age": 35, "employment_income": 50000}]
        year (int): Tax year (default: 2026)
        region (str): ITL 1 region (e.g., "LONDON", "SCOTLAND")
        rent (float): Annual rent amount
        would_claim_uc (bool): Whether household would claim Universal Credit
        **kwargs: Additional household attributes

    Returns:
        dict: Arguments to pass to UKHouseholdInput

    Example:
        from policyengine.tax_benefit_models.uk import UKHouseholdInput, calculate_household_impact

        input_args = create_uk_household_input(
            people=[{"age": 35, "employment_income": 50000}],
            region="LONDON",
        )
        household = UKHouseholdInput(**input_args)
        result = calculate_household_impact(household)
    """
    if region not in VALID_REGIONS:
        raise ValueError(f"Invalid region. Must be one of: {', '.join(VALID_REGIONS)}")

    household_attrs = {"region": region}
    if rent > 0:
        household_attrs["rent"] = rent
    household_attrs.update(kwargs.get("household", {}))

    benunit_attrs = {"would_claim_uc": would_claim_uc}
    benunit_attrs.update(kwargs.get("benunit", {}))

    return {
        "people": people,
        "year": year,
        "household": household_attrs,
        "benunit": benunit_attrs,
    }


def create_single_person_input(income, region="LONDON", age=30, year=CURRENT_YEAR, **kwargs):
    """
    Create UKHouseholdInput args for a single person.

    Args:
        income (float): Employment income
        region (str): ITL 1 region
        age (int): Person's age
        year (int): Tax year
        **kwargs: Additional person attributes

    Returns:
        dict: Arguments for UKHouseholdInput
    """
    person = {"age": age, "employment_income": income}
    person.update(kwargs)
    return create_uk_household_input(people=[person], year=year, region=region)


def create_couple_input(
    income_1, income_2=0, region="LONDON", age_1=35, age_2=35, year=CURRENT_YEAR, **kwargs
):
    """
    Create UKHouseholdInput args for a couple without children.

    Args:
        income_1 (float): First person's employment income
        income_2 (float): Second person's employment income
        region (str): ITL 1 region
        age_1 (int): First person's age
        age_2 (int): Second person's age
        year (int): Tax year

    Returns:
        dict: Arguments for UKHouseholdInput
    """
    people = [
        {"age": age_1, "employment_income": income_1},
        {"age": age_2, "employment_income": income_2},
    ]
    return create_uk_household_input(people=people, year=year, region=region, **kwargs)


def create_family_input(
    parent_income,
    num_children=1,
    child_ages=None,
    region="LONDON",
    parent_age=35,
    couple=False,
    partner_income=0,
    year=CURRENT_YEAR,
    **kwargs
):
    """
    Create UKHouseholdInput args for a family with children.

    Args:
        parent_income (float): Primary parent's employment income
        num_children (int): Number of children
        child_ages (list): List of child ages (defaults to [5, 8, 11, ...])
        region (str): ITL 1 region
        parent_age (int): Parent's age
        couple (bool): Whether this is a couple household
        partner_income (float): Partner's income if couple
        year (int): Tax year

    Returns:
        dict: Arguments for UKHouseholdInput
    """
    if child_ages is None:
        child_ages = [5 + i * 3 for i in range(num_children)]
    elif len(child_ages) != num_children:
        raise ValueError("Length of child_ages must match num_children")

    people = [{"age": parent_age, "employment_income": parent_income}]

    if couple:
        people.append({"age": parent_age, "employment_income": partner_income})

    for age in child_ages:
        people.append({"age": age})

    return create_uk_household_input(people=people, year=year, region=region, **kwargs)


# =============================================================================
# LEGACY API HELPERS (for policyengine_uk.Simulation situation dicts)
# =============================================================================

def create_single_person(income, region="LONDON", age=30, **kwargs):
    """
    [LEGACY] Create a situation dict for a single person household.

    For the new API, use create_single_person_input() instead.

    Args:
        income (float): Employment income
        region (str): ITL 1 region (e.g., "LONDON", "SCOTLAND")
        age (int): Person's age
        **kwargs: Additional person attributes (e.g., self_employment_income)

    Returns:
        dict: PolicyEngine situation dictionary
    """
    if region not in VALID_REGIONS:
        raise ValueError(f"Invalid region. Must be one of: {', '.join(VALID_REGIONS)}")

    person_attrs = {
        "age": {CURRENT_YEAR: age},
        "employment_income": {CURRENT_YEAR: income},
    }
    person_attrs.update({k: {CURRENT_YEAR: v} for k, v in kwargs.items()})

    return {
        "people": {"person": person_attrs},
        "benunits": {"benunit": {"members": ["person"]}},
        "households": {
            "household": {
                "members": ["person"],
                "region": {CURRENT_YEAR: region}
            }
        }
    }


def create_couple(
    income_1, income_2=0, region="LONDON", age_1=35, age_2=35, **kwargs
):
    """
    [LEGACY] Create a situation dict for a couple without children.

    For the new API, use create_couple_input() instead.
    """
    if region not in VALID_REGIONS:
        raise ValueError(f"Invalid region. Must be one of: {', '.join(VALID_REGIONS)}")

    members = ["person_1", "person_2"]

    household_attrs = {
        "members": members,
        "region": {CURRENT_YEAR: region}
    }
    household_attrs.update({k: {CURRENT_YEAR: v} for k, v in kwargs.items()})

    return {
        "people": {
            "person_1": {
                "age": {CURRENT_YEAR: age_1},
                "employment_income": {CURRENT_YEAR: income_1}
            },
            "person_2": {
                "age": {CURRENT_YEAR: age_2},
                "employment_income": {CURRENT_YEAR: income_2}
            }
        },
        "benunits": {"benunit": {"members": members}},
        "households": {"household": household_attrs}
    }


def create_family_with_children(
    parent_income,
    num_children=1,
    child_ages=None,
    region="LONDON",
    parent_age=35,
    couple=False,
    partner_income=0,
    **kwargs
):
    """
    [LEGACY] Create a situation dict for a family with children.

    For the new API, use create_family_input() instead.
    """
    if region not in VALID_REGIONS:
        raise ValueError(f"Invalid region. Must be one of: {', '.join(VALID_REGIONS)}")

    if child_ages is None:
        child_ages = [5 + i * 3 for i in range(num_children)]
    elif len(child_ages) != num_children:
        raise ValueError("Length of child_ages must match num_children")

    people = {
        "parent": {
            "age": {CURRENT_YEAR: parent_age},
            "employment_income": {CURRENT_YEAR: parent_income}
        }
    }

    members = ["parent"]

    if couple:
        people["partner"] = {
            "age": {CURRENT_YEAR: parent_age},
            "employment_income": {CURRENT_YEAR: partner_income}
        }
        members.append("partner")

    for i, age in enumerate(child_ages):
        child_id = f"child_{i+1}"
        people[child_id] = {"age": {CURRENT_YEAR: age}}
        members.append(child_id)

    household_attrs = {
        "members": members,
        "region": {CURRENT_YEAR: region}
    }
    household_attrs.update({k: {CURRENT_YEAR: v} for k, v in kwargs.items()})

    return {
        "people": people,
        "benunits": {"benunit": {"members": members}},
        "households": {"household": household_attrs}
    }


def add_axes(situation, variable_name, min_val, max_val, count=1001):
    """
    [LEGACY] Add axes to a situation for parameter sweeps.
    """
    situation["axes"] = [[{
        "name": variable_name,
        "count": count,
        "min": min_val,
        "max": max_val,
        "period": CURRENT_YEAR
    }]]
    return situation


def set_region(situation, region):
    """
    [LEGACY] Set or change the region for a household.
    """
    if region not in VALID_REGIONS:
        raise ValueError(f"Invalid region. Must be one of: {', '.join(VALID_REGIONS)}")

    household_id = list(situation["households"].keys())[0]
    situation["households"][household_id]["region"] = {CURRENT_YEAR: region}
    return situation
