"""Read-only bridge to the preserved demo API; no shared model process or code edits."""
import requests,time,json
BASE='http://127.0.0.1:8765'
def request(method,path,**kwargs):
    try:r=requests.request(method,BASE+path,timeout=60,**kwargs)
    except requests.RequestException as e:raise ValueError('Start the main workspace with paired_lab/start.ps1 before single-image analysis.') from e
    if not r.ok:
        try:detail=r.json().get('detail','Main workspace request failed.')
        except ValueError:detail=r.text
        raise ValueError(detail if isinstance(detail,str) else json.dumps(detail))
    return r
def upload(path,name):
    with open(path,'rb') as f:return request('POST','/api/images',files={'file':(name,f)}).json()
def run(record,query,plan,out):
    start=time.perf_counter();r=upload(record['path'],record['name'])
    launched=request('POST','/api/analyze',data={'image_id':r['id'],'question':query,'mode':plan['mode'],'threshold':plan['threshold']}).json()
    while time.perf_counter()-start<600:
        result=request('GET','/api/runs/'+launched['id']).json()
        if result['state']=='complete':break
        if result['state']=='error':raise ValueError(result.get('error','Main workflow failed.'))
        time.sleep(.4)
    else:raise ValueError('Main workflow exceeded the ten-minute wait; inspect the main workspace before retrying.')
    (out/'main-raw-result.json').write_text(json.dumps(result,indent=2))
    (out/'input-preview.png').write_bytes(request('GET','/api/images/'+r['id']).content)
    if plan['task']=='ndvi':
        for name in ['rgb','false-colour','evidence','mask','ndvi']:
            (out/(name+('.tif' if name=='ndvi' else '.png'))).write_bytes(request('GET','/api/runs/'+launched['id']+'/'+name).content)
    return {'task':plan['task'],'answer':result['answer'],'seconds':result['seconds'],'statistics':result.get('statistics'),'trace':result.get('trace',[])+[{'tool':'Preserved main workspace','run_id':launched['id'],'model':result.get('model'),'revision':result.get('revision'),'mode':result.get('mode'),'routing':result.get('routing')}],'limitations':['Model descriptions and visual counts remain interpretations, not verified measurements.'] if plan['task']=='vqa' else ['NDVI threshold coverage is not a plant-health diagnosis.'],'confidence':{'kind':'See original run evidence; no invented confidence score.'}}
