# Phase 4 model refinement

## Objective

Estimate dissolved oxygen concentration from contemporaneously measured physicochemical river-water variables while testing generalisation to monitoring stations excluded from training. This remains regression, not future forecasting, drinking-water safety classification or official ecological-status assessment.

## Phase 3 Baseline

The Phase 3 Random Forest used six core chemistry measurements and qualifier flags. On the fixed station-grouped holdout it obtained MAE 1.181 mg/L, RMSE 1.644 mg/L and R² 0.253. Its lowest-DO decile MAE was 2.362 mg/L and its highest-decile MAE was 2.117 mg/L.

## Group Cross-Validation

The original 31,341-row, 168-station test set was sealed during Phase 4 model selection. Five-fold `GroupKFold` was applied only to the 119,690 Phase 3 training rows and 672 training stations. Every fold fits preprocessing from its own training rows; no station crosses between fold training and validation, and no final-test station enters tuning.

Core-feature results were:

| Model | CV MAE mean | CV MAE SD | CV RMSE mean | CV R² mean |
|---|---:|---:|---:|---:|
| HistGradientBoosting | 1.184 | 0.039 | 1.696 | 0.272 |
| Random Forest | 1.219 | 0.036 | 1.732 | 0.240 |
| Linear Regression | 1.325 | 0.049 | 1.883 | 0.102 |
| Dummy Mean | 1.430 | 0.060 | 1.994 | -0.006 |

## Feature Set Experiments

Feature sets were compared with the core-CV winner, HistGradientBoosting:

| Feature set | Input predictors | CV MAE mean | CV MAE SD | CV RMSE mean | CV R² mean |
|---|---:|---:|---:|---:|---:|
| D — extended + temporal | 25 | 0.931 | 0.037 | 1.451 | 0.467 |
| C — core + temporal | 18 | 0.986 | 0.041 | 1.522 | 0.414 |
| B — extended chemistry | 23 | 1.132 | 0.032 | 1.621 | 0.335 |
| A — core chemistry | 16 | 1.184 | 0.039 | 1.696 | 0.272 |

The extended measurements are alkalinity (mg/L), conductivity (µS/cm) and suspended solids (mg/L), with qualifier flags where present. On the 151,031 eligible rows, missingness is 21.719%, 26.051% and 25.785%, respectively. Alkalinity has 2,719 `<` qualifiers, suspended solids has 22,465, and the conductivity qualifier is empty. The same numeric-value-plus-qualifier-flag strategy is used as in Phase 3.

Temporal context consists of sine and cosine transforms of day of year. These encode annual position without treating dates as arbitrary IDs. Seasonality can be predictively relevant to DO, but these variables do not prove a seasonal causal mechanism and do not turn contemporaneous estimation into forecasting.

No temperature field or alternative water-temperature representation exists in the raw 40-column export or documented schema. Temperature was not fabricated or estimated from date.

## Additional Model

`HistGradientBoostingRegressor` was added using scikit-learn. It fits a sequence of small trees that correct earlier errors. It improved on the core-feature Random Forest in group CV while preserving the project's existing dependency stack.

## Hyperparameter Search

Seven deliberately limited candidates were evaluated on the selected feature set: three Random Forest and four HistGradientBoosting configurations. This was a manual, reproducible search rather than a large optimisation sweep.

| Candidate | Main settings | CV MAE mean | CV MAE SD |
|---|---|---:|---:|
| RF leaf-2 | 150 trees, leaf ≥2, max features 0.8 | 0.880 | 0.035 |
| RF depth-20 leaf-4 | 150 trees, depth ≤20, leaf ≥4, max features 0.8 | 0.890 | 0.037 |
| RF Phase 3 settings | 100 trees, unrestricted, all features | 0.893 | 0.034 |
| HGB slow | rate 0.05, 200 iterations, 31 leaves, L2 0.1 | 0.930 | 0.037 |
| HGB baseline | rate 0.1, 100 iterations, 31 leaves | 0.931 | 0.037 |
| HGB compact | rate 0.1, 150 iterations, 15 leaves, L2 0.1 | 0.937 | 0.036 |
| HGB regularized | rate 0.05, 200 iterations, 15 leaves, L2 1.0 | 0.942 | 0.038 |

All exact parameter dictionaries and results are stored in `results/model_tuning_results.csv`.

## Final Model Selection

The predeclared primary rule was lowest mean station-grouped CV MAE on training stations. `RF leaf-2` was selected with CV MAE 0.880 ± 0.035 mg/L, CV RMSE 1.392 mg/L and CV R² 0.510. Its variability was similar to the nearby Random Forest candidates, and `min_samples_leaf=2` provides modest regularisation. The final holdout and its tail errors were not used for selection.

## Final Holdout Evaluation

After selection, the complete pipeline was fitted to the Phase 3 training portion and evaluated once on the unchanged test set:

| Model | MAE | RMSE | R² |
|---|---:|---:|---:|
| Phase 4 selected Random Forest | 0.831 | 1.291 | 0.539 |
| Phase 3 core Random Forest | 1.181 | 1.644 | 0.253 |

