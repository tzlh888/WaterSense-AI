#!/usr/bin/env python3
"""Offline evidence packaging and current-version hashes; no model access."""
import json
import shutil
import subprocess
import sys
from decimal import Decimal, InvalidOperation
from pathlib import Path

import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.portfolio_analysis import sha256_file
from scripts.audit_ea_compatibility import summarize_observations


def canonical(value, field):
    if value is None or pd.isna(value) or str(value).strip()=='':return None
    if field=='Date':return pd.Timestamp(value).date().isoformat()
    text=str(value).strip()
    try:return str(Decimal(text).normalize())
    except InvalidOperation:return text


def main():
    work=ROOT/'work/evidence_breakthrough';out=ROOT/'audits/evidence_breakthrough'
    snapshots=out/'public_source_snapshots';snapshots.mkdir(exist_ok=True)
    names=['ni_service.json','ni_count.json','ni_page.json','ea_swagger.json',
        'ea_materials_ld.json','ea_types_ld.json','ea_f6_open_points.json','ea_oxygen_ld.json',
        'ea_codes_accept.json','ea_pilot_observations.json','wqp_pilot.csv']
    for name in names:shutil.copyfile(work/name,snapshots/name)
    raw=pd.read_csv(ROOT/'data/raw/niea_river_water_quality_1990_2024.csv',low_memory=False).set_index('OBJECTID')
    page=json.loads((work/'ni_page.json').read_text())['features']
    differences=[];compared=0
    for feature in page:
        row=feature['attributes'];oid=row['OBJECTID']
        for key,value in row.items():
            if key=='OBJECTID' or key not in raw.columns:continue
            compared+=1
            if canonical(value,key)!=canonical(raw.loc[oid,key],key):differences.append([oid,key])
    check={'api_count':json.loads((work/'ni_count.json').read_text())['count'],
        'csv_rows':len(raw),'api_page_rows':len(page),'normalized_fields_compared':compared,
        'normalized_differences':differences,
        'interpretation':'Two-row semantic spot check only. Full original identity is established separately by exact CSV SHA-256, not by this partial API check.'}
    (out/'api_semantic_spotcheck.json').write_text(json.dumps(check,indent=2)+'\n')
    assert not differences and check['api_count']==len(raw)
    observations=json.loads((work/'ea_pilot_observations.json').read_text())
    pilot=json.loads((out/'ea_pilot_summary.json').read_text());pilot.update(summarize_observations(observations))
    ni_stations=set(raw.StationCode)
    pilot['station_identifier_overlap_with_ni']=sorted(ni_stations.intersection(pilot['points']))
    pilot['overlap_boundary']='England/2025 provenance differs from Northern Ireland/1990–2024. Zero station-ID overlap is supporting evidence, not a complete cross-provider physical-sample deduplication.'
    pilot['compatibility_gate']='NOT_FEASIBLE_FOR_PLANNED_CONFIRMATION_WITH_THIS_PILOT'
    (out/'ea_pilot_summary.json').write_text(json.dumps(pilot,indent=2)+'\n')
    pd.DataFrame(pilot['code_units_counts']).to_csv(out/'ea_feature_coverage.csv',index=False)
    samples={}
    for row in observations:
        sample=row['hasSample']['id'];entry=samples.setdefault(sample,{'sample_id':sample,'station':row['hasSamplingPoint']['notation'],'timestamp':row['phenomenonTime']})
        entry[row['observedProperty']['notation']]=True
    pd.DataFrame(samples.values()).fillna(False).to_csv(out/'ea_sample_joint_coverage.csv',index=False)
    rows=[]
    # Trace archived README expectation without changing the frozen assertion.
    expected=json.loads((ROOT/'research_upgrade_v4_candidate/V4_RELEASE_CANDIDATE_MANIFEST.json').read_text())['files']['README.md']
    import hashlib
    for ref in ['9672c80','d649c9d','c2ab7b4','HEAD']:
        content=subprocess.check_output(['git','show',f'{ref}:README.md'],cwd=ROOT)
        digest=hashlib.sha256(content).hexdigest()
        rows.append({'commit':ref,'readme_sha256':digest,'matches_v4_release_readme':digest==expected})
    (out/'readme_archive_trace.json').write_text(json.dumps(rows,indent=2)+'\n')
    snapshot_hashes={p.name:sha256_file(p) for p in sorted(snapshots.iterdir())}
    (out/'public_source_snapshot_hashes.json').write_text(json.dumps(snapshot_hashes,indent=2)+'\n')
    files=['README.md','paper/WATERSENSE_AI_MANUSCRIPT.md','research_extension/EXTERNAL_COMPATIBILITY_PROTOCOL.md',
        'admissions/ECOLE_POLYTECHNIQUE.md','admissions/PSL_IBSAI.md',
        'admissions/TECHNICAL_INTERVIEW_QA.md','audits/evidence_breakthrough/EXTERNAL_COMPATIBILITY_REPORT.md',
        'scripts/audit_ea_compatibility.py','scripts/reproduce_recovered_history.py',
        'scripts/validate_ni2025.py','research_extension/NI2025_CONFIRMATION_PROTOCOL.md',
        'research_extension/ni2025_confirmation/FREEZE.json','research_extension/ni2025_confirmation/RESULTS.json',
        'research_extension/ni2025_confirmation/TEMPORAL_CONFIRMATION_REPORT.md']
    manifest={'purpose':'Current-branch artifact consistency; historical V4 release manifest is retained unchanged.',
        'source_head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        'files':{p:sha256_file(ROOT/p) for p in files}}
    (out/'CURRENT_BRANCH_MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
    gate_path=out/'quality_gate_summary.json'
    if gate_path.exists():
        gate=json.loads(gate_path.read_text());tests=[]
        import re
        for path in sorted(out.glob('*_main.log'))+sorted(out.glob('*_v4.log')):
            for line in path.read_text().splitlines():
                match=re.match(r'^(test_\S+|setUpClass) \(([^)]+)\) \.\.\. (.*)$',line)
                if match:tests.append({'log':path.name,'test':match[2]+'.'+match[1],'outcome':match[3]})
        gate.update(tests=tests,ea_predictions_performed=False,ni2025_single_frozen_evaluation_completed=True)
        gate.pop('external_predictions_performed',None)
        (out/'quality_gate_summary.json').write_text(json.dumps(gate,indent=2)+'\n')
    print(json.dumps({'semantic_check':check,'snapshots':len(snapshot_hashes),'current_manifest_files':len(files)},indent=2))


if __name__=='__main__':main()
