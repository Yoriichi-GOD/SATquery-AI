from pathlib import Path
import json,hashlib,shutil
import rasterio,numpy as np
from floodlab.debris import debris_candidates
from floodlab.core import read_pair
B=Path(__file__).resolve().parents[1];root=B/'data/prepared/syapru-connectivity';m=json.loads((root/'manifest.json').read_text());pre,post,valid,profile=read_pair(m,root)
opt=[]
for day in ('2026-08-12','2026-08-27'):
 with rasterio.open(B/'data/optical'/day/'default.tif') as ds:
  if any(ds.profile[k]!=profile[k] for k in ('crs','transform','width','height')):raise ValueError('Optical SAR grids do not match')
  opt.append(ds.read())
mask=debris_candidates(*opt,pre,post,valid,valid)
p=root/'debris-candidates.tif';profile.update(count=1,dtype='uint8',nodata=255)
with rasterio.open(p,'w',**profile) as ds:ds.write(mask,1)
m['debris']={'path':p.name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'pre_date':'2026-08-12','post_date':'2026-08-27','method':'fixed vegetation-to-bare and SAR-change proxy','thresholds':{'pre_ndvi_min':0.4,'post_ndvi_max':0.3,'ndvi_drop_min':0.2,'sar_abs_change_db_min':3},'source_hashes':{day:hashlib.sha256((B/'data/optical'/day/'default.tif').read_bytes()).hexdigest() for day in ('2026-08-12','2026-08-27')},'limitations':'Candidate vegetation loss to bare ground with SAR change; can confuse land clearing/agriculture and misses debris on already bare ground. Not trained or independently calibrated. Optical SCL is native 20m resampled to 10m.'}
m['limitations'].append(m['debris']['limitations']);(root/'manifest-debris.json').write_text(json.dumps(m,indent=2))
print(json.dumps({'candidate_pixels':int((mask==1).sum()),'valid_pixels':int((mask!=255).sum()),'thresholds':m['debris']['thresholds']}))
