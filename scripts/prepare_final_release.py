#!/usr/bin/env python3
"""Post-hoc diagnostic on saved predictions and a bounded local chronology audit."""
import hashlib
import json
from datetime import datetime,timezone
from pathlib import Path
import subprocess
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

OUT=ROOT/'audits/final_release'
EXT=ROOT/'research_extension/final_release'
PRIMARY=ROOT/'research_extension/ni2025_confirmation'
FREEZE_COMMIT='2a55e5a7d4ff608f34695ef19bf9c1f8c9aa8d63'


def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT)


def utc(seconds):return datetime.fromtimestamp(seconds,timezone.utc).isoformat()


def sensitivity(data):
    marked=data.actual_do_mg_l.eq(94)
    if marked.sum()!=1:raise ValueError('Expected exactly one designated post-hoc 94 mg/L row')
    rows=[]
    for label,frame in [('FROZEN_PRIMARY',data),('POST_HOC_OMIT_SINGLE_94_ROW',data.loc[~marked])]:
        values=compute_experiment_metrics(frame.actual_do_mg_l,frame.predicted_do_mg_l,stations=frame.station_code)
        rows.append({'analysis':label,**values})
    return rows


def main():
    OUT.mkdir(parents=True,exist_ok=True);EXT.mkdir(parents=True,exist_ok=True)
    baseline_hashes={p.name:sha256_file(p) for p in PRIMARY.iterdir() if p.is_file()}
    data=pd.read_csv(PRIMARY/'predictions.csv.gz')
    rows=sensitivity(data)
    pd.DataFrame(rows).to_csv(EXT/'outlier_sensitivity.csv',index=False)
    marked=data.loc[data.actual_do_mg_l.eq(94)].iloc[0]
    original=ROOT/'work/evidence_breakthrough/ni2025_raw.csv'
    assert sha256_file(original)=='9e8713d94835f1bdb9c71f9d5bb36cfc944ed925b206d09aa18216482aa75c7a'
    source=pd.read_csv(original,encoding='cp1252')
    row=source.iloc[int(marked.source_object_id)-1]
    assert row['DO (mg/l)']==94 and 'UKGBNIF'+str(int(row['Station Code']))==marked.station_code
    subset=source.loc[source['Station Code'].eq(row['Station Code']),['Date','DO (mg/l)','DO % (SATN)','TEMP (°C)']]
    subset.to_csv(EXT/'flagged_station_context.csv',index=False)
    one_error=float(abs(marked.actual_do_mg_l-marked.predicted_do_mg_l))
    audit={'analysis_class':'POST_HOC_SENSITIVITY_NOT_REPLACEMENT','source_object_id':int(marked.source_object_id),
        'source_csv_line_including_header':int(marked.source_object_id)+1,'station_code':marked.station_code,
        'sample_date':marked.sample_date,'source_do_mg_l':94,'source_do_saturation_percent':float(row['DO % (SATN)']),
        'source_water_temperature_c':float(row['TEMP (°C)']),
        'preceding_target_qualifier':None if pd.isna(source.iloc[int(marked.source_object_id)-1,25]) else str(source.iloc[int(marked.source_object_id)-1,25]),
        'prediction_mg_l':float(marked.predicted_do_mg_l),'absolute_error':one_error,
        'share_of_total_squared_error':one_error**2/rows[0]['sum_squared_error'],
        'other_nonmissing_station_do_range':[float(v) for v in subset.loc[subset['DO (mg/l)'].ne(94),'DO (mg/l)'].agg(['min','max'])],
        'interpretation':'Source contains an internally suspicious DO/saturation pair. No verified correction is available; no replacement value is proposed.',
        'primary_files_unchanged':baseline_hashes=={p.name:sha256_file(p) for p in PRIMARY.iterdir() if p.is_file()}}
    (OUT/'outlier_source_audit.json').write_text(json.dumps(audit,indent=2)+'\n')
    (OUT/'primary_artifact_hashes.json').write_text(json.dumps(baseline_hashes,indent=2)+'\n')
    freeze=json.loads((PRIMARY/'FREEZE.json').read_text())
    frozen_paths={'adapter_sha256':'scripts/validate_ni2025.py','protocol_sha256':'research_extension/NI2025_CONFIRMATION_PROTOCOL.md',
        'preprocessing_sha256':'src/preprocessing.py','cohort_sha256':'research_extension/ni2025_confirmation/eligible_cohort.csv.gz'}
    verified=[]
    for key,path in frozen_paths.items():
        blob=git('show',f'{FREEZE_COMMIT}:{path}')
        digest=hashlib.sha256(blob).hexdigest()
        assert digest==freeze[key]==sha256_file(ROOT/path)
        verified.append({'path':path,'sha256':digest,'matches_freeze_commit_and_working_copy':True})
    assert git('show',f'{FREEZE_COMMIT}:research_extension/ni2025_confirmation/FREEZE.json')==(PRIMARY/'FREEZE.json').read_bytes()
    paths=git('ls-tree','-r','--name-only',FREEZE_COMMIT).decode().splitlines()
    absent=[p for p in ['research_extension/ni2025_confirmation/RESULTS.json','research_extension/ni2025_confirmation/predictions.csv.gz'] if p not in paths]
    metadata={}
    for name in ['FREEZE.json','predictions.csv.gz','RESULTS.json']:
        stat=(PRIMARY/name).stat()
        metadata[name]={'mtime_utc':utc(stat.st_mtime),'birthtime_utc':utc(stat.st_birthtime) if hasattr(stat,'st_birthtime') else None}
    stat=(ROOT/'audits/evidence_breakthrough/ni2025_evaluation.log').stat()
    metadata['execution_log']={'mtime_utc':utc(stat.st_mtime),'birthtime_utc':utc(stat.st_birthtime) if hasattr(stat,'st_birthtime') else None}
    chronology={'classification':'LOCAL_RECORDS_CONSISTENT_WITH_FREEZE_BEFORE_EXECUTION_NOT_INDEPENDENT_PROOF',
        'freeze_commit':FREEZE_COMMIT,'freeze_file_recorded_utc':freeze['frozen_utc'],
        'commit_metadata':git('show','-s','--format=%H%n%P%n%aI%n%cI%n%G?',FREEZE_COMMIT).decode().splitlines(),
        'git_reflog':git('reflog','show','--date=iso-strict','--format=%H %gD %gs').decode().splitlines(),
        'verified_inputs':verified,'prediction_and_result_absent_at_freeze_commit':absent,'local_filesystem_metadata':metadata,
        'execution_log_sha256':sha256_file(ROOT/'audits/evidence_breakthrough/ni2025_evaluation.log'),
        'evidence_limit':'Git and filesystem clocks are locally mutable; commit is unsigned, execution log has no UTC start timestamp. These records cannot prove no earlier unrecorded prediction or substitute for third-party preregistration.'}
    (OUT/'freeze_chronology.json').write_text(json.dumps(chronology,indent=2)+'\n')
    (OUT/'freeze_commit.txt').write_bytes(git('show','--format=fuller','--stat',FREEZE_COMMIT))
    fig,axes=plt.subplots(1,2,figsize=(9,4))
    for ax,key,title in [(axes[0],'overall_mae_mg_l','Overall MAE'),(axes[1],'overall_rmse_mg_l','Overall RMSE')]:
        ax.bar(['Frozen primary','Post-hoc omit 94'],[r[key] for r in rows],color=['#495057','#E67700'])
        ax.set_title(title);ax.set_ylabel('mg/L')
    fig.suptitle('Diagnostic sensitivity only: primary result retained')
    fig.tight_layout();fig.savefig(EXT/'outlier_sensitivity.png',dpi=180);plt.close(fig)
    r0,r1=rows
    report=f'''# DO=94 mg/L: post-hoc diagnostic sensitivity

The single record was flagged after inspecting 2025 outcomes. This analysis is
post hoc, is not confirmation, and does not change any frozen result or model.
Only saved predictions are read; no prediction, fitting or tuning occurs.

Source row ID {int(marked.source_object_id)} (CSV line {int(marked.source_object_id)+1}),
station {marked.station_code}, {marked.sample_date}, contains DO=94 mg/L,
saturation=10%, temperature=18 C, with no target qualifier. Other nonmissing
2025 DO values at this station span 8.6–13.4 mg/L. The combination is internally
suspicious and could reflect a transcription/column/decimal problem; neither a
specific mechanism nor a correct replacement value is verified.

| Analysis | n | MAE mg/L | RMSE mg/L | R² | Low-DO MAE | Recall | TP/FP/TN/FN |
|---|---:|---:|---:|---:|---:|---:|---|
| Frozen primary | 3490 | {r0['overall_mae_mg_l']:.6f} | {r0['overall_rmse_mg_l']:.6f} | {r0['overall_r2']:.6f} | {r0['low_do_mae_mg_l']:.6f} | 0.15 | 3/0/3470/17 |
| Post-hoc omit flagged row | 3489 | {r1['overall_mae_mg_l']:.6f} | {r1['overall_rmse_mg_l']:.6f} | {r1['overall_r2']:.6f} | {r1['low_do_mae_mg_l']:.6f} | 0.15 | 3/0/3469/17 |

The flagged row supplies {audit['share_of_total_squared_error']:.2%} of total
squared error. Removing it changes target variance as well as squared error,
so the R² change must not be read as pure estimator improvement. The 17/20
low-DO misses are unchanged. This diagnostic does not resolve selection from
missing targets or create additional rare-event stations.

![Primary and diagnostic sensitivity](outlier_sensitivity.png)

All primary 2025 files are checked against their existing hashes. No corrected
DO value or preferred alternative metric replaces the frozen main result.
'''
    (EXT/'POST_HOC_SENSITIVITY.md').write_text(report)
    print(json.dumps({'sensitivity':[{k:r[k] for k in ['analysis','overall_mae_mg_l','overall_rmse_mg_l','overall_r2']} for r in rows],
        'primary_unchanged':audit['primary_files_unchanged'],'chronology':chronology['classification']},indent=2))


if __name__=='__main__':main()
