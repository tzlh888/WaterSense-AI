# WaterSense AI — Research Contribution Statement

## Attribution rule

The applicant has confirmed that they were the sole human project lead and that AI tools assisted throughout research and development. Repository ownership, file presence, and GitHub account ownership still do not prove that one person independently wrote every line or made every research decision. This statement separates artifact-verifiable project contents and confirmed project-level facts from task-level biographical claims that require further confirmation.

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

These facts show what the project contains. The sole-human-lead confirmation does not by itself establish unaided authorship or which specific ideas, code, reviews, or interpretations originated with the applicant.

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

## Confirmed project-level attribution and AI assistance

The applicant was the sole human project lead. AI tools provided assistance during research and development, including technical discussions, coding, experiment analysis, checking, and documentation. Specific task-level idea attribution and unaided implementation claims are not asserted without supporting evidence.

## Applicant confirmation status

Project-level leadership and broad AI assistance are confirmed. Specific claims about who originated a method, personally wrote particular code, performed a particular check, or completed work without AI assistance remain pending unless supported by contemporaneous evidence and the applicant's explicit confirmation.
