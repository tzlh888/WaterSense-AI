# WaterSense AI Demo Script

## 30-second version

WaterSense AI asks whether long-term river-monitoring chemistry can estimate dissolved oxygen at locations the model has not seen before. I used 151,031 Northern Ireland monitoring observations and kept entire stations separate during validation to reduce leakage. The final Random Forest achieved 0.831 mg/L MAE on 168 held-out stations. The app lets a user explore the data and run the verified model, while clearly showing that errors are larger at unusually low and high dissolved oxygen.

## 60-second version

I built WaterSense AI around a Northern Ireland government river-monitoring dataset covering 1990 to 2024. My initial idea was risk classification, but the data had no defensible Safe or High-Risk label, so I reframed the task as regression on measured dissolved oxygen.

Because stations contain repeated observations, I grouped validation by station rather than randomly splitting rows. A Random Forest selected through training-only grouped cross-validation achieved 0.831 mg/L MAE on 31,341 observations from 168 unseen stations.

The Streamlit interface loads that saved pipeline without retraining. It accepts chemistry, reporting-limit qualifiers and sampling date, then shows an estimate alongside the validation context. The most important limitation is visible too: low dissolved-oxygen observations were usually overpredicted and high observations underpredicted.

## 2-minute version

WaterSense AI began with a question about applying machine learning to environmental monitoring. I selected an official NIEA/DAERA dataset containing 178,680 Northern Ireland river records from 1990 to 2024 because its source, licence and measurement schema were traceable.

My first idea was water-quality risk classification. During the dataset audit I found no official Safe, Moderate or High-Risk target. Creating one would have required unsupported thresholds, so I changed the problem to estimating the original continuous dissolved-oxygen measurement.

The data raised several modelling challenges: missing measurements, below- and above-reporting-limit values, repeated samples from the same stations and unusual observations. I preserved censoring information with explicit flags and fitted imputation only on training data.

For validation, I held out entire monitoring stations. The final test set contains 31,341 observations from 168 stations with zero overlap with training. Feature and model selection used five-fold GroupKFold only inside the training stations. The selected Random Forest achieved 0.831 mg/L MAE, 1.291 mg/L RMSE and R² of 0.539 on the untouched holdout.

In the app, I can load a real example monitoring record, adjust the chemistry and date, and request an estimate. The interface recreates the exact 25-feature model input, loads the saved pipeline and displays the numeric result without translating it into a safety category.

The error analysis matters as much as the headline metric. The lowest ten percent of observed dissolved oxygen had MAE 1.812 mg/L and were mostly overpredicted; the highest ten percent had MAE 1.396 mg/L and were mostly underpredicted. I learned that a responsible ML project is not only about improving an average score: it is also about defining a defensible target, preventing leakage and making failure regions visible.
