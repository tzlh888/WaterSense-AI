# WaterSense V4 final scientific audit

**Final audit status: PARTIAL.** V4 code and development evidence pass their checks; independent external confirmation is blocked.

1. **What is new?** One fixed outer-OOF Logistic Regression low-DO classifier, cost-sensitivity analysis, current official-export identity check, W02 consistency correction, machine-readable manifests, and review materials.
2. **What is historical?** All v1/v2 results and v3 baseline/selected-procedure metrics. V4 recomputed v3 metrics from saved predictions but does not call them new runs.
3. **True external confirmation?** No. The current official CSV is byte-identical to the historical raw source.
4. **Post-hoc selection?** No V4 candidate selection occurred. One classifier and threshold were frozen before fitting. Results were not used to add a two-stage model.
5. **Leakage?** No detected row or station leakage in the frozen outer folds; preprocessing was fitted within each training fold. This does not remove broader development reuse.
6. **Undisclosed failures?** No. The classifier’s 9,517 false positives and 0.0684 precision, the blocked external evaluation, and the W02 documentation error are explicit.
7. **Claims beyond evidence?** None found in V4 after correction. The classifier remains exploratory/development-only.
8. **Historical model changed?** No.
9. **Old results preserved?** Yes; V4 is additive.
10. **Code/report inconsistency?** The W02 multiplier omission exists in a historical report; V4 records the formal `{1,2,4,8}` grid and does not rewrite history.
11. **Untrustworthy personal contribution claim?** The sole-human-lead statement is identified as owner-supplied and still requires owner confirmation.
12. **Admissions/report alignment?** Yes. Both state no external confirmation and disclose the classifier’s precision/false-positive failure.

## Evidence-backed statuses

- Audit: **PARTIAL** — historical W02 documentation omission corrected additively.
- New Research: **EXPLORATORY** — `WATERSENSE_EXPERIMENT_COMPARISON.csv`.
- External Validation: **NOT AVAILABLE** — `WATERSENSE_EXTERNAL_VALIDATION.md`.
- Reproducibility: **PASS** for executable V4 and tests; scientific confirmation remains unavailable.
