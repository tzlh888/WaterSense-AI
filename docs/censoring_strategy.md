# Censoring strategy

**Dataset inspected:** NIEA River Water Quality Monitoring 1990–2024 — All Parameters  
**Inspection date:** 2026-09-30

## What the raw data contain

Each affected measurement has a numeric result column and a separate `Q_...` qualifier column. A raw record can therefore contain, for example, a numeric ammonia value of `0.04` and a qualifier of `<`. The numeric field remains numeric; the qualifier records that the result is below the reported limit rather than an ordinary exact observation.

The inspected core feature qualifiers contain only blank, `<`, and `>` values. No other notation was found. Every `<` or `>` core-feature qualifier has a non-missing numeric companion. The repository does not establish whether every historical limit is specifically a detection limit or a quantification limit, so the neutral term **reported limit** is used.

## Affected variables

Percentages below use all 178,680 raw rows as the denominator.

| Measurement | Qualifier | `<` count | `<` % | `>` count | `>` % | Observed numeric representation |
|---|---|---:|---:|---:|---:|---|
| Dissolved oxygen target | `Q_DO` | 6 | 0.003% | 0 | 0% | `<0.1` in four rows and `<1.0` in two rows |
| BOD | `Q_BOD` | 31,191 | 17.456% | 898 | 0.503% | Numeric companion values; most common `<` limits are 2.0 and 1.0 mg/L |
| Ammonia as nitrogen | `Q_NH4N` | 52,951 | 29.634% | 8 | 0.004% | Numeric companion values; 52,928 `<` rows report 0.04 mg/L |
| Nitrite as nitrogen | `Q_NO2N` | 32,106 | 17.969% | 0 | 0% | Numeric companion values with several historical limits, most commonly 0.02, 0.006 and 0.005 mg/L |
| Nitrate as nitrogen | `Q_NO3N` | 6,327 | 3.541% | 0 | 0% | Numeric companion values, most commonly 0.05 or 0.06 mg/L |
| Soluble reactive phosphorus | `Q_PSOL` | 27,312 | 15.285% | 2 | 0.001% | Numeric companion values, most commonly 0.01 or 0.05 mg/L |
| pH | `Q_pH` | 0 | 0% | 0 | 0% | Qualifier column is completely blank |

## Scientific implications

A result reported as `<0.04` does not mean the true concentration equals 0.04. It means the true value was reported below that limit. Treating every such number as an exact observation creates artificial spikes at laboratory reporting limits and can bias relationships learned by a model. `>` results are similarly not exact upper-tail measurements.

The official service notes a half-value convention for Water Framework Directive calculations. That convention serves a particular regulatory calculation and is not automatically valid for this machine-learning objective. This project does not replace censored values with half the reported limit and does not claim to recover their true concentrations.

## Phase 3 baseline treatment

The baseline preserves the numeric value exactly as exported and adds explicit binary flags for every core predictor with a qualifier:

- `<feature>_is_below_limit`
- `<feature>_is_above_limit`

This transparent representation lets the model distinguish reported-limit observations from unqualified values without pretending the numeric companion is the true concentration. The numeric values can still be imputed when missing, but censor flags are retained separately.

The six censored dissolved-oxygen target rows are excluded from supervised modelling because a target must be treated as the outcome itself; adding a target censor flag as a predictor would be leakage. Six rows are 0.004% of the 151,037 non-missing target observations, so exclusion is limited and explicitly recorded. The 27,643 rows with missing dissolved oxygen are also excluded from supervised modelling.

This is a baseline strategy, not a full censored-data model. Later work could compare it with methods designed for detection limits, but any alternative must be justified and evaluated without using the holdout to choose the method.

