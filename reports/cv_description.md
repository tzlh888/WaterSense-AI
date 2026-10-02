# WaterSense AI — Machine-Learning Environmental Data Project

## Final recommended version

- Audited and prepared 151,031 modelling observations from an official 1990–2024 Northern Ireland river-monitoring dataset, preserving missingness and laboratory reporting-limit information.
- Designed zero-overlap station-grouped validation and selected a Random Forest through training-only GroupKFold, achieving 0.831 mg/L MAE on 168 unseen stations.
- Built a Streamlit research interface and documented systematic overprediction at low dissolved oxygen and underprediction at high values rather than hiding extreme-region errors.
