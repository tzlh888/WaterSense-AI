# History note

## Commit hashes that do not resolve

Some files, for example section 9 of `paper/WATERSENSE_AI_MANUSCRIPT.md` and `audits/final_release/FREEZE_CHRONOLOGY.md`, cite commit hashes that do not exist in the public history of this repository.

## Relation to the author's local history

The author keeps a separate local history of this project. It also has 25 commits, with the same author dates and commit messages as the public history. For every pair of matching commits the file contents are byte-for-byte identical, except for 7 files under `reports/` that never appear in the public history. All commit hashes differ. In the local history, the 3 merge commits created by GitHub carry a signature header (the signatures were not verified); in the public history they do not.

## Commit mapping

Matched by author date and commit message. For each pair, `git ls-tree -r` shows no difference outside `reports/`.

| Old hash | New hash | Author date | Commit message |
|---|---|---|---|
| `220fd06` | `25f38339568b1c837b4fc6e242d62e9c543cef55` | 2026-10-02T09:08:28+02:00 | Initial public release of WaterSense AI |
| `09f84cf` | `c3032603fe8bb12259f5cb905dce0a256a3431f4` | 2026-10-04T23:25:59+02:00 | Finalize WaterSense AI research validation and documentation |
| `3553b29` | `b984e76faf912598e4055ddd381aa9670b927ec6` | 2026-10-05T11:54:16+02:00 | Complete WaterSense AI v2.0 robustness analysis |
| `8ed6c4c` | `4a117d36dfc0926f6f05249a128055d20ddeb1fa` | 2026-10-13T08:45:36+02:00 | Add reproducible low-DO research upgrade tooling |
| `095d00f` | `5c4d1475cbe7066531ba6b0b8b33848bf03257ce` | 2026-10-13T08:45:47+02:00 | Add frozen low-DO protocols and research evidence |
| `eb24304` | `330109f5545d51934e3f424c64de6a02649bb854` | 2026-10-13T08:46:02+02:00 | Document final scientific and release status |
| `97749f3` | `da3dbd07700e6606c80a4bd8d0379e4f9d34f1f1` | 2026-10-13T09:15:13+02:00 | Resolve legacy documentation links before main merge |
| `9672c80` | `d2602119e3d30bc062d511f6fe47f82d97af83af` | 2026-10-13T19:14:08+02:00 | Clarify research contribution and validation limits |
| `8a54cda` | `0e6409af8f264edd575533c0a4c8ec037306e4ad` | 2026-10-13T19:16:19+02:00 | Merge pull request #1 from tzlh888/research-upgrade-v3 |
| `d649c9d` | `f67dd16e5b753cdea887a472c986d5ab13daf201` | 2026-10-14T14:26:53+02:00 | Add WaterSense V4 exploratory research and reproducibility audit |
| `a7198a2` | `2a5a9b10b2494cc4edc46017445f63291d747333` | 2026-10-14T14:48:00+02:00 | Clarify applicant contribution and AI assistance boundaries |
| `12826aa` | `7599f4a47b3b3dd7bc8fb9a439dc7206470c8016` | 2026-10-14T20:11:42+02:00 | Merge pull request #2 from tzlh888/research/v4-watersense-20261014 |
| `93b13fb` | `e72d6fbc4d6cc03648288d17cd8660130170e415` | 2026-10-22T01:14:24+02:00 | docs(research): correct weighting attribution claims |
| `c2ab7b4` | `4fbdded3367b68667e4c5dbef3623d9f9d5a82f2` | 2026-10-22T01:38:29+02:00 | docs: add research evidence navigation |
| `82c19e9` | `789305bee536470f2cf312d43caa5b46987bb5cd` | 2026-11-03T09:17:22+01:00 | research: add verified reliability portfolio analysis |
| `b0ea7d7` | `8ae0f0faca716e4033424df42a8600a4df5ba3d0` | 2026-11-03T09:17:25+01:00 | docs: publish evidence-led admissions research portfolio |
| `f055a8e` | `d80f824cf2e68af9fd41fd2df86286abd7f4adaa` | 2026-11-03T09:55:46+01:00 | research: control sampling effort and quantify paired station uncertainty |
| `84fe98c` | `ca7d7c4b288f6294b87968d915b9bc69d7d79ffb` | 2026-11-03T09:55:46+01:00 | docs: align final claims with sampling controls and complete test audit |
| `18cf7d7` | `37c8c1adb69598894a85f1ced635ac32f6f663ba` | 2026-11-03T09:56:55+01:00 | audit: retain complete sprint execution logs |
| `2a55e5a` | `580def9eeb52180cb01552761332f66328b4c69f` | 2026-11-03T14:50:57+01:00 | protocol: freeze held-out 2025 temporal evaluation before prediction |
| `00e4cd3` | `ef0cd06a6342dc789c2ee62f823a9b8cd751b08b` | 2026-11-04T14:10:38+01:00 | research: recover exact history and report frozen 2025 temporal failure evidence |
| `3ad1670` | `c1663f17e97a18cbfadb4802937598caf7509416` | 2026-11-04T14:37:31+01:00 | audit: prepare final release with post-hoc sensitivity and provenance limits |
| `c6f0c39` | `74c5b06e72f5911594de08c24b9aea3ab7c20555` | 2026-11-04T15:00:33+01:00 | docs: record final admissions release gate and owner contribution signoff |
| `b0d15ee` | `3ca9fe1b719bb2b6bcec201d3ba3834afadad2fe` | 2026-11-04T15:01:37+01:00 | audit: seal admissions gate records with Unicode-safe path verification |
| `8342c0d` | `ac5f570091f4058b061d9ee4427abaa5f2964773` | 2026-11-04T15:20:38+01:00 | Merge pull request #3 from tzlh888/research/autonomous-portfolio-20261103 |

