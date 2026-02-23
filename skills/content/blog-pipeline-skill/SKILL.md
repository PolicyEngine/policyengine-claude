---
name: blog-pipeline
description: End-to-end blog post pipeline - results.json schema, template syntax, policyengine.py local simulation, chart generation, and SEO-optimized publishing
---

# Blog Post Pipeline

How to produce a fully traceable, SEO-optimized blog post from a policy reform using `policyengine.py` for local simulation.

## For Users

### What This Pipeline Does

Every PolicyEngine blog post follows a strict pipeline:

1. **Agent runs simulations locally** using `policyengine.py` — full microsimulation, all variables accessible
2. **Agent generates results.json** with every value, table, and chart traceable to its source
3. **Agent writes a blog post** using `{{value}}` template references — zero hard-coded numbers
4. **Build step resolves templates** at deploy time by fetching results.json from GitHub
5. **Output is fully indexable** — text with source links, `<img>` charts with alt text, HTML tables

### Core Principles

1. **Zero hard-coded values** — every number comes from results.json
2. **Every number is traceable** — click any number to see the code line that produced it
3. **No iframes** — charts are static `<img>` from GitHub Pages with descriptive alt text
4. **No computation in posts** — blog posts are a presentation layer only
5. **Auto-updating on deploy** — resolve-posts fetches latest results.json automatically
6. **Neutral language** — active voice, quantitative precision, no value judgments (see policyengine-writing-skill)

---

## For Analysts

### results.json Schema

Every analysis produces a `results.json` file. This is the contract between the analysis and the blog post.

```json
{
  "metadata": {
    "title": "SALT Cap Repeal Impact Analysis",
    "repo": "PolicyEngine/salt-cap-analysis",
    "commit": "a1b2c3d",
    "generated_at": "2026-02-23T14:30:00Z",
    "policyengine_version": "0.1.0",
    "dataset": "enhanced_cps_2024",
    "country_id": "us",
    "year": 2026
  },
  "values": {
    "budget_impact": {
      "value": -15200000000,
      "display": "$15.2 billion",
      "source_line": 47,
      "source_url": "https://github.com/PolicyEngine/salt-cap-analysis/blob/main/analysis.py#L47"
    }
  },
  "tables": {
    "distributional": {
      "title": "Distributional Impact by Income Decile",
      "headers": ["Decile", "Avg Change", "% Affected"],
      "rows": [["Bottom 10%", "+$340", "12%"], ["Top 10%", "+$8,200", "89%"]],
      "source_line": 82,
      "source_url": "https://github.com/PolicyEngine/salt-cap-analysis/blob/main/analysis.py#L82"
    }
  },
  "charts": {
    "distributional": {
      "url": "https://PolicyEngine.github.io/salt-cap-analysis/charts/distributional.png",
      "alt": "Bar chart showing SALT cap repeal benefits by income decile. Top 10% gains $8,200 on average.",
      "width": 1200,
      "height": 600,
      "source_line": 105,
      "source_url": "https://github.com/PolicyEngine/salt-cap-analysis/blob/main/analysis.py#L105"
    }
  }
}
```

### Required Fields

| Section | Field | Type | Purpose |
|---------|-------|------|---------|
| metadata | `repo` | string | GitHub org/repo for source links |
| metadata | `commit` | string | Exact commit for reproducibility |
| metadata | `policyengine_version` | string | Package version used |
| metadata | `dataset` | string | Dataset name (e.g., `enhanced_cps_2024`) |
| metadata | `year` | number | Analysis year |
| values.* | `value` | number | Raw numeric value |
| values.* | `display` | string | Formatted display text (e.g., "$15.2 billion") |
| values.* | `source_line` | number | Line number in analysis.py |
| values.* | `source_url` | string | Full GitHub URL to source line |
| tables.* | `headers` | string[] | Column headers |
| tables.* | `rows` | string[][] | Row data (pre-formatted) |
| charts.* | `url` | string | GitHub Pages URL to PNG |
| charts.* | `alt` | string | Descriptive alt text with data points |

