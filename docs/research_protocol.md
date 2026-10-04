# Generalization research protocol

This upgrade reuses the existing NIEA cleaning function and Phase 4 preprocessing.
It refits fixed Random Forests for retrospective research, saving everything under
`research_outputs/`. Original models, raw/processed files and Phase 3/4 results are
hashed before/after the run and left unchanged. The existing estimator keeps its model.

## Protocol fixed before the full run

- Target/group/date/feature definitions: `src/research_config.py`.
- Random Forest: 150 trees, unlimited depth, minimum leaf size 2,
  max_features 0.8, seed 42; same settings across experiments. No new tuning.
- Random rows: 80% train / 20% test, seed 42.
- Station groups: existing GroupShuffleSplit, 80% stations / 20% stations, seed 42.
- Time: train through 2018, calibration 2019–2021, final test 2022–2024.
  There is no refit after calibration. The middle period is not used for selection.
- Ablation: six core measurements; core plus censor/missingness indicators;
  core plus cyclical date without indicators; full supported 25 raw inputs.
  Imputation/scaling is reused; only `add_indicator` is disabled for the two
  explicitly indicator-free configurations. The full transformation matches Phase 4.
- Five grouped folds inside the training stations for every ablation.
  Minimum mean CV MAE defines the descriptive best configuration. No artifact is replaced.
- Residuals: actual minus predicted. DO bins: <4, 4–<8, 8–<12, ≥12 mg/L;
  these are descriptive, not environmental standards.
- Station rankings require at least 20 test observations. This threshold suppresses
  the smallest samples but does not make station error estimates equally precise.
- Permutation importance: 5 repeats, fixed sample of up to 5,000 grouped-test rows,
  MAE scoring; no test-driven feature removal or retuning.
- Interval calibration: rank `ceil((n+1)*0.9)` of absolute calibration residuals;
  prediction ± radius. For station calibration, reserve 20% of training stations
  before fitting a separate research model. For time, reuse the pre-2019 model.
  Final test residuals never set the interval width. Widths are not transferred
  to the differently fitted Streamlit estimator.
- Shift summaries: six highest permutation-ranked inputs, median/IQR/mean/SD,
  missing fraction, and signed test-minus-train standardized mean difference.

## Scientific boundaries

### Spatiotemporal addition (fixed before evaluating the new test)

The original three experiments are unchanged. Inspection found 502 stations with
at least one retained observation in both <=2021 and >=2022, 332 historical-only
stations, and 6 future-only stations. Future-observed station counts range from
1 to 36 records; station sampling is irregular. Eligibility requires presence in
both periods, with no outcome-based or additional count filtering. This answers
transfer to continuing stations excluded from fitting, not newly appearing sites.

Sort eligible station IDs, then use sklearn train_test_split with test_size=0.2
and random_state=42 (ceil to 101 held-out stations). Train on all <=2021 records
outside these stations, including historical-only sites. Test on >=2022 records
at held-out stations. Record every station's inventory and every row's role,
including unused held-out history and unused other-station future observations.
Assert row separation, zero train/test station overlap, and strict date ordering.
Fit the existing full pipeline only on training rows. No retuning or feature
selection; no intervals for this new point-only experiment. Its historical window
includes 2019–2021, unlike the unchanged temporal model's calibration reservation.

Reuse verified original scores/predictions and the existing top-six importance
ranking for descriptive summaries only. Compare all four test target distributions
with unchanged DO bins (<4, 4–<8, 8–<12, >=12). Flag bins with n<20, retaining them
in all metrics. Reuse pooled-SD standardized mean differences and median/IQR.
Single-seed station selection, continuing-site eligibility, unequal sample sizes,
different training horizons and correlated spatial/temporal shifts limit inference.
Results remain Northern Ireland-specific and descriptive, not causal or universal.

Standalone reproduction fits only the new model and verifies baseline checksums:

```bash
python scripts/run_research_experiments.py --experiment spatiotemporal --output research_runs/spatiotemporal-reproduction
```

One-time release integration explicitly targets `--output research_outputs`; it
refuses an already-present spatiotemporal result. Only the combined validation
table/chart/report and manifest may change. The manifest retains prior provenance,
original output hashes and new source hashes in an extension record, and verifies
all unrelated outputs unchanged. The `all` option includes the new experiment.

Station-disjoint splitting is not distance-blocked or catchment-disjoint validation.
Future-year evaluation is contemporaneous estimation with chemistry measured in
those years, not a forecast made years beforehand. Station identities may overlap
in temporal evaluation. These tests answer different generalization questions.

Phase 4 already selected the model settings using all-year grouped folds and
already evaluated its holdout. This study freezes that prior choice. Training
preprocessing in each new fit never sees validation/test rows, but the complete
historical selection process was not time-isolated. Treat all comparisons as
retrospective, descriptive evidence rather than untouched confirmatory validation.

Conformal-style residual calibration follows the finite-sample rank construction
in [Angelopoulos and Bates](https://arxiv.org/abs/2107.07511). Repeated observations
and temporal drift challenge exchangeability; no universal or station-conditional
coverage guarantee is claimed. Overall coverage can conceal poor extreme-DO coverage.

Errors are weighted by observations unless stated otherwise. Station association
tables use equal-weight stations with n≥20 and descriptive Spearman correlations.
No association, importance score, or split difference establishes causality.

## Reproduction

From the repository root, use Python with `requirements.txt` installed. Obtain the
unchanged raw export described in [dataset.md](dataset.md); it is intentionally
ignored by Git. No network data fetch, model replacement or app-data rebuild occurs.

```bash
python scripts/run_research_experiments.py --experiment all --output research_runs/reproduction
python scripts/run_research_experiments.py --experiment validation
python scripts/run_research_experiments.py --experiment temporal
python scripts/run_research_experiments.py --experiment ablation
python scripts/run_research_experiments.py --experiment error
python scripts/run_research_experiments.py --experiment uncertainty
python scripts/run_research_experiments.py --experiment importance
python scripts/run_research_experiments.py --experiment shift
python scripts/run_research_experiments.py --experiment report --output research_outputs
python scripts/run_research_experiments.py --fast --output research_runs/smoke-new
python -m unittest discover -s tests -v
streamlit run app/app.py
```

Each command runs its prerequisites and reuses identical fits within that invocation.
Full runs default to `research_outputs/`; partial/smoke runs default to ignored
`research_runs/`. Existing nonempty destinations are refused to prevent mixing
incompatible runs. Pass a new `--output` to reproduce a run safely. Smoke mode uses
4% sampled within each year, 12 trees and 3 folds; it is only software verification.

Outputs include machine-readable tables, Markdown tables, 240-DPI figures,
compressed row-level predictions, split membership, a generated report, and a
manifest with source hashes, protected-artifact hashes, package versions and output
checksums. Neither fold SD nor permutation-repeat SD is a confidence interval.
