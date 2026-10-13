# WaterSense AI — Final Release Readiness Report

Date: 2026-10-12

Branch: `research-upgrade-v3`

Frozen starting HEAD: `3553b29`
Release decision: **CONDITIONALLY READY**

## 1. Scope and safety boundary

This release-preparation pass did not train or tune a research model, alter a historical metric, stage files, create a commit, push, or publish a release. Existing results remain untracked until the repository owner approves the explicit allowlist in `RELEASE_FILE_CLASSIFICATION.csv`.

At entry, Git reported 137 untracked files and no tracked modification. The release-preparation backup contains those 137 files together with the pre-edit `README.md` and `.gitignore`:

- Archive: `outputs/release_prep_snapshots/watersense_release_prep_start_139_files.tar.gz`
- SHA-256: `13ba66cbeeaa1aee55f419c3385be332fb6cca65c918e61bd79a09976b6f0bf4`

The earlier Phase 4 archive also remains available:

- Archive: `outputs/phase4_snapshots/watersense_phase4_start_untracked_131.tar.gz`
- SHA-256: `d99c123e3f4964650895a97d1c9d58292b8f0e51bb6994e4230c270abe4908a6`

The 55 restart-checkpoint files under `research_upgrade_v3/experiment1_weighted_regression/.checkpoints/` are preserved locally and in the backup. They are now ignored because they duplicate consolidated, publishable experiment outputs; nothing was deleted.

## 2. File disposition

The authoritative path-level allowlist is `RELEASE_FILE_CLASSIFICATION.csv`.

| Action | Count | Release treatment |
|---|---:|---|
| `COMMIT` | 94 | Suitable for reviewed Git commits including eight final staging-audit deliverables and the scoped attributes update |
| `HUMAN_REVIEW` | 1 | Do not stage until the owner confirms the contribution statement |
| `KEEP_IGNORED` | 55 | Retain locally and in backup; do not publish |
| `CANNOT_PUBLIC` | 0 | No prohibited item was found among the 137-file baseline |

Repository-wide exclusion rules must continue to cover credentials, private raw data, local environments, caches, temporary files, and redundant checkpoints. Raw or processed source datasets must not be added merely because a report references them; publication requires a separate license and privacy determination.

## 3. Scientific consistency

The final README and closeout documents consistently identify the reported comparison as development-only nested, site-grouped cross-validation:

| Metric | Baseline | Weighted procedure | Interpretation |
|---|---:|---:|---|
| Low-DO MAE | 3.3235 mg/L | 2.3613 mg/L | Improved within development CV |
| Low-DO recall | 0.1293 | 0.3641 | Improved, but substantial misses remain |
| Overall MAE | 0.8797 mg/L | 0.9516 mg/L | Degraded |
| Low-DO precision | 0.7903 | 0.5576 | Degraded |
| False positives | 26 | 219 | Increased materially |

The values were recomputed from the saved outer-fold prediction artifacts: both procedures contain 119,690 rows and 672 sites. The report language does not describe these results as external confirmation, deployed reliability, or proof of causal attribution to weighting. The same-architecture weight-1 versus weight-8 attribution study remains explicitly exploratory.

## 4. Security, privacy, licensing, and size audit

- No Earthdata token, bearer header, GitHub token, AWS credential, private-key block, private user-home path, or AI development-workspace trace was found in the proposed text/code files.
- No symlink was found in the proposed release set.
- The largest new proposed file is approximately 6.2 MB; no new file approaches GitHub's 100 MB object limit.
- The existing approximately 175.6 MB model is already tracked through Git LFS; local `git lfs fsck` passed. Remote LFS availability must still be verified during the owner's push rehearsal.
- Public reports identify data provenance and limitations, but they do not grant redistribution rights for third-party or private source data. Such data remain excluded.
- `RESEARCH_CONTRIBUTION_STATEMENT.md` does not infer authorship from repository ownership and is blocked on owner confirmation.

## 5. Clean-environment verification

A fresh virtual environment was created with the bundled Python 3.12.14 runtime. `requirements.txt` installed successfully. The complete discoverable suite was then run with:

```bash
python -m unittest discover -s tests -v
```

Result: **88 passed, 0 failed, 0 skipped** in approximately 6.5 seconds.

Some tests fit tiny synthetic fixtures to exercise code paths; this is automated software testing, not a new research-model experiment. No historical prediction artifact was overwritten.

Static and artifact checks also passed:

- Python source compilation;
- CSV readability and consistent row structure;
- JSON parsing;
- gzip integrity;
- Markdown local-link resolution;
- recomputation of the frozen outer-prediction metrics;
- scan for secrets, private absolute paths, and development-tool directories.

## 6. Public reproducibility

A third party can install the declared environment, run the 88-test suite, inspect frozen protocols, and recompute the headline development-CV comparison from committed outer predictions. The release does not provide a new external confirmation set and therefore cannot reproduce an external validation that never occurred. Data-source availability and license restrictions may also prevent exact reconstruction of every historical preprocessing step.

## 7. Proposed staged commit sequence

Do not use `git add .`. Review `RELEASE_FILE_CLASSIFICATION.csv`, then stage only explicit paths in this order:

1. **Research implementation and tests** — the four new `src/` modules, four root `scripts/`, and four matching `tests/` files.
2. **Frozen protocols and Phase 2A/2B evidence** — publishable files under `research_upgrade_v3/phase2b0/`, `experiment1_weighted_regression/`, `experiment1a_attribution/`, and the non-checkpoint root-level v3 reports and figures.
3. **Final closeout and release governance** — final scientific report, one-page summary, reproducibility/public-release audits, interview Q&A, classification CSV, this report, README, and `.gitignore`.
4. **Contribution statement only after human approval** — stage `RESEARCH_CONTRIBUTION_STATEMENT.md` separately after the owner confirms authorship, tooling, and individual technical work.

Before each commit, run `git diff --cached --check`, inspect `git diff --cached --stat`, and confirm that no `.checkpoints/`, raw source data, environment, credential, or cache path is staged.

## 8. Remaining release gates

The repository is **CONDITIONALLY READY**, not fully READY, because:

1. the owner must confirm the contribution statement;
2. the exact staging allowlist must receive human review;
3. remote Git LFS object availability has not yet been exercised by a clean clone/push rehearsal;
4. the final public release must preserve the explicit development-only and no-deployment limitations.

None of these gates authorizes new model training. Once they are cleared, the reviewed files can be committed and pushed in the sequence above.
