# WaterSense AI — Research Upgrade V4 Candidate

## Status and evidence classes

- **HISTORICAL:** 151,031 modelling records, 840 stations, 1990–2024; station-grouped, spatiotemporal, basin, and nested-CV evidence.
- **REPRODUCED:** the current code suite passed 88/88 tests on 2026-10-14; v3 development metrics were re-read from frozen OOF predictions, not rerun or relabelled as new.
- **NEW EXPERIMENT — EXPLORATORY:** the fixed dedicated classifier was evaluated by five station-disjoint outer folds on the development population.
- **INDEPENDENT CONFIRMATION:** none.
- **BLOCKED:** current official OpenDataNI data are byte-identical to the historical raw export.

## Historical v3 result

The fixed regression baseline versus the v3 selected procedure had Overall MAE 0.8797 versus 0.9516 mg/L, Low-DO MAE 3.3235 versus 2.3613 mg/L, Recall 0.1293 versus 0.3641, Precision 0.7903 versus 0.5576, and false positives 26 versus 219. These are historical development-only outer-OOF results.

## New controlled classifier result

The Logistic Regression classifier was **pre-specified in the saved V4 development protocol; independent preregistration is not established**. On the same 119,690-row development OOF population it produced TP **699**, FP **9517**, TN **109415**, FN **59**, low-DO prevalence **0.6333%**, Recall **0.9222**, Precision **0.0684**, and F1 **0.1274** at `P(low DO) >= 0.5` for measured `DO < 4 mg/L`. Regression MAE is not applicable to a binary classifier. Fold and low-DO-station variation are retained in separate CSVs.

**DESCRIPTIVE; DIFFERENT PROTOCOL; NOT CONFIRMATORY.** V3 and V4 share sample IDs, stations, outer-fold membership and true labels, but differ in objective, decision function, model-selection protocol and research timing. They are `NOT DIRECTLY COMPARABLE AS A PERFORMANCE-IMPROVEMENT EXPERIMENT`. This is not a new model-selection victory. It is one fixed comparison after v3, on a repeatedly used development population, with no untouched confirmation set. The two-stage option was deliberately not added after viewing results.

## Scientific interpretation

V4 strengthens the evidence boundary rather than replacing the historical model. It demonstrates how a dedicated classifier changes the error trade-off and how the preferred rule depends on explicit hypothetical FN/FP cost assumptions. It also establishes that the checked official export is not independent of the preserved historical file; it does not establish that no other external source exists. No deployed model, historical result, or frozen v3 artifact was changed. See the additive [W02 erratum](../research_upgrade_v3/final_closeout/W02_ERRATUM_2026-10-14.md).
