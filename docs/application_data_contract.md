# Application data contract

This document defines how the Streamlit interface translates public inputs into the exact 25-feature contract stored in `models/phase4_selected_model.joblib`. The application loads the complete fitted preprocessing/model pipeline and does not recreate or retrain it.

## Measurement inputs

All measurement fields are optional because the trained pipeline supports missing values. “Measurement unavailable” is represented as `NaN`, never zero. Numeric imputation and missingness indicators are applied by the fitted pipeline using values learned from the Phase 4 training stations.

| User input | Model feature(s) | Unit | Optional | Missing-value behaviour | Censoring behaviour | Transformation |
|---|---|---|---|---|---|---|
| Biochemical oxygen demand | `bod_mg_l`; `bod_is_below_limit`; `bod_is_above_limit` | mg/L | Yes | Numeric value becomes `NaN`; qualifier flags remain 0 | Exact, `<`, and `>` options; reported numeric limit is preserved | Pipeline median imputation, missingness indicator and scaling for numeric value; flags pass through |
| Ammonia as nitrogen | `ammonia_n_mg_l`; `ammonia_is_below_limit`; `ammonia_is_above_limit` | mg/L | Yes | Same as above | Exact, `<`, and `>` options | Same as above |
| Nitrite as nitrogen | `nitrite_n_mg_l`; `nitrite_is_below_limit`; `nitrite_is_above_limit` | mg/L | Yes | Same as above | Exact or `<`; the `>` flag remains 0 because no `>` observations occurred in the inspected source | Same as above |
| Nitrate as nitrogen | `nitrate_n_mg_l`; `nitrate_is_below_limit`; `nitrate_is_above_limit` | mg/L | Yes | Same as above | Exact or `<`; the `>` flag remains 0 | Same as above |
| Soluble reactive phosphorus | `soluble_reactive_phosphorus_mg_l`; `phosphorus_is_below_limit`; `phosphorus_is_above_limit` | mg/L | Yes | Same as above | Exact, `<`, and `>` options | Same as above |
| pH | `ph` | pH units | Yes | Numeric value becomes `NaN` | No qualifier was present in the source export | Pipeline median imputation, missingness indicator and scaling |
| Alkalinity | `alkalinity_mg_l`; `alkalinity_is_below_limit`; `alkalinity_is_above_limit` | mg/L | Yes | Numeric value becomes `NaN`; flags remain 0 | Exact or `<`; the `>` flag remains 0 | Numeric preprocessing plus flag pass-through |
| Conductivity | `conductivity_us_cm` | µS/cm | Yes | Numeric value becomes `NaN` | Source qualifier column was empty | Pipeline median imputation, missingness indicator and scaling |
| Suspended solids | `suspended_solids_mg_l`; `suspended_solids_is_below_limit`; `suspended_solids_is_above_limit` | mg/L | Yes | Numeric value becomes `NaN`; flags remain 0 | Exact or `<`; the `>` flag remains 0 | Numeric preprocessing plus flag pass-through |

The interface never performs half-reporting-limit substitution. A value such as `<0.04` is represented by numeric value `0.04` plus the appropriate below-limit flag. This does not claim that the true concentration equals `0.04`.

## Sampling date

| User input | Model features | Unit | Required | Transformation |
|---|---|---|---|---|
| Sampling date | `day_of_year_sin`; `day_of_year_cos` | unitless cyclical coordinates | Yes | `sin(2π × day_of_year / 365.25)` and `cos(2π × day_of_year / 365.25)` |

The exact formula matches `prepare_water_quality_modeling_data` in `src/preprocessing.py`. Users never enter sine or cosine values directly. Date context describes the same sampling event; it does not make the prediction a future forecast.

## Saved-artifact feature order

The application obtains feature order from the artifact's `feature_columns` metadata. The verified order is:

1. `bod_mg_l`
2. `ammonia_n_mg_l`
3. `nitrite_n_mg_l`
4. `nitrate_n_mg_l`
5. `soluble_reactive_phosphorus_mg_l`
6. `ph`
7. `bod_is_below_limit`
8. `bod_is_above_limit`
9. `ammonia_is_below_limit`
10. `ammonia_is_above_limit`
11. `nitrite_is_below_limit`
12. `nitrite_is_above_limit`
13. `nitrate_is_below_limit`
14. `nitrate_is_above_limit`
15. `phosphorus_is_below_limit`
16. `phosphorus_is_above_limit`
17. `alkalinity_mg_l`
18. `conductivity_us_cm`
19. `suspended_solids_mg_l`
20. `alkalinity_is_below_limit`
21. `alkalinity_is_above_limit`
22. `suspended_solids_is_below_limit`
23. `suspended_solids_is_above_limit`
24. `day_of_year_sin`
25. `day_of_year_cos`

`dissolved_oxygen_mg_l`, `Q_DO`, station identifiers, location names and coordinates must never enter prediction input.

## Validation and range behaviour

- Non-finite numeric inputs are rejected.
- Negative concentrations/conductivity are rejected as mathematically invalid for this interface; no environmental safety range is inferred.
- pH is restricted to the mathematical 0–14 scale.
- Values outside the minimum/maximum observed among the 672 training stations are allowed but receive an extrapolation warning.
- Training-relative percentile positions are descriptive only and must not be labelled as risk.

## Output contract

The fitted pipeline returns one finite dissolved-oxygen estimate in mg/L. The interface displays it with:

- station-grouped holdout MAE 0.831 mg/L;
- group-CV MAE 0.880 ± 0.035 mg/L;
- empirical group-CV absolute-error percentiles; and
- warnings about missing inputs, extrapolation and weaker performance at observed DO extremes.

These validation statistics are population-level empirical summaries, not individual confidence intervals, safety limits or regulatory classifications.
