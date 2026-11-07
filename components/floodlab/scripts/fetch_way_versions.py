from pathlib import Path
import json,time,hashlib,requests,concurrent.futures,threading
import pyarrow.parquet as pq
B=Path(__file__).resolve().parents[1];out=B/'data/osm_pre_event/way_versions';out.mkdir(exist_ok=True)
allowed={'motorway','trunk','primary','secondary','tertiary','unclassified','residential','service','motorway_link','trunk_link','primary_link','secondary_link','tertiary_link','living_street'}
rows=pq.read_table(B/'data/osm_pre_event/nepal-corridor-20260727.parquet',columns=['osm_type','osm_id','version','tags','geom']).to_pylist()
ways=[r for r in rows if r['osm_type']=='way' and dict(r['tags']).get('highway') in allowed]
lock=threading.Lock();last=[0.]
def fetch(r):
 p=out/f"{r['osm_id']}-v{r['version']}.json"
 if p.exists():return True
 with lock:
  time.sleep(max(0,0.6-(time.monotonic()-last[0])));last[0]=time.monotonic()
 url=f"https://api.openstreetmap.org/api/0.6/way/{r['osm_id']}/{r['version']}.json"
 try:
  res=requests.get(url,headers={'User-Agent':'SatQuery-FloodLab research prototype'},timeout=25)
  if res.status_code!=200:return {'id':r['osm_id'],'http':res.status_code}
  d=res.json();e=d['elements'][0]
  if e['id']!=r['osm_id'] or e['version']!=r['version'] or not e.get('nodes'):return {'id':r['osm_id'],'error':'identity mismatch'}
  p.write_text(json.dumps(d));return True
 except requests.RequestException:return {'id':r['osm_id'],'error':'network failure'}
errors=[]
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
 for n,result in enumerate(pool.map(fetch,ways),1):
  if result is not True:errors.append(result)
  if n%50==0:print('Historical ways checked',n,'/',len(ways),flush=True)
summary={'requested':len(ways),'downloaded':len(ways)-len(errors),'errors':errors,'allowed_highways':sorted(allowed),'source':'https://api.openstreetmap.org/api/0.6/way/{id}/{historical_version}.json','snapshot':'2026-07-27T00:00:00Z'}
(out/'registry.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary),flush=True)
