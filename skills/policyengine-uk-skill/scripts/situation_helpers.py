"""
Helper functions for creating PolicyEngine-UK situations.

These utilities simplify the creation of situation dictionaries
for common household configurations.
"""

CURRENT_YEAR = 2025

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


def create_single_person(income, region="LONDON", age=30, **kwargs):
    """
    Create a situation for a single person household.

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
    Create a situation for a couple without children.

    Args:
        income_1 (float): First person's employment income
        income_2 (float): Second person's employment income
        region (str): ITL 1 region
        age_1 (int): First person's age
        age_2 (int): Second person's age
        **kwargs: Additional household attributes

    Returns:
        dict: PolicyEngine situation dictionary
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
    Create a situation for a family with children.

    Args:
        parent_income (float): Primary parent's employment income
        num_children (int): Number of children
        child_ages (list): List of child ages (defaults to [5, 8, 12, ...])
        region (str): ITL 1 region
        parent_age (int): Parent's age
        couple (bool): Whether this is a couple household
        partner_income (float): Partner's income if couple
        **kwargs: Additional household attributes

    Returns:
        dict: PolicyEngine situation dictionary
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


def add_income_sources(
    situation,
    person_id=None,
    self_employment_income=0,
    pension_income=0,
    property_income=0,
    savings_interest_income=0,
    dividend_income=0,
    miscellaneous_income=0
):
    """
    Add additional income sources to a person in an existing situation.

    Args:
        situation (dict): Existing PolicyEngine situation
        person_id (str): Person ID to add income to (defaults to first person)
        self_employment_income (float): Self-employment income
        pension_income (float): Private pension income
        property_income (float): Rental income
        savings_interest_income (float): Interest income
        dividend_income (float): Dividend income
        miscellaneous_income (float): Other income

    Returns:
        dict: Updated situation with additional income
    """
    # Get person ID
    if person_id is None:
        person_id = list(situation["people"].keys())[0]

    # Add income sources
    if self_employment_income > 0:
        situation["people"][person_id]["self_employment_income"] = {
            CURRENT_YEAR: self_employment_income
        }

    if pension_income > 0:
        situation["people"][person_id]["pension_income"] = {
            CURRENT_YEAR: pension_income
        }

    if property_income > 0:
        situation["people"][person_id]["property_income"] = {
            CURRENT_YEAR: property_income
        }

    if savings_interest_income > 0:
        situation["people"][person_id]["savings_interest_income"] = {
            CURRENT_YEAR: savings_interest_income
        }

    if dividend_income > 0:
        situation["people"][person_id]["dividend_income"] = {
            CURRENT_YEAR: dividend_income
        }

    if miscellaneous_income > 0:
        situation["people"][person_id]["miscellaneous_income"] = {
            CURRENT_YEAR: miscellaneous_income
        }

    return situation


def add_axes(situation, variable_name, min_val, max_val, count=1001):
    """
    Add axes to a situation for parameter sweeps.

    Args:
        situation (dict): Existing PolicyEngine situation
        variable_name (str): Variable to vary (e.g., "employment_income")
        min_val (float): Minimum value
        max_val (float): Maximum value
        count (int): Number of points (default: 1001)

    Returns:
        dict: Updated situation with axes
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
    Set or change the region for a household.

    Args:
        situation (dict): Existing PolicyEngine situation
        region (str): ITL 1 region (e.g., "LONDON", "SCOTLAND")

    Returns:
        dict: Updated situation
    """
    if region not in VALID_REGIONS:
        raise ValueError(f"Invalid region. Must be one of: {', '.join(VALID_REGIONS)}")

    household_id = list(situation["households"].keys())[0]
    situation["households"][household_id]["region"] = {CURRENT_YEAR: region}

    return situation


def create_pensioner_household(
    pension_income,
    state_pension_income=0,
    region="LONDON",
    age=70,
    couple=False,
    partner_pension_income=0,
    partner_age=68,
    **kwargs
):
    """
    Create a situation for a pensioner household.

    Args:
        pension_income (float): Private pension income
        state_pension_income (float): State pension income
        region (str): ITL 1 region
        age (int): Pensioner's age
        couple (bool): Whether this is a couple household
        partner_pension_income (float): Partner's pension income if couple
        partner_age (int): Partner's age if couple
        **kwargs: Additional household attributes

    Returns:
        dict: PolicyEngine situation dictionary
    """
    if region not in VALID_REGIONS:
        raise ValueError(f"Invalid region. Must be one of: {', '.join(VALID_REGIONS)}")

    people = {
        "pensioner": {
            "age": {CURRENT_YEAR: age},
            "pension_income": {CURRENT_YEAR: pension_income},
            "state_pension": {CURRENT_YEAR: state_pension_income}
        }
    }

    members = ["pensioner"]

    if couple:
        people["partner"] = {
            "age": {CURRENT_YEAR: partner_age},
            "pension_income": {CURRENT_YEAR: partner_pension_income},
            "state_pension": {CURRENT_YEAR: 0}
        }
        members.append("partner")

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