---

### Template Syntax

Blog posts use `{{}}` references that are resolved at build time:

| Pattern | Resolves To | Example |
|---------|-------------|---------|
| `{{value_name}}` | Linked display text | `{{budget_impact}}` → `[$15.2 billion](source_url)` |
| `{{table:name}}` | Markdown table with caption | `{{table:distributional}}` → full table |
| `{{chart:name}}` | `![alt](url)` image | `{{chart:distributional}}` → image with alt text |

**✅ Correct template usage:**
```markdown
The reform would cost {{budget_impact}} per year.

{{table:distributional}}

{{chart:distributional}}

The poverty rate changes by {{poverty_change}}.
```

**❌ Wrong — hard-coded numbers:**
```markdown
The reform would cost $15.2 billion per year.

| Decile | Avg Change |
| Bottom 10% | +$340 |

![chart](https://example.com/chart.png)

The poverty rate falls by 3.2%.
```

Every number in the blog post must come from results.json. If you type a raw number into the markdown, it will not have a source link and cannot be traced or auto-updated.

---

### Using policyengine.py

The agent writes and runs Python using `policyengine.py` for all simulations. This runs locally — no API calls, full variable access.

**Install:**
```bash
pip install policyengine
```

**Define a reform:**
```python
from policyengine.core import Simulation, Policy, Parameter, ParameterValue
from policyengine.tax_benefit_models.us import PolicyEngineUSDataset, us_latest
import datetime

# Create reform: e.g., remove SALT cap
param = Parameter(
    name="gov.irs.deductions.itemized.salt_and_real_estate.cap",
    tax_benefit_model_version=us_latest,
    data_type=float,
)
pv = ParameterValue(
    parameter=param,
    start_date=datetime.date(2026, 1, 1),
    end_date=datetime.date(2026, 12, 31),
    value=0,  # Remove cap
)
policy = Policy(name="SALT Cap Repeal", parameter_values=[pv])
```

**Run baseline + reform microsimulations:**
```python
# Load dataset
dataset = PolicyEngineUSDataset(
    name="enhanced_cps_2024",
    filepath="path/to/enhanced_cps_2024.h5",
    year=2026,
)

# Baseline
baseline_sim = Simulation(dataset=dataset, tax_benefit_model_version=us_latest)
baseline_sim.run()

# Reform
reform_sim = Simulation(dataset=dataset, tax_benefit_model_version=us_latest, policy=policy)
reform_sim.run()
```

**Access any variable directly:**
```python
# Household-level results
baseline_net = baseline_sim.output_dataset.data.household["household_net_income"]
reform_net = reform_sim.output_dataset.data.household["household_net_income"]
change = reform_net - baseline_net

# Person-level
baseline_tax = baseline_sim.output_dataset.data.tax_unit["income_tax"]
reform_tax = reform_sim.output_dataset.data.tax_unit["income_tax"]

# Access weights for proper aggregation
weights = baseline_sim.output_dataset.data.household["household_weight"]
```

**Built-in distributional analysis:**
```python
from policyengine.outputs.decile_impact import DecileImpact
from policyengine.outputs.poverty import Poverty
from policyengine.outputs.inequality import Inequality
from policyengine.outputs.change_aggregate import ChangeAggregate, ChangeAggregateType

# Decile impact
decile = DecileImpact(
    baseline_simulation=baseline_sim,
    reform_simulation=reform_sim,
    variable="household_net_income",
)
decile.run()

# Poverty
poverty = Poverty(
    baseline_simulation=baseline_sim,
    reform_simulation=reform_sim,
)
poverty.run()

# Winners/losers count
winners = ChangeAggregate(
    baseline_simulation=baseline_sim,
    reform_simulation=reform_sim,
    variable="household_net_income",
    aggregate_type=ChangeAggregateType.COUNT,
    change_geq=1,
)
winners.run()
```

