# WaterSense AI — Final Scientific Report

## Research question

Can routine river-water chemistry support dissolved-oxygen (DO) estimation at unseen monitoring stations, and can a development procedure improve recognition of observations below 4 mg/L without concealing the cost to ordinary-condition accuracy?

This is a retrospective observational study, not a causal analysis, regulatory instrument, or deployment validation.

## Data and provenance

The source is the OpenDataNI / Northern Ireland Environment Agency “River Water Quality Monitoring 1990 to 2024 — All Parameters” export, licensed under the UK Open Government Licence v3.0. Exact historical recovery used the British National Grid (`spatialRefId=29902`) export.

- Raw file: 178,680 rows, 1,311 station codes, SHA-256 `a5ce02d9ab3703edc4279c8dc5f9d38a593b92c555945c5cdb2ab3ca55632632`.
- Processed modelling table: 151,031 rows, 840 stations, SHA-256 `5685c2c352b1cc9502cd664736d85295580127016fb60bdca45c082c5d031761`.
- Recovered development partition: 119,690 unique observations, 672 stations, 758 low-DO observations at 115 stations.
- Historical station holdout: 31,341 observations, 168 stations, with zero station overlap with development.

The target is measured DO in mg/L. Rows with a missing or qualified target were excluded. Predictor missingness was retained for fold-local imputation. Exact source, cleaning, membership, and reconstruction evidence is recorded in the [data recovery report](../phase2b0/DATA_RECOVERY_REPORT.md) and [provenance manifest](../phase2b0/DATA_PROVENANCE_MANIFEST.json).

## Methodology and frozen protocol

Low DO was defined before the experiment as ground-truth DO `< 4 mg/L`; predicted low DO uses the same strict threshold. The development study used nested site-grouped cross-validation: five outer folds for procedure evaluation and four inner folds for configuration selection. A station could not appear in both training and validation within a fold. Data-dependent preprocessing was fitted inside training folds.

The fixed comparison was:

- baseline: the unchanged Random Forest anchor, weight 1;
- candidate procedure: a frozen 128-configuration grid across Random Forest, Extra Trees, and HistGradientBoosting with low-DO weight multipliers 1, 2, 4, or 8;
- selection: 2,560 candidate-fold evaluations across 20 inner folds, applying predeclared qualification and ranking rules;
- uncertainty: paired site-clustered bootstrap, resampling stations rather than rows.

All five outer folds selected HistGradientBoosting with weight 8, with fold-specific non-weight hyperparameters. The historical holdout was registered as a legacy benchmark and was not used for tuning this experiment.

## Results

The pooled out-of-fold results cover every development observation exactly once per procedure.

| Metric | Baseline | Selected weighted procedure | Change |
| --- | ---: | ---: | ---: |
| Overall MAE (mg/L) | 0.8797 | 0.9516 | +0.0719 |
| Low-DO MAE (mg/L) | 3.3235 | 2.3613 | -0.9622 |
| Low-DO bias, prediction − truth (mg/L) | 3.3080 | 2.2373 | -1.0707 |
| Low-DO recall | 0.1293 | 0.3641 | +0.2348 |
| Low-DO precision | 0.7903 | 0.5576 | -0.2327 |
| Low-DO F1 | 0.2222 | 0.4405 | +0.2183 |
| False negatives | 660 | 482 | -178 |
| False positives | 26 | 219 | +193 |

Paired site-bootstrap 95% intervals for weighted-minus-baseline changes were `[0.0643, 0.0794]` for overall MAE, `[-1.0895, -0.8527]` for low-DO MAE, `[-1.1950, -0.9506]` for low-DO bias, `[0.1877, 0.2810]` for recall, and `[-0.3109, -0.1123]` for precision. The frozen decision was therefore **IMPROVEMENT SUPPORTED**, specifically for the selected development procedure and its predeclared low-DO objectives.

These values were independently recomputed during final closeout from the saved `OUTER_CV_PREDICTIONS.csv.gz` (SHA-256 `b779effb1bb1f2d8333d7818b606d566ee52af7a199c8368ec674e2404767697`). The file contained 119,690 unique source IDs for each procedure, identical membership, 672 stations, and no station assigned to more than one outer fold.

## Error and benefit–cost analysis

