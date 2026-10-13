# WaterSense AI — Proposed Commit Plan

No commit has been created. The staging index contains one reviewed superset that should be committed in three groups after owner approval.

## Group 1 — Implementation, scripts and tests

Expected paths: **13**. This group contains the new reliability, recovery, readiness, experiment, and attribution implementation plus their entry points and tests.

Before committing, reset only the index without changing working-tree files, then stage the rows marked `1_implementation_tests` in `STAGED_FILE_MANIFEST.csv`.

Suggested message: `Add reproducible low-DO research upgrade tooling`

## Group 2 — Research protocols, results and reports

Expected paths: **63**. This group contains frozen protocols, manifests, compact predictions, metrics, uncertainty outputs, figures, and experiment handoffs. Restart checkpoints remain excluded.

Suggested message: `Add frozen low-DO protocols and research evidence`

## Group 3 — README, reproducibility and release documentation

Expected paths: **18**. This group contains the minimal README, ignore and attributes changes, final closeout documents, and staging/security audits.

Suggested message: `Document final scientific and release status`

## Safety checks for every group

Inspect `git diff --cached --stat`, `git diff --cached`, and `git diff --cached --check`. Confirm the staged paths equal the selected group rows exactly. Do not stage the contribution statement, restart checkpoints, raw data, processed source data, local environments, credentials, caches, or partial runs.
