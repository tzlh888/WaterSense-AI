# WaterSense Low-DO Reliability Report

**Generated from saved predictions only:** no model fitting or selection was performed.  
**Positive class:** ground-truth DO `< 4 mg/L`; predicted positive: prediction `< 4 mg/L`.  
**Primary detailed view:** the previously inspected station-grouped holdout; it is a legacy benchmark, not a new independent holdout.

## Executive finding

The deployed regression is not reliable for low-oxygen detection on the saved legacy evaluations. On the station-grouped holdout, overall MAE is **0.831 mg/L**, but low-DO MAE rises to **3.139 mg/L** and mean low-DO bias (prediction − truth) is **+3.119 mg/L**. Recall is **0.084** (14/167); the false-negative rate is **0.916** (153/167). Precision is **0.700** (14/20).

The direction is consistent with systematic overestimation of true low values. This is a confirmed descriptive finding for the saved predictions, not evidence of a causal mechanism or prospective generalisation.

## Denominators and metric rules

- Regression metrics use every row in the named saved-prediction partition.
- Low-DO MAE/RMSE/bias use rows whose ground truth is strictly below 4 mg/L.
- Recall = TP/(TP+FN); FNR = FN/(TP+FN); precision = TP/(TP+FP); F1 = 2TP/(2TP+FP+FN).
- If a partition has zero predicted positives, precision and F1 are stored as missing/undefined, never silently replaced with zero. If it has zero actual positives, recall and FNR are undefined. Each bootstrap metric reports its valid and invalid resample counts.
- Bias is always prediction minus ground truth; positive values mean overprediction.

## Independent evidence and repeated appearances

The repeated spatiotemporal file contains **129 low-DO appearances**, but only **56 unique low-DO source observations** at **20 stations**. The same source observation appears under multiple split seeds, so appearances share both measured outcomes and modelling context. They cannot be treated as 129 independent observations. The unique-observation view averages predictions across an observation's appearances before station-clustered bootstrap; this reduces duplication but still does not create a new holdout.

## Site-clustered uncertainty

The station-grouped low-DO MAE 95% interval is **[2.859, 3.498] mg/L**; low-DO bias is **[2.824, 3.486] mg/L**; FNR is **[0.875, 0.978]**. Bootstrap draws whole sites with replacement using seed 20261012 and 2,000 replicates. Only 31 holdout sites contain low-DO observations, so intervals remain sensitive to which rare sites appear; the bootstrap quantifies sampling instability within this observed station population, not external validity.

Resamples with undefined metrics are excluded only from that metric's percentile calculation and explicitly counted:

| partition | metric | valid_resamples | invalid_resamples |
| --- | --- | --- | --- |
| station_grouped_holdout | low_do_precision | 1999 | 1 |
| station_grouped_holdout | low_do_f1 | 1999 | 1 |
| spatiotemporal_seed_42 | low_do_mae_mg_l | 1994 | 6 |
| spatiotemporal_seed_42 | low_do_rmse_mg_l | 1994 | 6 |
| spatiotemporal_seed_42 | low_do_bias_prediction_minus_truth_mg_l | 1994 | 6 |
| spatiotemporal_seed_42 | low_do_recall | 1994 | 6 |
| spatiotemporal_seed_42 | low_do_precision | 1730 | 270 |
| spatiotemporal_seed_42 | low_do_f1 | 1730 | 270 |
| spatiotemporal_seed_42 | low_do_false_negative_rate | 1994 | 6 |
| repeated_spatiotemporal_unique_mean_prediction | low_do_precision | 1963 | 37 |
| repeated_spatiotemporal_unique_mean_prediction | low_do_f1 | 1963 | 37 |

## Error concentration and distribution

The five largest station contributors account for **62.6%** of station-grouped low-DO absolute error. Their identifiers and metrics are in `LOW_DO_SITE_ANALYSIS.csv`; this concentration is descriptive and partly reflects unequal observation counts.

Years differ in low-DO support and error; `LOW_DO_YEAR_ANALYSIS.csv` reports denominators rather than presenting unstable small-year estimates as equivalent. The strongest exploratory feature/error correlations are:

| feature | nonmissing_count | missing_fraction | spearman_with_absolute_error |
| --- | --- | --- | --- |
| suspended_solids_mg_l | 84 | 0.497 | 0.244 |
| conductivity_us_cm | 106 | 0.365 | -0.232 |
| alkalinity_mg_l | 125 | 0.251 | -0.225 |
| ph | 155 | 0.072 | 0.201 |
| soluble_reactive_phosphorus_mg_l | 148 | 0.114 | -0.118 |

These are statistical associations within low-DO holdout rows. They do not establish that changing a chemical measurement would change model error. Missingness is evaluated separately in `LOW_DO_MISSINGNESS_ANALYSIS.csv`.

## Training support and evidence gaps

The raw source CSV and processed modelling table are absent from the public checkout. Therefore exact training-set low-DO counts and row-level target membership cannot be freshly verified here. The saved `spatiotemporal_validation.csv` reports a training low-DO fraction of **0.005994 (0.5994%)** for its 120,955-row training partition. This is clear aggregate evidence of severe rarity in that historical partition, but remains saved metadata rather than a fresh row-level reconstruction. Feature associations can be computed for the full station holdout because that saved table includes features; comparable attribution is unavailable for prediction files that retain only identifiers, dates, actuals, and predictions.

Potential measurement anomalies are listed as review candidates in `LOW_DO_EXTREME_CASES.csv`. Saved predictions alone cannot determine whether an extreme value is a sensor/measurement error, a genuine event, or an underrepresented regime.

## Interpretation classes

- **Confirmed finding:** saved predictions substantially overpredict true low DO and miss most `<4 mg/L` cases across all recorded validation regimes.
- **Statistical association:** site, year, feature value, and missingness summaries identify concentration or correlation with error in the legacy holdout.
- **Hypothesis requiring further testing:** low-DO rarity, omitted hydrologic/context features, censoring, temporal shift, or measurement problems may cause the failure. Causal attribution requires eligible development data and prospectively frozen evaluation.
