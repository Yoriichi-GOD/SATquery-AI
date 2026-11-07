"""Metric raster/vector exposure and explicit-node road reachability."""
import math
import numpy as np
import networkx as nx
from rasterio.features import shapes
from shapely.geometry import shape, LineString
from shapely.ops import unary_union
from .core import metric_crs


def mask_geometry(mask, transform):
    return unary_union([shape(g) for g,v in shapes(mask.astype('uint8'),mask=mask,transform=transform) if v==1])


def exposure(features, flood, valid, crs):
    metric_crs(crs); rows=[]; seen=set()
    for f in features:
        p=f['properties']; fid=str(f['id'])
        if fid in seen: raise ValueError('Duplicate feature ID: '+fid)
        seen.add(fid); g=shape(f['geometry'])
        if not g.is_valid or g.is_empty: raise ValueError('Invalid/empty geometry: '+fid)
        kind=p['kind']
        if kind not in ('building','road','bridge'): continue
        area=kind=='building'
        if area and g.geom_type not in ('Polygon','MultiPolygon'): raise ValueError('Building must be polygon')
        if not area and g.geom_type not in ('LineString','MultiLineString'): raise ValueError('Road/bridge must be line')
        measure=lambda x: x.area if area else x.length
        total=measure(g); observed=measure(g.intersection(valid)); hit=measure(g.intersection(flood))
        rows.append({'id':fid,'kind':kind,'total':total,'observed':observed,'exposed':hit,'unit':'m2' if area else 'm',
                     'exposed_fraction':hit/total if total else None,'coverage_fraction':observed/total if total else None,
                     'status':'exposed' if hit>1e-8 else ('not_exposed' if observed>=total-1e-8 else 'unknown')})
    return rows


def road_graph(roads, flood, valid, crs, min_exposed_m=1.):
    metric_crs(crs)
    if min_exposed_m<=0: raise ValueError('Positive disruption threshold required')
    graph=nx.MultiDiGraph(); affected=[]; unknown=[]; seen=set()
    for f in roads:
        fid=str(f['id']); p=f['properties']; g=shape(f['geometry'])
        if fid in seen: raise ValueError('Duplicate road ID')
        seen.add(fid)
        if g.geom_type!='LineString': raise ValueError('Graph roads must be LineStrings')
        coords=list(g.coords); ids=p.get('node_ids',[])
        if len(ids)!=len(coords) or len(ids)<2: raise ValueError('Explicit historical OSM node IDs required')
        direction=str(p.get('oneway','no')).lower()
        if direction not in ('no','yes','-1','0','1','false','true'): raise ValueError('Unsupported oneway value')
        for j,(a,z) in enumerate(zip(ids,coords)):
            if a in graph and math.dist(graph.nodes[a]['xy'],z)>0.1: raise ValueError('Conflicting node coordinates')
            graph.add_node(a,xy=z)
        for i,(a,c) in enumerate(zip(ids,ids[1:])):
            segment=LineString(coords[i:i+2]); length=segment.length
            if length==0: continue
            eid=f'{fid}:{i}'; hit=segment.intersection(flood).length
            observed=segment.intersection(valid).length
            state='disrupted' if hit>=min_exposed_m else ('unknown' if observed<length-1e-6 else 'clear')
            if state=='disrupted': affected.append(eid)
            if state=='unknown': unknown.append(eid)
            data=dict(length_m=length,source_id=fid,edge_id=eid,state=state,exposed_m=hit,observed_m=observed)
            if direction not in ('-1',): graph.add_edge(a,c,key=eid,**data)
            if direction not in ('yes','1','true'): graph.add_edge(c,a,key=eid,**data)
    return graph,affected,unknown


def reachability(graph, settlements, hubs):
    """Compare access to the nearest reachable PRE-EVENT hub by road length. Unknown edges produce bounds."""
    if any(h not in graph for h in hubs): raise ValueError('Hub is not on network')
    def distances(g):
        return nx.multi_source_dijkstra_path_length(g.reverse(copy=False),hubs,weight='length_m') if hubs else {}
    before=distances(graph)
    hub_before={h:nx.single_source_dijkstra_path_length(graph.reverse(copy=False),h,weight='length_m') for h in hubs}
    optimistic=graph.copy(); conservative=graph.copy()
    optimistic.remove_edges_from([(a,b,k) for a,b,k,d in graph.edges(keys=True,data=True) if d['state']=='disrupted'])
    conservative.remove_edges_from([(a,b,k) for a,b,k,d in graph.edges(keys=True,data=True) if d['state']!='clear'])
    after=distances(optimistic); lower=distances(conservative); rows=[]
    for s in settlements:
        node=s.get('node_id'); boundary=s.get('boundary_truncated',True)
        candidates=[h for h in hubs if node in hub_before[h]]
        target=min(candidates,key=lambda h:(hub_before[h][node],str(h))) if candidates else None
        nearest_after=nx.single_source_dijkstra_path_length(optimistic.reverse(copy=False),target,weight='length_m') if target is not None else {}
        nearest_lower=nx.single_source_dijkstra_path_length(conservative.reverse(copy=False),target,weight='length_m') if target is not None else {}
        if not hubs: status='unknown_no_hubs'
        elif node not in graph: status='unknown_off_network'
        elif boundary: status='unknown_aoi_boundary'
        elif node not in before: status='disconnected_before'
        elif node not in after: status='potentially_cut_off'
        elif node not in nearest_after: status='nearest_hub_cut_off_alternative_available'
        elif node not in nearest_lower: status='unknown_unobserved_route'
        else: status='connected_after'
        rows.append({'id':s['id'],'name':s.get('name',s['id']),'snap_distance_m':s.get('snap_distance_m'),'node_id':node,'status':status,'connected_before':node in before if hubs and node in graph else None,
                     'connected_after_optimistic':node in after if hubs and node in graph else None,
                     'connected_after_conservative':node in lower if hubs and node in graph else None,
                     'nearest_pre_event_hub':target,'nearest_hub_after_conservative':node in nearest_lower if target is not None else None,'nearest_hub_after_optimistic':node in nearest_after if target is not None else None,
                     'alternative_hub_distance_after_m':after.get(node),'distance_before_m':before.get(node),'distance_after_m':nearest_after.get(node),'boundary_truncated':boundary})
    return rows
