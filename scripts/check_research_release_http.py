"""Actual local service checks; not a browser or model-inference validation."""
import argparse,hashlib,io,json,sys,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import requests
from PIL import Image
from research.terrain_exposure.io import save_json

def run(main,flood,output):
    records=[]
    def get(base,path,expected=200):
        r=requests.get(base+path,timeout=40);assert r.status_code==expected,(path,r.status_code)
        records.append({'path':base+path,'status':r.status_code,'bytes':len(r.content),'sha256':hashlib.sha256(r.content).hexdigest()})
        if r.headers.get('X-Artifact-SHA256'):assert r.headers['X-Artifact-SHA256']==hashlib.sha256(r.content).hexdigest()
        return r
    get(main,'/');get(main,'/jai/assets/earth.js');get(main,'/jai/assets/earth.css')
    get(main,'/api/status');get(main,'/api/samples');assert get(main,'/api/flood/health').json()['available']
    get(main,'/api/flood/runs/event-fe47db331390');get(main,'/api/flood/runs/nepal-syapru-004')
    catalogue=get(main,'/api/research/cases').json();assert len(catalogue['cases'])==4
    for item in catalogue['cases']:
        case=item['case_id'];value=get(main,f'/api/research/cases/{case}').json()
        assert value['accuracy_metrics'].startswith('NOT_ASSESSED')
        get(main,f'/api/research/cases/{case}/sources')
        r=get(main,f'/api/research/cases/{case}/panels.png');im=Image.open(io.BytesIO(r.content));im.verify()
    get(main,'/api/research/cases/not-a-case',404)
    scenes=get(main,'/api/terrain/status').json()['scenes'];assert scenes,'Preserved3D scene missing'
    get(main,'/api/terrain/scenes/'+scenes[0]['id'])
    scientific=get(main,'/api/terrain-exposure/runs').json();assert len(scientific['runs'])==1 and not scientific['rejected']
    get(main,'/api/terrain-exposure/runs/'+scientific['runs'][0]['id'])
    response=get(flood,'/api/response/runs/nepal-syapru-004').json()
    assert response['source']['population']=='GENUINE_SAVED_NETWORK_REPLAY'
    bundle=next(a for a in response['artifacts'] if a['name']=='bundle.zip');get(flood,bundle['url'])
    get(flood,'/api/response/runs/event-fe47db331390')
    selection={'question':'Which infrastructure has potential downstream water connections?','run_id':'event-fe47db331390'}
    r=requests.post(main+'/api/investigations',json=selection,headers={'Origin':main},timeout=40)
    assert r.status_code==202;r=r.json()
    for _ in range(60):
        job=get(main,'/api/investigations/'+r['id']).json()
        if job['state'] not in ['queued','running']:break
        time.sleep(.5)
    assert job['state']=='abstained',job.get('message')
    assert job['result']['resolution_status']=='INSUFFICIENT_RESOLUTION'
    value={'status':'PASS','checks':records,'investigation':{'id':job['id'],'state':job['state'],
        'resolution_status':job['result']['resolution_status'],'ai_model_used':job['ai_model_used']},
        'preserved_terrain_scene':scenes[0]['id'],'browser_verification':'NOT_RUN:local browser control disabled',
        'scope':'Live HTTP, source checksum, image parsing, saved-response exports and resolution abstention; not browser rendering or inference validation'}
    save_json(output,value);print(json.dumps({'status':'PASS','http_checks':len(records),'investigation_state':job['state']}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--main',default='http://127.0.0.1:18968');p.add_argument('--flood',default='http://127.0.0.1:18970')
    p.add_argument('--output',required=True);a=p.parse_args();run(a.main,a.flood,a.output)
