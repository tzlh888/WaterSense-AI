# WaterSense external-validation feasibility

**Status: BLOCKED — External Validation: NOT AVAILABLE.** Assessment date: 2026-10-14.

The official OpenDataNI/NIEA ArcGIS service describes 178,680 rows dated 1990-01-02 through 2024-12-11, with zero rows after 2024-12-31. The current official CSV was downloaded once from the documented ArcGIS Hub endpoint. Its SHA-256 is `a5ce02d9ab3703edc4279c8dc5f9d38a593b92c555945c5cdb2ab3ca55632632` and it is byte-for-byte identical to the preserved historical raw export (also `a5ce02d9ab3703edc4279c8dc5f9d38a593b92c555945c5cdb2ab3ca55632632`). It therefore has complete record overlap and cannot be called a new time period, external region, or independent confirmation set.

Source: OpenDataNI/NIEA, UK Open Government Licence v3.0. Catalogue: <https://www.data.gov.uk/dataset/15ec8080-ee1c-469b-858e-546d2fb57c27/riverwaterqualitymonitoring-1990to2024-allparameters13>. Service: <https://services-eu1.arcgis.com/kswen6BYexuc1SUk/arcgis/rest/services/River_Water_Quality_Monitoring_1990_to_2024_All_Parameters/FeatureServer/0>. Export URL is recorded in `external_validation.py`.

Because independence fails before model access, no external predictions or metrics were computed. A future candidate must pass the frozen license, provenance, overlap, units/method, target-validity, feature-coverage, and model-freeze gates in `EXPERIMENT_PROTOCOL.md`.
