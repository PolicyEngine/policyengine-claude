# Style, layout, and review

## Toolchain

- **`uv run` for everything** — `uv run pytest`, `uv run policyengine-core test`,
  `uv run ruff format .`, `uv run ruff check .`. Never bare `pytest`.
- **Ruff, line length 88** (the default — not 79). There is **no `black`** in this toolchain;
  don't add or run it.
- **Changelog:** a towncrier fragment `changelog.d/{branch}.{added|fixed|changed}.md` with one line.
  Never edit `CHANGELOG.md` directly. `.added` for new programs/reforms, `.fixed` for fixes.

## Formula style

Write the shortest formula that reads clearly. Cut single-use intermediates for simple values,
return directly, and combine boolean logic:
```python
# ✅
def formula(person, period, parameters):
    p = parameters(period).gov.program.eligibility
    age = person("age", period.this_year)
    assets = person("assets", period.this_year)
    monthly_income = person("employment_income", period)
    return (
        (age >= p.age_min) & (age <= p.age_max)
        & (assets <= p.asset_limit)
        & (monthly_income <= p.income_threshold)
    )
```
But **do name** a complex expression rather than inlining it in `where()`/`max_()`, and keep an
intermediate that's used more than once. Rule: more than a simple variable or parameter access →
give it a name.
```python
# ❌ inlined and unreadable          # ✅ named
standard_payment = max_(maximum_benefit - countable_income, 0)
return where(above_trigger, reduced_payment, standard_payment)
```
Let variable names carry the meaning — **minimal comments**. No comments restating what the code
does; a one-line `# NOTE:` about a non-obvious implementation decision is fine.

## Framework constants

Use `MONTHS_IN_YEAR` (12) and `WEEKS_IN_YEAR` (52) instead of literals or custom parameters;
weeks-per-month is `WEEKS_IN_YEAR / MONTHS_IN_YEAR`. **`WEEKS_IN_YEAR` is the integer 52**, so
`WEEKS_IN_YEAR * 7` gives 364, not 365 — use the literal `365` for days-per-year. When a regulation
cites an exact factor (e.g. "multiply by 4.3"), use that value even though `WEEKS_IN_YEAR /
MONTHS_IN_YEAR ≈ 4.333`; the difference matters at benefit boundaries.

Drop a `min_`/`max_` that can never bind: `max_(payment_standard - countable_income, 0)` already
can't exceed `payment_standard`, so wrapping it in `min_(..., payment_standard)` is dead code. Keep
`min_` only where the bound really binds (capping a subsidy at actual expenses).

## Folder layout

Variables one-per-file; the final benefit variable (`{prefix}.py`) sits at the program root. Scale
subfolders to program size — don't create a folder for a single file:
```
{program}/
├── {prefix}.py                      # final benefit at root
├── eligibility/{prefix}_eligible.py, {prefix}_income_eligible.py, ...
├── income/{prefix}_countable_income.py, ...
└── deductions/{prefix}_work_expense_deduction.py, ...
```
Small (~5 files) stays flat; medium (6–15) gets light `eligibility/` + `income/`; large (>15) gets
the full tree. Parameter folders group **by function** — an `eligibility/` folder holds eligibility
rules, not rate-table dimension boundaries (those go in `age_groups/`). Tests mirror the variable
path, with the unprefixed `integration.yaml` at the program root.

## Review

Triage findings by severity and don't stop the review-fix loop until **zero critical** issues
remain (even if lower tiers are clean):

- **Critical (crashes / wrong results):** non-vectorized code (`if`/`and` on arrays), hardcoded
  policy values, parameters with no primary-source reference.
- **Major (accuracy / maintainability):** test-quality gaps (missing separators, no positive case,
  wrong period), calculation-order errors, passive-voice descriptions.
- **Minor:** organization, one-variable-per-file, `adds` where a manual sum was written.

When reviewing a state variable that mirrors another state, check **why** it exists: read the
formula for state-specific logic and state-parameter access. A variable whose formula is just
`return entity("federal_variable", period)` is a wrapper — request its deletion and use the federal
variable directly. Trust domain-specific correctness over superficial simplicity: if an
implementer added a correct pattern (e.g. an `in_effect` boolean), don't push a "simpler" version
that reintroduces an anti-pattern. Renaming across the codebase is high-risk — require passing
microsim tests and grep for string references (reforms, API, parameter files) before approving.
