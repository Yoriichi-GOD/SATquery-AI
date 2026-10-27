"""Real HTTP CDVQA integration smoke; development inputs, not an accuracy evaluation."""
import argparse,io,json,time,zipfile
from pathlib import Path
import requests

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--url',default='http://127.0.0.1:8767')
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args()
    if a.out.exists():p.error('Use a new output directory.')
    root=Path(__file__).resolve().parents[1]
    client=requests.Session()
    client.headers['Origin']=a.url.rstrip('/')
    ids=[];originals=[]
    for name in ['before.tif','after.tif']:
        path=root/'paired_lab/samples/mci-test_000036'/name
        originals.append(path.read_bytes())
        with path.open('rb') as f:r=client.post(a.url+'/api/cdvqa-images',files={'file':(name,f)},timeout=30)
        r.raise_for_status();ids.append(r.json()['id'])
    payload=dict(images=ids,query='Did the areas of buildings change?',aligned=True)
    for bad in [{**payload,'aligned':False},{**payload,'query':'Count every changed car'}]:
        r=client.post(a.url+'/api/analyze',json=bad,timeout=30)
        assert r.status_code==400,r.text
    r=client.post(a.url+'/api/analyze',json=payload,timeout=30);r.raise_for_status()
    job=r.json();assert job['task']=='cdvqa'
    deadline=time.monotonic()+120
    while time.monotonic()<deadline:
        r=client.get(a.url+'/api/jobs/'+job['id'],timeout=30);r.raise_for_status();state=r.json()
        if state['state']=='failed':raise RuntimeError(state['error'])
        if state['state']=='complete':break
        time.sleep(.25)
    else:raise TimeoutError('Inference did not complete.')
    result=state['result'];assert len(result['class_scores_uncalibrated'])==19
    r=client.get(a.url+'/api/runs/'+job['id']+'/evidence.zip',timeout=30);r.raise_for_status()
    with zipfile.ZipFile(io.BytesIO(r.content)) as archive:
        assert archive.testzip() is None
        assert {'result.json','before.png','after.png','input-1.original','input-2.original'}<=set(archive.namelist())
        assert json.loads(archive.read('result.json'))['checkpoint_sha256']==result['checkpoint_sha256']
        for i,raw in enumerate(originals,1):
            assert archive.read(f'input-{i}.original')==raw, 'Original upload changed'
    a.out.mkdir(parents=True);(a.out/'evidence.zip').write_bytes(r.content)
    (a.out/'verification.json').write_text(json.dumps(dict(job=job,state=state,scope='Previously inspected MCI development pair; real integration only, not CDVQA accuracy.'),indent=2))
    print(json.dumps(dict(status='passed_real_http_inference',id=job['id'],answer=result['answer'],output=str(a.out))))
if __name__=='__main__':main()