## Files that cite old hashes

Files in this repository that contain at least one old hash from the table above:

- `audits/`
  - `audits/BASELINE_INTEGRITY.json`
  - `audits/EVIDENCE_LEDGER.csv`
  - `audits/REPRODUCIBILITY_REPORT.md`
- `audits/evidence_breakthrough/`
  - `audits/evidence_breakthrough/CURRENT_BRANCH_MANIFEST.json`
  - `audits/evidence_breakthrough/FINAL_REPORT_中文.md`
  - `audits/evidence_breakthrough/INITIAL_FIXED_REPLAY_RECORD.json`
  - `audits/evidence_breakthrough/INITIAL_NI2025_GATE_RECORD.md`
  - `audits/evidence_breakthrough/VERSION_CONSISTENCY_REPORT.md`
  - `audits/evidence_breakthrough/environment.json`
  - `audits/evidence_breakthrough/historical_replay.log`
  - `audits/evidence_breakthrough/readme_archive_trace.json`
  - `audits/evidence_breakthrough/recovery_manifest.json`
  - `audits/evidence_breakthrough/version_and_tests.log`
  - `audits/evidence_breakthrough/version_consistency.json`
- `audits/final_release/`
  - `audits/final_release/ARTIFACT_MANIFEST.json`
  - `audits/final_release/DRAFT_PR.md`
  - `audits/final_release/FINAL_RELEASE_REPORT.md`
  - `audits/final_release/FREEZE_CHRONOLOGY.md`
  - `audits/final_release/PREVIOUS_CURRENT_BRANCH_MANIFEST.json`
  - `audits/final_release/audit_execution.log`
  - `audits/final_release/environment.json`
  - `audits/final_release/freeze_chronology.json`
  - `audits/final_release/freeze_commit.txt`
  - `audits/final_release/test_results.json`
- `audits/final_release/attempt_01/`
  - `audits/final_release/attempt_01/audit_execution.log`
  - `audits/final_release/attempt_01/environment.json`
  - `audits/final_release/attempt_01/test_results.json`
- `audits/final_release/attempt_02/`
  - `audits/final_release/attempt_02/audit_execution.log`
  - `audits/final_release/attempt_02/environment.json`
  - `audits/final_release/attempt_02/test_results.json`
