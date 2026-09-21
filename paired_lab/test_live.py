import requests,time,json,zipfile,io,hashlib
from pathlib import Path
R=Path('/mnt/c/Users/nrgen/.codex/scratch/SATquery AI/paired_lab');url='http://127.0.0.1:8767';checks=[]
def record(name,passed,detail):checks.append({'test':name,'passed':bool(passed),'detail':detail})
samples=requests.get(url+'/api/samples').json()
for kind in ['temporal','optical_sar']:
    s=next(s for s in samples if s['kind']==kind);q='What changed between the dates?' if kind=='temporal' else 'Describe land cover using optical and SAR together'
    r=requests.post(url+'/api/analyze',json={'sample':s['id'],'query':q});r.raise_for_status();jid=r.json()['id']
    duplicate=requests.post(url+'/api/analyze',json={'sample':s['id'],'query':q});record(kind+' busy exclusion',duplicate.status_code==409,duplicate.status_code)
    for _ in range(120):
        j=requests.get(url+'/api/jobs/'+jid).json()
        if j['state']!='processing':break
        time.sleep(.25)
    record(kind+' real HTTP inference',j['state']=='complete',j)
    data=requests.get(url+f'/api/runs/{jid}/evidence.zip').content
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        result=json.loads(z.read('result.json'));inputs=result['input_checks']['inputs'];valid=all(hashlib.sha256(z.read(f'input-{i+1}.tif')).hexdigest()==r['sha256'] for i,r in enumerate(inputs))
        record(kind+' evidence ZIP verifies input hashes',valid,z.namelist())
r=requests.post(url+'/api/analyze',json={'sample':next(s['id'] for s in samples if s['kind']=='optical_sar'),'query':'What changed between the dates?'});record('cross-modal cannot masquerade as temporal',r.status_code==400,r.json())
r=requests.post(url+'/api/analyze',headers={'Origin':'https://example.com'},json={});record('foreign-origin write rejected',r.status_code==403,r.status_code)
s=samples[0];p=R/'samples'/s['id']/s['files'][0]
with p.open('rb') as f:r=requests.post(url+'/api/images',files={'file':('input.tif',f,'image/tiff')},data={'modality':'optical','date':'2020-01-01'})
record('TIFF upload supported',r.status_code==200,r.json())
iid=r.json()['id'];r=requests.post(url+'/api/analyze',json={'images':[iid,iid],'query':'What changed?','trusted_benchmark':True});record('client cannot bypass geographic checks',r.status_code==400,r.json())
(R/'evidence/live-checks.json').write_text(json.dumps(checks,indent=2));print([(r['test'],r['passed']) for r in checks]);assert all(r['passed'] for r in checks)
