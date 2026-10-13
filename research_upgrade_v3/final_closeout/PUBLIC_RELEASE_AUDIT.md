# WaterSense AI — Public Release Audit

## Decision

**Conditionally publishable after curation.** The scientific evidence is internally coherent and tests pass, but 137 untracked files now exist after adding the six closeout documents. They must be reviewed and staged deliberately; publishing the directory wholesale is not recommended.

## README consistency

The existing README accurately describes the historical v1/v2 work, rare low-DO failure, observational scope, legacy model, and non-deployment limitations. It does not yet expose the later exact data recovery, nested-CV weighted experiment, attribution boundary, or final closeout documents. This omission can make the repository homepage look scientifically older than the retained evidence.

Minimal recommended edits only:

1. Add a short “Research upgrade” notice after the opening snapshot.
2. State the development nested-CV trade-off exactly: low-DO MAE `3.3235→2.3613`, recall `0.1293→0.3641`, overall MAE `0.8797→0.9516`, precision `0.7903→0.5576`, and false positives `26→219`.
3. Label it development-only and link this final report, the experiment handoff, and attribution report.
4. State that no new external confirmation set exists and the deployed historical model was not replaced.
5. Add the closeout summary to the Research Reports table.

Do not replace the historical README narrative or silently update its old model metrics.

## Claims review

The public release may say:

- the exact historical data and development partition were recovered by hash;
- the frozen weighted procedure met its development nested-CV decision rule;
- low-DO improvement and overall/precision costs were observed across held-out development stations;
- matched inner evidence supports a weighting contribution exploratorily.

It must not say:

- the new procedure is externally validated, operationally reliable, or deployment-ready;
- weighting alone was confirmed by the formal outer comparison;
- repeated split appearances are independent samples;
- bootstrap intervals guarantee future-site or regional performance;
- the project predicts future DO without contemporaneous chemistry inputs.

## Data, models, and licensing

- Source data are public-sector information under OGL v3.0. Preserve attribution and the source/version information.
- Keep the 31.7 MB raw CSV and 23.7 MB processed modelling table outside ordinary Git, as currently configured; provide the recovery command and hashes instead.
- Keep exploratory checkpoints and partial-run files out of Git.
- The 175.6 MB historical deployed model is already designated for Git LFS and documented by SHA-256. Confirm LFS availability before publishing a commit that references it.
- Do not publish local environment files, secrets, logs, caches, or arbitrary joblib files. Joblib’s code-execution risk should remain documented.

## Privacy and path audit

A targeted scan of public text/code found no private absolute user path, AI development-workspace path, credential, bearer token, API key, or cookie value in the WaterSense upgrade scope. The only absolute-path pattern encountered was inside a test that rejects such paths. New closeout documents use repository-relative paths only.

## Repository hygiene

Recommended exclusions from staging:

- `__pycache__/`, `*.pyc`, test caches, logs, local environments;
- `research_upgrade_v3/experiment1_weighted_regression/.checkpoints/` after confirming the final consolidated predictions and manifest are sufficient; retain locally or archive externally if exact interruption recovery is important;
- ignored raw/processed data and non-release model artifacts.

The 6.2 MB compressed outer predictions are scientifically valuable and reasonably sized for ordinary Git, but should be staged with their manifest. The 0.53 MB bootstrap replicate file is optional for public audit; its summary and generator may be sufficient, although retaining it improves exact traceability.

## Suggested commit plan — do not execute automatically

1. **Protocol and data recovery:** Phase 2A/2B-0 reports, manifests, scripts, core modules, and tests.
2. **Experiment 1 evidence:** frozen config, selection tables, consolidated predictions, metrics, uncertainty, reports, source, and tests; exclude restart checkpoints.
3. **Attribution audit:** matched-pair summaries/data, reports, source, and tests.
4. **Publication closeout:** six final documents plus the minimal README links.

Before each commit, inspect `git diff --cached --stat`, `git diff --cached`, staged file sizes, `git check-ignore`, and a secret/path scan. Record the final artifact hashes after staging decisions are fixed.

## Mandatory pre-publication actions

- Have the project owner approve the personal contribution statement and AI-assistance disclosure.
- Decide whether checkpoint directories and full bootstrap replicates belong in Git or in an external archive.
- Make the minimal README link/claim update.
- Verify OGL attribution in the eventual staged report set.
- Preserve the successful clean Python 3.12.14 `requirements.txt` + 88/88 `unittest` result in the final release record.
- Confirm that Git LFS objects are available to a fresh clone.

No README, historical result, model, protocol, commit, push, or release was changed during this closeout.
