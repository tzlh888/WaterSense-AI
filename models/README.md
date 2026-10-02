# Model Artifact

`phase4_selected_model.joblib` is the complete verified Phase 4 preprocessing-and-regression pipeline.

- model: Random Forest;
- size: 175,556,503 bytes (approximately 176 MB);
- SHA-256: `7434cbd29bf6a1b2b624ef3283d073212a82ec72a839d7a050bb912b8506f44f`;
- producing command: `python -m src.refine`;
- verified scikit-learn version: 1.9.1;
- verified Joblib version: 1.6.0.

The file exceeds GitHub's normal 100 MB object limit and is therefore configured for Git LFS in `.gitattributes`. Other exploratory/baseline model files remain ignored.

Joblib artifacts can execute Python objects while loading. Use only the file reproduced by this project or obtained from the reviewed project release, and verify its checksum before replacing it. The Streamlit application never downloads or retrains a replacement automatically.
