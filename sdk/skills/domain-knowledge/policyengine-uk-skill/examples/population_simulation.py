"""
Example: Population-level microsimulation using the new policyengine API.

This example shows how to run population simulations using datasets
and calculate aggregate statistics.
"""

from policyengine.core import Simulation
from policyengine.tax_benefit_models.uk import (
    uk_latest,
    ensure_datasets,
)

# Load pre-prepared datasets
datasets = ensure_datasets(
    data_folder="./data",
    years=[2026],
)
dataset = datasets["enhanced_frs_2023_24_2026"]

# Run baseline simulation
simulation = Simulation(
    dataset=dataset,
    tax_benefit_model_version=uk_latest,
)
simulation.ensure()  # Runs if not cached, loads from cache if available

# Access output data (weighted MicroDataFrames)
output = simulation.output_dataset.data

# Calculate aggregate statistics
total_income_tax = output.household['household_tax'].sum()
total_uc = output.benunit['universal_credit'].sum()
mean_net_income = output.household['household_net_income'].mean()

print("=== UK Population Statistics (2026) ===")
print(f"Total income tax revenue: £{total_income_tax / 1e9:.1f}bn")
print(f"Total Universal Credit spending: £{total_uc / 1e9:.1f}bn")
print(f"Mean household net income: £{mean_net_income:,.0f}")

# IMPORTANT: Never strip weights from MicroSeries
# WRONG: output.household['income_tax'].values.mean()  # Unweighted!
# CORRECT: output.household['income_tax'].mean()  # Weighted
