# PSL IBSAI — Artificial Intelligence portfolio brief

> **Attribution gate:** the technical result is traceable. Personal authorship
> wording requires the owner to confirm which design, implementation, analysis,
> and review tasks were personally completed or independently verified.

## One-page research summary

**New temporal evidence — personal contribution awaiting confirmation:** one
frozen Phase4 model was evaluated once on 3,490 new-year records / 494 stations.
Its MAE was 0.6432 mg/L but it detected only 3 of 20 low-DO observations. The
nine event stations fail the prespecified support criterion. Precision 1.00 is
based on three predictions at one station; 36.88% of bootstrap precision
replicates are undefined. The result strengthens the failure narrative rather
than establishing warning readiness or independent V3 confirmation.

**Final CV draft — owner confirmation required:** executed a frozen temporal
evaluation and documented how satisfactory average error concealed 85% missed
rare events, with exact provenance and station-level uncertainty.

**Evidence breakthrough (owner contribution unconfirmed):** exact source and
cleaned-data recovery now support a fixed-model end-to-end replay, reproducing
historical holdout MAE 0.8311906 mg/L. A 2025 England pilot yielded 430
measurements / 49 samples / six stations; mapping and support gaps prevented
external scoring. Reproduction and external generalization remain separate.

WaterSense AI is an empirical AI reliability study using public river-monitoring
data. It asks whether models trained on routine chemistry can estimate
contemporaneous dissolved oxygen at unseen stations and, more importantly,
whether aggregate performance remains meaningful for rare low-oxygen events.

The project progresses from ordinary regression evaluation to structured
robustness analysis. It compares simple and nonlinear model families, separates
stations during validation, fits preprocessing inside training folds, checks
spatiotemporal and river-basin transfer, evaluates uncertainty coverage, and
preserves row-level predictions and manifests. The historical modelling data
contain 151,031 eligible observations from 840 Northern Ireland stations over
1990–2024.

The frozen V3 experiment targets measured DO below 4 mg/L using nested
station-grouped development cross-validation. The selected procedure reduces
low-DO MAE from 3.3235 to 2.3613 mg/L and increases recall from 0.1293 to 0.3641.
The same procedure worsens overall MAE from 0.8797 to 0.9516 mg/L, lowers
precision from 0.7903 to 0.5576, and increases false positives from 26 to 219.
This is a useful AI result because it reveals objective conflict rather than
hiding the cost of rare-event optimization.

V4 tests a different inductive choice: a fixed balanced logistic classifier.
It reaches 0.9222 recall but only 0.0684 precision and produces 9,517 false
positives. The experiment is retained as a negative finding, not presented as a
performance victory. Since V3 and V4 reuse the development population and use
different objectives, they are not a direct improvement comparison.

The new extension strengthens reliability interpretation without new model
selection. The 758 low-DO rows are concentrated at 115 stations, and the top ten
stations contain 49.5% of events. A balanced-station time analysis shows lower
descriptive MAE in later periods, but the manuscript refuses to call this
future generalization because training uses other rows from all eras. Analytic
cost breakpoints show exactly when different error profiles would be preferred
under hypothetical costs.

The project demonstrates empirical AI judgment: validation matches the intended
generalization unit; imbalance is evaluated with precision, recall, raw counts,
and subgroup error; negative results are preserved; and reproducibility is
separated from independent confirmation. It is an educational research system,
not a safety classifier, forecast, or deployed environmental decision tool.

## Three-sentence project introduction

**Final sprint evidence:** sampling volume alone is insufficient under a
constant-rate independent-observation null (observed HHI 0.03372; null mean
0.00352). This does not identify geographic risk. Whole-station paired bootstrap
intervals show that the classifier's point cost advantage at ratio 25 remains
uncertain; temporal case mix and target spread also change across decades.

**CV supplement — owner confirmation required:** audited sampling effort,
case-mix changes and cluster uncertainty to assess whether apparent performance
gains support a stable decision preference.

**Additional CV draft — owner confirmation required:** audited exact data/model
provenance and external measurement compatibility; retained an unresolved
external-validation gate instead of inferring reliability from runnable code.

