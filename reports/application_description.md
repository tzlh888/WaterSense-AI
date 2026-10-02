# University Application Descriptions

## Version A — approximately 100 words

WaterSense AI developed my interest in moving from software construction toward evidence-based machine learning. Using 151,031 eligible observations from an official Northern Ireland river-monitoring dataset, I built regression pipelines to estimate contemporaneously measured dissolved oxygen. The central lesson was that evaluation design matters as much as algorithms: repeated station records required grouped validation, and all feature selection and tuning had to remain separate from the final test stations. The selected Random Forest achieved 0.831 mg/L holdout MAE, but error analysis showed persistent overprediction at low dissolved oxygen. This taught me to treat limitations and failure regions as core results rather than inconvenient details.

## Version B — approximately 200 words

WaterSense AI began as an opportunity to connect software development with environmental data, but it became primarily a study of how to make machine-learning conclusions credible. I selected an official Northern Ireland Environment Agency dataset containing 178,680 river-monitoring observations and investigated its provenance, variables, missingness, reporting-limit qualifiers and repeated station structure.

The original idea of producing simple water-risk categories was not supported by the data: no official safety label existed, and inventing thresholds would have confused environmental monitoring with drinking-water regulation. I therefore defined a more defensible regression question—whether physicochemical measurements could estimate contemporaneously measured dissolved oxygen at stations not seen during training.

I learned that a random train/test split could give misleading results because the same monitoring station might appear on both sides. I used station-grouped cross-validation for feature and model selection and protected a separate 168-station holdout. The selected Random Forest achieved MAE 0.831 mg/L, a 29.6% improvement over the Phase 3 baseline.

More importantly, overall MAE hid a clear weakness. The lowest 10% of dissolved-oxygen observations had MAE 1.812 mg/L and were usually overpredicted. The project changed my understanding of machine learning from choosing an algorithm to designing a defensible experiment, investigating errors and communicating what the data cannot establish.

## Version C — approximately 350 words

WaterSense AI reflects my development from building software features toward asking whether data and evaluation methods genuinely support a machine-learning claim. I worked with the Northern Ireland Environment Agency’s River Water Quality Monitoring 1990–2024 dataset, an official government export containing 178,680 observations from 1,311 stations. Before modelling, I examined provenance, units, missing values, extreme observations and laboratory qualifier fields that mark measurements below or above reported limits.

The project initially considered classifying water into simple risk categories. That direction was scientifically weak because the dataset contained no official safety or ecological-status label. Creating categories from unsupported thresholds could also have applied drinking-water ideas incorrectly to environmental river samples. I replaced that concept with a narrower question: can machine-learning models estimate contemporaneously measured dissolved oxygen from physicochemical variables at previously unseen monitoring stations?

After excluding rows without a usable target, 151,031 observations from 840 stations remained. Censored predictor values were retained with indicator features, while missing values were imputed inside training pipelines. Station and location identifiers were not used as normal predictors.

The most important methodological decision concerned validation. Repeated observations from one monitoring station are related, so a random row split could expose the model to the same station during training and testing. I created a final holdout of 168 unseen stations and used five-fold station-grouped cross-validation only within the training portion for feature and model selection.

I compared linear, tree-based and gradient-boosted regression models across four feature sets. The selected Random Forest used extended chemistry and cyclical day-of-year context. It achieved training-only CV MAE 0.880 ± 0.035 mg/L and final holdout MAE 0.831 mg/L, RMSE 1.291 mg/L and R² 0.539.

The strongest lesson came from error analysis. Although average error improved by 29.6% over the earlier baseline, the lowest 10% of dissolved-oxygen values still had MAE 1.812 mg/L and were overpredicted almost 90% of the time. The model also lacked temperature and flow—important physical context that the dataset did not contain.

This project showed me that machine learning is not only implementation or optimisation. It requires choosing a defensible target, preventing leakage, understanding measurement limitations, examining where a model fails, and separating predictive association from causation. Those decisions made the project more rigorous than the original classification idea and gave me a clearer view of the responsibilities involved in applied AI.
