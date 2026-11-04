# Current branch versus historical baseline

Current feature branch: `research/autonomous-portfolio-20261103`.
Baseline: `c2ab7b4ce7c9499d2b1a75e76ff910095a0f0b31`, in a detached local
worktree. Both receive copies of the same exact ignored raw/processed fixtures.
The V4 test source is byte-identical in the two checkouts.

| Suite | Baseline | Current | Interpretation |
|---|---|---|---|
| Main tests | 88 passed, no skips | 108 passed, no skips | Data-dependent integrations now execute. Current suite also includes 20 portfolio/sprint/evidence tests added since baseline. |
| Historical V4 | 7 passed, 1 failure, no errors/skips | 7 passed, 1 failure, no errors/skips | Same stale README archive expectation in both versions. |

## README mismatch

The frozen V4 release manifest expects README SHA-256
`289f0605c4b5b5bf79ffc1cb200d593f7e0267a951d83518d5d002d9df297db8`.
The commit trace shows that this matches the V4-introduction README at
`d649c9d`; the pre-V4 README at `9672c80` differs, as does the later baseline
`c2ab7b4`. Consequently it is a historical archive/version mismatch after the
V4 snapshot, not a new regression introduced by the current portfolio work.

The assertion is not removed, replaced, or weakened. The historical suite still
fails and logs explicitly retain that failure. The new
`CURRENT_BRANCH_MANIFEST.json` checks current README/paper/adapter-audit files
under their own version boundary; its passing test does not turn the historical
failure into a pass.

## Missing-raw integration

`test_frozen_external_export_is_rejected` now passes in both checkouts after
exact source recovery. Its previous error was a missing local fixture, not an
estimator regression. The previous two skipped individual tests and skipped
four-test Phase4 class now execute successfully. This extends evidence from
saved predictions/synthetic code to exact source-data and split integration.

## Preservation and reproducibility limits

`version_consistency.json` enumerates all release-manifest differences, records
the two HEADs and commands, and verifies 269 protected historical files against
baseline bytes (Git LFS model checked by its frozen SHA-256). No protected
V1–V4 output, assertion or model has changed.

Exact cleaning and the fixed Phase4 selected-estimator replay are complete.
The original model/feature searches, V1/V2 full experiment suite and V3 2,560-fit
grid have not been rerun. The V3 runner's branch/HEAD guards remain intact;
no gate is monkey-patched or bypassed.

## PR recommendation

A draft PR for review is reasonable once the owner authorizes a push. Recommend
reviewing and accepting the scope as recovery, compatibility and acquired
2025 temporal evaluation. Do not represent it as cross-region validation or
independent confirmation of V3 weighting.
Main merge should follow owner review of personal attribution and acceptance of
the explicitly retained historical archive-test failure. No automatic push,
PR creation, merge, deployment or publication occurred.