WaterSense AI evaluates dissolved-oxygen models under station, time, basin, and
rare-event distribution shift. The central empirical result is that optimizing
low-oxygen reliability improves subgroup MAE and recall while worsening overall
error and false alarms; a dedicated classifier pushes recall higher but becomes
impractically imprecise. The project contributes a transparent, reproducible
example of responsible AI evaluation in which failure analysis and evidence
boundaries matter more than a single headline score.

## Two-line CV description — draft pending owner confirmation

**Final release qualification:** 2,590/6,080 source targets are missing (42.60%);
performance is conditional on measured DO. Only nine stations have low DO and
all three detections occur at one station. The post-hoc 94 mg/L sensitivity
leaves 17/20 misses unchanged. Local freeze records are not independent
preregistration. Every first-person statement below is a rehearsal template
requiring the [task-specific owner checklist](OWNER_CONTRIBUTION_CONFIRMATION.md).

**WaterSense AI — empirical AI reliability research:** developed and audited a
station-grouped ML workflow over 151k river observations, with nested CV,
rare-event analysis, uncertainty, and reproducible row-level evidence. Exposed
the recall–precision–MAE trade-off and preserved a high-recall/low-precision
classifier as a negative result rather than a deployment claim.

## Detailed CV description — draft pending owner confirmation

- Evaluated regression and classification objectives for rare low dissolved
  oxygen using public environmental data across 840 stations and 35 years.
- Implemented leakage-aware pipelines with fold-local preprocessing and
  station-grouped nested cross-validation.
- Compared Random Forest, Extra Trees, HistGradientBoosting, linear baselines,
  and a fixed logistic classifier without converting reused development results
  into false external validation.
- Recomputed metrics from 239,380 paired V3 prediction rows and 119,690 V4
  classifier rows under checksum and identity assertions.
- Added station-concentration, balanced-period, and analytic cost-sensitivity
  analyses, with tests and generated manifests.
- Documented failure modes, privacy/release boundaries, missing physical
  covariates, AI assistance, and the need for a frozen external evaluation.

## Sixty-second oral explanation

“WaterSense AI is an empirical study of how AI reliability changes when the
important cases are rare and clustered. I used station-grouped validation so
the model could not learn and test on the same monitoring locations. A
low-oxygen-oriented procedure improved subgroup MAE and recall, but increased
overall error and false alarms; a separate classifier reached 92% recall but
only 6.8% precision. Rather than selecting the most dramatic number, I analysed
why the trade-off occurs, how events concentrate across stations, and which
hypothetical error costs would prefer each rule. A new 2025 temporal test
reinforces the failure finding; cross-region validation remains outstanding.
The main result is a reproducible example of
responsible AI evaluation: the objective, validation unit, and failure costs
must match the intended use.”

## Three-minute research presentation script

“I studied whether routine river chemistry can estimate dissolved oxygen at
monitoring stations absent from training. The data are a useful AI test case:
there are many observations, but they are repeated within stations; important
low-oxygen cases are rare; and the monitoring system changes across decades.

The project therefore uses several validation regimes rather than one random
split. Station-grouped folds test spatial transfer. Temporal and
spatiotemporal checks ask different questions. Preprocessing is fit inside each
training boundary, and target or location identifiers are excluded from the
model.

In the primary frozen experiment, the selected procedure improved low-oxygen
MAE by 0.9622 mg/L and recall by 0.2348. But overall MAE worsened by 8.17%,
precision decreased, and there were 193 additional false positives. This is an
objective trade-off, not a universal improvement.

I also evaluated one fixed logistic classifier. Its recall was 0.9222, which
looks impressive in isolation. Its precision was only 0.0684 and it generated
9,517 false positives. Keeping this negative result was important: it shows how
class balancing can change the error surface without solving the decision
problem.

The extension adds three analyses from frozen predictions. First, low-oxygen
events are concentrated: 758 rows occur at 115 stations, and half occur at ten
stations. Second, a balanced-station time analysis separates some station-
composition change from descriptive temporal variation, while explicitly
remaining non-prospective. Third, a cost equation shows that the classifier is
preferred to the selected regression rule only if one false negative costs more
than about 22 false positives.

My conclusion is that responsible AI requires more than model fitting. It
requires matching validation to deployment structure, publishing failure
counts, resisting post-hoc claims, and knowing when the evidence is not yet
enough. After observing the 2025 failures, the next step is a separately frozen,
adequately supported test in another region; these 2025 outcomes are no longer
an untouched confirmation set.”
