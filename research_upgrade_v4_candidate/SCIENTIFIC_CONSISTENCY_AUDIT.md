# WaterSense scientific consistency audit

## Audit result: PARTIAL

Core data identity, split isolation, v3 metrics, and current tests are consistent. One genuine documentation error was found in the frozen v3 final report: it lists multipliers 1, 4, and 8, while the saved frozen configuration, decision log, executed candidate count, and result files establish the formal grid as **1, 2, 4, and 8**. The historical report is preserved; the additive `W02_ERRATUM_2026-10-14.md` supplies the correction without rewriting the evidence trail.

| File | Original statement | Code/data evidence | Classification | Action | Status |
| --- | --- | --- | --- | --- | --- |
| `research_upgrade_v3/final_closeout/FINAL_SCIENTIFIC_REPORT.md` | Candidate multipliers were 1, 4, or 8. | Both frozen JSON configurations list `[1,2,4,8]`; `RESEARCH_DECISION_LOG.md` says `{1,2,4,8}`; 128 candidates equal 32 non-weight settings × 4 weights. | Documentation omission in historical closeout, not a different experimental stage. | Preserve historical file; publish V4 clarification. | FIXED BY ADDITIVE ERRATUM |
| `research_upgrade_v3/phase2b0/WEIGHTED_REGRESSION_CONFIG.json` vs executed config | Status says not executed. | The file is the pre-execution protocol; `experiment1_weighted_regression/EXPERIMENT1_CONFIG.json` and outputs record later execution. | Stage distinction, not contradiction. | Retain both with dates/status labels. | CONSISTENT |
| README v3 metrics vs OOF predictions | 0.8797/0.9516 MAE, 3.3235/2.3613 Low-DO MAE, 0.1293/0.3641 recall, 26/219 FP. | Recomputed by V4 from 119,690 frozen OOF rows. | Claim/data check. | No correction. | VERIFIED |
| “IMPROVEMENT SUPPORTED” vs worse overall MAE/precision | Formal conclusion may sound global. | Frozen rule is co-primary and permits ≤10% Overall-MAE degradation plus precision ≥0.30; observed MAE rose 8.17%, precision fell to 0.5576. | Bounded protocol conclusion, not universal improvement. | V4 reports every cost and metric. | CONSISTENT WITH QUALIFICATION |
| Development evidence vs external confirmation | No external confirmation claimed. | Current official CSV is byte-identical to historical raw data. | Evidence-scope check. | External status remains NOT AVAILABLE. | VERIFIED |
| Station-grouped leakage | No station overlap. | Frozen assignments cover 672 stations once in the outer validation mapping; integration tests passed. | Leakage check. | No correction. | VERIFIED |
| Target leakage | Target/qualifier excluded from predictors. | Feature schema and 88 passing tests enforce exclusion and fold-local preprocessing. | Leakage check. | No correction. | VERIFIED |
| Historical model integrity | V4 must not replace deployed model. | Git and file manifest show the historical model hash unchanged; V4 writes only to its candidate directory. | Preservation check. | No model modification. | VERIFIED |
| AI disclosure | Substantial AI assistance is disclosed. | README and closeout language are aligned. | Disclosure check. | Owner review still required before public use. | CONSISTENT |

## Configuration-count proof for W02

Random Forest has 8 non-weight settings, Extra Trees has 8, and HistGradientBoosting has 16. Crossing all 32 settings with four multipliers gives `32 × 4 = 128` candidates per inner fold, matching the executed evidence. A three-weight grid would give only 96. Therefore `{1,2,4,8}` is the formal frozen experiment; `{1,4,8}` in the final report is not a separate executed phase.

No historical file was overwritten. V4 code and tests are new, isolated artifacts.
