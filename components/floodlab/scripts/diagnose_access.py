import requests,json
from pathlib import Path
b=Path(__file__).resolve().parents[1]/'data/catalogue'
params={'bboxes':'85.25,28.05,85.40,28.20','time':'2026-07-27T00:00:00Z','filter':'building=* or highway=* or bridge=* or place=* or amenity=hospital','properties':'tags,metadata'}
try:
 r=requests.post('https://api.ohsome.org/v1/elements/geometry',data=params,timeout=45)
 print('OSM POST',r.status_code,r.text[:400])
 if r.ok:(b/'osm-nepal-20260727.geojson').write_text(r.text)
except Exception as e:print(type(e).__name__,str(e))
try:
 d=json.loads((b/'pc-s1-nepal-2026.json').read_text()); href=d['features'][0]['assets']['vv']['href']
 r=requests.get(href,headers={'Range':'bytes=0-31'},timeout=20); print('PC direct asset',r.status_code,r.text[:200] if not r.ok else 'accessible')
except Exception as e:print(type(e).__name__,str(e))
