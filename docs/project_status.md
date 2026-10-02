# Project status

**Current phase:** Phase 7 — public-release and deployment preparation  
**Scientific objective:** Estimate contemporaneously measured dissolved oxygen from physicochemical river-monitoring variables at previously unseen monitoring stations.

## Completed

- credible government dataset selection and provenance review
- exploratory data analysis
- raw-data preservation and reproducible preprocessing
- explicit handling and documentation of censored measurements
- training-only missing-value imputation
- station-grouped holdout validation
- five-fold station-grouped cross-validation
- baseline regression modelling
- scientifically bounded feature-set refinement
- modest Random Forest and HistGradientBoosting comparison/tuning
- target-range, station and temporal error analysis
- held-out permutation importance and partial dependence
- academic report, portfolio summaries and interview preparation
- local Streamlit application with data exploration, saved-model estimation, validation results and limitations
- tested input-to-feature transformation matching the verified Phase 4 model contract
- application data contract and local run instructions
- responsive UI review at desktop, laptop and mobile-like widths
- reproducible lightweight public app data and Git LFS model packaging
- deployment guide, release audit, screenshots and final portfolio assets

## Not completed

- production deployment
- public GitHub repository and live URL
- regulatory or operational validation
- causal modelling
- formal prediction-interval or uncertainty modelling
- external geographic validation
- future river-condition forecasting

## Verified current result

The selected extended-plus-temporal Random Forest achieved training-only group-CV MAE **0.880 ± 0.035 mg/L** and final untouched 168-station holdout MAE **0.831 mg/L**, RMSE **1.291 mg/L** and R² **0.539**.

Lowest-decile observations remain difficult: MAE is **1.812 mg/L** and **89.964%** are overpredicted. The model is an educational research prototype, not a water-safety or regulatory system.

## Potential future work

- add water temperature if a scientifically compatible dataset can be linked
- integrate flow measurements and other physical context
- test external-region generalisation with a new untouched dataset
- investigate models or objectives designed for extreme DO behaviour
- develop formal, justified uncertainty estimates
- assess external validation and formal uncertainty before considering any operational use
