# Low-DO Weighted Regression — Frozen Execution Protocol

**Status:** prepared, not executed. **Training performed in Phase 2B-0:** no.

## Hypothesis and eligible data

Increasing the loss contribution of training-fold observations with ground-truth DO `<4 mg/L` may reduce low-DO overprediction and false negatives without unacceptable overall regression degradation. Only the exact 119,690-row/672-site historical development partition is eligible. Every registered legacy benchmark is prohibited from tuning and selection.

## Fold-local processing and weights

All imputation, missingness indicators and scaling are fitted inside the relevant training fold. For multiplier `m ∈ {1,2,4,8}`, raw sample weight is `m` for training target `<4`, otherwise `1`; divide by the training-fold mean raw weight so total weight equals the training row count. Validation targets never influence weights or preprocessing. Row duplication/resampling to imitate weights is prohibited.

## Candidates and frozen search

- Random Forest and Extra Trees: trees `{150,300}`, minimum leaf `{2,5}`, max features `{0.6,0.8}`.
- Histogram Gradient Boosting: learning rate `{0.03,0.07}`, max leaf nodes `{15,31}`, minimum leaf `{20,50}`, L2 `{0,1}`.
- Every candidate crosses the four weight multipliers; random seed 20261012. The complete machine-readable grid is in `WEIGHTED_REGRESSION_CONFIG.json`.

## Inner selection

Co-primary metrics are low-DO Recall (higher) and low-DO MAE (lower). A candidate qualifies only if inner out-of-fold overall MAE is no more than 10% worse than the same-fold unweighted anchor, low-DO Precision is at least 0.30, every fold with true low DO has at least one predicted-low row, and there is no data/split/non-finite/undefined-required-metric failure.

Rank qualified candidates lexicographically by: highest mean low-DO Recall; lowest mean low-DO MAE; lowest overall MAE; lower complexity; stable candidate ID. This prevents choosing whichever metric looks favorable after results.

## Outer evaluation and metrics

Fit the inner-selected configuration on each outer-training partition and evaluate it once on that outer validation partition. Concatenate outer out-of-fold predictions. Report Overall MAE/RMSE/R²; Low-DO MAE/RMSE/Bias (prediction−truth); Recall, Precision, F1 and FNR; row/site denominators; fold dispersion; and 2,000 paired whole-site percentile bootstrap intervals with seed 20261012.

Improved Recall with materially worse overall MAE is a tradeoff, not a universal improvement. No rule requires all metrics to improve.

## Stopping and failure

Execute the fixed grid once. Do not add candidates after viewing outcomes. Stop with `NO QUALIFIED MODEL` if all candidates fail. A fold with missing/overlapping sites, inadequate frozen support, non-finite predictions, no predicted positives, or unsupported sample weights is a recorded failure. Legacy tests cannot rescue or change a failed result.
