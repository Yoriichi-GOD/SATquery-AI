"""Frozen saved-run adapter and immutable field-kit exports for network scenarios."""
from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path
import re
import threading
import zipfile
import xml.etree.ElementTree as ET

import networkx as nx
from pyproj import Transformer
import rasterio

from .core import metric_crs
from .response import assess,rank_repairs

ARTIFACTS={'response.json':'application/json','routes.geojson':'application/geo+json','facts.json':'application/json',
           'fieldkit.kml':'application/vnd.google-earth.kml+xml','alert-en.txt':'text/plain; charset=utf-8',
           'alert-ne.txt':'text/plain; charset=utf-8','evidence.json':'application/json','bundle.zip':'application/zip'}


def digest(raw):return hashlib.sha256(raw).hexdigest()
def encode(value):return (json.dumps(value,ensure_ascii=False,sort_keys=True,allow_nan=False,indent=2)+'\n').encode()
def strict_json(raw):return json.loads(raw,parse_constant=lambda _: (_ for _ in ()).throw(ValueError('Nonfinite JSON value')))


class ResponseStore:
    def __init__(self,runs,output):
        self.runs=Path(runs);self.output=Path(output);self.lock=threading.Lock()

    def _source(self,run_id):
        if not re.fullmatch(r'[A-Za-z0-9_-]{1,100}',run_id):raise ValueError('Invalid saved run ID')
        root=(self.runs/run_id).resolve()
        if not root.is_relative_to(self.runs.resolve()) or not root.is_dir():raise FileNotFoundError('Saved run not found')
        frozen=(root/'freeze.json').read_bytes()
        if len(frozen)>1024*1024:raise ValueError('Freeze manifest too large')
        freeze=strict_json(frozen);files=freeze.get('files')
        if not isinstance(files,dict):raise ValueError('Incomplete saved run')
        values={};hashes={}
        names=['graph.json','connectivity.json','result.json','manifest.json','prediction.tif']
        names += [name for name in ['topology-audit.json','layers.geojson'] if name in files]
        for name in names:
            path=(root/name).resolve()
            if not path.is_relative_to(root) or not path.is_file() or path.stat().st_size>64*1024*1024:
                raise ValueError('Missing or oversized frozen response input: '+name)
            raw=path.read_bytes()
            if not re.fullmatch(r'[a-f0-9]{64}',str(files.get(name))) or digest(raw)!=files[name]:
                raise ValueError('Frozen source integrity mismatch: '+name)
            hashes[name]=files[name]
            if name.endswith('.json') or name.endswith('.geojson'):values[name]=strict_json(raw)
        with rasterio.open(root/'prediction.tif') as src:
            metric_crs(src.crs);crs=src.crs.to_string()
        raw_graph=values['graph.json'];g=nx.MultiDiGraph()
        if len(raw_graph['nodes'])>100_000 or len(raw_graph['edges'])>300_000:raise ValueError('Saved graph exceeds response limits')
        for node in raw_graph['nodes']:
            identity=str(node['id']);xy=node['xy']
            if identity in g or len(xy)!=2 or not all(__import__('math').isfinite(v) for v in xy):raise ValueError('Invalid graph node')
            g.add_node(identity,xy=xy)
        for edge in raw_graph['edges']:
            u,v=str(edge['u']),str(edge['v']);key=str(edge['edge_id'])
            if u not in g or v not in g or g.has_edge(u,v,key):raise ValueError('Invalid/duplicate graph edge')
            g.add_edge(u,v,key=key,**{k:value for k,value in edge.items() if k not in {'u','v'}})
        places=[]
        for row in values['connectivity.json']:
            places.append({**row,'node_id':None if row.get('node_id') is None else str(row['node_id'])})
        audit=values.get('topology-audit.json',{})
        hubs=[str(h['node_id']) for h in audit.get('hubs',[]) if h.get('node_id') is not None]
        # Older synthetic runs store their destination set in manifest, never infer it from graph endpoints.
        if not hubs and values['result.json'].get('synthetic'):
            hubs=[str(v) for v in audit.get('hub_node_ids',[])]
        source={'run_id':run_id,'population':'SYNTHETIC_SOFTWARE_TEST' if values['result.json'].get('synthetic') else 'GENUINE_SAVED_NETWORK_REPLAY',
                'freeze_sha256':digest(frozen),'files':hashes,'crs':crs,
                'event_time':values['manifest.json']['event_time'],'infrastructure_snapshot':values['manifest.json']['osm_snapshot'],
                'destination_basis':'Historical mapped service hubs; facility type/capacity and physical connectors not independently verified'}
        return g,places,hubs,source

    def calculate(self,run_id,restore_way_ids=()):
        graph,places,hubs,source=self._source(run_id)
        code=digest(Path(__file__).read_bytes()+Path(__file__).with_name('response.py').read_bytes())
        cache_id=digest(encode({'source':source,'restore_way_ids':sorted(restore_way_ids),'code':code}))[:24]
        folder=self.output/run_id/cache_id
        if (folder/'evidence.json').is_file():
            return self._read(folder,run_id,cache_id)
        if not self.lock.acquire(blocking=False):raise RuntimeError('Another response scenario is running')
        try:
            response=assess(graph,places,hubs,restore_way_ids)
            response['candidate_way_ids']=sorted({e['source_id'] for _,_,e in graph.edges(data=True) if e['state']=='disrupted'})
            response.update(source=source,scenario_id=cache_id,
                repair_search=rank_repairs(graph,places,hubs,restore_way_ids),algorithm_sha256=code)
            response['state']='COMPLETE_SCENARIO' if response['hubs_used'] else 'NOT_ASSESSED_NO_HUBS'
            projector=Transformer.from_crs(source['crs'],'EPSG:4326',always_xy=True)
            features=[]
            for row in response['rows']:
                if row['node_id'] in graph:
                    xy=graph.nodes[row['node_id']]['xy'];point=list(projector.transform(*xy))
                else:point=None
                features.append({'type':'Feature','id':row['id'],'geometry':{'type':'Point','coordinates':point} if point else None,
                    'properties':{'kind':'network-snap-point','name':row['name'],'status':row['status'],
                                  'note':'Mapped network snap location, not surveyed settlement coordinates'}})
                for mode,route in row.get('routes',{}).items():
                    if route is None:continue
                    coordinates=[list(projector.transform(*graph.nodes[n]['xy'])) for n in route['node_ids']]
                    if len(coordinates)<2:continue
                    features.append({'type':'Feature','id':str(row['id'])+':'+mode,
                        'geometry':{'type':'LineString','coordinates':coordinates},
                        'properties':{'kind':'response-route','settlement_id':row['id'],'mode':mode,
                            'length_m':route['length_m'],'unknown_segments':route['unobserved_segments'],
                            'repairs_assumed':list(restore_way_ids),'scope':response['mode']}})
            routes={'type':'FeatureCollection','features':features}
            facts=[{'id':key,'value':value,'unit':'settlements','source':'response.json#/summary/'+key}
                   for key,value in response['summary'].items()]
            assessed=response['state']=='COMPLETE_SCENARIO'
            count=str(response['summary']['observation_supported_mapped_routes']) if assessed else 'NOT ASSESSED'
            alert_en=(f"EXPERIMENTAL NETWORK SCENARIO · {run_id}\nHistorical map: {source['infrastructure_snapshot']}\n"
                f"Settlements with an observation-supported mapped route in this scenario: {count}.\n"
                f"Assumed candidate-way repairs: {', '.join(restore_way_ids) or 'none'}.\n"
                'Not confirmed damage, road access or a safe-route instruction. Unknown observations and AOI limits remain.\n')
            alert_ne=(f"प्रयोगात्मक सडक सञ्जाल परिदृश्य · {run_id}\nअवलोकनले समर्थन गरेको नक्साको मार्ग भएका बस्ती: {count}।\n"
                'यो वास्तविक क्षति, सडक पहुँच वा सुरक्षित मार्गको पुष्टि होइन। नदेखिएको क्षेत्र र नक्साको सीमा बाँकी छन्।\n'
                'नेपाली पाठको मानव समीक्षा बाँकी छ।\n')
            blobs={'response.json':encode(response),'routes.geojson':encode(routes),'facts.json':encode(facts),
                   'fieldkit.kml':self._kml(features),'alert-en.txt':alert_en.encode(),'alert-ne.txt':alert_ne.encode()}
            evidence={'state':'complete','source':source,'algorithm_sha256':code,'scenario_id':cache_id,
                'files':{name:digest(raw) for name,raw in blobs.items()},'scope':response['mode']}
            blobs['evidence.json']=encode(evidence)
            memory=io.BytesIO()
            with zipfile.ZipFile(memory,'w',compression=zipfile.ZIP_DEFLATED) as archive:
                for name,raw in blobs.items():archive.writestr(name,raw)
            blobs['bundle.zip']=memory.getvalue()
            folder.mkdir(parents=True,exist_ok=True)
            for name,raw in blobs.items():
                if name=='evidence.json':continue
                (folder/name).write_bytes(raw)
            # Evidence manifest is the completion marker; incomplete exports are never served.
            (folder/'evidence.json').write_bytes(blobs['evidence.json'])
            return self._read(folder,run_id,cache_id)
        finally:self.lock.release()

    def _read(self,folder,run_id,scenario_id):
        evidence=strict_json((folder/'evidence.json').read_bytes())
        if evidence.get('state')!='complete' or set(evidence.get('files',{}))!=set(ARTIFACTS)-{'evidence.json','bundle.zip'}:
            raise ValueError('Incomplete scenario export')
        for name,expected in evidence['files'].items():
            if name not in ARTIFACTS or digest((folder/name).read_bytes())!=expected:raise ValueError('Scenario export integrity mismatch')
        response=strict_json((folder/'response.json').read_bytes())
        response['artifacts']=[{'name':name,'url':f'/api/response/runs/{run_id}/scenarios/{scenario_id}/{name}'} for name in ARTIFACTS]
        return response

    def artifact(self,run_id,scenario_id,name):
        if (not re.fullmatch(r'[A-Za-z0-9_-]{1,100}',run_id) or not re.fullmatch(r'[a-f0-9]{24}',scenario_id) or name not in ARTIFACTS):
            raise FileNotFoundError('Unknown response artifact')
        folder=(self.output/run_id/scenario_id).resolve()
        if not folder.is_relative_to(self.output.resolve()) or not (folder/'evidence.json').is_file():raise FileNotFoundError('Scenario incomplete or missing')
        self._read(folder,run_id,scenario_id)
        raw=(folder/name).read_bytes()
        if name=='bundle.zip':
            evidence=strict_json((folder/'evidence.json').read_bytes())
            with zipfile.ZipFile(io.BytesIO(raw)) as archive:
                expected={*evidence['files'],'evidence.json'}
                if set(archive.namelist())!=expected or archive.testzip() is not None:raise ValueError('Invalid field-kit archive')
                if archive.read('evidence.json')!=(folder/'evidence.json').read_bytes():raise ValueError('Archive provenance mismatch')
                for item in evidence['files']:
                    if digest(archive.read(item))!=evidence['files'][item]:raise ValueError('Archive hash mismatch')
        return raw,digest(raw)

    @staticmethod
    def _kml(features):
        ns='http://www.opengis.net/kml/2.2';ET.register_namespace('',ns)
        root=ET.Element('{'+ns+'}kml');doc=ET.SubElement(root,'{'+ns+'}Document')
        ET.SubElement(doc,'{'+ns+'}name').text='Flood Lab — experimental mapped-network scenario'
        for feature in features:
            p=ET.SubElement(doc,'{'+ns+'}Placemark');props=feature['properties'];geom=feature['geometry']
            ET.SubElement(p,'{'+ns+'}name').text=str(props.get('name') or feature['id'])
            ET.SubElement(p,'{'+ns+'}description').text=json.dumps(props,ensure_ascii=False)
            if geom:
                geometry=ET.SubElement(p,'{'+ns+'}'+('Point' if geom['type']=='Point' else 'LineString'))
                coords=[geom['coordinates']] if geom['type']=='Point' else geom['coordinates']
                ET.SubElement(geometry,'{'+ns+'}coordinates').text=' '.join(f'{x},{y},0' for x,y in coords)
        return ET.tostring(root,encoding='utf-8',xml_declaration=True)
