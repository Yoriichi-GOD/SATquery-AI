import requests,json
from pathlib import Path
B=Path(__file__).resolve().parents[1]
q='[out:json][timeout:45][date:"2026-07-27T00:00:00Z"];(way["highway"](28.12,85.30,28.20,85.38););(._;>;);out body;'
r=requests.post('https://overpass-api.de/api/interpreter',data={'data':q},timeout=60)
print('Historical road topology HTTP',r.status_code,flush=True)
if r.ok:
 d=r.json()
 if d.get('remark'):raise SystemExit('Incomplete response: '+d['remark'])
 p=B/'data/osm_pre_event/syapru-road-topology.json';p.write_text(json.dumps(d))
 print('Elements',len(d.get('elements',[])))
else:print('No topology acquired')
