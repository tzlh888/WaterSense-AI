# Project log

## 2026-09-30 — Project foundation

**Goal:**  
Begin development of WaterSense AI.

**Initial research question:**  
Can machine-learning models identify meaningful water-quality risk patterns from physicochemical measurements?

**Initial development priorities:**

- establish reproducible project structure
- select a credible dataset
- understand variables and target
- perform EDA
- build baseline machine-learning models
- evaluate model limitations
- later create an interactive application

**Open questions:**

- Which dataset should be used?
- What is the target variable?
- Are any existing risk labels scientifically justified?
- Is classification or regression more appropriate?
- Which evaluation metrics are most important?

**Work completed:**

- Created the repository structure, three staged notebooks, reusable preprocessing, baseline training, evaluation, prediction modules, and unit tests.
- Made target and task selection explicit. The code does not infer scientific meaning from column names or fabricate risk classes.
- Kept preprocessing inside each fitted model pipeline to reduce train/test leakage.
- Added classification and regression paths because the correct task is not known before dataset inspection.

**Current evidence and blockers:**

- No raw dataset was present on 2026-09-30.
- No target variable, model, metric, feature importance, or scientific result can therefore be reported.
- Dataset selection and provenance review are the next required research activities.

## 2026-09-30 — Dataset selection and validation

**Phase:** Dataset Selection and Validation

**Datasets investigated:**

- NIEA River Water Quality Monitoring 1990–2024 — All Parameters
- Environment Agency Water Quality Explorer (England)
- European Environment Agency Waterbase — Water Quality ICM
- NERC EIDC LOCATE monthly river-chemistry dataset
- US EPA National Lakes Assessment 2017

**Dataset selected:**  
NIEA River Water Quality Monitoring 1990–2024 — All Parameters, published by OpenDataNI under the UK Open Government Licence.

**Reason for selection:**  
The dataset has direct government provenance, 178,680 dated sampling records, 1,311 monitoring stations, 35 years of coverage and 13 relevant chemistry measurements. It is large enough for meaningful ML work, but its single wide CSV is more understandable for a student than multi-table continental or national archives. Station, basin, coordinate and date fields also support a coherent spatial/temporal environmental story. The official warning about possible erroneous extremes and the preserved qualifier fields make data-quality decisions visible rather than hiding them.

**Important variables:**

- alkalinity, BOD and conductivity
- dissolved oxygen
- ammonia, nitrite and nitrate
- soluble reactive phosphorus
- pH and suspended solids
- dissolved copper, iron and zinc
- station, basin, coordinates, sampling date and time
- paired `<` / `>` qualifier fields for censored measurements

**Target-variable decision:**  
No classification target exists. “Safe”, “moderate risk” and “high risk” labels will not be created. The provisional supervised task is regression with dissolved oxygen (`DO_mg_l_`) as a continuous target because it is directly measured and has 151,037 non-missing values. This would be contemporaneous estimation, not future forecasting or official water-status classification. Unsupervised exploration remains a secondary option.

**Major data-quality concerns:**

- heterogeneous missingness; iron and zinc are missing in about 79.6% of rows
- 442 rows with all 13 chemistry results missing
- many below-detection qualifier flags, especially for ammonia, nitrite, BOD, phosphorus, suspended solids and zinc
- source-documented possibility of typos, sampling error or contamination causing extreme values
- irregular sampling effort across years and stations
- repeated sites create leakage risk under random row splitting
- duplicate coordinate fields, constant depth and non-scientific object identifier
- dissolved-iron unit conflict between catalogue prose and exported field schema
- no temperature measurement, which limits interpretation of dissolved oxygen

**Questions that remain:**

- What censored-value strategy is appropriate for this ML objective?
- Can NIEA clarify the dissolved-iron unit and any historical method changes?
- Should validation prioritise unseen stations, future dates, or both?
- Which predictors should be retained without allowing location identifiers to dominate?
- Are the most extreme records traceable to source errors, genuine events or differing conditions?
- Should rows without any chemistry result be excluded, and how should that decision be documented?
- Is dissolved-oxygen regression the most educational task after exploratory plots by station and time?

**Actions completed:**

- Downloaded the unchanged official CSV export to `data/raw/niea_river_water_quality_1990_2024.csv`.
- Recorded SHA-256 `a5ce02d9ab3703edc4279c8dc5f9d38a593b92c555945c5cdb2ab3ca55632632`.
- Created candidate comparison, dataset documentation and data-quality report.
- Updated the EDA notebook for the selected schema.
- Did not clean the data or train final models.