- `audits/final_release/attempt_03/`
  - `audits/final_release/attempt_03/environment.json`
  - `audits/final_release/attempt_03/test_results.json`
- `audits/sprint/`
  - `audits/sprint/REPRODUCTION_STATUS.md`
  - `audits/sprint/environment.json`
- `paper/`
  - `paper/WATERSENSE_AI_MANUSCRIPT.md`
- `research_extension/ni2025_confirmation/`
  - `research_extension/ni2025_confirmation/FREEZE.json`
  - `research_extension/ni2025_confirmation/TEMPORAL_CONFIRMATION_REPORT.md`
- `research_outputs_v2/manifests/`
  - `research_outputs_v2/manifests/v2_manifest.json`
- `research_upgrade_v3/`
  - `research_upgrade_v3/PROTOCOL_FREEZE.md`
  - `research_upgrade_v3/RESEARCH_DECISION_LOG.md`
- `research_upgrade_v3/experiment1_weighted_regression/`
  - `research_upgrade_v3/experiment1_weighted_regression/EXPERIMENT1_CONFIG.json`
  - `research_upgrade_v3/experiment1_weighted_regression/EXPERIMENT1_REPRODUCIBILITY.md`
  - `research_upgrade_v3/experiment1_weighted_regression/EXPERIMENT1_RUN_MANIFEST.json`
- `research_upgrade_v3/experiment1a_attribution/`
  - `research_upgrade_v3/experiment1a_attribution/EXPERIMENT1A_RUN_MANIFEST.json`
- `research_upgrade_v3/final_closeout/`
  - `research_upgrade_v3/final_closeout/FINAL_PRE_MERGE_CHECKLIST.md`
  - `research_upgrade_v3/final_closeout/FINAL_RELEASE_READINESS_REPORT.md`
  - `research_upgrade_v3/final_closeout/MAIN_MERGE_DIFF_AUDIT.md`
- `research_upgrade_v3/phase2b0/`
  - `research_upgrade_v3/phase2b0/DATA_PROVENANCE_MANIFEST.json`
  - `research_upgrade_v3/phase2b0/NESTED_CV_SPLIT_MANIFEST.json`
- `research_upgrade_v4_candidate/`
  - `research_upgrade_v4_candidate/BASELINE_INTEGRITY_MANIFEST.json`
- `scripts/`
  - `scripts/audit_final_release.py`
  - `scripts/audit_version_consistency.py`
  - `scripts/finalize_evidence_audit.py`
  - `scripts/prepare_final_release.py`
  - `scripts/report_ni2025.py`
  - `scripts/run_experiment1_weighted_regression.py`
  - `scripts/run_experiment1a_attribution.py`
  - `scripts/run_phase2b0_readiness.py`
  - `scripts/verify_scientific_sprint.py`

## Author statement [self-report]

Tang Zeluohe states that the public history was created deliberately, as a cleaned history, to keep private research records out of the public repository. That cleaning was not complete: `admissions/` and `audits/admissions_release_gate/` were public until this release and remain in earlier commits. Whether the public history was ever published in another form could not be confirmed.

## This release

This release removes `admissions/`, `audits/admissions_release_gate/` and `research_upgrade_v3/final_closeout/TECHNICAL_INTERVIEW_QA.md` from the current version. They remain in earlier commits and have not been deleted from the history.

## Outdated records

`audits/final_release/ARTIFACT_MANIFEST.json`, `audits/final_release/local_links_privacy.json`, `audits/final_release/PREVIOUS_CURRENT_BRANCH_MANIFEST.json` and several CSV files under `research_upgrade_v3/final_closeout/` record the state before this release and still list the removed files. scripts/audit_final_release.py and scripts/finalize_evidence_audit.py still list the moved files; they were not updated in this release, and they depend on local files that are not published in this repository.

## Limitation

Commit times are controlled by the author. Git history alone cannot independently prove that a freeze happened before an evaluation.
