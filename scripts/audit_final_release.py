#!/usr/bin/env python3
"""Final local release checks: no fitting, inference, tuning or remote mutation."""
import concurrent.futures
from datetime import datetime, timezone
import hashlib
from importlib.metadata import version
import json
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
import urllib.parse

import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.portfolio_analysis import sha256_file
from src.weighted_regression_experiment import compute_experiment_metrics

OUT=ROOT/'audits/final_release'
BASELINE=ROOT/'work/evidence_baseline_c2ab7b4'
SOURCE='https://www.daera-ni.gov.uk/sites/default/files/2026-10/DAERA%2026-784%20-%20Annex%20A.CSV'
LICENSE='https://www.daera-ni.gov.uk/articles/crown-copyright-daera'
DOCS=['README.md','paper/WATERSENSE_AI_MANUSCRIPT.md','admissions/ECOLE_POLYTECHNIQUE.md',
      'admissions/PSL_IBSAI.md','admissions/TECHNICAL_INTERVIEW_QA.md',
      'admissions/RESEARCH_SUMMARY.md','admissions/OWNER_CONTRIBUTION_CONFIRMATION.md',
      'audits/final_release/FREEZE_CHRONOLOGY.md','audits/final_release/DRAFT_PR.md',
      'research_extension/final_release/POST_HOC_SENSITIVITY.md',
      'docs/DATA_REUSE_AND_RELEASE.md','audits/final_release/FINAL_RELEASE_REPORT.md']


def now():return datetime.now(timezone.utc).isoformat()


def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT)


def save(name,value):(OUT/name).write_text(json.dumps(value,indent=2)+'\n')


def refresh_manifest():
    path=ROOT/'audits/evidence_breakthrough/CURRENT_BRANCH_MANIFEST.json'
    previous=OUT/'PREVIOUS_CURRENT_BRANCH_MANIFEST.json'
    if not previous.exists():shutil.copyfile(path,previous)
    value=json.loads(path.read_text())
    value.update(source_head=git('rev-parse','HEAD').decode().strip(),
                 purpose='Current working-version consistency; refreshed after documented final revisions. Old V4 Release Manifest and assertions unchanged.')
    value['files']={p:sha256_file(ROOT/p) for p in value['files']}
    path.write_text(json.dumps(value,indent=2)+'\n')


def numerical():
    pred=pd.read_csv(ROOT/'research_extension/ni2025_confirmation/predictions.csv.gz')
    observed=compute_experiment_metrics(pred.actual_do_mg_l,pred.predicted_do_mg_l,stations=pred.station_code)
    expected=json.loads((ROOT/'research_extension/ni2025_confirmation/RESULTS.json').read_text())['metrics']
    for key,value in expected.items():
        if value is not None:assert np.isclose(observed[key],value,rtol=1e-10,atol=1e-10),key
    raw=pd.read_csv(ROOT/'work/evidence_breakthrough/ni2025_raw.csv',encoding='cp1252')
    assert len(raw)==6080 and raw['DO (mg/l)'].isna().sum()==2590
    low=pred.actual_do_mg_l.lt(4);detected=pred.predicted_do_mg_l.lt(4)
    assert pred.loc[low,'station_code'].nunique()==9
    assert pred.loc[low&detected,'station_code'].nunique()==1
    sensitivity=pd.read_csv(ROOT/'research_extension/final_release/outlier_sensitivity.csv')
    assert len(sensitivity)==2 and list(sensitivity.sample_count)==[3490,3489]
    for key in ['low_do_mae_mg_l','low_do_recall','true_positive_count','false_positive_count','false_negative_count']:
        assert np.isclose(sensitivity.iloc[0][key],sensitivity.iloc[1][key]),key
    reps=pd.read_csv(ROOT/'research_extension/ni2025_confirmation/bootstrap_replicates.csv.gz')
    assert int(reps.precision.isna().sum())==1844
    primary=json.loads((ROOT/'research_extension/ni2025_confirmation/RESULTS.json').read_text())
    for col,key in [('overall_mae','overall_mae'),('low_do_mae','low_do_mae'),('recall','recall'),('precision','precision')]:
        interval=primary['cluster_intervals'][key]
        assert np.allclose(np.quantile(reps[col].dropna(),[.025,.975]),[interval['lower_95'],interval['upper_95']])
    save('numerical_consistency.json',{'status':'PASS','primary_metrics_recomputed':observed,
         'raw_rows':len(raw),'source_stations':int(raw['Station Code'].nunique()),
         'missing_do':2590,'missing_do_percent':2590/6080*100,
         'event_stations':9,'detected_event_stations':1,'bootstrap_precision_undefined':1844,
         'primary_intervals_recomputed':True,'sensitivity_low_event_metrics_unchanged':True,
         'interpretation':'Complete-target evaluation; no missing-at-random assumption. No new inference.'})


