from datetime import datetime,timezone,timedelta
import pytest
from floodlab.historical import historical_road
D=datetime(2026,7,27,tzinfo=timezone.utc)
def sample(**tags):
 row={'osm_type':'way','osm_id':1,'version':2,'tags':dict(highway='residential',**tags),'edit_timestamp':D-timedelta(days=1),'valid_to_timestamp':D+timedelta(days=1),'geometry':{'type':'LineString','coordinates':[[0,0],[1,1]]}}
 e={'id':1,'version':2,'timestamp':'2026-07-26T00:00:00Z','nodes':[10,11]}
 return row,e
def test_preserves_original_nodes():
 r,e=sample();f,_=historical_road(r,e,lambda x,y:(x,y),D);assert f['properties']['node_ids']==[10,11]
def test_private_access_excluded():
 r,e=sample(access='private');assert historical_road(r,e,lambda x,y:(x,y),D)[1]=='restricted_access'
def test_explicit_vehicle_overrides_general_access():
 r,e=sample(access='private',motor_vehicle='yes');assert historical_road(r,e,lambda x,y:(x,y),D)[0] is not None
def test_post_snapshot_version_rejected():
 r,e=sample();e['timestamp']='2026-08-01T00:00:00Z'
 with pytest.raises(ValueError):historical_road(r,e,lambda x,y:(x,y),D)
def test_node_count_mismatch_rejected():
 r,e=sample();e['nodes']=[10,11,12]
 with pytest.raises(ValueError):historical_road(r,e,lambda x,y:(x,y),D)
def test_roundabout_defaults_oneway():
 r,e=sample(junction='roundabout');assert historical_road(r,e,lambda x,y:(x,y),D)[0]['properties']['oneway']=='yes'
