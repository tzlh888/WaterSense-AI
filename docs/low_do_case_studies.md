# Low dissolved-oxygen case studies

These cases come from the untouched station-grouped Phase 4 holdout. “Low DO” means the lowest 10% of held-out target values (`actual DO ≤ 8.1 mg/L`); it is a data-derived error-analysis range, not an ecological or regulatory class.

The selected model's lowest-decile MAE is 1.812 mg/L. It overpredicts 89.964% of this group, showing that regression toward the middle remains even after refinement.

## Large low-DO overpredictions

| Station | Date | Actual DO | Predicted DO | Absolute error | Selected observed context |
|---|---|---:|---:|---:|---|
| `UKGBNIF10533` | 2015-02-26 | 2.5 | 12.107 | 9.607 | BOD 2.7, nitrite 0.014, phosphorus 0.09, pH 7.8, alkalinity 66, conductivity 254, suspended solids 6; ammonia and nitrate missing; no displayed `<` flags |
| `UKGBNIF10543` | 1994-10-21 | 6.8 | 14.672 | 7.872 | BOD 2.0, ammonia 0.06, nitrite 0.02, nitrate 2.8, phosphorus 1.2, pH 7.96, alkalinity 104, conductivity 365, suspended solids 2; no displayed `<` flags |
| `UKGBNIF10336` | 2010-11-17 | 2.5 | 9.261 | 6.761 | BOD 3.1, ammonia 0.32, nitrite 0.032, nitrate 1.65, phosphorus 0.07, pH 7.6, alkalinity 175, conductivity 464, suspended solids 17; no displayed `<` flags |
| `UKGBNIF10575` | 2000-06-07 | 2.6 | 9.327 | 6.727 | BOD 5.0, ammonia 1.2, pH 8.0 and alkalinity 186; nitrite, nitrate, phosphorus, conductivity and suspended solids missing; no displayed `<` flags |
| `UKGBNIF10519` | 1995-02-27 | 6.4 | 13.044 | 6.644 | BOD 3.0, ammonia 0.52, nitrite 0.03, nitrate 4.4, phosphorus 0.31, pH 7.87, alkalinity 115, conductivity 411, suspended solids 97; no displayed `<` flags |

Units are mg/L except conductivity (µS/cm) and pH (pH units).

## Observable patterns and limits

The cases occur at different stations, dates and seasons. Four have nearly complete extended chemistry, while one has several missing measurements. Qualifier censoring is not a shared explanation: none of the first five cases has a displayed below-limit flag. Some chemistry values differ substantially across the cases, so no single observed predictor pattern explains all failures.

In the complete lowest-decile subset, pH, alkalinity and conductivity are missing somewhat more often than in the overall holdout, but other variables are similar and suspended solids is missing less often. This descriptive comparison does not show that missingness causes the errors.

The dataset lacks water temperature, flow, sampling-condition detail and a documented explanation for unusual records. Those omissions prevent a confident scientific explanation for these individual low-DO measurements or predictions. The correct conclusion is that the model often cannot recognise extreme low DO from the available contemporaneous inputs—not that any particular unobserved mechanism caused these errors.
