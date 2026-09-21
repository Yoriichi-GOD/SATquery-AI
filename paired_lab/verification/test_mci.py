from pathlib import Path
import sys,json,zipfile,io,random,time
P=Path('/mnt/c/Users/nrgen/.codex/scratch/SATquery AI/paired_lab');sys.path.insert(0,str(P))
import engine,mci,torch,numpy as np
from PIL import Image
D=Path('/root/satquery/paired-lab/levir-mci');E=P/'evidence/resumed/mci';E.mkdir(exist_ok=True)
rows=json.loads((D/'metadata/LevirCCcaptions.json').read_text())['images'];test=[r for r in rows if r['split']=='test'];rng=random.Random(42)
selected=sum([rng.sample([r for r in test if r['changeflag']==flag],50) for flag in [0,1]],[])
report={'selection':'50 changed and 50 unchanged official test pairs, random seed 42; no local tuning on test','dataset_manifest':json.loads((D/'manifest.json').read_text()),'results':[],'controls':[]}
torch.cuda.reset_peak_memory_stats();start=time.perf_counter()
with zipfile.ZipFile(D/'LEVIR-MCI-dataset.zip') as z:
 def read(row,folder):return np.asarray(Image.open(io.BytesIO(z.read('LEVIR-MCI-dataset/images/test/'+folder+'/'+row['filename']))))
 for i,row in enumerate(selected):
  a=read(row,'A');b=read(row,'B');gt=read(row,'label')
  if i==0:print('REFERENCE MASK',gt.shape,np.unique(gt),flush=True)
  caption,mask,probs,checks=mci.infer(a,b,'cuda')
  out=E/row['filename'].removesuffix('.png');out.mkdir(exist_ok=True)
  for n,v in [('before.png',a),('after.png',b),('reference.png',gt),('prediction.png',mask)]:Image.fromarray(v).save(out/n)
  # Publisher masks are grayscale RGB: 0 unchanged, 128 roads, 255 buildings.
  gray=gt[:,:,0] if gt.ndim==3 else gt
  truth=np.zeros(gray.shape,dtype=np.uint8);truth[gray==128]=1;truth[gray==255]=2
  confusion=np.bincount((truth.astype(int)*3+mask).ravel(),minlength=9).reshape(3,3)
  no_change=any(s in caption.lower() for s in ['no change','no difference','nothing has changed','same as before','scenes seem identical','almost nothing','no obvious change','remain the same'])
  result={'file':row['filename'],'reference_changeflag':row['changeflag'],'raw_caption':caption,'reference_captions':[s['raw'] for s in row['sentences']],'caption_changeflag_heuristic':int(not no_change),'confusion_rows_reference_columns_prediction':confusion.tolist(),'predicted_class_pixels':{str(k):int((mask==k).sum()) for k in [0,1,2]}}
  report['results'].append(result);(out/'result.json').write_text(json.dumps(result,indent=2))
  if i==0:
   for name,bb in [('identical',a),('brightness_contrast',np.clip((a.astype(float)-127.5)*1.2+127.5+15,0,255).astype(np.uint8))]:
    c,m,_,_=mci.infer(a,bb,'cuda');report['controls'].append({'name':name,'raw_caption':c,'changed_pixels':int((m>0).sum())})
  if i%10==0:print('MCI',i+1,caption,flush=True)
  (E/'evaluation.json').write_text(json.dumps(report,indent=2))
report.update(seconds=time.perf_counter()-start,peak_allocated_MiB=torch.cuda.max_memory_allocated()/2**20,peak_reserved_MiB=torch.cuda.max_memory_reserved()/2**20,load_checks=checks)
cm=np.array([r['confusion_rows_reference_columns_prediction'] for r in report['results']]).sum(0)
report['confusion']=cm.tolist();report['class_iou']={str(k):float(cm[k,k]/(cm[k,:].sum()+cm[:,k].sum()-cm[k,k])) for k in range(3)}
report['caption_changeflag_agreement']={'correct':sum(r['reference_changeflag']==r['caption_changeflag_heuristic'] for r in report['results']),'total':100,'warning':'Lexical change/no-change agreement only, not caption factual accuracy.'}
(E/'evaluation.json').write_text(json.dumps(report,indent=2));print('FINAL',json.dumps({k:v for k,v in report.items() if k not in ['results','load_checks','dataset_manifest']}),flush=True)
