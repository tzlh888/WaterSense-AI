#!/usr/bin/env python3
"""Verify and visualize saved confirmation results without running predictions."""
import json
from pathlib import Path
import sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.portfolio_analysis import sha256_file
from src.weighted_regression_experiment import compute_experiment_metrics


def main():
    out=ROOT/'research_extension/ni2025_confirmation'
    summary=json.loads((out/'RESULTS.json').read_text());freeze=json.loads((out/'FREEZE.json').read_text())
    assert sha256_file(ROOT/'scripts/validate_ni2025.py')==freeze['adapter_sha256']
    assert sha256_file(ROOT/'research_extension/NI2025_CONFIRMATION_PROTOCOL.md')==freeze['protocol_sha256']
    assert sha256_file(out/'FREEZE.json')==summary['freeze_sha256']
    assert sha256_file(out/'predictions.csv.gz')==summary['prediction_sha256']
    data=pd.read_csv(out/'predictions.csv.gz');cohort=pd.read_csv(out/'eligible_cohort.csv.gz')
    assert not data.source_object_id.duplicated().any()
    assert data.source_object_id.equals(cohort.source_object_id)
    assert np.array_equal(data.actual_do_mg_l,cohort.dissolved_oxygen_mg_l)
    metrics=compute_experiment_metrics(data.actual_do_mg_l,data.predicted_do_mg_l,stations=data.station_code)
    historical=pd.read_csv(ROOT/'results/phase4_holdout_predictions.csv')
    historical_metrics=compute_experiment_metrics(historical.actual_do_mg_l,historical.predicted_do_mg_l,stations=historical.station_code)
    (out/'historical_phase4_comparison.json').write_text(json.dumps({'historical':historical_metrics,'temporal_2025':metrics},indent=2)+'\n')
    for key in ['overall_mae_mg_l','low_do_mae_mg_l','low_do_precision','low_do_recall','true_positive_count','false_positive_count','true_negative_count','false_negative_count']:
        assert np.isclose(metrics[key],summary['metrics'][key]),key
    reps=pd.read_csv(out/'bootstrap_replicates.csv.gz')
    for metric,record in summary['cluster_intervals'].items():
        valid=reps[metric].dropna()
        assert len(valid)==record['valid_replicates']
        assert np.allclose(valid.quantile([.025,.975]),[record['lower_95'],record['upper_95']])
    tp_sites=data.loc[(data.actual_do_mg_l<4)&data.predicted_low_do,'station_code'].nunique()
    errors=(data.actual_do_mg_l-data.predicted_do_mg_l).abs()
    largest=data.loc[errors.idxmax()]
    fig,axes=plt.subplots(1,2,figsize=(10,4.2))
    axes[0].bar(['Detected','Missed'],[metrics['true_positive_count'],metrics['false_negative_count']],color=['#087F8C','#C92A2A'])
    axes[0].set(ylabel='Measured low-DO observations',title='2025: 3 of 20 low-DO observations detected')
    axes[1].bar(['Overall MAE','Low-DO MAE'],[metrics['overall_mae_mg_l'],metrics['low_do_mae_mg_l']],color=['#495057','#087F8C'])
    axes[1].set(ylabel='MAE (mg/L)',title='Low mean error conceals subgroup failure')
    fig.tight_layout();fig.savefig(out/'temporal_confirmation.png',dpi=180);plt.close(fig)
    report=f'''# 2025 acquired temporal confirmation of the frozen Phase4 model

## Evidence boundary

This evaluation uses a newly acquired later period in the same NIEA monitoring
programme. It does not establish cross-region transport, future forecasting, or
confirmation of the V3 weighted selected procedure. The input mapping, model,
threshold, exclusions and interval code were frozen in commit `2a55e5a` before
the single prediction execution. The local freeze is not independent preregistration.

Official source: [DAERA/26-784](https://www.daera-ni.gov.uk/publications/daera26-784-river-water-quality-monitoring-data-all-northern-ireland-2025),
published 2026-10-26. Contains public sector information licensed under the
[OGL](https://www.daera-ni.gov.uk/articles/crown-copyright-daera); no endorsement.

## Cohort and exclusions

6,080 source rows / 503 stations. Two conflicting same-station/date/time/depth
records were excluded together under a documented pre-freeze amendment. Both
had missing target values. Of the remaining 6,078 rows, 2,588 missing targets
were excluded; no qualified target survived. Final cohort: 3,490 rows / 494
stations. No historical station/date pair overlaps the 2025 data.

493 of 494 stations appear somewhere in the historical monitoring programme.
Relative to the actual model training partition, 391 known stations supply
2,777 rows; 103 unseen training stations supply 713 rows. Thus temporal novelty
is stronger than geographic novelty. Sampler identities and coordinates are
not predictors or republished derived outputs. New temperature data are unused.

## Results and whole-station uncertainty

| Metric | Estimate | 95% station-bootstrap interval |
|---|---:|---|
| Overall MAE (mg/L) | 0.6432 | [0.5896, 0.7176] |
| Overall RMSE (mg/L) | 1.6872 | not bootstrapped in the frozen primary plan |
| R² | 0.4150 | not bootstrapped in the frozen primary plan |
| Low-DO MAE (mg/L) | 2.2888 | [1.9237, 2.6796] |
| Recall | 0.1500 | [0.0000, 0.3462] |
| Precision | 1.0000 | conditional [1,1], **not informative about unseen false alarms** |

TP=3, FP=0, TN=3470, FN=17. Low-DO prevalence is 20/3490=0.5731%.
Only nine stations contain low-DO events, below the predeclared ten-station
support criterion. This triggers insufficient support for stable rare-event
reliability claims; no cohort expansion or tuning follows the result.

All three positive predictions occur at **{tp_sites} station**. In 1,844 of
5,000 complete-station bootstrap draws no positive prediction is present, so
precision is undefined. The conditional [1,1] interval among 3,156 valid draws
is a boundary artifact of resampling an observed dataset with zero false
positives, not proof of perfect precision. Other metrics have 5,000 valid draws.

![2025 detection failure and error](temporal_confirmation.png)

Known-training-station recall is 3/15=0.20. Unseen-training-station recall is
0/5=0 and precision is undefined, with events at only two stations; this stratum
cannot support a stable geographic-transfer claim.

## Historical comparison and distribution shift

The identical saved Phase4 model had historical station-holdout MAE 0.8312,
RMSE 1.2911 and R² 0.5391. In 2025 MAE is lower while RMSE is higher and R²
lower. Different populations and measurement conditions prevent interpreting
that contrast as model improvement. V3 OOF baseline/selected results remain
development evidence and are not an external weighted/unweighted comparison.

| Same saved model, different evaluation populations | Historical holdout | 2025 |
|---|---:|---:|
| Rows | 31,341 | 3,490 |
| Low-DO observations / stations | 167 / 31 | 20 / 9 |
| Low-DO MAE (mg/L) | 3.1387 | 2.2888 |
| Recall | 0.0838 | 0.1500 |
| Precision | 0.7000 | 1.0000 (three predictions only) |
| TP / FP / TN / FN | 14 / 6 / 31168 / 153 | 3 / 0 / 3470 / 17 |

Historical values are recomputed from the preserved Phase4 prediction table.
Neither prevalence nor station support is matched; this is a descriptive
comparison, not a paired superiority experiment.

Suspended-solids missingness rises from 26.00% in historical training to 75.10%
in the 2025 cohort. BOD missingness rises from 3.49% to 8.54%; pH from 1.30%
to 8.51%. Conductivity missingness falls from 26.04% to 8.51%. Feature means,
medians and quantiles are retained without adapting the frozen imputer.

One supplied DO value is {largest.actual_do_mg_l:.1f} mg/L with prediction
{largest.predicted_do_mg_l:.3f} mg/L. Its absolute error is {errors.max():.3f}
mg/L and it materially affects RMSE. The measurement's validity is unresolved;
it remains in the primary result under the frozen no-outlier-filter rule.
No favorable post-hoc exclusion is substituted.

## Conclusion

New-period evidence reproduces the substantive failure pattern: acceptable
average absolute error coexists with missing 85% of measured low-DO rows.
The test supports the existence of this observed failure in 2025, while sparse
event-bearing stations and degenerate precision uncertainty limit reliability
claims. Cross-region external validation and independent confirmation of V3
remain outstanding.
'''
    (out/'TEMPORAL_CONFIRMATION_REPORT.md').write_text(report)
    manifest={p.name:sha256_file(p) for p in out.iterdir() if p.is_file() and p.name!='ARTIFACT_MANIFEST.json'}
    (out/'ARTIFACT_MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print('PASS: frozen hashes, identities, metrics, bootstrap intervals; report and figure generated')


if __name__=='__main__':main()
