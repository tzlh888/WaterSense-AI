# WaterSense AI Project Timeline

| Phase | Objective | Main decision | Main result |
|---|---|---|---|
| 1 — Architecture | Establish a reproducible research repository. | Separate raw data, processing, modelling, results, tests and documentation. | A traceable project structure with immutable raw-data handling. |
| 2 — Dataset validation | Select and audit a credible water-quality dataset. | Use the NIEA/DAERA river-monitoring export and avoid inventing a safety label. | Verified provenance, schema, licence, missingness, censoring and limitations. |
| 3 — Baseline modelling | Test whether chemistry predicts continuous dissolved oxygen. | Use station-grouped holdout validation instead of random row splitting. | Baseline regressors and a documented first error analysis on unseen stations. |
| 4 — Refinement and explainability | Improve the model without contaminating the final holdout. | Select features and parameters with training-only GroupKFold; retain non-causal explanations. | Random Forest holdout MAE 0.831 mg/L, with clear extreme-value limitations. |
| 5 — Research report | Package the work for academic and portfolio review. | Keep one consistent scientific claim across reports and summaries. | Academic report, portfolio copy, interview preparation and claim audit. |
| 6 — Interactive application | Expose the verified research through a usable local interface. | Load the saved pipeline unchanged and keep limitations beside predictions. | Five-page Streamlit app with exact input contract and application tests. |
| 7 — Deployment and portfolio preparation | Prepare a public repository and safe manual deployment. | Use lightweight derived app data and Git LFS for the unchanged verified model. | Responsive UI polish, deployment documentation, screenshots and final portfolio assets. |

The project remains an educational contemporaneous-estimation study, not a safety classifier, regulatory assessment or forecasting system.
