# Baseline model results

## Experimental Question

Can baseline regression models estimate dissolved oxygen concentration from contemporaneously measured physicochemical river-water variables at monitoring stations not used for model training?

This experiment is not future forecasting, a drinking-water safety classification, or an official ecological-status assessment.

## Dataset Used

The experiment uses the Northern Ireland Environment Agency **River Water Quality Monitoring 1990 to 2024 — All Parameters** dataset. The raw export contains 178,680 rows and 40 columns. After excluding 27,643 rows without a dissolved-oxygen result and six rows with a `<`-qualified dissolved-oxygen result, the processed modelling dataset contains 151,031 rows from 840 stations.

## Target

The continuous target is the original `DO_mg_l_` measurement, renamed `dissolved_oxygen_mg_l`, in mg/L. It is not a derived label. Qualifier `Q_DO` is never used as a predictor.

## Feature Set

The six baseline measurements are:

- BOD (mg/L)
- ammonia as nitrogen (mg/L)
- nitrite as nitrogen (mg/L)
- nitrate as nitrogen (mg/L)
- soluble reactive phosphorus (mg/L)
- pH (pH units)

Ten binary below/above-reported-limit flags accompany the five measurements that have qualifier information. Station, location, coordinates, basin, date, year, identifiers, depth, dissolved iron and the target are excluded from the predictor matrix. Station and date metadata are retained only for validation and error analysis.

## Cleaning Decisions

- The raw file was read but not overwritten; its SHA-256 remained `a5ce02d9ab3703edc4279c8dc5f9d38a593b92c555945c5cdb2ab3ca55632632`.
- Dates were parsed, core variables received explicit modelling names, and validation metadata was retained.
- Rows without a usable target were excluded only from supervised modelling.
- Statistical outliers were retained because none was verified as erroneous.
- No risk class or regulatory threshold was created.

## Censoring Strategy

For each core predictor with `<` or `>` qualifiers, the exported numeric companion is retained and binary below-limit and above-limit flags are added. The project does not interpret the numeric companion as the true concentration and does not replace it with half the reported limit. The six `<`-qualified target observations are excluded because their exact outcome is unknown and a target qualifier cannot safely be used as a feature.

## Missing Data Strategy

Among the 151,031 eligible modelling rows, predictor missingness is:

| Feature | Missing rows | Missing % |
|---|---:|---:|
| BOD | 5,218 | 3.455% |
| Ammonia as N | 755 | 0.500% |
| Nitrite as N | 9,805 | 6.492% |
| Nitrate as N | 10,380 | 6.873% |
| Soluble reactive phosphorus | 7,459 | 4.939% |
| pH | 1,893 | 1.253% |

Complete-case filtering would retain 135,280 rows, or 89.571% of eligible rows. The main pipeline instead applies median imputation to numeric predictors, adds missingness indicators through `SimpleImputer`, and standardises measurements. All preprocessing is fitted on training data only. Qualifier flags pass through separately.

## Validation Strategy

The primary holdout is a reproducible `GroupShuffleSplit` grouped by station with `random_state=42` and a 20% station test fraction:

| Split | Rows | Stations |
|---|---:|---:|
| Training | 119,690 | 672 |
| Test | 31,341 | 168 |

The station-code intersection is empty. This tests transfer to held-out monitoring stations and avoids putting repeated observations from one station into both sets.

A secondary temporal sensitivity experiment trains on 132,766 records from 1990–2018 and tests on 18,265 records from 2019–2024. It asks whether relationships learned from earlier records remain useful later; it is not a forecasting experiment.

## Models

Four untuned baselines were executed: mean `DummyRegressor`, `LinearRegression`, `DecisionTreeRegressor`, and `RandomForestRegressor`. Tree models use `random_state=42`. Each saved joblib artifact contains the fitted preprocessing and estimator pipeline.

## Metrics

MAE is primary because it reports typical absolute error directly in mg/L. RMSE gives more weight to large errors. R² compares the model with a mean-prediction reference on the same holdout.

