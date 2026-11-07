"""Directed mapped-network scenarios, explicit observation bounds and repair counterfactuals.

This is not observed road closure, operational routing, a calibrated probability,
or an evacuation recommendation. Original graph states are never modified.
"""
from __future__ import annotations

import math
import time

import networkx as nx

SCHEMA='floodlab.response/1'
STATES={'clear','disrupted','unknown'}
MAX_WITNESS_VERTICES=250_000


def validate_graph(graph):
    if not isinstance(graph,nx.MultiDiGraph) or len(graph)>100_000 or graph.number_of_edges()>300_000:
        raise ValueError('A bounded directed multigraph is required')
    for _,_,_,edge in graph.edges(keys=True,data=True):
        if edge.get('state') not in STATES or not isinstance(edge.get('source_id'),str) or not edge['source_id']:
            raise ValueError('Explicit edge observation state and source-way ID required')
        length=edge.get('length_m')
        if not isinstance(length,(int,float)) or not math.isfinite(length) or length<=0:
            raise ValueError('Finite positive metric edge lengths required')


def network_view(graph,mode,repairs=()):
    repaired=set(repairs)
    if mode not in {'before','optimistic','conservative'}:raise ValueError('Unknown network view')
    def allowed(u,v,key):
        edge=graph[u][v][key];state=edge['state']
        if mode=='before':return True
        if state=='disrupted':return edge['source_id'] in repaired
        return state=='clear' or mode=='optimistic'
    return nx.subgraph_view(graph,filter_edge=allowed)


def destination_paths(graph,hubs):
    """Only lengths for the full network; witnesses are reconstructed for selected places.

    Materializing every full path on a long rural network can require quadratic memory.
    """
    return nx.multi_source_dijkstra_path_length(graph.reverse(copy=False),hubs,weight='length_m') if hubs else {}


def witness(graph,node,distances,hubs):
    if node not in distances:return None
    result=[node];destinations=set(hubs)
    while node not in destinations:
        options=[]
        for other,keys in graph[node].items():
            if other not in distances or distances[other]>=distances[node]:continue
            for key,edge in keys.items():
                if math.isclose(edge['length_m']+distances[other],distances[node],rel_tol=1e-10,abs_tol=1e-6):
                    options.append((str(other),str(key),other))
        if not options:raise ValueError('Shortest-path witness inconsistent with distance evidence')
        node=min(options)[2];result.append(node)
        if len(result)>len(graph):raise ValueError('Cycle in route witness')
    return result


def route_record(graph,nodes):
    if nodes is None:return None
    segments=[]
    for a,b in zip(nodes,nodes[1:]):
        key,edge=min(graph[a][b].items(),key=lambda item:(item[1]['length_m'],str(item[0])))
        segments.append({'edge_id':str(edge.get('edge_id',key)),'source_id':edge['source_id'],
            'u':a,'v':b,'state':edge['state'],'length_m':edge['length_m']})
    return {'node_ids':nodes,'destination_node':nodes[-1],
            'length_m':sum(s['length_m'] for s in segments),'segments':segments,
            'unobserved_segments':sum(s['state']=='unknown' for s in segments),
            'note':'Shortest mapped length, not measured journey time or a safe-route instruction'}


