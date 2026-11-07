from pathlib import Path
import json,datetime,tarfile
import numpy as np,rasterio
from rasterio.features import geometry_mask
from shapely.geometry import shape,mapping
from shapely.ops import transform
from pyproj import Transformer
from floodlab.acquisition import Provider
B=Path(__file__).resolve().parents[1];provider=Provider(B/'.env.local');base=json.loads((B/'data/requests/syapru-pre.json').read_text());aoi=shape(json.loads((B/'data/aoi/nepal-official-boundaries.geojson').read_text())['features'][0]['geometry']);aoi=transform(Transformer.from_crs(4326,32645,always_xy=True).transform,aoi)
script='''//VERSION=3
function setup(){return {input:["B02","B03","B04","B08","B11","SCL","dataMask"],output:{bands:7,sampleType:"FLOAT32"},mosaicking:"TILE"};}
function evaluatePixel(a){if(a.length!==1)return [0,0,0,0,0,0,0];let s=a[0];return [s.B02,s.B03,s.B04,s.B08,s.B11,s.SCL,s.dataMask];}
function updateOutputMetadata(scenes,inputMetadata,outputMetadata){outputMetadata.userData={scenes:scenes.tiles,inputMetadata:inputMetadata};}'''
event=datetime.datetime(2026,8,26,tzinfo=datetime.timezone.utc);records=[]
for period in ('pre','post'):
 features=json.loads((B/'data/metadata'/f'syapru_besi_s2_{period}.json').read_text())['stac']['features']
 features=[f for f in features if abs((datetime.datetime.fromisoformat(f['properties']['datetime'].replace('Z','+00:00'))-event).total_seconds())<=14*86400]
 for f in features:
  day=f['properties']['datetime'][:10];out=B/'data/optical'/day;out.mkdir(parents=True,exist_ok=True);dest=out/'response.tar'
  req={'input':{'bounds':base['input']['bounds'],'data':[{'type':'sentinel-2-l2a','dataFilter':{'timeRange':{'from':day+'T00:00:00Z','to':day+'T23:59:59Z'}},'processing':{'upsampling':'NEAREST','downsampling':'NEAREST'}}]},'output':base['output'],'evalscript':script}
  (out/'request.json').write_text(json.dumps(req,indent=2))
  if not dest.exists():provider.process(req,dest)
  if not tarfile.is_tarfile(dest):raise ValueError('Provider did not return requested metadata archive')
  with tarfile.open(dest) as t:t.extractall(out,filter='data')
  with rasterio.open(out/'default.tif') as ds:
   a=ds.read();inside=geometry_mask([mapping(aoi)],out_shape=(ds.height,ds.width),transform=ds.transform,invert=True);valid=inside&np.isfinite(a).all(0)&np.isin(a[5],[4,5,6])&(a[6]==1)
   row={'period':period,'date':day,'catalogue_id':f['id'],'valid_aoi_pixels':int(valid.sum()),'aoi_pixels':int(inside.sum()),'clear_fraction':float(valid.sum()/inside.sum()),'scenes':json.loads((out/'userdata.json').read_text())}
   records.append(row);print(period,day,row['clear_fraction'],flush=True)
  (B/'data/optical/coverage.json').write_text(json.dumps(records,indent=2))
print('Optical coverage inventory complete',flush=True)
