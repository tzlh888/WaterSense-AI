# WaterSense AI — One-Page Research Summary

## Research objective

WaterSense AI asks whether routine river-water chemistry can estimate dissolved oxygen (DO) at monitoring stations not seen during training, with special attention to rare low-oxygen observations below 4 mg/L. The project is designed as a reliability study rather than a performance leaderboard: it tests whether a model that appears accurate overall can still fail on the environmental condition of greatest concern.

## Data and validation

The study uses Northern Ireland Environment Agency river-monitoring data from 1990–2024. Exact historical recovery verified a 178,680-row raw export and a 151,031-row modelling table by SHA-256. The model-development partition contains 119,690 unique observations from 672 stations; 758 observations at 115 stations are below 4 mg/L. A separate 31,341-row historical station holdout is treated only as a legacy benchmark because its results had already influenced research decisions.

The main experiment used five outer and four inner site-grouped folds. Stations never crossed a training/validation boundary, and all data-dependent preprocessing was fitted within the relevant training fold. The inner loop evaluated a frozen 128-candidate space, while the outer loop compared the selected procedure with an unchanged Random Forest anchor. Uncertainty was estimated by resampling whole stations, not individual records.

## Main result

Across pooled outer out-of-fold predictions, the selected low-DO-weighted procedure reduced low-DO MAE from **3.3235 to 2.3613 mg/L** and raised low-DO recall from **0.1293 to 0.3641**. The paired station-bootstrap intervals supported both changes within the development population. However, overall MAE worsened from **0.8797 to 0.9516 mg/L**, precision fell from **0.7903 to 0.5576**, and false positives increased from **26 to 219**. The false-negative rate remained high at **0.6359**.

The benefit was distributed rather than confined to one station: low-DO MAE improved at 102 of 115 low-DO stations, and recall gains appeared at 50. The cost was also distributed: additional false positives appeared at 76 stations, including many observations far above the 4 mg/L boundary. The correct conclusion is therefore not “the model became better,” but “the frozen procedure shifted the error trade-off toward detecting more low-DO cases.”

## Attribution and scientific interpretation

The formal outer comparison changed both model configuration and sample weighting, so it cannot attribute the entire gain to weighting alone. A post hoc analysis of saved inner-fold results formed 640 exact weight-1 versus weight-8 pairs across Random Forest (160), Extra Trees (160), and HistGradientBoosting (320), with model family, non-weight hyperparameters, folds, and preprocessing held constant. Every pair improved low-DO MAE and recall. This strongly supports weighting as a contributor, but remains exploratory because it was not an independently designed outer validation.

The frozen experiment conclusion is **IMPROVEMENT SUPPORTED** within development nested cross-validation. It is not external confirmation. No new external dataset was available, and no application-specific tolerance was defined for trading missed events against false alarms and ordinary-condition error.

## Research contribution

The project’s central contribution is methodological: it recovered exact data provenance, separated legacy tests from development evidence, measured rare-condition performance explicitly, used site-clustered uncertainty, preserved failed experiments, and reported benefits and costs together. It shows why aggregate MAE alone is insufficient for environmental ML and why repeated appearances of the same observations do not create independent evidence.

## Final conclusion

WaterSense AI provides a reproducible, technically interpretable undergraduate research result. It supports a controlled development-set improvement in low-DO sensitivity while documenting substantial remaining failures. It does not justify operational water-quality warnings, regulatory decisions, or claims of external generalization. The highest-value next step would be one genuinely independent external validation with a predefined error-cost policy—not additional tuning on legacy data.
