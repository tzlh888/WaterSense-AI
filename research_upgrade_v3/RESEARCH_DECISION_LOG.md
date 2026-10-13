# WaterSense Research Decision Log

Append entries; do not rewrite prior decisions. Proposed Phase 2B runs require an entry before execution.

| Date | ID | Decision / hypothesis | Evidence and selection rule | Outcome / status |
| --- | --- | --- | --- | --- |
| 2026-10-12 | WS-D-001 | Freeze baseline at `3553b29ff104918b12da8c84d2c9a8c5ed032e18` on branch `research-upgrade-v3`. | Clean `main`; historical artifacts retained. | Complete; no commit or push. |
| 2026-10-12 | WS-D-002 | Define low DO and predicted low DO as strictly `<4 mg/L`; define bias as prediction minus truth. | Domain threshold in Phase 2A brief; ambiguity removed in code/tests. | Frozen. |
| 2026-10-12 | WS-D-003 | Use whole-site, not row, bootstrap; 2,000 resamples; seed 20261012; percentile 95% CI. | Repeated measurements within stations are dependent. | Implemented; invalid resamples counted. |
| 2026-10-12 | WS-D-004 | Treat 10-seed predictions as dependent appearances and add an observation-level mean-prediction view. | 19,396 appearances map to 8,607 source IDs; 129 low-DO appearances map to 56 IDs/20 sites. | Implemented; neither view is called independent confirmation. |
| 2026-10-12 | WS-D-005 | Preserve historical outputs and add corrected sign-explicit bias metrics in v3 only. | Historical residual fields use `actual − predicted`; Phase 2A requires `prediction − truth`. | Implemented without editing old files. |
| 2026-10-12 | WS-D-006 | Do not train Phase 2B models in this phase. | Raw/processed modelling table absent; protocol must precede fitting. | Enforced. |
| 2026-10-12 | WS-D-007 | Prioritise Low-DO Weighted Regression as the first Phase 2B experiment, conditional on data restoration. | Smallest intervention directly tests rare-regime underweighting while retaining continuous prediction. | Proposed, not executed. |
| 2026-10-12 | WS-D-008 | Execute Phase 2B Experiment 1 once under the Phase 2B-0 frozen 128-candidate grid and 5×4 nested site folds. | Eligible input `5685c2...1761`; site split `0fa76b...8025`; seed 20261012; config canonical hash `39d126...0896`; legacy benchmarks prohibited. Selection and conclusion rules below were recorded before model results. | Registered for execution; development-only evidence. |

## WS-D-008 execution detail — recorded before fitting

- **Decision owner:** Senior ML Research Engineer / independent audit execution.
- **Hypothesis:** fold-local loss weighting for training observations with true DO `<4 mg/L` may reduce low-DO overprediction and false negatives without unacceptable overall MAE degradation.
- **Eligible data:** exact historical development partition only, 119,690 rows/672 stations; processed SHA-256 `5685c2c352b1cc9502cd664736d85295580127016fb60bdca45c082c5d031761`.
- **Frozen folds:** site assignment SHA-256 `0fa76b39cd3697aed2b615f5921a2cfa8dbaf0fdbd216393520c25c52bf58025`; outer row hash `d18f55c62e6baab38223c804cc3dbcdf549837560f5984dccda6139d6599b1fd`; inner row hash `7a143df06162994efc65b0fb58770b21a2b49a6371a66ce46a592d7218dcb0b0`.
- **Grid:** exactly the three frozen estimator families, their enumerated hyperparameters, and weight multipliers `{1,2,4,8}`; 128 stable candidate IDs per inner fold. No post-result extension.
- **Baseline:** Random Forest, 150 trees, minimum leaf 2, max features 0.8, multiplier 1, refitted on the same folds with Phase 2B seed 20261012.
- **Selection:** pooled inner qualification followed by the frozen lexicographic order: mean fold Low-DO Recall, mean fold Low-DO MAE, mean fold Overall MAE, preregistered complexity score, stable candidate ID.
- **Conclusion rule:** `IMPROVEMENT SUPPORTED` requires both paired whole-site 95% intervals to exclude zero beneficially for Recall and Low-DO MAE, pooled Overall MAE within the 10% guard, pooled Precision at least 0.30, and at least one selected multiplier above one. Neither co-primary point estimate improving yields `NO SUPPORTED IMPROVEMENT`; all mixed, costly, or interval-crossing outcomes yield `TRADE-OFF / INCONCLUSIVE`; absence of any qualified candidate yields `NO QUALIFIED MODEL`.
- **Stopping:** complete the fixed grid once, retain failures, stop after Experiment 1, and do not run legacy evaluation or Experiment 2.
- **Output:** `research_upgrade_v3/experiment1_weighted_regression/` with identity-checked per-fold checkpoints.

