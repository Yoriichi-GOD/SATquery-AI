from pathlib import Path
import json, math, hashlib, datetime
import requests, rasterio
from pyproj import Transformer
from shapely.geometry import shape
B=Path(__file__).resolve().parents[1]
aois=json.loads((B/'data/aoi/nepal-official-boundaries.geojson').read_text())['features']
root=B/'data/terrain';root.mkdir(parents=True,exist_ok=True)
tile='Copernicus_DSM_COG_10_N28_00_E085_00_DEM'
url=f'https://copernicus-dem-30m.s3.eu-central-1.amazonaws.com/{tile}/{tile}.tif'
p=root/(tile+'.tif')
if not p.exists():
 with requests.get(url,stream=True,timeout=(20,60)) as r:
  r.raise_for_status()
  with p.with_suffix('.part').open('wb') as f:
   for chunk in r.iter_content(1024*1024):f.write(chunk)
 p.with_suffix('.part').replace(p)
with rasterio.open(p) as ds:
 checks=[]
 for a in aois:
  bounds=shape(a['geometry']).bounds
  from rasterio.windows import from_bounds
  x=ds.read(1,window=from_bounds(*bounds,transform=ds.transform),masked=True)
  checks.append({'area':a['properties']['id'],'valid_pixels':int(x.count()),'pixels':int(x.size),'min_m':float(x.min()),'max_m':float(x.max())})
 manifest={'source':'Copernicus DEM GLO-30','url':url,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size,'crs':str(ds.crs),'bounds':list(ds.bounds),'checks':checks,'downloaded_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'role':'terrain input; not flood reference','license_source':'https://registry.opendata.aws/copernicus-dem/'}
(root/'manifest.json').write_text(json.dumps(manifest,indent=2))
print(json.dumps(manifest,indent=2))
rdir=B/'data/requests';rdir.mkdir(exist_ok=True)
tf=Transformer.from_crs(4326,32645,always_xy=True)
a=aois[0];w,s,e,n=shape(a['geometry']).bounds
x0,y0=tf.transform(w,s);x1,y1=tf.transform(e,n)
bbox=[math.floor(x0/10)*10-100,math.floor(y0/10)*10-100,math.ceil(x1/10)*10+100,math.ceil(y1/10)*10+100]
# One acquisition per request. No temporal mosaicking beyond that acquisition.
evalscript='''//VERSION=3
function setup(){return {input:["VV","VH","localIncidenceAngle","shadowMask","dataMask","scatteringArea"],output:{bands:6,sampleType:"FLOAT32"},mosaicking:"TILE"};}
function evaluatePixel(samples){if(samples.length!==1)return [0,0,0,1,0,0];let s=samples[0];return [s.VV,s.VH,s.localIncidenceAngle,s.shadowMask,s.dataMask,s.scatteringArea];}
function updateOutputMetadata(scenes,inputMetadata,outputMetadata){outputMetadata.userData={scenes:scenes.tiles,inputMetadata:inputMetadata};}'''
for period,day in [('pre','2026-08-16'),('post','2026-08-28')]:
 req={'input':{'bounds':{'bbox':bbox,'properties':{'crs':'http://www.opengis.net/def/crs/EPSG/0/32645'}},'data':[{'type':'sentinel-1-grd','dataFilter':{'timeRange':{'from':day+'T12:21:30Z','to':day+'T12:22:00Z'},'acquisitionMode':'IW','polarization':'DV','orbitDirection':'ASCENDING','resolution':'HIGH'},'processing':{'orthorectify':True,'demInstance':'COPERNICUS_30','backCoeff':'GAMMA0_TERRAIN','radiometricTerrainOversampling':2,'speckleFilter':{'type':'NONE'}}}]},'output':{'width':(bbox[2]-bbox[0])//10,'height':(bbox[3]-bbox[1])//10,'responses':[{'identifier':'default','format':{'type':'image/tiff'}},{'identifier':'userdata','format':{'type':'application/json'}}]},'evalscript':evalscript}
 (rdir/f'syapru-{period}.json').write_text(json.dumps(req,indent=2))
 print(period,req['output']['width'],req['output']['height'],bbox)
