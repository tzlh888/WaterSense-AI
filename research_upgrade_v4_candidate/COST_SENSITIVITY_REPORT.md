# WaterSense decision-cost sensitivity

**Status: NEW ANALYSIS — EXPLORATORY / DEVELOPMENT-ONLY.**

The analysis applies `Cost = C_FN × FN + C_FP × FP` to the same 119,690 frozen outer-OOF development observations. `C_FP` is fixed at 1 and `C_FN` is varied. The values are hypothetical scenario weights, not observed ecological, public-health, or regulatory costs.

| FN:FP | Minimum-cost model(s) |
| --- | --- |
| 10:1 | historical_v3_selected_procedure |
| 1:1 | historical_fixed_regression_baseline |
| 25:1 | dedicated_logistic_classifier |
| 2:1 | historical_v3_selected_procedure |
| 50:1 | dedicated_logistic_classifier |
| 5:1 | historical_v3_selected_procedure |

The conclusion is conditional: changing the assumed consequence ratio changes the preferred decision rule. The CSV retains every model/scenario result, including ties, and the figure visualizes the complete set specified in the saved V4 development protocol. These are hypothetical assumptions, not measured regulatory or economic losses. No scenario was selected after results as the single 'correct' cost.
