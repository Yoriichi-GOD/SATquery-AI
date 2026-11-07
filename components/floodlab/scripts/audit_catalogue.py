import json, urllib.request, urllib.parse, datetime
from pathlib import Path
base=Path(__file__).resolve().parents[1]
queries={
 's1-nepal-2026':('https://stac.dataspace.copernicus.eu/v1/search',{'collections':'sentinel-1-grd','bbox':'84.9,27.7,86.1,28.5','datetime':'2026-08-10T00:00:00Z/2026-09-10T23:59:59Z','limit':100}),
 's2-nepal-2026':('https://stac.dataspace.copernicus.eu/v1/search',{'collections':'sentinel-2-l1c','bbox':'84.9,27.7,86.1,28.5','datetime':'2026-08-10T00:00:00Z/2026-09-10T23:59:59Z','limit':100}),
 'ohsome-metadata':('https://api.ohsome.org/v1/metadata',{}),
}
for name,(url,params) in queries.items():
    full=url+'?'+urllib.parse.urlencode(params) if params else url
    try:
        with urllib.request.urlopen(full,timeout=35) as r:
            body=r.read(); status=r.status
        (base/'data/catalogue'/f'{name}.json').write_bytes(body)
        data=json.loads(body)
        print(name,status,'features',len(data.get('features',[])),json.dumps(data.get('context',data.get('temporalExtent',{}))))
        if data.get('features'): print(json.dumps(data['features'][0])[:2500])
    except Exception as e: print(name,type(e).__name__,str(e))
