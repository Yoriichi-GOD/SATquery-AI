import hashlib,io,json,zipfile
import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin
from floodlab.response_store import ResponseStore


def fixture(tmp_path):
    root=tmp_path/'runs'/'fixture';root.mkdir(parents=True)
    values={
        'graph.json':{'nodes':[{'id':n,'xy':[300000+i*10,3100000]} for i,n in enumerate(['v','a','h'])],
            'edges':[{'u':'v','v':'a','edge_id':'road-a:0','source_id':'road-a','length_m':10,'state':'disrupted'},
                     {'u':'a','v':'h','edge_id':'road-b:0','source_id':'road-b','length_m':10,'state':'unknown'}]},
        'connectivity.json':[{'id':'village','name':'A < B & C','node_id':'v','boundary_truncated':True}],
        'result.json':{'synthetic':True},
        'manifest.json':{'event_time':'2026-08-26','osm_snapshot':'2026-08-25'},
        'topology-audit.json':{'hubs':[{'node_id':'h'}]}}
    for name,value in values.items():(root/name).write_text(json.dumps(value))
    with rasterio.open(root/'prediction.tif','w',driver='GTiff',height=2,width=2,count=1,dtype='uint8',
        crs='EPSG:32645',transform=from_origin(300000,3100000,10,10)) as dst:dst.write(np.zeros((2,2),dtype='uint8'),1)
    freeze(root)
    return root,ResponseStore(tmp_path/'runs',tmp_path/'outputs')


def freeze(root):
    (root/'freeze.json').write_text(json.dumps({'files':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in root.iterdir() if p.name!='freeze.json'}}))


def test_source_is_frozen_and_repairs_do_not_clear_unknown(tmp_path):
    root,store=fixture(tmp_path);before={p.name:p.read_bytes() for p in root.iterdir()}
    value=store.calculate('fixture',['road-a'])
    assert value['source']['population']=='SYNTHETIC_SOFTWARE_TEST'
    assert value['rows'][0]['status']=='UNKNOWN_UNOBSERVED_ROUTE'
    assert value['rows'][0]['after_optimistic'] is True and value['rows'][0]['after_conservative'] is False
    assert {p.name:p.read_bytes() for p in root.iterdir()}==before
    assert store.calculate('fixture',['road-a'])==value

def test_tampered_input_cannot_reuse_cached_answer(tmp_path):
    root,store=fixture(tmp_path);store.calculate('fixture')
    (root/'graph.json').write_text('{}')
    with pytest.raises(ValueError,match='integrity'):store.calculate('fixture')

def test_zip_hashes_kml_escaping_and_archive_manifest(tmp_path):
    root,store=fixture(tmp_path);value=store.calculate('fixture',['road-a']);sid=value['scenario_id']
    raw,sha=store.artifact('fixture',sid,'bundle.zip')
    assert hashlib.sha256(raw).hexdigest()==sha
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        manifest=json.loads(archive.read('evidence.json'))
        assert all(hashlib.sha256(archive.read(name)).hexdigest()==expected for name,expected in manifest['files'].items())
        assert 'A &lt; B &amp; C' in archive.read('fieldkit.kml').decode()
    folder=store.output/'fixture'/sid
    with zipfile.ZipFile(folder/'bundle.zip','w') as archive:
        for name in manifest['files']:archive.writestr(name,(folder/name).read_bytes())
        archive.writestr('evidence.json',b'{}')
    with pytest.raises(ValueError,match='provenance'):store.artifact('fixture',sid,'bundle.zip')

def test_path_escape_and_unknown_repair_fail(tmp_path):
    root,store=fixture(tmp_path)
    with pytest.raises(ValueError):store.calculate('../outside')
    with pytest.raises(ValueError):store.calculate('fixture',['road-b'])
    value=store.calculate('fixture')
    with pytest.raises(FileNotFoundError):store.artifact('fixture',value['scenario_id'],'../../secret')

def test_no_hubs_is_not_a_zero_impact_result(tmp_path):
    root,store=fixture(tmp_path);(root/'topology-audit.json').write_text(json.dumps({'hubs':[]}));freeze(root)
    value=store.calculate('fixture')
    assert value['state']=='NOT_ASSESSED_NO_HUBS'
    assert value['rows'][0]['after_optimistic'] is None
    raw,_=store.artifact('fixture',value['scenario_id'],'alert-en.txt')
    assert b'NOT ASSESSED' in raw