MAE decreased by 0.350 mg/L, or 29.640%. This comparison combines the feature-set change and modest model refinement; it does not attribute the entire gain to tuning.

## Tail Error Analysis

| Actual-DO range | Rows | MAE | RMSE | Mean residual | Overpredicted | Underpredicted |
|---|---:|---:|---:|---:|---:|---:|
| Lowest 5% | 1,615 | 2.243 | 2.638 | -2.163 | 93.313% | 6.687% |
| Lowest 10% | 3,308 | 1.812 | 2.218 | -1.684 | 89.964% | 10.036% |
| 10–25% | 4,589 | 0.824 | 1.091 | -0.533 | 73.284% | 26.716% |
| 25–75% | 15,130 | 0.572 | 0.768 | +0.029 | 48.942% | 51.058% |
| 75–90% | 4,774 | 0.560 | 0.762 | +0.382 | 28.069% | 71.931% |
| Highest 10% | 3,540 | 1.396 | 2.305 | +1.358 | 5.169% | 94.831% |
| Highest 5% | 1,750 | 2.018 | 3.124 | +1.992 | 2.400% | 97.600% |

Lowest-decile MAE improved by 0.550 mg/L (23.283%) and highest-decile MAE by 0.720 mg/L (34.033%) relative to Phase 3. Nevertheless, extreme low values are still usually overpredicted and extreme high values underpredicted. Prediction compression therefore remains the central failure pattern.

Station-level error also varies. Among stations with at least 30 test samples, `UKGBNIF10521` has the highest MAE (3.195 mg/L across 202 samples) and a +1.187 mg/L mean residual. `UKGBNIF10098` has a -1.674 mg/L mean residual across 95 samples, while `UKGBNIF10575` has -1.482 mg/L across 232 samples. These are descriptive differences, not causal site diagnoses.

Summer has the highest seasonal MAE (0.919 mg/L); autumn, winter and spring have MAEs of 0.788, 0.789 and 0.825 mg/L. The earliest test years have several of the largest annual errors. No climatic, policy or pollution cause is inferred.

## Explainability

Held-out permutation importance ranks the cyclical seasonal variables and pH highest:

| Feature | Mean MAE increase after permutation | SD |
|---|---:|---:|
| Day-of-year cosine | 0.447 | 0.003 |
| pH | 0.322 | 0.004 |
| Day-of-year sine | 0.291 | 0.002 |
| Alkalinity | 0.150 | 0.002 |
| Nitrate | 0.083 | 0.002 |
| Nitrite | 0.080 | 0.001 |
| Conductivity | 0.080 | 0.002 |

Permutation importance asks how much held-out MAE worsens when one input's information is disrupted. Partial-dependence plots were also produced for well-supported leading inputs. Both techniques describe fitted model behaviour and predictive association, not physical causation.

SHAP was not added. It is not part of the existing dependency stack, and adding it was unnecessary because permutation importance and partial dependence provided stable global explanations. This avoids forcing a compatibility-sensitive dependency solely for extra visualisations.

## Low-DO Case Studies

The largest low-DO overpredictions span different stations, dates, seasons, chemistry patterns and missingness profiles. Qualifier censoring is not a shared explanation among the five reviewed cases. Available metadata does not support one common cause. Full cases are recorded in `docs/low_do_case_studies.md`.

## Uncertainty / Error Distribution

Across all five group-CV validation folds, absolute-error percentiles are:

| Percentile | Absolute error |
|---|---:|
| 50th | 0.592 mg/L |
| 75th | 1.117 mg/L |
| 90th | 1.908 mg/L |
| 95th | 2.622 mg/L |

These are empirical validation-error summaries, not individual prediction intervals or formal confidence bounds.

## Temporal Sensitivity

The selected pipeline trained on 1990–2018 and evaluated on 2019–2024 obtained MAE 0.657 mg/L, RMSE 0.922 mg/L and R² 0.675. This split tests transfer from earlier to later monitoring records, whereas the primary split tests transfer to unseen stations. Neither is a true forecasting design.

## Limitations

- Water temperature, flow, time-of-day conditions and other physical drivers are unavailable or unused.
- Seasonal variables are predictive context, not a substitute for temperature and not evidence of causation.
- Missing values are median-imputed; this does not reconstruct the true measurements.
- Censored values remain imperfectly represented by reported numeric limits plus flags.
- Extreme observations remain unverified and materially affect tail metrics.
- Five grouped folds and one fixed final holdout do not establish performance in other regions or monitoring programs.
- Empirical absolute-error percentiles are not formal uncertainty intervals.
- The final model artifact is relatively large and remains an analytical baseline rather than a deployment model.

## What Changed From Phase 3

Phase 4 added five-fold station-grouped validation, three extended measurements, cyclical seasonal context, HistGradientBoosting, seven modest tuning candidates, an untouched-test selection protocol, finer tail/station/time analysis, empirical error percentiles, permutation importance and partial dependence. Overall and tail metrics improved, but prediction compression and missing physical context remain important limitations.
