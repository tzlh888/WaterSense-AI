# WaterSense AI — Undergraduate Application Project Description

## 100-word version

I developed WaterSense AI to study whether river-monitoring chemistry can estimate dissolved oxygen at unseen monitoring stations. Using 151,031 observations from an official Northern Ireland dataset, I first audited missing values, reporting-limit censoring and repeated station records. I rejected my original risk-classification idea because the dataset contained no defensible safety labels, and reframed the task as continuous regression. I used station-grouped validation to prevent location leakage and selected a Random Forest through training-only cross-validation. It achieved 0.831 mg/L MAE on 168 held-out stations. Error analysis revealed systematic overprediction at low dissolved oxygen and underprediction at high values.

## 200-word version

WaterSense AI is an environmental machine-learning project built from an official Northern Ireland river-monitoring dataset covering 1990–2024. I wanted to investigate how AI methods could support the analysis of long-running scientific observations, but the dataset forced me to reconsider my original problem definition.

I initially considered water-quality risk classification. The audit showed that the data contained no scientifically defensible Safe, Moderate or High-Risk label. Rather than inventing thresholds, I selected the original continuous dissolved-oxygen measurement as a regression target. I then addressed missing measurements, laboratory reporting-limit censoring and repeated samples from the same monitoring stations.

Randomly dividing individual rows could place observations from one station in both training and testing. I therefore held out complete stations and used grouped cross-validation for feature and model selection. The final Random Forest achieved 0.831 mg/L mean absolute error on 31,341 observations from 168 stations absent from training.

The most useful result was not only the improved average error. Detailed analysis showed that unusually low dissolved oxygen was usually overpredicted and unusually high values underpredicted. I built a Streamlit interface that presents this limitation beside each estimate. The project taught me to treat problem formulation, leakage control and failure analysis as central parts of machine learning rather than additions after model training.

## Interview version

The key decision in WaterSense AI was changing the question when the data did not support my first idea. I began with risk classification, but the government dataset had measurements rather than defensible safety labels. I therefore modelled continuous dissolved oxygen and designed validation around complete monitoring stations. That prevented repeated records from the same location leaking across the split. The final Random Forest reached 0.831 mg/L MAE on 168 unseen stations, but the error analysis showed a clear weakness at low and high dissolved oxygen. I kept that limitation visible in the app because understanding when a model fails is as important as its average score.
