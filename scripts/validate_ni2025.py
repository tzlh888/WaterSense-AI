#!/usr/bin/env python3
"""Freeze then evaluate one previously acquired, outcome-unseen 2025 cohort."""
import argparse
from datetime import datetime,timezone
import json
from pathlib import Path
import subprocess
import sys

import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.preprocessing import prepare_water_quality_modeling_data, WATER_QUALITY_FEATURE_SETS
from src.portfolio_analysis import sha256_file
from src.weighted_regression_experiment import compute_experiment_metrics
from scripts.run_scientific_sprint import station_stats,bootstrap_weights,interval

OUT=ROOT/'research_extension/ni2025_confirmation'
RAW=ROOT/'work/evidence_breakthrough/ni2025_raw.csv'
MODEL=ROOT/'models/phase4_selected_model.joblib'
PROTOCOL=ROOT/'research_extension/NI2025_CONFIRMATION_PROTOCOL.md'
RAW_SHA='9e8713d94835f1bdb9c71f9d5bb36cfc944ed925b206d09aa18216482aa75c7a'
MODEL_SHA='7434cbd29bf6a1b2b624ef3283d073212a82ec72a839d7a050bb912b8506f44f'
MAPPING={'ALK (mg/l)':'ALK_mg_l_','BOD (mg/l)':'BOD_mg_l_',
    'COND (US/CM)':'COND_US_CM_','DO (mg/l)':'DO_mg_l_',
    'NH4-N (mg/l)':'NH4_N_mg_l_','NO2-N (mg/l)':'NO2_N_mg_l_',
    'NO3-N (mg/l)':'NO3_N_mg_l_','P(SOL) (mg/l)':'P_SOL__mg_l_',
    'PH (PH UNITS)':'PH_PHUNITS_','SS (mg/l)':'SS_mg_l_'}
QUALIFIERS={'ALK_mg_l_':'Q_Alk','BOD_mg_l_':'Q_BOD','COND_US_CM_':'Q_COND',
    'DO_mg_l_':'Q_DO','NH4_N_mg_l_':'Q_NH4N','NO2_N_mg_l_':'Q_NO2N',
    'NO3_N_mg_l_':'Q_NO3N','P_SOL__mg_l_':'Q_PSOL','PH_PHUNITS_':'Q_pH','SS_mg_l_':'Q_SS'}


def clean_json(value):
    if isinstance(value,dict):return {k:clean_json(v) for k,v in value.items()}
    if isinstance(value,list):return [clean_json(v) for v in value]
    if isinstance(value,(float,np.floating)) and not np.isfinite(value):return None
    if isinstance(value,np.generic):return value.item()
    return value


def write_json(path,value):path.write_text(json.dumps(clean_json(value),indent=2,allow_nan=False)+'\n')


def adapt(source):
    dates=pd.to_datetime(source.Date,format='%d/%m/%Y',errors='raise')
    if not dates.dt.year.eq(2025).all():raise ValueError('Not a 2025-only source')
    station='UKGBNIF'+pd.to_numeric(source['Station Code'],errors='raise').astype(int).astype(str)
    time=source.Time.astype(int).astype(str).str.zfill(4)
    pd.to_datetime(time,format='%H%M',errors='raise')
    identities=pd.DataFrame({'station':station,'date':dates.dt.strftime('%Y-%m-%d'),'time':time,'depth':source.Depth})
    duplicate=identities.duplicated(keep=False)
    converted=pd.DataFrame({'OBJECTID':np.arange(1,len(source)+1),'StationCode':station,
        'Date':dates.dt.strftime('%Y/%m/%d')})
    invalid=duplicate.copy()
    reasons={}
    for field,old in MAPPING.items():
        position=source.columns.get_loc(field)
        qname=source.columns[position-1]
        if not qname.startswith('Q'):raise ValueError('Qualifier must precede measurement')
        q=source[qname].fillna('').astype(str).str.strip()
        unknown=~q.isin(['','<','>'])
        values=pd.to_numeric(source[field],errors='raise')
        nonfinite=values.notna() & ~np.isfinite(values)
        invalid|=unknown|nonfinite
        if old in ['PH_PHUNITS_','COND_US_CM_']:invalid|=q.ne('')
        converted[old]=values
        converted[QUALIFIERS[old]]=q.replace('',np.nan)
        reasons[field]={'unsupported_qualifiers':int(unknown.sum()),'nonfinite':int(nonfinite.sum()),
            'missing':int(values.isna().sum()),'qualified':int(q.ne('').sum())}
    valid=converted.loc[~invalid].copy()
    processed,audit=prepare_water_quality_modeling_data(valid)
    return processed,identities,{'schema_rows':len(source),'excluded_identity_conflict_rows':int(duplicate.sum()),
        'invalid_predictor_qualifier_or_identity_rows':int(invalid.sum()),
        'field_checks':reasons,'cleaning':audit}


