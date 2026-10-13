# WaterSense Data Recovery Report

## Result

**Exact historical recovery succeeded.** The official ArcGIS Hub CSV exported in British National Grid spatial reference `29902` has SHA-256 `a5ce02d9ab3703edc4279c8dc5f9d38a593b92c555945c5cdb2ab3ca55632632`, exactly matching both historical research manifests. It contains 178,680 rows, 40 columns, 1,311 station codes, unique `OBJECTID`, and dates from 1990-01-02 to 2024-12-11.

An initial WGS84 (`4326`) export had a different byte hash because its X/Y representation differed. It was not accepted as historical recovery. The exact `29902` export replaced it in the ignored raw-data location; the nonhistorical download was retained only outside the repository as working evidence.

## Provenance

- Publisher: OpenDataNI / Northern Ireland Environment Agency, Water Science and Evidence Unit.
- Dataset: River Water Quality Monitoring 1990 to 2024 — All Parameters.
- ArcGIS item: `a8f8de1ad58a4ee28340f23a9be4bdad`.
- Download parameter: `format=csv&spatialRefId=29902`.
- Licence: UK Open Government Licence v3.0.
- Retrieval date: 2026-10-12; service content last modified 2026-06-23.

## Reconstruction checks

| Artifact | Expected SHA-256 | Observed SHA-256 | Status |
| --- | --- | --- | --- |
| Raw CSV | `a5ce02d9ab3703edc4279c8dc5f9d38a593b92c555945c5cdb2ab3ca55632632` | `a5ce02d9ab3703edc4279c8dc5f9d38a593b92c555945c5cdb2ab3ca55632632` | exact |
| Processed modelling CSV | `5685c2c352b1cc9502cd664736d85295580127016fb60bdca45c082c5d031761` | `5685c2c352b1cc9502cd664736d85295580127016fb60bdca45c082c5d031761` | exact |
| Cleaning audit JSON | `da6a408003ad98a23887596eecfbc329fb3c370f936a2cb63237d3bc27b0174d` | `da6a408003ad98a23887596eecfbc329fb3c370f936a2cb63237d3bc27b0174d` | exact |
| Historical grouped membership | `b42814782f7290ab73faece96634c7a65448912ea40891f3c9a714b157594229` | `b42814782f7290ab73faece96634c7a65448912ea40891f3c9a714b157594229` | exact |

Fresh execution of `prepare_water_quality_modeling_data` produced a dataframe value-equal to the restored processed file and reproduced the historical audit exactly. The historical `src/preprocessing.py` hash also matches the frozen manifest. No model code was executed.

`scripts/recover_phase2b0_data.py` makes the recovery fail-closed and repeatable: it uses the frozen download URL only when the ignored raw file is absent, verifies every SHA-256 before installation, reconstructs both processed artifacts, and refuses to overwrite a nonmatching existing file.

## Schema and cleaning

The target is `DO_mg_l_` / `dissolved_oxygen_mg_l`, measured in mg/L. Cleaning excludes 27,643 missing-target rows and 6 qualified-target rows; predictor numeric values are retained, qualifier flags are separated, predictor missing values remain for fold-local imputation, and date/month/season/cyclical fields are derived deterministically. Result: 151,031 rows, 840 sites and 32 columns.

The raw and processed files remain under ignored `data/` paths and are not proposed for Git staging.
