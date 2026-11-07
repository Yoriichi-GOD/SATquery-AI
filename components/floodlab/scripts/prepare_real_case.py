from pathlib import Path
import json,hashlib,tarfile,datetime
import numpy as np
import rasterio
from rasterio.features import geometry_mask
import pyarrow.parquet as pq
from shapely import from_wkb
from shapely.geometry import shape,mapping
from shapely.ops import transform
from pyproj import Transformer
B=Path(__file__).resolve().parents[1]
D=B/'data/prepared/syapru-20260826';D.mkdir(parents=True,exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):p.write_text(json.dumps(x,indent=2,ensure_ascii=False,allow_nan=False))
aoi=shape(json.loads((B/'data/aoi/nepal-official-boundaries.geojson').read_text())['features'][0]['geometry'])
project=Transformer.from_crs(4326,32645,always_xy=True).transform
metric_aoi=transform(project,aoi);obs={};quality={};grid=None
expected={'pre':'S1D_IW_GRDH_1SDV_20260816T122141_20260816T122206_004151_007980_B091_COG.SAFE','post':'S1D_IW_GRDH_1SDV_20260828T122141_20260828T122206_004326_007FA4_C73B_COG.SAFE'}
for period in ('pre','post'):
 src=B/'data/sar'/period
 with tarfile.open(src/'response.tar') as t:t.extractall(src,filter='data')
 meta=json.loads((src/'userdata.json').read_text());scenes=meta['scenes']
 if len(scenes)!=1 or scenes[0]['sentinel1ProductId']!=expected[period]:raise ValueError('Unexpected acquisition; refuse temporal/orbit mixing')
 with rasterio.open(src/'default.tif') as ds:
  p=ds.profile;a=ds.read();current=(ds.crs,ds.transform,ds.width,ds.height)
  if ds.count!=6 or ds.crs.to_epsg()!=32645:raise ValueError('Unexpected raster contract')
  if grid is not None and grid!=current:raise ValueError('Pair not aligned')
  grid=current
  inside=geometry_mask([mapping(metric_aoi)],out_shape=(ds.height,ds.width),transform=ds.transform,invert=True)
  finite=np.isfinite(a).all(0);positive=(a[:2]>0).all(0)
  valid=inside&finite&positive&(a[4]==1)&(a[3]==0)&(a[2]>5)&(a[2]<85)
  result=np.full(a[:2].shape,-9999,dtype='float32');result[:,valid]=10*np.log10(a[:2,valid])
  p.update(count=2,nodata=-9999,compress='deflate');dest=D/(period+'.tif')
  with rasterio.open(dest,'w',**p) as out:out.write(result);out.set_band_description(1,'VV gamma0 terrain dB');out.set_band_description(2,'VH gamma0 terrain dB')
  quality[period]={'aoi_pixels':int(inside.sum()),'valid_pixels':int(valid.sum()),'shadow_pixels':int((inside&(a[3]==1)).sum()),'nonfinite_pixels':int((inside&~finite).sum()),'source_sha256':sha(src/'default.tif'),'source_metadata':meta,'backscatter':'GAMMA0_TERRAIN','mask':'AOI; dataMask; finite positive VV/VH; shadowMask=0; local incidence 5..85 degrees; not a complete layover mask'}
 obs[period]={'role':'observation','source':'Sentinel-1','units':'dB','bands':['VV','VH'],'terrain_corrected':True,'scene_id':expected[period],'datetime':scenes[0]['date'],'relative_orbit':85,'orbit_state':'ascending','platform':'sentinel-1d','path':dest.name,'sha256':sha(dest),'backscatter_coefficient':'GAMMA0_TERRAIN','processing_request':str((B/'data/requests'/f'syapru-{period}.json').relative_to(B))}
snapshot='2026-07-27T00:00:00Z';when=datetime.datetime.fromisoformat(snapshot.replace('Z','+00:00'))
features=[];settlements=[];invalid=[];ids=set()
cols=['osm_type','osm_id','version','tags','geom','edit_timestamp','valid_to_timestamp','clipped']
for r in pq.read_table(B/'data/osm_pre_event/nepal-corridor-20260727.parquet',columns=cols).to_pylist():
 g=from_wkb(r['geom'])
 if not g.intersects(aoi):continue
 if not r['edit_timestamp']<=when<r['valid_to_timestamp']:raise ValueError('Snapshot validity failure')
 if r['clipped']:raise ValueError('Clipped geometry cannot preserve feature scope')
 tags=dict(r['tags']);fid=f"{r['osm_type']}/{r['osm_id']}"
 if fid in ids:raise ValueError('Duplicate OSM ID')
 ids.add(fid)
 if not g.is_valid:invalid.append(fid);continue
 if tags.get('place') or tags.get('amenity')=='hospital':settlements.append({'id':fid,'name':tags.get('name:en',tags.get('name',fid)),'node_id':None,'boundary_truncated':True})
 kind='building' if tags.get('building') and g.geom_type in ('Polygon','MultiPolygon') else ('bridge' if tags.get('bridge') not in (None,'no') else 'road') if tags.get('highway') and g.geom_type in ('LineString','MultiLineString') else None
 if kind:features.append({'type':'Feature','id':fid,'properties':{'kind':kind,'osm_version':r['version'],'snapshot':snapshot,'tags':tags},'geometry':mapping(transform(project,g))})
infra={'role':'historical_osm','snapshot':snapshot,'analysis_crs':'EPSG:32645','features':features,'graph_roads':[],'settlements':settlements,'hub_node_ids':[],'topology_status':'unavailable; no connections inferred from geometry crossings','excluded_invalid_ids':invalid}
save(D/'infrastructure.json',infra);save(D/'quality.json',quality)
m={'event_name':'Syapru Besi, Nepal · 26 August 2026','synthetic':False,'event_time':'2026-08-26T00:00:00+05:45','osm_snapshot':snapshot,'infrastructure_role':'historical_osm','infrastructure_path':'infrastructure.json','infrastructure_sha256':sha(D/'infrastructure.json'),'pre':obs['pre'],'post':obs['post'],'analysis':{'tile_size':256,'water_db':-17.0,'drop_db':3.0,'min_exposed_road_m':1.0},'limitations':['Infrastructure is historical OSM from 27 July 2026; missing/unmapped assets are not counted.','Road topology acquisition failed; connectivity is NOT assessed, not zero isolation.','Copernicus Sentinel Hub processed raw GRD with Copernicus DEM30; API orchestration remains manual for this run.','Gamma0 terrain threshold is uncalibrated; exposure is to water candidates, not confirmed flood damage.','EMSR927 damage labels were not used for prediction or threshold selection.']}
save(D/'manifest.json',m)
print(json.dumps({'quality':{k:{x:v for x,v in val.items() if x!='source_metadata'} for k,val in quality.items()},'infrastructure_features':len(features),'settlements':len(settlements),'excluded_invalid':invalid},indent=2))
