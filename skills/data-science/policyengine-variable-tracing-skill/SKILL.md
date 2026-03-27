---
name: policyengine-variable-tracing
description: |
  Tracing PolicyEngine variable definitions, formulas, and data lineage in country model packages.
  Use this skill when working in policyengine-us-data or policyengine-uk-data to understand where
  variable values come from, how to find variable source code, read formulas, trace dependencies,
  and map H5 dataset values back to their origins.
  Triggers: "trace variable", "find variable", "where is this variable defined", "variable formula",
  "why does this value", "data lineage", "H5 value", "variable source", "navigate policyengine-us",
  "navigate policyengine-uk", "variable dependency", "how is this calculated", "input variable",
  "formula variable", "adds variable", "entity level", "cross-entity"
---

# PolicyEngine Variable Tracing

Practical guide for finding, reading, and tracing variable definitions in PolicyEngine country
model packages (policyengine-us, policyengine-uk) when working on data pipelines.

**Before using this skill:** Load the relevant country domain skill (`policyengine-us` or
`policyengine-uk`) for country-specific variable semantics, entity structures, and program details.

## Tracing workflow and narration

When tracing a variable, **surface findings progressively** — do not accumulate all results
silently and report at the end. After each meaningful discovery, output a short inline summary
before continuing. This keeps the user informed and lets them redirect if needed.

After finding the variable definition, immediately output a summary block like:

```
**Variable: `snap_reported`**
- Entity: SPMUnit
- Type: Input (no formula)
- Period: YEAR
- Legal reference: [URL if present]
- Next: trace back into the data pipeline
```

After identifying the pipeline source, output:

```
**Pipeline source: `snap_reported`**
- Origin: Direct from CPS survey — column `SPM_SNAPSUB`
- Calibration target: yes — `snap` targeted at state + national level (USDA FNS data)
- Next: check for known nuances or pitfalls
```

Use your judgment on granularity — one summary per logical step is enough. The goal is that
the user can follow the reasoning in real time without waiting for a final report.

## 1. Finding a Variable Definition

Every variable is a Python class in a `.py` file. The class name IS the variable name.

### Search strategies (fastest first)

**Grep for the class definition:**
```bash
# In the country model repo
grep -r "class snap" policyengine_us/variables/ --include="*.py" -l
```

**Infer from directory structure:**
```
policyengine_{country}/variables/
├── input/          # Input variables (no formula, data-driven)
├── gov/            # Government programs
│   ├── {agency}/   # Federal agencies (irs, usda, ssa, hhs, etc.)
│   └── states/     # State-specific (us) or regions (uk)
│       └── {code}/ # e.g., ca/, ny/, scotland/
├── household/      # Household-level aggregations
│   └── income/     # Income variables by entity level
└── contrib/        # Contributed/experimental programs
```

Variable names often encode their location:
- `snap_*` -> `gov/usda/snap/`
- `ca_*` -> `gov/states/ca/`
- `income_tax*` -> `gov/irs/` or `gov/hmrc/`
- `is_*` or `has_*` -> boolean eligibility, search within the program directory
- `*_reported` -> typically input variables

**Use the tax-benefit system at runtime:**
```python
from policyengine_us import CountryTaxBenefitSystem
system = CountryTaxBenefitSystem()
var = system.variables["snap_normal_allotment"]
print(var.entity.key)        # Which entity (person, household, etc.)
print(var.value_type)        # float, int, bool, Enum
print(var.definition_period) # YEAR, MONTH, ETERNITY
print(var.reference)         # List of legal citation URLs
```

Note: there is no `source_file_path` attribute on variable objects. To find the source
file, use grep — the class name always matches the variable name.

## 2. Variable Types

Look at the class body to determine the type. This matters for data pipelines because it tells
you whether the variable's value comes from data or from computation.

### Input variables (data-driven, no formula)

```python
class employment_income_before_lsr(Variable):
    value_type = float
    entity = Person
    label = "employment income before labor supply responses"
    unit = USD
    definition_period = YEAR
    uprating = "calibration.gov.irs.soi.employment_income"
```

**How to identify:** No `formula` method, no `adds`/`subtracts`. Often has `uprating`.
**Data pipeline meaning:** This variable's value comes directly from the dataset (H5 file).
If missing from the dataset, it defaults to the `value_type` zero value (0.0, 0, False).

### Aggregating variables (adds/subtracts)

```python
class household_net_income(Variable):
    value_type = float
    entity = Household
    unit = USD
    definition_period = YEAR
    adds = [
        "household_market_income",
        "household_benefits",
        "household_refundable_tax_credits",
    ]
    subtracts = ["household_tax_before_refundable_credits"]
```

