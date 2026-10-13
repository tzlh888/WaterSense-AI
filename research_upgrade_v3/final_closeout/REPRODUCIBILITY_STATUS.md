# WaterSense AI — Reproducibility Status

## Status

**Publicly reviewable and locally reproducible with documented external data recovery; external scientific confirmation remains absent.**

## What can be reproduced from saved artifacts

- Exact low-DO and overall metrics can be recomputed from saved outer predictions.
- Inner selections, outer fold metrics, site analyses, attribution pairs, and clustered bootstrap summaries are retained.
- Observation identity, development membership, station isolation, and fold hashes can be verified.
- The exact public raw export can be re-fetched by the recovery script and must match the frozen SHA-256 before use.
- Historical and upgraded result directories are separate.

Closeout independently recomputed the two 119,690-row procedure outputs from `OUTER_CV_PREDICTIONS.csv.gz`. Results matched the frozen tables: baseline/weighted overall MAE `0.8797269594/0.9515970765`, low-DO MAE `3.3235268405/2.3613472246`, recall `0.1292875989/0.3641160950`, precision `0.7903225806/0.5575757576`, with false positives `26/219`.

## What is only partially reproducible

- A fresh clone does not contain the ignored raw and processed CSV files. Reproduction depends on the external OpenDataNI service remaining available or on a lawful local copy.
- The large deployed historical joblib artifact is managed by Git LFS. Loading a joblib file executes Python objects; users should verify its documented SHA-256 and trust its origin.
- Exact package versions and platform details are recorded for historical runs, but floating-point and parallel estimators may still show platform-level differences.
- No new external confirmation dataset exists, so the scientific claim cannot be independently replicated on an unseen population from this repository alone.

## Verification performed at final closeout

- Saved prediction SHA-256 matched the experiment manifest.
- 119,690 unique source IDs and 672 stations were present for both variants.
- Baseline and weighted membership were identical; each station occurred in one outer fold.
- `python3 -m unittest discover -s tests -v`: **88/88 passed**, including a repeat in a newly created Python 3.12.14 virtual environment with the declared `requirements.txt` installed.
- Targeted upgrade tests: **34/34 passed**.
- The repository’s documented standard test entry is `unittest`; `pytest` is not a declared WaterSense dependency and was not required.
- No new research model or hyperparameter search was run. Some existing unit tests fit tiny synthetic models as test fixtures only and created no research artifact.

## Reproduction commands

Run in a clean environment from the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
git lfs pull
python scripts/recover_phase2b0_data.py
python -m unittest discover -s tests -v
```

To inspect, rather than rerun, the frozen upgrade evidence, verify hashes in:

- `research_upgrade_v3/phase2b0/DATA_PROVENANCE_MANIFEST.json`
- `research_upgrade_v3/phase2b0/NESTED_CV_SPLIT_MANIFEST.json`
- `research_upgrade_v3/experiment1_weighted_regression/EXPERIMENT1_RUN_MANIFEST.json`
- `research_upgrade_v3/experiment1a_attribution/EXPERIMENT1A_RUN_MANIFEST.json`

The experiment runner can be computationally expensive and must write to a new directory. Never overwrite the frozen evidence directory.

## Evidence-strength boundary

Reproducibility of code, hashes, and development predictions does not create new statistical independence. The conclusion remains limited to the recovered development population and frozen procedure.
