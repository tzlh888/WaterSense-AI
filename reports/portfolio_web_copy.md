# WaterSense AI — Portfolio Website Copy

Historical Phase 4/7 copy. For the completed spatial/temporal study and current application wording, use [application materials](../docs/application_materials.md) and the [research report](../research_outputs/reports/RESEARCH_RESULTS.md). The earlier results below are preserved as development history.

## Project title

WaterSense AI

## Short subtitle

Leakage-aware dissolved-oxygen estimation from long-term river-monitoring data

## 50-word summary

WaterSense AI is an educational environmental machine-learning project using 151,031 Northern Ireland river-monitoring observations. I replaced an unsupported risk-classification idea with continuous dissolved-oxygen regression, designed station-grouped validation, built a Random Forest pipeline, analysed its extreme-value errors and created a transparent Streamlit interface around the verified model.

## 100-word summary

WaterSense AI investigates whether physicochemical monitoring measurements can estimate contemporaneous dissolved oxygen at previously unseen river stations. The project uses an official NIEA/DAERA dataset covering 1990–2024. I audited missingness and reporting-limit censoring, rejected unsupported Safe/Unsafe labels, and kept complete stations separate during validation. A Random Forest selected through training-only GroupKFold achieved 0.831 mg/L MAE on 31,341 observations from 168 held-out stations. Error analysis showed systematic regression toward the middle at low and high dissolved oxygen. A five-page Streamlit application exposes the dataset, estimator, validation evidence and scientific limitations without presenting the result as safety or regulatory advice.

## Key technologies

Python, pandas, NumPy, scikit-learn, Streamlit, Plotly, Joblib, Jupyter

## Key result

Random Forest holdout MAE: 0.831 mg/L on 168 stations absent from training, with zero station overlap.

## Main challenge

Repeated station measurements, censoring and missingness required an explicit validation question. Random rows test familiar-site interpolation rather than unseen-station transfer; the later measured comparison did not show lower random-split MAE.

## Main insight

A defensible target and leakage-aware evaluation mattered more than preserving the initial classification idea. Overall MAE also concealed much larger errors at dissolved-oxygen extremes.

## Limitations

No water temperature or flow data; Northern Ireland rivers only; contemporaneous estimation rather than forecasting; no causal, safety or regulatory validation; weaker performance at target extremes.

## Calls to action

- [GitHub Repository]
- [Live Demo]