**Budget impact:**
```python
from policyengine.outputs.aggregate import Aggregate, AggregateType

baseline_revenue = Aggregate(
    simulation=baseline_sim,
    variable="household_tax",
    aggregate_type=AggregateType.SUM,
)
baseline_revenue.run()

reform_revenue = Aggregate(
    simulation=reform_sim,
    variable="household_tax",
    aggregate_type=AggregateType.SUM,
)
reform_revenue.run()

budget_impact = reform_revenue.result - baseline_revenue.result
```

---

### Chart Generation

Generate chart PNGs using Plotly with PolicyEngine brand styling:

```python
import plotly.graph_objects as go
import plotly.io as pio

TEAL = "#39C6C0"
BLUE = "#2C6496"

fig = go.Figure()
fig.add_trace(go.Bar(
    x=[f"Decile {i}" for i in range(1, 11)],
    y=decile_values,
    marker_color=[TEAL if v >= 0 else "#DC2626" for v in decile_values],
))
fig.update_layout(
    template="plotly_white",
    font=dict(family="Inter, sans-serif"),
    xaxis_title="Income Decile",
    yaxis_title="Average Annual Change ($)",
)

os.makedirs("charts", exist_ok=True)
pio.write_image(fig, "charts/distributional.png", width=1200, height=600, scale=2)
```

Charts are deployed to GitHub Pages via a GitHub Actions workflow in the analysis repo.

---

### Alt Text for Charts

Every chart needs descriptive alt text that includes key data points. Critical for SEO and accessibility.

**✅ Correct (descriptive, includes data):**
```
Bar chart showing SALT cap repeal benefits by income decile.
Top decile gains $8,200 average. Bottom decile gains $340 average.
Middle deciles gain $500-$1,200. 89% of top-decile households affected.
```

**❌ Wrong (vague, no data):**
```
Chart showing distributional impact of the reform.
```
```
distributional.png
```
```
Impact by income group.
```

Alt text should:
- Start with the chart type ("Bar chart showing...", "Line chart of...")
- Include 2-3 key data points with actual numbers
- Mention the most significant finding
- Be 1-3 sentences

---

### Blog Post Writing Rules

Blog posts generated through this pipeline must follow the policyengine-writing-skill. Key rules:

#### Neutral tone

**✅ Correct (neutral — describes what policies do):**
```
The reform reduces poverty by 3.2% and raises inequality by 0.16%
The top income decile receives 42% of total benefits
```

**❌ Wrong (value judgments):**
```
The reform successfully reduces poverty but unfortunately raises inequality
The wealthiest households receive a disproportionate share of benefits
```

#### Active voice with specific numbers

**✅ Correct:**
```
The bill lowers the top rate from 5.9% to 5.4%
Repealing the SALT cap costs $15.2 billion in 2026
```

**❌ Wrong:**
```
The top rate is lowered by the bill
Repealing the SALT cap significantly increases the deficit
```

#### Sentence case headings

**✅ Correct:**
```
## Budgetary impact
## Distributional analysis
## Poverty and inequality
```

**❌ Wrong:**
```
## Budgetary Impact
## Distributional Analysis
## Poverty and Inequality
```

#### Show calculations explicitly

**✅ Correct:**
```
The reform costs $15.2 billion per year: $18.4 billion in reduced income tax
revenue, partially offset by $3.2 billion in higher payroll tax collections.
```

**❌ Wrong:**
```
The reform has a significant budgetary impact.
```

---

### Source Tracking

Every value in results.json must include `source_line` and `source_url` pointing to the exact line in analysis.py that computed it:

```python
import inspect

line = inspect.currentframe().f_lineno
budget_impact = reform_revenue.result - baseline_revenue.result

results["values"]["budget_impact"] = {
    "value": budget_impact,
    "display": format_currency(budget_impact),
    "source_line": line,
    "source_url": f"https://github.com/{REPO}/blob/main/analysis.py#L{line}",
}
```

**✅ Correct — every value traceable:**
```json
{
  "budget_impact": {
    "value": -15200000000,
    "display": "$15.2 billion",
    "source_line": 47,
    "source_url": "https://github.com/PolicyEngine/salt-cap/blob/main/analysis.py#L47"
  }
}
```

