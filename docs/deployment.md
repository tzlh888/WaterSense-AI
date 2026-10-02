# Deployment Guide

## Local Run

From the repository root:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
streamlit run app/app.py
```

The app does not require credentials or a `secrets.toml` file.

## GitHub Preparation

The raw export and full processed modelling table remain excluded by `.gitignore`. Public-facing files in `data/app/` are reproducibly generated from the processed data with:

```bash
python scripts/build_app_artifacts.py
```

The verified model is approximately 176 MB, above GitHub's normal 100 MB single-object limit. `.gitattributes` therefore marks only `models/phase4_selected_model.joblib` for Git LFS. Before the first commit containing the model:

```bash
git lfs install
git lfs track "models/phase4_selected_model.joblib"
git lfs ls-files
```

Review staged files before committing. Do not commit `.env`, `.streamlit/secrets.toml`, raw data, processed data, virtual environments, caches or OS metadata.

## Streamlit Deployment

Streamlit Community Cloud can deploy from a GitHub repository and supports Git LFS files. Create the app manually and select:

- repository: the reviewed public WaterSense AI repository;
- branch: the intended release branch;
- entrypoint: `app/app.py`;
- Python: a currently supported version compatible with the pinned requirements.

No secrets are needed. Do not enter placeholder credentials.

## Required Files

The deployed application requires:

- `app/`;
- `.streamlit/config.toml`;
- `requirements.txt`;
- `models/phase4_selected_model.joblib` via Git LFS;
- `data/app/`;
- the small executed CSV tables in `results/` used by the app.

The raw export and `data/processed/water_quality_modeling.csv` are not required at runtime.

## Expected Resource Usage

- verified model on disk: 175,556,503 bytes (approximately 176 MB); SHA-256 `7434cbd29bf6a1b2b624ef3283d073212a82ec72a839d7a050bb912b8506f44f`;
- public app data: approximately 1.8 MB compressed;
- model: loaded once per server process with `st.cache_resource`;
- app tables: loaded with `st.cache_data`;
- no database, external API or background worker.

Peak deployment memory and cold-start time must be confirmed on the selected hosting account; they are not inferred from file size alone.

The model artifact is a Joblib/pickle-family binary. Load it only from this reviewed project or another trusted source. Compatibility is protected by pinning the direct package versions used for final verification, especially scikit-learn and Joblib.

## Troubleshooting

### Model artifact missing or contains an LFS pointer

Confirm Git LFS is installed, the model is tracked, and the full binary—not only its pointer—was fetched:

```bash
git lfs pull
git lfs ls-files
```

### Application data missing

Reproduce Phase 4 locally, then run:

```bash
python scripts/build_app_artifacts.py
```

Commit the resulting small files in `data/app/`.

### Dependency incompatibility

Install from the committed `requirements.txt`. If a hosting Python version cannot install those versions, choose another currently supported Python version rather than silently changing scikit-learn.

### Resource-limit error

Check hosting logs and memory use. Confirm the app is reading `data/app/` instead of the full processed dataset and that the model/data caches are active.

### Scientific or numerical mismatch

Do not retrain during deployment. Run the full test suite and compare the model artifact metadata, feature order and documented Phase 4 metrics before publishing.
