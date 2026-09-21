import json,hashlib
from pathlib import Path
import numpy as np
import rasterio
from rasterio.windows import Window
from rasterio.vrt import WarpedVRT
from rasterio.enums import Resampling
from pyproj import Transformer
p=Path('/root/satquery/scenes');item=json.loads((p/'reference-item.json').read_text());bands=['red','green','blue','nir','scl'];data=[];manifest={'item_id':item['id'],'acquired':item['properties']['datetime'],'source_catalog':'https://earth-search.aws.element84.com/v1','collection':'sentinel-2-c1-l2a','calibration_version':'c1-header-verified-v2','attribution':'Contains modified Copernicus Sentinel data (2021), accessed through Element 84 Earth Search / AWS.','bands':{}}
with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN='EMPTY_DIR',CPL_VSIL_CURL_ALLOWED_EXTENSIONS='.tif',GDAL_HTTP_TIMEOUT='60',GDAL_HTTP_MAX_RETRY='2'):
 for name in bands:
  asset=item['assets'][name]
  with rasterio.open(asset['href']) as src:
   if name=='red':
    x,y=Transformer.from_crs(4326,src.crs,always_xy=True).transform(78.025,30.305);row,col=src.index(x,y)
    win=Window(col-256,row-256,512,512);assert win.col_off>=0 and win.row_off>=0 and win.col_off+512<=src.width and win.row_off+512<=src.height
    transform=src.window_transform(win);crs=src.crs
   with WarpedVRT(src,crs=crs,transform=transform,width=512,height=512,resampling=Resampling.nearest) as vrt:
    a=vrt.read(1,masked=True).astype('float32').filled(np.nan)
   meta=asset['raster:bands'][0];scale=meta.get('scale',1);offset=meta.get('offset',0)
   if name!='scl':
    if not np.isclose(src.scales[0],scale) or not np.isclose(src.offsets[0],offset):
     raise ValueError('Calibration conflict between COG header and STAC; do not guess.')
    a=a*scale+offset
   data.append(a);manifest['bands'][name]={'source':asset['href'],'scale_applied':scale,'offset_applied':offset,'resampling':'nearest to red-band 10 m grid'}
  print('Fetched window:',name,flush=True)
 out=p/'dehradun-sentinel2-20211125.tif'
 with rasterio.open(out,'w',driver='GTiff',width=512,height=512,count=5,dtype='float32',crs=crs,transform=transform,nodata=np.nan,compress='deflate') as dst:
  dst.write(np.stack(data));dst.descriptions=tuple(bands);dst.update_tags(acquired=manifest['acquired'],source_item=item['id'],reflectance_units='surface_reflectance',calibration_version='c1-header-verified-v2',attribution=manifest['attribution'],processing='Collection 1 COG header and STAC scale/offset matched; applied exactly once; SCL nearest-neighbour 20m to 10m.')
 manifest.update(sha256=hashlib.sha256(out.read_bytes()).hexdigest(),file=str(out),crs=str(crs),transform=list(transform)[:6],size=[512,512])
 (p/'scene-manifest.json').write_text(json.dumps(manifest,indent=2));print(json.dumps(manifest,indent=2))
