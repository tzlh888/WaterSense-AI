# WaterSense AI — Human Review Checklist

## Required before the contribution statement is staged

- Confirm which code, tests, protocols, analyses, and reports the owner personally wrote or materially revised.
- Confirm who selected the low-DO threshold, nested-CV design, weighting hypothesis, qualification rules, and stopping criteria.
- Confirm which data-recovery, experiment-execution, plot-review, and failure-analysis tasks the owner performed.
- Identify all assistance tools used and describe their roles accurately.
- Confirm which generated code, prose, calculations, and claims the owner independently checked.
- Replace every bracketed placeholder in `RESEARCH_CONTRIBUTION_STATEMENT.md` or keep that document unpublished.

## Required before push or release

- Review the three staged groups and their cached diffs.
- Run an LFS-enabled clean-clone rehearsal and verify the existing large model is available from the remote LFS store.
- Preserve OGL v3.0 attribution and do not add ignored raw or processed source data.
- Confirm that the README still describes the weighted result as development-only and not deployment-ready.

`RESEARCH_CONTRIBUTION_STATEMENT.md` remains `HUMAN_REVIEW` and is not staged in this audit.