## 2026-09-30 — Phase 3 baseline regression and error analysis

**Goal:**  
Create a scientifically defensible baseline experiment for estimating contemporaneously measured dissolved oxygen at monitoring stations excluded from training.

**Evidence inspected:**

- all 178,680 raw records and paired chemistry qualifier columns
- target completeness and the six `<`-qualified dissolved-oxygen observations
- predictor missingness and complete-case retention
- extreme-value distributions, associated stations and dates
- grouped-station and earlier/later-period holdout predictions

**Decisions and rationale:**

- Used measured dissolved oxygen as a continuous regression target; no safety or risk label was created.
- Excluded 27,643 rows without a target and six censored target rows, producing 151,031 modelling rows from 840 stations.
- Used BOD, ammonia, nitrite, nitrate, soluble reactive phosphorus and pH as the core measurement features.
- Excluded identifiers, location, station, coordinates, basin, depth, dissolved iron, date/year and target-derived fields from predictors. Station and date were retained as validation metadata.
- Preserved reported numeric values for censored predictors and added below/above-limit flags. Did not substitute half the limit.
- Retained unverified extreme values rather than treating statistical rarity as proof of error.
- Used training-only median imputation with missingness indicators and scaling inside each pipeline. Complete-case filtering would have retained 135,280 rows (89.571%), so it was not used as the main strategy.
- Made a station-grouped holdout the primary validation design. The split has 119,690 training rows from 672 stations and 31,341 test rows from 168 different stations, with no station overlap.
- Added a secondary sensitivity split trained on 1990–2018 and tested on 2019–2024. This was not presented as forecasting.

**Results:**

- Random Forest had the lowest grouped-holdout MAE among the four tested baselines: MAE 1.181 mg/L, RMSE 1.644 mg/L and R² 0.253.
- Linear Regression obtained MAE 1.282 mg/L, RMSE 1.767 mg/L and R² 0.136.
- The mean dummy obtained MAE 1.392 mg/L, RMSE 1.902 mg/L and R² approximately 0.
- The single Decision Tree obtained MAE 1.686 mg/L, RMSE 2.404 mg/L and R² -0.599, worse than the dummy.
- Random Forest reduced MAE by 15.2% relative to the dummy and 7.9% relative to Linear Regression. The gain is useful but modest.
- In the temporal sensitivity split, Random Forest obtained MAE 0.977 mg/L, RMSE 1.281 mg/L and R² 0.372.
- Error analysis showed strong regression toward the middle. Lowest-decile DO observations had MAE 2.362 mg/L and were overpredicted 93.2% of the time; highest-decile observations had MAE 2.117 mg/L and were underpredicted 97.5% of the time.
- Held-out permutation importance ranked nitrite and nitrate highest, followed by soluble reactive phosphorus and pH. This was recorded as predictive association, not causation.

**Unexpected problems:**

- The single Decision Tree generalised substantially worse than both Linear Regression and the dummy baseline.
- Overall MAE concealed much larger errors at both ends of the target distribution.
- Several largest errors involved unusually high dissolved-oxygen measurements, which remain unverified rather than automatically removed.

**Limitations / open questions:**

- Important physical drivers such as water temperature, flow, season and time of day are absent or not used.
- One grouped holdout does not quantify split-to-split uncertainty.
- Censor flags preserve reporting information but do not estimate unknown values below or above reported limits.
- The next phase should compare justified feature sets, use group-aware resampling, deepen tail-error analysis and add non-causal explainability before application development.

## 2026-09-30 — Phase 4 robust validation and model refinement

**Goal:**  
Measure variation across held-out station groups, compare scientifically bounded feature sets, perform modest training-only refinement, and investigate remaining prediction failures without changing the modelling claim.

**Experiments performed:**

- Recreated and sealed the Phase 3 holdout: 119,690 training rows from 672 stations and 31,341 test rows from 168 different stations.
- Ran five-fold `GroupKFold` only within the training portion, with fold-specific preprocessing and no station overlap.
- Compared Dummy Mean, Linear Regression, Random Forest and HistGradientBoosting on core chemistry.
- Compared core, extended, temporal, and extended-plus-temporal feature sets.
- Tested three Random Forest and four HistGradientBoosting configurations using mean group-CV MAE.
- Evaluated the selected pipeline once on the sealed test set, then analysed target ranges, stations, years, months and seasons.
- Calculated held-out permutation importance, partial dependence and empirical group-CV absolute-error percentiles.
- Re-ran the 1990–2018 to 2019–2024 temporal sensitivity experiment with the selected pipeline.

**Feature and data findings:**

