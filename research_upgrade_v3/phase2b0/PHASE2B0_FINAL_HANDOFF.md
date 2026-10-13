# Phase 2B-0 Final Handoff

## Final status: READY

The original raw CSV, processed modelling table, cleaning audit and historical split membership were recovered with exact historical SHA-256 values. The development partition is exactly 119,690 rows/672 sites, contains 758 low-DO rows at 115 sites, and excludes all 31,341 legacy-test rows/168 sites.

The frozen 5×4 nested site-grouped split passes every pre-model support gate. Outer validation has 143–166 low rows at 12–33 sites; inner validation has 137–168 low rows at 11–36 sites. All train/validation station overlaps are zero and fold hashes reproduce exactly.

The weighted-regression candidate grid, fold-local sample weights, inner qualification/ranking, outer evaluation, metrics, site-bootstrap uncertainty and stopping rules are frozen. Phase 2B-0 fitted no model and used no legacy test metric for design.

Targeted automated validation passed (Ran 19 tests in 1.639s). It includes labelled synthetic unit tests for failure paths and a separate integration test against the exact recovered historical hashes, partition and frozen fold hashes.

**Permission boundary:** the evidence permits starting Phase 2B controlled development training under the frozen protocol. It does not permit changing folds/search rules, using legacy test results for selection, or making confirmatory/generalisation claims.

Remaining limits: low DO is only 0.6333% of development rows; repeated rows within sites are dependent; some validation folds have a single site contributing about 44.5% of low rows; event independence is not available; the four historical v1 source-hash provenance gaps remain; and no new independent confirmation set exists.
