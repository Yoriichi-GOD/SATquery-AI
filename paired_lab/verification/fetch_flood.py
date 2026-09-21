import requests,json,concurrent.futures,hashlib,time
from pathlib import Path
BASE='https://storage.googleapis.com/sen1floods11/'
D=Path('/root/satquery/paired-lab/sen1floods11');D.mkdir(exist_ok=True)
P=Path('/mnt/c/Users/nrgen/.codex/scratch/SATquery AI/paired_lab/evidence/resumed')
listing=requests.get('https://storage.googleapis.com/storage/v1/b/sen1floods11/o',params={'prefix':'v1.1/','maxResults':1000},timeout=30)
listing.raise_for_status();j=listing.json();(D/'listing.json').write_text(json.dumps(j,indent=2))
names=[x['name'] for x in j.get('items',[])]
print('FIRST LISTING',len(names),names[:8],flush=True)
for prefix in ['v1.1/splits/','v1.1/data/flood_events/HandLabeled/','v1.1/metadata/']:
 r=requests.get('https://storage.googleapis.com/storage/v1/b/sen1floods11/o',params={'prefix':prefix,'maxResults':1000},timeout=30);r.raise_for_status();v=r.json();(D/(prefix.strip('/').replace('/','_')+'.json')).write_text(json.dumps(v,indent=2));print(prefix,[x['name'] for x in v.get('items',[])][:12],flush=True)
spliturls={s:BASE+'v1.1/splits/flood_handlabeled/flood_'+s+'_data.csv' for s in ['train','valid','test','bolivia']}
splits={};files=[]
for split,url in spliturls.items():
 r=requests.get(url,timeout=30)
 if r.status_code!=200:print('SPLIT',split,r.status_code,r.text[:200],flush=True);continue
 (D/(split+'.csv')).write_bytes(r.content)
 ids=[line.split(',')[0].replace('_S1Hand.tif','') for line in r.text.strip().splitlines()]
 splits[split]=ids
 for sid in ids:
  for layer in ['S1Hand','S2Hand','LabelHand']:
   files.append(('v1.1/data/flood_events/HandLabeled/'+layer+'/'+sid+'_'+layer+'.tif',D/layer/(sid+'_'+layer+'.tif')))
print('SPLITS',{s:len(ids) for s,ids in splits.items()},flush=True)
(D/'splits.json').write_text(json.dumps(splits,indent=2))
def fetch(item):
 name,p=item;p.parent.mkdir(exist_ok=True)
 if not p.exists():
  for attempt in range(3):
   try:
    r=requests.get(BASE+name,timeout=90);r.raise_for_status();p.write_bytes(r.content);break
   except Exception:
    if attempt==2:raise
    time.sleep(1)
 return {'file':str(p),'url':BASE+name,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
out=[]
with concurrent.futures.ThreadPoolExecutor(10) as pool:
 for i,res in enumerate(pool.map(fetch,files)):
  out.append(res)
  if i%60==0:print('DOWNLOADED',i+1,'/',len(files),flush=True)
manifest={'dataset':'Sen1Floods11 v1.1 hand-labelled optical/SAR pairs','source':'https://github.com/cloudtostreet/Sen1Floods11','splits':{s:len(ids) for s,ids in splits.items()},'files':out}
(D/'manifest.json').write_text(json.dumps(manifest,indent=2));(P/'flood-data-manifest.json').write_text(json.dumps(manifest,indent=2));print('DONE',len(out),flush=True)
