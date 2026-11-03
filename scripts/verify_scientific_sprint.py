#!/usr/bin/env python3
"""Capture reproducible commands, complete test output, environment and preservation."""
import json
import platform
import re
import subprocess
import sys
import numpy as np
import pandas as pd
from importlib.metadata import version
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.portfolio_analysis import sha256_file


def main():
    out=ROOT/'audits/sprint'
    out.mkdir(parents=True,exist_ok=True)
    def git(*args):
        return subprocess.check_output(['git',*args],cwd=ROOT,text=True).strip()
    environment={'git_head':git('rev-parse','HEAD'),'branch':git('branch','--show-current'),
        'python':sys.version,'platform':platform.platform(),
        'packages':{p:version(p) for p in ['numpy','pandas','scikit-learn','matplotlib','joblib']},
        'source_hashes':{p:sha256_file(ROOT/p) for p in ['scripts/run_scientific_sprint.py','scripts/verify_scientific_sprint.py','scripts/run_portfolio_analysis.py']},
        'raw_data':{p:({'sha256':sha256_file(ROOT/p)} if (ROOT/p).exists() else {'status':'MISSING'})
            for p in ['data/raw/niea_river_water_quality_1990_2024.csv','data/processed/water_quality_modeling.csv']}}
    (out/'environment.json').write_text(json.dumps(environment,indent=2)+'\n')
    commands=[['scripts/run_portfolio_analysis.py'],['scripts/run_scientific_sprint.py'],
        ['-m','unittest','discover','-s','tests','-v'],
        ['-m','unittest','discover','-s','research_upgrade_v4_candidate','-p','test*.py','-v']]
    results=[]
    test_outcomes=[]
    for i,args in enumerate(commands,1):
        run=subprocess.run([sys.executable,*args],cwd=ROOT,text=True,capture_output=True)
        path=out/f'{i:02d}_execution.log'
        path.write_text(('COMMAND: python3 '+' '.join(args)+'\nEXIT: '+str(run.returncode)+'\nSTDOUT:\n'+run.stdout+'\nSTDERR:\n'+run.stderr).replace(str(ROOT),'<REPO>'))
        results.append({'args':args,'exit_code':run.returncode,'log':str(path.relative_to(ROOT))})
        for line in run.stderr.splitlines():
            match=re.match(r'^(test_\S+|setUpClass) \(([^)]+)\) \.\.\. (.*)$',line)
            if match:
                test_outcomes.append({'suite':i,'test':match[2]+'.'+match[1],'outcome':match[3]})
        print(json.dumps(results[-1]),flush=True)
    protected=['research_outputs','research_outputs_v2','research_upgrade_v3','research_upgrade_v4_candidate','results','models']
    changes=git('diff','c2ab7b4','--name-only','--',*protected)
    result={'commands':results,'historical_changes':changes.splitlines(),'historical_unchanged':not changes}
    result['test_outcomes']=test_outcomes
    # Compare every protected working file with its original Git blob; LFS model uses its SHA-256.
    files=git('ls-tree','-r','--name-only','c2ab7b4','--',*protected).splitlines()
    mismatches=[]
    for relative in files:
        if relative=='models/phase4_selected_model.joblib':
            if sha256_file(ROOT/relative)!='7434cbd29bf6a1b2b624ef3283d073212a82ec72a839d7a050bb912b8506f44f':
                mismatches.append(relative)
        else:
            original=subprocess.check_output(['git','show',f'c2ab7b4:{relative}'],cwd=ROOT)
            if (ROOT/relative).read_bytes()!=original:
                mismatches.append(relative)
    result.update(protected_files_checked=len(files),byte_mismatches=mismatches)
    result['status']='PARTIAL' if any(r['exit_code'] for r in results) else 'PASS'
    result['input_hashes']={p:sha256_file(ROOT/p) for p in [
        'research_upgrade_v3/experiment1_weighted_regression/OUTER_CV_PREDICTIONS.csv.gz',
        'research_upgrade_v4_candidate/WATERSENSE_CLASSIFIER_OOF_PREDICTIONS.csv.gz']}
    sprint=ROOT/'research_extension/sprint'
    station=pd.read_csv(sprint/'station_sampling_rates.csv')
    assert station.observations.sum()==119690 and station.low_do_events.sum()==758
    assert np.isclose(station.sampling_share.sum(),1) and np.isclose(station.event_share.sum(),1)
    assert np.allclose(station.low_do_rate,station.low_do_events/station.observations)
    reps=pd.read_csv(sprint/'cost_bootstrap_replicates.csv.gz')
    costs=pd.read_csv(sprint/'cluster_cost_differences.csv')
    for row in costs.itertuples():
        subset=reps[(reps['first']==row.first)&(reps['second']==row.second)&(reps.ratio==row.fn_fp_ratio)]
        assert len(subset)==5000
        assert np.allclose(np.quantile(subset.delta_per_10000,[.025,.975]),[row.lower_95,row.upper_95])
    null=pd.read_csv(sprint/'null_hhi_replicates.csv.gz').hhi
    reference=pd.read_csv(sprint/'sampling_null_sensitivity.csv').iloc[0]
    assert np.isclose(np.square(station.event_share).sum(),reference.observed_hhi)
    assert np.allclose(np.quantile(null,[.025,.975]),[reference.null_lower,reference.null_upper])
    result['numerical_cross_checks']='PASS: counts/rates/shares, cost replicate intervals, null HHI distribution'
    manifest={str(p.relative_to(ROOT)):sha256_file(p) for p in sorted(sprint.iterdir()) if p.is_file()}
    (out/'artifact_hashes.json').write_text(json.dumps(manifest,indent=2)+'\n')
    (out/'execution_summary.json').write_text(json.dumps(result,indent=2)+'\n')
    if mismatches or changes or any(r['exit_code'] for r in results):
        raise SystemExit(1)


if __name__=='__main__':
    main()
