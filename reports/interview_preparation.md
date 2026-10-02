# WaterSense AI — Interview Preparation

## Dataset

### 1. Why did you choose this dataset?

It has traceable Northern Ireland government provenance, an open licence, 178,680 dated observations, repeated station identifiers, relevant chemistry measurements and 35 years of coverage. It is large enough for modelling while remaining understandable as one documented export.

### 2. Why did only 151,031 observations enter modelling?

There were 27,643 rows without a dissolved-oxygen target and six additional targets marked `<`. Supervised regression requires a usable outcome, so those rows were excluded without changing the raw file.

### 3. How did you handle values reported below a limit?

For predictors, I retained the exported numeric companion and added a below-limit indicator. I did not claim that the numeric limit was the true concentration or automatically substitute half the limit. The six censored targets were excluded because their exact outcomes were unknown.

## Machine Learning

### 4. Why is this a regression problem rather than classification?

Dissolved oxygen is an original continuous measurement in mg/L. The dataset contains no scientifically documented safety or risk class, so classification would require inventing labels.

### 5. Which baseline models did you compare?

Phase 3 compared a mean Dummy Regressor, Linear Regression, a Decision Tree and a Random Forest. Random Forest had the lowest baseline holdout MAE at 1.181 mg/L, while the single tree performed worse than the dummy.

### 6. What did HistGradientBoosting contribute?

It provided an additional nonlinear model within scikit-learn. It had the lowest core-feature group-CV MAE at 1.184 mg/L, although the refined Random Forest performed best once the extended-plus-temporal feature set was selected.

### 7. What was the final model?

A Random Forest with 150 trees, `min_samples_leaf=2`, `max_features=0.8` and `random_state=42`, using extended chemistry and cyclical day-of-year context.

## Validation

### 8. Why would a random row split be misleading?

The same stations were measured repeatedly. A random row split could put one station in both training and test data, producing an easier within-site interpolation problem rather than testing transfer to unseen stations.

### 9. What does GroupKFold do in this project?

It assigns whole station groups to folds. No station appears in both the training and validation portions of one fold. Five folds were used inside the Phase 3 training set.

### 10. How did you protect the final test set?

The 168-station holdout was recreated once and excluded from feature comparison and parameter selection. All decisions used training-only grouped CV, and the selected pipeline was then evaluated once on the holdout.

### 11. Why report both CV and holdout performance?

CV shows variation across several groups of withheld training stations and supports model selection. The holdout provides a final reference on stations not used in those choices. The selected model had CV MAE 0.880 ± 0.035 mg/L and holdout MAE 0.831 mg/L.

## Error Analysis

### 12. What was the main failure pattern?

Regression toward the middle. The lowest 10% of actual DO values were overpredicted 89.964% of the time, and the highest 10% were underpredicted 94.831% of the time.

### 13. Why is overall MAE not sufficient?

Overall MAE was 0.831 mg/L, but lowest-decile MAE was 1.812 and highest-decile MAE was 1.396. One average therefore hides systematic target-range differences.

### 14. Did you find one cause for the large low-DO errors?

No. Reviewed cases occurred across different stations, dates, chemistry values and missingness patterns, and censoring was not a shared explanation. The available metadata does not justify one causal account.

## Explainability

### 15. What does permutation importance measure?

It measures how much held-out MAE worsens when one input is shuffled. Day-of-year cosine, pH, day-of-year sine and alkalinity had the largest measured effects in the selected model.

### 16. Why did you not implement SHAP?

The project needed stable global explanation, which held-out permutation importance and partial dependence already provided. SHAP would add dependency and compatibility complexity without being necessary for that objective. None of these methods would establish causality.

## Scientific Limitations

### 17. What is the strongest missing variable?

Water temperature. Flow and other physical conditions are also absent. These omissions limit prediction at extremes and prevent a complete physical interpretation of model behaviour.

### 18. Can the model be used to assess water safety or predict future pollution?

No. It estimates a co-measured dissolved-oxygen value from the same monitoring context. It has no safety target, regulatory validation, future forecasting design or causal basis.

## Personal Reflection

### 19. What was the most important thing you learned?

Evaluation design can matter more than algorithm complexity. Defining a defensible target, separating stations, fitting preprocessing inside folds and investigating failure regions made the result more credible than simply maximising a score.

### 20. What would you do next with more time or data?

I would seek compatible temperature and flow measurements, test geographic transfer outside Northern Ireland, and investigate models or loss functions focused on extreme DO behaviour while preserving a new untouched external test set.

# Three Questions I Must Be Able to Answer Perfectly

## Why did you change the original risk-classification idea?

The dataset contains no official risk or safety label. Creating one would require unsupported thresholds and could incorrectly apply drinking-water concepts to environmental river monitoring. Regression on measured dissolved oxygen preserves an original target with clear units and provenance.

## Why was station-grouped validation essential?

Repeated observations from one station are related. Random row splitting could expose the model to the same location during training and testing. Grouping by `StationCode` tests whether the learned relationship transfers to stations not used for training and prevents that source of leakage.

## What does the final result prove—and not prove?

It shows that the available chemistry and cyclical date context contain predictive information for contemporaneous DO at held-out Northern Ireland stations: holdout MAE was 0.831 mg/L. It does not establish water safety, future conditions, causal mechanisms, formal uncertainty, regulatory validity or geographic generalisation beyond this program.
