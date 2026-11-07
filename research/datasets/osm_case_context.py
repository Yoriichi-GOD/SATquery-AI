"""Bounded historical OSM context. Missing mapped objects are never negative labels."""
import argparse,json,time
from pathlib import Path
from datetime import datetime,timezone
import requests
from research.cases.acquire_campaign import PROTOCOL
from research.terrain_exposure.io import save_json,sha256,canonical_hash

ENDPOINTS=['https://overpass-api.de/api/interpreter','https://overpass.kumi.systems/api/interpreter']

def run(output):
    output=Path(output);cfg=json.loads(PROTOCOL.read_text());records={}
    for case in ['kedarnath','varanasi','sangam-vihar']:
        folder=output/case;folder.mkdir(parents=True,exist_ok=True)
        path=folder/'osm-context.json';receipt=folder/'osm-context.source.json'
        if path.exists() and receipt.exists():
            r=json.loads(receipt.read_text())
            if sha256(path)!=r['sha256']:raise ValueError('OSM context cache changed')
            records[case]=r;continue
        date='2013-06-15T00:00:00Z' if case=='kedarnath' else '2023-12-31T23:59:59Z'
        w,s,e,n=cfg['cases'][case]['bbox'];bbox=f'({s},{w},{n},{e})'
        query=f'[out:json][timeout:25][maxsize:33554432][date:"{date}"];('
        query+=f'nwr[amenity~"^(hospital|clinic|fire_station|police|school)$"]{bbox};'
        query+=f'way[waterway~"^(river|stream|drain|ditch|canal)$"]{bbox};'
        query+=f'way[highway~"^(primary|secondary|tertiary|primary_link|secondary_link|tertiary_link)$"]{bbox};);out geom;'
        save_json(folder/'osm-query-protocol.json',{'query':query,'query_sha256':canonical_hash(query),'maximum_response_bytes':16*1024*1024,
            'role':'Historical mapped context, not complete surveyed infrastructure or validation labels',
            'dates':'OSM database state, not construction date or historical physical verification'})
        attempts=[];done=False
        for endpoint in ENDPOINTS:
            try:
                with requests.post(endpoint,data={'data':query},timeout=(10,45),stream=True) as response:
                    response.raise_for_status();chunks=[];total=0
                    for chunk in response.iter_content(65536):
                        total+=len(chunk)
                        if total>16*1024*1024:raise ValueError('OSM response exceeds budget')
                        chunks.append(chunk)
                payload=json.loads(b''.join(chunks))
                if payload.get('remark'):raise ValueError('Overpass reported incomplete result')
                if 'elements' not in payload:raise ValueError('Missing OSM elements')
                save_json(path,payload)
                r={'state':'ACQUIRED','source_url':endpoint,'query_sha256':canonical_hash(query),'snapshot':date,
                    'elements':len(payload['elements']),'sha256':sha256(path),'bytes':path.stat().st_size,
                    'license':'ODbL1.0 https://www.openstreetmap.org/copyright','retrieved_utc':datetime.now(timezone.utc).isoformat(),
                    'role':'Historical mapped context; completeness and event-time reality unverified','attempts':attempts}
                save_json(receipt,r);records[case]=r;done=True;break
            except Exception as exc:
                attempts.append({'endpoint':endpoint,'error_type':type(exc).__name__,
                    'http_status':getattr(getattr(exc,'response',None),'status_code',None)})
        if not done:
            records[case]={'state':'UNAVAILABLE','attempts':attempts};save_json(folder/'osm-unavailable.json',records[case])
        print(json.dumps({'case':case,'state':records[case]['state'],'elements':records[case].get('elements')}),flush=True)
    save_json(output/'osm-acquisition-summary.json',records)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',required=True);a=p.parse_args();run(a.output)
