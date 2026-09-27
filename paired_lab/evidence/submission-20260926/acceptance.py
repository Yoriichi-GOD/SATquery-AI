"""Bounded, predeclared submission acceptance. No training or tuning."""
from pathlib import Path
import json,hashlib,random,re,sys,zipfile,io,time
import numpy as np
from PIL import Image
ROOT=Path('/mnt/c/Users/nrgen/.codex/scratch/SATquery AI')
OUT=Path(__file__).resolve().parent/'acceptance-20260926';OUT.mkdir(exist_ok=True)
DATA=Path('/root/satquery/paired-lab/levir-mci')
sys.path.insert(0,str(ROOT/'paired_lab'))
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for c in iter(lambda:f.read(8*1024*1024),b''):h.update(c)
 return h.hexdigest()
def save(n,d):(OUT/n).write_text(json.dumps(d,indent=2))
def freeze():
 if (OUT/'freeze.json').exists():raise RuntimeError('Already frozen; do not replace.')
 used=set();sources={}
 for p in ROOT.rglob('*'):
  if not p.is_file() or any(k in p.parts for k in ['.venv','.git','__pycache__']):continue
  if p.suffix.lower() in ['.json','.jsonl','.md','.py'] and p.stat().st_size<20_000_000:
   hits=set(re.findall(r'test_\d+\.png',p.read_text(errors='replace')))
   if hits:used|=hits;sources[str(p.relative_to(ROOT))]=sorted(hits)
 rows=json.loads((DATA/'metadata/LevirCCcaptions.json').read_text())['images']
 rng=random.Random(20260926);cases=[]
 for flag in [0,1]:
  pool=sorted([r for r in rows if r['split']=='test' and r['changeflag']==flag and r['filename'] not in used],key=lambda r:r['filename'])
  if len(pool)<20:raise RuntimeError('Insufficient unused cases')
  cases+=rng.sample(pool,20)
 with zipfile.ZipFile(DATA/'LEVIR-MCI-dataset.zip') as z:
  prior_hashes=set()
  for name in used:
   for layer in ['A','B']:
    try:prior_hashes.add(hashlib.sha256(z.read('LEVIR-MCI-dataset/images/test/'+layer+'/'+name)).hexdigest())
    except KeyError:pass
  selected=[]
  for r in cases:
   hashes={layer:hashlib.sha256(z.read('LEVIR-MCI-dataset/images/test/'+layer+'/'+r['filename'])).hexdigest() for layer in ['A','B','label']}
   if any(hashes[k] in prior_hashes for k in ['A','B']):raise RuntimeError('Prior byte-identical imagery encountered; no replacement selection')
   selected.append({'filename':r['filename'],'changeflag':r['changeflag'],'hashes':hashes})
 code={str(p.relative_to(ROOT)):sha(p) for folder in [ROOT,ROOT/'paired_lab',ROOT/'paired_lab/mci_vendor'] for p in folder.glob('*.py')}
 manifest=Path('/root/satquery/paired-lab/mci-model/manifest.json');model=json.loads(manifest.read_text())
 freeze={'created_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'seed':20260926,'cases':selected,'excluded_ids':sorted(used),'exclusion_sources':sources,'source_hashes':code,'model_manifest':model,'model_sha256':sha(Path(model['path'])),'metadata_sha256':sha(DATA/'metadata/LevirCCcaptions.json'),'protocol':{'task':'MCI road/building segmentation; raw captions retained but unscored','size':'40 locally unused official-test pairs, balanced 20 changed/20 unchanged','acceptance':{'road_iou_min':0.70,'building_iou_min':0.70,'unchanged_false_positive_pixel_fraction_max':0.01,'execution_failures_max':0},'threshold_basis':'Predeclared internal engineering floor for this bounded submission check, NOT an ISRO requirement or published benchmark threshold. No changes after results.','limits':'Local file-ID and exact compressed image-byte exclusions only. Geographic/source-scene independence and upstream model test exposure unknown. Does not establish full-system untouched acceptance or CDVQA performance.','decoding':'Existing greedy caption; segmentation argmax; no model or policy changes permitted'}}
 save('freeze.json',freeze);print('Frozen',len(selected),'cases; excluded',len(used),'prior IDs',flush=True)
def run():
 f=json.loads((OUT/'freeze.json').read_text())
 if (OUT/'results.json').exists():raise RuntimeError('Already evaluated; do not overwrite')
 for name,h in f['source_hashes'].items():
  if sha(ROOT/name)!=h:raise RuntimeError('Candidate changed: '+name)
 if sha(Path(f['model_manifest']['path']))!=f['model_sha256']:raise RuntimeError('Model changed')
 import mci
 results=[];start=time.perf_counter()
 with zipfile.ZipFile(DATA/'LEVIR-MCI-dataset.zip') as z:
  for c in f['cases']:
   arrays=[]
   for layer in ['A','B','label']:
    raw=z.read('LEVIR-MCI-dataset/images/test/'+layer+'/'+c['filename'])
    if hashlib.sha256(raw).hexdigest()!=c['hashes'][layer]:raise RuntimeError('Input changed')
    arrays.append(np.array(Image.open(io.BytesIO(raw))))
   a,b,g=arrays;g=g[:,:,0] if g.ndim==3 else g
   truth=np.zeros(g.shape,dtype=np.uint8);truth[g==128]=1;truth[g==255]=2
   if not set(np.unique(g))<={0,128,255}:raise RuntimeError('Unknown label encoding')
   t=time.perf_counter()
   try:
    caption,mask,probs,_=mci.infer(a,b,'cpu');cm=np.bincount((truth.astype(int)*3+mask).ravel(),minlength=9).reshape(3,3)
    np.savez_compressed(OUT/(c['filename']+'.npz'),prediction=mask,reference=truth)
    row={**c,'state':'complete','caption':caption,'confusion':cm.tolist(),'changed_pixels':int((mask>0).sum()),'seconds':time.perf_counter()-t}
   except Exception as e:row={**c,'state':'failed','error':str(e)}
   results.append(row);save('results.json',results)
   if len(results)%10==0:print('Acceptance',len(results),'/40',flush=True)
 cm=np.sum([r['confusion'] for r in results if r['state']=='complete'],axis=0);metrics={}
 for k,name in [(1,'road'),(2,'building')]:
  tp=int(cm[k,k]);fp=int(cm[:,k].sum()-tp);fn=int(cm[k,:].sum()-tp)
  metrics[name]={'tp':tp,'fp':fp,'fn':fn,'iou':tp/(tp+fp+fn) if tp+fp+fn else None,'f1':2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else None}
 neg=[r for r in results if r['state']=='complete' and r['changeflag']==0]
 fp=sum(r['changed_pixels'] for r in neg)/(len(neg)*256*256) if neg else 1
 failed=sum(r['state']!='complete' for r in results)
 passed=failed==0 and all(metrics[n]['iou'] is not None and metrics[n]['iou']>=.7 for n in ['road','building']) and fp<=.01
 save('summary.json',{'passed_internal_gate':passed,'n':len(results),'failures':failed,'metrics':metrics,'unchanged_false_positive_fraction':fp,'seconds':time.perf_counter()-start,'limits':f['protocol']['limits']})
 print((OUT/'summary.json').read_text(),flush=True)
if __name__=='__main__':{'freeze':freeze,'run':run}[sys.argv[1]]()
