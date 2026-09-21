import requests,time,json,io,zipfile,sys,numpy as np,rasterio
from pathlib import Path
P=Path('/mnt/c/Users/nrgen/.codex/scratch/SATquery AI/paired_lab');O=P/'evidence/resumed/live';O.mkdir(exist_ok=True)
URL='http://127.0.0.1:8767';results=[]
def run(name,payload):
 started=time.perf_counter();r=requests.post(URL+'/api/analyze',json=payload,timeout=90)
 if r.status_code!=200:raise RuntimeError(name+' '+str(r.status_code)+' '+r.text)
 launched=r.json();jid=launched['id']
 while time.perf_counter()-started<600:
  j=requests.get(URL+'/api/jobs/'+jid,timeout=60).json()
  if j['state']=='complete':break
  if j['state']=='failed':raise RuntimeError(name+' '+j['error'])
  time.sleep(.5)
 else:raise RuntimeError(name+' timed out')
 result=j['result'];z=requests.get(URL+'/api/runs/'+jid+'/evidence.zip',timeout=60);z.raise_for_status()
 with zipfile.ZipFile(io.BytesIO(z.content)) as archive:
  assert archive.testzip() is None
  saved=json.loads(archive.read('result.json'));assert saved==result
  files=archive.namelist()
 (O/(name+'.json')).write_text(json.dumps(result,indent=2))
 results.append({'name':name,'id':jid,'task':result['task'],'elapsed_seconds':time.perf_counter()-started,'answer':result['answer'],'bundle_files':files,'passed':True})
 (O/'replay.json').write_text(json.dumps(results,indent=2));print(name,result['task'],result['answer'][:250],flush=True)
 return result
def upload(path):
 with open(path,'rb') as f:r=requests.post(URL+'/api/single-images',files={'file':(Path(path).name,f)},timeout=90)
 r.raise_for_status();return r.json()['id']
stadium=upload(P.parent/'grounding_lab/samples/stadium.png')
v1=run('01-vqa-before',{'images':[stadium],'query':'How many stadiums are in this image?'})
catalog=requests.get(URL+'/api/samples',timeout=20).json()
temporal=next(s['id'] for s in catalog if s['id'].startswith('mci-') and any('build' in c.lower() for c in s.get('reference_captions',[])))
run('02-temporal',{'sample':temporal,'query':'Describe what changed between these dates.'})
run('03-water-india',{'sample':'flood-India_900498','query':'Map water using the optical and SAR images together.'})
run('04-water-bolivia',{'sample':'flood-Bolivia_103757','query':'Map water using the optical and SAR images together.'})
run('05-scene-fusion',{'sample':'ben-validation-33-69','query':'Identify land cover using optical and SAR together.'})
source=Path('/root/satquery/scenes/dehradun-sentinel2-20211125.tif');iid=upload(source)
ndvi=run('06-ndvi',{'images':[iid],'query':'Calculate NDVI coverage.','threshold':.5})
# Independent recomputation using exported NDVI values, not the displayed rounded percentage.
raw=requests.get(URL+'/api/runs/'+ndvi['id']+'/ndvi.tif',timeout=60).content
with rasterio.io.MemoryFile(raw) as mem:
 with mem.open() as ds:arr=ds.read(1)
valid=np.isfinite(arr);stats=ndvi['statistics'];assert int(valid.sum())==stats['valid_pixels'];assert int(((arr>=.5)&valid).sum())==stats['selected_pixels']
v2=run('07-vqa-after',{'images':[stadium],'query':'How many stadiums are in this image?'})
assert v1['answer']==v2['answer'],'VQA answer changed across workflow replay'
run('08-rural-urban',{'images':[stadium],'query':'Is this a rural/urban area?'})
checks={'ndvi_export_counts_match':True,'vqa_before_after_identical':True,'all_bundles_verified':True,'runs':len(results)}
(O/'checks.json').write_text(json.dumps(checks,indent=2));print('LIVE CHECKS',checks,flush=True)
