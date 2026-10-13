# WaterSense Research Protocol Freeze — Phase 2A

**Freeze date:** 2026-10-12  
**Upgrade branch:** `research-upgrade-v3`  
**Frozen baseline HEAD:** `3553b29ff104918b12da8c84d2c9a8c5ed032e18`  
**Scope:** protocol, audit, and evaluation tooling only; no model training, tuning, selection, commit, or push.

## 1. Historical study state

The historical target is dissolved oxygen in mg/L. The saved modelling population contains 151,031 processed rows and 840 stations according to `research_outputs/manifest.json`; the raw export had 178,680 rows, of which 27,643 missing-target rows and six target-qualified rows were excluded. The checkout contains the saved model, predictions, split membership, metrics, reports, and manifests, but `data/raw` and `data/processed` do not contain the raw export or processed modelling table.

The original fixed configuration is seed 42; test fraction 0.2; calibration fraction 0.2; five station-grouped CV folds; Random Forest with 150 trees, minimum leaf size 2, and `max_features=0.8`; temporal boundaries 2018/2021. The exact feature sets and preprocessing rules remain in `research_outputs/manifest.json` and `src/preprocessing.py`. The grouped split has 119,690 training rows/672 stations and 31,341 test rows/168 stations, with zero station overlap and one partition per source ID in the saved split file.

Phase 2A does not alter any of those choices or historical outputs. Important artifact hashes are regenerated in `EVIDENCE_MANIFEST.csv`; generated-output hashes and the evaluation seed are in `RUN_MANIFEST.json`.

## 2. Frozen evaluation definitions

- Low DO positive class: ground-truth DO strictly `< 4 mg/L`.
- Predicted low DO: predicted DO strictly `< 4 mg/L`.
- Bias: prediction minus ground truth. Positive low-DO bias means unsafe overprediction.
- Recall denominator: all ground-truth low-DO rows. Precision denominator: all predicted-low rows. FNR denominator: all ground-truth low-DO rows.
- If predicted positives are zero, precision and F1 are undefined and stored as missing. If actual positives are zero, recall and FNR are undefined.
- Repeated split appearances are not independent observations. The 10-seed file is reported both as dependent appearances and as one row per `source_object_id`, with predictions averaged across appearances.
- Uncertainty uses 2,000 whole-site bootstrap resamples, seed 20261012. Invalid replicate metrics are counted rather than imputed.

## 3. Evidence classes and eligibility

| Evidence/data | Status after freeze | Permitted use |
| --- | --- | --- |
| Original Phase 3 training partition (119,690 rows, 672 stations) | Potential Phase 2B development population, conditional on restoring and hash-verifying row-level data | Nested station-grouped training, tuning, ablation, and internal validation only |
| Original Group-CV validation folds | Results already viewed; legacy developmental evidence | Pipeline checks and historical comparison; not confirmation |
| Station-grouped holdout and Phase 4 reuse | Legacy benchmark; repeatedly inspected and used for error/importance analysis | Descriptive comparison only; never configuration choice |
| Random, temporal, spatiotemporal, repeated-spatiotemporal, basin and calibration evaluations | Legacy benchmarks | Robustness context only; never hyperparameter/model choice |
| Saved prediction tables | Historical derived evidence | Metric reproduction and failure analysis only |
| Future untouched external/prospective sites/events | Not yet acquired or registered | Only possible future confirmatory evidence after preregistration |

No existing test partition may be renamed an independent holdout. If legacy data are folded into future development, their former evaluation status must be retired explicitly and a genuinely untouched confirmation set created first.

## 4. Data and code integrity boundary

The target and its qualifier are excluded from predictor lists. The preprocessing transformer is placed inside each fitted scikit-learn pipeline, so imputation and scaling are learned from the training portion. Saved grouped and spatiotemporal split memberships have no source ID assigned to multiple partitions; the intended test/train station intersections are zero. The spatiotemporal file deliberately places held-out-station history outside training and uses the same held-out sites in the future test.

The Phase 4 holdout was used for permutation importance and has now also been used for low-DO failure analysis. This is test-set reuse/decision contamination, not evidence that target values entered model features or fitted preprocessing. It removes confirmatory status but does not by itself invalidate the saved prediction computation.

The Phase 1 audit found the v2 source/output hashes internally consistent. Four v1 source hashes could not be matched to the current public history, while v1 output hashes remained verifiable. This provenance gap remains open and historical v1 results are preserved rather than rewritten.

## 5. Evidence gaps

1. Raw and processed row-level modelling data are absent, so exact training low-DO prevalence and a fresh end-to-end reconstruction cannot be performed.
2. The original data acquisition URL and raw SHA-256 are recorded in historical metadata, but the raw file itself is unavailable in this checkout.
3. Rare low-DO support is concentrated in few sites/years; site bootstrap cannot manufacture external independence.
4. Saved predictions cannot distinguish genuine extreme events from measurement or provenance errors.
5. A new confirmatory dataset has not been acquired or sealed.

These gaps are blockers for claiming prospective improvement, not invitations to fill values with synthetic data. Synthetic rows are used only in unit tests.

## 6. Change control

Every Phase 2B run must receive a decision-log entry before execution, identify eligible development rows, record split hashes/seeds, state the hypothesis and qualification rule, and write to a new run directory. Legacy metrics must not change candidate selection. Bugs must be logged with before/after behavior; historical files remain immutable. No result may be called confirmatory without a preregistered, previously unseen evaluation population.
