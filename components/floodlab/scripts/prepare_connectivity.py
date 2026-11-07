from pathlib import Path
import json,hashlib,datetime,shutil
import pyarrow.parquet as pq
import numpy as np
from scipy.spatial import cKDTree
from shapely import from_wkb
from shapely.geometry import mapping,shape,box
from shapely.ops import transform
from pyproj import Transformer
import networkx as nx
from floodlab.historical import historical_road
from floodlab.impact import road_graph
B=Path(__file__).resolve().parents[1];src=B/'data/prepared/syapru-20260826';dst=B/'data/prepared/syapru-connectivity';dst.mkdir(exist_ok=True)
for name in ('pre.tif','post.tif','quality.json'):shutil.copy2(src/name,dst/name)
infra=json.loads((src/'infrastructure.json').read_text());manifest=json.loads((src/'manifest.json').read_text());when=datetime.datetime.fromisoformat(manifest['osm_snapshot'].replace('Z','+00:00'));proj=Transformer.from_crs(4326,32645,always_xy=True).transform
rows=pq.read_table(B/'data/osm_pre_event/nepal-corridor-20260727.parquet',columns=['osm_type','osm_id','version','tags','geom','edit_timestamp','valid_to_timestamp']).to_pylist();roads=[];excluded=[];way_hashes={}
for row in rows:
 p=B/'data/osm_pre_event/way_versions'/f"{row['osm_id']}-v{row['version']}.json"
 if row['osm_type']!='way' or not p.exists():continue
 row['geometry']=mapping(from_wkb(row['geom']))
 try:r,reason=historical_road(row,json.loads(p.read_text())['elements'][0],proj,when)
 except ValueError as e:excluded.append({'id':row['osm_id'],'reason':str(e)});continue
 if r:roads.append(r);way_hashes[p.name]=hashlib.sha256(p.read_bytes()).hexdigest()
 else:excluded.append({'id':row['osm_id'],'reason':reason})
# Graph coordinates must agree globally; never merge crossing coordinates.
g,_,_=road_graph(roads,box(0,0,0,0),box(-1e9,-1e9,1e9,1e9),'EPSG:32645')
nodes=list(g.nodes);xy=np.array([g.nodes[n]['xy'] for n in nodes]);tree=cKDTree(xy)
footprint=transform(proj,box(85.25,27.90,85.45,28.35));boundary_nodes={n for n in nodes if footprint.boundary.distance(shape({'type':'Point','coordinates':g.nodes[n]['xy']}))<150 or not footprint.covers(shape({'type':'Point','coordinates':g.nodes[n]['xy']}))}
components={};touch={}
for i,c in enumerate(nx.weakly_connected_components(g)):
 touch[i]=bool(c&boundary_nodes)
 for n in c:components[n]=i
settlement_ids={s['id'] for s in infra['settlements']};settlements=[];hubs=[]
for row in rows:
 tags=dict(row['tags']);fid=f"{row['osm_type']}/{row['osm_id']}"
 ishub=tags.get('amenity')=='hospital' or tags.get('place') in ('town','city')
 if not ishub and (fid not in settlement_ids or tags.get('place') not in ('city','town','village','hamlet','isolated_dwelling','suburb','quarter','neighbourhood')):continue
 geom=transform(proj,from_wkb(row['geom']));point=geom if geom.geom_type=='Point' else geom.representative_point();distance,index=tree.query([point.x,point.y]);node=nodes[int(index)] if distance<=200 else None
 entry={'id':fid,'name':tags.get('name:en',tags.get('name',fid)),'node_id':node,'snap_distance_m':float(distance),'snap_method':'nearest historical road node within 200m; connector not ground-verified','boundary_truncated':touch.get(components.get(node),True)}
 if ishub:hubs.append(entry)
 if fid in settlement_ids:settlements.append(entry)
infra.update(graph_roads=roads,settlements=settlements,hub_node_ids=sorted({h['node_id'] for h in hubs if h['node_id'] is not None}),hubs=hubs,topology_status='Historical original-node IDs joined to same-snapshot geometry; motor-vehicle roads only; turn restrictions unmodelled')
(dst/'infrastructure.json').write_text(json.dumps(infra));manifest['infrastructure_sha256']=hashlib.sha256((dst/'infrastructure.json').read_bytes()).hexdigest();manifest['limitations']=[x for x in manifest['limitations'] if 'topology acquisition failed' not in x];manifest['limitations']+=['Historical road topology acquired; inferred disruption assumes every exposed road segment is unusable.','Nearest-node settlement/hospital snapping is a proximity assumption, not verified driveway access.','Network components touching extract edges are boundary-uncertain. Unobserved roads remain unknown, not open.','Turn restrictions and time-dependent access restrictions are not modelled.']
(dst/'manifest.json').write_text(json.dumps(manifest,indent=2))
report={'roads':len(roads),'nodes':len(nodes),'directed_edges':g.number_of_edges(),'hubs':hubs,'settlements':settlements,'excluded':excluded,'way_hashes':way_hashes}
(dst/'topology-audit.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k!='way_hashes'},indent=2))
