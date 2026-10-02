# Intended methodology

This document describes the project workflow and the validation design used through Phase 4.

## 1. Problem definition

The broad research question is whether machine-learning models can identify meaningful patterns in physicochemical water measurements. Before modelling, this must be converted into a precise prediction question: what is one observation, what outcome is predicted, for which population or locations, and for what intended use?

### Phase 3 modelling objective

> Estimate dissolved oxygen concentration from contemporaneously measured physicochemical river-water variables.

The target is the original `DO_mg_l_` measurement in mg/L. The initial predictors are BOD, ammonia, nitrite, nitrate, soluble reactive phosphorus and pH measurements recorded in the same monitoring context.

This objective has deliberately narrow boundaries:

- it is **not future forecasting**;
- it is **not a drinking-water safety classifier**;
- it is **not an official ecological-status assessment**;
- predictors and target are measurements from the same monitoring record; and
- performance measures the ability to estimate dissolved oxygen from related contemporaneous measurements, not the ability to predict future river conditions.

The primary validation claim is transfer to monitoring stations withheld from training. A separate earlier-years/later-years sensitivity analysis asks whether relationships learned from earlier records remain useful on later records; it still does not constitute time-series forecasting.

The target cannot be invented for convenience. Classification requires existing labels or a transparent external rule supported by an appropriate scientific or regulatory source. A continuous measured outcome suggests regression. If no defensible target exists, descriptive EDA, clustering, anomaly detection, or dimensionality reduction may be explored, but those methods must not be presented as proof that water is safe or unsafe.

## 2. Dataset selection

A candidate dataset should be evaluated for:

- an identifiable, trustworthy source and usable licence
- documentation of variables, units, instruments, detection limits, and sampling procedures
- geographic and temporal coverage
- the meaning and provenance of any target variable
- sample size, class balance, missingness, duplicates, and repeated measurements
- possible selection bias and whether the data represent the intended setting

Data from the same site, sampling event, person, or time sequence may be correlated. If so, a random row split could leak related information across training and test sets. Grouped, spatial, or time-based validation may be required.

## 3. Exploratory data analysis

EDA examines the raw data without silently changing it. The exploration notebook inventories shape, columns, data types, sample rows, missingness, duplicates, numeric summaries, categorical levels, distributions, and correlations. It also flags non-finite values, constant columns, negative measurements, and values outside the ordinary interquartile range for review.

These flags are prompts for investigation, not automatic evidence of error. Environmental extremes may be genuine, and correlations do not establish causal relationships.

## 4. Data cleaning

Cleaning decisions should be based on dataset documentation and recorded in the project log. The framework standardises column names and can apply explicit type conversions or documented valid ranges. It preserves the raw file and writes a separate processed copy.

Missing values may reflect instrument limitations, non-detects, or sampling design. They should not be converted or removed without understanding their meaning. Exact duplicates should be checked against identifiers and sampling procedures before removal. Statistical outliers are retained by default.

## 5. Train/test split

The test set is held back to estimate performance on unseen observations. The default random seed is 42 so that the split and baseline models are reproducible. Classification is stratified when class counts permit it.

The default random split is only a starting point. Once dataset structure is known, the validation design must reflect groups, location, time, and the intended generalisation claim. The test set must not be used to choose cleaning rules, features, or hyperparameters.

For the selected NIEA dataset, the Phase 3 primary split is grouped by `StationCode`: no station may appear in both training and test sets. A simple random row split is not used because repeated records from the same station would make the holdout overly similar to training data. The secondary temporal sensitivity split trains on records through 2018 and evaluates on records from 2019–2024; this boundary was chosen before model comparison rather than optimised for performance.

In Phase 4, that original grouped holdout is sealed as the final reference test set. Five-fold `GroupKFold` operates only on the original training stations. Feature-set comparison, model comparison and modest parameter selection use mean fold MAE rather than the final holdout. Only the selected pipeline is evaluated on the holdout.

## 6. Preprocessing

Numeric chemistry predictors receive median imputation, missingness indicators and standardisation. Qualifier-derived binary flags pass through separately. The Phase 4 selected set adds alkalinity, conductivity and suspended solids plus cyclical sine/cosine transforms of day of year. Station, location, coordinates, basin and raw date identifiers remain excluded from predictors.

Preprocessing is stored inside a scikit-learn `Pipeline`. The pipeline is fitted only on training data, preventing medians, scales, or category levels from being learned from the held-out test set. This is a central defence against data leakage.

## 7. Baseline models

The executed regression baselines are a mean Dummy Regressor, Linear Regression, a Decision Tree Regressor and a Random Forest Regressor. The tree models use `random_state=42`.

The models are intentionally not heavily tuned. Baselines help check whether a predictive signal exists and expose data or evaluation problems before complexity is added.

## 8. Evaluation

Classification evaluation includes accuracy, macro and weighted precision, recall and F1, a confusion matrix, and a per-class report. Macro scores show how performance is distributed across classes; weighted scores also reflect class frequency. Results must be compared with class prevalence and a simple baseline.

Regression evaluation includes MAE, RMSE, and R². MAE expresses typical absolute error in target units, RMSE gives larger errors more influence, and R² compares performance with a mean-prediction reference. Residual plots and performance across relevant subgroups should be examined later.

All reported metrics must come from actual held-out predictions and should include sample counts. Cross-validation and uncertainty estimates can be added once the dataset structure is understood.

## 9. Error analysis

For classification, inspect false positives, false negatives, misclassified rows, class imbalance, difficult classes, and systematic error across sites or other relevant groups. If the target genuinely represents water risk, false negatives may be especially consequential because a high-risk sample could be predicted as low-risk. That cost structure is not universal and must be tied to the intended application.

For regression, sort and inspect large absolute residuals, check whether errors vary across the target range, and look for systematic patterns associated with time, location, missingness, or measurement conditions. Test data should not be repeatedly used to redesign the model.

## 10. Explainability

Phase 4 uses held-out permutation importance and partial dependence. Permutation importance measures the increase in error when one input is disrupted; partial dependence visualises fitted model behaviour while averaging over other observed inputs. Neither establishes causation. SHAP was not introduced because it was unnecessary for the current global explanation objective and would add a compatibility-sensitive dependency.

## 11. Limitations

Model credibility is limited by dataset provenance, measurement error, detection limits, missingness, sample dependence, coverage, target validity, and distribution shift. A model trained in one region or period may not generalise elsewhere. Good held-out metrics cannot establish regulatory compliance or replace laboratory testing.

This system is an educational prototype and should not be used as a substitute for professional environmental testing or regulatory water-quality assessment.
