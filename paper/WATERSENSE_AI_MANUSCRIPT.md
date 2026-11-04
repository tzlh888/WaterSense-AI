# WaterSense AI: Station-Grouped Evaluation of Rare Low-Oxygen Reliability in Long-Term River Monitoring Data

**Manuscript status:** research portfolio manuscript; not peer-reviewed,
published or accepted; acquired 2025 same-programme temporal evidence is
distinct from outstanding cross-region validation.
**Author:** `[OWNER TO CONFIRM NAME AND CONTRIBUTION BEFORE SUBMISSION]`

## Abstract

Machine-learning performance averaged over environmental monitoring records can
hide failure on rare, operationally important conditions. WaterSense AI studies
whether routine physicochemical measurements can estimate contemporaneously
measured dissolved oxygen (DO) at river-monitoring stations excluded from model
training, with special attention to observations below 4 mg/L. The documented
Northern Ireland Environment Agency source contains 178,680 records from 1,311
stations (1990–2024); the historical modelling table contains 151,031 eligible
records from 840 stations. The primary V3 experiment used a frozen nested
station-grouped design on 119,690 development rows from 672 stations. Recomputed
outer out-of-fold results show that the selected low-DO-oriented procedure
reduced low-DO mean absolute error (MAE) from 3.3235 to 2.3613 mg/L and increased
recall from 0.1293 to 0.3641, but worsened overall MAE from 0.8797 to 0.9516
mg/L, reduced precision from 0.7903 to 0.5576, and increased false positives
from 26 to 219. A later fixed classifier reached 0.9222 recall but only 0.0684
precision and 9,517 false positives on the same reused development population.
New exploratory artifact analysis shows that the 758 low-DO observations are
concentrated in 115 stations; inverse HHI corresponds to 29.7 equally represented
stations, a concentration summary rather than an effective sample size. A
sampling-volume-controlled null has mean HHI 0.00352 versus observed 0.03372.
Paired whole-station bootstrap intervals quantify model and cost differences;
cost preference remains uncertain near the arithmetic crossings. Error-cost breakpoints make the decision
trade-off explicit, while balanced-station time slices show descriptive—not
prospective—variation across decades. The study’s contribution is therefore a
reproducible reliability and failure analysis. A separately frozen evaluation of
newly acquired 2025 records (3,490 rows, 494 stations) gives the historical
Phase4 model MAE 0.6432 mg/L but recall only 0.15 (3/20 low-DO observations).
Only nine stations contain low-DO events; precision 1.00 rests on three positive
predictions at one station. Cross-region confirmation, independent validation
of V3 weighting, real decision costs and owner-verified contribution remain
outstanding. DO is missing in 2,590/6,080 source rows (42.60%), so these
2025 estimates are conditional on observed targets, not the entire programme.

## 1. Introduction

Dissolved oxygen is an important physicochemical property of surface water, but
it is difficult to infer reliably from a small set of routine measurements.
Environmental monitoring records also violate the convenient fiction that each
row is an independent observation: stations are repeatedly sampled, monitoring
practice changes, missingness is structured, and rare events may cluster at a
small number of locations.

The project began as a regression study and evolved into a question about model
reliability. An average error below 1 mg/L can coexist with severe
overprediction of genuinely low DO. That distinction matters scientifically:
a model can be useful for ordinary estimation while remaining unsuitable for
warning decisions.

This manuscript consolidates historical V1–V4 evidence and a new artifact-only
portfolio extension. It reports positive and negative findings together,
separates current-value estimation from forecasting, and distinguishes
development evidence from independent confirmation.

## 2. Related Work

Blocked validation is recommended when ecological data have spatial, temporal,
or hierarchical dependence, because random row splitting can produce
over-optimistic error estimates [1]. WaterSense operationalizes this concern by
grouping on monitoring station and by retaining separate random, grouped,
temporal, spatiotemporal, and basin analyses with different interpretations.

Random forests provide a nonlinear ensemble baseline for regression [2]. The
project also evaluated linear, tree, Extra Trees, and histogram gradient
boosting families through scikit-learn [3]. Model-family breadth was used to
test whether conclusions depended on a single estimator, not to conduct an
unbounded performance search.

