---
name: policyengine-prior-scores
description: |
  Curated anchor list of PolicyEngine's previously-published scored reforms, plus the map of the
  real prior-scores infrastructure in this repo (presets, the scorekeepers registry, the
  /prior-scores command, and the prior-scores-finder agent). Use to find a benchmark magnitude to
  anchor a new analysis (Stage 3 / Stage 5 of /analyze-policy) or to cite PE's prior work on a
  similar reform.
  Triggers: "prior PE score", "PolicyEngine has scored", "what did PE find", "PE benchmark",
  "anchor reform", "comparable reform", "EITC expansion scored", "CTC expansion scored", "SALT
  cap analysis", "state CTC analysis", "ARPA reform impact", "American Family Act score",
  "published_scores", "preset reform", "scorekeepers".
  NOT for: broader blog discovery (see policyengine-research-lookup) or diagnosing why a run
  mismatches a prior (see policyengine-calibration-diagnostics).
metadata:
  category: analysis
---

# PolicyEngine prior scores

Finding a prior score to anchor a new analysis has two parts: a **curated anchor list** of
notable PE reforms (below, with URLs) and the **real infrastructure** in this repo that
enumerates presets, external scorekeepers, and local archived runs. Earlier versions of this
skill described a `data/prior-scores.json` file with `get_priors_by_program()` query functions —
those never existed. The sections below point only at things that are actually on disk or live.

## When to use

- `/analyze-policy` Stage 3 (find prior scores) and Stage 5 (compare the microsim to them).
- The `/prior-scores` command (external-benchmark research without running the microsim).
- The `prior-scores-finder` agent's Tier-1 lookup.
- Writing a research post and citing PE's prior work on a similar reform.

## Real infrastructure in this repo

### Presets — named reform-dicts with published scores

`presets/reforms/*.yaml` and `presets/baselines/*.yaml` are callable-by-name reform/baseline
dicts. A preset may carry a `published_scores` block recording what external sources scored that
exact shape — which is what makes external corroboration turn-key.

```bash
python3 scripts/presets.py list                 # all presets
python3 scripts/presets.py list --category reform --country us
python3 scripts/presets.py show arpa-ctc-restoration   # prints the reform_dict + published_scores
```

```python
from scripts.presets import load_preset
preset = load_preset("arpa-ctc-restoration")
preset["reform_dict"]        # ready to pass as a reform
preset["published_scores"]   # [{source: JCT, ten_year_billion: 1100, ...}, ...]
```