def assess(graph,settlements,hubs,repairs=(),*,include_paths=True):
    validate_graph(graph)
    if len(settlements)>500 or len(hubs)>500:raise ValueError('Too many settlements or service destinations')
    if len({s['id'] for s in settlements})!=len(settlements):raise ValueError('Duplicate settlement IDs')
    requested=list(repairs)
    if len(set(requested))!=len(requested) or len(requested)>64:raise ValueError('Choose at most 64 distinct repair ways')
    repairable={e['source_id'] for _,_,e in graph.edges(data=True) if e['state']=='disrupted'}
    if set(requested)-repairable:raise ValueError('Repairs must name candidate-disrupted source ways; unknown edges cannot be cleared by a repair toggle')
    usable_hubs=sorted({h for h in hubs if h in graph},key=str)
    missing_hubs=[h for h in hubs if h not in graph]
    views={mode:network_view(graph,mode,requested) for mode in ['before','optimistic','conservative']}
    paths={mode:destination_paths(view,usable_hubs) for mode,view in views.items()}
    rows=[];witness_vertices=0
    for s in sorted(settlements,key=lambda s:str(s['id'])):
        node=s.get('node_id');boundary=bool(s.get('boundary_truncated',True))
        valid=bool(usable_hubs) and node in graph
        before=node in paths['before'] if valid else None
        optimistic=node in paths['optimistic'] if valid else None
        conservative=node in paths['conservative'] if valid else None
        if not usable_hubs:status='NOT_ASSESSED_NO_HUBS'
        elif node not in graph:status='NOT_ASSESSED_OFF_NETWORK'
        elif not before:status='DISCONNECTED_IN_MAPPED_BASELINE'
        elif conservative:status='MAPPED_ROUTE_SUPPORTED'
        elif optimistic:status='UNKNOWN_UNOBSERVED_ROUTE'
        elif boundary:status='UNKNOWN_AOI_BOUNDARY'
        else:status='NO_MAPPED_ROUTE_IN_CLOSURE_SCENARIO'
        quality=['Mapped infrastructure is incomplete; turn restrictions and facility capacity are not modelled',
                 'Candidate intersections are hypothetical closures, not confirmed damage',
                 'Clear means covered without a qualifying candidate intersection, not field-confirmed open',
                 'Network snap/connector is not field-verified']
        if boundary:quality.append('AOI boundary may hide alternate routes; negative access claims remain unknown')
        row={'id':s['id'],'name':s.get('name') or str(s['id']),'node_id':node,'status':status,
             'connected_before':before,'after_optimistic':optimistic,'after_conservative':conservative,
             'boundary_truncated':boundary,'snap_distance_m':s.get('snap_distance_m'),
             'population':s.get('population'),'quality':quality}
        if include_paths:
            row['routes']={}
            for mode in views:
                nodes=witness(views[mode],node,paths[mode],usable_hubs) if valid else None
                witness_vertices+=len(nodes) if nodes else 0
                if witness_vertices>MAX_WITNESS_VERTICES:raise ValueError('Route witness export exceeds bounded vertex budget')
                row['routes'][mode]=route_record(views[mode],nodes)
        rows.append(row)
    return {'schema':SCHEMA,'mode':'MAPPED_NETWORK_SCENARIO_NOT_CONFIRMED_CLOSURE',
        'restore_way_ids':sorted(requested),'hubs_used':usable_hubs,'missing_hubs':missing_hubs,
        'rows':rows,'summary':{'settlements':len(rows),'mapped_before_route':sum(r['connected_before'] is True for r in rows) if usable_hubs else None,
            'observation_supported_mapped_routes':sum(r['after_conservative'] is True for r in rows) if usable_hubs else None,
            'possible_routes_through_unknown':sum(r['status']=='UNKNOWN_UNOBSERVED_ROUTE' for r in rows) if usable_hubs else None,
            'unknown_aoi_boundary':sum(r['status']=='UNKNOWN_AOI_BOUNDARY' for r in rows) if usable_hubs else None,
            'no_mapped_route_in_scenario':sum(r['status']=='NO_MAPPED_ROUTE_IN_CLOSURE_SCENARIO' for r in rows) if usable_hubs else None,
            'not_assessed':sum(r['connected_before'] is None for r in rows)},
        'uncertainty_method':'Unknown edges open in optimistic bound; closed in conservative bound. No closure probabilities assumed.',
        'limitations':['Routes are evidence-bound model scenarios, not operational access or safety decisions',
                       'Positive mapped route witnesses are retained even if the component touches the AOI boundary',
                       'Absence of a route in a truncated/incomplete network cannot establish actual isolation']}


