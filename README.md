# WaterSense AI

Can a model estimate dissolved oxygen in rivers at monitoring stations it has never seen? I tested this on 151,031 measurements from 840 stations in Northern Ireland (1990–2024). Each station was used either for training or for testing, never both.

Low-oxygen readings (below 4 mg/L) are rare. A baseline model found only 13% of them. A tuned version found 36%, but overall error rose from 0.88 to 0.95 mg/L and false alarms rose from 26 to 219. On new 2025 data, an earlier model missed 17 of 20 low-oxygen readings.

My research decisions: group validation by station, keep the unfavorable results, and stop where the evidence ended. [待本人确认：C2 —— 用你自己的话改写这一句]

Limitations and full disclosure: see [LIMITATIONS.md](LIMITATIONS.md).

My own reproduction: [待本人完成后补充：R1 —— 链接到 my_reproduction/]

## Results at a glance

Main experiment: 119,690 observations from 672 stations, five folds, every station entirely in training or entirely in testing.

| Metric | Baseline | Tuned procedure |
|---|---|---|
| Overall MAE (mg/L) | 0.8797 | 0.9516 |
| Low-DO MAE (mg/L) | 3.3235 | 2.3613 |
| Low-DO recall | 0.1293 | 0.3641 |
| Low-DO precision | 0.7903 | 0.5576 |
| Missed low-DO readings | 660 | 482 |
| False alarms | 26 | 219 |

The comparison is between two whole procedures, so it does not show that sample weighting alone caused the difference.

## Run the app

```bash
pip install -r requirements.txt
streamlit run app/app.py
```

The app uses the earlier deployed model, not the tuned procedure above. It is a research demo, not a tool for warnings.

## More detail

- [Detailed evidence guide](docs/DETAILED_EVIDENCE_GUIDE.md) — protocols, reports and how to rerun the analysis
- [Research manuscript](paper/WATERSENSE_AI_MANUSCRIPT.md)

Public environmental data keep their source terms: [data attribution and reuse](docs/DATA_REUSE_AND_RELEASE.md).

## How this was built

[待本人确认：C3 —— I defined the question and validation rules; AI tools did much of the implementation, analysis and writing under my direction.]