**❌ Wrong — value without source:**
```json
{
  "budget_impact": {
    "value": -15200000000,
    "display": "$15.2 billion"
  }
}
```

---

## For Contributors

### Analysis Repo Structure

```
analysis-repo/
├── analysis.py          # Main script — policyengine.py simulations, charts, results.json
├── results.json         # Generated output — the contract
├── charts/              # Generated PNGs — deployed to GitHub Pages
│   ├── distributional.png
│   └── household_impact.png
├── requirements.txt     # policyengine, plotly, kaleido
├── README.md            # How to reproduce
└── .github/workflows/
    └── pages.yml        # Auto-deploy charts to GitHub Pages on push
```

### Blog Post in policyengine-app-v2

```
app/src/data/posts/
├── posts.json           # Add entry with analysis_repo field
└── articles/
    └── salt-cap-analysis.md  # Blog post with {{}} template refs
```

**posts.json entry:**
```json
{
  "title": "SALT Cap Repeal Would Cost $15 Billion",
  "description": "Analysis of repealing the SALT deduction cap...",
  "date": "2026-02-23",
  "tags": ["us", "policy", "featured"],
  "authors": ["max-ghenis"],
  "filename": "salt-cap-analysis.md",
  "image": "salt-cap-analysis.png",
  "analysis_repo": "PolicyEngine/salt-cap-analysis"
}
```

The `analysis_repo` field triggers the resolve-posts build step to fetch results.json and resolve all `{{}}` templates before Vite builds the site.

### resolve-posts Build Step

Runs automatically before Vite build:

1. Reads posts.json → finds posts with `analysis_repo` field
2. Fetches `results.json` from `raw.githubusercontent.com/{repo}/main/results.json`
3. Reads the markdown template file
4. Resolves `{{value}}` → `[display](source_url)` (linked text)
5. Resolves `{{table:name}}` → markdown table with caption and source link
6. Resolves `{{chart:name}}` → `![alt](github_pages_url)` image
7. Writes resolved markdown back to the articles directory
8. Vite builds the site with all values populated

### SEO Output

The resolved blog post produces:
- **Text with source links** — every number is a clickable link to the code
- **Charts as `<img>`** — from GitHub Pages with descriptive alt text (fully indexable)
- **Data tables in HTML** — eligible for Google featured snippets
- **JSON-LD Article schema** — served by middleware to crawlers
- **OG tags** — for social media sharing previews

---

## Pipeline Checklist

Before publishing, verify:

- [ ] Every `{{}}` ref in the markdown exists in results.json
- [ ] Every value in results.json has `source_line` and `source_url`
- [ ] Charts load from GitHub Pages URLs
- [ ] Alt text is descriptive with 2-3 key data points
- [ ] No hard-coded numbers in the markdown (search for raw digits)
- [ ] Neutral language — no value judgments (see policyengine-writing-skill)
- [ ] Active voice throughout
- [ ] Sentence case headings
- [ ] Methodology section specifies model version, dataset, and assumptions
- [ ] Source links point to real code lines (not stale line numbers)

---

## Common Issues

| Problem | Cause | Fix |
|---------|-------|-----|
| `{{name}}` appears literally in published post | Key missing from results.json | Add the key to results.json or fix the spelling |
| Source link points to wrong line | Code changed after results.json was generated | Re-run analysis.py to regenerate results.json |
| Chart 404 on GitHub Pages | Pages workflow hasn't run | Push to main to trigger the pages.yml workflow |
| Numbers don't match between text and tables | Template refs point to different values | Each number should reference one canonical value in results.json |
| Alt text says "chart" with no data | Generic placeholder | Rewrite to include chart type and 2-3 key data points |

---

## Resources

- policyengine.py repo: See policyengine-python-client-skill
- Writing skill: See policyengine-writing-skill for tone and style
- Content generation skill: See content-generation-skill for social images
- Analysis skill: See policyengine-analysis-skill for simulation patterns