- Added alkalinity, conductivity and suspended solids after verifying their units, missingness and qualifier fields.
- Eligible-row missingness is 21.719% for alkalinity, 26.051% for conductivity and 25.785% for suspended solids.
- Alkalinity has 2,719 `<` qualifiers, suspended solids has 22,465 and conductivity has none. Numeric exported values plus qualifier flags were retained.
- Added day-of-year sine/cosine context. Raw date IDs were not used.
- Confirmed that no temperature field or documented alternative representation exists in the export. No temperature proxy was manufactured.

**Cross-validation and selection:**

- On core features, HistGradientBoosting had the lowest mean CV MAE at 1.184 ± 0.039 mg/L; Random Forest obtained 1.219 ± 0.036, Linear Regression 1.325 ± 0.049 and Dummy Mean 1.430 ± 0.060.
- Extended-plus-temporal features performed best in the feature comparison: HistGradientBoosting CV MAE 0.931 ± 0.037 mg/L.
- The selected candidate was a Random Forest with 150 trees, `min_samples_leaf=2` and `max_features=0.8`. Its group-CV MAE was 0.880 ± 0.035 mg/L.
- Selection used training-station CV only. The final holdout and tail results were not consulted during selection.

**Final results:**

- On the untouched station holdout, the selected model obtained MAE 0.831 mg/L, RMSE 1.291 mg/L and R² 0.539.
- Relative to the Phase 3 Random Forest MAE of 1.181 mg/L on the same holdout, MAE decreased by 0.350 mg/L (29.640%). This gain combines feature and model changes.
- Lowest-decile MAE decreased from 2.362 to 1.812 mg/L, but 89.964% of low-DO observations were still overpredicted.
- Highest-decile MAE decreased from 2.117 to 1.396 mg/L, but 94.831% were still underpredicted.
- Empirical group-CV absolute-error percentiles were 0.592, 1.117, 1.908 and 2.622 mg/L at the 50th, 75th, 90th and 95th percentiles.
- Temporal sensitivity performance was MAE 0.657 mg/L, RMSE 0.922 mg/L and R² 0.675.

**Explainability observations:**

- Permutation importance ranked day-of-year cosine, pH, day-of-year sine and alkalinity highest, followed by nitrate, nitrite and conductivity.
- These are model associations, not causal effects. Seasonal context may partly encode omitted environmental conditions, including unavailable temperature.
- SHAP was not added because the existing stack did not require it; permutation importance and partial dependence provided stable global explanations.

**Unexpected findings:**

- Temporal context produced a larger CV improvement than adding extended chemistry alone.
- HistGradientBoosting was best on core features, but the modestly regularized Random Forest was best after the extended-plus-temporal feature set was selected.
- Overall error improved substantially while regression toward the middle remained pronounced in the lowest and highest 5–10% of observations.
- The reviewed largest low-DO overpredictions did not share one observable censoring, missingness, station or chemistry pattern.

**Limitations / open questions:**

- Temperature, flow and other physical drivers remain unavailable.
- Error percentiles are descriptive validation errors, not formal prediction intervals.
- Extreme source measurements remain unverified.
- The model and explanations are specific to this monitoring program and do not establish causation or regulatory suitability.
- The next phase should prioritise a defensible project report and, if desired, a carefully constrained educational application rather than further test-set optimisation.

## 2026-10-01 — Phase 5 academic and portfolio packaging

**Goal:**  
Convert the completed research workflow into consistent academic, portfolio, application and interview materials without changing the model or scientific conclusions.

**Work completed:**

- Created a concise academic report with six existing Phase 4 figures and captions.
- Created portfolio, one-page, CV, university-application, interview-preparation and project-reflection documents.
- Reworked the README around the current research question, verified results, limitations and repository-relative reproducibility commands.
- Added a project-status document separating completed research from deployment, regulatory, causal, uncertainty and external-validation work that remains incomplete.
- Added a neutral AI-assisted development note without attributing scientific decisions to automation.

**Consistency and claim audit:**

- Kept the final holdout result at MAE 0.831 mg/L, RMSE 1.291 mg/L and R² 0.539 throughout public-facing documents.
- Kept training-only group-CV performance at MAE 0.880 ± 0.035 mg/L, RMSE 1.392 mg/L and R² 0.510.
- Preserved the Phase 3 comparison and 29.640% MAE improvement without attributing the gain solely to tuning.
- Preserved the lowest-decile MAE of 1.812 mg/L with 89.964% overprediction and highest-decile MAE of 1.396 mg/L with 94.831% underprediction.
- Audited language concerning safety, forecasting, accuracy and causality. Positive claims now consistently describe contemporaneous DO estimation at held-out stations.
- Confirmed that public-facing Markdown contains no `/Users/...` paths or local file URIs.

