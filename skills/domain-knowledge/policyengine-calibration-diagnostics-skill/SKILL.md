---
name: policyengine-calibration-diagnostics
description: |
  Sensitivity registry for PolicyEngine microsim results — maps {program × deviation signature} to the most likely calibration target or imputed variable driving the mismatch. The knowledge base that powers the calibration-diagnostics agent.
  Load when investigating why a microsim result differs from a prior score, or when reviewing whether a reform classification is calibration-sensitive.
  Triggers: "why does my reform not match", "policyengine cost off", "calibration mismatch", "imputed variable", "takeup rate", "non-filer", "itemizer share", "small state variance", "ECPS calibration target", "policyengine-us-data target", "calibration dashboard", "diagnose mismatch", "deviation signature".
---

# PolicyEngine Calibration Diagnostics

Converts tribal "I'd check the takeup rate first" knowledge into a structured sensitivity registry. When a `/analyze-policy` Stage 5 comparison fails, this skill provides the ranked candidate causes.

## When to use

- Stage 6 of `/analyze-policy` — invoked by the `calibration-diagnostics` agent.
- Code review of microsim PRs where the headline number differs from priors.
- Designing a new `policyengine-us-data` calibration target.
- Debugging why a state-level run looks volatile.

## Top-level architecture

PolicyEngine microsim results depend on three layers:

1. **Country model logic** (policyengine-us, policyengine-uk, policyengine-canada) — formulas, parameters.
2. **Calibrated microdata** (`policyengine-us-data`) — survey weights + imputations matched to administrative targets.
3. **Behavioral assumptions** (takeup rates, labor-supply elasticities) — usually parameters but easy to overlook.

A mismatch is almost always rooted in layer 2 or 3, not layer 1 (layer 1 mismatches show up as outright simulation errors, not magnitude drift).

## Sensitivity table — top programs

### EITC

| Calibration input | Direction of effect | Notes |
|---|---|---|
| Childless-adult takeup rate | Higher → more cost, more poverty reduction in deciles 1-3 | Historically ~65% childless vs ~80% with-kids. If model uses uniform takeup, expansions over-state. Verify against `policyengine_us/parameters/gov/irs/credits/eitc/takeup.yaml` if present. |
| Earnings distribution in $5K-$15K band | More density → more phase-in/plateau region beneficiaries | PUF→CPS imputation is sparse for childless filers here. |
| Tax-unit definition for cohabiting adults | More split units → more eligible filers | Look at `tax_unit_count` calibration vs SOI Table 1.1. |
| Age cohort 19-24 workers (newly eligible) | Newly eligible under ARPA-style age expansion | Not separately calibrated in ECPS; the marginal population shows up under generic young-adult bucket. |
| Age cohort 65+ workers (newly eligible) | Eligible under ARPA age-cap removal | **Note: this drives meaningful senior poverty reduction (e.g., -5% in live EITC test). The SKILL previously didn't surface this.** Senior workers with earnings in the EITC phase-in range are NOT in the typical childless-EITC analytical lens — but they are in the ARPA reform's lens. Calibration: 65+ earners with $5-15K earned income are not a separately calibrated population; expect higher variance. |
| Known issue | `github.com/PolicyEngine/policyengine-us/issues/4276` — total EITC over-estimate ~9% vs CBO |

**EITC SKILL coverage note:** This row is thinner than the CTC and SALT rows. The diagnostics agent should emit `coverage_note: "EITC SKILL row is partial; hypotheses below cover takeup and age-cohort but do NOT cover joint-filer marriage-penalty mechanics, investment-income limit interactions, or self-employment-income imputation. If your deviation signature touches any of these, widen the confidence band."`

### CTC

| Calibration input | Direction of effect | Notes |
|---|---|---|
| Non-filer CTC takeup | Higher → much more poverty reduction (largest lever) | ARPA achieved ~90%+ via IRS portal; non-ARPA defaults ~75%. |
| Imputed child age distribution (0-5 vs 6-17) | More 0-5 → more cost (the $3,600 tier) | ECPS imputes; compare to ACS published by year of age. |
| Non-filer share of CPS | Higher → more refundability benefit | CPS undercounts non-filers; addressed via PUF imputation. |
| EITC interaction (refundable ordering) | Incorrect ordering → double-count | Check `irs_credits_ordering` parameter. |
| SPM threshold + state benefit offsets | State-specific | Few states tax CTC; SSI supplements vary. |

### SALT cap

| Calibration input | Direction of effect | Notes |
|---|---|---|
| Itemizer share | Higher → cost balloons, benefit cascades down deciles | Post-TCJA only ~10% itemize. Targeted by `salt_deduction = $21.247B` in `loss.py`. |
| State income tax imputation | Flat (federal-AGI-driven) → regressive signature disappears | High earners in NY/NJ/CA drive the SALT story. |
| Top-1% AGI calibration | Under-weighted → top-decile concentration compresses | Targeted via SOI Table 1.1 AGI bands. |
| AMT interaction | Missing → over-states upper-middle benefit | Pre-TCJA AMT clawed back much SALT. |

### State income tax (any state)

| Calibration input | Direction of effect | Notes |
|---|---|---|
| State weights from CPS | Small state → high variance | RI has ~3-4k records; CA has ~50k. Relative uncertainty inversely scaling. |
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

## Sources

- `github.com/PolicyEngine/policyengine-us-data` — `utils/loss.py` for calibration targets; docs at `policyengine.github.io/policyengine-us-data`.
- `github.com/PolicyEngine/calibration-diagnostics` — live diagnostic dashboard.
- `github.com/PolicyEngine/policyengine-us/issues` — known program-level issues.
- `github.com/PolicyEngine/policyengine-us-data/issues` — known calibration issues.

## Related skills

- `policyengine-us-data-skill` — calibration pipeline structure (microimpute / microcalibrate / l0).
- `policyengine-prior-scores` — what we're comparing against.
- `microcalibrate`, `microimpute`, `l0` — the underlying tools.
