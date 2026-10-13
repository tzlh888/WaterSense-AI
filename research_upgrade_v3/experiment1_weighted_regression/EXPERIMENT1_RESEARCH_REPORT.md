# Experiment 1 Research Report

## Conclusion: IMPROVEMENT SUPPORTED

This is nested-CV development evidence, not external confirmation. Reasons: Both co-primary paired 95% intervals exclude zero beneficially.

## Frozen execution

The exact 119,690-row/672-site development partition and frozen 5×4 site-grouped folds were used. All preprocessing and weights were fitted/computed inside the applicable training fold. The 128-candidate grid was evaluated once in every inner fold; legacy benchmark outcomes were not read.

Outer-selected configurations:

- Outer 1: `HistGradientBoostingRegressor__learning_rate=0.07__max_leaf_nodes=31__min_samples_leaf=50__l2_regularization=0__weight=8`
- Outer 2: `HistGradientBoostingRegressor__learning_rate=0.07__max_leaf_nodes=31__min_samples_leaf=50__l2_regularization=1__weight=8`
- Outer 3: `HistGradientBoostingRegressor__learning_rate=0.07__max_leaf_nodes=31__min_samples_leaf=50__l2_regularization=1__weight=8`
- Outer 4: `HistGradientBoostingRegressor__learning_rate=0.07__max_leaf_nodes=15__min_samples_leaf=20__l2_regularization=0__weight=8`
- Outer 5: `HistGradientBoostingRegressor__learning_rate=0.07__max_leaf_nodes=31__min_samples_leaf=50__l2_regularization=0__weight=8`

## Pooled outer out-of-fold results

| Metric | Baseline | Selected procedure | Delta (weighted − baseline) | Paired 95% CI for delta |
| --- | ---: | ---: | ---: | ---: |
| Overall MAE | 0.8797 | 0.9516 | 0.0719 | [0.0643, 0.0794] |
| Low-DO MAE | 3.3235 | 2.3613 | -0.9622 | [-1.0895, -0.8527] |
| Low-DO Bias | 3.3080 | 2.2373 | -1.0707 | [-1.1950, -0.9506] |
| Recall | 0.1293 | 0.3641 | 0.2348 | [0.1877, 0.2810] |
| Precision | 0.7903 | 0.5576 | -0.2327 | [-0.3109, -0.1123] |
| F1 | 0.2222 | 0.4405 | 0.2183 | [0.1776, 0.2621] |
| False-positive rate | 0.000219 | 0.001841 | 0.001623 | [0.001158, 0.002154] |
| False positives | 26 | 219 | 193 | not bootstrapped as a scale-dependent count |

## Trade-offs and distribution shift

Overall MAE increased by 8.17%, inside but close to the frozen 10% guard. False positives increased from 26 to 219; Precision declined from 0.7903 to 0.5576, while remaining above the 0.30 qualification floor. The false-positive-rate increase has a paired 95% interval [0.001158, 0.002154].

Across all rows, the selected procedure shifted predictions by a mean -0.0595 mg/L and median -0.0219 mg/L; 52.5% of predictions moved downward. This is not a uniform global shift. For actual DO `<2 mg/L`, positive bias fell from 3.6571 to 2.2647 mg/L, but remained materially positive; the extreme tail is improved, not solved.

## Station-level attribution

The selected procedure changed low-DO MAE in 102 of 115 low-DO sites beneficially and 13 adversely. The five largest positive station contributions account for 30.6% of total positive absolute-error reduction and the largest ten for 49.8%; improvement is distributed beyond a handful of sites, but remains concentrated enough to report explicitly.

## Largest station-level Low-DO MAE reductions

| station_code | low_do_rows | baseline_low_do_mae_mg_l | weighted_low_do_mae_mg_l | total_low_do_absolute_error_reduction_mg_l |
| --- | --- | --- | --- | --- |
| UKGBNIF10910 | 65 | 2.327452 | 1.525456 | 52.129772 |
| UKGBNIF10523 | 37 | 3.755083 | 2.367913 | 51.325278 |
| UKGBNIF10936 | 57 | 4.664121 | 3.854147 | 46.168558 |
| UKGBNIF10337 | 46 | 2.410479 | 1.523184 | 40.815558 |
| UKGBNIF10545 | 21 | 3.100788 | 1.416648 | 35.366940 |
| UKGBNIF10102 | 35 | 4.540447 | 3.556430 | 34.440614 |
| UKGBNIF11293 | 18 | 3.774301 | 2.049164 | 31.052470 |
| UKGBNIF10338 | 37 | 1.669712 | 0.950152 | 26.623748 |
| UKGBNIF10626 | 23 | 2.820673 | 1.689519 | 26.016553 |
| UKGBNIF10451 | 22 | 3.557653 | 2.502851 | 23.205651 |

## Largest adverse station-level changes

| station_code | low_do_rows | baseline_low_do_mae_mg_l | weighted_low_do_mae_mg_l | total_low_do_absolute_error_reduction_mg_l |
| --- | --- | --- | --- | --- |
| UKGBNIF10477 | 1 | 3.463890 | 5.342713 | -1.878823 |
| UKGBNIF10586 | 1 | 3.000580 | 4.109933 | -1.109353 |
| UKGBNIF10328 | 1 | 4.178135 | 4.872498 | -0.694363 |
| UKGBNIF10512 | 2 | 5.410030 | 5.743011 | -0.665962 |
| UKGBNIF10384 | 1 | 3.279947 | 3.859071 | -0.579124 |
| UKGBNIF10582 | 1 | 2.992194 | 3.466507 | -0.474312 |
| UKGBNIF10129 | 1 | 5.453939 | 5.917077 | -0.463138 |
| UKGBNIF10135 | 1 | 5.413657 | 5.852499 | -0.438842 |
| UKGBNIF10287 | 1 | 9.225211 | 9.633464 | -0.408253 |
| UKGBNIF10703 | 2 | 2.451570 | 2.615153 | -0.327166 |

## Interpretation boundary

The weighted label denotes the complete inner-selected procedure; selected model family, hyperparameters and multiplier may differ by outer fold. A multiplier of one is an eligible unweighted candidate under the frozen grid and is not relabelled as a weighting success. Site bootstrap resamples entire outer-validation stations. It does not make repeated observations independent or create an unseen test set.
