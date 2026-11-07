"""Optional optical coverage selection and fixed debris proxy, never reference-driven."""
from pathlib import Path
from datetime import datetime,timedelta,timezone
import json,tarfile,hashlib,requests
import numpy as np,rasterio
from .acquisition import Provider
from .core import read_pair
from .debris import debris_candidates
from .event_acquisition import STAC
SCRIPT='''//VERSION=3
function setup(){return {input:["B02","B03","B04","B08","B11","SCL","dataMask"],output:{bands:7,sampleType:"FLOAT32"},mosaicking:"TILE"};}
function evaluatePixel(a){if(a.length!==1)return [0,0,0,0,0,0,0];let s=a[0];return [s.B02,s.B03,s.B04,s.B08,s.B11,s.SCL,s.dataMask];}
function updateOutputMetadata(scenes,inputMetadata,outputMetadata){outputMetadata.userData={scenes:scenes.tiles,inputMetadata:inputMetadata};}'''
def attach_optical(root,config,progress=lambda message:None):
 root=Path(root);dst=root/'prepared';m=json.loads((dst/'manifest.json').read_text());plan=json.loads((root/'plan.json').read_text());event=datetime.fromisoformat(plan['event_date']).replace(tzinfo=timezone.utc);provider=Provider(config);pre,post,valid,profile=read_pair(m,dst);chosen={};records=[]
 for period in ('pre','post'):
  start,end=(event-timedelta(days=14),event-timedelta(seconds=1)) if period=='pre' else (event+timedelta(days=1),event+timedelta(days=14))
  response=requests.get(STAC,params={'collections':'sentinel-2-l2a','bbox':','.join(map(str,plan['bbox'])),'datetime':start.isoformat()+'/'+end.isoformat(),'limit':100},timeout=45);response.raise_for_status();catalogue=response.json();(root/f'optical-{period}-catalogue.json').write_text(json.dumps(catalogue))
  if any(l.get('rel')=='next' for l in catalogue.get('links',[])):raise ValueError('Optical catalogue pagination requires narrower area')
  # Bounded search: three nearest distinct dates, report this selection limit.
  features=sorted(catalogue['features'],key=lambda f:abs((datetime.fromisoformat(f['properties']['datetime'].replace('Z','+00:00'))-event).total_seconds()));days=list(dict.fromkeys(f['properties']['datetime'][:10] for f in features))[:3];best=None
  for day in days:
   progress('Checking clear optical coverage: '+day);folder=root/'optical'/day;folder.mkdir(parents=True,exist_ok=True)
   req={'input':{'bounds':{'bbox':plan['bounds'],'properties':{'crs':f"http://www.opengis.net/def/crs/EPSG/0/{plan['epsg']}"}},'data':[{'type':'sentinel-2-l2a','dataFilter':{'timeRange':{'from':day+'T00:00:00Z','to':day+'T23:59:59Z'}},'processing':{'upsampling':'NEAREST','downsampling':'NEAREST'}}]},'output':{'width':plan['width'],'height':plan['height'],'responses':[{'identifier':'default','format':{'type':'image/tiff'}},{'identifier':'userdata','format':{'type':'application/json'}}]},'evalscript':SCRIPT}
   (folder/'request.json').write_text(json.dumps(req));provider.process(req,folder/'response.tar')
   with tarfile.open(folder/'response.tar') as archive:
    for name in ('default.tif','userdata.json'):
     member=archive.getmember(name)
     if not member.isfile():raise ValueError('Unexpected optical archive member')
     with archive.extractfile(member) as f:(folder/name).write_bytes(f.read())
   with rasterio.open(folder/'default.tif') as ds:
    if ds.count!=7 or any(ds.profile[k]!=profile[k] for k in ('crs','transform','width','height')):raise ValueError('Optical grid contract mismatch')
    a=ds.read();clear=valid&np.isfinite(a).all(0)&np.isin(a[5],[4,5,6])&(a[6]==1);count=int(clear.sum())
   records.append({'period':period,'date':day,'clear_sar_valid_pixels':count,'source_sha256':hashlib.sha256((folder/'default.tif').read_bytes()).hexdigest()})
   if best is None or count>best[0]:best=(count,day,a)
  if best and best[0]>0:chosen[period]=best
 (root/'optical-coverage.json').write_text(json.dumps(records,indent=2))
 m['limitations']=[x for x in m['limitations'] if x!='Automatic debris is not yet available.']
 if len(chosen)==2:
  mask=debris_candidates(chosen['pre'][2],chosen['post'][2],pre,post,valid,valid)
  if np.any(mask!=255):
   p=dst/'debris-candidates.tif';profile.update(count=1,dtype='uint8',nodata=255)
   with rasterio.open(p,'w',**profile) as ds:ds.write(mask,1)
   m['debris']={'path':p.name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'pre_date':chosen['pre'][1],'post_date':chosen['post'][1],'method':'fixed vegetation-to-bare and SAR-change proxy','source_hashes':{r['date']:r['source_sha256'] for r in records},'limitations':'Unvalidated debris proxy; clearing/agriculture can be confused and already-bare deposits missed. SCL is resampled from 20m. Three nearest optical dates per side searched within 14 days; greatest clear coverage selected without reference labels.'}
   m['limitations'].append(m['debris']['limitations'])
  else:m['limitations'].append('Debris not assessed: no jointly valid optical/SAR pixels for the proxy.')
 else:m['limitations'].append('Debris not assessed: no clear pre/post optical pair within bounded search.')
 (dst/'manifest.json').write_text(json.dumps(m,indent=2));return dst/'manifest.json'
