# WaterSense V4 reproducibility

Status: **PASS for code/tests and V4 development analysis; PARTIAL for full scientific confirmation.**

Commands from the repository root:

```bash
PYTHONPATH=. python -m unittest discover -s tests -v
PYTHONPATH=. python research_upgrade_v4_candidate/v4_upgrade.py
PYTHONPATH=. python -m unittest discover -s research_upgrade_v4_candidate -p 'test_*.py' -v
```

Use a compatible environment installed from `requirements.txt`. The V4 runner writes only to its candidate directory and verifies exact row/station coverage. Raw and processed data remain ignored local artifacts and are hash-recorded in the baseline manifest. Independent confirmation cannot be reproduced because no qualifying external dataset exists.
