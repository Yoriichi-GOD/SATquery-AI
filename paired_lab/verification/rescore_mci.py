import json,numpy as np,shutil
from pathlib import Path
from PIL import Image
P=Path('/mnt/c/Users/nrgen/.codex/scratch/SATquery AI/paired_lab/evidence/resumed/mci');f=P/'evaluation.json';d=json.loads(f.read_text());shutil.copy2(f,P/'evaluation-incorrect-palette-superseded.json')
for r in d['results']:
 o=P/r['file'].removesuffix('.png');gt=np.asarray(Image.open(o/'reference.png'))[:,:,0];truth=np.zeros(gt.shape,dtype=np.uint8);truth[gt==128]=1;truth[gt==255]=2
 assert set(np.unique(gt))<={0,128,255}
 mask=np.asarray(Image.open(o/'prediction.png'));cm=np.bincount((truth.astype(int)*3+mask).ravel(),minlength=9).reshape(3,3)
 r['confusion_rows_reference_columns_prediction']=cm.tolist();(o/'result.json').write_text(json.dumps(r,indent=2))
cm=np.array([r['confusion_rows_reference_columns_prediction'] for r in d['results']]).sum(0);d['confusion']=cm.tolist();d['class_iou']={str(k):float(cm[k,k]/(cm[k,:].sum()+cm[:,k].sum()-cm[k,k])) for k in range(3)}
d['label_encoding']='Verified against publisher data/LEVIR_MCI.py: grayscale 0 unchanged, 128 road, 255 building. Initial incorrect RGB-palette scoring is superseded, preserved separately.'
f.write_text(json.dumps(d,indent=2));print(d['class_iou']);print(d['caption_changeflag_agreement'])
