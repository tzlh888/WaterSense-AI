#!/usr/bin/env python3
"""Exact source recovery and fixed historical estimator replay; no reselection."""
import json
import os
import shutil
import subprocess
import sys
import platform
from importlib.metadata import version
from pathlib import Path
from datetime import datetime, timezone

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.phase2b0_readiness import EXPECTED_RAW_SHA256, sha256_file


def main():
    out=ROOT/'audits/evidence_breakthrough'
    out.mkdir(parents=True,exist_ok=True)
    candidate=ROOT/'work/evidence_breakthrough/official_csv.csv'
    url='https://opendata.arcgis.com/api/v3/datasets/a8f8de1ad58a4ee28340f23a9be4bdad_0/downloads/data?format=csv&spatialRefId=29902'
    if not candidate.exists():
        candidate.parent.mkdir(parents=True,exist_ok=True)
        subprocess.run(['curl','--fail','--location','--silent','--show-error','--max-time','60',
            '--dump-header',str(candidate.parent/'official_csv.headers'),url,'--output',str(candidate)],check=True)
    if sha256_file(candidate)!=EXPECTED_RAW_SHA256:
        raise ValueError('Downloaded bytes do not match historical raw file')
    raw=ROOT/'data/raw/niea_river_water_quality_1990_2024.csv'
    if raw.exists() and sha256_file(raw)!=EXPECTED_RAW_SHA256:
        raise ValueError('Existing raw differs: refusing overwrite')
    if not raw.exists(): shutil.copyfile(candidate,raw)
    run=subprocess.run([sys.executable,'scripts/recover_phase2b0_data.py'],cwd=ROOT,text=True,capture_output=True)
    (out/'recovery.log').write_text(run.stdout+run.stderr)
    if run.returncode: raise RuntimeError(run.stderr)
    import pandas as pd
    import numpy as np
    from sklearn.base import clone
    from sklearn.metrics import mean_absolute_error,mean_squared_error,r2_score
    import joblib
    from src.refine import fixed_phase3_split
    data=pd.read_csv(ROOT/'data/processed/water_quality_modeling.csv')
    source=pd.read_csv(raw,low_memory=False)
    manifest={'recovered_utc':datetime.now(timezone.utc).isoformat(),
        'source_url':url,'source_bytes':candidate.stat().st_size,
        'python':sys.version,'platform':platform.platform(),
        'packages':{p:version(p) for p in ['numpy','pandas','scikit-learn','joblib']},
        'git_head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        'raw_byte_identity':True,'raw_sha256':sha256_file(raw),
        'processed_sha256':sha256_file(ROOT/'data/processed/water_quality_modeling.csv'),
        'cleaning_audit_sha256':sha256_file(ROOT/'data/processed/water_quality_modeling_audit.json'),
        'raw_rows':len(source),'raw_columns':len(source.columns),'raw_stations':source.StationCode.nunique(),
        'date_min':str(pd.to_datetime(source.Date).min().date()),'date_max':str(pd.to_datetime(source.Date).max().date()),
        'model_rows':len(data),'model_stations':data.station_code.nunique(),
        'replay':'Fixed Phase4 selected estimator only; selection searches and V3 nested grid are not rerun'}
    (out/'recovery_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    train,test=fixed_phase3_split(data)
    model_path=ROOT/'models/phase4_selected_model.joblib'
    if sha256_file(model_path)!='7434cbd29bf6a1b2b624ef3283d073212a82ec72a839d7a050bb912b8506f44f':
        raise ValueError('Frozen deployed model hash changed')
    artifact=joblib.load(model_path)
    features=artifact['feature_columns']
    model=clone(artifact['pipeline'])
    # Refit exact selected configuration. The historical holdout is descriptive only.
    print('Refitting historical Phase4 selected estimator',flush=True)
    model.fit(data.iloc[train][features],data.iloc[train].dissolved_oxygen_mg_l)
    prediction=model.predict(data.iloc[test][features])
    saved=pd.read_csv(ROOT/'results/phase4_holdout_predictions.csv')
    fresh=data.iloc[test][['source_object_id','station_code','dissolved_oxygen_mg_l']].copy()
    fresh['prediction']=prediction
    print('Historical prediction columns:',list(saved.columns),flush=True)
    merged=fresh.merge(saved,on='source_object_id',validate='one_to_one',suffixes=('_fresh','_saved'))
    reference=merged.predicted_do_mg_l.to_numpy()
    actual=fresh.dissolved_oxygen_mg_l.to_numpy()
    manifest['fixed_model_replay']={'training_rows':len(train),'test_rows':len(test),
        'mae':mean_absolute_error(actual,prediction),'rmse':float(np.sqrt(mean_squared_error(actual,prediction))),
        'r2':r2_score(actual,prediction),'max_prediction_difference':float(np.max(np.abs(merged.prediction-reference))),
        'predictions_match_at_1e_10':bool(np.allclose(merged.prediction,reference,rtol=0,atol=1e-10)),
        'parameters':model.named_steps['model'].get_params()}
    replay=ROOT/'research_runs/evidence_breakthrough'
    replay.mkdir(parents=True,exist_ok=True)
    fresh.to_csv(replay/'fixed_phase4_predictions.csv.gz',index=False,compression={'method':'gzip','mtime':0})
    manifest['replay_prediction_sha256']=sha256_file(replay/'fixed_phase4_predictions.csv.gz')
    (out/'recovery_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps(manifest,indent=2),flush=True)


if __name__=='__main__':main()
