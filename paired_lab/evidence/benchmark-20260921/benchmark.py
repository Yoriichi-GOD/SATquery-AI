from pathlib import Path
import sys,json,hashlib,time,random,zipfile,io,subprocess,platform,resource
import numpy as np
from PIL import Image
OUT=Path(__file__).resolve().parent
ROOT=Path('/mnt/c/Users/nrgen/.codex/scratch/SATquery AI')
sys.path.insert(0,str(ROOT/'paired_lab'))
import engine,flood,mci,torch,rasterio
DATA=engine.DATA
def save(name,data): (OUT/name).write_text(json.dumps(data,indent=2,default=str))
def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(2**20),b''):h.update(b)
 return h.hexdigest()
def binary(p,g,valid):
 return [int((p&g&valid).sum()),int((p&~g&valid).sum()),int((~p&g&valid).sum()),int((~p&~g&valid).sum())]
def metrics(v):
 tp,fp,fn,tn=map(int,v)
 return dict(tp=tp,fp=fp,fn=fn,tn=tn,iou=tp/(tp+fp+fn) if tp+fp+fn else None,f1=2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else None,precision=tp/(tp+fp) if tp+fp else None,recall=tp/(tp+fn) if tp+fn else None)
def freeze():
 files={}
 for folder in [ROOT,ROOT/'paired_lab',ROOT/'tests',ROOT/'paired_lab/web']:
  for p in sorted(folder.iterdir()):
   if p.is_file() and p.suffix in ['.py','.js','.css','.html','.json']:files[str(p.relative_to(ROOT))]=sha(p)
 models=json.loads((DATA/'models.json').read_text());models['mci']=json.loads(mci.MANIFEST.read_text());models['water']={'path':str(flood.WEIGHTS),'sha256':sha(flood.WEIGHTS)}
 for v in models.values():
  p=Path(v['path']); p=p/'model.safetensors' if p.is_dir() else p
  v['observed_sha256']=sha(p)
 manifest={'created_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'source':files,'models':models,'python':sys.version,'platform':platform.platform(),'cpu':subprocess.getoutput('lscpu'),'gpu':subprocess.getoutput('nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv'),'packages':subprocess.getoutput(sys.executable+' -m pip freeze'),'protocol':{'seed':20260921,'water':'All 90 test +15 Bolivia cases; already evaluated historically; regression, not untouched test. CPU float32; all three modalities; threshold >=0.5.','temporal':'100 official test pairs, balanced changed/unchanged; exclude prior 100-case trial filenames. Public checkpoint upstream test-selection exposure not established. Not CDVQA.','land_cover':'All locally available nontraining BENv2 fixtures; narrow geographic scope.','changes':'No model or prompt tuning during benchmark. Forecasting removed from scope; refusal tests retained.'}}
 save('baseline.json',manifest)
def water():
 splits=json.loads((flood.DATA/'splits.json').read_text());cases=[(split,sid) for split in ['test','bolivia'] for sid in sorted(splits[split])]
 assert not (set(splits['train']) & {sid for _,sid in cases}); assert not(set(splits['valid']) & {sid for _,sid in cases})
 save('water-manifest.json',{'cases':cases,'splits_sha256':sha(flood.DATA/'splits.json'),'checkpoint_sha256':sha(flood.WEIGHTS)})
 started=time.perf_counter();net,ckpt=flood.load();load_seconds=time.perf_counter()-started;rows=[]
 for split,sid in cases:
  t=time.perf_counter();arr=[];hashes={}
  for layer in ['S1Hand','S2Hand','LabelHand']:
   p=flood.DATA/layer/(sid+'_'+layer+'.tif');hashes[layer]=sha(p)
   with rasterio.open(p) as ds:arr.append(ds.read() if layer=='LabelHand' else ds.read(masked=True).astype('float32').filled(np.nan))
  x,finite=flood.prepare(*arr[:2]);truth=arr[2][0]==1;valid=finite&(arr[2][0]>=0);tensor=torch.from_numpy(x)[None];preds={};scores={};duration={}
  for mode in ['s1','s2','all']:
   t0=time.perf_counter()
   with torch.inference_mode():pred=net(flood.available(tensor,mode)).softmax(1)[0,1].numpy()>=.5
   duration[mode]=time.perf_counter()-t0;preds[mode]=pred;scores[mode]=metrics(binary(pred,truth,valid))
  row={'split':split,'id':sid,'event':sid.rsplit('_',1)[0],'hashes':hashes,'valid_pixels':int(valid.sum()),'metrics':scores,'inference_seconds':duration,'total_seconds':time.perf_counter()-t,'disagreement_pixels':int(((preds['s1']!=preds['s2'])&valid).sum())};rows.append(row)
  with (OUT/'water-rows.jsonl').open('a') as f:f.write(json.dumps(row)+'\n')
  if len(rows)%10==0:print('water',len(rows),'/',len(cases),flush=True)
 groups={}
 for group in sorted({r['split'] for r in rows}|{r['event'] for r in rows}):
  rr=[r for r in rows if group in [r['split'],r['event']]]
  groups[group]={'n':len(rr),'modalities':{m:metrics(np.sum([[r['metrics'][m][k] for k in ['tp','fp','fn','tn']] for r in rr],axis=0)) for m in ['s1','s2','all']}}
 save('water-summary.json',{'groups':groups,'load_seconds':load_seconds,'elapsed_seconds':time.perf_counter()-started,'peak_process_rss_MiB':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,'scope':'Previously evaluated test/holdout data. No new untouched-test claim. Standalone CPU process, not service end-to-end timing.'})
def temporal():
 D=DATA/'levir-mci';allrows=json.loads((D/'metadata/LevirCCcaptions.json').read_text())['images'];previous=json.loads((ROOT/'paired_lab/evidence/resumed/mci/evaluation.json').read_text());used={r['file'] for r in previous['results']};rng=random.Random(20260921)
 cases=sum([rng.sample(sorted([r for r in allrows if r['split']=='test' and r['changeflag']==flag and r['filename'] not in used],key=lambda r:r['filename']),50) for flag in [0,1]],[])
 save('temporal-manifest.json',{'cases':cases,'excluded_previous_files':sorted(used),'archive_sha256':sha(D/'LEVIR-MCI-dataset.zip'),'scope':'New to this local evaluation; upstream checkpoint test exposure unknown; balanced custom subset, not full CDVQA.'})
 rows=[];started=time.perf_counter();mci.load('cpu');load_seconds=time.perf_counter()-started
 with zipfile.ZipFile(D/'LEVIR-MCI-dataset.zip') as z:
  def read(r,folder):return np.asarray(Image.open(io.BytesIO(z.read('LEVIR-MCI-dataset/images/test/'+folder+'/'+r['filename']))))
  for row in cases:
   a,b,g=[read(row,f) for f in ['A','B','label']];g=g[:,:,0] if g.ndim==3 else g;assert set(np.unique(g))<={0,128,255};truth=np.zeros(g.shape,dtype=np.uint8);truth[g==128]=1;truth[g==255]=2
   t=time.perf_counter();caption,mask,probs,_=mci.infer(a,b,'cpu');seconds=time.perf_counter()-t;cm=np.bincount((truth.astype(int)*3+mask).ravel(),minlength=9).reshape(3,3)
   item={'file':row['filename'],'reference_changeflag':row['changeflag'],'caption':caption,'references':[s['raw'] for s in row['sentences']],'confusion':cm.tolist(),'changed_pixels':int((mask>0).sum()),'seconds':seconds};rows.append(item)
   with (OUT/'temporal-rows.jsonl').open('a') as f:f.write(json.dumps(item)+'\n')
   if len(rows)<=4:
    folder=OUT/'temporal-examples'/row['filename'];folder.mkdir(parents=True,exist_ok=True)
    for name,img in [('before',a),('after',b),('reference',truth),('prediction',mask)]:Image.fromarray(img).save(folder/(name+'.png'))
   if len(rows)%10==0:print('temporal',len(rows),'/100',flush=True)
  controls=[]
  for row in cases[:5]:
   a=read(row,'A')
   for name,b in [('identical',a),('brightness',np.clip(a.astype(float)*1.1+10,0,255).astype('uint8'))]:
    c,m,_,_=mci.infer(a,b,'cpu');controls.append({'file':row['filename'],'control':name,'changed_pixels':int((m>0).sum()),'caption':c})
 cm=np.sum([r['confusion'] for r in rows],axis=0);scores={}
 for k,name in enumerate(['unchanged','road','building']):
  tp=cm[k,k];fp=cm[:,k].sum()-tp;fn=cm[k,:].sum()-tp;tn=cm.sum()-tp-fp-fn;scores[name]=metrics([tp,fp,fn,tn])
 save('temporal-summary.json',{'n':len(rows),'classes':scores,'confusion':cm.tolist(),'controls':controls,'unchanged_false_positive_pixels':sum(r['changed_pixels'] for r in rows if not r['reference_changeflag']),'unchanged_total_pixels':50*256*256,'load_seconds':load_seconds,'elapsed_seconds':time.perf_counter()-started,'peak_process_rss_MiB':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,'caption_scoring':'Raw captions and references preserved; no automatic factuality score assigned.'})
def land():
 import pandas as pd,lmdb
 from safetensors.numpy import load
 base=DATA/'ConfigILM/configilm/extra/mock_data/BENv2';df=pd.read_parquet(base/'metadata.parquet');env=lmdb.open(str(base/'BigEarthNet-V2-LMDB'),readonly=True,lock=False);rows=[]
 for _,r in df.iterrows():
  if r['split']=='train':continue
  with env.begin() as tx:bands={**load(tx.get(r['s1_name'].encode())),**load(tx.get(r['patch_id'].encode()))}
  bands={k:bands[k] for k in engine.S1+engine.S2};out=OUT/'land-artifacts'/r['patch_id'];result=engine.fusion(bands,out);truth=np.array([c in r['labels'] for c in engine.CLASSES]);valid=np.ones(19,dtype=bool)
  rows.append({'id':r['patch_id'],'split':r['split'],'references':list(r['labels']),'metrics':{m:metrics(binary(np.array([scores[c]>=.5 for c in engine.CLASSES]),truth,valid)) for m,scores in result['scores'].items()},'seconds':result['seconds']})
 env.close();save('land-summary.json',{'n':len(rows),'rows':rows,'modalities':{m:metrics(np.sum([[r['metrics'][m][k] for k in ['tp','fp','fn','tn']] for r in rows],axis=0)) for m in ['s1','s2','all']},'scope':'Existing real BENv2 fixtures; narrow scene coverage, not broad generalization.'});print('land',len(rows),flush=True)
if __name__=='__main__':
 globals()[sys.argv[1]]()
