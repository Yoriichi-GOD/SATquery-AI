from pathlib import Path
import requests,json,time
R=Path('/mnt/c/Users/nrgen/.codex/scratch/SATquery AI');E=R/'grounding_lab/evidence/buildings-tiles';E.mkdir(exist_ok=True);B='http://127.0.0.1:8765/grounding';rows=[]
from PIL import Image
samples=[]
for scene in ['assam-monsoon','bengaluru-lake-city']:
 image=Image.open(R/'results/reliability-20260907/scenes'/scene/'rgb.png')
 for y in [0,256]:
  for x in [0,256]:
   d=E/(scene+f'-tile-{x}-{y}');d.mkdir(exist_ok=True);p=d/'rgb.png';image.crop((x,y,x+256,y+256)).save(p);samples.append(p)
for p in samples:
 for threshold in [.2]:
  name=p.parent.name;im=requests.post(B+'/api/images',files={'file':(name+'.png',p.read_bytes())});im.raise_for_status();q=requests.post(B+'/api/runs',json=dict(image_id=im.json()['id'],category='building',threshold=threshold,mode='both'));q.raise_for_status();rid=q.json()['id'];start=time.time()
  while time.time()-start<300:
   j=requests.get(B+'/api/runs/'+rid).json()
   if j['state']!='running':break
   time.sleep(.5)
  d=E/(name+'-'+str(threshold));d.mkdir(exist_ok=True);(d/'run.json').write_text(json.dumps(j,indent=2))
  if j['state']=='complete':
   for artifact,filename in [('source','source.png'),('boxes','boxes.png'),('outlines','outlines.png'),('bundle','evidence.zip')]:
    a=requests.get(B+f'/api/runs/{rid}/{artifact}');a.raise_for_status();(d/filename).write_bytes(a.content)
   z=j['result'];row=dict(scene=name,threshold=threshold,objects=z['objects'],raw=z['raw_candidates'],coverage=z['union_mask_percent'],capped=z['capped'],seconds=z['seconds'])
  else:row=dict(scene=name,threshold=threshold,error=j)
  rows.append(row);(E/'summary.json').write_text(json.dumps(rows,indent=2));print(row,flush=True)