def prepare():
    if sha256_file(RAW)!=RAW_SHA or sha256_file(MODEL)!=MODEL_SHA:raise ValueError('Raw/model hash mismatch')
    source=pd.read_csv(RAW,encoding='cp1252')
    data,identities,audit=adapt(source)
    historical=pd.read_csv(ROOT/'data/raw/niea_river_water_quality_1990_2024.csv',low_memory=False)
    old_dates=pd.to_datetime(historical.Date,format='%Y/%m/%d')
    if not (old_dates.max()<pd.Timestamp('2025-01-01')):raise ValueError('Historical data extend into confirmation year')
    old_keys=set(zip(historical.StationCode,old_dates.dt.strftime('%Y-%m-%d')))
    overlaps=sum((r.station,r.date) in old_keys for r in identities.itertuples())
    if overlaps:raise ValueError('Historical station/date overlap')
    OUT.mkdir(parents=True,exist_ok=True)
    data.to_csv(OUT/'eligible_cohort.csv.gz',index=False,compression={'method':'gzip','mtime':0})
    audit.update({'old_new_station_date_overlap':overlaps,'historical_station_overlap':len(set(data.station_code)&set(historical.StationCode)),
        'eligible_rows':len(data),'eligible_stations':data.station_code.nunique(),
        'data_scope':'Same-programme later-period acquired confirmation; not independent region',
        'new_temperature_feature_used':False})
    write_json(OUT/'compatibility_audit.json',audit)
    return data


def freeze():
    if (OUT/'FREEZE.json').exists():raise ValueError('Freeze exists: refusing overwrite')
    data=prepare()
    record={'frozen_utc':datetime.now(timezone.utc).isoformat(),'git_head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        'raw_sha256':RAW_SHA,'model_sha256':MODEL_SHA,'protocol_sha256':sha256_file(PROTOCOL),
        'adapter_sha256':sha256_file(Path(__file__)),'preprocessing_sha256':sha256_file(ROOT/'src/preprocessing.py'),
        'cohort_sha256':sha256_file(OUT/'eligible_cohort.csv.gz'),
        'mapping':MAPPING,'feature_order':WATER_QUALITY_FEATURE_SETS['D_extended_plus_temporal'],
        'threshold':4,'bootstrap_seed':20261103,'bootstrap_draws':5000,
        'external_predictions_seen':False,'authority':'Current user request subject to passed data/overlap and code gates; no human signature invented',
        'eligible_rows':len(data),'eligible_stations':data.station_code.nunique()}
    write_json(OUT/'FREEZE.json',record)
    print(json.dumps(record,indent=2))