Presets on disk today (verify with `python3 scripts/presets.py list` — `load_preset` raises
on names that don't exist): reforms `arpa-ctc-restoration`, `obbba-salt-bump`; baseline
`tcja-extension`. A `pre-obbba` baseline is wanted but not yet authored. Add a preset by copying
a nearby file and, if any external source scored the shape, filling in `published_scores` — see
`presets/README.md`.

### Scorekeepers — the external-benchmark registry

`presets/scorekeepers.yaml` enumerates the official fiscal offices (Tier 2) and think-tanks
(Tier 3) to consult per jurisdiction and domain — so the search casts a wide, non-US-only net
without hardcoding sources into agents. Add a scorekeeper by appending to the YAML; no code
change.

```bash
python3 scripts/scorekeepers.py list --country us --tier 2   # JCT, CBO, OTA, SSA-OCACT
python3 scripts/scorekeepers.py list --country us --tier 3   # CRFB, TPC, Tax Foundation, CBPP, ITEP, ...
python3 scripts/scorekeepers.py list --country uk --tier 3   # IFS, Resolution Foundation, IPPR, NIESR, ...
python3 scripts/scorekeepers.py list --country ca            # PBO, DoF-Canada, CD Howe, IRPP, ...
```

```python
from scripts.scorekeepers import list_scorekeepers
tier_2 = list_scorekeepers(country="us", tier=2)
```

Each entry has `search_hints` (e.g. `site:crfb.org`) for constructing WebSearch queries, plus
`domains` and `caveats`.

### Command and agent

- **`/prior-scores`** (`targets/claude/commands/prior-scores.md`) — standalone external-benchmark
  research: loads the scorekeepers registry filtered by country/tier/domain, also consults the
  local `analyses/` archive (Tier 0, via `scripts/analyses_kb.py`) and PE published research
  (Tier 1, this skill), and returns a ranked benchmark cluster. It does NOT run the microsim.
- **`prior-scores-finder`** (`targets/claude/agents/prior-scores-finder.md`) — the agent behind
  Stage 3. It runs BLIND to the current run's own microsim result (pre-registration), records
  each source **with its framing** at registration time, and requires all tiers: Tier 0 (local
  archive), Tier 1 (PE published — this skill), Tier 2 (official), Tier 3 (think-tanks). A PE
  prior does not excuse skipping the external tiers.

## Curated anchor reforms

Notable PE-published scores, kept as quick anchors. Verify the live number before quoting — these
are pointers, not a maintained database. Confirm current figures with the search recipe below.

### Federal CTC
- **Restoration of the ARPA expanded CTC** —
  `policyengine.org/us/research/restoration-of-the-american-rescue-plan-acts-expanded-child-tax-credit`
  — ~$100.2B/yr (2023), child poverty −37%, Gini −1.9%. ARPA parameters ($3,600 / $3,000, fully
  refundable). Preset: `arpa-ctc-restoration`.
- **2025 American Family Act** — `policyengine.org/us/research/american-family-act-2025` —
  ~$2.5T/10yr, child poverty −25.2%, deep child poverty −29.9%. Larger amounts + baby bonus +
  ITIN eligibility.

### Federal EITC
- **Restoring the ARPA EITC** — single-year ~$9.8B. Childless-adult expansion (max credit ~tripled,
  age limits widened).
- **NY Working Families Tax Credit** (state, EITC-adjacent) — ~$9.1B over 5 years; child poverty
  −4.0% rising to −16.8% by year 4.

### SALT cap
- **Ways and Means SALT cap** ($30k cap, phasedown above $400k AGI) —
  `policyengine.org/us/research/ways-and-means-salt-cap` — +$937B/10yr revenue; top decile
  +$4,405/yr; 5.2% of residents net-reduced; Gini −0.4%.
- **SALTernative tool** — `policyengine.org/us/salternative` — interactive; CBO behavioral
  elasticities.

### State CTC
- **RI Gov McKee $325 CTC** — `policyengine.org/us/research/ri-governor-mckee-child-tax-credit` —
  ~$36.7M/yr, child poverty −2.1%, TY 2027.
- **NYC $300 CTC (S2238)** — `policyengine.org/us/research/nyc-ctc-s2238` — ~$333.8M/yr, child
  poverty −2.0%.
- **NY WFTC up to $1,822/child** — ~$660M year 1, $3.1B fully phased in, child poverty −4.0%
  year 1.
- **MN HF1938 (Walz)** — `policyengine.org/us/research/mn-hf1938-walz`.

### UK
- Spring/Autumn Statement analyses, Universal Credit reforms — `policyengine.org/uk/research`.

## Comparability caveats (surface every time)

A magnitude without its frame is not a benchmark. Whenever you cite a prior score, state:

- **Baseline frame** — what the estimate is measured against (prior-law schedule, current law,
  year-over-year vs an already-scheduled rate, repeal counterfactual). Two scores of "the same"
  reform against different baselines are not comparable. This is the most commonly missed caveat.
- **Horizon** — single-year (which year?), budget-window (which window?), or full-implementation.
  Never compare a single-year score directly to a 10-year run.
- **Year of analysis** — costs drift roughly 3-4%/yr from uprating and caseload growth; an
  older single-year score needs extrapolation before it brackets a current run.
- **Dataset vintage** — magnitudes shift across microdata versions. Older PolicyEngine scores
  predate Populace and were computed on earlier enhanced-survey datasets; do not treat their
  absolute levels as directly comparable to a current Populace run (see `policyengine-data`).
- **Static vs dynamic** — most PE scores are static; a dynamic score adds behavioral response.
- **Scope** — which provisions the estimate includes/excludes.

If any of these cannot be determined from the source, record it as `unknown` rather than guessing
— the comparator treats unknown-frame sources as incommensurable.

## Live search recipe

For scores not in the anchor list or presets, search directly:

1. `site:policyengine.org/{country}/research <reform_keywords>` — the primary index.
2. `site:policyengine.org <reform_keywords>` — catches dedicated calculators/tools.
3. `WebFetch policyengine.org/{country}/research` — browse the research index directly.
4. `blog.policyengine.org <reform_keywords>` — narrative posts (Medium redirects may need a
   fallback fetch).

Extract for each hit: reform name + URL, year, single-year and/or 10-year cost, distributional
impact (Gini, top-decile share), poverty impact (overall + child), and the methodology frame from
the caveats above.

## Related skills

- `policyengine-research-lookup` — broader blog/post discovery beyond scored reforms.
- `policyengine` — actually running the microsim to compare against these anchors.
- `policyengine-calibration-diagnostics` — when a new run mismatches a prior, diagnose why.
