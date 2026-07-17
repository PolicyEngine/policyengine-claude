---
name: policyengine-calibration-diagnostics
description: |
  Sensitivity registry for PolicyEngine microsim results — maps {program x deviation signature}
  to the calibration target or imputed variable most likely driving a mismatch, and reads the
  live per-target diagnostics for the current Populace release. The knowledge base behind the
  calibration-diagnostics agent and /analyze-policy Stage 5.6.
  Load when investigating why a microsim result differs from a prior score, or when reviewing
  whether a reform classification is calibration-sensitive.
  Triggers: "why does my reform not match", "policyengine cost off", "calibration mismatch",
  "imputed variable", "takeup rate", "non-filer", "itemizer share", "small state variance",
  "calibration target", "populace target", "calibration dashboard", "target-diagnostics",
  "relative_error", "diagnose mismatch", "deviation signature".
metadata:
  category: data
---

# PolicyEngine calibration diagnostics

Converts tribal "I'd check the takeup rate first" knowledge into a structured sensitivity
registry, and pairs it with the live per-target calibration API so hypotheses are ranked against
real `relative_error` numbers rather than assumptions. When an `/analyze-policy` comparison
returns INVESTIGATE, this skill supplies the ranked candidate causes.

The calibrated microdata is now a **Populace** build (see the `policyengine-data` skill for how
targets, weights, and L0 sparsity work). Calibration targets live in the populace build's target
set — not in a hand-maintained loss file — and their fit is queryable per release from the
dashboard API below.

## When to use

- Stage 5.6 / Stage 6 of `/analyze-policy` — invoked by the `calibration-diagnostics` agent.
- Code review of microsim PRs where the headline number differs from priors.
- Designing or auditing a populace calibration target.
- Debugging why a state-level run looks volatile.

## Top-level architecture

PolicyEngine microsim results depend on three layers:

1. **Country model logic** (policyengine-us, policyengine-uk, policyengine-canada) — formulas,
   parameters.
2. **Calibrated microdata** (Populace) — survey weights + imputations matched to administrative
   targets.
3. **Behavioral assumptions** (takeup rates, labor-supply elasticities) — usually parameters but
   easy to overlook.

A magnitude mismatch is almost always rooted in layer 2 or 3, not layer 1 (layer-1 mismatches
show up as outright simulation errors, not magnitude drift).

## Live calibration API (check this first)

Per-target fit for the current populace release, no auth, reads the release from Hugging Face:

```
BASE = https://calibration-diagnostics.vercel.app/calibration/dashboard/api/populace
GET {BASE}/target-diagnostics?source=<source>     # every target for a source, with relative_error
GET {BASE}/target-investigation?target=<id>        # full investigation packet for one target
GET {BASE}/releases                                # release ids for pinning
```

Sources map to reform domains: Social Security → `ssa`; Medicaid/ACA/Medicare →
`cms_medicaid` / `cms_aca` / `cms_medicare`; TANF → `hhs_acf_tanf`; income tax / credits →
`irs_soi`, `jct`, `cbo`; state income tax → `state_income_*`. A target already >10% off in the
release diagnostics is a stronger hypothesis than any prior. (Dashboard UI:
`calibration-diagnostics.vercel.app`.)

### The three-ring reading method (align with /analyze-policy Stage 5.6)

Checking only the reform's primary marginal is the classic miss — a reform's cost usually depends
on the **joint** distribution of its variable with other income, and the primary marginal can
calibrate perfectly while the interaction is off. Check three rings outward:

1. **Ring 1 — the primary variable's marginals.** Map the reform's domain to a calibration
   source and fetch its targets.
2. **Ring 2 — the mechanism's other inputs.** Every variable that enters the formula the reform
   changes. SS-benefit taxation depends on combined income, so dividends, taxable interest, and
   pensions (`irs_soi`) are load-bearing; a CTC phase-in depends on earnings; a SNAP change on
   rents and deductions.
3. **Ring 3 — the interacted quantity itself (best single check).** Search for the downstream
   quantity the reform directly reprices — `taxable_social_security_amount` for SS-taxation,
   `eitc_amount` for EITC, itemizer counts for deduction caps. When such a target exists it
   validates the joint distribution end-to-end through the actual formula, and its
   `relative_error` bounds the data-side bias of the score. Weight it above every marginal. When
   no ring-3 target exists, say so — "marginals within tolerance; joint distribution untargeted"
   is materially weaker evidence.

Worked example (HR 904, SS-taxation reform): `ssa` total benefits calibrate to −0.2% (ring 1 fine)
while `irs_soi ... taxable_social_security_amount` runs −10.9% (ring 3) — the score's operative
base is ~11% low in the data even though the headline marginal is nearly exact.

Interpretation is **informative, not a gate**: a poorly-calibrated but reform-relevant target does
not flip the comparator verdict by itself, but it belongs in the report's uncertainty discussion.
Escalate to INVESTIGATE when a directly-load-bearing target (the primary variable OR the ring-3
interacted quantity) is off by `|relative_error| > 25%`, even if headline numbers match anchors.

## Sensitivity table — top programs

The rows below are the paradigm-independent knowledge: which calibration input moves which
result, and in which direction. They hold regardless of which build produced the weights — use
them to decide *which* targets to pull from the API above.

