"""Live localhost integration receipt against retained Nepal inputs, not field truth."""
import argparse
from datetime import datetime,timezone
import hashlib
import io
import json
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request,urlopen
import xml.etree.ElementTree as ET
import zipfile

def run(base,output):
    output=Path(output)
    if output.exists():raise FileExistsError('Use a new verification receipt path')
    def request(path,payload=None,expected=200):
        raw=None if payload is None else json.dumps(payload).encode()
        req=Request(base+path,data=raw,headers={'Content-Type':'application/json'} if raw else {})
        try:
            with urlopen(req,timeout=90) as response:
                status=response.status;headers={k.lower():v for k,v in response.headers.items()};body=response.read()
        except HTTPError as error:status=error.code;headers={k.lower():v for k,v in error.headers.items()};body=error.read()
        assert status==expected,(path,status,body[:300])
        return body,headers
    root=Path(__file__).resolve().parents[1]
    saved=root/'artifacts/runs/nepal-syapru-004'
    freeze=json.loads((saved/'freeze.json').read_bytes())['files']
    def source_hashes():
        values={name:hashlib.sha256((saved/name).read_bytes()).hexdigest() for name in freeze}
        assert values==freeze,'Frozen source changed'
        return values
    before=source_hashes()
    for path in ['/','/assets/response-panel.js','/assets/response-panel.css','/assets/cosmic-shell.css']:
        request(path)
    asset_receipts={}
    for folder in ['web/cosmic','web/fonts']:
        for path in sorted((root/folder).iterdir()):
            url='/assets/'+path.relative_to(root/'web').as_posix()
            raw,_=request(url)
            assert raw==path.read_bytes(),'Served UI asset differs: '+url
            asset_receipts[url]={'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
    baseline=json.loads(request('/api/response/runs/nepal-syapru-004')[0])
    assert len(baseline['candidate_way_ids'])==13
    assert baseline['summary']['unknown_aoi_boundary']==1
    assert baseline['summary']['not_assessed']==1
    rankings=baseline['repair_search']['rankings']
    assert len(rankings)==1 and rankings[0]['possible_gain']==1 and rankings[0]['supported_gain']==0
    bundle=rankings[0]['restore_way_ids']
    assert bundle==['way/332122791','way/83925854','way/84566285','way/84566287']
    scenario=json.loads(request('/api/response/runs/nepal-syapru-004/scenarios',{'restore_way_ids':bundle})[0])
    row=next(row for row in scenario['rows'] if row['name']=='Syabru Bensi')
    assert row['status']=='UNKNOWN_UNOBSERVED_ROUTE'
    assert row['routes']['optimistic'] and row['routes']['conservative'] is None
    assert scenario['summary']['possible_routes_through_unknown']==1
    exports={};bodies={}
    for item in scenario['artifacts']:
        raw,headers=request(item['url'])
        digest=hashlib.sha256(raw).hexdigest()
        assert headers['x-artifact-sha256']==digest
        assert headers['x-content-type-options']=='nosniff'
        bodies[item['name']]=raw;exports[item['name']]={'sha256':digest,'bytes':len(raw)}
    evidence=json.loads(bodies['evidence.json'])
    for name,sha in evidence['files'].items():assert exports[name]['sha256']==sha
    ET.fromstring(bodies['fieldkit.kml'])
    with zipfile.ZipFile(io.BytesIO(bodies['bundle.zip'])) as archive:
        assert archive.testzip() is None
        assert set(archive.namelist())==set(bodies)-{'bundle.zip'}
        for name in archive.namelist():assert archive.read(name)==bodies[name]
    nohub=json.loads(request('/api/response/runs/event-fe47db331390')[0])
    assert nohub['state']=='NOT_ASSESSED_NO_HUBS'
    assert nohub['summary']['observation_supported_mapped_routes'] is None
    request('/api/response/runs/nepal-syapru-004/scenarios',{'restore_way_ids':['not-a-real-way']},422)
    request('/api/response/runs/nepal-syapru-004/scenarios',{'restore_way_ids':[bundle[0],bundle[0]]},422)
    request('/api/response/runs/missing-run',expected=404)
    assert source_hashes()==before
    report={'checked_at':datetime.now(timezone.utc).isoformat(),'base_url':base,'state':'PASS',
        'population':'GENUINE_SAVED_NETWORK_REPLAY_NOT_FIELD_VALIDATION',
        'baseline_scenario_id':baseline['scenario_id'],'repair_scenario_id':scenario['scenario_id'],
        'baseline_summary':baseline['summary'],'repair_summary':scenario['summary'],
        'repair_way_ids':bundle,'search':baseline['repair_search'],
        'no_hub_state':nohub['state'],'exports':exports,'served_ui_assets':asset_receipts,'frozen_files_verified_unchanged':len(before),
        'checks':['live GET/POST','all field exports and SHA headers','KML XML parse','ZIP CRC and exact payloads',
                  'missing hubs remain null','invalid repairs rejected','unknown observations preserved',
                  'all frozen source hashes unchanged']}
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'state':'PASS','report':str(output),'frozen_files':len(before),'exports':len(exports)}))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--base',default='http://127.0.0.1:18870')
    parser.add_argument('--output',required=True);args=parser.parse_args();run(args.base,args.output)
