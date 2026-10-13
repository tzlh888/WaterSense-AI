# WaterSense AI — Technical Interview Preparation

## 1. Why was station-grouped validation necessary?

Random row splitting places measurements from the same monitoring station on both sides, allowing station-specific structure to leak into evaluation. Grouping by station tests transfer to unseen sites. In the nested design, both outer evaluation and inner configuration selection keep station identities disjoint.

## 2. Why use nested cross-validation?

The inner folds select among frozen candidates; the outer folds evaluate the entire selection procedure on stations not used for that choice. Reporting only inner validation would be optimistically biased. Five outer and four inner folds were fixed before results were examined.

## 3. What is the positive class?

An observation is positive when ground-truth DO is strictly below 4 mg/L. A prediction is positive when predicted DO is strictly below 4 mg/L. A value exactly equal to 4 is negative. This same definition is tested in code and used for recall, precision, F1, and false-negative rate.

## 4. What improved, and what worsened?

Low-DO MAE fell from 3.3235 to 2.3613 mg/L and recall rose from 0.1293 to 0.3641. But overall MAE rose from 0.8797 to 0.9516 mg/L, precision fell from 0.7903 to 0.5576, and false positives rose from 26 to 219. I would describe this as a changed error trade-off, not a universally better model.

## 5. Why not treat the 129 repeated low-DO appearances as independent observations?

The repeated spatiotemporal experiments reused records across splits. Those 129 appearances reduced to 56 unique observations from 20 stations. Repeating a record in several evaluations measures partition sensitivity; it does not create new environmental evidence.

## 6. Why bootstrap stations rather than rows?

Rows from one station are correlated. Row-wise bootstrap would treat them as independent and usually understate uncertainty. The analysis resamples entire stations and reports replicates where a metric is undefined, such as when no positive prediction occurs.

## 7. Can the gain be attributed to sample weighting?

Not completely from the formal outer comparison, because the baseline is Random Forest while the selected procedure used HistGradientBoosting with fold-specific hyperparameters and weight 8. Saved inner results allowed 640 exact weight-1/weight-8 HGB pairs, all favoring weight 8 on low-DO MAE and recall. That is strong exploratory attribution, not independent outer confirmation.

## 8. Was there data leakage?

The upgraded pipeline showed no confirmed target-feature leakage or cross-fold preprocessing leakage. Target and target qualifier are excluded; preprocessing is trained within folds; station identities do not cross fold boundaries. The main evidence limitation is historical test reuse: those results had already influenced research decisions, so they are legacy benchmarks rather than fresh confirmation.

## 9. Why is the model not deployment-ready?

The weighted procedure still misses about 63.6% of low-DO observations, creates many additional false alarms, has no predefined application cost tolerance, and lacks a genuinely new external confirmation set. Bootstrap intervals within development stations do not guarantee performance under regional or temporal shift.

## 10. What would you do next?

I would stop tuning on current data. The next valuable experiment is a one-time, preregistered evaluation on genuinely new stations or another compatible monitoring network, with a fixed model, threshold, and error-cost policy. If such data cannot be obtained, the honest conclusion is the current development-only trade-off.