Low-DO detection is highly imbalanced. Under strong imbalance, precision and
recall expose false-alarm and miss trade-offs that accuracy or specificity can
obscure [4]. The project therefore reports confusion counts and denominators,
not only area-based summaries. Historical prediction intervals were inspired
by split residual calibration, but coverage under distribution shift must be
interpreted cautiously; distribution-free guarantees depend on assumptions
such as exchangeability [5].

Cluster bootstrap methods require an explicit cluster structure and sampling
assumptions [7]. Environmental monitoring can also be preferential: where and
when observations are taken may depend on the underlying process [8]. The new
analysis therefore controls observed sampling volume while retaining temporal
clustering and preferential monitoring as unresolved explanations. Relative to
these established methods, the contribution is an auditable application linking
rare-event concentration, case-mix diagnostics and paired decision uncertainty
in one frozen environmental ML evidence chain; no new estimator is claimed.

## 3. Research Questions

The primary question is:

> How reliably can routine river-water chemistry estimate contemporaneously
> measured dissolved oxygen at monitoring stations excluded from training?

The portfolio extension addresses four secondary questions:

1. Do row-level frozen artifacts reproduce the published V3/V4 metrics and
   station-fold boundaries?
2. How concentrated are rare `DO < 4 mg/L` events across stations?
3. Does error vary across calendar periods after reducing changes in station
   composition?
4. At what hypothetical false-negative/false-positive cost ratios does the
   preferred development rule change?

No question asks whether the model forecasts future DO, establishes a causal
environmental mechanism, or is ready for regulatory use.

## 4. Dataset and Provenance

The source is *River Water Quality Monitoring 1990 to 2024 — All Parameters*,
published by OpenDataNI/NIEA under the UK Open Government Licence [6]. The
source catalogue warns that extreme values may include genuine events as well
as errors caused by sampling, contamination, or typographical mistakes.

| Property | Historical verified value | Evidence |
|---|---:|---|
| Raw rows / columns | 178,680 / 40 | `research_upgrade_v3/phase2b0/DATA_RECOVERY_REPORT.md` |
| Raw stations | 1,311 | same |
| Modelling rows / stations | 151,031 / 840 | `research_outputs/manifest.json` |
| Dates | 1990-01-02 to 2024-12-11 | same |
| V3 development rows / stations | 119,690 / 672 | recomputed from V3 predictions |

The target is the original DO measurement in mg/L. Rows with missing targets
and six qualified targets were excluded historically. Predictor values reported
with censor qualifiers retained their numeric export values plus explicit
indicator features. Predictor missingness was handled by training-fold median
imputation with missingness indicators. The raw and complete processed tables
are ignored by Git; frozen predictions and manifests are public.

An initial recovery attempt on 2026-11-03 failed. The later evidence sprint
retrieved the official CSV with SHA-256 exactly matching the historical source;
the original cleaning code reproduced both processed CSV and audit JSON hashes.
The raw source has 178,680 rows, 40 fields and 1,311 stations; the rebuilt
modelling table has 151,031 rows and 840 stations. These claims are now directly
verified. An ArcGIS count query agrees, and a normalized two-row API spot check
is reported separately from full byte identity.

## 5. Experimental Methodology

### 5.1 Predictors and preprocessing

The historical full feature set combines routine chemistry, censor flags,
missingness information, and cyclical day-of-year context. Station identifiers,
coordinates, database identifiers, raw date identifiers, target, and target
qualifier are excluded from predictors. Pipelines learn preprocessing only from
the applicable training rows. Synthetic tests verify this boundary.

### 5.2 Historical development sequence

- **V1:** fixed Random Forest evaluated under random-row, unseen-station,
  future-year, and spatiotemporal designs; feature ablation and residual
  diagnostics were retained.
- **V2:** ten predefined spatiotemporal splits, one basin holdout, reduced
  ablations, interval coverage, importance stability, and fixed model-family
  checks. These are robustness analyses on previously studied data.
- **V3:** frozen nested station-grouped model/weight selection targeted low-DO
  reliability on a 119,690-row development partition. The baseline was a fixed
  Random Forest; the selected procedure chose among Random Forest, Extra Trees,
  and HistGradientBoosting configurations crossed with weights 1, 2, 4, and 8.
