# Technical interview questions and evidence-grounded answer notes

## 1. Why is random row splitting inappropriate here?

Rows from the same station share location, catchment, instruments, and repeated
conditions. Putting one station on both sides can reward station-specific
interpolation. Station-grouped folds align the validation unit with transfer to
unseen monitoring locations. Evidence: `docs/research_protocol.md` and the
zero-cross-fold station check in `audits/verification_summary.json`.

## 2. What exactly improved in V3—and what became worse?

Low-DO MAE improved by 0.9622 mg/L and recall by 0.2348. Overall MAE worsened by
0.0719 mg/L, precision fell by 0.2327, and false positives increased by 193.
The correct phrase is “a bounded low-DO trade-off,” not “the model improved.”

## 3. Can the V3 gain be attributed to sample weighting?

Not completely. The outer baseline is a fixed Random Forest and the selected
procedure uses outer-specific HGB configurations plus weight 8. Saved matched
inner comparisons support weighting as a contributor, but they are post-hoc,
dependent, and not an outer-level causal isolation.

## 4. Why use station-clustered bootstrap intervals?

The model has repeated rows per station, so row bootstrap would treat dependent
measurements as independent and understate uncertainty. Resampling whole
stations preserves the main cluster structure. It still estimates uncertainty
within the observed monitoring system and does not replace external validation.

## 5. What does the effective station count of 29.7 mean?

If station event shares are `p_s`, the Herfindahl index is `sum(p_s²)=0.0337`;
its inverse is 29.7. It means the observed event concentration equals that of
29.7 equally represented stations. It is not a literal fractional sample size
or proof of independence.

## 6. Why is the V4 classifier not the best model if recall is 0.9222?

Because it has precision 0.0684: fewer than 7 in 100 positive predictions are
true low-DO observations in this development population. It produces 9,517
false positives. Whether that is acceptable depends on a real decision cost and
operational capacity, neither of which is available.

## 7. How are the decision-cost breakpoints derived?

Set the two costs equal. For V3 baseline and selected:
`660r + 26 = 482r + 219`, hence `178r = 193` and `r = 1.084`.
The calculation is exact for saved counts; the costs themselves are hypothetical.

## 8. Does lower error in 2020–2024 prove temporal robustness?

No. The OOF model for a held-out station can still train on other stations from
all periods, so the analysis is not forward chaining. Restricting to 173
stations represented in every decade reduces site-composition differences, but
measurement practice, covariates, and target composition remain confounded.

## 9. What is the most important missing variable?

Water temperature and flow/discharge are major physical contexts for dissolved
oxygen but are absent from the frozen predictors. Date harmonics can capture
seasonal association, but cannot substitute for direct physical measurement or
support a causal claim.

## 10. What experiment should be run next?

Freeze the model, preprocessing, threshold, primary metrics, and analysis code;
obtain a licensed compatible dataset from a later period or different region;
audit row/station overlap and measurement units before model access; then report
all results once. If predictor coverage is incomplete, do not silently change
the model and call the result external confirmation.

## Questions the applicant should answer personally

### What did the first new-year evaluation actually show?

Local Git records are consistent with a freeze before the recorded evaluation
of the newly acquired 2025 NIEA release; they do not independently prove the
first-ever inference time. In 3,490 rows at 494 stations, MAE was 0.6432 mg/L but recall
was only 3/20=15%. All detections occurred at one station; nine low-DO stations
fell below the predeclared support criterion. Conditional bootstrap precision
[1,1] is misleading if its 1,844 undefined replicates are hidden. The result is
same-programme temporal evidence, not validation of V3 weighting or a forecast.

### What do missing targets and the 94 mg/L diagnostic change?

DO is missing in 2,590/6,080 source rows (42.60%), so performance is conditional
on measured targets and cannot be assumed representative of missing ones.
The flagged source record combines DO=94 mg/L with 10% saturation at 18°C;
no corrected value is verified. Its separate post-hoc omission yields MAE
0.618805 and RMSE 0.861795 mg/L, but still misses 17/20 low-DO observations.
Keep the frozen primary MAE 0.643181 and RMSE 1.687180. Do not present the
diagnostic as an optimized model or second independent test.

### Was the protocol independently preregistered?

No. Commit 2a55e5a contains the matching protocol, adapter, cohort and hashes,
but its unsigned local timestamp and later file creation cannot prove inference
start. The old execution log has no UTC start line. The
[chronology report](../audits/final_release/FREEZE_CHRONOLOGY.md) states those
limits; the [owner checklist](OWNER_CONTRIBUTION_CONFIRMATION.md) requires
separate confirmation of any personal pre-run review.

### What changed after recovery, and why is it not external validation?

The raw CSV, cleaned CSV and audit JSON match historical hashes. The fixed
Phase4 model was retrained from these data; its 31,341 predictions match the
historical table within 1e-10 mg/L. This establishes computational reproduction.
The holdout had already been inspected and is not a new population. The full V3
inner search was not rerun.

### Why did the EA pilot stop before prediction?

Exact sample IDs and units are available, but NI method definitions do not
establish equivalence for ATU BOD, temperature-standardized conductivity,
alkalinity titration and reactive phosphorus. Missing predictors alone can be
handled by a frozen imputer; incompatible chemistry cannot. The pilot also has
only six represented stations. Neither data access nor running a model proves
external reliability.

Before interview use, prepare a truthful account of which hypotheses, code,
debugging, statistical choices, visual reviews, and manuscript revisions were
personally performed or independently checked. Do not memorize first-person
claims generated by AI that cannot be defended from direct experience.
