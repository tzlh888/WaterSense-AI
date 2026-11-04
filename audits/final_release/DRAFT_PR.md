# Local GitHub Draft PR preparation — no remote PR created

**Title:** Strengthen WaterSense evidence: exact historical replay, bounded 2025 failure analysis and release audit

## Proposed description

WaterSense's average-error results conceal rare-event failure and incomplete
evidence provenance. This branch makes the limitations reviewable: it controls
station sampling volume, reports paired station uncertainty, restores the exact
historical source, audits external compatibility and documents a locally frozen
2025 same-programme evaluation.

The primary 2025 Phase4 result is MAE 0.643181 mg/L, RMSE 1.687180 mg/L,
TP/FP/TN/FN=3/0/3470/17. DO is missing in 2,590/6,080 source rows. Only nine
stations contain low DO and all three detections occur at one station. This is
neither independent-region validation nor confirmation of V3 weighting.
A separately labelled post-hoc omission of one suspicious 94 mg/L row gives
MAE 0.618805 and RMSE 0.861795; the 17 misses remain. No model, threshold or
frozen primary artifact changes.

The chronology audit verifies the Git blobs at 2a55e5a and retains local
timestamps and log hashes. It cannot independently establish inference start
or exclude earlier unrecorded inference; no third-party preregistration claim
is made. Historical V4 release assertions and protected artifacts remain
unchanged. Code, manuscript, README, evidence ledger and school drafts disclose
AI assistance and require applicant confirmation of personal contributions.

Validation: current main suite 110 passed, zero skipped; unchanged V4 suite
7 passed / 1 failed, reproduced on baseline c2ab7b4. The failure is the archived
README hash mismatch, not a new model regression. Full logs, named outcomes,
environment and integrity records are in audits/final_release.

## Reviewer checklist

- [ ] Verify source/data/model hashes and primary artifact preservation.
- [ ] Read the local chronology evidence limits; do not call this independent preregistration.
- [ ] Distinguish primary results from the post-hoc 94 mg/L diagnostic.
- [ ] Check missing-target selection, event-station support and undefined precision.
- [ ] Accept or resolve by a separately designed archival policy the pre-existing
      V4 README assertion; do not replace its frozen hash to obtain green tests.
- [ ] Check data attribution/licence scope and public derived fields.
- [ ] Review all personal-contribution placeholders and AI disclosure.
- [ ] Obtain owner approval before remote actions or application submission.

## Merge recommendation

**Ready for a Draft PR review after explicit owner authorization to create it.**
Do not merge automatically. Merge should wait for independent human review,
explicit acceptance of the documented legacy V4 failure, and the owner's
contribution/privacy review. Cross-region validation and a reliable rare-event
warning model remain unresolved research problems, not claims this PR closes.

No push, PR creation, main merge, Release, deployment or paper publication
has been executed.