- **V4:** one fixed, balanced logistic classifier at probability threshold 0.5
  on the same development folds. It changed the objective from regression to
  classification and is not a direct V3 upgrade.

### 5.3 Portfolio extension

The extension performs no fitting. It reads the checksum-verified V3/V4 OOF
predictions, enforces identity invariants, recomputes metrics, and produces
descriptive station, time, and cost analyses under a written protocol.

## 6. Validation Design

Station grouping is the central protection against location leakage. V3 uses
five outer folds with 672 stations, and each station appears in exactly one
outer validation fold. Inner selection uses four station-grouped folds within
each outer training partition. This design estimates transfer to other stations
within the same historical monitoring system; it does not estimate transfer to
another country or a future monitoring regime.

The project retains several validation settings because each answers a different
question. Random-row evaluation approximates interpolation among known sites;
station-grouped evaluation tests unseen-site transfer; temporal evaluation tests
later observations that often include known sites; and spatiotemporal evaluation
holds out later rows at stations excluded from training. Their metrics are not
interchangeable.

Earlier holdouts have been repeatedly inspected and cannot be relabelled as
fresh confirmation. A V4 audit found that the then-current official export was
byte-identical to the historical source. No external predictions were made.

## 7. Statistical Analysis

For observations \(i=1,\ldots,n\), MAE is

\[
\mathrm{MAE}=\frac{1}{n}\sum_i |\hat y_i-y_i|.
\]

Low-DO MAE restricts the sum to measured \(y_i<4\) mg/L. Recall is
\(TP/(TP+FN)\) and precision is \(TP/(TP+FP)\); all denominators and raw counts
are retained.

Historical V3 uncertainty uses paired bootstrap resampling of whole stations,
not rows. This respects the principal sampling cluster but does not create a new
population. The extension quantifies event concentration by station shares
\(p_s=n_s/\sum_s n_s\), with Herfindahl index \(H=\sum_s p_s^2\) and inverse
effective count \(1/H\). The effective count is a concentration analogy, not a
claim that exactly 29.7 statistically independent observations exist.

Time bands are fixed at 1990–1999, 2000–2009, 2010–2019, and 2020–2024. Pooled
MAE is accompanied by a station-macro sensitivity analysis restricted to the
173 stations represented in all bands. Hypothetical decision cost is

\[
C(r)=r\,FN+FP, \qquad r=C_{FN}/C_{FP}.
\]

Pairwise breakpoints are solved algebraically; no cost value is fitted to the
data. The sprint additionally draws 5,000 paired samples of 672 complete
stations with replacement (seed 20261103) and reports percentile 95% intervals.
Model fits remain fixed. Cost differences are normalized per 10,000 observations
using each replicate's row count; fractions favoring a rule describe bootstrap
stability, not posterior probabilities. No denominator was undefined in these
5,000 draws. Dependence between stations and model fitting/selection uncertainty
are outside this conditional analysis.

To control sampling intensity, each station retains n_s observations and receives
independent binomial events with the pooled event probability. We simulate
20,000 null replicates for minimum station counts 1, 10, 30 and 100. The central
95% null range is a reference distribution, not an interval for the observed
HHI. The independent constant-rate null is a benchmark whose violation can also
reflect temporal clustering, case mix or monitoring practice.

## 8. Results

### 8.1 Historical robustness

Across ten predefined V2 spatiotemporal splits, mean MAE was 0.6793 mg/L (SD
0.0353). Low-DO subsets contained only 3–21 rows per split and had MAE
2.8846–4.7678 mg/L. Nine of ten splits overpredicted every low-DO observation.
These are historical reported values; they demonstrate partition sensitivity
but are not ten independent datasets.

### 8.2 V3 low-DO trade-off

| Metric | Baseline | Selected procedure | Change |
|---|---:|---:|---:|
| Overall MAE (mg/L) | 0.8797 | 0.9516 | +0.0719 |
| Low-DO MAE (mg/L) | 3.3235 | 2.3613 | -0.9622 |
| Low-DO bias (mg/L) | 3.3080 | 2.2373 | -1.0707 |
| Recall | 0.1293 | 0.3641 | +0.2348 |
| Precision | 0.7903 | 0.5576 | -0.2327 |
| False negatives | 660 | 482 | -178 |
| False positives | 26 | 219 | +193 |

