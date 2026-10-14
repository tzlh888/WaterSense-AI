# WaterSense V4 Candidate frozen protocol

**Frozen:** 2026-10-14 before the V4 classifier results were computed.

## Scope and evidence boundary

The only new model experiment is a fixed, development-only Logistic Regression classifier for the event `DO < 4 mg/L`. It uses the exact 119,690-row, 672-station development population and the existing five outer station-grouped folds. The historical grouped holdout and every other legacy test result are prohibited for fitting, threshold choice, model choice, or interpretation. This is not independent confirmation and does not modify the deployed regression model.

## Fixed classifier

- Predictors: the frozen full WaterSense feature set; target and target qualifier excluded.
- Preprocessing: fold-local median imputation with missing indicators and scaling for measurements; censor indicators pass through.
- Estimator: `LogisticRegression(C=1.0, solver="lbfgs", class_weight="balanced", max_iter=1000, random_state=20261014)`.
- Decision threshold: 0.5, fixed without inspection or tuning.
- Evaluation: concatenate exactly one out-of-fold prediction for every development row.
- Metrics: Recall, Precision, F1, FP, FN, fold variation, and station-level variation. MAE is not defined for the classifier.
- Status: `NEW EXPERIMENT — EXPLORATORY / DEVELOPMENT-ONLY` regardless of outcome.

No two-stage classifier-regressor is run. Adding one after seeing these results would expand the search space post hoc; it requires a separately frozen protocol and a new untouched evaluation population.

## Fixed cost sensitivity

For the historical regression baseline, the v3 selected procedure, and the fixed classifier, compute `Cost = C_FN × FN + C_FP × FP` at hypothetical ratios `C_FN:C_FP` of 1:1, 2:1, 5:1, 10:1, 25:1, and 50:1. These ratios are scenario parameters, not measured regulatory or environmental costs. Ties remain ties.

## External-validation gate

An external candidate must have documented license, acquisition URL/date/version/hash, non-overlap with the 1990–2024 source records, compatible DO units and method, target validity, and complete coverage of the frozen predictors. The current OpenDataNI publication fails the independence gate because its downloaded bytes exactly match the historical raw export. No external evaluation is run.
