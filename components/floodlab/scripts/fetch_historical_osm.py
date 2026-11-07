from pathlib import Path
import json,hashlib,requests,datetime
B=Path(__file__).resolve().parents[1]
config={}
for line in (B/'.env.local').read_text().splitlines():
 if '=' in line and not line.lstrip().startswith('#'):
  k,v=line.split('=',1);config[k.strip()]=v.strip().strip('\"').strip("'")
key=config.get('OHSOME_API_KEY')
if not key:raise SystemExit('HeiGIT key is missing')
url='https://api.heigit.org/ohsome-api/v2-rc/extraction/features.parquet'
out=B/'data/osm_pre_event';out.mkdir(exist_ok=True)
# Bounded corridor includes both official AOIs and routing context southwards.
bbox=[85.25,27.90,85.45,28.35]
w,s,e,n=bbox
payload={'aoi':{'type':'Polygon','coordinates':[[[w,s],[e,s],[e,n],[w,n],[w,s]]]},'filter':'building=* or highway=* or bridge=* or place=* or amenity=hospital','time':'2026-07-27T00:00:00Z','clip':False}
p=out/'nepal-corridor-20260727.parquet'
if not p.exists():
 r=requests.post(url,json=payload,headers={'Authorization':key},timeout=(20,240),allow_redirects=False)
 print('Historical OSM HTTP',r.status_code,flush=True)
 if r.status_code!=200:raise SystemExit('Historical OSM request failed; credentials not logged')
 raw=r.content
 if raw[:4]!=b'PAR1' or raw[-4:]!=b'PAR1':raise SystemExit('Response is not Parquet')
 p.write_bytes(raw)
manifest={'source':url,'request':payload,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'role':'historical_osm','retrieved_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'license':'ODbL; OpenStreetMap contributors','topology_verified':False}
(out/'manifest.json').write_text(json.dumps(manifest,indent=2))
print('Historical OSM saved:',p.name,manifest['bytes'],'bytes',flush=True)
