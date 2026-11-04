# Sprint reproduction evidence and unresolved checks

## Evidence level

Current evidence supports reconstruction from committed frozen development
predictions, code-level/synthetic checks, and byte preservation of historical
artifacts. Raw and full processed CSVs are missing, so source-data cleaning and
exact full-data split reconstruction cannot currently be independently verified.
Raw hashes are not invented: environment.json marks those inputs MISSING.
Frozen prediction SHA-256 values are recorded in execution_summary.json.

Run `python3 scripts/verify_scientific_sprint.py` to capture HEAD, Python and
dependency versions, analysis commands, full stdout/stderr, test outcomes and
269 protected-file byte checks. This verification command exits nonzero while
historical V4 checks remain unresolved; a nonzero status is intentionally visible.

## Main suite

Main suite: 94 individual tests executed, 92 passed and 2 skipped; additionally
one four-test class was skipped at setup. unittest reports `Ran 94 tests` and
`skipped=3` because the class setup skip is a separate result entry, not an
executed individual test. It is incorrect to infer passes by subtracting three
from 94. The earlier report's 87-of-90 pass count had this accounting error;
the old run had 88 individual passes, two skips and one class setup skip.

| Skipped entry | Reason | Validation impact |
|---|---|---|
| ApplicationLogicTests.test_date_transformation_matches_processed_phase4_data | processed CSV absent | Cannot compare the date transform against its exact historical processed row. Synthetic transform tests still run. |
| HistoricalDataIntegrationTests.test_exact_historical_identity_partition_and_fold_hashes | exact raw/processed data absent | Cannot reconstruct the original full-data identity and nested folds from source; frozen prediction membership and recorded station assignments remain checkable. |
| Phase4RefinementTests.setUpClass (four tests not executed) | processed CSV absent | Cannot run historical grouped train/test split check, feature-set check in this class, full-data transformer check, or saved-pipeline prediction check on its original rows. Other code and app-model tests do not replace these integrations. |

## Separately discovered historical V4 suite

Eight tests: six pass, one fails, one errors. These results were not covered by
the former `tests/` discovery command and are now recorded explicitly.

- `test_release_candidate_manifest` FAIL: historical V4 release manifest pins
  the pre-redesign README hash. The modern README intentionally differs. The
  frozen manifest and test are preserved, and this failure is not reclassified
  as a pass. It limits validation of that historical release package, not the
  identity of saved V4 predictions.
- `test_frozen_external_export_is_rejected` ERROR: original raw CSV is absent.
  The historical byte-identity rejection cannot be independently rerun locally.
  No new external validation is inferred from the other six tests.

The exact names and results of all main and V4 tests are recorded in
execution_summary.json and full execution logs 03/04. All 269 protected working
files match baseline c2ab7b4 bytes (the LFS model is checked by SHA-256).

## Remaining blockers

Independent external validation requires authorized compatible non-overlapping
data and the existing frozen evaluation gate. Applicant-specific contribution
requires owner authentication. Neither can be supplied by artifact arithmetic.

## Owner confirmations

1. Identify personally performed and independently checked code, analysis and
   interpretation tasks before using first-person CV/interview language.
2. Confirm authorship name and AI assistance roles.
3. Supply an exact lawful source export if available to rerun data integrations.
4. Authorize any later push, PR, merge, publication or external experiment.
