import json,urllib.request,urllib.parse
from pathlib import Path
b=Path(__file__).resolve().parents[1]/'data/catalogue'
url='https://planetarycomputer.microsoft.com/api/stac/v1/search?'+urllib.parse.urlencode({'collections':'sentinel-1-rtc','bbox':'85.15,27.85,85.55,28.35','datetime':'2026-08-10T00:00:00Z/2026-09-10T23:59:59Z','limit':100})
try:
 with urllib.request.urlopen(url,timeout=35) as r: data=r.read()
 (b/'pc-s1-nepal-2026.json').write_bytes(data)
 d=json.loads(data); print('PC features',len(d.get('features',[]))); print(json.dumps(d.get('features',[{}])[:1])[:1200])
except Exception as e: print(type(e).__name__,str(e))
d=json.loads((b/'s1-nepal-2026.json').read_text()); a=d['features'][0]['assets']['vv']['alternate']['https']['href']
try:
 with urllib.request.urlopen(urllib.request.Request(a,headers={'Range':'bytes=0-31'}),timeout=30) as r: print('CDSE asset access',r.status,r.read(32))
except Exception as e: print('CDSE asset access',type(e).__name__,str(e))
params={'bboxes':'85.25,28.05,85.40,28.20','time':'2026-07-27T00:00:00Z','filter':'building=* or highway=* or bridge=* or place=* or amenity=hospital','properties':'tags,metadata'}
try:
 url='https://api.ohsome.org/v1/elements/geometry?'+urllib.parse.urlencode(params)
 with urllib.request.urlopen(url,timeout=45) as r: data=r.read()
 (b/'osm-nepal-20260727.geojson').write_bytes(data); d=json.loads(data); print('OSM features',len(d.get('features',[])))
except Exception as e: print('OSM extract',type(e).__name__,str(e))
