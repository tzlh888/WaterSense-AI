# Data quality report

**Dataset:** NIEA River Water Quality Monitoring 1990–2024 — All Parameters  
**File inspected:** `data/raw/niea_river_water_quality_1990_2024.csv`  
**Inspection date:** 2026-09-30

This report is the Phase 2 data-quality snapshot. It separates facts observed in the downloaded CSV from interpretations that require judgement. No rows or values were changed during this audit; subsequent cleaning and modelling decisions are documented in `censoring_strategy.md`, `baseline_model_results.md` and `model_refinement.md`.

## Structural summary

| Observation | Interpretation |
|---|---|
| 178,680 rows and 40 columns. | The dataset is large enough for exploratory and baseline modelling work on ordinary hardware. |
| 13 chemistry-result columns and 13 paired qualifier columns. | Result and qualifier fields must be processed together; dropping qualifiers would lose detection-limit information. |
| 1,311 station codes, 1,304 location names and 61 non-missing primary basins. | There is strong spatial structure. Station-aware validation will be more credible than a random row split if the goal is generalisation to new locations. |
| Dates range from 1990-01-02 to 2024-12-11; every date parsed successfully. | Long temporal coverage supports trend exploration, but measurement practices and monitoring priorities may have changed over 35 years. This possibility is not documented by the CSV alone. |
| Annual row counts range from 2,376 (1990) to 7,468 (2009); 2020 has 2,697 records. | Sampling effort is uneven over time. Annual counts should not be interpreted as water-quality change. The reason for the 2020 count is not documented in the source. |

## Missing-value summary

Blank and whitespace-only cells are treated as missing for this audit.

| Chemistry result | Non-missing | Missing | Missing % |
|---|---:|---:|---:|
| Ammonia (`NH4_N_mg_l_`) | 174,667 | 4,013 | 2.246% |
| Nitrite (`NO2_N_mg_l_`) | 164,462 | 14,218 | 7.957% |
| Nitrate (`NO3_N_mg_l_`) | 163,872 | 14,808 | 8.287% |
| Soluble reactive phosphorus (`P_SOL__mg_l_`) | 168,073 | 10,607 | 5.936% |
| pH (`PH_PHUNITS_`) | 155,301 | 23,379 | 13.084% |
| BOD (`BOD_mg_l_`) | 151,264 | 27,416 | 15.344% |
| Dissolved oxygen (`DO_mg_l_`) | 151,037 | 27,643 | 15.471% |
| Alkalinity (`ALK_mg_l_`) | 124,296 | 54,384 | 30.437% |
| Conductivity (`COND_US_CM_`) | 117,509 | 61,171 | 34.235% |
| Suspended solids (`SS_mg_l_`) | 116,752 | 61,928 | 34.659% |
| Dissolved copper (`D_Cu_µg_l_`) | 92,741 | 85,939 | 48.097% |
| Dissolved zinc (`ZNSOL_µg_l_`) | 36,490 | 142,190 | 79.578% |
| Dissolved iron (`D_FE_µg_l_`) | 36,414 | 142,266 | 79.621% |

**Observation:** 442 rows contain no non-missing chemistry result; only 14,675 rows are complete across all 13 chemistry results.  
**Interpretation:** A complete-case analysis across every measurement would discard most rows and may select a non-representative subset. Predictor selection and imputation must be justified after studying missingness by station and year.

**Observation:** For a provisional dissolved-oxygen regression using BOD, ammonia, nitrite, nitrate, soluble reactive phosphorus and pH, 135,283 rows have all seven values present. Adding conductivity reduces this overlap to 105,739 rows.  
**Interpretation:** A useful regression sample may exist without using the sparsest metals, but the feature set must be chosen before test data are examined.

## Duplicates and identifiers

| Observation | Interpretation |
|---|---|
| Exact duplicate rows: 0. | There is no evidence for deleting duplicate rows. |
| Duplicate `StationCode` + `Date` + `Time` combinations: 0. | The three fields identify unique sampling records in this export. |
| `OBJECTID` is unique and sequential from 1 to 178,680. | It is a database identifier and should not be used as a predictor; it may encode export/order information. |
| `X` exactly equals `Easting`, and `Y` exactly equals `Northing`, for every row. | Keep one coordinate pair during cleaning to avoid redundant features. |
| `Depth` is zero for all rows. | The field has no predictive variation and should normally be excluded unless documentation reveals a different meaning. |

## Detection and quantification qualifiers

