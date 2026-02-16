"""
Example: Policy reform analysis using the new policyengine API.

This example shows how to create and compare policy reforms for the US.
"""

from datetime import datetime
from policyengine.core import Simulation, Policy, ParameterValue
from policyengine.tax_benefit_models.us import (
    us_latest,
    ensure_datasets,
)

# Load dataset
datasets = ensure_datasets(data_folder="./data", years=[2026])
dataset = datasets["enhanced_cps_2024_2026"]

# === Method 1: Parametric Reform ===
# Increase Child Tax Credit to $5,000

param = us_latest.get_parameter("gov.irs.credits.ctc.amount.base_amount")

ctc_5000_policy = Policy(
    name="CTC $5000",
    parameter_values=[
        ParameterValue(
            parameter=param,
            value=5000,
            start_date=datetime(2026, 1, 1),
        )
    ],
)

# === Method 2: Simulation Modifier ===
# Expand EITC phase-out threshold


def expand_eitc(sim):
    """Expand EITC by raising the phase-out start threshold."""
    sim.tax_benefit_system.parameters.get_child(
        "gov.irs.credits.eitc.phase_out.start"
    ).update(period="year:2026:10", value=25000)
    sim.tax_benefit_system.reset_parameter_caches()


eitc_policy = Policy(
    name="Expand EITC",
    simulation_modifier=expand_eitc,
)

# Run baseline
baseline_sim = Simulation(
    dataset=dataset,
    tax_benefit_model_version=us_latest,
)
baseline_sim.ensure()

# Run CTC reform
reform_sim = Simulation(
    dataset=dataset,
    tax_benefit_model_version=us_latest,
    policy=ctc_5000_policy,
)
reform_sim.ensure()

# Compare
baseline_ctc = baseline_sim.output_dataset.data.tax_unit["ctc"].sum()
reform_ctc = reform_sim.output_dataset.data.tax_unit["ctc"].sum()

print("=== CTC $5000 Reform ===")
print(f"Baseline CTC: ${baseline_ctc / 1e9:.1f}bn")
print(f"Reform CTC: ${reform_ctc / 1e9:.1f}bn")
print(f"Additional cost: ${(reform_ctc - baseline_ctc) / 1e9:.1f}bn")