Historical paired station-bootstrap 95% intervals exclude zero beneficially for
low-DO MAE and recall, and exclude zero adversely for overall MAE and precision.
The frozen decision rule therefore supported the selected procedure for its
bounded co-primary objectives. It did not establish a globally better model.

The newly executed paired station bootstrap gives low-DO MAE change -0.9622
mg/L [95% interval -1.0838, -0.8514] and recall change +0.2348
[0.1878, 0.2799]. Overall MAE increases by 0.0719 [0.0643, 0.0799] and precision
falls by 0.2327 [-0.3123, -0.1264]. These new intervals have a separately recorded
seed and do not replace historical frozen uncertainty outputs. Absolute model
intervals are in the [sprint statistical report](../research_extension/sprint/SCIENTIFIC_REPORT.md).

### 8.3 Attribution boundary

The formal outer comparison changes architecture, non-weight hyperparameters,
and weight. It cannot identify a weight-only causal effect. In saved inner-grid
results, 640 exact comparisons holding architecture, hyperparameters, folds,
preprocessing, and training flow constant all moved low-DO MAE and recall in a
beneficial direction when changing weight 1 to 8. Because inner folds are reused
and the analysis is post hoc, this is strong exploratory consistency evidence,
not 640 independent replications.

### 8.4 V4 classifier failure trade-off

The fixed classifier produced TP 699, FP 9,517, TN 109,415, and FN 59: recall
0.9222, precision 0.0684, and F1 0.1274. High recall was obtained by generating
false alarms on approximately 8.0% of measured non-low-DO rows. The negative
result is scientifically useful because it shows why recall alone is not an
adequate selection criterion.

### 8.5 Station concentration

The 758 low-DO observations occur at 115 stations; 47 stations have exactly one
event. The top station contributes 8.6% of events, the top five 31.9%, and the
top ten 49.5%. \(H=0.0337\), so \(1/H=29.7\) equally represented stations.

![Low-DO station concentration](../figures/low_do_station_concentration.png)

Controlling sampling volume gives observed HHI 0.033723 against null mean
0.003523, central 95% reference range [0.003295, 0.003773]. None of 20,000 draws
reaches the observation (add-one Monte Carlo tail fraction 0.000050). Excluding
stations with fewer than 10, 30 or 100 records preserves this discrepancy.
Sampling volume alone is therefore insufficient under the independent
common-rate benchmark. This does not identify geographic low-oxygen risk.

![Sampling intensity control](../research_extension/sprint/sampling_control.png)

### 8.6 Descriptive temporal sensitivity

Baseline pooled MAE declines from 1.211 mg/L in 1990–1999 to 0.608 mg/L in
2020–2024. Among the same 173 stations represented in all periods, station-macro
MAE declines from 1.176 to 0.560 mg/L. The selected procedure shows the same
direction. This suggests station membership alone is insufficient to explain
the pattern, but does not distinguish changes in measurement practice,
covariates, event composition, or relationships.

![Temporal sensitivity](../figures/temporal_robustness.png)

Temporal composition also changes: low-DO prevalence is 1.120%, 0.384%, 0.486%
and 0.611% across the four periods, while target SD is 2.588, 1.774, 1.627 and
1.635 mg/L. Baseline low-DO MAE is 3.110, 3.957, 3.193 and 3.085 mg/L, so the
overall decline is not evidence of steadily improving rare-event reliability.
The [temporal composition table](../research_extension/sprint/temporal_composition.csv)
retains counts, prevalence, target quantiles and both model errors.

### 8.7 Decision breakpoints

V3 selected has lower hypothetical cost than V3 baseline only when
\(C_{FN}/C_{FP}>1.084\). V4 classifier crosses V3 baseline at 15.792 and V3
selected at 21.981. These are transparent implications of development counts,
not recommended real-world valuations.

At ratio 1, V3 selected-minus-baseline cost difference per 10,000 rows is +1.25
[paired cluster 95% interval -4.04, 6.32]; at ratio 2 it is -13.62
[-24.51, -4.28]. At ratio 25, classifier-minus-V3-selected is -106.69
[-410.87, 152.11]. Thus the point crossing does not guarantee a stable preference.
V4 recall has interval [0.8896, 0.9482] and precision [0.0490, 0.0897].

