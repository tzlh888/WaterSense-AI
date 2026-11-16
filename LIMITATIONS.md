# Limitations and disclosure

This page collects what WaterSense AI does not show, the failures kept on purpose, and how AI tools were used. The short project page is the [README](README.md).

## What this project does not establish

- No independent external region confirms the result; the 2025 same-programme temporal test does not validate V3's selected weighted procedure.
- Most low-DO observations are still missed by the V3 selected procedure.
- Northern Ireland observations do not establish transfer to other regions.
- Temperature, flow/discharge, and catchment context are absent.
- Repeated rows within station and reused splits are dependent.
- Descriptive time-band results are not future forecasting evidence.
- Feature importance is predictive association, not causation.
- No defensible operational false-negative/false-positive cost has been set.
- The model is not validated for warnings, regulation, safety, or deployment.
- Applicant-specific personal contribution requires owner confirmation.
- The 2025 target-missing selection and sparse event-station support limit population claims; post-hoc source-value diagnostics do not replace main results.

## The 2025 test

An England EA compatibility pilot retrieved 430 observations / 49 exact samples / 6 stations. Mapping gaps in measurement definitions and insufficient pilot support keep EA scoring blocked. A separate compatible 2025 NIEA release was subsequently evaluated under a local freeze. The chronology is consistent with freezing before the recorded run; no independent preregistration or exact execution-start timestamp exists. ([Recovery and compatibility evidence](audits/evidence_breakthrough/EXTERNAL_COMPATIBILITY_REPORT.md))

**The new evidence is a failure result.** On 2025 data the frozen Phase4 model has overall MAE 0.6432 mg/L [95% station-bootstrap interval 0.5896–0.7176], but misses 17 of 20 measured low-DO observations. Recall is 0.15 [0.00–0.3462]; low-DO MAE is 2.2888 mg/L. Precision 1.00 comes from just three positive predictions at one station; 1,844/5,000 bootstrap draws have undefined precision. Only nine low-DO stations fail the predeclared support criterion. This is same-programme later-period evidence, not cross-region validation or confirmation of V3 weighting.

DO is absent in 2,590/6,080 source rows (42.60%); evaluation describes the measured-target subset. A separately labelled post-hoc omission of one suspicious 94 mg/L source value changes MAE to 0.618805 and RMSE to 0.861795 mg/L, while 17/20 low-DO misses remain. Primary MAE 0.643181 and RMSE 1.687180 remain unchanged. No correction to the source value is verified.

More: [Sensitivity and source check](research_extension/final_release/POST_HOC_SENSITIVITY.md) · [Local freeze chronology and limits](audits/final_release/FREEZE_CHRONOLOGY.md) · [2025 protocol, counts, uncertainty and failure analysis](research_extension/ni2025_confirmation/TEMPORAL_CONFIRMATION_REPORT.md)

## Results kept because they make the study more honest

1. The V3 selected procedure improves low-DO MAE and recall but worsens overall MAE, precision, and false alarms.
2. The fixed V4 classifier reaches high recall only with 9,517 false positives and 0.0684 precision.
3. Historical prediction intervals have near-nominal aggregate coverage but very poor low-DO coverage.
4. Rare events are concentrated, so row counts overstate the diversity of geographic support.
5. The official data checked in V4 were not independent of historical data, so external evaluation was correctly stopped.
6. A historical report omitted weight 2 from the written candidate list; an additive erratum corrects the documentation without rewriting the record.

## Limitations that must remain visible

- There is no independent external confirmation.
- Data come from one regional monitoring programme.
- Temperature, flow, and catchment context are missing.
- Repeated observations and reused splits are statistically dependent.
- V3 does not isolate the full outer effect of weighting alone.
- V4 uses a different objective and reused development data.
- Time-slice analysis is descriptive, not a forecast evaluation.
- No application owner has supplied a defensible false-negative/false-positive cost ratio.
- The system is not validated for warnings, regulation, or deployment.
- The applicant's exact independent contribution requires human confirmation.

## Use of AI tools

WaterSense AI is an educational research project. AI systems provided substantial assistance with implementation, testing, analysis, writing, visualization, and auditing. The repository does not present AI-generated work as unaided human work, and personal contribution language remains subject to owner verification.

The [research contribution statement](research_upgrade_v3/final_closeout/RESEARCH_CONTRIBUTION_STATEMENT.md) records what is confirmed at project level and what is not.

## Removed files and older records

Some earlier files were removed from the current tree: school-specific application drafts, contribution checklists, interview rehearsal templates, and the `audits/admissions_release_gate/` directory (internal release-check logs and review reports). They remain in this repository's git history, in commits up to and including `ac5f570`, the last commit on `main` before this cleanup. Several older audit records (for example `audits/EVIDENCE_LEDGER.csv`, the `ARTIFACT_MANIFEST.json` files and two scripts under `scripts/`) still refer to those paths or record their hashes. Those records are left unchanged on purpose, so they stay accurate for the commits they describe.

## Data

Public environmental data keep their source terms: [data attribution and reuse boundaries](docs/DATA_REUSE_AND_RELEASE.md).
