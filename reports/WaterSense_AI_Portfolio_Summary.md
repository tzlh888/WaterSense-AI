# Project Overview

WaterSense AI is an educational environmental machine-learning project that estimates contemporaneously measured dissolved oxygen from river-monitoring chemistry data. Its central question is whether models trained on historical measurements can generalise to monitoring stations they have never seen before.

The project was designed as a complete data-science workflow: dataset selection, provenance checking, exploratory analysis, preprocessing, baseline modelling, group-aware validation, feature comparison, modest refinement, error analysis and explainability. It deliberately avoids presenting the model as a water-safety system, regulatory tool or future river forecast.

# Problem

Dissolved oxygen is an important environmental measurement, but its relationship with other water measurements is complex. A machine-learning model may identify useful predictive patterns among chemistry variables, yet environmental monitoring data introduce difficult methodological problems. The same stations are sampled repeatedly, many measurements are missing, laboratory results can be reported below detection or quantification limits, and unusual values cannot automatically be assumed to be errors.

The resulting research question was:

> Can machine-learning models estimate contemporaneously measured dissolved oxygen from physicochemical river-monitoring variables at previously unseen monitoring stations?

# Data

I used the Northern Ireland Environment Agency’s **River Water Quality Monitoring 1990 to 2024 — All Parameters** dataset. The official export contains 178,680 observations, 40 columns and 1,311 monitoring stations. After removing rows without a usable dissolved-oxygen target, 151,031 observations from 840 stations remained for modelling.

The data include BOD, ammonia, nitrite, nitrate, soluble reactive phosphorus, pH, alkalinity, conductivity and suspended solids. They also contain qualifier fields marking some values as below or above reported limits. The raw file remained unchanged, and a checksum was recorded for reproducibility.

# What I Built

I built reusable scikit-learn preprocessing and modelling pipelines. Missing numeric measurements use median imputation and missingness indicators fitted only on training data. Censored predictor values remain available with explicit below-limit and above-limit flags; I did not assume that half the reporting limit represented the true value.

The modelling work compared Dummy, Linear Regression, Decision Tree, Random Forest and HistGradientBoosting regressors. Phase 4 evaluated four planned feature sets: core chemistry, extended chemistry, core plus temporal context, and extended plus temporal context. Temporal context was represented with cyclical day-of-year features rather than arbitrary date identifiers.

# Key Technical Decisions

The most important decision was to validate by monitoring station. A random row split could place repeated observations from one station in both training and test data, allowing the model to benefit from site-specific similarities. The final holdout therefore contained 31,341 observations from 168 stations entirely absent from training.

Feature and model selection used five-fold `GroupKFold` only within the 672 training stations. The final holdout remained sealed during this process. Every fold refitted imputation and scaling using only fold-training rows.

The parameter search was intentionally modest: three Random Forest and four HistGradientBoosting configurations. This limited computational expense and reduced the risk of repeatedly adapting the experiment to validation noise.

# Results

The Phase 3 core-feature Random Forest produced holdout MAE 1.181 mg/L, RMSE 1.644 mg/L and R² 0.253. In Phase 4, extended chemistry plus temporal context performed best in training-only feature comparison. The final selected model was a Random Forest with 150 trees, `min_samples_leaf=2` and `max_features=0.8`.

Its five-fold station-grouped CV MAE was 0.880 ± 0.035 mg/L. On the untouched 168-station holdout, it achieved:

- MAE: 0.831 mg/L
- RMSE: 1.291 mg/L
- R²: 0.539

This reduced MAE by 0.350 mg/L, or 29.6%, relative to the Phase 3 model on the same test set. The gain combines feature development and modest model refinement rather than tuning alone.

The most important error finding was that overall MAE concealed much poorer performance at the target extremes. The lowest 10% of observed DO values had MAE 1.812 mg/L and 89.964% were overpredicted. The highest 10% had MAE 1.396 mg/L and 94.831% were underpredicted. The model therefore compresses unusual values toward the middle.

Permutation importance identified cyclical day-of-year context, pH and alkalinity as major predictive inputs. These results describe how the model used the available data; they do not demonstrate environmental causation.

# What I Learned

The project showed me that validation design can be more important than choosing a complicated algorithm. Grouping by station changed the question from “Can the model reproduce random records?” to “Can it transfer to locations it has not seen?” I also learned that one overall metric can hide important failure regions, and that a model should be investigated where its errors matter rather than judged only by an average.

Working with censored and missing measurements reinforced that preprocessing decisions encode scientific assumptions. Preserving qualifier information was more defensible than silently treating every reported limit as an exact concentration.

# Limitations

Water temperature, flow and other physical conditions important to dissolved oxygen are unavailable. The data cover Northern Ireland rivers only, span decades with possible method changes, and contain missing, censored and unverified extreme observations. The model estimates a contemporaneous measurement; it does not forecast future conditions, determine water safety or provide causal explanations. Empirical error percentiles are descriptive rather than formal prediction intervals.

# Future Work

Useful next steps would include adding compatible temperature or flow measurements, evaluating external geographic transfer, investigating methods designed specifically for extreme DO behaviour, and building a constrained educational interface that presents predictions alongside validation context and limitations. Further work should avoid repeated optimisation against the existing final holdout.

AI-assisted coding tools were used during implementation and debugging. The project’s design, validation choices, scientific interpretation and documentation were reviewed and directed by the project author.
