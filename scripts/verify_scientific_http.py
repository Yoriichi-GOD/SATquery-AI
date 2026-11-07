"""Actual local HTTP/source/claim checks; does not acquire imagery or run a model."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import time

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import requests
from research.terrain_exposure.io import save_json
from jai_extension.investigation import verify_trace


def run(base,output):
    if base not in {'http://127.0.0.1:18868','http://127.0.0.1:8768'}:
        raise ValueError('Use the documented local scientific or primary service')
    checks=[];jobs=[]
    def get(path,expected=200):
        response=requests.get(base+path,timeout=30)
        assert response.status_code==expected,(path,response.status_code,response.text[:120])
        checks.append({'path':path,'status':response.status_code,'sha256':hashlib.sha256(response.content).hexdigest()})
        return response
    assert 'SAT' in get('/').text.upper()
    runs=get('/api/terrain-exposure/runs').json()['runs']
    assert len(runs)==1
    identity=runs[0]['id'];detail=get('/api/terrain-exposure/runs/'+identity).json()
    assert detail['summary']['observations']['water']['candidate_pixels']==956
    assert detail['summary']['observations']['debris']['candidate_pixels']==1041
    assert detail['summary']['resolution']['status']=='INSUFFICIENT_RESOLUTION'
    for source in detail['sources']:
        response=get(source['url'])
        assert hashlib.sha256(response.content).hexdigest()==source['sha256']==response.headers['x-artifact-sha256']
    get('/api/terrain-exposure/runs/not-a-run',404)
    get('/api/terrain-exposure/runs/'+identity+'/artifact/secret',404)
    # Exercise unchanged flood/debris endpoints through the real upstream bridge too.
    raw=get('/api/flood/runs/event-fe47db331390').json()
    assert raw['summary']['new_water_m2']==95600
    assert get('/api/flood/runs/event-fe47db331390/debris').json()['summary']['debris_candidate_m2']==104100
    questions=[('Show catchments and flow accumulation','complete'),
               ('Which buildings have downstream connections?','abstained'),
               ('Show debris pathways near roads','abstained'),
               ('Predict flood depth downstream','abstained'),
               ('Are roads safe downstream?','abstained'),
               ('Show catchments in 2020','abstained')]
    supported=0;claims=0;abstained=0;unsupported_claims=0
    for question,expected in questions:
        response=requests.post(base+'/api/investigations',json={'question':question,'run_id':'event-fe47db331390'},timeout=30)
        assert response.status_code==202,response.text
        job=response.json();deadline=time.monotonic()+45
        while job['state'] not in {'complete','abstained','failed','cancelled','interrupted'}:
            assert time.monotonic()<deadline,'Investigation did not finish'
            time.sleep(.05);job=get('/api/investigations/'+job['id']).json()
        assert job['state']==expected,(question,job)
        verify_trace(job['trace'])
        result=job['result'];assert result['ai_model_used'] is False
        abstained+=result['state']=='abstained'
        for claim in result.get('claims',[]):
            claims+=1;source=result['sources'][claim['source']]
            response=get(source['url']);data=response.json()
            assert hashlib.sha256(response.content).hexdigest()==source['sha256']
            for component in claim['field'].strip('/').split('/'):
                data=data[component.replace('~1','/').replace('~0','~')]
            if data==claim['value']:supported+=1
            else:unsupported_claims+=1
        jobs.append(job)
    assert unsupported_claims==0
    value={'population':'GENUINE_SAVED_DATA_HTTP_REPLAY_WITH_DEVELOPMENT_QUERY_SET',
           'base':base,'checks':checks,'jobs':jobs,'queries':len(questions),'claims':claims,
           'mechanically_source_supported_claims':supported,'unsupported_by_recorded_source_claims':unsupported_claims,
           'source_support_rate':supported/claims if claims else None,
           'abstentions':abstained,'abstention_rate':abstained/len(questions),
           'limitations':['Development query set, not routing population accuracy',
                          'Source support is not independent physical truth',
                          'HTTP/source checks do not verify rendered browser behaviour']}
    save_json(output,value)
    print(json.dumps({k:v for k,v in value.items() if k not in {'checks','jobs'}},indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',default='http://127.0.0.1:18868');p.add_argument('--output',required=True);a=p.parse_args()
    if Path(a.output).exists():raise FileExistsError('Do not overwrite an HTTP receipt')
    run(a.base,a.output)
