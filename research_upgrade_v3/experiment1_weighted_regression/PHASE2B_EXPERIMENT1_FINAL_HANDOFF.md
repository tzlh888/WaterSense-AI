# Phase 2B Experiment 1 Final Handoff

## Conclusion: IMPROVEMENT SUPPORTED

The complete frozen 128-candidate grid was evaluated in all 20 inner folds (2,560 candidate-fold evaluations). One qualified configuration was selected independently inside each outer-training partition, then compared with the unchanged RF anchor on the corresponding held-out stations. No legacy benchmark outcome was read or used.

Selected configurations:

- Outer 1: `HistGradientBoostingRegressor__learning_rate=0.07__max_leaf_nodes=31__min_samples_leaf=50__l2_regularization=0__weight=8`
- Outer 2: `HistGradientBoostingRegressor__learning_rate=0.07__max_leaf_nodes=31__min_samples_leaf=50__l2_regularization=1__weight=8`
- Outer 3: `HistGradientBoostingRegressor__learning_rate=0.07__max_leaf_nodes=31__min_samples_leaf=50__l2_regularization=1__weight=8`
- Outer 4: `HistGradientBoostingRegressor__learning_rate=0.07__max_leaf_nodes=15__min_samples_leaf=20__l2_regularization=0__weight=8`
- Outer 5: `HistGradientBoostingRegressor__learning_rate=0.07__max_leaf_nodes=31__min_samples_leaf=50__l2_regularization=0__weight=8`

## Pooled outer out-of-fold comparison

| Metric | Baseline | Selected weighted procedure | Delta (weighted - baseline) | Paired site-bootstrap 95% CI for delta |
| --- | ---: | ---: | ---: | ---: |
| Overall MAE (mg/L) | 0.8797 | 0.9516 | 0.0719 | [0.0643, 0.0794] |
| Low-DO MAE (mg/L) | 3.3235 | 2.3613 | -0.9622 | [-1.0895, -0.8527] |
| Low-DO bias (mg/L) | 3.3080 | 2.2373 | -1.0707 | [-1.1950, -0.9506] |
| Low-DO recall | 0.1293 | 0.3641 | 0.2348 | [0.1877, 0.2810] |
| Low-DO precision | 0.7903 | 0.5576 | -0.2327 | [-0.3109, -0.1123] |

The frozen decision rule is satisfied: Both co-primary paired 95% intervals exclude zero beneficially. This is nevertheless a documented trade-off. Overall MAE increased, precision declined, and false positives rose from 26 to 219, even though Low-DO MAE, bias, recall, F1 and false-negative rate improved. Detailed station attribution and prediction-shift analyses are retained in `SITE_ERROR_COMPARISON.csv` and `PREDICTION_SHIFT_ANALYSIS.csv`.

This conclusion is development-only nested-CV evidence. It is not external confirmation, and it does not authorize Experiment 2. No historical output was overwritten, and no Git commit or push was performed.
