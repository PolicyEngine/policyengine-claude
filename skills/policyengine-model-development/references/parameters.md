# Parameters

Parameters are dated policy values in YAML under `parameters/gov/...`. Federal under
`gov/{agency}/{program}/`, state under `gov/states/{st}/{agency}/{program}/`, contributed reforms
under `gov/contrib/...`. Before creating any, read 3–5 files from a similar program and match their
structure — this is the highest-leverage way to get it right.

## Required structure

```yaml
description: Illinois excludes this share of earnings from countable income under the Temporary Assistance for Needy Families program.
values:
  2024-01-01: 0.67

metadata:
  unit: /1            # currency-USD | /1 | year | month | bool | person
  period: year        # year | month | day | eternity
  label: Illinois TANF earned income disregard rate
  reference:
    - title: 305 ILCS 5/4-1.6         # full section path, no page number in title
      href: https://www.ilga.gov/legislation/ilcs/...   # PDFs: add #page=XX here
```

Missing any of `unit` / `period` / `label` / `reference` is a validation error.

- **`values` formatting:** underscores in big numbers (`3_000`), no trailing zeros (`0.2` not
  `0.20`), no decimals on integers (`2` not `2.0`).
- **Dates:** exact effective date from the source (`YYYY-MM-01`), never a placeholder like
  `2000-01-01`, and never a filing/publication date. The first entry is returned for *all* prior
  periods, so if a program starts later, add an explicit `2000-01-01: 0` before it — otherwise the
  value phantoms backward in time.
- **`period` matches the parameter's semantics.** A dimensionless rate is `period: year` even if it
  modifies a weekly quantity — the rate itself is time-invariant.
- **`label`:** `[State] [PROGRAM] [description]`, spell out the state, abbreviate the program, no
  trailing period. **`description`:** one sentence, spell the program out fully (no acronyms),
  `[State] [verb] ... under the [Full Program Name] program.`
- **`reference`:** prefer an online statute/reg (Cornell LII, public.law, `.gov` HTML with a
  section anchor) over a PDF; full subsection path in the title; verify PDF `#page=XX` is the file
  page, not the printed page.

## Federal / state separation for income taxes

State income taxes start from federal definitions — reference `adjusted_gross_income` /
`taxable_income` and apply state additions/subtractions. **Never** recreate income-source
parameters at the state level; that bypasses federal limits (e.g. the $3,000 capital-loss cap) and
overstates deductions.

## Bracket parameters

Brackets are a list of `threshold`/`amount` (or `threshold`/`rate`) pairs with a `type`.

**First threshold must be `-.inf` when negative inputs are valid** (AGI can be negative from
business losses). Starting a threshold at `0` silently drops negative-AGI filers into no bracket.
```yaml
brackets:
  - threshold: {2023-01-01: -.inf}   # covers negative AGI; not 0
    amount: {2023-01-01: 300}
  - threshold: {2023-01-01: 30_000}
    amount: {2023-01-01: 110}
```
Use `0` only where negatives are impossible (ages, counts, resource limits). (Verified: `-.inf`
first threshold in `parameters/gov/contrib/harris/rent_relief_act/.../applicable_percentage.yaml`.)

