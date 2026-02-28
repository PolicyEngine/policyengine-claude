"""
Template for PolicyEngine reform impact analysis.

This template provides a starting point for analyzing the impact
of a policy reform across the income distribution.
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
from policyengine_us import Simulation

# Configuration
CURRENT_YEAR = 2026
INCOME_MIN = 0
INCOME_MAX = 200000
INCOME_STEPS = 101

# Define your reform here
REFORM = {
    "gov.irs.credits.ctc.amount.base[0].amount": {
        "2026-01-01.2100-12-31": 5000  # Example: Increase CTC to $5,000
    }
}


def create_situation(income, num_children=0, state="CA"):
    """Create a basic household situation."""
    people = {
        "parent": {
            "age": {CURRENT_YEAR: 35},
            "employment_income": {CURRENT_YEAR: income}
        }
    }

    members = ["parent"]

    # Add children
    for i in range(num_children):
        child_id = f"child_{i+1}"
        people[child_id] = {"age": {CURRENT_YEAR: 8}}
        members.append(child_id)

    return {
        "people": people,
        "families": {"family": {"members": members}},
        "marital_units": {"marital_unit": {"members": ["parent"]}},
        "tax_units": {"tax_unit": {"members": members}},
        "spm_units": {"spm_unit": {"members": members}},
        "households": {
            "household": {
                "members": members,
                "state_name": {CURRENT_YEAR: state}
            }
        }
    }


def analyze_reform(num_children=2, state="CA"):
    """Analyze reform impact across income distribution."""
    incomes = np.linspace(INCOME_MIN, INCOME_MAX, INCOME_STEPS)
    results = []

    for income in incomes:
        situation = create_situation(
            income=income,
            num_children=num_children,
            state=state
        )

        # Baseline
        sim_baseline = Simulation(situation=situation)
        income_tax_baseline = sim_baseline.calculate("income_tax", CURRENT_YEAR)[0]
        ctc_baseline = sim_baseline.calculate("ctc", CURRENT_YEAR)[0]
        net_income_baseline = sim_baseline.calculate("household_net_income", CURRENT_YEAR)[0]

        # Reform
        sim_reform = Simulation(situation=situation, reform=REFORM)
        income_tax_reform = sim_reform.calculate("income_tax", CURRENT_YEAR)[0]
        ctc_reform = sim_reform.calculate("ctc", CURRENT_YEAR)[0]
        net_income_reform = sim_reform.calculate("household_net_income", CURRENT_YEAR)[0]

        results.append({
            "income": income,
            "income_tax_baseline": income_tax_baseline,
            "income_tax_reform": income_tax_reform,
            "ctc_baseline": ctc_baseline,
            "ctc_reform": ctc_reform,
            "net_income_baseline": net_income_baseline,
            "net_income_reform": net_income_reform,
            "tax_change": income_tax_reform - income_tax_baseline,
            "ctc_change": ctc_reform - ctc_baseline,
            "net_income_change": net_income_reform - net_income_baseline
        })

    return pd.DataFrame(results)


def create_chart(df, title="Reform Impact Analysis"):
    """Create Plotly chart of reform impacts."""
    TEAL = "#39C6C0"

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df.income,
        y=df.net_income_change,
        mode='lines',
        name='Net Income Change',
        line=dict(color=TEAL, width=3)
    ))

    fig.update_layout(
        title=title,
        xaxis_title="Income",
        yaxis_title="Net Income Change ($)",
        font=dict(family="Inter", size=14),
        plot_bgcolor="white",
        hovermode="x unified",
        xaxis=dict(
            tickformat="$,.0f",
            showgrid=True,
            gridcolor="lightgray"
        ),
        yaxis=dict(
            tickformat="$,.0f",
            showgrid=True,
            gridcolor="lightgray",
            zeroline=True,
            zerolinecolor="black",
            zerolinewidth=1
        )
    )

    return fig


def print_summary(df):
    """Print summary statistics."""
    print("\n=== Reform Impact Summary ===\n")

    winners = df[df.net_income_change > 0]
    losers = df[df.net_income_change < 0]

    print(f"Winners: {len(winners) / len(df) * 100:.1f}%")
    print(f"Losers: {len(losers) / len(df) * 100:.1f}%")

    if len(winners) > 0:
        print(f"\nAverage gain (winners): ${winners.net_income_change.mean():,.2f}")
        print(f"Max gain: ${df.net_income_change.max():,.2f}")

    if len(losers) > 0:
        print(f"\nAverage loss (losers): ${losers.net_income_change.mean():,.2f}")
        print(f"Max loss: ${df.net_income_change.min():,.2f}")

    print(f"\nAverage CTC change: ${df.ctc_change.mean():,.2f}")
    print(f"Average tax change: ${df.tax_change.mean():,.2f}")


if __name__ == "__main__":
    # Run analysis
    print("Running reform analysis...")
    df = analyze_reform(num_children=2, state="CA")

    # Print summary
    print_summary(df)

    # Save results
    df.to_csv("reform_impact_results.csv", index=False)
    print("\nResults saved to reform_impact_results.csv")

    # Create and save chart
    fig = create_chart(df)
    fig.write_html("reform_impact_chart.html")
    print("Chart saved to reform_impact_chart.html")

    # Display chart (if running interactively)
    fig.show()
