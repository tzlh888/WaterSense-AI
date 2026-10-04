# Project status

**Current phase:** Research development complete — final communication and application packaging.

**Scientific objective:** Evaluate spatial and temporal generalization in dissolved-oxygen prediction, including where aggregate errors conceal poor reliability.

## Completed

- credible government dataset selection and provenance review
- exploratory data analysis
- raw-data preservation and reproducible preprocessing
- explicit handling and documentation of censored measurements
- training-only missing-value imputation
- station-grouped holdout validation
- five-fold station-grouped cross-validation
- random-row, temporal and spatiotemporal comparison with fixed model settings
- separately calibrated residual prediction intervals and subgroup empirical coverage
- reproducible research runner, saved predictions, distribution-shift analysis and checksum verification
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
- a verified public live demo URL (none is claimed in the README)
- regulatory or operational validation
- causal modelling
- prospective or externally validated prediction-interval guarantees
- external geographic validation
- future river-condition forecasting

## Verified current result

The full-feature Random Forest achieved station-grouped five-fold CV MAE **0.8798 ± 0.0353 mg/L** (fold SD). The unseen-station holdout has MAE **0.8312 mg/L**, RMSE **1.2911 mg/L** and R² **0.5391**. This is now a previously inspected retrospective holdout, not a fresh external test.

The completed [research report](../research_outputs/reports/RESEARCH_RESULTS.md) compares random, unseen-station, temporal and spatiotemporal settings. Spatiotemporal MAE is **0.6918 mg/L**, but all **14** observations below 4 mg/L were overpredicted, with MAE **4.7678 mg/L**. This small subgroup is a warning signal, not evidence of universal systematic bias. Separate research prediction intervals also had poorer low-DO coverage; none is attached to the deployed estimator.

Historical Phase 4 lowest-decile observations remain difficult: MAE is **1.812 mg/L** and **89.964%** are overpredicted. This decile is distinct from the research DO <4 mg/L subgroup. The model is an educational research prototype, not a water-safety or regulatory system.

## Potential future work

- add water temperature if a scientifically compatible dataset can be linked
- integrate flow measurements and other physical context
- test external-region generalization with a new untouched dataset
- investigate models or objectives designed for extreme DO behaviour
- investigate calibration under station/time dependence and rare low-DO conditions
- assess external validation and formal uncertainty before considering any operational use
