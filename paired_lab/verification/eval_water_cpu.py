from pathlib import Path
import sys,json,time,shutil
P=Path('/mnt/c/Users/nrgen/.codex/scratch/SATquery AI/paired_lab');sys.path.insert(0,str(P))
import engine,flood,torch,numpy as np,rasterio
D=flood.DATA;report=json.loads((D/'training/evaluation.json').read_text());shutil.copy2(D/'training/evaluation.json',D/'training/evaluation-mixed-precision.json')
net,ckpt=flood.load();splits=json.loads((D/'splits.json').read_text());start=time.perf_counter()
def metric(v):
 tp,fp,fn,tn=map(int,v)
 return {'tp':tp,'fp':fp,'fn':fn,'tn':tn,'water_iou':tp/(tp+fp+fn) if tp+fp+fn else None,'water_f1':2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else None}
for split in ['test','bolivia']:
 total={m:np.zeros(4,dtype=np.int64) for m in ['s1','s2','all']};rows=[]
 for i,sid in enumerate(splits[split]):
  arrays=[]
  for layer in ['S1Hand','S2Hand','LabelHand']:
   with rasterio.open(D/layer/(sid+'_'+layer+'.tif')) as ds:arrays.append(ds.read() if layer=='LabelHand' else ds.read(masked=True).astype('float32').filled(np.nan))
  x,finite=flood.prepare(*arrays[:2]);y=arrays[2][0];valid=finite&(y>=0);truth=y==1;t=torch.from_numpy(x)[None];row={'sample':sid}
  for m in total:
   with torch.inference_mode():pred=net(flood.available(t,m)).argmax(1)[0].numpy()==1
   v=np.array([(pred&truth&valid).sum(),(pred&~truth&valid).sum(),(~pred&truth&valid).sum(),(~pred&~truth&valid).sum()]);total[m]+=v;row[m]=metric(v)
  rows.append(row)
  if i%15==0:print('CPU',split,i+1,flush=True)
 report[split]={'aggregate':{m:metric(v) for m,v in total.items()},'samples':rows}
 print(split,report[split]['aggregate'],flush=True)
report['evaluation_precision']='float32 CPU, same normalization/nodata/model execution as served water mapping';report['cpu_evaluation_seconds']=time.perf_counter()-start;report['selected_epoch']=ckpt['epoch']
(D/'training/evaluation.json').write_text(json.dumps(report,indent=2));(P/'evidence/resumed/water-evaluation.json').write_text(json.dumps(report,indent=2))
print('CPU evaluation complete',flush=True)
