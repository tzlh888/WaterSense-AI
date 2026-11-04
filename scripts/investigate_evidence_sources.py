#!/usr/bin/env python3
"""Read-only public-source probes; retain HTTP evidence, never run predictions."""
import concurrent.futures
import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
WORK=ROOT/'work/evidence_breakthrough'
OUT=ROOT/'audits/evidence_breakthrough'
NI='https://services-eu1.arcgis.com/kswen6BYexuc1SUk/arcgis/rest/services/River_Water_Quality_Monitoring_1990_to_2024_All_Parameters/FeatureServer/0'


def probe(item):
    name,url,*options=item
    headers=options[0] if options else {}
    path=WORK/name
    run=subprocess.run(['curl','--location','--silent','--show-error','--max-time','30',
        '--dump-header',str(path)+'.headers','--output',str(path),'--write-out','%{http_code}',
        *[arg for key,value in headers.items() for arg in ['-H',f'{key}: {value}']],url],text=True,capture_output=True)
    record={'name':name,'url':url,'retrieved_utc':datetime.now(timezone.utc).isoformat(),
        'curl_exit':run.returncode,'http_status':run.stdout,'stderr':run.stderr,'headers':headers,
        'bytes':path.stat().st_size if path.exists() else 0,
        'sha256':hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None}
    print(json.dumps(record),flush=True)
    return record


def main():
    WORK.mkdir(parents=True,exist_ok=True); OUT.mkdir(parents=True,exist_ok=True)
    urls=[('ni_service.json',NI+'?f=json'),
        ('ni_count.json',NI+'/query?where=1%3D1&returnCountOnly=true&f=json'),
        ('ni_page.json',NI+'/query?where=1%3D1&outFields=*&orderByFields=OBJECTID&resultOffset=0&resultRecordCount=2&returnGeometry=false&f=json'),
        ('ea_reference.html','https://environment.data.gov.uk/water-quality/doc/reference'),
        ('ea_api.html','https://environment.data.gov.uk/water-quality/api'),
        ('ea_sampling.json','https://environment.data.gov.uk/water-quality/id/sampling-point.json?_limit=2'),
        ('ea_determinands.json','https://environment.data.gov.uk/water-quality/id/determinand.json?_limit=1000')]
    index=WORK/'ea_index.html'
    if index.exists():
        sources=re.findall(r'src="([^" ]+\.js[^" ]*)',index.read_text())
        urls.extend((f'ea_chunk_{i}.js','https://environment.data.gov.uk'+url) for i,url in enumerate(dict.fromkeys(sources)))
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        records=list(pool.map(probe,urls))
    (OUT/'source_probes.json').write_text(json.dumps(records,indent=2)+'\n')


if __name__=='__main__':main()
