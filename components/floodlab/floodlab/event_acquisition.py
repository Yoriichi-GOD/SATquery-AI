"""Bounded area/date satellite acquisition; no evaluation maps enter this path."""
from datetime import datetime,timedelta,timezone
import math,json,time
from pathlib import Path
import requests
from shapely.geometry import box,shape
from pyproj import Transformer
from .acquisition import Provider
STAC='https://stac.dataspace.copernicus.eu/v1/search'
def validate_area(bbox):
 if len(bbox)!=4 or not all(math.isfinite(x) for x in bbox):raise ValueError('Four finite bbox coordinates required')
 w,s,e,n=bbox
 if not -180<=w<e<=180 or not -80<=s<n<=84:raise ValueError('Require west<east and south<north inside supported UTM latitudes; antimeridian unsupported')
 return box(w,s,e,n)
def discover(bbox,event_date):
 aoi=validate_area(bbox);event=datetime.fromisoformat(event_date).replace(tzinfo=timezone.utc)
 if event.time()!=datetime.min.time():raise ValueError('Use a YYYY-MM-DD event date')
 def catalogue(start,end):
  params={'collections':'sentinel-1-grd','bbox':','.join(map(str,bbox)),'datetime':start.isoformat().replace('+00:00','Z')+'/'+end.isoformat().replace('+00:00','Z'),'limit':100}
  r=requests.get(STAC,params=params,timeout=45);r.raise_for_status();data=r.json()
  if any(l.get('rel')=='next' for l in data.get('links',[])):raise ValueError('Catalogue needs pagination; narrow date/area before acquisition')
  return data['features']
 before=catalogue(event-timedelta(days=25),event-timedelta(microseconds=1));after=catalogue(event+timedelta(days=1),event+timedelta(days=25));pairs=[]
 dt=lambda f:datetime.fromisoformat(f['properties']['datetime'].replace('Z','+00:00'))
 for pre in before:
  for post in after:
   if any(pre['properties'].get(k) is None or pre['properties'].get(k)!=post['properties'].get(k) for k in ('platform','sat:relative_orbit','sat:orbit_state')):continue
   if not 11.9<=(dt(post)-dt(pre)).total_seconds()/86400<=12.1:continue
   if not shape(pre['geometry']).covers(aoi) or not shape(post['geometry']).covers(aoi):continue
   if not all(set(f['properties'].get('sar:polarizations',[]))>={'VV','VH'} for f in (pre,post)):continue
   pairs.append((pre,post))
 if not pairs:raise ValueError('No same-platform, same-orbit, dual-polarization 12-day pair fully covers this area')
 pre,post=min(pairs,key=lambda p:((dt(p[1])-event).total_seconds(),(event-dt(p[0])).total_seconds()))
 center=aoi.centroid;epsg=(32600 if center.y>=0 else 32700)+min(60,int((center.x+180)//6)+1);project=Transformer.from_crs(4326,epsg,always_xy=True)
 pts=[project.transform(x,y) for x,y in aoi.exterior.coords];xs,ys=zip(*pts);bounds=[math.floor(min(xs)/10)*10,math.floor(min(ys)/10)*10,math.ceil(max(xs)/10)*10,math.ceil(max(ys)/10)*10];width=(bounds[2]-bounds[0])//10;height=(bounds[3]-bounds[1])//10
 if width*height>1_000_000 or max(width,height)>2500:raise ValueError('Current automatic-run limit is one million 10m pixels and 2500 pixels per side; choose a smaller AOI. Large-area tiling is not yet verified.')
 return {'bbox':bbox,'event_date':event_date,'epsg':epsg,'bounds':bounds,'width':width,'height':height,'pre':pre,'post':post,'selection':'earliest post-event full-coverage 12-day same-orbit pair; no reference labels','limitations':['Bounded AOI, no antimeridian support; catalogue pagination fails closed.','Automatic water baseline only; debris and road topology require their own prepared stages.']}
def acquire(plan,destination,config,progress=lambda text:None):
 root=Path(destination);root.mkdir(parents=True,exist_ok=False);(root/'plan.json').write_text(json.dumps(plan,indent=2));provider=Provider(config)
 template=json.loads((Path(__file__).resolve().parents[1]/'configs/sar-request.json').read_text())
 for period in ('pre','post'):
  feature=plan[period];stamp=datetime.fromisoformat(feature['properties']['datetime'].replace('Z','+00:00'));request=json.loads(json.dumps(template));request['input']['bounds']={'bbox':plan['bounds'],'properties':{'crs':f"http://www.opengis.net/def/crs/EPSG/0/{plan['epsg']}"}};request['output']['width']=plan['width'];request['output']['height']=plan['height'];flt=request['input']['data'][0]['dataFilter'];flt['timeRange']={'from':(stamp-timedelta(seconds=5)).isoformat().replace('+00:00','Z'),'to':(stamp+timedelta(seconds=5)).isoformat().replace('+00:00','Z')};flt['orbitDirection']=feature['properties']['sat:orbit_state'].upper();p=root/period;p.mkdir();(p/'request.json').write_text(json.dumps(request,indent=2));progress('Processing '+period+' Sentinel-1 acquisition');provider.process(request,p/'response.tar')
 return root