![Decision uncertainty](../research_extension/sprint/cluster_cost_uncertainty.png)

## 9. Robustness and Failure Analysis

### 2025 acquired temporal confirmation

DAERA/26-784, published 2026-10-26, supplies previously unused 2025 observations
from the same programme [9]. A local protocol and adapter/data/model hashes
were committed at `2a55e5a`. Local records are consistent with freezing before
the recorded single evaluation, but do not independently establish its exact
start time or exclude earlier unrecorded inference. The freeze JSON records
13:50:32 UTC, the unsigned commit 13:50:57 UTC, and the prediction file's local
creation time 13:50:59 UTC on 2026-11-03. The execution log lacks a UTC start
timestamp. This is a local freeze, not third-party preregistration; the
[chronology audit](../audits/final_release/FREEZE_CHRONOLOGY.md) preserves Git
objects, log hashes and the evidential limits. The unchanged
Phase4 model uses its original training imputer, 25 predictors and <4 mg/L rule.
The new source's temperature field is unused. Two conflicting identity records
were excluded together before freezing; both lack targets. Subsequent missing-
target exclusion leaves 3,490 observations at 494 stations, with zero historical
station/date overlap.

The original release has 2,590 missing DO targets among 6,080 rows (42.60%).
Both identity-conflict exclusions have missing DO; 2,588 additional target-
missing rows are excluded after resolving identity. No target is imputed.
The 3,490-row evaluation is thus a measured-target subset of 503 source
stations, representing 494 stations. Missingness may depend on sampling
practice or environmental conditions; the available evidence does not establish
missing-at-random sampling or performance on the unmeasured targets.

| 2025 quantity | Estimate | Whole-station 95% percentile interval |
|---|---:|---|
| MAE (mg/L) | 0.6432 | [0.5896, 0.7176] |
| Low-DO MAE (mg/L) | 2.2888 | [1.9237, 2.6796] |
| Recall | 0.1500 | [0.0000, 0.3462] |
| Precision | 1.0000 | Conditional [1,1]; 1,844/5,000 replicates undefined |

TP=3, FP=0, TN=3470 and FN=17; RMSE=1.6872 mg/L and R²=0.4150.
Only nine low-DO stations fail the predeclared ten-station support criterion.
All three detections occur at one station. Conditional bootstrap precision is
degenerate because resampling cannot introduce unobserved false positives; the
observed 1.00 is not evidence of robust perfect precision.
Twenty events at nine stations are not twenty independent replications;
three detections at one station provide just one detected station cluster.
The station bootstrap preserves within-station dependence but cannot create
new event-station information or remedy this sparse support.

391 stations (2,777 rows) were in model training; 103 stations (713 rows) were
absent from training. The latter have only five low-DO observations at two
stations, all missed. Since 493 stations occur somewhere in the historical
programme, this test establishes later-period evidence, not cross-region
transportability or confirmation of the V3 weighted procedure.

Suspended-solids missingness rises from 26.00% in historical training to 75.10%
in 2025. One source DO value of 94 mg/L produces an 85.69 mg/L error and
materially raises RMSE; its validity remains unresolved, and it is retained
under the frozen no-outlier-filter rule. Lower MAE than the historical Phase4
holdout (0.8312) coexists with higher RMSE (historical 1.2911). Population and
measurement differences prevent interpreting that comparison as improvement.

A separately labelled **post-hoc diagnostic**, using only saved predictions,
omits the single 94 mg/L row: n=3,489, MAE=0.618805 mg/L,
RMSE=0.861795 mg/L and R²=0.740684. The source pairs 94 mg/L with
10% saturation at 18°C; the same station's other nonmissing 2025 DO values
range from 8.6 to 13.4 mg/L. This internal inconsistency is suspicious, but
neither an error nor a replacement value is verified. The row supplies 73.92%
of primary squared error. Removing it also changes target variance, so the
R² increase is not evidence of a model improvement. Low-DO MAE, recall and
TP/FP/FN remain unchanged; TN changes from 3,470 to 3,469. No model or threshold
was changed and the primary table and its intervals remain the frozen results.
This diagnostic is not a second confirmation test and has no newly claimed
confirmatory interval. See the
[full sensitivity analysis](../research_extension/final_release/POST_HOC_SENSITIVITY.md).