Low-DO MAE improved at 102 of 115 low-DO stations and worsened at 13. Recall gains occurred at 50 low-DO stations; no station had a net true-positive loss. The benefit was not confined to one station, although the five largest contributors accounted for 37.6% of the total low-DO absolute-error reduction and the ten largest for 56.7%.

The cost was also broad. The 193 additional false positives occurred across 76 stations. Eighty-three had true DO at least 6 mg/L, including 40 at least 8 mg/L, so the increase cannot be described as only threshold-adjacent ambiguity. Total absolute error increased by about 8,602 mg/L across all rows: low-DO rows reduced it by about 729 mg/L, while rows at or above 6 mg/L added about 9,674 mg/L. Predictions shifted modestly downward overall (mean -0.0595 mg/L; median -0.0219 mg/L), with a much larger downward shift for true DO below 2 mg/L.

## Attribution

The formal outer comparison changes both model family/non-weight hyperparameters and weighting, so it does not identify weighting alone. A post hoc analysis reused the already saved inner-grid results and formed 640 exact pairs with identical model family, non-weight parameters, fold membership, preprocessing, and training flow, differing only between weights 1 and 8. The pairs cover Random Forest (160), Extra Trees (160), and HistGradientBoosting (320). Low-DO MAE and recall moved beneficially in all 640 pairs.

This is strong, consistent **exploratory** support for weighting as a contributor when model family and non-weight parameters are held fixed. The matched rows reuse dependent inner folds and are not 640 independent experiments. This is not a preregistered outer-level causal attribution and does not upgrade the main result to external confirmation. No additional diagnostic model was trained for the attribution audit.

## Uncertainty and evidence levels

### Confirmed within development cross-validation

- The selected weighted procedure improved low-DO MAE and recall relative to the frozen baseline under the specified nested site-grouped design.
- It simultaneously worsened overall MAE and precision and generated substantially more false positives.
- Site-clustered intervals support both the benefit and the cost within this development population.

### Exploratory evidence

- Exact matched inner-fold comparisons support weighting as a contributor within architecture- and non-weight-parameter-matched comparisons.
- Error decomposition indicates that most overall degradation occurs at normal-to-high DO values.

### Unresolved

- An acceptable operational exchange rate among missed low-DO events, false alarms, and general regression error has not been specified.
- Performance under new regions, monitoring practices, instruments, or climate regimes is unknown.
- Remaining false-negative rate is 0.6359: most low-DO observations are still missed.

### Requires independent external validation

- Any claim of real-world warning reliability, transport beyond Northern Ireland, or stable benefit under a new data-generating process.
- Any deployment threshold, decision cost, or intervention policy.

Development bootstrap intervals quantify uncertainty under the observed station structure; they are not guarantees of deployment reliability.

## Leakage and integrity audit

No confirmed target-column leakage or use of validation/test statistics in imputation, scaling, or feature preprocessing was found in the upgraded experiment. Target and target qualifier are excluded from predictors, station groups are isolated, and saved identities are unique. A genuine historical evidence limitation remains: prior model development and analysis had already inspected historical test outcomes, including failure and permutation-importance analyses. Those test sets remain legacy benchmarks and cannot be relabelled as new independent confirmation.

## Reproducibility

The frozen configuration, fold membership, selected configurations, inner results, outer predictions, bootstrap replicates, source code, tests, and file hashes are retained under `research_upgrade_v3/`. Final closeout ran 88 repository tests successfully; 34 targeted upgrade tests were also run separately. Unit tests include synthetic model fits, but no new research model, candidate search, or research prediction artifact was created during closeout.

Full reproduction requires the public source export or the exact ignored local raw file. The recovery script verifies its hash before installation. Historical and upgraded outputs are separate and no prior result was overwritten.

## Final scientific conclusion

The study demonstrates a real, reproducible development-set trade-off: a frozen low-DO-weighted selection procedure substantially reduces low-DO error and increases recall across many stations, but worsens overall MAE, lowers precision, and increases false alarms. The formal result supports the procedure, while the claim that weighting itself caused the whole improvement remains exploratory because the outer baseline also differs in architecture.

This is a scientifically useful negative-and-positive result about subgroup reliability and objective trade-offs. It does **not** establish environmental-warning deployment readiness. Without a genuinely new external confirmation set and an application-defined error-cost policy, model development should stop at this evidence level.