**How to identify:** Has `adds` and/or `subtracts` lists instead of a `formula`.
**What it means:** The framework auto-generates `formula = sum(adds) - sum(subtracts)`.
**Tracing:** Follow each variable name in the lists to find sub-components. The `adds` field
can also be a string referencing a parameter path (e.g., `"gov.household.market_income_sources"`)
which resolves to a list of variable names defined in parameter YAML.

### Calculated variables (explicit formula)

```python
class snap_emergency_allotment(Variable):
    value_type = float
    entity = SPMUnit
    definition_period = MONTH
    unit = USD

    def formula(spm_unit, period, parameters):
        p = parameters(period).gov.usda.snap.emergency_allotment
        eligible = spm_unit("is_snap_eligible", period)
        max_allotment = spm_unit("snap_max_allotment", period)
        state = spm_unit.household("state_code", period)
        ...
```

**How to identify:** Has a `def formula(entity, period, parameters)` method.
**Tracing:** Read the formula body. Every `entity("variable_name", period)` call is a
dependency. Every `parameters(period).path.to.param` is a parameter lookup.

### Conditional variables (defined_for)

```python
class ca_care(Variable):
    entity = Household
    defined_for = StateCode.CA
    ...
```

**How to identify:** Has a `defined_for` attribute.
**What it means:** The formula only runs when the condition is met. For all other cases,
the variable returns its zero value. `defined_for` can be a state code enum or a string
referencing a boolean variable name.

## 3. Entity Level

Every variable belongs to exactly one entity. The entity determines which records in the
dataset the variable applies to and how it interacts with other variables.

**Always check the entity:** Read `entity = ...` on the variable class. Do not assume —
the same program may have variables at different entity levels.

### Discovering entities

Each country model defines its entities in an `entities.py` file:
```python
# Check what entities exist
grep -n "class.*Entity" policyengine_{country}/entities.py
```

### Entity hierarchy and cross-references

Entities form a containment hierarchy. The exact hierarchy varies by country — inspect
`entities.py` and the `containing_entities` attribute on each entity definition.

**Upward reference (child to containing entity):**
```python
# A variable on SPMUnit accessing its containing Household
state = spm_unit.household("state_code", period)
```

**Downward reference (parent to contained members):**
```python
# A variable on SPMUnit accessing Person members
adult_count = spm_unit.sum(spm_unit.members("is_adult", period))
```

**Key patterns in formulas:**
- `entity("var", period)` — same-entity variable reference
- `entity.parent_entity("var", period)` — look up to containing entity
- `entity.members("var", period)` — look down to member-level, returns array
- `entity.sum(...)`, `entity.max(...)`, `entity.any(...)` — aggregate members
- `entity.nb_persons()` — count of members

**Why this matters for data pipelines:** When you see a variable value in an H5 file, you
must know its entity to understand which rows it maps to. A `household_weight` applies to
household-level rows, not person-level rows. Cross-entity aggregations (e.g., summing
person-level income to household level) happen at simulation time, not in the H5 file.

## 4. Reading Formulas

### The formula signature

```python
def formula(entity, period, parameters):
```

- `entity` — the entity instance (e.g., `person`, `tax_unit`). Used to reference other variables.
- `period` — the time period being calculated. Passed through to dependencies.
- `parameters` — the parameter tree. Access with `parameters(period).path.to.param`.

### Common formula patterns

**Parameter lookups:**
```python
p = parameters(period).gov.usda.snap
rate = p.some_rate                    # Scalar parameter
threshold = p.threshold[filing_status] # Keyed by enum
```

Parameter paths match the YAML file hierarchy in `policyengine_{country}/parameters/`.
File `parameters/gov/usda/snap/some_rate.yaml` -> `parameters(period).gov.usda.snap.some_rate`.

**Vectorized operations (all PolicyEngine formulas operate on arrays, never scalars):**
```python
where(condition, value_if_true, value_if_false)  # Vectorized if/else
select([cond1, cond2, ...], [val1, val2, ...], default=0)  # Multi-branch
max_(a, b)   # Element-wise max (not Python's max())
min_(a, b)   # Element-wise min
not_(array)  # Boolean negation
```

**The `add()` helper inside formulas:**
```python
# Sums multiple variables on the same entity
total = add(tax_unit, period, ["var_a", "var_b", "var_c"])
```

### Dated formulas

Some variables have multiple formula versions for different time periods:
```python
class some_variable(Variable):
    def formula_2020(person, period, parameters):
        ...  # Applies for 2020 onwards

    def formula_2017(person, period, parameters):
        ...  # Applies for 2017-2019
```

