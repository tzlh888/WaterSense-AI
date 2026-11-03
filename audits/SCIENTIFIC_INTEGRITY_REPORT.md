# Scientific integrity report

## Audit conclusion: PARTIAL — evidence is internally strong; independence is blocked

The frozen V3 and V4 prediction artifacts pass hash, membership, station-fold,
target, denominator, and metric reconstruction checks. No new model was trained,
no historical artifact was overwritten, and no protected holdout was relabelled
as new. The main unresolved limitation is scientific rather than computational:
there is no eligible independent external confirmation set.

## Data and provenance

- The fresh clone contains public samples and all frozen prediction artifacts,
  but intentionally omits the raw and full processed CSVs.
- The repository recovery endpoint returned HTTP 500 on 2026-11-03, so exact
  raw/processed reconstruction could not be repeated. The failed download was
  not installed.
- Prior recovery records report exact raw, processed, audit, and membership
  hashes. Those claims remain `REPORTED_ONLY` in this audit because the source
  rows were not locally available.
- A public 1990–2025 DAERA “identified nutrients” annex was investigated as a
  possible later-period source. It could not be fetched in the execution
  environment, and eligibility cannot be inferred from its title. No evaluation
  was attempted.

## Leakage and validation boundaries

- Saved V3 rows are unique per variant, variant membership is identical, and
  every station belongs to one outer fold.
- Code and synthetic tests verify target exclusion and training-only fitting of
  imputation/preprocessing.
- Historical holdouts were previously inspected and remain legacy benchmarks.
- The new temporal analysis is an OOF time slice, not a forward-chaining test.
- V4 uses the same development population as V3 and a different objective; it
  is exploratory, not confirmatory.

## Statistical findings

The headline V3 trade-off was reconstructed exactly. Station concentration adds
an important qualification: 758 low-DO rows occur at 115 stations, 47 stations
have one event, and their concentration is equivalent to 29.7 equally
represented event-bearing stations. This supports station-clustered uncertainty
and prevents a false row-independence interpretation.

The balanced-station time sensitivity shows that changing site membership alone
does not explain the lower MAE in recent periods. It does not identify a cause
and cannot be interpreted as prospective robustness.

## Claim corrections and unresolved claims

- The historical `{1,4,8}` documentation omission was already corrected by the
  additive W02 erratum; frozen code and candidate counts support `{1,2,4,8}`.
- The outer V3 difference cannot be attributed solely to weighting because the
  model family and hyperparameters also change.
- Applicant-specific contribution remains unverified. Every admissions document
  marks personal language as awaiting owner confirmation.
- No deployment, regulatory, safety, forecasting, publication, peer-review, or
  admissions-outcome claim is supported.

## Integrity status by area

| Area | Status | Reason |
|---|---|---|
| Frozen artifact identity | COMPLETE | Input hashes match recorded values. |
| Row-level metric reconstruction | COMPLETE | Counts and metrics recomputed. |
| Station-fold isolation | COMPLETE | No station crosses outer folds. |
| Raw/processed reconstruction | BLOCKED | Official endpoint unavailable. |
| External validation | BLOCKED | No eligible compatible independent data evaluated. |
| Weight-only causal attribution | PARTIAL | Matched inner evidence is exploratory. |
| Applicant contribution attribution | BLOCKED | Owner attestation required. |
| Deployment readiness | NOT STARTED | Outside supported evidence and authorization. |