## Model Comparison

### Primary station-grouped holdout

| Model | MAE (mg/L) | RMSE (mg/L) | R² |
|---|---:|---:|---:|
| Random Forest | 1.181 | 1.644 | 0.253 |
| Linear Regression | 1.282 | 1.767 | 0.136 |
| Dummy Mean | 1.392 | 1.902 | -0.000 |
| Decision Tree | 1.686 | 2.404 | -0.599 |

Random Forest achieved the lowest MAE among the four tested baselines. Its MAE is 15.2% lower than the dummy baseline and 7.9% lower than linear regression, so the improvement is real but modest. The unrestricted single decision tree performed worse than the dummy baseline. A non-linear model therefore did not automatically outperform the linear model.

### Temporal sensitivity

| Model | MAE (mg/L) | RMSE (mg/L) | R² |
|---|---:|---:|---:|
| Random Forest | 0.977 | 1.281 | 0.372 |
| Linear Regression | 1.121 | 1.453 | 0.192 |
| Dummy Mean | 1.206 | 1.618 | -0.002 |
| Decision Tree | 1.428 | 1.966 | -0.479 |

These later-period results do not establish forecasting ability. They differ from the station-grouped results because the validation question and held-out observations differ.

## Error Analysis

For the grouped-holdout Random Forest:

| Actual-DO range | Rows | Actual range (mg/L) | MAE (mg/L) | RMSE (mg/L) | R² |
|---|---:|---:|---:|---:|---:|
| Overall | 31,341 | 0.50–32.50 | 1.181 | 1.644 | 0.253 |
| Lowest 10% | 3,308 | 0.50–8.10 | 2.362 | 2.754 | -3.371 |
| Middle 80% | 24,493 | 8.17–12.27 | 0.887 | 1.132 | -0.163 |
| Highest 10% | 3,540 | 12.30–32.50 | 2.117 | 2.823 | -1.844 |

The strongest finding is regression toward the middle. In the lowest-DO group, 93.2% of predictions are too high and the mean residual (`actual - predicted`) is -2.262 mg/L. In the highest-DO group, 97.5% are too low and the mean residual is +2.084 mg/L. The largest absolute error is 23.486 mg/L: an actual value of 32.5 mg/L at station `UKGBNIF10575` on 2013-07-22 was predicted as 9.014 mg/L. These tail errors are visible rather than removed or hidden.

## Feature Importance

Held-out permutation importance measured by increase in MAE ranks nitrite (0.334 mg/L), nitrate (0.326), soluble reactive phosphorus (0.171), pH (0.156), ammonia (0.060), and BOD (0.048) as the six most influential measurement inputs in this fitted model. Impurity importance and the full permutation table are stored in `results/`.

These values are predictive associations, not causal effects. Correlated chemistry, monitoring practices, missingness and reporting limits can all affect importance. The experiment does not show that changing a feature would cause dissolved oxygen to change.

## Limitations

- Dissolved oxygen depends on conditions absent from the dataset, especially temperature, flow, season, time of day and possibly salinity.
- Predictors and target are contemporaneous measurements, so the model cannot forecast future conditions.
- The target and some predictors include unverified extreme values.
- Censored predictors are represented transparently but their unknown true concentrations are not modelled explicitly.
- Median imputation is a baseline assumption, not recovery of true missing measurements.
- Results cover Northern Ireland river monitoring data and may not generalise to other regions, water bodies or sampling programs.
- The station holdout is one split and does not provide uncertainty intervals across multiple grouped folds.
- Feature importance does not establish mechanism or causation.

## Next Questions

The next scientifically useful phase should compare a small number of justified feature sets, quantify variability with repeated or cross-validated station-grouped evaluation, examine tail performance more deeply, and add model explanation without causal language. Any modest tuning should occur inside group-aware cross-validation, leaving the current grouped holdout untouched. Application development should follow only after the prediction contract and limitations are stable.
