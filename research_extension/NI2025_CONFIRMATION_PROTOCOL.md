# Frozen 2025 temporal confirmation protocol

Recorded after schema/missing-target availability inspection and before any
2025 prediction. This is a local outcome-blind analysis freeze, not independent
preregistration. It supersedes neither the failed EA compatibility pilot nor
the historical model-selection protocols.

## Input and scope

DAERA/26-784 Annex A, published 2026-10-26, downloaded 2026-11-03, 1,044,781
bytes, SHA-256 9e8713d94835f1bdb9c71f9d5bb36cfc944ed925b206d09aa18216482aa75c7a.
Source: https://www.daera-ni.gov.uk/publications/daera26-784-river-water-quality-monitoring-data-all-northern-ireland-2025
The metadata audit saw 6,080 rows, 503 stations and 3,490 nonmissing DO values;
no low-DO prevalence or external predictive performance was inspected.

Use all eligible calendar-2025 river records. This is an acquired later-period
test in the same monitoring programme, potentially at known training stations.
It is not independent-region validation, a prospectively collected experiment,
or evidence for the V3 selected weighted procedure. The target is estimated
from contemporaneous predictors, not forecast from an earlier issue time.

## Model and mapping

Only the existing fitted Phase4 model, SHA-256
7434cbd29bf6a1b2b624ef3283d073212a82ec72a839d7a050bb912b8506f44f.
No refitting, recalibration, model choice, new temperature predictor or threshold
search. Use its saved feature order and preprocessing, fitted on historical
training stations. The new TEMP field is intentionally unused.

| Annex value | Historical raw column | Qualifier |
|---|---|---|
| ALK (mg/l) | ALK_mg_l_ | immediately preceding Q |
| BOD (mg/l) | BOD_mg_l_ | immediately preceding Q |
| COND (US/CM) | COND_US_CM_ | immediately preceding Q |
| DO (mg/l) | DO_mg_l_ | immediately preceding Q |
| NH4-N (mg/l) | NH4_N_mg_l_ | immediately preceding Q |
| NO2-N (mg/l) | NO2_N_mg_l_ | immediately preceding Q |
| NO3-N (mg/l) | NO3_N_mg_l_ | immediately preceding Q |
| P(SOL) (mg/l) | P_SOL__mg_l_ | immediately preceding Q |
| PH (PH UNITS) | PH_PHUNITS_ | immediately preceding Q |
| SS (mg/l) | SS_mg_l_ | immediately preceding Q |

Decode cp1252; verify the original CSV positional headers (repeated Q names).
Strip whitespace from qualifiers, normalize blank to missing, allow < and >.
Retain reporting-limit values plus frozen censor flags; never halve limits.
Map integer station n to UKGBNIF + n (station metadata only), parse DD/MM/YYYY
dates and HHMM time. Use ordinal source row ID within this separately hashed
file; it is not an historical OBJECTID. Run the unmodified historical cleaning
function after mapping, with YYYY/MM/DD dates.

Exclude missing/nonfinite/qualified targets with reason counts. Exclude rows
with nonfinite supplied predictors, unsupported qualifier codes or qualified
pH/conductivity, which the frozen feature schema cannot represent explicitly.
Missing predictor values remain missing for the existing training imputer.
No target quantile/outlier filters and no complete-case selection in the primary
cohort. Exclude every row of a conflicting station/date/time/depth identity group;
do not choose or average one member. Abort on invalid dates,
schema mismatch, nonempty old/new full-sample overlap or model/code hash mismatch.

Mapping is within NIEA's same named river chemistry programme and units. It
does not prove laboratory methods were unchanged across years; method changes
are a limitation of temporal transportability. Unlike cross-provider EA mapping,
no alternative determinand family or temperature reference is selected here.

## Evaluation and uncertainty

Measured and predicted low DO are strictly <4 mg/L. Primary: overall MAE,
low-DO MAE, recall, precision; report TP/FP/TN/FN, RMSE and R². Zero predicted
positives means undefined precision; zero actual positives means undefined
recall and low-DO MAE. Never replace these by favorable zeros.

5,000 whole-station bootstrap draws with replacement, seed 20261103, percentile
95% intervals. Report valid/undefined replicate counts. Fewer than 30 total
stations or 10 event-bearing stations triggers an insufficient-support warning
for stable rare-event claims; retain the descriptive result and intervals with
that limitation. No additional data is selected in response to the outcome.

Secondary predeclared strata: stations present/absent in the model's original
training partition. Record all 2025 stations overlapping the full historical
programme. Compare feature means, medians, 5th/95th quantiles and missingness
against historical training rows, without adapting the pipeline. Compare with
the saved Phase4 holdout using its identical model; V3 OOF metrics are context
only, not an external confirmation of weighting.

## Authority and stop rules

The user's current instructions authorize evaluation after compatibility and
freeze. The public release and DAERA Crown-copyright/OGL policy allow data reuse
with attribution; no endorsement, logos or sampler identities are republished.
The release letter discloses 2025 data and withholds unfinished 2026 data; the
latter is outside scope. No existing external human-signature requirement was
found, and no approval signature is invented. Passed overlap and adapter/code
hash gates must be recorded before loading the model for prediction.

Save a machine freeze with raw/model/adapter/protocol hashes and the eligible
cohort hash. Record local UTC time and Git HEAD. The evaluation must refuse to
overwrite its result file and fail on any freeze mismatch. Publish all outcomes,
including model failure, and do not inspect alternatives afterward.

## Pre-freeze amendment 1

The initial metadata gate stopped before a freeze or prediction because two
records share station 10546 / 2025-03-03 / 09:00 / depth 0 and have different
sampler metadata. They are not exact duplicate rows. The rule was amended
before performance access to exclude both records, retaining exclusion counts.
This is an outcome-blind QC amendment, not a post-result threshold or model
change. The failed initial gate is retained in the investigation record.
