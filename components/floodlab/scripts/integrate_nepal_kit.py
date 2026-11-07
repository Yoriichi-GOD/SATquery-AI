import json,sqlite3,hashlib,struct,concurrent.futures,datetime,os
from pathlib import Path
import requests
from shapely import from_wkb
from shapely.geometry import mapping,shape
B=Path(__file__).resolve().parents[1]
def save(p,x):p.write_text(json.dumps(x,indent=2,ensure_ascii=False),encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
refs=[];aois=[]
for area,filename in [('syapru_besi','EMSR927_AOI01_GRA_PRODUCT_v1.gpkg'),('timure','EMSR927_AOI02_GRA_PRODUCT_v2.gpkg')]:
 p=B/'evaluation_only/emsr'/filename;c=sqlite3.connect(p.as_uri()+'?mode=ro',uri=True)
 integrity=c.execute('PRAGMA quick_check').fetchone()[0]
 layers=c.execute('SELECT table_name,geometry_type_name,srs_id,column_name FROM gpkg_geometry_columns').fetchall()
 layer=next(x for x in layers if x[0].startswith('areaOfInterestA'))
 if layer[2]!=4326:raise ValueError('Unexpected AOI CRS')
 geoms=[]
 for (blob,) in c.execute(f'SELECT "{layer[3]}" FROM "{layer[0]}"'):
  if blob[:2]!=b'GP':raise ValueError('Invalid GeoPackage geometry')
  envelope=(blob[3]>>1)&7;offset=8+{0:0,1:32,2:48,3:48,4:64}[envelope]
  g=from_wkb(blob[offset:])
  if not g.is_valid:raise ValueError('Invalid AOI geometry')
  geoms.append(g)
 from shapely.ops import unary_union
 g=unary_union(geoms)
 aois.append({'type':'Feature','properties':{'id':area,'source_file':filename,'source_sha256':sha(p),'source_layer':layer[0],'use':'Geographic boundary only; no damage geometry inspected'},'geometry':mapping(g)})
 refs.append({'area':area,'filename':filename,'bytes':p.stat().st_size,'sha256':sha(p),'integrity':integrity,'role':'evaluation_only','layers':[{'name':a,'geometry':b,'epsg':s} for a,b,s,_ in layers],'damage_features_inspected':False})
 c.close()
save(B/'data/aoi/nepal-official-boundaries.geojson',{'type':'FeatureCollection','features':aois})
save(B/'evaluation_only/emsr/registry.json',refs)
kit=json.loads((B/'data/acquisition-kit/aoi/nepal_aoi_bbox.geojson').read_text())
print('References registered; AOI-only boundaries extracted',flush=True)
windows={'pre':'2026-07-20T00:00:00Z/2026-08-25T23:59:59Z','post':'2026-08-27T00:00:00Z/2026-09-30T23:59:59Z'}
def discover(task):
 a,sensor,period=task
 cached=B/'data/metadata'/f"{a['properties']['id']}_{sensor}_{period}.json"
 if cached.exists():return cached.stem,json.loads(cached.read_text())['stac']
 g=shape(a['geometry']);params={'collections':{'s1':'sentinel-1-grd','s2':'sentinel-2-l2a'}[sensor],'bbox':','.join(map(str,g.bounds)),'datetime':windows[period],'limit':100}
 r=requests.get('https://stac.dataspace.copernicus.eu/v1/search',params=params,timeout=35);r.raise_for_status();d=r.json()
 if any(l.get('rel')=='next' for l in d.get('links',[])):raise ValueError('Pagination required before selecting scenes')
 name=f"{a['properties']['id']}_{sensor}_{period}"
 save(B/'data/metadata'/f'{name}.json',{'url':r.url,'stac':d})
 print(name,len(d.get('features',[])),flush=True);return name,d
results={};errors=[]
with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
 futs=[pool.submit(discover,(a,s,p)) for a in aois for s in ('s1','s2') for p in windows]
 for f in concurrent.futures.as_completed(futs):
  try:k,d=f.result();results[k]=d
  except Exception as e:errors.append(str(e))
selections=[]
for a in aois:
 name=a['properties']['id'];aoi=shape(a['geometry']);candidates=[]
 for pre in results.get(name+'_s1_pre',{}).get('features',[]):
  for post in results.get(name+'_s1_post',{}).get('features',[]):
   x,y=pre['properties'],post['properties'];keys=['sat:relative_orbit','sat:orbit_state','platform']
   if any(x.get(k) is None or x.get(k)!=y.get(k) for k in keys):continue
   if not shape(pre['geometry']).covers(aoi) or not shape(post['geometry']).covers(aoi):continue
   t=lambda p:datetime.datetime.fromisoformat(p['datetime'].replace('Z','+00:00'))
   gap=(t(y)-t(x)).total_seconds()/86400
   if not 11.9<=gap<=12.1:continue
   candidates.append({'pre':pre['id'],'post':post['id'],'pre_datetime':x['datetime'],'post_datetime':y['datetime'],'relative_orbit':x['sat:relative_orbit'],'orbit_state':x['sat:orbit_state'],'platform':x['platform'],'gap_days':gap,'full_aoi_footprint_coverage':True,'imagery_downloaded':False})
 candidates.sort(key=lambda x:x['post_datetime'])
 old=next(f for f in kit['features'] if f['properties']['id']==name)
 selections.append({'area':name,'official_bounds':list(aoi.bounds),'kit_bounds':list(shape(old['geometry']).bounds),'candidate_pairs':candidates,'recommended_metadata_pair':candidates[0] if candidates else None})
report={'references':refs,'areas':selections,'catalogue_counts':{k:len(v['features']) for k,v in sorted(results.items())},'errors':errors,'credentials_present':{k:bool(os.environ.get(k)) for k in ['CDSE_ACCESS_TOKEN','OHSOME_API_KEY']},'status':'Metadata and reference registration only; no imagery or historical OSM downloaded','remaining':['Authenticated scene download','SAR calibration and terrain correction','DEM acquisition','Historical OSM including road topology and routing context','Optical preparation and cloud masks','Real prediction, AI integration and independent scoring']}
save(B/'docs/dataset-readiness.json',report)
print(json.dumps({'areas':selections,'errors':errors,'credentials_present':report['credentials_present']},indent=2),flush=True)

