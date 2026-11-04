#!/usr/bin/env python3
"""Capture complete final checks; distinguish archived expected failures from passes."""
import json
import os
import platform
import re
import subprocess
import sys
from importlib.metadata import version
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.portfolio_analysis import sha256_file


def main():
    out=ROOT/'audits/evidence_breakthrough';out.mkdir(parents=True,exist_ok=True)
    environment={'git_head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        'python':sys.version,'platform':platform.platform(),
        'packages':{p:version(p) for p in ['numpy','pandas','scikit-learn','matplotlib','joblib']},
        'source_hashes':{str(p.relative_to(ROOT)):sha256_file(p) for p in ROOT.glob('scripts/*evidence*.py')}}
    (out/'environment.json').write_text(json.dumps(environment,indent=2)+'\n')
    results=[]
    for name,args in [('historical_replay',['scripts/reproduce_recovered_history.py']),
        ('saved_metric_reconstruction',['scripts/run_portfolio_analysis.py']),
        ('current_artifact_packaging',['scripts/finalize_evidence_audit.py']),
        ('version_and_tests',['scripts/audit_version_consistency.py'])]:
        env={**os.environ,'OMP_NUM_THREADS':'2','OPENBLAS_NUM_THREADS':'2'}
        run=subprocess.run([sys.executable,*args],cwd=ROOT,env=env,text=True,capture_output=True)
        log='COMMAND: python3 '+' '.join(args)+'\nEXIT: '+str(run.returncode)+'\nSTDOUT:\n'+run.stdout+'\nSTDERR:\n'+run.stderr
        (out/f'{name}.log').write_text(log.replace(str(ROOT),'<REPO>'))
        results.append({'command':args,'exit_code':run.returncode,'log':f'{name}.log'})
        print(json.dumps(results[-1]),flush=True)
        if run.returncode:raise RuntimeError('Required reproduction command failed: '+name)
    tests=[]
    for path in sorted(out.glob('*_main.log'))+sorted(out.glob('*_v4.log')):
        for line in path.read_text().splitlines():
            m=re.match(r'^(test_\S+|setUpClass) \(([^)]+)\) \.\.\. (.*)$',line)
            if m:tests.append({'log':path.name,'test':m[2]+'.'+m[1],'outcome':m[3]})
    version_report=json.loads((out/'version_consistency.json').read_text())
    assert all(r['exit_code']==0 for r in version_report['runs'] if r['suite']=='main')
    assert all(r['exit_code']==1 for r in version_report['runs'] if r['suite']=='v4')
    for name in ['baseline','current']:
        failure=[r for r in tests if r['log']==f'{name}_v4.log' and r['outcome']!='ok']
        assert len(failure)==1 and failure[0]['test'].endswith('.test_release_candidate_manifest') and failure[0]['outcome']=='FAIL'
    missing=[]
    for folder in ['paper','admissions','audits','research_extension']:
        for path in (ROOT/folder).rglob('*.md'):
            for target in re.findall(r'!?\[[^]]*\]\(([^)]+)\)',path.read_text()):
                target=target.split('#',1)[0]
                if target and not target.startswith(('http:','https:','mailto:')) and not (path.parent/target).exists():missing.append([str(path.relative_to(ROOT)),target])
    assert not missing
    summary={'status':'PARTIAL_HISTORICAL_ARCHIVE_ASSERTION_RETAINED','commands':results,
        'tests':tests,'local_missing_links':missing,'ea_predictions_performed':False,
        'ni2025_single_frozen_evaluation_completed':(ROOT/'research_extension/ni2025_confirmation/RESULTS.json').exists(),
        'protected_files_checked':version_report['protected_files_checked'],
        'protected_byte_mismatches':version_report['protected_byte_mismatches']}
    (out/'quality_gate_summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print('Required checks PASS; historical V4 suite retains exactly its documented README failure.')


if __name__=='__main__':main()
