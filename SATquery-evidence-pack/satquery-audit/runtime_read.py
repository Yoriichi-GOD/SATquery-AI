import json, hashlib, urllib.request, sys, platform, importlib.metadata, zipfile
from pathlib import Path
import numpy as np
R=Path('/mnt/c/Users/nrgen/.codex/scratch/SATquery AI')
O=Path('/mnt/c/Users/nrgen/.codex/visualizations/2026/09/19/01a0b9f9-b20e-71a2-b139-ca9ab926b94e/satquery-audit')
d={'scope':'Read-only status, asset and preserved output inspection. No new inference, uploads, startup, restart or training.'}
d['python']=sys.version;d['platform']=platform.platform()
d['packages']={}
for name in ['torch','transformers','peft','numpy','rasterio','pyproj','pillow','fastapi','uvicorn','huggingface-hub','safetensors','requests','timm','opencv-python-headless']:
 try:d['packages'][name]=importlib.metadata.version(name)
 except importlib.metadata.PackageNotFoundError:d['packages'][name]='not in base environment metadata'
d['http']={}
for port,path in [(8765,'/api/status'),(8765,'/grounding/api/status'),(8767,'/api/status'),(8765,'/api/development'),(8765,'/api/reliability')]:
 try:
  with urllib.request.urlopen(f'http://127.0.0.1:{port}{path}',timeout=10) as f:body=json.load(f)
  d['http'][f'{port}{path}']=body if 'status' in path else {'available':True,'label':body.get('label'),'keys':list(body)}
 except Exception as e:d['http'][f'{port}{path}']={'error':str(e)}
d['assets']=[]
paths=[Path('/root/satquery/experiments/lora-pilot-v1/adapter/adapter_model.safetensors'),R/'paired_lab/checkpoints/water-v1.pt',Path('/root/satquery/paired-lab/mci-model/MCI_model.pth')]
for file in ['/root/satquery/paired-lab/models.json','/root/satquery/grounding-lab/models.json','/root/satquery/paired-lab/mci-model/manifest.json']:
 p=Path(file);obj=json.loads(p.read_text());d[file]=obj
 records=obj if isinstance(obj,list) else list(obj.values()) if 'path' not in obj else [obj]
 for x in records:
  if isinstance(x,dict) and x.get('path'):
   q=Path(x['path'])
   if q.is_file():paths.append(q)
   elif q.is_dir():paths.extend(q.glob('*.safetensors'))
for p in dict.fromkeys(paths):
 item={'path':str(p),'exists':p.exists()}
 if p.is_file():
  h=hashlib.sha256()
  with p.open('rb') as f:
   for chunk in iter(lambda:f.read(8*1024*1024),b''):h.update(chunk)
  item.update(bytes=p.stat().st_size,sha256=h.hexdigest())
 d['assets'].append(item)
d['preserved_run_checks']=[]
for p in sorted((R/'paired_lab/evidence/resumed/live').glob('0*.json')):
 result=json.loads(p.read_text());run=Path('/root/satquery/paired-lab/app/runs')/result['id'];item={'record':str(p),'runtime_folder':str(run),'exists':run.exists()}
 if run.exists():
  item['files']=[x.name for x in run.iterdir() if x.is_file()]
  if (run/'evidence.zip').exists():
   with zipfile.ZipFile(run/'evidence.zip') as z:item['zip_crc_error']=z.testzip();item['zip_files']=z.namelist()
  if result['task']=='water_map':
   a=np.load(run/'water-scores.npz');valid=a['valid'];counts={m:int(((a[m]>=.5)&valid).sum()) for m in ['s1','s2','all']};item['recomputed_counts']=counts;item['counts_match']=counts==result['water_pixels'];item['valid_match']=int(valid.sum())==result['denominator_pixels']
  if result['task']=='temporal':
   a=np.load(run/'scores.npz');c=a['classes'];counts={'road':int((c==1).sum()),'building':int((c==2).sum())};item['recomputed_counts']=counts;item['counts_match']=counts==result['class_pixels'];item['argmax_matches']=bool(np.array_equal(c,a['scores'].argmax(0)))
  if result['task']=='ndvi':
   import rasterio
   with rasterio.open(run/'ndvi.tif') as f:a=f.read(1)
   s=result['statistics'];item['selected_from_export']=int((np.isfinite(a)&(a>=s['threshold'])).sum());item['counts_match']=item['selected_from_export']==s['selected_pixels']
  if (run/'main-raw-result.json').exists():
   raw=json.loads((run/'main-raw-result.json').read_text());item['main_metrics']={k:raw.get(k) for k in ['seconds','generation_seconds','peak_allocated_GiB','trace','mode','raw_answer','answer_policy']}
 try:
  with urllib.request.urlopen('http://127.0.0.1:8767/api/jobs/'+result['id'],timeout=5) as f:item['current_job_status']=json.load(f)['state']
 except Exception as e:item['current_job_status']=str(e)
 d['preserved_run_checks'].append(item)
d['licenses']=[]
for pattern in ['/root/.cache/huggingface/hub/models--*/snapshots/*/README.md','/root/satquery/paired-lab/Change-Agent/LICENSE*','/root/satquery/paired-lab/ChangeFormer/README.md','/root/satquery/grounding-lab/models.json']:
 import glob
 for name in glob.glob(pattern):
  p=Path(name)
  if any(x in str(p) for x in ['AdaptLLM','BIFOLD','grounding','sam','Change-Agent','ChangeFormer']):
   lines=p.read_text(errors='replace').splitlines();matches=[{'line':i+1,'text':x} for i,x in enumerate(lines) if any(w in x.lower() for w in ['license','commercial','academic','copyright','permission'])];d['licenses'].append({'path':str(p),'matches':matches[:15]})
(O/'runtime-verification.json').write_text(json.dumps(d,indent=2))
print(json.dumps({'http':d['http'],'assets':d['assets'],'runs':[{k:v for k,v in x.items() if k not in ['files','zip_files','main_metrics']} for x in d['preserved_run_checks']],'licenses':d['licenses']},indent=2))
