#!/usr/bin/env python3
"""Audit bounded external records and exact sample joins; never load a model."""
import concurrent.futures
import json
import sys
from collections import Counter,defaultdict
from pathlib import Path
from urllib.parse import urlencode

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.investigate_evidence_sources import probe,WORK,OUT

CODES=['9924','0082','0085','0088','0111','0118','0117','0180','0189','7692','0162','0062','0077','0135','0061']
HEADERS={'Accept':'application/ld+json','API-Version':'1'}


def point_audit(point):
    observations=[]; records=[]; complete=False
    for page in range(20):
        query=urlencode({'dateFrom':'2025-01-01','dateTo':'2025-12-31',
            'sampleMaterialType':'2AZZ','determinand':','.join(CODES),'limit':250,'skip':page*250})
        name=f'ea_pilot_{point}_{page}.json'
        result=probe((name,f'https://environment.data.gov.uk/water-quality/sampling-point/{point}/observation?{query}',HEADERS))
        records.append(result)
        if result['http_status']!='200' or not result['bytes']:break
        value=json.loads((WORK/name).read_text())
        observations.extend(value.get('member',[]))
        if not (value.get('view') or {}).get('next'):
            complete=True;break
    return point,observations,records,complete


def main():
    points=json.loads((WORK/'ea_f6_open_points.json').read_text())['member']
    assert len(points)==10 and all(p['samplingPointType']['notation']=='F6' for p in points)
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        results=list(pool.map(point_audit,[p['notation'] for p in points]))
    observations=[]; records=[]
    for point,rows,attempts,complete in results:
        observations.extend(rows);records.extend(attempts)
    (OUT/'ea_pilot_requests.json').write_text(json.dumps(records,indent=2)+'\n')
    (WORK/'ea_pilot_observations.json').write_text(json.dumps(observations,indent=2)+'\n')
    coverage=summarize_observations(observations)
    summary={'points':[p['notation'] for p in points],
        'observations':len(observations),'all_pages_complete':all(r[3] for r in results),
        'station_observation_counts':{r[0]:len(r[1]) for r in results},'prediction_performed':False,
        'compatibility_gate':'NOT_FEASIBLE_FOR_PLANNED_CONFIRMATION_WITH_THIS_PILOT',**coverage}
    (OUT/'ea_pilot_summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary,indent=2))


def summarize_observations(observations):
    samples=defaultdict(set); counts=Counter(); bounds=Counter(); dates=[]; identities=set()
    for row in observations:
        if row['id'] in identities:raise ValueError('Duplicate observation identity')
        identities.add(row['id'])
        if row['hasSamplingPoint']['samplingPointType']['notation']!='F6':raise ValueError('Nonriver station')
        if row['hasSample']['sampleMaterialType']['notation']!='2AZZ':raise ValueError('Nonriver material')
        code=row['observedProperty']['notation']
        samples[row['hasSample']['id']].add(code)
        counts[(code,row['observedProperty']['prefLabel'],row['hasUnit'])]+=1
        result=row['hasResult']
        if result.get('upperBound') is not None:bounds['upper_bound']+=1
        if result.get('lowerBound') is not None:bounds['lower_bound']+=1
        dates.append(row['phenomenonTime'])
    required={'9924','0085','0111','0117','0118','0180','0162','0077','0135','0061'}
    return {'exact_samples':len(samples),'complete_ten_determinand_samples':sum(required<=v for v in samples.values()),
        'same_sample_bod_and_suspended_solids':sum({'0085','0135'}<=v for v in samples.values()),
        'code_units_counts':[{'code':k[0],'label':k[1],'unit':k[2],'count':v} for k,v in sorted(counts.items())],
        'censoring_counts':dict(bounds),'date_min':min(dates) if dates else None,'date_max':max(dates) if dates else None}


if __name__=='__main__':main()
