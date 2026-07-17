---
name: policyengine-model-development
description: |
  Load when editing a PolicyEngine country model repo (policyengine-us, policyengine-uk,
  policyengine-canada) — adding or changing variables, parameters, YAML tests, or contributed
  reforms. This is the engineering layer (how formulas, parameter YAML, and tests are written),
  distinct from running analysis.
  Triggers: add a variable, add a parameter, write a formula, defined_for, adds/subtracts,
  value_type, definition_period, entity, SPMUnit, TaxUnit, vectorize, where/select, period vs
  period.this_year, monthly_age, YAML test, absolute_error_margin, contrib reform, in_effect,
  create_x_reform, neutralize_variable, modify_parameters, changelog.d, StateCode, TANF/SNAP
  encoding, bracket parameter, -.inf, single_amount.
  NOT for: household calculations, microsimulation, reform scoring, or distributional analysis
  (use the policyengine skill); calling the REST API (use policyengine-api).
metadata:
  category: model-development
---

# PolicyEngine model development

Engineering patterns for the country-model repos — `policyengine-us`, `policyengine-uk`,
`policyengine-canada`. These packages encode enacted law (and proposed reforms) as **variables**
(Python formulas) driven by **parameters** (YAML), validated by **YAML tests**, all running on
the vectorized policyengine-core engine.

This skill is the *how-to-write-it* layer. To run calculations or score reforms, use the
`policyengine` skill instead. Verified against policyengine-us 1.764.x / policyengine-core 3.30.x
(2026-07).

## Mental model

- **Parameters** are a YAML tree under `parameters/gov/...`. Each leaf is a dated value (or a
  bracket/breakdown table) with required metadata. Accessed in formulas as
  `parameters(period).gov.agency.program.thing`. Federal under `gov/{agency}/`, state under
  `gov/states/{st}/`, contributed reforms under `gov/contrib/`.
- **Variables** live one-per-file under `variables/gov/...`, each a `Variable` subclass with
  `value_type` / `entity` / `definition_period` / metadata and either a `formula` **or** an
  `adds`/`subtracts` list (never both). Formulas run vectorized over the whole population.
- **Entities** nest: `Person` → `TaxUnit` / `SPMUnit` / `Family` / `MaritalUnit` / `Household`
  (US); `Person` → `BenUnit` / `Household` (UK). Aggregation across entity levels is automatic
  via `adds`/`add()`.
- **Tests** are YAML files mirroring the variable path under `tests/policy/baseline/...`,
  asserting outputs for a described household at a period.

## The absolute musts

1. **Never hardcode a numeric policy value in a formula.** Every threshold, rate, and amount
   comes from a parameter (`p.income_limit`, not `2000`). Bare `0`/`1`/`-1` and `MONTHS_IN_YEAR`
   are the only acceptable literals. See references/variables.md.
2. **Vectorize everything.** No `if`/`elif`/`else` or `and`/`or`/`not` on entity arrays — use
   `where` / `select` / `&` / `|` / `~`. Python `if` is allowed **only** on scalar parameters
   (`if p.flat_applies:`). See references/vectorization.md.
3. **`adds`/`subtracts` XOR `formula` — never both** in one variable. A pure sum uses the `adds`
   attribute with no formula; anything else uses a formula (with `add()` inside). See
   references/periods-and-aggregation.md.
4. **Get the period right.** From a MONTH formula, YEAR flow variables (income) use `period`
   (auto ÷12); YEAR stocks/counts/ages/booleans use `period.this_year` (no division). See
   references/periods-and-aggregation.md.
5. **`uv run` for everything.** `uv run pytest ...`, `uv run policyengine-core test ...`. Never
   bare `pytest`. Format with `uv run ruff` (line length **88**, the default — not 79). There is
   **no `black`** in this toolchain.
6. **Changelog = a towncrier fragment**, never an edit to `CHANGELOG.md`. Write
   `changelog.d/{branch-name}.{added|fixed|changed}.md` with one line.
7. **Branch from the PolicyEngine upstream repo, not a fork.** Encoding work targets
   `origin/main` of `PolicyEngine/policyengine-us` (etc.).

## Routing

| You are working on… | Read |
|---|---|
| A variable: `value_type`/`entity`/`defined_for`, `adds` vs formula, naming, gotchas (age float, `monthly_age`, `is_ssi_eligible`), federal aggregators | references/variables.md |
| A parameter: YAML structure, brackets (`-.inf`, `.inf`, `single_amount`), breakdowns, metadata, path syntax | references/parameters.md |
| Periods (`period` vs `period.this_year`, ÷12) or aggregation (`adds`/`add()`, `.any()`) | references/periods-and-aggregation.md |
| Vectorization: `where`/`select`, `max_(A-B,0)` floors, divide-by-zero, phantom values | references/vectorization.md |
| YAML tests: structure, period restrictions, error margins, enums, the CLI | references/tests.md |
| A contributed reform under `contrib/` / `reforms/`: factory, `in_effect`, registration | references/reforms.md |
| Code style, framework constants, folder layout, review response | references/style.md |

## Setup

```bash
cd policyengine-us            # or -uk / -canada; branch off origin/main
uv pip install -e ".[dev]"    # editable install with dev deps
uv run pytest policyengine_us/tests/... -q
uv run policyengine-core test <yaml_path> -c policyengine_us   # runs a YAML test file
uv run ruff format . && uv run ruff check .
```

Discover names against the live tree instead of guessing — grep the `variables/` and
`parameters/` directories, or introspect the parameter tree in Python (see
references/parameters.md). Paths and parameter names change; the repo is the source of truth.