The engine picks the most recent formula that does not exceed the requested period.

## 5. Dependency Tracing

To trace why a variable has a specific value, walk the dependency tree.

### Manual trace (reading code)

1. Find the variable's `.py` file (Section 1)
2. Check the type (Section 2):
   - **Input**: value comes from dataset. Stop — trace into the data pipeline.
   - **Adds/subtracts**: follow each listed variable recursively.
   - **Formula**: read the body, note every `entity("var_name", period)` call.
3. For each dependency, repeat from step 1.
4. The leaves of the tree are always input variables or parameters.

### Runtime trace (using the simulation engine)

```python
from policyengine_us import Microsimulation

sim = Microsimulation()
# or with a specific dataset:
# sim = Microsimulation(dataset=path_to_h5)

sim.trace = True
sim.calculate("snap_normal_allotment", 2024)

# Print the dependency tree
sim.tracer.print_computation_log()
```

This shows every variable computed, its value, and its dependencies — the definitive
way to verify how a value was derived.

### Verifying a formula against legal sources

Every variable should have a `reference` field linking to the authoritative legal text.
When tracing, compare the formula logic against the cited law to confirm correctness:
```python
var = system.variables["snap_normal_allotment"]
print(var.reference)  # URL to legal citation
```

The variable name itself often encodes what legal concept it represents — use it as a
starting point, but read the cited legal text directly to verify the formula captures the
correct conditions, thresholds, and scope. If you want to read the full implementation,
find the source file using grep (the class name always matches the variable name):
```bash
grep -r "class snap_normal_allotment" policyengine_us/variables/ --include="*.py" -l
```

## 6. Data Lineage: From H5 Value to Source

When you see a variable's value in an H5 file produced by a data pipeline (e.g.,
policyengine-us-data or policyengine-uk-data), the value came from one of these sources.

### Source determination workflow

1. **Is the variable an input variable in the country model?**
   - Check: no `formula`, no `adds`/`subtracts` in its class definition.
   - If yes: the value was placed into the H5 by the data pipeline. Continue to step 2.
   - If no: it should NOT be in the H5 — the simulation engine recomputes it at runtime.
     (Data pipelines drop formula variables before writing H5 files.)

2. **Where did the data pipeline get the input value?**

   Search the pipeline codebase for the variable name as a starting point:
   ```bash
   grep -rn "\"variable_name\"" policyengine_{country}_data/ --include="*.py"
   ```

   Then trace through the following stages in order:

   **Stage A — Direct from survey microdata:**
   Check the survey processing file (e.g., `cps.py`, `frs.py`) for a direct column mapping.
   These are the most transparent: a raw survey column is renamed to a PolicyEngine variable.
   ```bash
   grep -n "variable_name" policyengine_{country}_data/datasets/cps/cps.py
   ```

   **Stage B — Imputed from a primary or secondary source:**
   If not directly from the survey, it may be statistically imputed. Check:
   - `IMPUTED_VARIABLES` list (controls what the extended dataset imputes)
   - `FINANCIAL_SUBSET` list (controls what is extracted from tax records like PUF)
   - Source imputation files (e.g., `source_impute.py`) for variables drawn from
     alternative surveys (ACS, SIPP, SCF for US)
   Imputed values are model predictions — their accuracy depends on the training data
   and predictors used. Check which predictors the model uses; variables not in the
   predictor set will produce state- or demographic-blind estimates.

   **Stage C — Stochastic takeup assignment:**
   For boolean participation variables (`takes_up_*`), values are drawn from Bernoulli
   distributions using program-specific administrative takeup rates. These are not
   deterministic across pipeline runs.

   **Stage D — Check calibration targets:**
   Even after the microdata value is set (stages A–C), the calibration step adjusts
   household weights to match administrative totals. If the variable (or a formula
   variable that depends on it) is a calibration target, the weighted aggregate will
   be forced toward the target — but the individual microdata values are unchanged.

   Check `target_config.yaml` for the variable name:
   ```bash
   grep -n "variable_name" policyengine_{country}_data/policyengine_{country}_data/calibration/target_config.yaml
   ```
   If it appears, note the `geo_level` (national, state, district) — this tells you
   the granularity at which the weighted total is constrained. A variable calibrated
   at state level will have correct state-level weighted sums, but individual record
   values may still be noisy or biased.

   Also note the **source of the administrative target itself**. Check the ETL script
   that populates the target (e.g., `db/etl_snap.py`, `db/etl_national_targets.py`):
   - Targets sourced from **USDA, CMS, SSA** cover the full population regardless of
     tax filing status.
   - Targets sourced from **IRS SOI** (Statistics of Income) cover only tax filers.
     Variables calibrated against IRS SOI targets — such as `employment_income`,
     `adjusted_gross_income`, or `capital_gains` — will have correctly weighted totals
     only when aggregated over the filer population. Comparing an unfiltered population
     aggregate against an IRS SOI target is a common source of apparent discrepancy: the
     target was never meant to represent everyone, only those who filed a return.

   For deeper inspection, the calibration targets are also stored in the policy database:
   ```bash
   # Check the SQLite target database
   sqlite3 policyengine_{country}_data/db/policy_data.db \
     "SELECT * FROM targets WHERE variable = 'variable_name' LIMIT 10;"
   ```

