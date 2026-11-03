# Reproducibility report

## Current status

**Artifact-level reproduction: COMPLETE. Full raw-data reconstruction: BLOCKED.**

The portfolio extension requires only committed, checksum-verified OOF
predictions and runs without model fitting:

```bash
python3 scripts/run_portfolio_analysis.py
python3 -m unittest tests.test_portfolio_analysis -v
```

The run verifies the two frozen input hashes, exact V3/V4 row membership, target
agreement, strict low-DO labels, unique identities, and station-fold separation.
It then regenerates all extension tables, figures, report text, and a hash
manifest.

## Test evidence on 2026-11-03

- New portfolio tests: **6/6 passed**.
- Full discovered suite: **90 tests run, 87 passed, 3 skipped, 0 failed**.
- The three skips require exact ignored
  `data/processed/water_quality_modeling.csv` research data. Data-dependent
  tests now distinguish unavailable fixtures from code failures, consistently
  with the existing historical-data integration gate.
- Recovery was attempted. Python HTTPS failed certificate verification and the
  system client reached the frozen URL but received HTTP 500. No nonmatching
  source file was installed.

## Reproduction levels

| Level | Status | Requirement |
|---|---|---|
| Recompute portfolio metrics/figures | COMPLETE | Fresh clone and declared Python dependencies. |
| Verify frozen V3/V4 identity | COMPLETE | Committed compressed prediction files. |
| Load historical deployed model | COMPLETE | Git LFS object is present and hash-verified; loading joblib requires trusting the repository. |
| Rebuild exact processed data | BLOCKED | Frozen public raw export or exact lawful copy. |
| Rerun historical model searches | PARTIAL | Code/config exist; exact raw data and substantial compute required. Not needed for artifact verification. |
| Independent scientific replication | BLOCKED | New compatible non-overlapping population. |

## Preservation check

Baseline commit `c2ab7b4` had tree
`b8e7fd922c68ed737f254f135cbf99cdd08864ac`. Historical V1–V4 files remain
unchanged; verification is performed by comparing the feature branch against
that tree and by rechecking protected hashes.
