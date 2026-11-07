"""Bounded official native Delhi GIS extraction. Dates/license/negative labels not inferred."""
import argparse,json,time
from pathlib import Path
from datetime import datetime,timezone
import requests
from research.terrain_exposure.io import save_json,sha256

BASE='https://gsdl.org.in/arcgis/rest/services/'
PROTOCOL=Path(__file__).resolve().parents[1]/'experiments/validation-closure-20261107.json'

def get(url,params=None):
    if not url.startswith(BASE):raise ValueError('Only the declared official GIS host/path allowed')
    with requests.get(url,params=params,timeout=(10,40),stream=True) as r:
        r.raise_for_status();chunks=[];size=0
        for chunk in r.iter_content(65536):
            size+=len(chunk)
            if size>32*1024*1024:raise ValueError('Official query exceeds size limit')
            chunks.append(chunk)
    value=json.loads(b''.join(chunks))
    if 'error' in value:raise ValueError('Official GIS query returned an error')
    return value

def acquire(output):
    out=Path(output)
    if out.exists():raise FileExistsError('Keep earlier reference acquisitions immutable')
    out.mkdir(parents=True);protocol=json.loads(PROTOCOL.read_text());cfg=protocol['delhi_drainage'];records=[]
    save_json(out/'protocol.json',protocol)
    for service in cfg['services']:
        url=BASE+service+'/MapServer';metadata=get(url,{'f':'json'});folder=out/service.split('/')[-1];folder.mkdir()
        save_json(folder/'service.json',metadata)
        layers=metadata['layers']
        if service.endswith('sangam'):layers=[x for x in layers if x['id'] in range(8)]
        elif service.endswith('08082024'):layers=[x for x in layers if x['id'] in range(21)]
        else:layers=[x for x in layers if x['name'] in ['WaterLogging_50m','dem']]
        for layer in layers:
            lu=url+'/'+str(layer['id']);lm=get(lu,{'f':'json'});save_json(folder/f"layer-{layer['id']}.json",lm)
            record={'service':service,'layer_id':layer['id'],'name':layer['name'],'metadata_url':lu,
                'license':'NOT_ESTABLISHED;private local research only','observation_date':'UNKNOWN',
                'metadata_sha256':sha256(folder/f"layer-{layer['id']}.json")}
            if lm.get('type')!='Feature Layer':record['state']='METADATA_ONLY'
            else:
                params={'f':'json','where':'1=1','geometry':','.join(map(str,cfg['bbox'])),
                    'geometryType':'esriGeometryEnvelope','inSR':'4326','spatialRel':'esriSpatialRelIntersects','returnIdsOnly':'true'}
                ids=get(lu+'/query',params);identities=sorted(ids.get('objectIds') or [])
                if ids.get('exceededTransferLimit') or len(identities)>25000:raise ValueError('Reference feature budget exceeded')
                record.update(count=len(identities),object_id_field=ids.get('objectIdFieldName'))
                save_json(folder/f"layer-{layer['id']}-ids.json",ids)
                features=[];seen=set()
                for i in range(0,len(identities),200):
                    batch=identities[i:i+200]
                    payload=get(lu+'/query',{'f':'json','objectIds':','.join(map(str,batch)),'outFields':'*',
                        'returnGeometry':'true','outSR':'32643','returnZ':'false','returnM':'false'})
                    if payload.get('exceededTransferLimit'):raise ValueError('Truncated native feature response')
                    rows=payload['features'];actual={r['attributes'][record['object_id_field']] for r in rows}
                    if actual!=set(batch) or seen&actual:raise ValueError('Official feature identity/count mismatch')
                    seen|=actual;features.extend(rows)
                path=folder/f"layer-{layer['id']}-features.json"
                save_json(path,{'spatialReference':{'wkid':32643},'geometryType':lm['geometryType'],
                    'objectIdFieldName':record['object_id_field'],'features':features})
                record.update(state='ACQUIRED_NATIVE_GEOMETRY',file=path.relative_to(out).as_posix(),sha256=sha256(path),bytes=path.stat().st_size)
            records.append(record);save_json(out/'acquisition.json',{'protocol_sha256':sha256(PROTOCOL),'layers':records,
                'retrieved_utc':datetime.now(timezone.utc).isoformat(),'source':'Delhi GeoSpatial Data Limited public ArcGIS services'})
            print(json.dumps({k:record.get(k) for k in ['service','name','state','count']}),flush=True)
    return records

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',required=True);a=p.parse_args();acquire(a.output)