**`single_amount` brackets are "at or above" the threshold.** A value exactly at a threshold gets
that bracket. When a regulation says "**above** X" (X belongs to the *lower* bracket), shift the
threshold by `0.0001`, applied consistently to every threshold in the scale:
```yaml
# "0%: ≤100% FPL; 2%: above 100%–125%; ..."
brackets:
  - threshold: {2024-01-01: 0}       ; amount: {2024-01-01: 0}
  - threshold: {2024-01-01: 1.0001}  ; amount: {2024-01-01: 0.02}   # "above 100%"
  - threshold: {2024-01-01: 1.2501}  ; amount: {2024-01-01: 0.05}   # "above 125%"
```
No shift for "at or above X" / "X or more" (already PolicyEngine's default).

**Adding a new bracket in a later year: use `.inf` for the base year** so it's structurally present
but functionally unreachable until it takes effect. Adding it with only the new date breaks the
scale for prior years.
```yaml
# Ohio personal exemption: 3 brackets, plus a 4th phase-out cap added in 2025 (HB 96).
brackets:
  - threshold: {2021-01-01: 0}       ; amount: {2021-01-01: 2_400}
  - threshold: {2021-01-01: 40_001}  ; amount: {2021-01-01: 2_150}
  - threshold: {2021-01-01: 80_001}  ; amount: {2021-01-01: 1_900}
  - threshold:                                   # new cap bracket
      2021-01-01: .inf                           # pre-2025: unreachable → inert
      2025-01-01: 750_000
      2026-01-01: 500_000
    amount: {2021-01-01: 0}
```
The variable needs no change — `.calc()` still works. (Verified: `.inf` new bracket in
`parameters/gov/states/oh/tax/income/exemptions/personal/amount.yaml`; policyengine-us PR #7107.)

## Multi-dimensional rate tables: Enum breakdowns

A rate table over several dimensions (time × quality × age) is **one file per top dimension with a
`breakdown`**, not one file per combination. Three files, not 45:
```yaml
# rates/licensed_center.yaml
metadata:
  period: week
  unit: currency-USD
  label: Rhode Island CCAP licensed center weekly rates
  breakdown: [ri_ccap_time_category, ri_ccap_star_rating, ri_ccap_center_age_group]
  reference: [...]
FULL_TIME:
  STAR_1:
    INFANT: {2025-07-01: 334}
    TODDLER: {2025-07-01: 278}
  STAR_2:
    INFANT: {2025-07-01: 341}
```
The lookup collapses to `p.licensed_center[time_category][star_rating][center_age]`. When
dimensions differ across categories (centers have 4 age groups, family care 3; stars 1–5 vs steps
1–4), give each its own Enum variable. Rule of thumb: if the variable needs a helper function to do
the lookup, the parameter tree is too granular — restructure it.

## Bracket path syntax (Python / reform dicts)

The bracket index attaches to the scale node **directly** — there is no `.brackets` segment.

<!-- verify -->
```python
from policyengine_us import CountryTaxBenefitSystem

p = CountryTaxBenefitSystem().parameters
# ✅ correct: scale node, then [index], then .amount / .rate / .threshold
assert p.gov.irs.credits.ctc.amount.base[0].amount("2026-01-01") == 2200
# ❌ wrong: "...amount.base.brackets[0].amount" — no such path
```
Same shape for reform dicts: `"gov.states.ca.tax.income.rates.single[8].rate"`,
`"gov.hmrc.income_tax.rates.uk[0].threshold"`. To find a path: take the YAML file's directory path,
dot-joined, drop `.yaml`, then append `[N].rate`/`[N].threshold`. Verify in Python before relying
on it — a `ValueError` listing real children means you guessed a name.

## Three structural-transition toggles (parameter side)

The variable-side branches are in references/variables.md. Parameter side:

- **`flat_applies` (structure change).** Split the parameter into a folder with three files:
  `flat.yaml` (original value), `incremental.yaml` (new `type: marginal_rate` brackets), and
  `flat_applies.yaml` (`values: {2022-01-01: true, 2025-01-01: false}`). A single file can't hold
  both structures without retroactively applying the new one. (Verified:
  `parameters/gov/states/wa/tax/income/capital_gains/rate/flat_applies.yaml`.)
- **`in_effect` (provision gating).** One `in_effect.yaml` boolean (`false` before, `true` from the
  effective date) beside the provision's own sub-parameters (rate, threshold). Different from
  `flat_applies`: it toggles whether a logic block runs at all, not which access method is used.
- **`regional_in_effect` (regional ↔ statewide).** One boolean beside a `regional/` subtree
  (per-region amounts) **and** a flat `amount.yaml`; the boolean selects which is live.

Reform `in_effect` toggles are different — they default off with the `0000-01-01: false` sentinel;
see references/reforms.md.

## Don't create unnecessary parameters

Skip parameters for universal conversion factors (use `MONTHS_IN_YEAR`, `WEEKS_IN_YEAR`;
weeks-per-month is `WEEKS_IN_YEAR / MONTHS_IN_YEAR`), for thresholds with no simulation impact
("1 week old" minimum age), and for anything derivable from existing parameters (FPL tables).
