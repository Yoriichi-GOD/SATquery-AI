
import sys,json,time,csv,collections,math,shutil,platform,subprocess,importlib.metadata as md,hashlib,io,tempfile
from pathlib import Path
import requests,numpy as np,rasterio,tifffile
from PIL import Image
from safetensors import safe_open
p=Path(__file__).resolve().parents[2];h=p/'ppt_handoff';sys.path.insert(0,str(p))
import geo
exp=Path('/root/satquery/experiments/lora-pilot-v1')
def save(n,v):(h/n).write_text(json.dumps(v,indent=2))
def csvout(n,rows):
 with (h/n).open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
r=json.loads((exp/'result.json').read_text());save('raw/training_result.json',r);csvout('metrics/training_loss.csv',r['losses'])
for name in ['baseline_dev_predictions.jsonl','adapted_dev_predictions.jsonl','adapter/adapter_config.json']:
 shutil.copy2(exp/name,h/'raw'/Path(name).name)
for name in ['learning_manifest.json','train.jsonl','dev.jsonl']:shutil.copy2(Path('/root/satquery/data')/name,h/'raw'/name)
for name in ['calibration-audit.md','calibration-comparison.json','independent-ndvi-check.json','independent-validation.md','ndvi-integration.json','ndvi-invalid-v1.json']:
 shutil.copy2(p/'results'/name,h/'raw'/name)
for name in ['scene-manifest.json','reference-item.json']:shutil.copy2(Path('/root/satquery/scenes')/name,h/'raw'/name)
shutil.copy2(p/'results/ndvi-visual-validation.png',h/'exports/visual-validation.png')
base=[json.loads(x) for x in (exp/'baseline_dev_predictions.jsonl').read_text().splitlines()]
adapt=[json.loads(x) for x in (exp/'adapted_dev_predictions.jsonl').read_text().splitlines()]
pairs=[]
for b,a in zip(base,adapt):
 assert b['question_id']==a['question_id']
 kind='unchanged'
 if not b['correct'] and a['correct']:kind='semantic-label gain' if b['valid_format'] else 'format-confounded gain'
 if b['correct'] and not a['correct']:kind='regression'
 pairs.append({'question_id':b['question_id'],'image_id':b['image_id'],'category':b['category'],'question':b['question'],'reference':b['answer'],'base':b['prediction'],'adapter':a['prediction'],'base_correct':b['correct'],'adapter_correct':a['correct'],'base_valid_format':b['valid_format'],'kind':kind,'image':b['image']})
csvout('metrics/all_prediction_comparisons.csv',pairs)
cats=[]
for c in ['rural_urban','presence','comp']:
 rows=[x for x in pairs if x['category']==c];counts=collections.Counter(x['reference'] for x in rows)
 cats.append({'category':c,'n':len(rows),'base_correct':sum(x['base_correct'] for x in rows),'adapter_correct':sum(x['adapter_correct'] for x in rows),'dev_majority_correct':max(counts.values()),'labels':json.dumps(counts)})
csvout('metrics/evaluation.csv',cats)
chosen=[]
for kind,n in [('semantic-label gain',5),('regression',2),('format-confounded gain',2)]:
 chosen += [x for x in pairs if x['kind']==kind][:n]
for x in chosen:
 name=f"image-{x['image_id']}.png";shutil.copy2(x['image'],h/'examples'/name);x['image']='examples/'+name
save('examples/selected.json',chosen)
snapshot=next(Path('/root/.cache/huggingface/hub/models--AdaptLLM--remote-sensing-Qwen2-VL-2B-Instruct/snapshots').glob('*'))
params=0
for f in snapshot.glob('*.safetensors'):
 with safe_open(f,framework='pt',device='cpu') as sf:
  for k in sf.keys():params+=math.prod(sf.get_slice(k).get_shape())
