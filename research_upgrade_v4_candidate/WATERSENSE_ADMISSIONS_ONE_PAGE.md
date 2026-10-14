# WaterSense AI — Admissions Research Brief

**Research Question.** Can machine-learning estimates of dissolved oxygen remain reliable when evaluated at monitoring stations, years, and river basins not represented during training—and what happens specifically in rare low-oxygen conditions?

**Why It Matters.** A low average prediction error can conceal failure in environmentally important edge cases. WaterSense therefore treats generalization design and failure analysis as central research outputs, rather than presenting a single favorable score as proof of reliability.

**Methodology.** The project studies 151,031 modelling observations from 840 Northern Ireland monitoring stations collected between 1990 and 2024. Historical work used station-grouped cross-validation, future-year and spatiotemporal holdouts, a basin holdout, and repeated splits. Research Upgrade v3 added a frozen 5×4 nested station-grouped design on a 119,690-row development partition. Its formal weighting grid was `{1,2,4,8}`; the additive [W02 erratum](../research_upgrade_v3/final_closeout/W02_ERRATUM_2026-10-14.md) documents a historical report that accidentally omitted weight 2. V4 then evaluated one class-balanced Logistic Regression classifier pre-specified in the saved V4 development protocol; independent preregistration is not established. It used the same five outer folds and no test-driven threshold tuning. False-negative and false-positive burdens were also compared under explicitly hypothetical cost assumptions, not real regulatory losses.

**Strongest Verified Evidence.** The historical fixed regression baseline and v3 selected procedure had low-DO recall of 0.1293 and 0.3641 respectively, while low-DO MAE decreased from 3.3235 to 2.3613 mg/L. The V4 classifier produced TP 699, FP 9,517, TN 109,415 and FN 59: recall 0.9222, precision 0.0684 and F1 0.1274 at 0.6333% low-DO prevalence. This result is retained because it quantifies the severe false-alarm cost. It is **descriptive, based on a different protocol, and not confirmatory**; V3 and V4 are not directly comparable as a performance-improvement experiment. The checked official OpenDataNI export was byte-identical to the preserved historical file, showing that this source is not a new confirmation dataset but not ruling out all other sources.

**Most Important Failure.** Improving rare-event recall can create an operationally unacceptable alert burden. Even the v3 procedure increased false positives from 26 to 219; the simple classifier made that trade-off much more severe.

**Scientific Limitation.** Every V3/V4 comparison remains internal development evidence. No genuinely independent region or post-2024 period with compatible predictors was available, so external validation is not claimed.

**AI Assistance Disclosure.** The applicant states that they were the sole human project lead and used substantial AI assistance for implementation, testing, analysis, and documentation. That statement is owner-supplied, not third-party certification. The applicant should personally confirm and be prepared to explain each decision and result.

**Current Research Status.** V4 Candidate: reproducible development analysis, external validation **NOT AVAILABLE**, deployed model unchanged, and conclusions deliberately limited.
