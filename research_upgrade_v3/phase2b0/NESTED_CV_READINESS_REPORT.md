# Nested Site-Grouped CV Readiness Report

## Status: READY

The exact historical development partition supports the frozen five-outer/four-inner site-grouped design. `StratifiedGroupKFold` uses the binary `<4 mg/L` label only to balance fold support; station code is the grouping unit. Outer seed is 20261012; inner seed is `20261012 + outer_fold`.

Pre-model gates were frozen before model results: validation partitions require at least 10 low rows, 3 low sites, no site contributing more than 50% of low rows, and zero overlap; training partitions require at least 50 low rows and 10 low sites.

## Outer validation support

| outer_fold | rows | sites | low_do_rows | low_do_sites | low_do_fraction | max_single_site_low_share | qualified |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 23936 | 138 | 150 | 12 | 0.00626671 | 0.38 | True |
| 2 | 23932 | 137 | 146 | 17 | 0.00610062 | 0.445205 | True |
| 3 | 23938 | 135 | 153 | 24 | 0.00639151 | 0.24183 | True |
| 4 | 23933 | 127 | 143 | 33 | 0.00597501 | 0.160839 | True |
| 5 | 23951 | 135 | 166 | 29 | 0.00693082 | 0.277108 | True |

## Inner validation range across 20 folds

| measure | rows | sites | low_do_rows | low_do_sites | low_do_fraction | max_single_site_low_share |
| --- | --- | --- | --- | --- | --- | --- |
| inner validation minimum | 23924 | 129 | 137 | 11 | 0.00572647 | 0.189781 |
| inner validation maximum | 23954 | 138 | 168 | 36 | 0.00701344 | 0.445205 |

All 50 train/validation partition rows in `NESTED_CV_FOLD_SUPPORT.csv` pass their applicable support gates; all paired site overlaps are zero. Every outer validation fold has 143–166 low rows at 12–33 sites. Every inner validation fold has 137–168 low rows at 11–36 sites. The largest single-site low-row share is below 50% in every validation fold, although several folds reach roughly 44.5%, which must remain a reported limitation.

## Reproducibility

- Site assignment canonical SHA-256: `0fa76b39cd3697aed2b615f5921a2cfa8dbaf0fdbd216393520c25c52bf58025`.
- Outer row-assignment canonical SHA-256: `d18f55c62e6baab38223c804cc3dbcdf549837560f5984dccda6139d6599b1fd`.
- Inner row-assignment canonical SHA-256: `7a143df06162994efc65b0fb58770b21a2b49a6371a66ce46a592d7218dcb0b0`.
- A second independent construction in the same run produced all three identical hashes.

`NESTED_CV_SITE_ASSIGNMENTS.csv` is the compact frozen index. Together with the exact processed-data hash it determines every row-level fold. No legacy test metric was used to design or qualify these folds.

## Statistical limits

Readiness means the design can support controlled development comparison; it does not make 758 low rows independent, eliminate site concentration, or create confirmatory evidence. Precision/F1 can still be undefined for a candidate that predicts no low values; that candidate must fail as preregistered. Final uncertainty remains whole-site clustered.
