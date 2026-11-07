from pathlib import Path
import json,hashlib,numpy as np,rasterio
b=Path.cwd();out=b/'web/observations';out.mkdir(exist_ok=True);sources={}
for p in list((b/'data/optical').glob('*/default.tif'))+list((b/'data/automatic').glob('*/optical/*/default.tif')):
 sources[hashlib.sha256(p.read_bytes()).hexdigest()]=p
index={}
for root in (b/'artifacts/runs').iterdir():
 if not (root/'freeze.json').exists():continue
 freeze=json.loads((root/'freeze.json').read_text());raw=(root/'manifest.json').read_bytes()
 if hashlib.sha256(raw).hexdigest()!=freeze['files']['manifest.json']:raise ValueError('Manifest mismatch')
 m=json.loads(raw);debris=m.get('debris');entry={}
 pair=':'.join((m['pre']['sha256'],m['post']['sha256']))
 if not debris:continue
 for period in ('pre','post'):
  day=debris[period+'_date'];digest=debris['source_hashes'][day];source=sources.get(digest)
  if source is None:continue
  dest=out/(digest+'.png')
  if not dest.exists():
   with rasterio.open(source) as ds:
    a=ds.read();rgb=a[[2,1,0]];valid=np.isfinite(rgb).all(0)&(a[6]==1);pixels=(np.clip(rgb/0.3,0,1)**(1/2.2)*255).astype('uint8');pixels[:,~valid]=0
    with rasterio.open(dest,'w',driver='PNG',width=ds.width,height=ds.height,count=3,dtype='uint8') as image:image.write(pixels)
  entry['optical-'+period]={'url':'/assets/observations/'+dest.name,'date':day,'source_sha256':digest,'description':'Sentinel-2 RGB (B04/B03/B02), fixed 0–0.3 reflectance display and gamma 2.2. Clouds remain visible; black indicates invalid/no data. Display preview, not a classification.'}
 if entry:
  entry['sar_pair_sha256']=pair
  index[root.name]=entry
# Share previews only with runs whose full before/after georeferenced SAR files match exactly.
for root in (b/'artifacts/runs').iterdir():
 if root.name in index or not (root/'freeze.json').exists():continue
 m=json.loads((root/'manifest.json').read_text());pair=':'.join((m['pre']['sha256'],m['post']['sha256']))
 source=next((run for run in index.values() if run.get('sar_pair_sha256')==pair and run.get('optical-pre') and run.get('optical-post')),None)
 if source:
  index[root.name]={**{k:v for k,v in source.items() if k.startswith('optical-')},'sar_pair_sha256':pair,'shared_grid_match':True}
(out/'index.json').write_text(json.dumps(index,indent=2));print('Optical previews indexed for',len(index),'runs')
