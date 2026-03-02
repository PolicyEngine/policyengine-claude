"""
Example: Population-level microsimulation using the new policyengine API.

This example shows how to run US population simulations using datasets.
"""

from policyengine.core import Simulation
from policyengine.tax_benefit_models.us import (
    us_latest,
    ensure_datasets,
)

# Load pre-prepared datasets
datasets = ensure_datasets(
    data_folder="./data",
    years=[2026],
)
dataset = datasets["enhanced_cps_2024_2026"]

# Run baseline simulation
simulation = Simulation(
    dataset=dataset,
    tax_benefit_model_version=us_latest,
)
simulation.ensure()

# Access output data
output = simulation.output_dataset.data

# Calculate aggregate statistics
total_income_tax = output.tax_unit['income_tax'].sum()
total_eitc = output.tax_unit['eitc'].sum()
total_ctc = output.tax_unit['ctc'].sum()
total_snap = output.spm_unit['snap'].sum()

print("=== US Population Statistics (2026) ===")
print(f"Total federal income tax: ${total_income_tax / 1e9:.1f}bn")
print(f"Total EITC: ${total_eitc / 1e9:.1f}bn")
print(f"Total CTC: ${total_ctc / 1e9:.1f}bn")
print(f"Total SNAP: ${total_snap / 1e9:.1f}bn")
