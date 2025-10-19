"""
Helper functions for creating PolicyEngine-US situations.

These utilities simplify the creation of situation dictionaries
for common household configurations.
"""

CURRENT_YEAR = 2024


def create_single_filer(income, state="CA", age=35, **kwargs):
    """
    Create a situation for a single tax filer.

    Args:
        income (float): Employment income
        state (str): Two-letter state code (e.g., "CA", "NY")
        age (int): Person's age
        **kwargs: Additional person attributes (e.g., self_employment_income)

    Returns:
        dict: PolicyEngine situation dictionary
    """
    person_attrs = {
        "age": {CURRENT_YEAR: age},
        "employment_income": {CURRENT_YEAR: income},
    }
    person_attrs.update({k: {CURRENT_YEAR: v} for k, v in kwargs.items()})

    return {
        "people": {"person": person_attrs},
        "families": {"family": {"members": ["person"]}},
        "marital_units": {"marital_unit": {"members": ["person"]}},
        "tax_units": {"tax_unit": {"members": ["person"]}},
        "spm_units": {"spm_unit": {"members": ["person"]}},
        "households": {
            "household": {
                "members": ["person"],
                "state_name": {CURRENT_YEAR: state}
            }
        }
    }


def create_married_couple(
    income_1, income_2=0, state="CA", age_1=35, age_2=35, **kwargs
):
    """
    Create a situation for a married couple filing jointly.

    Args:
        income_1 (float): First spouse's employment income
        income_2 (float): Second spouse's employment income
        state (str): Two-letter state code
        age_1 (int): First spouse's age
        age_2 (int): Second spouse's age
        **kwargs: Additional household attributes

    Returns:
        dict: PolicyEngine situation dictionary
    """
    members = ["spouse_1", "spouse_2"]

    household_attrs = {
        "members": members,
        "state_name": {CURRENT_YEAR: state}
    }
    household_attrs.update({k: {CURRENT_YEAR: v} for k, v in kwargs.items()})

    return {
        "people": {
            "spouse_1": {
                "age": {CURRENT_YEAR: age_1},
                "employment_income": {CURRENT_YEAR: income_1}
            },
            "spouse_2": {
                "age": {CURRENT_YEAR: age_2},
                "employment_income": {CURRENT_YEAR: income_2}
            }
        },
        "families": {"family": {"members": members}},
        "marital_units": {"marital_unit": {"members": members}},
        "tax_units": {"tax_unit": {"members": members}},
        "spm_units": {"spm_unit": {"members": members}},
        "households": {"household": household_attrs}
    }


def create_family_with_children(
    parent_income,
    num_children=1,
    child_ages=None,
    state="CA",
    parent_age=35,
    married=False,
    spouse_income=0,
    **kwargs
):
    """
    Create a situation for a family with children.

    Args:
        parent_income (float): Primary parent's employment income
        num_children (int): Number of children
        child_ages (list): List of child ages (defaults to [5, 8, 12, ...])
        state (str): Two-letter state code
        parent_age (int): Parent's age
        married (bool): Whether parents are married
        spouse_income (float): Spouse's income if married
        **kwargs: Additional household attributes

    Returns:
        dict: PolicyEngine situation dictionary
    """
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

    if married:
        people["spouse"] = {
            "age": {CURRENT_YEAR: parent_age},
            "employment_income": {CURRENT_YEAR: spouse_income}
        }
        members.append("spouse")

    for i, age in enumerate(child_ages):
        child_id = f"child_{i+1}"
        people[child_id] = {"age": {CURRENT_YEAR: age}}
        members.append(child_id)

    household_attrs = {
        "members": members,
        "state_name": {CURRENT_YEAR: state}
    }
    household_attrs.update({k: {CURRENT_YEAR: v} for k, v in kwargs.items()})

    return {
        "people": people,
        "families": {"family": {"members": members}},
        "marital_units": {
            "marital_unit": {
                "members": members if married else ["parent"]
            }
        },
        "tax_units": {"tax_unit": {"members": members}},
        "spm_units": {"spm_unit": {"members": members}},
        "households": {"household": household_attrs}
    }


def add_itemized_deductions(
    situation,
    charitable_donations=0,
    mortgage_interest=0,
    real_estate_taxes=0,
    medical_expenses=0,
    casualty_losses=0
):
    """
    Add itemized deductions to an existing situation.

    Adds deductions to the first person in the situation.

    Args:
        situation (dict): Existing PolicyEngine situation
        charitable_donations (float): Cash charitable contributions
        mortgage_interest (float): Mortgage interest paid
        real_estate_taxes (float): State and local property taxes
        medical_expenses (float): Medical and dental expenses
        casualty_losses (float): Casualty and theft losses

    Returns:
        dict: Updated situation with deductions
    """
    # Get first person ID
    first_person = list(situation["people"].keys())[0]

    # Add deductions
    if charitable_donations > 0:
        situation["people"][first_person]["charitable_cash_donations"] = {
            CURRENT_YEAR: charitable_donations
        }

    if mortgage_interest > 0:
        situation["people"][first_person]["mortgage_interest"] = {
            CURRENT_YEAR: mortgage_interest
        }

    if real_estate_taxes > 0:
        situation["people"][first_person]["real_estate_taxes"] = {
            CURRENT_YEAR: real_estate_taxes
        }

    if medical_expenses > 0:
        situation["people"][first_person]["medical_expense"] = {
            CURRENT_YEAR: medical_expenses
        }

    if casualty_losses > 0:
        situation["people"][first_person]["casualty_loss"] = {
            CURRENT_YEAR: casualty_losses
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


def set_state_nyc(situation, in_nyc=True):
    """
    Set state to NY and configure NYC residence.

    Args:
        situation (dict): Existing PolicyEngine situation
        in_nyc (bool): Whether household is in NYC

    Returns:
        dict: Updated situation
    """
    household_id = list(situation["households"].keys())[0]
    situation["households"][household_id]["state_name"] = {CURRENT_YEAR: "NY"}
    situation["households"][household_id]["in_nyc"] = {CURRENT_YEAR: in_nyc}

    return situation
