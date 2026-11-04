# WaterSense AI — final research summary (owner attribution pending)

Why can apparently accurate machine-learning models fail on rare but important
environmental events? WaterSense examines this question using 151,031
historical river observations at 840 Northern Ireland stations (1990–2024),
with a 119,690-row nested station-grouped V3 development experiment.

The selected procedure improves low-DO MAE from 3.3235 to 2.3613 mg/L and recall
from 0.1293 to 0.3641, while increasing overall MAE from 0.8797 to 0.9516 and
false positives from 26 to 219. Low-DO observations are concentrated across
stations beyond a simple sampling-volume null; inverse HHI is concentration,
not statistical effective sample size or geographic risk.

Exact source recovery enables fixed historical replay. A later, locally frozen
Phase4 evaluation on 3,490 measured-target 2025 rows at 494 stations gives
MAE 0.6432 mg/L [95% station-bootstrap 0.5896–0.7176], but recall 0.15
[0–0.3462], with TP/FP/TN/FN=3/0/3470/17. DO is missing in 42.60% of the
source records. Twenty low-DO events occur at only nine stations and all
detections at one station. A suspicious 94 mg/L source value dominates squared
error; separately omitting it post hoc leaves the 17 low-DO misses unchanged.
Primary results are retained. Local Git records are not third-party preregistration.

The contribution is a transparent failure analysis with group-aware validation,
station-level uncertainty and preserved negative evidence. Independent-region
validation, confirmation of V3 weighting and operational decision costs remain
outstanding. The system estimates current co-measured DO; it is not a forecast
or validated warning tool.

Substantial AI assistance covered engineering, analysis and drafting. Personal
authorship is unverified; see the [owner checklist](OWNER_CONTRIBUTION_CONFIRMATION.md).