def integrity():
    dirs=['research_outputs','research_outputs_v2','research_upgrade_v3','research_upgrade_v4_candidate','results','models']
    paths=git('ls-tree','-r','--name-only','c2ab7b4','--',*dirs).decode().splitlines()
    mismatch=[]
    for p in paths:
        expected=hashlib.sha256(git('show',f'c2ab7b4:{p}')).hexdigest()
        if p=='models/phase4_selected_model.joblib':expected='7434cbd29bf6a1b2b624ef3283d073212a82ec72a839d7a050bb912b8506f44f'
        if sha256_file(ROOT/p)!=expected:mismatch.append(p)
    primary=ROOT/'research_extension/ni2025_confirmation'
    changed_primary=[str(p.relative_to(ROOT)) for p in primary.iterdir() if p.is_file()
         and p.read_bytes()!=git('show',f'00e4cd3:{p.relative_to(ROOT)}')]
    old='research_upgrade_v4_candidate/V4_RELEASE_CANDIDATE_MANIFEST.json'
    archived=json.loads((ROOT/old).read_text())
    save('integrity.json',{'historical_files_checked':len(paths),'historical_byte_mismatches':mismatch,
         'primary_2025_files_checked':len(list(primary.iterdir())),'primary_2025_changed':changed_primary,
         'v4_release_manifest_sha256':sha256_file(ROOT/old),
         'v4_expected_readme_sha256':archived['files']['README.md'],
         'current_readme_sha256':sha256_file(ROOT/'README.md'),
         'frozen_model_sha256':sha256_file(ROOT/'models/phase4_selected_model.joblib'),
         'status':'PASS' if not mismatch and not changed_primary else 'FAIL'})
    assert not mismatch and not changed_primary


def links_and_privacy():
    broken=[];urls=set()
    for name in DOCS:
        content=(ROOT/name).read_text()
        for target in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)',content):
            target=target.strip('<>')
            if target.startswith(('https://','http://')):urls.add(target);continue
            if target.startswith('#'):continue
            path=urllib.parse.unquote(target.split('#')[0])
            if path and not (ROOT/name).parent.joinpath(path).exists():broken.append({'file':name,'target':target})
        urls.update(re.findall(r'<(https?://[^>]+)>',content))
    candidates=git('ls-files','--cached','--others','--exclude-standard').decode().splitlines()
    patterns={'private_key':r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',
              'token_like':r'\b(?:ghp_[A-Za-z0-9]{30,}|sk-proj-[A-Za-z0-9_-]{40,})',
              'private_absolute_path':r'/(?:Users|home)/[A-Za-z0-9_.-]+/'}
    findings=[]
    for name in candidates:
        path=ROOT/name
        if not path.is_file() or path.suffix in {'.gz','.png','.joblib','.pdf','.ipynb'}:continue
        try:content=path.read_text()
        except UnicodeDecodeError:continue
        for category,pattern in patterns.items():
            if re.search(pattern,content):findings.append({'file':name,'category':category})
    save('local_links_privacy.json',{'documents_checked':DOCS,'broken_local_links':broken,
        'text_files_inventory':len(candidates),'pattern_findings':findings,
        'scope':'Heuristic tracked/unignored text scan; not proof that no personal information exists. Raw source CSV remains ignored.',
        'external_urls':sorted(urls)})
    assert not broken
    return urls