def evaluate():
    if (OUT/'RESULTS.json').exists():raise ValueError('Results exist: refusing repeated evaluation')
    f=json.loads((OUT/'FREEZE.json').read_text())
    for path,key in [(RAW,'raw_sha256'),(MODEL,'model_sha256'),(PROTOCOL,'protocol_sha256'),
        (Path(__file__),'adapter_sha256'),(ROOT/'src/preprocessing.py','preprocessing_sha256'),
        (OUT/'eligible_cohort.csv.gz','cohort_sha256')]:
        if sha256_file(path)!=f[key]:raise ValueError(f'Frozen input changed: {key}')
    data=pd.read_csv(OUT/'eligible_cohort.csv.gz')
    import joblib
    from src.refine import fixed_phase3_split
    artifact=joblib.load(MODEL)
    if artifact['feature_columns']!=f['feature_order']:raise ValueError('Frozen feature order mismatch')
    predictions=artifact['pipeline'].predict(data[f['feature_order']])
    result=data[['source_object_id','station_code','sample_date','dissolved_oxygen_mg_l']].rename(columns={'dissolved_oxygen_mg_l':'actual_do_mg_l'})
    result['predicted_do_mg_l']=predictions;result['predicted_low_do']=predictions<4
    result.to_csv(OUT/'predictions.csv.gz',index=False,compression={'method':'gzip','mtime':0})
    metric=compute_experiment_metrics(result.actual_do_mg_l,predictions,stations=result.station_code)
    stats=station_stats(result)
    totals=bootstrap_weights(len(stats),draws=f['bootstrap_draws'],seed=f['bootstrap_seed'])@stats.to_numpy(dtype=float)
    columns=list(stats.columns);vectors={c:totals[:,i] for i,c in enumerate(columns)}
    with np.errstate(divide='ignore',invalid='ignore'):
        draws={'overall_mae':vectors['ae']/vectors['n'],'low_do_mae':vectors['low_ae']/vectors['low'],
            'recall':vectors['tp']/vectors['low'],'precision':vectors['tp']/(vectors['tp']+vectors['fp'])}
    intervals={m:interval(v) for m,v in draws.items()}
    pd.DataFrame(draws).to_csv(OUT/'bootstrap_replicates.csv.gz',index=False,compression={'method':'gzip','mtime':0})
    history=pd.read_csv(ROOT/'data/processed/water_quality_modeling.csv');train,_=fixed_phase3_split(history)
    historical_training=history.iloc[train];train_stations=set(historical_training.station_code)
    strata={}
    for label,mask in [('known_training_stations',result.station_code.isin(train_stations)),
        ('unseen_training_stations',~result.station_code.isin(train_stations))]:
        subset=result.loc[mask]
        strata[label]=compute_experiment_metrics(subset.actual_do_mg_l,subset.predicted_do_mg_l,stations=subset.station_code) if len(subset) else {'rows':0}
    shift=[]
    for feature in f['feature_order']:
        old=historical_training[feature];new=data[feature]
        shift.append({'feature':feature,'train_missing_fraction':old.isna().mean(),'external_missing_fraction':new.isna().mean(),
            'train_mean':old.mean(),'external_mean':new.mean(),'train_median':old.median(),'external_median':new.median(),
            'train_q05':old.quantile(.05),'external_q05':new.quantile(.05),'train_q95':old.quantile(.95),'external_q95':new.quantile(.95)})
    pd.DataFrame(shift).to_csv(OUT/'feature_distribution_shift.csv',index=False)
    low_sites=result.loc[result.actual_do_mg_l<4].station_code.nunique()
    summary={'evidence_class':'Acquired later-period same-programme confirmation of frozen Phase4 estimator',
        'freeze_sha256':sha256_file(OUT/'FREEZE.json'),'metrics':metric,'cluster_intervals':intervals,
        'low_do_stations':low_sites,'insufficient_rare_event_station_support':low_sites<10,
        'strata':strata,'training_performed':False,'model_changed':False,
        'prediction_sha256':sha256_file(OUT/'predictions.csv.gz')}
    write_json(OUT/'RESULTS.json',summary)
    print(json.dumps(clean_json(summary),indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['freeze','evaluate']);args=p.parse_args()
    freeze() if args.action=='freeze' else evaluate()
