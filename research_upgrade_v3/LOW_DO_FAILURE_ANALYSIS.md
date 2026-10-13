# Low-DO Failure Analysis

## Confirmed findings

- In the station-grouped legacy holdout, 153 of 167 true low-DO observations are false negatives (FNR 0.916).
- Mean prediction minus truth on true low-DO rows is +3.119 mg/L; the error is overwhelmingly in the unsafe overprediction direction.
- Error is not uniformly distributed across stations. The leading station contributions are:

| station_code | low_do_count | false_negative_count | low_do_mae_mg_l | low_do_bias_prediction_minus_truth_mg_l | absolute_error_share |
| --- | --- | --- | --- | --- | --- |
| UKGBNIF10575 | 59 | 52 | 3.113 | 3.097 | 0.350 |
| UKGBNIF10533 | 13 | 13 | 3.819 | 3.819 | 0.095 |
| UKGBNIF10292 | 18 | 17 | 2.476 | 2.390 | 0.085 |
| UKGBNIF10521 | 10 | 10 | 2.789 | 2.789 | 0.053 |
| UKGBNIF10398 | 5 | 5 | 4.464 | 4.464 | 0.043 |
| UKGBNIF10342 | 6 | 6 | 3.536 | 3.536 | 0.040 |
| UKGBNIF11449 | 8 | 5 | 1.993 | 1.894 | 0.030 |
| UKGBNIF10546 | 4 | 3 | 3.862 | 3.862 | 0.029 |
| UKGBNIF10675 | 5 | 5 | 2.769 | 2.769 | 0.026 |
| UKGBNIF10121 | 3 | 3 | 4.526 | 4.526 | 0.026 |

`LOW_DO_FALSE_NEGATIVES.csv` preserves row identifiers, station/date, actual, prediction, error, and available feature missingness so every listed failure can be traced to a saved historical prediction.

## Statistical associations

- `LOW_DO_YEAR_ANALYSIS.csv` compares years while retaining low-DO counts and site counts.
- `LOW_DO_FEATURE_ASSOCIATIONS.csv` reports Spearman associations with absolute error and signed bias. These are exploratory, unadjusted, and based only on low-DO rows.
- `LOW_DO_MISSINGNESS_ANALYSIS.csv` compares error by row-level feature missingness. Missingness may proxy period, station, laboratory practice, or chemistry; it is not proven causal.
- `LOW_DO_SITE_ANALYSIS.csv` reports each site's contribution to total low-DO absolute and squared error. Large shares can result from more observations, larger per-row errors, or both.

## Hypotheses requiring further testing

1. Low-DO rarity may cause regression-to-the-centre and weak threshold recall.
2. Missing hydrologic, meteorological, depth, flow, or event context may limit transfer to low-oxygen regimes.
3. Some extreme rows may be genuine events, censoring artifacts, or measurement problems; raw records and provenance are needed to adjudicate them.
4. Year/site associations may reflect distribution shift rather than stable effects.

No item in this section is promoted to a causal conclusion. Phase 2B must test preregistered interventions only within development stations.
