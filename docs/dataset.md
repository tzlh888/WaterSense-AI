# Dataset overview

## Source

**Dataset:** River Water Quality Monitoring 1990 to 2024 — All Parameters  
**Official catalogue:** [National Data Library / OpenDataNI](https://www.data.gov.uk/dataset/0840ab33-18ae-4670-8523-ac43105f5902/river-water-quality-monitoring-1990-to-2024-all-parameters)  
**Official service:** [ArcGIS FeatureServer](https://services-eu1.arcgis.com/kswen6BYexuc1SUk/arcgis/rest/services/River_Water_Quality_Monitoring_1990_to_2024_All_Parameters/FeatureServer)  
**Licence:** [UK Open Government Licence v3.0](https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/)  
**Local raw file:** `data/raw/niea_river_water_quality_1990_2024.csv`  
**SHA-256:** `a5ce02d9ab3703edc4279c8dc5f9d38a593b92c555945c5cdb2ab3ca55632632`

The local file is an unchanged CSV export from the official ArcGIS Hub service. It is ignored by Git because it is approximately 31.7 MB; the checksum records the exact file inspected in this phase.

## Original organisation

Northern Ireland Environment Agency (NIEA), Water Science and Evidence Unit, within the Department of Agriculture, Environment and Rural Affairs (DAERA). The public catalogue publisher is OpenDataNI.

## Geographic coverage

Northern Ireland river-monitoring stations, including Water Framework Directive monitoring sites. The file contains 1,311 unique station codes, 1,304 location names and 61 non-missing primary-basin names. Coordinates are supplied as projected X/Y and easting/northing values; the service reports a metre-based spatial reference identified as 29900 (29902).

## Time coverage

The source describes coverage from 1 January 1990 through 31 December 2024. Dates actually present in the downloaded file run from **2 January 1990 through 11 December 2024**. All 178,680 date strings parsed successfully using the documented `YYYY/MM/DD` form. Sampling frequency is not fixed in the source and the observed number of records varies by year and station.

## Number of observations

- Rows: **178,680**
- Columns: **40**
- Exact duplicate rows: **0**
- Duplicate station/date/time combinations: **0**
- Chemistry result columns: **13**
- Paired qualifier columns: **13**

One row represents a dated and timed monitoring record at one station. The export is wide: different measurements from the same sampling record occupy separate columns.

## Variables

Blank and whitespace-only fields are counted as missing below. “Missing values” describes the downloaded file, not all historical versions of the source.

| Variable | Meaning | Unit | Data type after loading | Missing values | Notes |
|---|---|---|---|---:|---|
| `X` | Projected x coordinate | metres | integer | 0 | Exactly duplicates `Easting` in this export. |
| `Y` | Projected y coordinate | metres | integer | 0 | Exactly duplicates `Northing` in this export. |
| `OBJECTID` | ArcGIS row identifier | none | integer | 0 | Unique sequential identifier; not a scientific predictor. |
| `StationCode` | Monitoring-station identifier | none | string | 0 | 1,311 unique values. |
| `OpenClosed` | Station open/closed field | none | string | 29,891 (16.729%) | Values present are `Open` and `Closed`; blanks are not interpreted. |
| `DateClosed` | Recorded station closure date | Unknown / not documented | string | 173,160 (96.911%) | Primarily present for closed stations. |
| `Location` | Station/location name | none | string | 0 | 1,304 unique values. |
| `PrimaryBasin` | Named primary river basin | none | string | 1,733 (0.970%) | 61 non-missing names. |
| `GridReference` | Grid-reference text | none | string | 0 | Location field, not a water-quality measurement. |
| `Easting` | Projected easting coordinate | metres | integer | 0 | Exactly duplicates `X`. |
| `Northing` | Projected northing coordinate | metres | integer | 0 | Exactly duplicates `Y`. |
| `Depth` | Depth field | Unknown / not documented | integer | 0 | Constant value `0` in every row; currently uninformative. |
| `Date` | Sampling date | date | string in raw CSV | 0 | Parses without error as `YYYY/MM/DD`. |
| `Time` | Sampling time | time | string | 0 | Exact timezone and field protocol are not documented in the catalogue. |
| `Q_Alk` | Qualifier paired with alkalinity | none | string | 175,700 (98.332%) | 2,980 `<` flags; exact qualifier coding is not separately documented. |
| `ALK_mg_l_` | Alkalinity | mg/L | float | 54,384 (30.437%) | Numeric result. |
| `Q_BOD` | Qualifier paired with BOD | none | string | 146,591 (82.041%) | 31,191 `<` and 898 `>` flags. |
| `BOD_mg_l_` | Biochemical oxygen demand | mg/L | float | 27,416 (15.344%) | Numeric result. |
| `Q_COND` | Qualifier paired with conductivity | none | float/all missing | 178,680 (100%) | Empty column in this export. |
| `COND_US_CM_` | Conductivity | µS/cm | float | 61,171 (34.235%) | Source alias uses `US/CM`. |
| `Q_DCu_µg_l_` | Qualifier paired with dissolved copper | none | string | 173,009 (96.826%) | 5,671 `<` flags. |
| `D_Cu_µg_l_` | Dissolved copper | µg/L | float | 85,939 (48.097%) | Numeric result in the CSV. |
| `Q_Fe` | Qualifier paired with dissolved iron | none | string | 172,930 (96.782%) | 5,750 `<` flags. |
| `D_FE_µg_l_` | Dissolved iron | µg/L in field alias/export | float | 142,266 (79.621%) | Catalogue prose says mg/L, but the official field alias and CSV header say µg/L; this conflict must be resolved before modelling iron. |
| `Q_DO` | Qualifier paired with dissolved oxygen | none | string | 178,674 (99.997%) | Six `<` flags. |
| `DO_mg_l_` | Dissolved oxygen | mg/L | float | 27,643 (15.471%) | Selected continuous regression target in Phases 3–5. |
| `Q_NH4N` | Qualifier paired with ammonia | none | string | 125,721 (70.361%) | 52,951 `<` and 8 `>` flags. |
| `NH4_N_mg_l_` | Ammonia as nitrogen | mg/L | float | 4,013 (2.246%) | Exact chemical expression follows the source field name. |
| `Q_NO2N` | Qualifier paired with nitrite | none | string | 146,574 (82.032%) | 32,106 `<` flags. |
| `NO2_N_mg_l_` | Nitrite as nitrogen | mg/L | float | 14,218 (7.957%) | Exact chemical expression follows the source field name. |
| `Q_NO3N` | Qualifier paired with nitrate | none | string | 172,353 (96.459%) | 6,327 `<` flags. |
| `NO3_N_mg_l_` | Nitrate as nitrogen | mg/L | float | 14,808 (8.287%) | Exact chemical expression follows the source field name. |
| `Q_PSOL` | Qualifier paired with soluble reactive phosphorus | none | string | 151,366 (84.713%) | 27,312 `<` and 2 `>` flags. |
| `P_SOL__mg_l_` | Soluble reactive phosphorus | mg/L | float | 10,607 (5.936%) | Source describes this as phosphorus, soluble reactive (SRP). |
| `Q_pH` | Qualifier paired with pH | none | float/all missing | 178,680 (100%) | Empty column in this export. |
| `PH_PHUNITS_` | pH | pH units | float | 23,379 (13.084%) | Dimensionless logarithmic scale, conventionally reported as pH units. |
| `Q_SS` | Qualifier paired with suspended solids | none | string | 155,387 (86.964%) | 23,293 `<` flags. |
| `SS_mg_l_` | Suspended solids | mg/L | float | 61,928 (34.659%) | Numeric result. |
| `Q_ZnSOL` | Qualifier paired with dissolved zinc | none | string | 156,020 (87.318%) | 22,660 `<` flags. |
| `ZNSOL_µg_l_` | Dissolved zinc | µg/L | float | 142,190 (79.578%) | Numeric result. |

## Target variable

The dataset contains **no risk class, ecological-status class, regulatory-compliance field or drinking-water safety label**. Supervised risk classification is therefore not justified.

The implemented supervised task is **regression with `DO_mg_l_` (dissolved oxygen in mg/L) as a continuous target**:

- it is an observed measurement rather than an invented label;
- it has 151,037 non-missing observations;
- BOD, ammonia, nitrite, nitrate, soluble reactive phosphorus and pH overlap on 135,283 rows with a non-missing dissolved-oxygen result; and
- it permits an explainable question about predictive associations among co-measured river-chemistry variables.

This estimates a contemporaneous measurement, not future oxygen, and does not classify water as safe or unsafe. Temperature—an important contextual variable for dissolved oxygen—is absent: no temperature-named field or alternative documented water-temperature representation exists in the 40-column export. The regression target and grouped validation strategy were implemented in Phases 3 and 4 and retained in Phase 5 reporting.

## Dataset limitations

- The official source warns that typos, sampling error or contamination may produce values several orders of magnitude above expected values.
- Missingness varies from 2.246% for ammonia to about 79.6% for dissolved iron and zinc; 442 rows have all 13 chemistry results missing.
- Qualifier columns contain `<` and occasional `>` markers. These are censored measurements, not ordinary missing values. The service notes a half-value rule for Water Framework Directive calculations, but that rule must not be adopted automatically for a different ML objective.
- Only 14,675 rows are complete across all 13 chemistry results.
- Sampling intensity varies across stations and years; observations are not independent random draws.
- A random row split could put the same station and nearby dates into both training and test sets, overstating generalisation.
- `X`/`Easting` and `Y`/`Northing` are duplicate fields; `Depth` is constant; `OBJECTID` is only an identifier.
- Several maxima are far above the corresponding 99th percentile and require record-level investigation, not automatic deletion.
- Temperature, turbidity and TDS are not included.
- The dissolved-iron unit is inconsistent between catalogue prose and the exported schema/header.
- Geographic coverage is Northern Ireland rivers; conclusions would not automatically generalise to other regions or water types.
