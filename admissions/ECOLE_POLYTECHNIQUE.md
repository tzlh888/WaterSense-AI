# École Polytechnique — Mathematics & Computer Science portfolio brief

> **Attribution gate:** the scientific descriptions below are evidence-backed.
> Any first-person claim about the applicant’s own work must remain draft text
> until the owner completes the contribution checklist.

## One-page research summary

**New temporal evidence — owner contribution unconfirmed:** after a committed
pre-prediction freeze, the historical model was evaluated on 3,490 newly acquired
2025 records from 494 stations. MAE was 0.6432 mg/L, but recall was 3/20=15%.
Nine event-bearing stations fall below the fixed support criterion; precision
1.00 relies on three detections at one station and has 1,844 undefined bootstrap
replicates. This provides a concrete new-period failure result, while independent
regional transfer and the V3 weighting effect remain unconfirmed.

**Final CV draft — owner confirmation required:** evaluated a frozen model on
new-year monitoring records, reporting low average error alongside 85% missed
low-oxygen events and explicitly accounting for sparse station support.

**Evidence breakthrough (draft attribution remains unconfirmed):** the official
raw bytes and deterministic cleaned artifacts have now been recovered exactly.
Refitting the frozen historical configuration reproduces 31,341 predictions to
within 1e-10 mg/L. An external England pilot was audited at exact sample level;
measurement-definition gaps prevented scoring. This demonstrates a reproducibility
result and an evidence boundary, not external performance confirmation.

WaterSense AI asks a mathematical reliability question hidden inside an
environmental machine-learning problem: when observations are clustered by
monitoring station and rare events are unevenly distributed, what does an
apparently good average error actually measure?

The project studies Northern Ireland river-monitoring records from 1990–2024.
Historical manifests describe 151,031 eligible observations from 840 stations.
The primary V3 experiment uses 119,690 development observations from 672
stations and nested cross-validation that keeps every station within a single
outer fold. Preprocessing is fitted inside training boundaries, and the target,
target qualifier, station identity, and location metadata are excluded from
predictors.

The main result is a constrained trade-off. Relative to a fixed Random Forest
baseline, a frozen low-oxygen-oriented selection procedure reduces mean
absolute error for measured DO below 4 mg/L from 3.3235 to 2.3613 mg/L and
raises recall from 0.1293 to 0.3641. It simultaneously raises overall MAE from
0.8797 to 0.9516 mg/L, reduces precision from 0.7903 to 0.5576, and creates 219
false positives instead of 26. Paired uncertainty resamples complete stations,
not individual rows.

The extension makes dependence visible. Although there are 758 low-DO rows,
they occur at 115 stations, 47 stations have only one event, and half of all
events occur at the ten most event-rich stations. The Herfindahl concentration
index is 0.0337, corresponding to 29.7 equally represented stations. This is
not a replacement sample size; it is a compact demonstration that row count and
effective geographic evidence are different objects.

The project also formulates model choice as an explicit loss problem. For cost
`r × FN + FP`, the selected V3 procedure overtakes the baseline at
`r = 193/178 = 1.084`. A high-recall V4 classifier overtakes V3 selected only
above `r = 9298/423 = 21.981`, because its 59 false negatives come with 9,517
false positives. The preferred rule therefore cannot be inferred from model
metrics without specifying a cost ratio.

This work demonstrates group-aware experimental design, exact metric
reconstruction, clustered uncertainty, concentration measures, sensitivity
analysis, and careful separation between descriptive and causal statements. It
does not claim cross-region validation, forecasting, deployment readiness, or a
weight-only causal effect. The mathematically strongest outcome is the ability
to state precisely what the evidence does—and does not—identify.

## Three-sentence project introduction

**Final sprint evidence:** preserving each station's observation count under a
common-rate binomial benchmark yields mean HHI 0.00352 against observed 0.03372;
the contrast survives minimum-record sensitivities. Temporal clustering and
monitoring selection remain unresolved. A 5,000-draw paired whole-station
bootstrap quantifies both the MAE/recall benefit and its overall-error/precision
cost. At FN/FP ratio 25, classifier-minus-V3 cost has a 95% interval spanning
zero. These conclusions concern fixed development predictions.

**CV supplement — owner confirmation required:** examined whether station
sampling volume explains rare-event concentration and quantified paired
station-cluster uncertainty in hypothetical error-cost comparisons.