## Required fields for future entries

Record: timestamp; decision owner; research hypothesis; eligible input hash; outer/inner split hashes; seed; candidate/search space; primary/secondary metrics; qualification constraints; stopping rule; result directory; failures; and whether the conclusion is exploratory or confirmatory.

## WS-D-009 Experiment 1 outcome — recorded after the frozen run

- **Execution completeness:** all 2,560 preregistered candidate-fold evaluations completed (128 candidates × 20 inner folds); no candidate failures; all five outer folds produced a qualified selection. Every selected procedure used HistGradientBoostingRegressor with weight multiplier 8; configuration details remain fold-specific in `experiment1_weighted_regression/INNER_CV_SELECTION.csv`.
- **Pooled outer OOF result:** baseline versus selected procedure Overall MAE was 0.8797 versus 0.9516 mg/L; Low-DO MAE 3.3235 versus 2.3613 mg/L; Low-DO bias +3.3080 versus +2.2373 mg/L; Recall 0.1293 versus 0.3641; Precision 0.7903 versus 0.5576; F1 0.2222 versus 0.4405; false positives 26 versus 219.
- **Paired whole-site uncertainty:** weighted-minus-baseline Low-DO MAE delta 95% CI `[-1.0895, -0.8527]`; Recall delta `[0.1877, 0.2810]`; Overall MAE delta `[0.0643, 0.0794]`; Precision delta `[-0.3109, -0.1123]`.
- **Frozen-rule conclusion:** `IMPROVEMENT SUPPORTED`. Both co-primary intervals exclude zero in the beneficial direction, the 8.17% Overall MAE increase remains inside the frozen 10% guard, pooled Precision remains above 0.30, and selected multipliers exceed one.
- **Required trade-off interpretation:** this label does not mean every metric improved. Overall MAE and false-positive burden worsened, Precision fell, and substantial positive bias and false-negative burden remain. The evidence is development-only nested-CV evidence, not an external confirmation or deployment claim.
- **Integrity:** no legacy benchmark outcome was read; the grid, folds, thresholds, features, qualification rules and conclusion rule were not changed after observing results. Interrupted execution resumed only from configuration- and file-hash-verified fold checkpoints. Experiment 2 was not started.

## WS-D-010 Experiment 1A attribution audit — recorded after saved-evidence analysis

- **Decision:** do not run a new diagnostic model because the frozen Experiment 1 inner grid already contains 640 exact same-fold, same-architecture, same-nonweight-hyperparameter comparisons of weight 8 versus weight 1 across 32 configurations and 20 inner folds.
- **Formal Experiment 1 boundary:** the outer-CV `IMPROVEMENT SUPPORTED` label remains a conclusion about the complete inner-selected procedure versus the fixed RF anchor. It cannot by itself identify the causal contribution of weighting because estimator family and nonweight hyperparameters differ.
- **Exploratory attribution:** weight 8 reduced Low-DO MAE and increased Recall in all 640 matched inner-fold comparisons. For the five selected HGB configurations, the mean pooled-inner weight-8-minus-weight-1 difference was −0.8879 mg/L Low-DO MAE and +0.2101 Recall, while adding +0.0118 mg/L Overall MAE and lowering Precision by 0.1644. These overlapping inner folds are descriptive evidence, not 640 independent replicates or new confirmation.
- **Benefit–cost finding:** outer predictions show Low-DO MAE improvement at 102/115 low-DO sites and net TP gains at 50/115 sites. The 193 newly introduced false positives span 76 sites; 83 have actual DO `>=6 mg/L`, so the false-positive cost is not confined to threshold-adjacent cases. Most total absolute-error increase comes from actual DO `>=6 mg/L`.
- **Research interpretation:** weighting has strong exploratory support as a contributor to low-DO gains and false-positive cost, but an independent outer-level weight-only effect remains unresolved. Deployment, alert reliability, and application acceptability require an external validation source and a prespecified error-cost standard.
- **Execution:** saved Experiment 1 evidence only; zero models trained or selected; no legacy benchmark read; no AquaVision change; no Experiment 2, commit, or push.
