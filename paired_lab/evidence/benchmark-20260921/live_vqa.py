from pathlib import Path
import json,random,hashlib,zipfile,io,time,re,requests,subprocess
from PIL import Image
OUT=Path(__file__).resolve().parent;DATA=Path('/root/satquery/evaluation');ROOT=Path('/mnt/c/Users/nrgen/.codex/scratch/SATquery AI');BASE='http://127.0.0.1:8767'
def save(n,d):(OUT/n).write_text(json.dumps(d,indent=2))
def run(image,question):
 t=time.perf_counter();r=requests.post(BASE+'/api/single-images',files={'file':(image.name,image.read_bytes())},timeout=60)
 if r.status_code==404:r=requests.post(BASE+'/api/images',files={'file':(image.name,image.read_bytes())},data={'modality':'optical'},timeout=60)
 r.raise_for_status();record=r.json();r=requests.post(BASE+'/api/analyze',json={'images':[record['id']],'query':question,'threshold':.5},timeout=60)
 if not r.ok:return {'state':'refused','detail':r.json(),'end_to_end_seconds':time.perf_counter()-t}
 job=r.json()
 for _ in range(1800):
  d=requests.get(BASE+'/api/jobs/'+job['id'],timeout=30).json()
  if d['state'] in ['complete','failed']:break
  time.sleep(.3)
 d['end_to_end_seconds']=time.perf_counter()-t
 if d['state']=='complete':
  zraw=requests.get(BASE+'/api/runs/'+job['id']+'/evidence.zip',timeout=60).content
  with zipfile.ZipFile(io.BytesIO(zraw)) as z:
   originals=[n for n in z.namelist() if n.startswith('input-1.')];d['archive_verified']=z.testzip() is None and len(originals)==1 and z.read(originals[0])==image.read_bytes()
  (OUT/'live-artifacts').mkdir(exist_ok=True);(OUT/'live-artifacts'/(job['id']+'.zip')).write_bytes(zraw)
 return d
def main():
 qs=json.loads((DATA/'LR_split_test_questions.json').read_text())['questions'];ans={r['id']:r for r in json.loads((DATA/'LR_split_test_answers.json').read_text())['answers']};ims={r['id']:r for r in json.loads((DATA/'LR_split_test_images.json').read_text())['images']}
 used={json.loads(line)['image_id'] for line in (DATA/'eval_v1.jsonl').read_text().splitlines()};old=ROOT/'results/reliability-20260907/vqa/frozen-cases.json'
 if old.exists():used|={c['image_id'] for c in json.loads(old.read_text())['cases'] if 'image_id' in c}
 train=[json.loads(line) for split in ['train','dev'] for line in Path('/root/satquery/data/'+split+'.jsonl').read_text().splitlines()];scenes={r['source_scene'] for r in train};rng=random.Random(20260921);cases=[]
 for category,answer in [('rural_urban','rural'),('rural_urban','urban'),('presence','no'),('presence','yes')]:
  pool=[q for q in qs if q.get('active') and q['type']==category and ans[q['answers_ids'][0]]['answer']==answer];rng.shuffle(pool);count=0
  for q in pool:
   if q['img_id'] in used:continue
   scene=ims[q['img_id']]['original_name'].rsplit('_',1)[0]
   if scene in scenes:continue
   if category=='presence' and re.search(r'commercial|residential|left|right|top|bottom|medium|small|large',q['question']):continue
   cases.append({'image_id':q['img_id'],'question_id':q['id'],'question':'Is this image rural or urban?' if category=='rural_urban' else q['question'],'reference':answer,'category':category,'source_scene':scene});used.add(q['img_id']);count+=1
   if count==12:break
  print('Selected',category,answer,count,flush=True)
 imagefolder=OUT/'vqa-inputs';imagefolder.mkdir(exist_ok=True)
 with zipfile.ZipFile(DATA/'Images_LR.zip') as z:
  for c in cases:
   p=imagefolder/(str(c['image_id'])+'.png');Image.open(io.BytesIO(z.read('Images_LR/'+str(c['image_id'])+'.tif'))).convert('RGB').save(p);c['image']=str(p);c['sha256']=hashlib.sha256(p.read_bytes()).hexdigest()
 save('vqa-manifest.json',{'seed':20260921,'cases':cases,'scope':'Up to 12 per answer/category RSVQA-LR official test questions; availability-limited, not necessarily balanced; local prior image IDs and local training source scenes excluded. Upstream model pretraining exposure unknown. Not full benchmark; published labels may be noisy. Original presence wording retained; refusals count separately.'})
 rows=[]
 for c in cases:
  d=run(Path(c['image']),c['question']);answer=d.get('result',{}).get('answer','');normal=re.sub(r'[.!?]+$','',' '.join(answer.lower().strip().split()));row={**c,'run':d,'normalized':normal,'exact_correct':normal==c['reference']};rows.append(row)
  with (OUT/'vqa-rows.jsonl').open('a') as f:f.write(json.dumps(row)+'\n')
  print('VQA',len(rows),d['state'],repr(answer),flush=True)
 save('vqa-summary.json',{'n':len(rows),'complete':sum(r['run']['state']=='complete' for r in rows),'exact_correct':sum(r['exact_correct'] for r in rows),'categories':{k:{'n':sum(r['category']==k for r in rows),'correct':sum(r['exact_correct'] for r in rows if r['category']==k)} for k in ['presence','rural_urban']}})
if __name__=='__main__':main()