![2025 detection failure](../research_extension/ni2025_confirmation/temporal_confirmation.png)

The [full confirmation report](../research_extension/ni2025_confirmation/TEMPORAL_CONFIRMATION_REPORT.md)
retains counts, exclusions, strata, missingness shifts and all undefined metrics.

### Historical replay and external compatibility

The exact source reconstruction enables a new end-to-end replay of the fixed
historical Phase4 pipeline: 119,690 training rows and 31,341 previously inspected
holdout rows, seed 42, the original 25 predictors, and the saved selected
150-tree Random Forest configuration. Retraining yields MAE 0.8311906044 mg/L,
RMSE 1.2910610827 and R² 0.5390543500. The maximum per-row prediction difference
from the historical table is below 1e-10 mg/L in both replay executions. This is computational reproduction,
not new scientific validation. Feature selection and the 2,560-fit V3 inner
grid were not rerun; their branch/HEAD gates remain unchanged.

An external compatibility pilot on EA England river records for 2025 retrieved
430 determinand observations from 49 exact samples at six stations. Units and
sample identities are accessible, but BOD is available in 29 samples and
suspended solids in nine, never together. Intermittent missingness can be
handled by the frozen imputer, but equivalence of BOD incubation/ATU,
alkalinity basis, conductivity reference temperature and soluble-reactive-P
methods is not established by the NI export. These method gaps and insufficient
station support prevent the pilot from passing the confirmation gate. No
EA predictions or performance claims were generated. Full details and
source links are in the
[compatibility audit](../audits/evidence_breakthrough/EXTERNAL_COMPATIBILITY_REPORT.md).

The main result survives several checks: five outer station folds, paired
membership, station-clustered bootstrap intervals, exact artifact
reconstruction, matched inner weight comparisons, repeated earlier
spatiotemporal splits, and a balanced-station time sensitivity analysis.

The failures are equally important:

- most V3 low-DO events remain missed (FN rate 0.6359);
- the selected procedure raises overall error and false alarms;
- V4 obtains high recall with extremely low precision;
- aggregate prediction-interval coverage historically concealed very poor
  low-DO coverage;
- rare events are concentrated across a small number of stations;
- prior data reuse limits prospective interpretation; and
- no new region or time period has confirmed the effect.

## 10. Discussion

WaterSense is strongest as a study of objective mismatch. Standard regression
selection rewards performance where observations are abundant. Weighting rare
events or switching to a classifier reallocates errors, but the preferred
allocation depends on an application-defined loss function. The data alone
cannot decide how many false alarms equal one missed low-oxygen observation.

The concentration analysis changes the apparent evidence scale without
discarding information. Row-level performance is still relevant, but station
clusters—not individual measurements—are the more credible unit for uncertainty
about geographic transfer. This is why the project reports both event counts
and station structure.

The temporal result is deliberately restrained. Lower later-period error could
reflect improved measurement consistency, different sampling, a narrower target
distribution, or model access to patterns learned from all eras. It does not
prove that the model has improved over time and does not support forecasting.

## 11. Limitations

1. Data come from one Northern Ireland monitoring system.
2. Water temperature, flow, catchment state, and other physical drivers are
   absent from the frozen predictor set.
3. Measurements within station and across repeated splits are dependent.
4. Rare-event station support is limited and uneven.
5. Historical holdouts were inspected during iterative research.
6. V3’s outer comparison does not isolate weighting from model selection.
7. V4 changes the objective and is not directly comparable as an upgrade.
8. Time-band analysis is descriptive rather than prospective.
9. Prediction intervals can fail under spatial or temporal distribution shift.
10. No ecological, regulatory, or financial cost ratio has been established.
11. Cross-region validation and confirmation of V3 weighting remain absent;
    the 2025 same-programme test has just nine low-DO stations and one detected
    station; its complete-target selection excludes 42.60% of source rows.
12. Applicant-specific personal contribution has not yet been authenticated.
13. Local freeze timestamps are not independent proof of the first inference;
    the 94 mg/L source value is unresolved and its omission is post hoc.

## 12. Conclusion

