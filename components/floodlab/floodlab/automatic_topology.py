"""Historical-node topology for automatic AOIs; boundary uncertainty is retained."""
from pathlib import Path
from datetime import datetime
import json,time,requests,hashlib
import numpy as np,networkx as nx,pyarrow.parquet as pq
from scipy.spatial import cKDTree
from shapely import from_wkb
from shapely.geometry import mapping,box,Point
from shapely.ops import transform
from pyproj import Transformer
from .historical import historical_road
from .impact import road_graph

def attach_topology(root,progress=lambda message:None):
 root=Path(root);dst=root/'prepared';manifest=json.loads((dst/'manifest.json').read_text());infra=json.loads((dst/'infrastructure.json').read_text());plan=json.loads((root/'plan.json').read_text());when=datetime.fromisoformat(manifest['osm_snapshot'].replace('Z','+00:00'));proj=Transformer.from_crs(4326,plan['epsg'],always_xy=True).transform
 rows=pq.read_table(root/'historical-osm.parquet',columns=['osm_type','osm_id','version','tags','geom','edit_timestamp','valid_to_timestamp']).to_pylist()
 cache=Path(__file__).resolve().parents[1]/'data/osm_pre_event/way_versions';cache.mkdir(parents=True,exist_ok=True)
 allowed={'motorway','trunk','primary','secondary','tertiary','unclassified','residential','service','motorway_link','trunk_link','primary_link','secondary_link','tertiary_link','living_street'}
 ways=[r for r in rows if r['osm_type']=='way' and dict(r['tags']).get('highway') in allowed];roads=[];excluded=[];hashes={}
 for index,row in enumerate(ways):
  path=cache/f"{row['osm_id']}-v{row['version']}.json"
  if not path.exists():
   time.sleep(.6);response=requests.get(f"https://api.openstreetmap.org/api/0.6/way/{row['osm_id']}/{row['version']}.json",timeout=30,headers={'User-Agent':'SatQuery-FloodLab research prototype'});response.raise_for_status();path.write_text(json.dumps(response.json()))
  row['geometry']=mapping(from_wkb(row['geom']));road,reason=historical_road(row,json.loads(path.read_text())['elements'][0],proj,when)
  if road:roads.append(road);hashes[path.name]=hashlib.sha256(path.read_bytes()).hexdigest()
  else:excluded.append({'id':row['osm_id'],'reason':reason})
  if index%25==0:progress(f'Checking historical road topology: {index+1}/{len(ways)}')
 g,_,_=road_graph(roads,box(0,0,0,0),box(-1e9,-1e9,1e9,1e9),f"EPSG:{plan['epsg']}");nodes=list(g.nodes);footprint=transform(proj,box(*plan['bbox']));settlements=[];hubs=[];touch={};components={}
 if nodes:
  tree=cKDTree(np.array([g.nodes[n]['xy'] for n in nodes]));boundary={n for n in nodes if footprint.boundary.distance(Point(g.nodes[n]['xy']))<150 or not footprint.covers(Point(g.nodes[n]['xy']))}
  for i,c in enumerate(nx.weakly_connected_components(g)):
   touch[i]=bool(c&boundary)
   for n in c:components[n]=i
 for row in rows:
  tags=dict(row['tags']);ishub=tags.get('amenity')=='hospital' or tags.get('place') in ('town','city');issettlement=tags.get('place') in ('city','town','village','hamlet','isolated_dwelling','suburb','quarter','neighbourhood')
  if not ishub and not issettlement:continue
  geom=transform(proj,from_wkb(row['geom']));point=geom if geom.geom_type=='Point' else geom.representative_point();distance,index=tree.query([point.x,point.y]) if nodes else (float('inf'),0);node=nodes[int(index)] if distance<=200 else None;fid=f"{row['osm_type']}/{row['osm_id']}"
  entry={'id':fid,'name':tags.get('name:en',tags.get('name',fid)),'node_id':node,'snap_distance_m':float(distance) if np.isfinite(distance) else None,'boundary_truncated':touch.get(components.get(node),True),'snap_method':'nearest historical road node within 200m; unverified connector'}
  if ishub:hubs.append(entry)
  if issettlement:settlements.append(entry)
 infra.update(graph_roads=roads,settlements=settlements,hubs=hubs,hub_node_ids=sorted({h['node_id'] for h in hubs if h['node_id'] is not None}),topology_status='Historical nodes; AOI boundary and observation coverage uncertain; turn restrictions unmodelled')
 (dst/'infrastructure.json').write_text(json.dumps(infra));manifest['infrastructure_sha256']=hashlib.sha256((dst/'infrastructure.json').read_bytes()).hexdigest()
 manifest['limitations']=[v for v in manifest['limitations'] if not v.startswith(('Automatic bounded','Connectivity is not assessed'))]+['Automatic debris is not yet available.','Historical road graph computed within the requested AOI. Boundary-connected components and unobserved roads remain unknown.','Nearest-node snapping within 200m is not verified driveway access; turn restrictions are unmodelled.']
 (dst/'manifest.json').write_text(json.dumps(manifest,indent=2));(dst/'topology-audit.json').write_text(json.dumps({'roads':len(roads),'nodes':len(nodes),'directed_edges':g.number_of_edges(),'hubs':hubs,'settlements':settlements,'excluded':excluded,'way_hashes':hashes},indent=2));return dst/'manifest.json'