def _gains(baseline,changed):
    initial={r['id']:r for r in baseline['rows']}
    optimistic=[];supported=[]
    for row in changed['rows']:
        old=initial[row['id']]
        if old['connected_before'] is not True:continue
        if old['after_optimistic'] is False and row['after_optimistic'] is True:optimistic.append(row['id'])
        if old['after_conservative'] is False and row['after_conservative'] is True:supported.append(row['id'])
    return optimistic,supported


def rank_repairs(graph,settlements,hubs,repairs=(),*,max_candidates=64,max_bundle_size=64,budget_seconds=20):
    if not 1<=max_candidates<=128 or not 1<=max_bundle_size<=64 or not 0<budget_seconds<=40:
        raise ValueError('Invalid bounded repair-search configuration')
    started=time.monotonic();baseline=assess(graph,settlements,hubs,repairs)
    groups={}
    for a,b,key,e in graph.edges(keys=True,data=True):
        if e['state']=='disrupted' and e['source_id'] not in repairs:
            groups.setdefault(e['source_id'],{})[str(e.get('edge_id',key))]=e['length_m']
    candidates=sorted(groups)
    if not baseline['hubs_used']:
        return {'state':'NOT_ASSESSED_NO_HUBS','rankings':[],'search_complete':False,'candidate_way_count':len(candidates)}
    if not any(r['connected_before'] is True for r in baseline['rows']):
        return {'state':'NOT_ASSESSED_NO_BASELINE_ROUTES','rankings':[],'search_complete':False,'candidate_way_count':len(candidates)}
    if len(candidates)>max_candidates:
        return {'state':'NOT_ASSESSED_CANDIDATE_BUDGET','rankings':[],'search_complete':False,
                'candidate_way_count':len(candidates),'maximum_candidates':max_candidates}
    scenarios={(way,) for way in candidates}
    # Test serial-cut bundles from actual directed pre-event shortest-path witnesses.
    # This is a declared candidate search, not an exhaustive minimum-repair optimizer.
    bundles_skipped=0
    for row in baseline['rows']:
        if row['connected_before'] is True and row['after_optimistic'] is False:
            route=row['routes']['before']
            ways=tuple(sorted({e['source_id'] for e in route['segments'] if e['state']=='disrupted' and e['source_id'] not in repairs}))
            if 1<len(ways)<=max_bundle_size and len(set(ways)|set(repairs))<=64:scenarios.add(ways)
            elif len(ways)>max_bundle_size:bundles_skipped+=1
    ranking=[];evaluated=0;timed_out=False
    for ways in sorted(scenarios,key=lambda v:(len(v),v)):
        if time.monotonic()-started>budget_seconds:timed_out=True;break
        changed=assess(graph,settlements,hubs,[*repairs,*ways],include_paths=False)
        optimistic,supported=_gains(baseline,changed);evaluated+=1
        if not optimistic and not supported:continue
        ranking.append({'restore_way_ids':list(ways),'newly_possible_mapped_routes':optimistic,
            'newly_observation_supported_mapped_routes':supported,'possible_gain':len(optimistic),
            'supported_gain':len(supported),'repaired_candidate_length_m':sum(sum(groups[w].values()) for w in ways),
            'scope':'Conditional model counterfactual; unknown observations remain unknown'})
    ranking.sort(key=lambda r:(-r['supported_gain'],-r['possible_gain'],len(r['restore_way_ids']),r['repaired_candidate_length_m'],r['restore_way_ids']))
    for index,row in enumerate(ranking):row['rank']=index+1
    return {'state':'PARTIAL_BUDGET' if timed_out else 'COMPLETE_DECLARED_SEARCH','rankings':ranking,
            'candidate_way_count':len(candidates),'scenarios_evaluated':evaluated,'search_complete':not timed_out,
            'bundles_skipped_size_limit':bundles_skipped,'bundle_search':'Directed pre-event shortest-path bundles only; not global optimum',
            'seconds':time.monotonic()-started}
