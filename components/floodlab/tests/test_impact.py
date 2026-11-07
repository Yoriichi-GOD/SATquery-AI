import pytest
from shapely.geometry import box, mapping, LineString
from floodlab.impact import exposure,road_graph,reachability
CRS='EPSG:32645'; VALID=box(-100,-100,100,100)
def road(fid,coords,ids,**props): return {'id':fid,'type':'Feature','geometry':mapping(LineString(coords)),'properties':dict(kind='road',node_ids=ids,**props)}
def run(roads, flood, hubs=['h'],valid=VALID,boundary=False):
    g,_,_=road_graph(roads,flood,valid,CRS)
    return reachability(g,[{'id':'village','node_id':'v','boundary_truncated':boundary}],hubs)[0]
def test_bridge_cut():
    r=run([road('bridge',[(0,0),(10,0)],['v','h'])],box(4,-2,6,2))
    assert r['status']=='potentially_cut_off' and r['distance_before_m']==10

def test_alternate_route():
    r=run([road('bridge',[(0,0),(10,0)],['v','h']),road('detour',[(0,0),(0,10),(10,0)],['v','d','h'])],box(4,-1,6,1))
    assert r['status']=='connected_after' and r['distance_after_m']>20

def test_overpass_not_connected():
    r=run([road('a',[(-10,0),(10,0)],['v','a']),road('b',[(0,-10),(0,10)],['b','h'])],box(50,50,60,60))
    assert r['status']=='disconnected_before'

def test_no_hub_unknown():
    assert run([road('a',[(0,0),(10,0)],['v','h'])],box(50,50,60,60),hubs=[])['status']=='unknown_no_hubs'

def test_missing_hub_rejected():
    with pytest.raises(ValueError): run([road('a',[(0,0),(10,0)],['v','x'])],box(50,50,60,60))

def test_boundary_unknown():
    assert run([road('a',[(0,0),(10,0)],['v','h'])],box(4,-1,6,1),boundary=True)['status']=='unknown_aoi_boundary'

def test_unknown_coverage():
    assert run([road('a',[(0,0),(10,0)],['v','h'])],box(50,50,60,60),valid=box(-1,-1,5,1))['status']=='unknown_unobserved_route'

def test_oneway():
    assert run([road('a',[(0,0),(10,0)],['v','h'],oneway='-1')],box(50,50,60,60))['status']=='disconnected_before'

def test_duplicate_rejected():
    a=road('a',[(0,0),(10,0)],['v','h'])
    with pytest.raises(ValueError): road_graph([a,a],box(50,50,60,60),VALID,CRS)

def test_area_length_touch_and_unknown():
    fs=[{'id':'b','geometry':mapping(box(0,0,10,10)),'properties':{'kind':'building'}},road('r',[(-5,5),(15,5)],['a','z']),{'id':'touch','geometry':mapping(box(10,0,20,10)),'properties':{'kind':'building'}}]
    rows=exposure(fs,box(0,0,10,10),box(-10,-10,11,11),CRS)
    assert rows[0]['exposed']==100 and rows[1]['exposed']==10
    assert rows[2]['exposed']==0 and rows[2]['status']=='unknown'


def test_nearest_hub_cut_but_distant_hub_available():
    roads=[road('near',[(0,0),(10,0)],['v','near']),road('far',[(0,0),(0,30)],['v','far'])]
    r=run(roads,box(4,-1,6,1),hubs=['far','near'])
    assert r['nearest_pre_event_hub']=='near'
    assert r['status']=='nearest_hub_cut_off_alternative_available'
    assert r['distance_after_m'] is None
    assert r['alternative_hub_distance_after_m']==30