3. **Reconcile microdata vs. weighted totals:**
   If the individual H5 values look reasonable but weighted aggregates are off (or
   vice versa), the distinction between stages A–C (microdata) and stage D (weights)
   is the key. Calibration fixes the aggregate but cannot correct a systematically
   wrong imputation at the record level.

See `examples/snap-trace.md` for a walkthrough of this workflow
applied to the `snap` variable.

### Important: formula variables are NOT stored

Data pipelines store only leaf input variables. Variables with formulas or `adds`/`subtracts`
are recomputed by the simulation engine. If you find a formula variable in an H5 file,
something unexpected happened — investigate the pipeline code.

The pipeline typically has an explicit step that drops formula variables:
```python
# Example pattern — look for this in the data pipeline
formula_vars = [v for v in system.variables if system.variables[v].formulas]
# These get excluded from the H5 output
```

## 7. Quick Reference

### Checklist: tracing a variable end-to-end

- [ ] Find the variable class in the country model (`grep -r "class {name}" ...`)
- [ ] Note the **entity** (`entity = ...`) — which dataset rows does this apply to?
- [ ] Note the **type**: input (no formula) / adds / subtracts / formula / defined_for
- [ ] Note the **definition_period**: YEAR, MONTH, or ETERNITY
- [ ] If input: search the data pipeline for how the value enters the H5
- [ ] If formula: read dependencies, trace each one recursively
- [ ] If adds/subtracts: follow each listed variable
- [ ] Check `reference` field for the authoritative legal source
- [ ] Use `sim.trace = True` to verify at runtime if needed

### Common pitfalls

- **Wrong entity assumption**: A variable named `household_*` might actually be defined on
  `SPMUnit` or `TaxUnit`. Always check `entity = ...`.
- **Missing from H5**: If an input variable has no value in the H5, it defaults to zero.
  This is silent — the simulation won't error, it just uses 0.
- **Stale country model version**: The data pipeline's pinned version of the country model
  may not include a recently added variable. Check version constraints in `pyproject.toml`.
- **`adds` referencing a parameter path**: When `adds` is a string like
  `"gov.household.market_income_sources"`, it resolves to a list defined in a parameter
  YAML file, not a single variable. Read the parameter file to find the actual components.
- **For US variables IRS SOI calibration targets are filer-only**: Variables whose administrative targets
  come from IRS Statistics of Income data (e.g., `employment_income`, `adjusted_gross_income`,
  capital gains variables) are calibrated against totals that only cover tax filers. If you
  aggregate these variables over the full population and compare against the target, the numbers
  will not match — not because the data is wrong, but because the target was never meant to
  represent non-filers. Always check the ETL source (`db/etl_*.py`) to know what population
  a calibration target represents before drawing conclusions from aggregate comparisons.
- **Variable definitions may not perfectly match legal reality**: A variable's name, label,
  or formula is an implementation choice — it reflects the developer's interpretation at
  the time of writing. The legal code may have conditions, exclusions, or edge cases that
  aren't captured, or the variable may aggregate concepts that the law treats separately.
  Before assuming a variable represents exactly what its name suggests, read its `reference`
  citation and verify the formula against the actual legal text. Pay attention to what
  conditions the formula applies (via `defined_for`, parameter switches, or `where()` guards)
  and what it silently omits. When the data pipeline uses a variable as a calibration target
  or imputation output, these assumptions propagate into the dataset.

## Related Skills

- **policyengine-us** / **policyengine-uk** — Country-specific variable semantics and programs
- **policyengine-variable-patterns** — How to *write* new variables (this skill is for *reading* them)
- **policyengine-core** — Simulation engine internals (formula resolution, period handling)
- **policyengine-us-data** / **policyengine-uk-data** — Data pipeline specifics
- **policyengine-simulation-mechanics** — Running simulations and inspecting output