| Qualifier | `<` count | `>` count |
|---|---:|---:|
| Alkalinity | 2,980 | 0 |
| BOD | 31,191 | 898 |
| Dissolved copper | 5,671 | 0 |
| Dissolved iron | 5,750 | 0 |
| Dissolved oxygen | 6 | 0 |
| Ammonia | 52,951 | 8 |
| Nitrite | 32,106 | 0 |
| Nitrate | 6,327 | 0 |
| Soluble reactive phosphorus | 27,312 | 2 |
| Suspended solids | 23,293 | 0 |
| Dissolved zinc | 22,660 | 0 |

**Observation:** Conductivity and pH qualifier columns are completely blank. Other qualifier columns mark many results with `<` and a smaller number with `>`.  
**Interpretation:** Values paired with `<` are left-censored rather than fully observed at the stored number. Treating them as ordinary exact measurements could bias distributions. The source mentions half-value treatment for Water Framework Directive calculations, but whether that rule is appropriate for this ML question must be decided and documented with domain guidance.

## Data types and schema issues

| Observation | Interpretation |
|---|---|
| Dates and times arrive as strings; dates parse successfully. | Convert date explicitly in processed data and derive time features only when relevant to the research question. |
| Chemistry results parse as numeric after blank fields are recognised. | Basic numeric conversion is feasible, but each result must remain linked to its qualifier. |
| `D_FE_µg_l_` and the ArcGIS field alias specify µg/L, while the catalogue prose says mg/L. | Do not model or compare dissolved iron until the unit conflict is resolved with NIEA documentation. |
| `OpenClosed` is missing for 29,891 rows and `DateClosed` for 173,160 rows. | Blank status fields must not be silently interpreted as open or closed. |

## Suspicious values and possible outliers

The following are review flags, not deletion decisions or regulatory exceedances.

| Measurement | 99th percentile | Maximum | Rows outside 1.5 × IQR | Observation / interpretation |
|---|---:|---:|---:|---|
| BOD (mg/L) | 9.3 | 632.0 | 13,978 | Maximum is far above most records; source warning makes record-level verification necessary. |
| Conductivity (µS/cm) | 736 | 39,900 | 2,715 | Extreme maximum could be real, a different water influence, or an error; location/date and source record must be checked. |
| Dissolved oxygen (mg/L) | 14.5 | 41.9 | 5,028 | High maximum is suspicious-looking but is not removed or labelled impossible without measurement context. |
| Soluble reactive phosphorus (mg/L) | 0.86 | 67.0 | 16,160 | Strong right tail requires checking qualifiers, station history and possible decimal/unit errors. |
| Suspended solids (mg/L) | 85 | 3,232 | 9,913 | Large values may reflect high-flow events or errors; no flow/context field is present. |
| pH | 8.7 | 10.9 | 4,785 | Values remain within the conventional 0–14 mathematical scale, but the minimum 0.82 and upper tail require source-level review. |

**Observation:** No chemistry result is negative. All pH values lie between 0.82 and 10.9.  
**Interpretation:** The generic negative-value and pH-scale checks did not find obvious mathematical impossibilities. This does not prove that all measurements are valid.

## Target and class balance

**Observation:** No risk class, ecological-status class, compliance result or safety label exists.  
**Interpretation:** There is no class distribution to analyse, and supervised classification must not be performed.

**Observation:** Dissolved oxygen is a continuous measurement with 151,037 non-missing values.  
**Interpretation:** Regression is the most defensible provisional supervised task. Its target distribution is continuous and should be evaluated for tails and site/time structure, not converted into arbitrary classes.

## Leakage and validation concerns

- A random row split would place repeated observations from the same station into training and test sets. This could measure interpolation within known sites rather than generalisation to unseen sites.
- Coordinates, station code, location and basin can act as location identifiers. They may be useful, but they can also let a model memorise site-level patterns.
- Dates and `OBJECTID` are ordered. `OBJECTID` is not a scientific feature and may leak collection/export ordering.
- If the goal is future prediction, a chronological split is needed. If the goal is transfer to new monitoring sites, a grouped split by `StationCode` is needed. These are different claims.
- Measurements on the same row are contemporaneous. A model predicting dissolved oxygen from them estimates a co-measured value; it does not automatically forecast future water quality.

## Data-quality limitations

At the end of Phase 2, the unresolved issues were censored results, heterogeneous missingness, potential erroneous extremes, unequal sampling effort, repeated-site dependence, absent temperature and the iron-unit conflict. No cleaning or modelling was performed within this historical audit. Later project phases addressed the modelling decisions while preserving absent temperature and unresolved source-level extremes as limitations.
