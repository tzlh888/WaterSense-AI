# WaterSense AI — One-Page Summary

WaterSense AI is an educational machine-learning study of long-term river-monitoring data. It asks whether physicochemical measurements can estimate **contemporaneously measured dissolved oxygen at monitoring stations not seen during training**. It is not a drinking-water safety classifier, regulatory system or future pollution forecast.

The project uses the Northern Ireland Environment Agency’s *River Water Quality Monitoring 1990 to 2024 — All Parameters* dataset. The official export contains 178,680 observations from 1,311 stations. After excluding missing and six censored dissolved-oxygen targets, 151,031 observations from 840 stations remained.

I investigated dataset provenance, units, missingness, reporting-limit qualifiers, extreme observations and leakage risk. Censored predictor measurements were retained with explicit qualifier indicators rather than silently treated as exact values or replaced with half the reporting limit. Missing predictors were median-imputed inside scikit-learn pipelines using training data only. Station and location identifiers were excluded from predictors.

The project compared Dummy, Linear Regression, Decision Tree, Random Forest and HistGradientBoosting models. Validation was grouped by `StationCode` because repeated measurements from the same location are statistically related. The final holdout contained 31,341 observations from 168 stations absent from training, with zero station overlap. All feature and parameter choices used five-fold group cross-validation within the training stations.

The selected model was a Random Forest using extended chemistry and cyclical day-of-year context. It achieved group-CV MAE **0.880 ± 0.035 mg/L** and untouched station-holdout MAE **0.831 mg/L**, RMSE **1.291 mg/L** and R² **0.539**. Holdout MAE was 29.6% lower than the Phase 3 core-feature baseline.

The most important finding was not simply the improved average score. The model continued to regress extreme observations toward the middle: the lowest 10% of DO values had MAE 1.812 mg/L and 89.964% were overpredicted, while the highest 10% had MAE 1.396 mg/L and 94.831% were underpredicted. This showed why error analysis is necessary even when overall performance improves.

The strongest limitation is missing physical context, especially water temperature and flow. Consequently, the project demonstrates a reproducible, leakage-aware machine-learning workflow and meaningful predictive associations, but it does not provide causal conclusions, future forecasts or regulatory water assessments. The result is best understood as a carefully bounded research prototype.