import torch
versions={n:md.version(n) for n in ['torch','transformers','peft','accelerate','rasterio','pyproj','fastapi','uvicorn','numpy','Pillow','tifffile','python-multipart']}
system={'python':sys.version,'packages':versions,'gdal':rasterio.__gdal_version__,'cuda_torch_build':torch.version.cuda,'platform':platform.platform(),'cpu':subprocess.run(['lscpu'],capture_output=True,text=True).stdout,'memory':Path('/proc/meminfo').read_text(),'gpu':subprocess.run(['nvidia-smi'],capture_output=True,text=True).stdout,'node':subprocess.run(['sh','-c','command -v node && node --version'],capture_output=True,text=True).stdout or 'Not installed in WSL; not used by app','checkpoint_tensor_elements':params,'checkpoint_files_bytes':sum(f.stat().st_size for f in snapshot.iterdir() if f.is_file()),'adapter_bytes':sum(f.stat().st_size for f in (exp/'adapter').iterdir() if f.is_file()),'dev_image_dimensions':Image.open(base[0]['image']).size}
save('metrics/system.json',system)
scene=Path('/root/satquery/scenes/dehradun-sentinel2-20211125.tif')
data=tifffile.imread(scene);run=json.loads((p/'results/ndvi-integration.json').read_text())
out=Path('/root/satquery/app-data/runs')/run['id']
pipeline=tifffile.imread(out/'ndvi.tif')
pix=[]
for row,col in [(0,0),(50,50),(100,200),(150,350),(200,250),(250,300),(300,150),(350,400),(450,100),(511,511)]:
 red=float(data[row,col,0]);nir=float(data[row,col,3]);manual=(nir-red)/(nir+red);v=float(pipeline[row,col])
 pix.append({'row':row,'column':col,'red':red,'nir':nir,'manual_ndvi':manual,'pipeline_ndvi':v,'absolute_difference':abs(manual-v)})
csvout('metrics/ndvi_audit.csv',pix)
thresholds=[{'threshold':t,'selected_pixels':int((pipeline>=t).sum()),'percent':float(100*(pipeline>=t).mean())} for t in [.3,.5,.7]]
assert thresholds[0]['selected_pixels']>=thresholds[1]['selected_pixels']>=thresholds[2]['selected_pixels']
csvout('metrics/thresholds.csv',thresholds);save('metrics/dehradun_metadata.json',run['image']['geo'])
shutil.copy2(out/'ndvi.tif',h/'exports/ndvi.tif')
shutil.copy2(scene,h/'exports/source-calibrated.tif')
shutil.copy2(out/'overlay.png',h/'exports/overlay-transparent.png')
Image.fromarray(((pipeline>=.5)*255).astype('uint8')).save(h/'exports/threshold-mask.png')
for name,indices in [('rgb',[0,1,2]),('false-colour',[3,0,1])]:
 arr=[]
 for k in indices:
  v=data[:,:,k];lo,hi=np.percentile(v,[2,98]);arr.append(np.clip((v-lo)/(hi-lo),0,1))
 Image.fromarray((np.stack(arr,-1)*255).astype('uint8')).save(h/'exports'/f'{name}.png')
rgb=Image.open(h/'exports/rgb.png').convert('RGBA');ol=Image.open(out/'overlay.png');Image.alpha_composite(rgb,ol).save(h/'exports/evidence-overlay.png')
# Twenty serial HTTP jobs, each reading TIFF and writing output. OS cache is not flushed.
b='http://127.0.0.1:8765'
upload=requests.post(b+'/api/images',files={'file':('benchmark.tif',scene.read_bytes(),'image/tiff')});upload.raise_for_status()
iid=upload.json()['id'];times=[]
for i in range(20):
 start=time.perf_counter();resp=requests.post(b+'/api/ndvi',data={'image_id':iid,'threshold':.5});resp.raise_for_status();rid=resp.json()['id']
 while True:
  j=requests.get(b+'/api/runs/'+rid).json()
  if j['state'] in ['complete','error']:break
  time.sleep(.01)
 assert j['state']=='complete'
 times.append({'repetition':i+1,'server_reported_seconds':j['seconds'],'client_submit_poll_seconds':time.perf_counter()-start})
csvout('metrics/ndvi_timing.csv',times)
stats={}
for key in ['server_reported_seconds','client_submit_poll_seconds']:
 a=np.array([r[key] for r in times]);stats[key]={k:float(v) for k,v in [('mean',a.mean()),('median',np.median(a)),('p95',np.percentile(a,95)),('min',a.min()),('max',a.max())]}
save('metrics/ndvi_timing_summary.json',stats)
print(json.dumps({'changes':dict(collections.Counter(x['kind'] for x in pairs)),'categories':cats,'system':{k:system[k] for k in ['checkpoint_tensor_elements','checkpoint_files_bytes','adapter_bytes','dev_image_dimensions','gdal','node']},'timings':stats,'thresholds':thresholds},indent=2))