**Additional CV draft — owner confirmation required:** reconstructed the exact
historical data-to-prediction computation and audited independent river data for
sample identity, measurement compatibility and censoring before model access.

WaterSense AI studies whether routine river chemistry can estimate dissolved
oxygen at monitoring stations excluded from training. Its central finding is a
quantified reliability trade-off: improving rare low-oxygen detection reduces
misses but worsens overall error and false alarms, while rare events are highly
clustered across stations. The project uses nested group validation,
station-clustered uncertainty, concentration measures, and explicit error-cost
breakpoints to prevent an attractive average score from becoming an
overstated scientific claim.

## Two-line CV description — draft pending owner confirmation

**WaterSense AI — environmental ML reliability study:** analysed 151k historical
river records using station-grouped validation and reproducible artifact audits.
Quantified rare-event concentration and the mathematical trade-off among MAE,
recall, precision, and decision costs; 2025 temporal test exposed 85% low-DO misses.

## Detailed CV description — draft pending owner confirmation

- Built and audited a group-aware dissolved-oxygen research pipeline spanning
  840 monitoring stations and 35 years of public observations.
- Used nested station-grouped cross-validation and station-clustered bootstrap
  summaries to account for repeated measurements within monitoring sites.
- Reconstructed 119,690 paired out-of-fold predictions and showed that a
  low-DO-oriented procedure improved low-DO MAE by 0.9622 mg/L while increasing
  overall MAE by 0.0719 mg/L and false positives by 193.
- Introduced a station-concentration analysis: 758 rare events at 115 stations
  correspond to 29.7 equally represented stations under inverse HHI.
- Derived decision-cost breakpoints algebraically and documented why no method
  can be called operationally preferable without a real loss function.
- Preserved negative results, published code/tests/manifests, and disclosed
  substantial AI assistance and the absence of independent external validation.

## Sixty-second oral explanation

“WaterSense AI began as a dissolved-oxygen regression project, but the more
interesting question became statistical: can a good average error hide failure
on rare events? I kept monitoring stations separated during validation because
repeated samples from one site are dependent. A low-oxygen-oriented procedure
reduced rare-event MAE from 3.32 to 2.36 mg/L and nearly tripled recall, but it
also worsened total MAE and increased false positives from 26 to 219. I then
measured how concentrated the 758 low-oxygen observations were: half came from
only ten stations, and the distribution had an inverse-HHI effective count of
29.7 stations. Finally, I derived the cost ratio at which one rule becomes
preferable to another. The conclusion is not that the model is ready for use;
it is that model evaluation must reflect dependence, rarity, and an explicit
decision objective.”

## Three-minute research presentation script

“My project investigates dissolved oxygen in long-term river-monitoring data.
The modelling challenge is not only nonlinear prediction. The same stations
are sampled repeatedly, low-oxygen events are rare, and measurement coverage
changes over 35 years. A random row split would therefore answer an easier and
less useful question.

The core design keeps monitoring stations disjoint. The main V3 experiment has
119,690 development observations from 672 stations in five outer folds, with
four group-aware inner folds for model and weight selection. Preprocessing is
learned only from training rows. This lets the outer predictions estimate
transfer to other stations in the same monitoring system.

The result is deliberately mixed. The selected procedure reduces MAE below 4
mg/L from 3.3235 to 2.3613 and raises recall from 0.1293 to 0.3641. However,
overall MAE increases from 0.8797 to 0.9516, precision falls, and false positives
rise from 26 to 219. Station-level bootstrap intervals show that both the benefit
and the cost are systematic within the development population.

I then asked whether 758 low-oxygen rows really represent 758 independent
pieces of evidence. They occur at 115 stations, 47 of those have one event, and
the top ten contain 49.5% of all events. If `p_s` is each station’s event share,
the concentration `sum p_s squared` is 0.0337; its inverse is 29.7 equally
represented stations. I use that only as a concentration measure, not as a
literal effective sample size.

Finally, I express decision cost as `r times false negatives plus false
positives`. The selected procedure overtakes the baseline at `r = 1.084`. A
separate high-recall classifier overtakes it only at `r = 21.981`, because the
classifier generates 9,517 false positives. The dataset cannot choose `r`.

The project’s contribution is therefore a reproducible framework for asking
what a metric means under dependence and imbalance. Its main limitation is the
absence of confirmation in an independent region. I would freeze the current rule
and test it on a later or geographically independent dataset before making any
deployment claim.”
