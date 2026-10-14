# WaterSense AI — Research Contribution Statement

## Attribution rule

Repository ownership, file presence, and GitHub account ownership do not prove that one person independently wrote every line or made every research decision. This statement separates artifact-verifiable project contents from biographical claims that require the project owner’s confirmation.

## Verifiable from repository evidence

The repository contains and can substantiate the following project-level contributions:

- an exact, hash-verified recovery of the OpenDataNI/NIEA raw export and processed modelling table;
- deterministic cleaning, unique observation identity, station membership, and historical partition recovery;
- a frozen five-outer/four-inner site-grouped cross-validation design with fold manifests and support audits;
- low-DO metrics with an explicit `< 4 mg/L` definition, zero-positive handling, station-level analysis, and clustered bootstrap uncertainty;
- a frozen 128-candidate weighted-regression experiment with saved inner results and complete outer out-of-fold predictions;
- an honest benefit–cost analysis covering low-DO gains, overall-error degradation, precision loss, and false positives;
- a post hoc matched attribution audit that does not overstate exploratory evidence as independent confirmation;
- automated tests for thresholding, false negatives, unique identity, fold isolation, deterministic hashes, invalid folds, saved prediction pairing, and bootstrap behavior;
- preservation of historical results, failed experiments, decision rules, and legacy-benchmark status.

These facts show what the project contains. They do not by themselves establish which individual designed, implemented, reviewed, or interpreted each item.

## Statements requiring the project owner’s confirmation

Before using a first-person contribution statement, the owner should explicitly verify:

1. Which source, test, analysis, and report files they personally wrote or materially revised.
2. Whether they independently proposed the low-DO question, the 4 mg/L threshold, weighting hypothesis, nested-CV design, qualification constraints, and stopping rule.
3. Which data recovery, cleaning, debugging, experiment execution, and result-review steps they personally performed.
4. Whether they inspected raw records and plots and independently checked the reported failure cases.
5. Whether another person supplied code, data, experimental decisions, or scientific interpretation.
6. The exact role of AI-assisted tools: prompting, code generation, refactoring, test creation, analysis, report drafting, and error checking.
7. Which AI-generated or externally supplied outputs they personally validated before retaining.
8. Whether the public Git history omits substantial earlier work and, if so, what other contemporaneous evidence supports their account.

## Public data and third-party software

- Data: OpenDataNI / Northern Ireland Environment Agency, “River Water Quality Monitoring 1990 to 2024 — All Parameters,” UK Open Government Licence v3.0.
- Core frameworks: Python, pandas, NumPy, SciPy, scikit-learn, joblib, Matplotlib, and Streamlit, according to repository requirements and source imports.
- Models: scikit-learn Random Forest, Extra Trees, HistGradientBoosting, Ridge, and dummy baselines; these are third-party implementations, not novel algorithms authored by the project.
- No pretrained neural-network model is used in the WaterSense weighted-regression study.

## AI-assisted development

The existing README explicitly states that implementation was AI-assisted and that research direction was supplied by the author. The precise division of labor is not recoverable from the public files alone. A publication-ready disclosure should therefore name the tools used, describe the tasks they assisted with, and state that the owner reviewed code, tests, numerical outputs, and claims—only if the owner can truthfully confirm those actions.

## Safe first-person template, pending confirmation

> I investigated low-dissolved-oxygen reliability in station-grouped river monitoring data. I [designed/reviewed—choose only what is accurate] the nested cross-validation and weighting protocol, [implemented/validated—choose only what is accurate] the analysis and tests, and interpreted both the improvement in low-DO recall and the accompanying increase in false positives and overall error. I used public NIEA/OpenDataNI data and standard open-source ML libraries. AI-assisted tools supported [list exact tasks], and I independently verified [list exact checks].

Do not publish the template until every bracketed statement is replaced with a verified description.
