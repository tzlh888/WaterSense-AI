# External data compatibility: evidence and decision

**Subsequent compatible source:** DAERA/26-784 supplied the complete same-
programme 2025 field schema. A separate pre-prediction freeze and single
evaluation were completed; see the
[2025 confirmation report](../../research_extension/ni2025_confirmation/TEMPORAL_CONFIRMATION_REPORT.md).
The EA-specific block below remains. The new test is temporal, not cross-region,
and does not validate the V3 selected weighted procedure.

## Decision

**EA pilot: NOT FEASIBLE for the planned confirmation evaluation.** This is
limited to the recorded ten-station pilot, not a conclusion that all England
data are incompatible. Full EA evaluation remains **BLOCKED** by unresolved
measurement mapping and an unsealed sufficiently supported cohort. No external
model was loaded or used for prediction, and no external performance was scored.

The current user authorizes lawful investigation and compatible evaluation
subject to the existing gates. No additional signed external approval is
established or fabricated. Repository V4 requires a passed overlap audit and
explicit frozen-model adapter; those requirements are not yet satisfied.
The [protocol](../../research_extension/EXTERNAL_COMPATIBILITY_PROTOCOL.md)
fixes the pilot, candidate model, threshold, metrics, interval plan, QC rules
and final-freeze requirements. It does not claim a completed confirmation freeze.

## Actual acquisition and provenance

The [official catalogue](https://www.data.gov.uk/dataset/583e771f-1af6-4934-b8f0-28f1d1ddd48c/water-quality-explorer)
identifies EA as publisher, England as scope, and Open Government Licence as
the licence. The live [API documentation](https://environment.data.gov.uk/water-quality/api-docs)
serves OpenAPI 1.3.1 via `/water-quality/api/swagger`.

Several legacy URLs returned 404. Current public routes require content
negotiation: `Accept: application/ld+json`, `API-Version: 1`. Without suitable
negotiation even the current proxy returned empty responses. Every URL, HTTP
status, retrieval time and payload hash is retained in the probe JSON files.
An HTTP 200 with zero bytes was not treated as a valid dataset.

The actual river station code is **F6**; FJ denotes canals. Station material
**2AZZ** is river/running surface water. These definitions were verified from
live codelists before the pilot. The first ten open F6 points returned by the
recorded request form an alphabetically clustered Anglian pilot, not an England
probability sample. Pagination was checked on all requests.

For calendar 2025 the pilot returned **430 determinand observations**, comprising
**49 exact sample identities at six stations** (four requested stations had no
matching records). Dates span 2025-01-07 to 2025-12-10. The station IDs have zero
literal overlap with 1,311 historical NIEA IDs; region and year provide stronger
provenance separation, but a final cross-provider physical-sample audit is still
required. England data were not added to development or used to choose a model.

## Feature mapping audit

| Frozen requirement | EA code and observed definition | Pilot coverage | Mapping decision |
|---|---|---:|---|
| DO mg/L | 9924, dissolved oxygen as O2, mg/l | 49 | Measurement quantity/unit available; field/lab protocol equivalence still needs documentation. 9901 saturation is not substituted. |
| BOD mg/L | 0085, 5-day ATU, mg/l | 29 | NI export does not establish incubation/inhibitor equivalence. |
| Ammonia as N mg/L | 0111, ammoniacal nitrogen as N, mg/l | 49 | Chemical expression/unit compatible at label level; method/QC equivalence incomplete. |
| Nitrite as N mg/L | 0118, nitrite as N, mg/l | 49 | Same label-level status. |
| Nitrate as N mg/L | 0117, nitrate as N, mg/l | 49 | Same label-level status; NO3 mass is not silently equated with N mass. |
| Soluble reactive P mg/L | 0180, reactive orthophosphate as P, mg/l | 49 | Solubility/filter equivalence unresolved; other total/filtered phosphate codes are not interchangeable. |
| pH | 0061, PHUNITS | 49 | Compatible quantity; lab versus in-situ context not fully harmonized. |
| Alkalinity mg/L | 0162, pH-4.5 titration as CaCO3 | 49 | NI chemical basis/endpoint undocumented in export. |
| Conductivity µS/cm | 0077, conductivity at 25 C | 49 | NI reference temperature undocumented; 20C/25C conversions are not invented. |
| Suspended solids mg/L | 0135, solids at 105 C | 9 | NI preparation method undocumented. |
| Date harmonics | exact sample timestamp | 49 | Deterministically derivable after final adapter freeze. |
| Censor indicators | 45 upper-bound results across predictors | 45 | Numeric upper limits must be retained with `<` flags; null numericValue must not erase reporting limits. |

Among these samples, BOD and suspended solids never occur together; **zero**
samples have all ten determinands. This alone does not prohibit use of the
frozen imputer: intermittent missing predictors can be legitimate. It does
prevent claiming complete-case full-feature coverage, and the unresolved method
definitions prevent passing the strict frozen mapping gate. Six stations also
fail the protocol's planned 30-station support requirement.

`ea_sample_joint_coverage.csv` uses exact sample IDs. It never merges rows
merely because station and day coincide. No ambiguous-code pooling, target
conversion from saturation, half-limit substitution or feature invention was
performed. The archive describes verified source results but does not expose
all laboratory QC information in these rows; source inclusion is not a quality
guarantee. Available qualifier bounds and sampling purpose are retained.

## Other independent sources investigated

**US Water Quality Portal:** the [official guide](https://www.waterqualitydata.us/portal_userguide/)
provides activity identifiers, chemical speciation, sample fraction, units,
result status, analytical methods and detection-limit links. This is a plausible
future source, but those fields must be checked per organization/method. A fixed
2025 query for USGS-01463500 returned a valid 63-column CSV header with zero
rows; this single query is NOT FEASIBLE as an evaluation cohort. It does not
establish absence of usable WQP records elsewhere. No global search or model
evaluation was claimed.

**EEA Waterbase:** [annual aggregated data](https://dd.eionet.europa.eu/datasets/latest/WISE-SoE_WaterQualityICM/tables/AggregatedData)
are NOT FEASIBLE for sample-level `DO < 4 mg/L` validation, since annual means
discard event identity and threshold excursions. The separate
[disaggregated table](https://dd.eionet.europa.eu/datasets/latest/WISE-SoE_WaterQualityICM/tables/DisaggregatedData)
is a further candidate, not rejected wholesale. Same-sample feature coverage,
country-specific methods and potential UK/NIEA overlap still require auditing.

## Material needed to unlock the gate

1. Publisher method documentation resolving NI BOD, alkalinity basis,
   conductivity temperature and P/sample-fraction definitions.
2. A sufficiently supported external cohort chosen before prediction access.
3. Frozen mapping, exact unit/QC conversions, exclusions and adapter source hash.
4. Cohort byte hash and complete physical-sample overlap checks.
5. A final signed record only if a governing human approval requirement is
   identified; no such signature is supplied by this audit.

No EA performance is reported. The subsequent NIEA 2025 test reports all
outcomes in its separate report, including 17/20 missed low-DO observations.
