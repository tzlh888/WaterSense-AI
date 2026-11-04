# External compatibility investigation — sealed evaluation boundary

This is a prospective compatibility protocol, not a preregistration of successful
validation. No external predictions have been inspected or generated.

## Fixed audit sample

EA API 1.3.1; negotiated API-Version 1, Accept application/ld+json. Inspect the
first ten station identifiers returned by the recorded `samplingPointType=F6`,
`samplingPointStatus=O`, `limit=10` request. F6 is freshwater rivers; FJ is canals
and must not be used. Restrict observations to 2025-01-01 through 2025-12-31,
sample material 2AZZ (river/running surface water). These sites form an API
compatibility pilot, not a representative England confirmation cohort.

Read determinands and units, qualifiers, exact sample IDs, timestamps and joint
coverage only. No fitting, prediction, model selection or performance metric is
permitted in this audit. Record pagination; incomplete retrieval cannot pass.

## Candidate model and future evaluation plan

Historical Phase4 deployed Random Forest SHA-256
7434cbd29bf6a1b2b624ef3283d073212a82ec72a839d7a050bb912b8506f44f.
The actual saved pipeline and its 25 feature columns are the candidate. V3/V4
OOF rows do not constitute exportable final fitted models and are not silently
substituted. No external adaptation or refitting is allowed.

Outcome definition remains measured DO < 4 mg/L; predictions < 4 mg/L. Primary
metrics: overall MAE, low-DO MAE, recall and precision; report TP/FP/TN/FN.
Uncertainty: 5,000 paired complete-station bootstrap draws, seed 20261103,
percentile 95% intervals; count undefined denominators. Require at least 30
eligible stations and 10 event-bearing stations for the planned cluster summary;
otherwise report insufficient support and refrain from stable reliability claims.

Only exact sample identity joins are allowed, never station/date approximations.
Ambiguous duplicate determinands, invalid/censored targets, nonfinite values,
unsupported qualifiers and incompatible units are excluded with reason counts.
Preserve numeric reporting limits plus known < / > flags as in training; do not
replace limits by half-values. A validated missing field may use the frozen
training imputer; a structurally unavailable or chemically incompatible feature
cannot be invented as all-missing to claim full compatibility.

Before any external evaluation, a separate final freeze must contain a hashed
cohort file, exact feature mapping with method/unit equivalence, overlap audit,
fixed pipeline feature order, QC exclusions, and executable adapter hash. Until
then **EVALUATION BLOCKED**. This audit protocol does not itself pass the gate.
The current user authorizes compatible evaluation subject to existing gates;
no human signature is invented. Existing V4 adapter/overlap requirements remain.

Unresolved mapping decisions (not adopted): NI BOD method versus EA 5-day/ATU
variants; NI unspecified conductivity temperature versus 20C/25C; NI alkalinity
chemical basis versus CaCO3; soluble reactive P versus filtered orthophosphate
and filter type. Labels alone cannot resolve these measurement differences.
