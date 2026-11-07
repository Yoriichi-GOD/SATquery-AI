"""Synthetic graph proofs, not disaster accuracy or field accessibility validation."""
import copy
import networkx as nx
import pytest

from floodlab.response import assess,rank_repairs


def graph(edges):
    g=nx.MultiDiGraph()
    for i,(u,v,state,way,length) in enumerate(edges):
        g.add_edge(u,v,key=str(i),state=state,source_id=way,length_m=length,edge_id=str(i))
    return g

def village(node='v',boundary=False):return [{'id':'s','name':'Village','node_id':node,'boundary_truncated':boundary}]

def test_oneway_is_not_turned_into_access():
    g=graph([('h','v','clear','oneway',10)])
    row=assess(g,village(),['h'])['rows'][0]
    assert row['connected_before'] is False and row['after_optimistic'] is False

def test_serial_cuts_need_joint_repair_and_original_is_immutable():
    g=graph([('v','a','disrupted','bridge-a',10),('a','h','disrupted','bridge-b',10)])
    before=copy.deepcopy(dict(g.edges))
    ranking=rank_repairs(g,village(),['h'])
    assert ranking['rankings'][0]['restore_way_ids']==['bridge-a','bridge-b']
    assert ranking['rankings'][0]['supported_gain']==1
    assert assess(g,village(),['h'],['bridge-a'])['rows'][0]['after_conservative'] is False
    assert assess(g,village(),['h'],['bridge-a','bridge-b'])['rows'][0]['routes']['conservative']['node_ids']==['v','a','h']
    assert dict(g.edges)==before

def test_unknown_remains_unknown_after_repair():
    g=graph([('v','a','disrupted','bridge',10),('a','h','unknown','unseen',10)])
    row=assess(g,village(),['h'],['bridge'])['rows'][0]
    assert row['status']=='UNKNOWN_UNOBSERVED_ROUTE'
    assert row['after_optimistic'] is True and row['after_conservative'] is False
    assert row['routes']['optimistic']['unobserved_segments']==1
    with pytest.raises(ValueError):assess(g,village(),['h'],['unseen'])

def test_boundary_blocks_negative_claim_not_positive_witness():
    g=graph([('v','h','clear','road',10)])
    assert assess(g,village(boundary=True),['h'])['rows'][0]['status']=='MAPPED_ROUTE_SUPPORTED'
    g['v']['h']['0']['state']='disrupted'
    assert assess(g,village(boundary=True),['h'])['rows'][0]['status']=='UNKNOWN_AOI_BOUNDARY'

def test_parallel_detour_and_alternative_hub_are_kept():
    g=graph([('v','near','disrupted','bridge',10),('v','near','clear','parallel',30),('v','far','clear','alt',20)])
    row=assess(g,village(),['near','far'])['rows'][0]
    assert row['routes']['before']['destination_node']=='near'
    assert row['routes']['conservative']['destination_node']=='far'
    assert row['routes']['conservative']['length_m']==20

def test_missing_hubs_and_unmapped_places_are_not_zero_exposure():
    g=graph([('v','h','clear','road',10)])
    missing=assess(g,village(),[])
    assert missing['summary']['observation_supported_mapped_routes'] is None
    assert missing['summary']['mapped_before_route'] is None
    row=missing['rows'][0]
    assert row['status']=='NOT_ASSESSED_NO_HUBS' and row['after_optimistic'] is None
    row=assess(g,village(None),['h'])['rows'][0]
    assert row['status']=='NOT_ASSESSED_OFF_NETWORK' and row['connected_before'] is None
    assert rank_repairs(g,village(),[])['state']=='NOT_ASSESSED_NO_HUBS'

def test_repair_budget_is_explicit_not_fake_empty_complete():
    g=graph([('v','a','disrupted','a',10),('a','h','disrupted','b',10)])
    value=rank_repairs(g,village(),['h'],max_candidates=1)
    assert value['state']=='NOT_ASSESSED_CANDIDATE_BUDGET' and value['search_complete'] is False

def test_many_serial_cuts_are_offered_as_one_explicit_bundle():
    g=graph([(str(i),str(i+1),'disrupted',f'way-{i}',10) for i in range(8)])
    value=rank_repairs(g,village('0'),['8'])
    assert len(value['rankings'][0]['restore_way_ids'])==8
    assert value['rankings'][0]['supported_gain']==1

def test_invalid_metric_edges_and_duplicate_repairs_rejected():
    g=graph([('v','h','clear','a',float('nan'))])
    with pytest.raises(ValueError):assess(g,village(),['h'])
    g=graph([('v','h','disrupted','a',10)])
    with pytest.raises(ValueError):assess(g,village(),['h'],['a','a'])

def test_large_overlapping_route_exports_fail_explicitly_at_budget(monkeypatch):
    monkeypatch.setattr('floodlab.response.MAX_WITNESS_VERTICES',20)
    g=graph([(str(i),str(i+1),'clear',f'road-{i}',10) for i in range(10)])
    with pytest.raises(ValueError,match='vertex budget'):
        assess(g,village('0'),['10'])
