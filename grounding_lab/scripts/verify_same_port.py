import sys,json,time,requests,hashlib,io,zipfile
from pathlib import Path
import numpy as np
from PIL import Image
R=Path('/mnt/c/Users/nrgen/.codex/scratch/SATquery AI/grounding_lab');B='http://127.0.0.1:8765/grounding';E=R/'evidence/same-port-http';E.mkdir(exist_ok=True)
rows=[]
for name,cat,mode in [('stadium','stadium','both'),('car','car','both'),('farmland','stadium','both'),('stadium','stadium','boxes')]:
 p=R/'samples'/f'{name}.png';r=requests.post(B+'/api/images',files={'file':(p.name,p.read_bytes())});r.raise_for_status();im=r.json()
 r=requests.post(B+'/api/runs',json=dict(image_id=im['id'],category=cat,threshold=.3,mode=mode));r.raise_for_status();rid=r.json()['id'];start=time.monotonic()
 # Verify a simultaneous job is rejected before loading another model.
 duplicate=requests.post(B+'/api/runs',json=dict(image_id=im['id'],category=cat));assert duplicate.status_code==409
 while time.monotonic()-start<300:
  j=requests.get(B+'/api/runs/'+rid).json()
  if j['state']!='running':break
  time.sleep(.3)
 assert j['state']=='complete',j
 out=E/f'{name}-{mode}';out.mkdir(exist_ok=True)
 artifacts={}
 for a in ['source','boxes','outlines','masks','instances','arrays','record','bundle']:
  r=requests.get(B+f'/api/runs/{rid}/{a}');r.raise_for_status();artifacts[a]=r.content
 with zipfile.ZipFile(io.BytesIO(artifacts['bundle'])) as z:assert z.testzip() is None
 masks=np.load(io.BytesIO(artifacts['arrays']))['masks'];report=j['result'];h,w=report['image']['height'],report['image']['width']
 assert masks.shape==(report['segmented_objects'],h,w)
 union=masks.any(axis=0) if len(masks) else np.zeros((h,w),bool)
 assert int(union.sum())==report['union_mask_pixels']
 labels=np.asarray(Image.open(io.BytesIO(artifacts['instances'])))
 assert np.array_equal(labels>0,union)
 assert labels.max(initial=0)<=report['objects']
 for i,d in enumerate(report['detections']):
  x1,y1,x2,y2=d['box_xyxy'];assert 0<=x1<x2<=w and 0<=y1<y2<=h
  if mode=='both':assert int(masks[i].sum())==d['mask_pixels']
 (out/'run.json').write_text(json.dumps(j,indent=2));(out/'evidence.zip').write_bytes(artifacts['bundle'])
 rows.append(dict(case=name,mode=mode,run_id=rid,objects=report['objects'],segmented=report['segmented_objects'],artifacts=8,mask_consistency_passed=True,seconds=report['seconds']))
 (E/'summary.json').write_text(json.dumps(rows,indent=2));print(rows[-1],flush=True)
checks=[]
for payload in [dict(image_id=im['id'],category='unknown'),dict(image_id=im['id'],category='stadium',threshold=.99),dict(image_id='../',category='stadium'),dict(image_id=im['id'],category='stadium',mode='fake')]:
 r=requests.post(B+'/api/runs',json=payload);assert r.status_code in [404,422];checks.append(dict(payload=payload,status=r.status_code))
r=requests.post(B+'/api/images',files={'file':('bad.png',b'not an image')});assert r.status_code==400
r=requests.post(B+'/api/runs',headers={'Origin':'https://example.com'},json=dict(image_id=im['id'],category='stadium'));assert r.status_code==403
for name,digest in json.loads((R/'preserved-main-sha256.json').read_text()).items():
 if name in ['server.py','web/index.html','web/app.js']:continue
 assert hashlib.sha256((R.parent/name).read_bytes()).hexdigest()==digest,name
(E/'safety-checks.json').write_text(json.dumps(dict(invalid_selections=checks,invalid_image=400,cross_origin=403,analytical_files_unchanged=True),indent=2));print('Input, artifact, concurrency and main-source preservation checks passed.',flush=True)