WaterSense AI demonstrates that rigorous evaluation can turn an apparently
successful regression model into a more informative scientific result. The
selected procedure materially improves low-DO development performance, but the
cost appears in overall error and false alarms, and a high-recall classifier
amplifies that trade-off dramatically. Rare-event evidence is concentrated
across stations, reinforcing the need for group-aware validation and
cluster-aware uncertainty.

The 2025 result confirms an observed failure pattern in newly acquired records:
low overall absolute error can coexist with missing most low-DO observations.
Further decisive evidence requires a compatible independent region or a
separately frozen V3 model, adequate event-station support and an explicit
decision policy. The 2025 outcomes cannot now be reused as an untouched test.

## 13. References

1. Roberts, D. R., et al. (2017). Cross-validation strategies for data with
   temporal, spatial, hierarchical, or phylogenetic structure. *Ecography*,
   40, 913–929. <https://doi.org/10.1111/ecog.02881>
2. Breiman, L. (2001). Random Forests. *Machine Learning*, 45, 5–32.
   <https://doi.org/10.1023/A:1010933404324>
3. Pedregosa, F., et al. (2011). Scikit-learn: Machine Learning in Python.
   *Journal of Machine Learning Research*, 12, 2825–2830.
   <https://www.jmlr.org/papers/v12/pedregosa11a.html>
4. Saito, T., & Rehmsmeier, M. (2015). The Precision-Recall Plot Is More
   Informative than the ROC Plot When Evaluating Binary Classifiers on
   Imbalanced Datasets. *PLOS ONE*, 10(3), e0118432.
   <https://doi.org/10.1371/journal.pone.0118432>
5. Lei, J., G’Sell, M., Rinaldo, A., Tibshirani, R. J., & Wasserman, L. (2018).
   Distribution-Free Predictive Inference for Regression. *Journal of the
   American Statistical Association*, 113(523), 1094–1111.
   <https://doi.org/10.1080/01621459.2017.1307116>
6. OpenDataNI / Northern Ireland Environment Agency. *River Water Quality
   Monitoring 1990 to 2024 — All Parameters*. UK Open Government Licence.
   <https://www.data.gov.uk/dataset/15ec8080-ee1c-469b-858e-546d2fb57c27/riverwaterqualitymonitoring-1990to2024-allparameters13>

7. Field, C. A., & Welsh, A. H. (2007). Bootstrapping clustered data.
   *Journal of the Royal Statistical Society: Series B*, 69(3), 369–390.
   <https://doi.org/10.1111/j.1467-9868.2007.00593.x>
8. Diggle, P. J., Menezes, R., & Su, T.-l. (2010). Geostatistical inference under
   preferential sampling. *Journal of the Royal Statistical Society: Series C*,
   59(2), 191–232. <https://doi.org/10.1111/j.1467-9876.2009.00701.x>

9. DAERA / NIEA (2026). DAERA/26-784: River water quality monitoring data for
   all of Northern Ireland for 2025. Published 26 October 2026. Annex A.
   <https://www.daera-ni.gov.uk/publications/daera26-784-river-water-quality-monitoring-data-all-northern-ireland-2025>

## 14. Reproducibility Statement

The repository preserves code, frozen configurations, fold assignments,
row-level compressed predictions, bootstrap summaries, tests, and hashes.
Portfolio verification is run with:

```bash
python3 scripts/run_portfolio_analysis.py
python3 scripts/verify_scientific_sprint.py
python3 -m unittest tests.test_portfolio_analysis -v
```

The script fails on input-hash, membership, target, duplicate-identity, or
station-fold mismatch. Full historical retraining additionally requires the
exact ignored public export documented in `docs/dataset.md`. Reproducibility of
development artifacts does not create statistical independence.

## 15. AI Assistance and Contribution Disclosure

AI systems provided substantial assistance with coding, testing, statistical
checks, figure generation, prose drafting, repository auditing, and portfolio
organization. No claim is made that the work was completed without AI.

`[OWNER CONFIRMATION REQUIRED: identify the research questions, design choices,
code, analyses, interpretations, and revisions personally performed or
independently verified by the applicant before using first-person authorship
language.]`

The scientific claims in this manuscript are limited to traceable repository
artifacts. AI assistance does not substitute for owner review or external peer
review.