def probe(url):
    started=now()
    try:
        folder=ROOT/'work/final_release/link_bodies';folder.mkdir(parents=True,exist_ok=True)
        target=folder/hashlib.sha256(url.encode()).hexdigest()
        # Native curl uses the system certificate trust store. TLS checks stay enabled.
        run=subprocess.run(['curl','--location','--silent','--show-error','--max-time','25',
             '--output',str(target),'--write-out','%{http_code}\n%{url_effective}',url],text=True,capture_output=True)
        if run.returncode:raise RuntimeError(run.stderr.strip())
        status,final=run.stdout.split('\n',1);content=target.read_bytes()
        record={'url':url,'final_url':final,'status':int(status),'retrieved_utc':started,
                'bytes':len(content),'sha256':hashlib.sha256(content).hexdigest(),
                'transport':'system curl; TLS verification enabled'}
        if url==SOURCE:
            target=ROOT/'work/final_release/source_recheck.csv';target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(content)
            record['matches_evaluated_source_bytes']=record['sha256']=='9e8713d94835f1bdb9c71f9d5bb36cfc944ed925b206d09aa18216482aa75c7a'
            if record['matches_evaluated_source_bytes']:
                frame=pd.read_csv(target,encoding='cp1252')
                record['source_row_4859_do_mg_l']=float(frame.iloc[4858]['DO (mg/l)'])
        return record
    except Exception as error:return {'url':url,'retrieved_utc':started,'status':'UNVERIFIED','reason':str(error)}


def tests():
    runs=[];outcomes=[]
    assert (BASELINE/'.git').is_file(),'Expected retained detached baseline worktree'
    for label,repo in [('baseline',BASELINE),('current',ROOT)]:
        for suite,args in [('main',['-m','unittest','discover','-s','tests','-v']),
            ('v4',['-m','unittest','discover','-s','research_upgrade_v4_candidate','-p','test*.py','-v'])]:
            started=now();run=subprocess.run([sys.executable,*args],cwd=repo,text=True,capture_output=True)
            ended=now();body=run.stdout+'\n'+run.stderr
            body=body.replace(str(BASELINE),'<BASELINE>').replace(str(ROOT),'<REPO>')
            name=f'{label}_{suite}.log'
            (OUT/name).write_text(f'START_UTC: {started}\nEND_UTC: {ended}\nCOMMAND: python3 '+ ' '.join(args)+f'\nEXIT: {run.returncode}\n'+body)
            count=re.search(r'Ran (\d+) tests?',body)
            runs.append({'version':label,'suite':suite,'head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip(),
                         'exit_code':run.returncode,'tests_run':int(count[1]) if count else None,
                         'started_utc':started,'ended_utc':ended,'log':name})
            for line in body.splitlines():
                match=re.match(r'^(test_\S+|setUpClass) \(([^)]+)\) \.\.\. (.*)$',line)
                if match:outcomes.append({'run':label+'_'+suite,'test':match[2],'outcome':match[3]})
            print(json.dumps(runs[-1]),flush=True)
    save('test_results.json',{'status':'PARTIAL_LEGACY_V4_FAILURE_RETAINED','runs':runs,'named_outcomes':outcomes,
         'not_executed':['Model searches, tuning, new external inference or prospective experiments (outside final-release scope).'],
         'skips_are_passes':False})
    assert all(r['exit_code']==0 for r in runs if r['suite']=='main')
    assert all(r['exit_code']==1 for r in runs if r['suite']=='v4')
    for label in ['baseline','current']:
        group=[r for r in outcomes if r['run']==label+'_v4']
        assert len(group)==8 and sum(r['outcome']=='ok' for r in group)==7
        assert sum(r['outcome']=='FAIL' and 'test_release_candidate_manifest' in r['test'] for r in group)==1
    assert not any('skip' in r['outcome'].lower() for r in outcomes)


def main():
    OUT.mkdir(exist_ok=True,parents=True)
    save('environment.json',{'started_utc':now(),'git_head':git('rev-parse','HEAD').decode().strip(),
        'branch':git('branch','--show-current').decode().strip(),'python':sys.version,'platform':platform.platform(),
        'packages':{p:version(p) for p in ['numpy','pandas','scikit-learn','matplotlib','joblib']},
        'input_hashes':{p:sha256_file(ROOT/p) for p in ['data/raw/niea_river_water_quality_1990_2024.csv',
          'data/processed/water_quality_modeling.csv','work/evidence_breakthrough/ni2025_raw.csv',
          'research_extension/ni2025_confirmation/predictions.csv.gz','scripts/prepare_final_release.py',
          'scripts/audit_final_release.py']},
        'working_diff_sha256':hashlib.sha256(git('diff','--binary','HEAD')).hexdigest(),
        'experiment_config':{'new_training':False,'new_inference':False,'new_random_sampling':False,
                             'random_seed':'Not applicable: deterministic saved-prediction diagnostic'}})
    refresh_manifest();numerical();integrity();urls=links_and_privacy()
    urls.update([SOURCE,LICENSE])
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
        save('source_and_link_probes.json',list(executor.map(probe,sorted(urls))))
    tests()


if __name__=='__main__':main()
