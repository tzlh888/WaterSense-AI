#!/usr/bin/env python3
"""Run the same historical tests in an isolated baseline and current branch."""
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.portfolio_analysis import sha256_file


def main():
    out=ROOT/'audits/evidence_breakthrough'
    out.mkdir(parents=True,exist_ok=True)
    baseline=ROOT/'work/evidence_baseline_c2ab7b4'
    if not baseline.exists():
        subprocess.run(['git','worktree','add','--detach',str(baseline),'c2ab7b4'],cwd=ROOT,check=True)
    for relative in ['data/raw/niea_river_water_quality_1990_2024.csv',
        'data/processed/water_quality_modeling.csv','data/processed/water_quality_modeling_audit.json']:
        target=baseline/relative
        target.parent.mkdir(parents=True,exist_ok=True)
        if target.exists() and sha256_file(target)!=sha256_file(ROOT/relative):
            raise ValueError('Nonmatching baseline fixture: refusing overwrite')
        if not target.exists():shutil.copyfile(ROOT/relative,target)
    results=[]
    for name,repo in [('baseline',baseline),('current',ROOT)]:
        for suite,args in [('main',['-m','unittest','discover','-s','tests','-v']),
            ('v4',['-m','unittest','discover','-s','research_upgrade_v4_candidate','-p','test*.py','-v'])]:
            run=subprocess.run([sys.executable,*args],cwd=repo,text=True,capture_output=True)
            log=(run.stdout+'\n'+run.stderr).replace(str(baseline),'<BASELINE>').replace(str(ROOT),'<REPO>')
            (out/f'{name}_{suite}.log').write_text(log)
            results.append({'version':name,'suite':suite,'exit_code':run.returncode,
                'head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip(),
                'log':f'{name}_{suite}.log'})
            print(json.dumps(results[-1]),flush=True)
    manifest=json.loads((ROOT/'research_upgrade_v4_candidate/V4_RELEASE_CANDIDATE_MANIFEST.json').read_text())
    mismatches={}
    for name,repo in [('baseline',baseline),('current',ROOT)]:
        mismatches[name]=[{'file':p,'expected':expected,'observed':sha256_file(repo/p) if (repo/p).is_file() else None}
            for p,expected in manifest['files'].items() if not (repo/p).is_file() or sha256_file(repo/p)!=expected]
    protected=['research_outputs','research_outputs_v2','research_upgrade_v3','research_upgrade_v4_candidate','results','models']
    changed=subprocess.check_output(['git','diff','c2ab7b4','--name-only','--',*protected],cwd=ROOT,text=True).splitlines()
    # Both staged and unstaged protected bytes are checked, including the LFS model.
    files=subprocess.check_output(['git','ls-tree','-r','--name-only','c2ab7b4','--',*protected],cwd=ROOT,text=True).splitlines()
    byte_mismatches=[]
    for p in files:
        if p=='models/phase4_selected_model.joblib':
            if sha256_file(ROOT/p)!='7434cbd29bf6a1b2b624ef3283d073212a82ec72a839d7a050bb912b8506f44f':byte_mismatches.append(p)
        elif (ROOT/p).read_bytes()!=subprocess.check_output(['git','show',f'c2ab7b4:{p}'],cwd=ROOT):byte_mismatches.append(p)
    result={'runs':results,'release_manifest_mismatches':mismatches,'protected_tracked_changes':changed,
        'protected_files_checked':len(files),'protected_byte_mismatches':byte_mismatches,
        'v4_test_source_identical':sha256_file(baseline/'research_upgrade_v4_candidate/test_v4_upgrade.py')==sha256_file(ROOT/'research_upgrade_v4_candidate/test_v4_upgrade.py')}
    (out/'version_consistency.json').write_text(json.dumps(result,indent=2)+'\n')
    assert not changed and not byte_mismatches


if __name__=='__main__':main()
