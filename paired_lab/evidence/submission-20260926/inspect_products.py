"""Read public sample archives without modifying their imagery."""
import json,hashlib,zipfile,sys
from pathlib import Path
from datetime import datetime,timezone
import rasterio
from rasterio.warp import transform_bounds

OUT=Path(__file__).resolve().parent
def sha(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for chunk in iter(lambda:f.read(8*1024*1024),b''):h.update(chunk)
 return h.hexdigest()
for name in sys.argv[1:]:
 p=OUT/name
 result={'archive':name,'bytes':p.stat().st_size,'sha256':sha(p),'inspected_utc':datetime.now(timezone.utc).isoformat(),'members':[],'rasters':[],'metadata':{}}
 with zipfile.ZipFile(p) as z:
  for m in z.infolist():
   result['members'].append({'name':m.filename,'bytes':m.file_size,'compressed_bytes':m.compress_size,'crc':m.CRC})
   if m.file_size<2_000_000 and Path(m.filename).suffix.lower() in ['.txt','.xml','.json','.dim','.rpb','.rpc','.imd','.hdr']:
    result['metadata'][m.filename]=z.read(m).decode('utf-8',errors='replace')
   if Path(m.filename).suffix.lower() not in ['.tif','.tiff']:continue
   uri='/vsizip/'+str(p)+'/'+m.filename
   with rasterio.open(uri) as ds:
    r={'member':m.filename,'driver':ds.driver,'width':ds.width,'height':ds.height,'count':ds.count,'dtypes':ds.dtypes,'descriptions':ds.descriptions,'colorinterp':[c.name for c in ds.colorinterp],'crs':str(ds.crs),'bounds':list(ds.bounds),'transform':list(ds.transform)[:6],'res':ds.res,'nodata':ds.nodata,'scales':ds.scales,'offsets':ds.offsets,'tags':ds.tags(),'band_tags':[ds.tags(i) for i in ds.indexes],'gcps_count':len(ds.gcps[0]),'rpc':ds.tags(ns='RPC')}
    if ds.crs:r['bounds_wgs84']=transform_bounds(ds.crs,'EPSG:4326',*ds.bounds)
    result['rasters'].append(r)
 (OUT/(p.stem+'-inventory.json')).write_text(json.dumps(result,indent=2,allow_nan=True))
 print(json.dumps({'archive':name,'sha256':result['sha256'],'members':len(result['members']),'rasters':result['rasters'],'metadata_names':list(result['metadata'])},indent=2),flush=True)
