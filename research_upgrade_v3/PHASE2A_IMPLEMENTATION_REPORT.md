# WaterSense Phase 2A Implementation Report

## Outcome

Phase 2A protocol freezing and saved-prediction analysis are complete on `research-upgrade-v3`. Historical files were not edited. No model was fitted, tuned, selected, committed, or pushed.

## Additions

- `src/low_do_reliability.py`: canonical threshold metrics, repeated-observation aggregation, site-clustered bootstrap, site/error strata, feature associations, validation, and hashing.
- `scripts/run_low_do_reliability.py`: reproducible saved-prediction runner that creates all v3 tables, reports, plots, and manifests.
- `tests/test_low_do_reliability.py`: six synthetic-only tests covering the strict threshold, false negatives, zero predicted positives, deterministic site bootstrap/invalid replicates, unique counting/mean aggregation, and repeated-identity inconsistency.
- `research_upgrade_v3/`: protocol/registry/log, analysis outputs, Phase 2B preregistration, four reproducible figures, and evidence/output manifests.

## Verified numerical result

The station-grouped legacy holdout contains 31,341 rows, 168 sites, 167 true low-DO rows at 31 sites. Overall MAE is 0.8312 mg/L; low-DO MAE 3.1387; RMSE 3.5232; prediction-minus-truth bias +3.1193; recall 0.0838; precision 0.7000; F1 0.1497; FNR 0.9162. The 2,000-resample site bootstrap yields low-DO MAE 95% CI 2.8585–3.4984, bias 2.8242–3.4858, and FNR 0.8750–0.9778. One precision replicate was undefined and is reported as invalid.

The repeated spatiotemporal file has 129 low-DO appearances but 56 unique low-DO source IDs at 20 sites. After per-source mean prediction, low-DO MAE is 3.6628, bias +3.6628, recall 0.0357, and FNR 0.9643. The appearance count is not treated as independent evidence.

## Leakage and reproducibility review

- No target or target qualifier appears in the frozen feature sets.
- Imputation/scaling is encapsulated inside fitted pipelines; historical fitting code applies them per training fold/partition.
- Saved grouped split: 151,031 unique IDs, one partition each, zero train/test station overlap.
- Saved spatiotemporal split: one partition per ID; future test sites are absent from training, while their history is deliberately isolated as `unused_heldout_history`.
- Historical holdout permutation importance used test outcomes after prediction. This is test reuse and destroys confirmation status; it is not a demonstrated feature/preprocessing leakage path.
- Historical residual sign differs from this protocol's requested bias sign. v3 recomputes bias explicitly without changing old files.
- Four v1 source hashes remain unmatched to public history; the evidence gap is retained.

No confirmed target leakage or train/test preprocessing-statistic leakage was found in the inspected code. Full raw-to-result reproduction remains impossible until the missing raw/processed dataset is restored.

## Verification

`python3 -m unittest -v tests.test_low_do_reliability` completed six tests with zero failures. `python3 scripts/run_low_do_reliability.py` completed from repository-relative inputs and performed no training. `RUN_MANIFEST.json` records output hashes, seed, threshold, source paths, and `training_performed: false`.

## Remaining gates

Do not begin Phase 2B training until row-level development data are restored and hash/split checks pass. Do not interpret any legacy score as new independent generalisation evidence. A new confirmatory population is still required.
