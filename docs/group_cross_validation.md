# Station-grouped cross-validation

## Purpose

Phase 3 used one station-grouped holdout. That split remains the sealed final reference set: 119,690 training rows from 672 stations and 31,341 test rows from 168 different stations. Phase 4 performs model and feature selection only within the Phase 3 training portion.

Five-fold `GroupKFold` uses `StationCode` as the group. Each validation fold contains records from 134 or 135 stations that are absent from that fold's training data. The 168 final-test stations are absent from every cross-validation fold. Preprocessing, including median imputation, missingness indicators and scaling, is fitted separately inside each fold.

## Core-feature results

| Model | CV MAE mean | CV MAE SD | MAE min–max | CV RMSE mean | CV R² mean |
|---|---:|---:|---:|---:|---:|
| HistGradientBoosting | 1.184 | 0.039 | 1.129–1.227 | 1.696 | 0.272 |
| Random Forest | 1.219 | 0.036 | 1.172–1.255 | 1.732 | 0.240 |
| Linear Regression | 1.325 | 0.049 | 1.267–1.381 | 1.883 | 0.102 |
| Dummy Mean | 1.430 | 0.060 | 1.350–1.492 | 1.994 | -0.006 |

The complete fold-level MAE, RMSE, R², row counts and station counts are stored in `results/group_cv_results.csv`.

## Interpretation

Cross-validation shows whether performance is consistent across several different groups of withheld stations instead of depending on one favourable split. HistGradientBoosting had the lowest mean core-feature MAE, but its fold results still varied from 1.129 to 1.227 mg/L. This variation is evidence that the particular station groups matter.

Cross-validation does not remove all uncertainty. There are only five folds, monitoring effort is uneven, and every fold still comes from the same Northern Ireland monitoring program and historical dataset.
