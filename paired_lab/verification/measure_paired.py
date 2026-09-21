import sys,json,time,gc,subprocess
from pathlib import Path
P=Path('/mnt/c/Users/nrgen/.codex/scratch/SATquery AI/paired_lab');sys.path.insert(0,str(P))
import engine as e
import torch,numpy as np,rasterio
OUT=P/'evidence/resumed';OUT.mkdir(exist_ok=True)
def gpu():return subprocess.check_output(['nvidia-smi','--query-gpu=memory.used,memory.total','--format=csv,noheader,nounits'],text=True).strip()
report={'gpu':torch.cuda.get_device_name(0),'measurements':[],'note':'Actual isolated GPU loads and batch-one inference, float32. Demo defaults remain CPU for paired models. Device total includes display/driver.'}
for kind in ['temporal','s1','s2','all']:
 gc.collect();torch.cuda.empty_cache();torch.cuda.reset_peak_memory_stats();before=gpu();start=time.perf_counter()
 net=(e.load_temporal() if kind=='temporal' else e.load_fusion(kind)).to('cuda').eval()
 if kind=='temporal':
  from PIL import Image
  a=np.asarray(Image.open(P/'samples/levir-test_102_0512_0000/before.tif'));b=np.asarray(Image.open(P/'samples/levir-test_102_0512_0000/after.tif'))
  xs=[torch.from_numpy(z.copy()).permute(2,0,1)[None].float().cuda()/127.5-1 for z in [a,b]]
 else:
  sample=next(z for z in json.loads((P/'samples/catalog.json').read_text()) if z['kind']=='optical_sar')
  bands={}
  for f in sample['files']:
   with rasterio.open(P/'samples'/sample['id']/f) as ds:bands.update(dict(zip(ds.descriptions,ds.read())))
  xs=[e.normalize(bands,{'s1':e.S1,'s2':e.S2,'all':e.S1+e.S2}[kind]).cuda()]
 with torch.inference_mode():y=net(*xs)
 torch.cuda.synchronize()
 item={'kind':kind,'checkpoint':e.MODELS[kind],'input_shapes':[list(x.shape) for x in xs],'load_and_infer_seconds':time.perf_counter()-start,'allocated_MiB':torch.cuda.memory_allocated()/2**20,'peak_allocated_MiB':torch.cuda.max_memory_allocated()/2**20,'peak_reserved_MiB':torch.cuda.max_memory_reserved()/2**20,'device_before_used_total_MiB':before,'device_after_used_total_MiB':gpu()}
 report['measurements'].append(item);print(json.dumps(item),flush=True)
 if kind=='all':
  baseline=y.sigmoid().cpu().numpy()[0];abl=[]
  for mode in ['zero_normalized_SAR','spatially_reversed_SAR']:
   x=xs[0].clone()
   if mode=='zero_normalized_SAR':x[:,:2]=0
   else:x[:,:2]=torch.flip(x[:,:2],[-1,-2])
   with torch.inference_mode():scores=net(x).sigmoid().cpu().numpy()[0]
   abl.append({'intervention':mode,'max_absolute_score_change':float(abs(scores-baseline).max()),'mean_absolute_score_change':float(abs(scores-baseline).mean()),'scores':dict(zip(e.CLASSES,map(float,scores)))})
  report['within_joint_checkpoint_SAR_ablation']={'sample':sample['id'],'baseline_scores':dict(zip(e.CLASSES,map(float,baseline))),'interventions':abl,'interpretation':'Nonzero changes show this joint checkpoint uses SAR values. Ablated inputs are interventions, not realistic sensor observations or proof that SAR improves accuracy.'}
  del x,scores
 net.cpu();del net,xs,y;gc.collect();torch.cuda.empty_cache()
 (OUT/'gpu-and-ablation.json').write_text(json.dumps(report,indent=2))
