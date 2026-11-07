import copy
import numpy as np
import pytest
from floodlab.core import validate_manifest, sar_change, metric_crs


def manifest():
    x={'role':'observation','source':'Sentinel-1','units':'dB','bands':['VV','VH'],'terrain_corrected':True,'relative_orbit':19,'orbit_state':'ascending','scene_id':'fixture','sha256':'fixture'}
    return {'event_time':'2026-08-26T00:00:00Z','osm_snapshot':'2026-07-27T00:00:00Z','infrastructure_role':'historical_osm','pre':dict(x,datetime='2026-08-20T00:00:00Z'),'post':dict(x,datetime='2026-09-01T00:00:00Z')}


def test_valid_manifest(): validate_manifest(manifest())

@pytest.mark.parametrize('field,value',[('units','linear'),('role','reference'),('source','EMSR927'),('relative_orbit',None),('terrain_corrected',False),('bands',['VH','VV'])])
def test_bad_sensor_contract(field,value):
    m=manifest(); m['pre'][field]=value
    with pytest.raises(ValueError): validate_manifest(m)

@pytest.mark.parametrize('key,value',[('osm_snapshot','2026-09-01T00:00:00Z'),('event_time','2026-08-01T00:00:00Z'),('infrastructure_role','post_event_osm')])
def test_invalid_temporal_or_source(key,value):
    m=manifest(); m[key]=value
    with pytest.raises(ValueError): validate_manifest(m)


def test_orbit_mismatch():
    m=manifest(); m['post']['relative_orbit']=20
    with pytest.raises(ValueError): validate_manifest(m)


def test_water_change_invalid_and_persistent():
    pre=np.array([[[-10,-20,-10,-10,-10]],[[-15,-25,-15,-15,-15]]],dtype=float)
    post=np.array([[[-22,-23,-11,-22,-22]],[[-28,-26,-17,np.nan,-28]]],dtype=float)
    assert sar_change(pre,post,np.array([[1,1,1,1,0]],bool)).tolist()==[[2,1,0,255,255]]

@pytest.mark.parametrize('crs',['EPSG:4326','EPSG:2263'])
def test_nonmetric_rejected(crs):
    with pytest.raises(ValueError): metric_crs(crs)
