# Vectorization

Formulas run over the whole population at once, so entity reads are NumPy arrays. `if`/`elif`/`else`
and `and`/`or`/`not` on array data raise "truth value of an array is ambiguous" — branch with
`where`/`select` and combine with `&`/`|`/`~`. Python `if` is fine on **scalar parameters** only
(`if p.flat_applies:`; see references/variables.md). This page covers the PolicyEngine-specific
helpers and the non-obvious floor/division/phantom traps — assume the generic array-vs-scalar rule.

## The helpers come from `model_api`

`where`, `select`, `max_`, `min_`, `clip`, and `add` are exported from
`policyengine_core.model_api` (re-exported by `policyengine_us.model_api` / `_uk` / `_canada`). Use
`max_`/`min_` — the trailing underscore versions are element-wise over arrays; Python's builtin
`max`/`min` mishandle array dtypes.

<!-- verify -->
```python
from policyengine_us.model_api import where, select, max_, min_, add, clip, MONTHS_IN_YEAR, WEEKS_IN_YEAR

assert MONTHS_IN_YEAR == 12 and WEEKS_IN_YEAR == 52
assert max_(3, 0) == 3 and min_(3, 5) == 3
```

- Two-way branch: `where(cond, a, b)`.
- Many-way: `select([c1, c2, c3], [v1, v2, v3], default=v0)`. List **every** case explicitly and set
  `default` to the Enum's `default_value` — don't bury a real category in the default.
- Bounds: `clip(x, lo, hi)` or `max_(lo, min_(x, hi))`.

## Floor a subtraction with `max_(A - B, 0)`, not `max_(A, 0) - B`

The single most common tax bug. `max_(A, 0) - B` floors `A` but then subtracts `B`, so the *result*
can still go negative — and if `B` is itself a negative loss, `A - B` grows instead. Wrap the whole
subtraction:
```python
# ❌ phantom negative income when capital_gains is a loss (B < 0 → income - B larger; or result < 0)
regular_income = max_(income, 0) - capital_gains
# ✅
regular_income = max_(income - capital_gains, 0)
```
This is the Montana income-tax bug: `max_(agi, 0) - capital_gains` taxed phantom income. The same
shape protects benefit caps — `max_(payment_standard - countable_income, 0)` must floor the
subtraction, or negative countable income inflates the benefit past the cap (see the negative-income
test in references/tests.md).

## Divide without divide-by-zero warnings

`where(total > 0, part / total, 0)` still evaluates `part / total` for the zero rows (both branches
are computed), emitting warnings and NaNs. Use `np.divide` with a `where=` mask; `out` supplies the
value for masked-out rows:
```python
mask = total_income > 0
share = np.divide(
    person_income,
    total_income,
    out=np.zeros_like(person_income),   # rows where mask is False keep this (0.0)
    where=mask,
)
# out=np.ones_like(...) makes the default 1.0 instead.
```
Reference implementations: `taxable_social_security.py`, `mo_taxable_income.py`,
`md_two_income_subtraction.py`, `ok_child_care_child_tax_credit.py`.

## Conditional accumulation

To sum only over qualifying members, zero out the rest before aggregating (don't slice):
```python
person = household.members
eligible_income = where(person("is_eligible", period), person("income", period), 0)
total = household.sum(eligible_income)
```

## Debugging phantom values

A tax that is non-zero when taxable income is zero usually comes from a bracket/rate applied without
short-circuiting on zero income. Trace the chain (`uv run pytest path -vv` to see intermediates);
where a downstream value should be zero but isn't, guard it:
```python
return where(taxable_income == 0, 0, p.rates.calc(taxable_income))
```
And prefer `max_`/`clip` over Python `max`/`min` so array dtypes are preserved through the chain.
