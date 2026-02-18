"""
Helper functions for creating PolicyEngine-US inputs.

These utilities simplify the creation of household inputs for both:
1. New API: USHouseholdInput for calculate_household_impact()
2. Legacy API: Situation dictionaries for policyengine_us.Simulation
"""

CURRENT_YEAR = 2026


# =============================================================================
# NEW API HELPERS (for USHouseholdInput)
# =============================================================================

def create_us_household_input(
    people,
    year=CURRENT_YEAR,
    state="CA",
    filing_status=None,
    **kwargs
):
    """
    Create a USHouseholdInput-compatible dict for the new policyengine API.

    Args:
        people (list): List of person dicts with tax unit roles
        year (int): Tax year (default: 2026)
        state (str): Two-letter state code (e.g., "CA", "NY")
        filing_status (str): Filing status ("JOINT", "SEPARATE", "HEAD_OF_HOUSEHOLD")
        **kwargs: Additional entity attributes

    Returns:
        dict: Arguments to pass to USHouseholdInput

    Example:
        from policyengine.tax_benefit_models.us import USHouseholdInput, calculate_household_impact

        input_args = create_us_household_input(
            people=[{"age": 35, "employment_income": 50000, "is_tax_unit_head": True}],
            state="CA",
        )
        household = USHouseholdInput(**input_args)
        result = calculate_household_impact(household)
    """
    result = {
        "people": people,
        "year": year,
        "household": {"state_code_str": state},
    }

    if filing_status:
        result["tax_unit"] = {"filing_status": filing_status}

    # Merge any additional kwargs
    for key in ["household", "tax_unit", "spm_unit", "family", "marital_unit"]:
        if key in kwargs:
            if key in result:
                result[key].update(kwargs[key])
            else:
                result[key] = kwargs[key]

    return result


def create_single_filer_input(income, state="CA", age=35, year=CURRENT_YEAR, **kwargs):
    """
    Create USHouseholdInput args for a single filer.

    Args:
        income (float): Employment income
        state (str): Two-letter state code
        age (int): Person's age
        year (int): Tax year
        **kwargs: Additional person attributes

    Returns:
        dict: Arguments for USHouseholdInput
    """
    person = {"age": age, "employment_income": income, "is_tax_unit_head": True}
    person.update(kwargs)
    return create_us_household_input(people=[person], year=year, state=state)


def create_married_couple_input(
    income_1, income_2=0, state="CA", age_1=35, age_2=35, year=CURRENT_YEAR, **kwargs
):
    """
    Create USHouseholdInput args for a married couple filing jointly.

    Args:
        income_1 (float): First spouse's employment income
        income_2 (float): Second spouse's employment income
        state (str): Two-letter state code
        age_1 (int): First spouse's age
        age_2 (int): Second spouse's age
        year (int): Tax year

    Returns:
        dict: Arguments for USHouseholdInput
    """
    people = [
        {"age": age_1, "employment_income": income_1, "is_tax_unit_head": True},
        {"age": age_2, "employment_income": income_2, "is_tax_unit_spouse": True},
    ]
    return create_us_household_input(
        people=people, year=year, state=state, filing_status="JOINT", **kwargs
    )


def create_family_input(
    parent_income,
    num_children=1,
    child_ages=None,
    state="CA",
    parent_age=35,
    married=False,
    spouse_income=0,
    year=CURRENT_YEAR,
    **kwargs
):
    """
    Create USHouseholdInput args for a family with children.

    Args:
        parent_income (float): Primary parent's employment income
        num_children (int): Number of children
        child_ages (list): List of child ages (defaults to [5, 8, 11, ...])
        state (str): Two-letter state code
        parent_age (int): Parent's age
        married (bool): Whether parents are married
        spouse_income (float): Spouse's income if married
        year (int): Tax year

    Returns:
        dict: Arguments for USHouseholdInput
    """
    if child_ages is None:
        child_ages = [5 + i * 3 for i in range(num_children)]
    elif len(child_ages) != num_children:
        raise ValueError("Length of child_ages must match num_children")

    people = [{"age": parent_age, "employment_income": parent_income, "is_tax_unit_head": True}]

    if married:
        people.append({
            "age": parent_age,
            "employment_income": spouse_income,
            "is_tax_unit_spouse": True
        })

    for age in child_ages:
        people.append({"age": age, "is_tax_unit_dependent": True})

    filing_status = "JOINT" if married else "HEAD_OF_HOUSEHOLD"
    return create_us_household_input(
        people=people, year=year, state=state, filing_status=filing_status, **kwargs
    )


# =============================================================================
# LEGACY API HELPERS (for policyengine_us.Simulation situation dicts)
# =============================================================================

def create_single_filer(income, state="CA", age=35, **kwargs):
    """
    [LEGACY] Create a situation dict for a single tax filer.

    For the new API, use create_single_filer_input() instead.
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
    [LEGACY] Create a situation dict for a married couple filing jointly.

    For the new API, use create_married_couple_input() instead.
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
    [LEGACY] Create a situation dict for a family with children.

    For the new API, use create_family_input() instead.
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

    marital_members = members if married else ["parent"]

    return {
        "people": people,
        "families": {"family": {"members": members}},
        "marital_units": {"marital_unit": {"members": marital_members}},
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
    [LEGACY] Add itemized deductions to an existing situation.
    """
    first_person = list(situation["people"].keys())[0]

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
