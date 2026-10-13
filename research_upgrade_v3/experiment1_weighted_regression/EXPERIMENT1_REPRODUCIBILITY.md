# Experiment 1 Reproducibility

## Commands

```bash
python3 scripts/run_experiment1_weighted_regression.py
python3 -m unittest tests.test_weighted_regression_experiment -v
```

## Identity

- Baseline HEAD: `3553b29ff104918b12da8c84d2c9a8c5ed032e18`.
- Experiment config canonical SHA-256: `39d12658f1d63a3a0cd98ee1edd625163c42f8a57f009203fd5e2f04aa660896`.
- Processed data SHA-256: `5685c2c352b1cc9502cd664736d85295580127016fb60bdca45c082c5d031761`.
- Historical membership SHA-256: `b42814782f7290ab73faece96634c7a65448912ea40891f3c9a714b157594229`.
- Frozen site assignment SHA-256: `0fa76b39cd3697aed2b615f5921a2cfa8dbaf0fdbd216393520c25c52bf58025`.
- Frozen fold support SHA-256: `d0e29ddeb6b77263fdafe4f5a654c550395e885170a79a4d563d0740c42d1379`.
- Seed: 20261012.
- Bootstrap: 2000 paired whole-site draws.

## Checkpoint recovery

Each completed inner fold and outer prediction pair has its own CSV hash plus the experiment config hash. A restart accepts a checkpoint only when both identities match; otherwise it fails closed. Checkpoints are not counted twice because final tables are rebuilt from one checkpoint per frozen fold.

## Environment

- Python: 3.14.0.
- NumPy: 2.5.3.
- pandas: 3.0.6.
- scikit-learn: 1.9.1.
- joblib: 1.6.0.