**Result:**

The repository is packaged as an application-ready academic portfolio project. The recommended next phase is a constrained interactive educational application that exposes validation context, target-range warnings and limitations rather than presenting a bare prediction.

## 2026-10-01 — Phase 6 local educational application

**Goal:**  
Build a polished local Streamlit interface around the verified Phase 4 model without retraining, changing the scientific question, or presenting predictions as regulatory or safety conclusions.

**Work completed:**

- Added Home, Data Explorer, Dissolved Oxygen Estimator, Model Performance and About the Model pages.
- Loaded the complete saved Phase 4 preprocessing-and-model pipeline from `models/phase4_selected_model.joblib`; the application contains no training path.
- Implemented the exact 25-feature input contract, including censoring flags and the documented day-of-year sine/cosine transformation.
- Preserved unavailable measurements as missing values for the fitted imputer instead of inventing replacements in the interface.
- Added range, missing-input and extreme-target-behaviour warnings, plus the persistent scientific-use notice.
- Presented the executed grouped-validation, holdout, tail-error, permutation-importance and prediction-compression results with non-causal language.
- Added cached data loading, a formal application data contract, local run instructions and application-logic tests.

**Verification:**

- Confirmed that a complete UI input row has the model's exact ordered feature columns and excludes the target and target qualifier.
- Confirmed that the saved pipeline reloads and returns a finite prediction.
- Confirmed that the application date transformation matches a Phase 4 processed-data row.
- Confirmed that missing values and censoring qualifiers are encoded according to the model contract.
- Ran the full repository test suite and visually exercised the running local application, including a real estimator submission.

**Limitations / open questions:**

- The application is local and educational; it is not deployed or operationally validated.
- Its estimate is contemporaneous, not a forecast, and cannot replace sampling or laboratory measurement.
- Error percentiles remain descriptive validation summaries rather than individual prediction intervals.
- Generalisation beyond the Northern Ireland monitoring programme has not been tested.
- Missing water temperature, flow and other physical context, plus weaker performance at target extremes, remain unresolved scientific limitations.

## 2026-10-01 — Phase 7 public-release and deployment preparation

**Goal:**  
Polish the interface, prepare a practical public repository and Streamlit deployment package, create genuine demo assets, and complete final privacy, licensing, consistency and scientific-claim audits without altering the trained model.

**Work completed:**

- Reorganised the Home page around four headline facts, followed by the research question, workflow and limitations.
- Grouped estimator controls into sampling context, core chemistry and additional chemistry; added a real complete training-record example.
- Reworked Model Performance into a numbered narrative from baselines through grouped validation, refinement, final metrics and error analysis.
- Added a restrained responsive style layer and checked all five pages at wide, 768 px and 390 px widths.
- Replaced runtime dependence on the full processed dataset with approximately 1.8 MB of reproducible public app artifacts generated by `scripts/build_app_artifacts.py`.
- Kept the verified 175,556,503-byte model unchanged and prepared Git LFS tracking because it exceeds GitHub's normal object limit.
- Added deployment, release-audit, checklist and timeline documentation plus demo, portfolio, CV and undergraduate-application copy.
- Captured five genuine local application screenshots; the estimator capture uses a real example record and saved-model result.

**Audits and verification:**

- No credential, private contact detail or required local absolute path was found.
- Raw and processed datasets remain ignored; licence attribution is present for the OGL v3.0 source.
- Direct dependencies are pinned to the versions used for final verification.
- Phase 3/4 result files, split, hyperparameters and scientific conclusions were not changed.
- Public wording was checked for safety, forecasting, diagnosis, causal and individual-uncertainty claims; one ambiguous use of “accuracy” was replaced with “MAE.”
- The local application started from the repository root, loaded the saved model and produced a finite example prediction.

**Limitations / open questions:**

- Git LFS must be installed and verified by the author before the first public push.
- Public GitHub creation, Streamlit deployment and live-URL testing remain manual author actions.
- Mobile behaviour was checked in a browser-sized viewport but still requires confirmation on a physical device.
- Deployment resource use and cold-start time must be measured on the selected hosting account.

## Future development notes

Add dated entries below. For each important decision, record the evidence, the change made, why it was made, and any limitations introduced.

### YYYY-MM-DD — Short title

**Goal:**

**Evidence inspected:**

**Decision and rationale:**

**Results:**

**Limitations / open questions:**
