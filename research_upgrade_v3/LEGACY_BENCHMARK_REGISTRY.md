# WaterSense Legacy Benchmark Registry

All entries below have had outcomes inspected by researchers or used in earlier decisions. They are frozen as **legacy evidence** on 2026-10-12 and cannot be used to select Phase 2B configurations.

| Registry ID | Population / artifact | Historical purpose and exposure | Current status |
| --- | --- | --- | --- |
| WS-LB-01 | Phase 3 random row holdout; `results/baseline_results.csv`, `research_outputs/predictions/random.csv.gz` | Baseline comparison; metrics viewed | Legacy exploratory benchmark; row mixing limits spatial claims |
| WS-LB-02 | Fixed station-grouped holdout; split seed 42, 31,341 rows/168 sites; `results/phase4_holdout_predictions.csv`, `research_outputs/predictions/grouped.csv.gz` | Phase 3 evaluation, Phase 4 final evaluation, test-set permutation importance, repeated reporting, Phase 2A failure analysis | Legacy benchmark only; not independent or sealed |
| WS-LB-03 | Five station-grouped CV validation folds; `results/group_cv_results.csv`, `research_outputs/tables/group_cv_results.csv` | Model/feature comparison and historical selection | Legacy development evidence; cannot select new v3 configuration |
| WS-LB-04 | Temporal holdouts and calibration; `research_outputs/predictions/temporal.csv.gz`, `temporal_calibration.csv.gz` | Later-period sensitivity and uncertainty analysis | Legacy robustness evidence |
| WS-LB-05 | Seed-42 continuing-station spatiotemporal holdout; `research_outputs/predictions/spatiotemporal.csv.gz` | Future observations at held-out sites; result viewed | Legacy robustness evidence; only 14 low-DO rows/6 low-DO sites |
| WS-LB-06 | Ten repeated spatiotemporal partitions; seeds 11, 23, 42, 57, 71, 89, 101, 123, 149, 173; `research_outputs_v2/predictions/repeated_spatiotemporal_predictions.csv.gz` | Partition sensitivity; all outcomes viewed | Legacy robustness evidence; 19,396 appearances are 8,607 unique source IDs; 129 low-DO appearances are 56 unique low-DO IDs at 20 sites |
| WS-LB-07 | Basin-group holdout; `research_outputs_v2/predictions/spatial_basin_predictions.csv.gz` | Spatial robustness by named basin | Legacy robustness evidence; basin metadata missing for six sites in the historical experiment |
| WS-LB-08 | Station and temporal calibration partitions plus saved prediction intervals | Empirical residual-interval analysis | Legacy calibration evidence; not an exchangeability guarantee |
| WS-LB-09 | Model-family and ablation comparisons in v1/v2 reports/tables | Retrospective model and feature comparisons | Legacy exploratory evidence; may motivate hypotheses but not select Phase 2B winners |

## Governance rule

Phase 2B code may print these benchmarks only after a candidate and all hyperparameters are frozen from eligible development data. A legacy result cannot trigger a new candidate, feature, weight, threshold, stopping rule, or narrative of confirmation. Reusing a legacy row in training permanently retires it as an evaluation row and must be logged.