### EITC

| Calibration input | Direction of effect | Notes |
|---|---|---|
| Childless-adult takeup rate | Higher → more cost, more poverty reduction in deciles 1-3 | Historically ~65% childless vs ~80% with-kids. Uniform-takeup models over-state expansions. Verify against `gov/irs/credits/eitc/takeup.yaml` if present. |
| Earnings distribution in $5K-$15K band | More density → more phase-in/plateau beneficiaries | PUF→CPS imputation is sparse for childless filers here. |
| Tax-unit definition for cohabiting adults | More split units → more eligible filers | Check `tax_unit_count` calibration vs SOI Table 1.1. |
| Age cohort 19-24 workers | Newly eligible under ARPA-style age expansion | Not separately calibrated; marginal population sits under the generic young-adult bucket. |
| Age cohort 65+ workers | Eligible under ARPA age-cap removal | Drives meaningful senior poverty reduction (e.g. −5% in a live EITC test). 65+ earners with $5-15K earned income are NOT a separately calibrated population; expect higher variance. |
| Known issue | `github.com/PolicyEngine/policyengine-us/issues/4276` — total EITC over-estimate ~9% vs CBO |

**EITC coverage note:** thinner than the CTC and SALT rows. The diagnostics agent should emit
`coverage_note: "EITC row is partial; hypotheses cover takeup and age-cohort but NOT joint-filer
marriage-penalty mechanics, investment-income-limit interactions, or self-employment-income
imputation. If your deviation signature touches any of these, widen the confidence band."`

### CTC

| Calibration input | Direction of effect | Notes |
|---|---|---|
| Non-filer CTC takeup | Higher → much more poverty reduction (largest lever) | ARPA achieved ~90%+ via IRS portal; non-ARPA defaults ~75%. |
| Imputed child age distribution (0-5 vs 6-17) | More 0-5 → more cost (the $3,600 tier) | Compare imputed age-0-5 share to ACS published by single year of age. |
| Non-filer share | Higher → more refundability benefit | CPS undercounts non-filers; addressed via PUF imputation. |
| EITC interaction (refundable ordering) | Incorrect ordering → double-count | Check `irs_credits_ordering` parameter. |
| SPM threshold + state benefit offsets | State-specific | Few states tax CTC; SSI supplements vary. |

### SALT cap

| Calibration input | Direction of effect | Notes |
|---|---|---|
| Itemizer share | Higher → cost balloons, benefit cascades down deciles | Post-TCJA only ~10% itemize. Track the itemized-deduction / SALT calibration target via `irs_soi` in the live diagnostics. |
| State income tax imputation | Flat (federal-AGI-driven) → regressive signature disappears | High earners in NY/NJ/CA drive the SALT story. |
| Top-1% AGI calibration | Under-weighted → top-decile concentration compresses | Targeted via SOI Table 1.1 AGI bands. |
| AMT interaction | Missing → over-states upper-middle benefit | Pre-TCJA AMT clawed back much SALT. |

### State income tax (any state)

| Calibration input | Direction of effect | Notes |
|---|---|---|
| State weights from CPS | Small state → high variance | RI has ~3-4k records; CA has ~50k. Relative uncertainty scales inversely. |
| State-AGI tail imputation | High-income tail mis-calibrated for some states | Affects progressive brackets disproportionately. |
| Federal conformity | Outdated assumption → cascading error | Check `gov.states.{state}.tax.income.conformity.*` if present. |

### Refundable credits broadly

| Calibration input | Direction of effect | Notes |
|---|---|---|
| Non-filer share | Higher → more refundability benefit | CPS undercounts; PUF imputation step matters. |
| Takeup rate by income | Defaults often uniform | Real-world takeup varies; mis-spec biases low-income impact. |

## Deviation signature playbook

| Signature | Top hypothesis | Test to run |
|---|---|---|
| Cost too high, benefit too even across deciles | Itemizer share or state-tax imputation flat | Perturb itemizer share −10%; rerun. |
| Cost roughly right, poverty impact understates by ≥30% | Non-filer takeup or SPM unit definition | Set takeup = 0.95; rerun. |
| Small-state cost volatile vs prior | State CPS weight variance | Bootstrap state weights, report CI. |
| Top-decile benefit share too low | Top-AGI under-weighted | Cross-check AGI by SOI band. |
| Reform-vs-baseline difference flat across years | Uprating index mis-set | Verify `uprating.*` parameters. |
| Reform touching an untargeted variable scores ~$0 | Operative base pruned by L0 sparsity | Check if the base is a calibration target; if not, try a denser build (see `policyengine-data`). |

## Sources

- **`calibration-diagnostics.vercel.app`** — live per-target diagnostics API and dashboard (first
  stop; reads the current populace release). Source: `github.com/PolicyEngine/calibration-diagnostics`.
- **`PolicyEngine/populace`** — where calibration targets, weights, and the L0 sparsity live; the
  build that produces the certified dataset. See the `policyengine-data` skill.
- `github.com/PolicyEngine/policyengine-us/issues` — known program-level model issues.

## Related skills

- `policyengine-data` — how Populace builds targets, weights, and the sparse-vs-dense tradeoff.
- `policyengine-prior-scores` — what a run is being compared against.
- `policyengine` — running the perturbation tests this skill recommends.
