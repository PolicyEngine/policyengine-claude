---
name: policyengine-prior-scores
description: |
  Structured index of PolicyEngine's previously-published scored reforms. Use this skill to find an anchor for Stage 5 comparison in /analyze-policy, or any time you need a benchmark magnitude for a new policy analysis.
  Returns a queryable mapping of {reform name → (cost, poverty, distribution, year, methodology)} drawn from policyengine.org/{us,uk,canada}/research and blog.policyengine.org.
  Triggers: "prior PE score", "PolicyEngine has scored", "what did PE find", "PE benchmark", "anchor reform", "comparable reform", "EITC expansion scored", "CTC expansion scored", "SALT cap analysis", "state CTC analysis", "ARPA reform impact", "American Family Act score".
---

# PolicyEngine Prior Scores

This skill documents the curated index of PolicyEngine's published reform scores. The index is maintained in `data/prior-scores.json` (alongside this skill) and refreshed by scraping `policyengine.org/{country}/research` and the blog.

## When to use

Load this skill when:
- Running `/analyze-policy` Stage 3 (find prior scores)
- Writing a research blog post and wanting to cite PE's prior work on a similar reform
- Calibrating expectations for a new reform analysis
- The `prior-scores-finder` agent invokes this skill as its first lookup

## Query patterns

### By program

```python
# Pseudocode — the actual implementation reads data/prior-scores.json
priors = get_priors_by_program("federal-ctc")
# Returns:
# [
#   {"reform": "Restoration of ARPA CTC", "annual_cost_billion_2023": 100.2, "child_poverty_pct_change": -37, "url": "..."},
#   {"reform": "American Family Act 2025", "ten_year_cost_billion": 2500, "child_poverty_pct_change": -25.2, "url": "..."},
#   ...
# ]
```

### By state

```python
priors = get_priors_by_jurisdiction(country="us", state="ri")
# Returns RI-specific prior reforms (e.g., the McKee $325 CTC analysis at $36.7M/year).
```

### By reform-keyword

```python
priors = search_priors("SALT cap repeal")
# Fuzzy-matches reform descriptions.
```

## Known anchor reforms (as of 2026-06)

### Federal CTC
- **Restoration of the ARPA expanded CTC** — `policyengine.org/us/research/restoration-of-the-american-rescue-plan-acts-expanded-child-tax-credit` — $100.2B/yr (2023), child poverty −37%, Gini −1.9%. ARPA parameters ($3,600 / $3,000, fully refundable).
- **2025 American Family Act** — `policyengine.org/us/research/american-family-act-2025` — $2.5T/10yr, child poverty −25.2%, deep child poverty −29.9%. Larger amounts + baby bonus + ITIN eligibility.

### Federal EITC
- **Restoring the ARPA EITC** — single-year score ~$9.8B. Childless-adult expansion (max credit ~tripled, age limits widened).
- **NY Working Families Tax Credit** (state-scoped but EITC-adjacent) — $9.1B over 5 years; child poverty −4.0% rising to −16.8% by year-4.

### SALT cap
- **Ways and Means SALT cap** ($30k cap, phasedown above $400k AGI) — `policyengine.org/us/research/ways-and-means-salt-cap` — +$937B/10yr revenue; top decile pays +$4,405/yr; 5.2% of residents see net reduction; Gini −0.4%.
- **SALTernative tool** — `policyengine.org/us/salternative` — interactive; uses CBO behavioral elasticities.

### State CTC
- **RI Gov McKee $325 CTC** — `policyengine.org/us/research/ri-governor-mckee-child-tax-credit` — $36.7M/yr, child poverty −2.1%, 29.2% benefit, TY 2027.
- **NYC $300 CTC (S2238)** — `policyengine.org/us/research/nyc-ctc-s2238` — $333.8M/yr, child poverty −2.0%, 32% benefit.
- **NY WFTC up to $1,822/child** — $660M year-1, $3.1B fully phased in, child poverty −4.0% year-1.
- **MN HF1938 (Walz)** — see `policyengine.org/us/research/mn-hf1938-walz`.

### UK
- Spring Statement analyses, Universal Credit reforms — see `policyengine.org/uk/research`.

## Refresh

The static index in `data/prior-scores.json` (if present in this skill's directory) is generated periodically. To refresh:

```bash
python3 scripts/refresh_prior_scores.py
```

For up-to-date scores not yet in the index, fall back to:
1. `site:policyengine.org/{country}/research <reform_keywords>`
2. `site:blog.policyengine.org <reform_keywords>`
3. WebFetch `policyengine.org/{country}/research` directly.

## Methodology caveats to surface

When citing a prior score, always note:
- **Year of analysis** (priors compound at ~3-4% per year for cost growth).
- **Dataset version** (CPS vs Enhanced CPS vs synthetic — affects magnitudes).
- **Static vs dynamic** (most PE scores are static; dynamic adds behavioral response).
- **Single-year vs 10-year window** (don't compare a 2023 single-year score directly to a 10-year run).

## Related skills

- `policyengine-research-lookup` — broader blog post discovery (not just scored reforms).
- `policyengine-microsimulation` — patterns for actually running the simulation.
- `policyengine-calibration-diagnostics` — when a new run mismatches a prior, this is where to look.
