"""
Example: Policy reform analysis using the new policyengine API.

This example shows how to create and compare policy reforms using
both ParameterValue (simple) and simulation_modifier (complex) approaches.
"""

from datetime import datetime
from policyengine.core import Simulation, Policy, ParameterValue
from policyengine.tax_benefit_models.uk import (
    uk_latest,
    ensure_datasets,
)
from policyengine.tax_benefit_models.uk.analysis import economic_impact_analysis

# Load dataset
datasets = ensure_datasets(data_folder="./data", years=[2026])
dataset = datasets["enhanced_frs_2023_24_2026"]

# === Method 1: Parametric Reform (ParameterValue) ===
# Simple parameter changes - increase basic rate to 25%

param = uk_latest.get_parameter("gov.hmrc.income_tax.rates.uk[0].rate")

basic_rate_25_policy = Policy(
    name="Basic rate 25%",
    parameter_values=[
        ParameterValue(
            parameter=param,
            value=0.25,
            start_date=datetime(2026, 1, 1),
        )
    ],
)

# === Method 2: Simulation Modifier (Complex Reform) ===
# For programmatic/complex changes - remove 2-child limit


def remove_two_child_limit(sim):
    """Remove the Universal Credit two-child limit."""
    sim.tax_benefit_system.parameters.get_child(
        "gov.dwp.universal_credit.elements.child.limit.child_count"
    ).update(period="year:2026:10", value=float("inf"))
    sim.tax_benefit_system.reset_parameter_caches()


remove_limit_policy = Policy(
    name="Remove UC 2-child limit",
    simulation_modifier=remove_two_child_limit,
)

# Run baseline simulation
baseline_sim = Simulation(
    dataset=dataset,
    tax_benefit_model_version=uk_latest,
)
baseline_sim.ensure()

# Run reform simulation
reform_sim = Simulation(
    dataset=dataset,
    tax_benefit_model_version=uk_latest,
    policy=basic_rate_25_policy,
)
reform_sim.ensure()

# Compare results
baseline_tax = baseline_sim.output_dataset.data.household["household_tax"].sum()
reform_tax = reform_sim.output_dataset.data.household["household_tax"].sum()

print("=== Basic Rate 25% Reform ===")
print(f"Baseline tax revenue: £{baseline_tax / 1e9:.1f}bn")
print(f"Reform tax revenue: £{reform_tax / 1e9:.1f}bn")
print(f"Additional revenue: £{(reform_tax - baseline_tax) / 1e9:.1f}bn")

# Full economic impact analysis
analysis = economic_impact_analysis(
    baseline_simulation=baseline_sim,
    reform_simulation=reform_sim,
)
print(f"\nDecile impacts available: {len(analysis.decile_impacts)} deciles")

# === Combining Policies ===
combined_policy = basic_rate_25_policy + remove_limit_policy
print(f"\nCombined policy: {combined_policy.name}")
