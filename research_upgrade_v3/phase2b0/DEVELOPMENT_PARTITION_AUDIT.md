# Development Partition Audit

## Verdict

The historical development partition is **exactly recovered**: 119,690 rows, 672 sites, and the exact saved membership. The legacy test remains isolated at 31,341 rows/168 sites with zero station overlap.

## Identity checks

- Every processed row has one unique `source_object_id`; no processed duplicate rows or duplicate station/date records were found.
- All 151,031 processed identities join one-to-one to `split_grouped.csv.gz` using source ID, station and date.
- Each source ID has exactly one historical partition membership.
- A fresh seed-42 `GroupShuffleSplit(test_size=0.2)` exactly reproduces the saved development and legacy-test source IDs.
- All saved holdout feature and target values match the reconstructed processed rows at tolerance `1e-12`.
- All 119,690 saved training-feature-reference rows match reconstructed development features in value and order.
- No legacy-test row or site is included in development.

## Development target support

- Low-DO definition: ground truth strictly `<4 mg/L`.
- Low-DO rows: **758** (0.6333%).
- Independent sites with low-DO rows: **115**.

These are repeated observations within sites, not 758 independent events. Site remains the split and uncertainty unit.
