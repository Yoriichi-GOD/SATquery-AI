from pathlib import Path
import sys,json,time,shutil,numpy as np
from PIL import Image
P=Path('/mnt/c/Users/nrgen/.codex/scratch/SATquery AI/paired_lab');sys.path.insert(0,str(P));import engine,mci
E=P/'evidence/resumed/mci';f=E/'evaluation.json';d=json.loads(f.read_text());shutil.copy2(f,E/'evaluation-gpu.json');start=time.perf_counter();caption_diff=0;pixel_diff=0
for i,r in enumerate(d['results']):
 o=E/r['file'].removesuffix('.png');a=np.asarray(Image.open(o/'before.png'));b=np.asarray(Image.open(o/'after.png'));caption,mask,_,_=mci.infer(a,b,'cpu')
 prior=np.asarray(Image.open(o/'prediction.png'));pixel_diff+=int((prior!=mask).sum());caption_diff+=caption!=r['raw_caption']
 gt=np.asarray(Image.open(o/'reference.png'))[:,:,0];truth=np.zeros(gt.shape,dtype=np.uint8);truth[gt==128]=1;truth[gt==255]=2
 r['gpu_caption']=r['raw_caption'];r['raw_caption']=caption;r['confusion_rows_reference_columns_prediction']=np.bincount((truth.astype(int)*3+mask).ravel(),minlength=9).reshape(3,3).tolist()
 Image.fromarray(mask).save(o/'prediction-cpu.png');r['predicted_class_pixels']={str(k):int((mask==k).sum()) for k in range(3)}
 no_change=any(s in caption.lower() for s in ['no change','no difference','nothing has changed','same as before','scenes seem identical','almost nothing','no obvious change','remain the same']);r['caption_changeflag_heuristic']=int(not no_change)
 (o/'result-cpu.json').write_text(json.dumps(r,indent=2))
 if i%10==0:print('CPU temporal',i+1,flush=True)
cm=np.array([r['confusion_rows_reference_columns_prediction'] for r in d['results']]).sum(0);d['confusion']=cm.tolist();d['class_iou']={str(k):float(cm[k,k]/(cm[k,:].sum()+cm[:,k].sum()-cm[k,k])) for k in range(3)}
d['caption_changeflag_agreement']['correct']=sum(r['reference_changeflag']==r['caption_changeflag_heuristic'] for r in d['results']);d['served_precision_verification']={'device':'float32 CPU','seconds':time.perf_counter()-start,'captions_different_from_GPU':caption_diff,'class_pixels_different_from_GPU':pixel_diff,'pixels_total':100*256*256}
f.write_text(json.dumps(d,indent=2));print(d['class_iou'],d['served_precision_verification'],flush=True)
