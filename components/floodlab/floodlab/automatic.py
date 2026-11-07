"""Reproducible bounded water/exposure run from area and date; connectivity remains unknown."""
from pathlib import Path
from datetime import datetime,timedelta,timezone
import json,tarfile,hashlib,argparse
import numpy as np
import rasterio
from rasterio.features import geometry_mask
from shapely.geometry import box,mapping
from shapely.ops import transform
from shapely import from_wkb
from pyproj import Transformer
import pyarrow.parquet as pq
import requests
from .event_acquisition import discover,acquire
from .pipeline import run

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):p.write_text(json.dumps(v,indent=2),encoding='utf-8')
def same_product(a,b):
 return a.removesuffix('.SAFE')==b.removesuffix('.SAFE')

def prepare(root,config):
 root=Path(root);plan=json.loads((root/'plan.json').read_text());dest=root/'prepared';dest.mkdir(exist_ok=True)
 if any(dest.iterdir()):raise ValueError('Prepared destination is not empty; preserve evidence')
 aoi=box(*plan['bbox']);project=Transformer.from_crs(4326,plan['epsg'],always_xy=True).transform;metric=transform(project,aoi);obs={};grid=None
 for period in ('pre','post'):
  source=root/period
  with tarfile.open(source/'response.tar') as archive:
   for name in ('default.tif','userdata.json'):
    member=archive.getmember(name)
    if not member.isfile():raise ValueError('Unexpected archive member')
    with archive.extractfile(member) as f:(source/name).write_bytes(f.read())
  meta=json.loads((source/'userdata.json').read_text());scenes=meta['scenes'];feature=plan[period];props=feature['properties']
  if len(scenes)!=1 or not same_product(scenes[0]['sentinel1ProductId'],feature['id']):raise ValueError('Provider scene does not match selected catalogue scene')
  with rasterio.open(source/'default.tif') as ds:
   current=(ds.crs,ds.transform,ds.width,ds.height)
   if ds.count!=6 or ds.crs.to_epsg()!=plan['epsg'] or ds.width!=plan['width'] or ds.height!=plan['height']:raise ValueError('Raster contract mismatch')
   if grid is not None and grid!=current:raise ValueError('Grid mismatch')
   grid=current;a=ds.read();inside=geometry_mask([mapping(metric)],out_shape=a.shape[1:],transform=ds.transform,invert=True)
   valid=inside&np.isfinite(a).all(0)&(a[:2]>0).all(0)&(a[4]==1)&(a[3]==0)&(a[2]>5)&(a[2]<85)
   if not valid.any():raise ValueError('No valid SAR coverage')
   values=np.full(a[:2].shape,-9999,dtype='float32');values[:,valid]=10*np.log10(a[:2,valid]);profile=ds.profile;profile.update(count=2,nodata=-9999,compress='deflate')
   p=dest/(period+'.tif')
   with rasterio.open(p,'w',**profile) as out:out.write(values)
  obs[period]={'role':'observation','source':'Sentinel-1','units':'dB','bands':['VV','VH'],'terrain_corrected':True,'scene_id':feature['id'],'datetime':props['datetime'],'relative_orbit':props['sat:relative_orbit'],'orbit_state':props['sat:orbit_state'],'platform':props['platform'],'path':p.name,'sha256':digest(p),'source_sha256':digest(source/'default.tif'),'processing_request':str(source/'request.json')}
 snapshot=(datetime.fromisoformat(plan['event_date'])-timedelta(days=1)).replace(tzinfo=timezone.utc);stamp=snapshot.isoformat().replace('+00:00','Z');config_values={}
 for line in Path(config).read_text().splitlines():
  if '=' in line and not line.lstrip().startswith('#'):
   k,v=line.split('=',1);config_values[k.strip()]=v.strip().strip('\"').strip("'")
 key=config_values.get('OHSOME_API_KEY')
 if not key:raise ValueError('Historical OSM credential is missing')
 payload={'aoi':mapping(aoi),'filter':'building=* or highway=* or bridge=* or place=* or amenity=hospital','time':stamp,'clip':False}
 response=requests.post('https://api.heigit.org/ohsome-api/v2-rc/extraction/features.parquet',json=payload,headers={'Authorization':key},timeout=(20,240),allow_redirects=False)
 if response.status_code!=200:raise ValueError('Historical OSM acquisition failed; HTTP '+str(response.status_code))
 raw=response.content
 if raw[:4]!=b'PAR1' or raw[-4:]!=b'PAR1':raise ValueError('Invalid historical OSM payload')
 p=root/'historical-osm.parquet';p.write_bytes(raw);save(root/'osm-provenance.json',{'request':payload,'sha256':digest(p),'license':'ODbL; OpenStreetMap contributors'})
 features=[]
 for row in pq.read_table(p,columns=['osm_type','osm_id','version','tags','geom','edit_timestamp','valid_to_timestamp','clipped']).to_pylist():
  if row['clipped'] or not row['edit_timestamp']<=snapshot<row['valid_to_timestamp']:raise ValueError('Historical snapshot contract mismatch')
  geom=from_wkb(row['geom']);tags=dict(row['tags'])
  if not geom.is_valid:raise ValueError('Invalid infrastructure geometry; repair requires review')
  kind='building' if tags.get('building') and geom.geom_type in ('Polygon','MultiPolygon') else ('bridge' if tags.get('bridge') not in (None,'no') else 'road') if tags.get('highway') and geom.geom_type in ('LineString','MultiLineString') else None
  if kind:features.append({'type':'Feature','id':f"{row['osm_type']}/{row['osm_id']}",'properties':{'kind':kind,'osm_version':row['version'],'snapshot':stamp},'geometry':mapping(transform(project,geom))})
 infra={'role':'historical_osm','snapshot':stamp,'analysis_crs':f"EPSG:{plan['epsg']}",'features':features,'graph_roads':[],'settlements':[],'hub_node_ids':[]}
 save(dest/'infrastructure.json',infra)
 manifest={'event_name':'Area/date water baseline '+plan['event_date'],'synthetic':False,'event_time':plan['event_date']+'T00:00:00Z','osm_snapshot':stamp,'infrastructure_role':'historical_osm','infrastructure_path':'infrastructure.json','infrastructure_sha256':digest(dest/'infrastructure.json'),**obs,'analysis':{'tile_size':256,'water_db':-17.,'drop_db':3.,'min_exposed_road_m':1.},'limitations':['Automatic bounded water/exposure baseline only: debris and historical road topology are not connected in this path.','Connectivity is not assessed; empty settlement results do not mean zero isolation.','Fixed thresholds are unvalidated; incomplete radar layover mask; provider terrain correction recorded in request provenance.','OSM snapshot is one day before the event in UTC; missing assets are not counted.']}
 save(dest/'manifest.json',manifest);return dest/'manifest.json'
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--bbox',nargs=4,type=float,required=True);parser.add_argument('--date',required=True);parser.add_argument('--run-id',required=True);args=parser.parse_args()
 import re
 if not re.fullmatch('[A-Za-z0-9_-]+',args.run_id):raise ValueError('Invalid run ID')
 base=Path(__file__).resolve().parents[1];config=base/'.env.local';root=base/'data/automatic'/args.run_id
 plan=discover(args.bbox,args.date);acquire(plan,root,config,lambda msg:print(msg,flush=True));manifest=prepare(root,config);run(manifest,base/'artifacts/runs'/args.run_id)
 print('Frozen water/exposure run:',args.run_id,flush=True)
