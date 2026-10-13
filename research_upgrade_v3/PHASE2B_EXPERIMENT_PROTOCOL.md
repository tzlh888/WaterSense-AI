# Frozen Phase 2B Experiment Protocol

**Status:** preregistered design only; no candidate has been trained.  
**Freeze date:** 2026-10-12. Amendments require a dated decision-log entry before seeing affected results.

## 1. Entry gate and data eligibility

Phase 2B may start only after the processed modelling table is restored, its row count/source IDs/raw SHA-256 are checked against the historical manifests, and the original grouped split is reconstructed exactly. Development is restricted to the original 119,690-row, 672-station training partition. Every registered legacy benchmark, including the original holdout and all temporal/spatial variants, is prohibited from tuning, thresholding, early stopping, candidate addition, feature decisions, or failure-driven iteration.

Before fitting, tabulate low-DO rows and low-DO sites per proposed outer/inner fold. Default validation is nested station-grouped CV: five outer folds and four inner folds with deterministic, low-DO-support-balanced site assignment, seed 20261012. A site must occur in exactly one fold at each level; preprocessing is fitted inside every inner/outer training fold. The fold-assignment algorithm and membership hashes must be saved before scores are read.

If any outer fold has fewer than three low-DO sites or 10 low-DO rows, nested five-fold estimates are declared unsupported. The fallback is three outer station folds with the same isolation and four inner folds where feasible. If that also fails, use the ten frozen grouped Monte Carlo seeds `[11,23,42,57,71,89,101,123,149,173]` on development stations only, report all split-specific outcomes, and label the result exploratory; do not claim reliable nested-CV model ranking.

## 2. Shared outcome and selection rules

Co-primary metrics are low-DO recall (higher is better) and low-DO MAE (lower is better). Candidate qualification requires, on inner out-of-fold predictions: (a) overall MAE no more than 10% worse than the unchanged historical-model configuration refit on the same folds; (b) low-DO precision at least 0.30; (c) at least one predicted low observation in every fold containing true low observations; and (d) no data-integrity failure. Among qualified candidates, choose lexicographically by highest mean low-DO recall, lowest mean low-DO MAE, then lowest overall MAE, then lower complexity, then stable candidate ID.

Secondary metrics: overall RMSE/R²; low-DO RMSE; prediction-minus-truth bias; precision/F1/FNR; sample/site counts; fold dispersion; and error by DO range/year/missingness. All denominators use the Phase 2A definitions. Final development estimates concatenate outer-fold predictions, with 2,000 paired whole-site bootstrap resamples (seed 20261012) for metric and candidate-difference intervals. Small-site limitations must be reported.

The fixed search budget is executed once. A family stops when its enumerated space is exhausted or all candidates fail qualification. No search extension follows a disappointing result. Runtime failure, unsupported low-DO folds, non-finite predictions, split overlap, or undefined required metrics are retained as failures rather than silently dropped.

## 3. Experiment 1 — Low-DO Weighted Regression

- **Hypothesis:** increasing training loss contribution for true DO `<4 mg/L` reduces low-DO overprediction and false negatives without unacceptable global degradation.
- **Training eligibility/validation:** shared gate and nested site CV above; weights are computed only from each training fold's target.
- **Candidates:** the current Random Forest configuration; `HistGradientBoostingRegressor`; `ExtraTreesRegressor`. Each uses the frozen full feature set and fold-fitted preprocessing.
- **Search space:** low-DO weight multiplier `{1, 2, 4, 8}`; RF/ExtraTrees trees `{150, 300}`, minimum leaf `{2, 5}`, `max_features {0.6, 0.8}`; HGB learning rate `{0.03, 0.07}`, max leaf nodes `{15, 31}`, minimum leaf `{20, 50}`, L2 `{0, 1}`. Seed 20261012 where supported. Multiplier 1 anchors the unweighted comparison.
- **Qualification/metrics/uncertainty:** shared rules. Weight support must be native and verified; resampling rows to mimic weights is prohibited because it fabricates apparent sample size.
- **Stopping/failure interpretation:** stop after the fixed grid. No qualified improvement suggests simple loss reweighting is insufficient under available features/support; it does not prove low DO is intrinsically unpredictable.

## 4. Experiment 2 — Two-stage Classification + Regression

- **Hypothesis:** an explicit low-DO detector can improve threshold sensitivity, while separate continuous regressors preserve concentration estimation.
- **Training eligibility/validation:** shared gate; classifier probability threshold and both regressors are selected only in inner site folds.
- **Candidates:** classifiers `LogisticRegression` with class weight `{balanced, 2, 4, 8}`, `RandomForestClassifier`, and `HistGradientBoostingClassifier`; general regressor and low-DO specialist from the frozen RF or HGB families. A gated prediction uses the specialist only when detector probability crosses its inner-selected threshold.
- **Search space:** probability threshold `{0.10,0.20,0.30,0.40,0.50}`; RF classifier trees `{200,400}`, minimum leaf `{2,5}`, max features `{0.6,0.8}`; HGB classifier learning rate `{0.03,0.07}`, max leaf nodes `{15,31}`, L2 `{0,1}`. Regressor settings are restricted to the corresponding Experiment 1 grid. No test-informed threshold.
- **Qualification/metrics/uncertainty:** shared rules plus calibration slope/intercept and PR-AUC as secondary classifier diagnostics. If a fold lacks enough low-DO training sites to fit the specialist, that configuration fails rather than borrowing validation rows.
- **Stopping/failure interpretation:** stop after the fixed grid. High recall with precision below 0.30 fails qualification; good classification with poor continuous low-DO MAE indicates the specialist regression is unsupported.

## 5. Experiment 3 — Feature / Missingness Ablation

- **Hypothesis:** extended chemistry, censor flags, temporal features, and explicit missingness convey different predictive signal; some may amplify site/year artifacts in the low-DO tail.
- **Training eligibility/validation:** shared gate and the winning eligible estimator family from development-only Experiment 1, or the unchanged RF anchor if Experiment 1 has no qualifier. This experiment cannot promote a family using legacy results.
- **Frozen ablations:** full historical set; core chemistry only; core plus censor indicators; full minus temporal sine/cosine; full minus extended chemistry; full values without censor indicators; full plus per-feature missing indicators and row missing fraction. No station ID, target qualifier, location label, coordinates, basin, or target-derived feature is permitted.
- **Search space:** no new estimator hyperparameters beyond the development-selected setting; only the seven named feature specifications.
- **Qualification/metrics/uncertainty:** shared rules, paired site bootstrap against full features, and fold-level missingness/error summaries.
- **Stopping/failure interpretation:** stop after all seven. Association or ablation changes identify predictive dependence, not chemical causality. Instability across folds indicates site-specific signal or insufficient support, not a basis for inspecting legacy tests and redesigning.

## 6. Post-selection boundary

After nested CV, one configuration per experiment may be frozen. Legacy benchmarks may then be run once for descriptive continuity, clearly labelled legacy. They cannot alter the winner. A genuinely new confirmation requires independently acquired/sealed sites or prospective observations whose outcomes were unavailable during this protocol and all Phase 2B development.
