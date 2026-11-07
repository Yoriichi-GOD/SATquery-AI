import json,csv
import numpy as np
import pytest
import rasterio
from floodlab.fixture import create
from floodlab.pipeline import run,classify_tiled,digest
from floodlab.core import sar_change


def test_end_to_end_exports(tmp_path):
    m=create(tmp_path/'inputs');out=tmp_path/'run';r=run(m,out)
    assert r['synthetic'] is True
    assert r['summary']['new_water_pixels']==32
    assert r['summary']['new_water_m2']==3200
    assert r['summary']['exposed_buildings']==1
    assert r['summary']['exposed_road_m']==40
    assert r['summary']['potentially_cut_off']==1
    with rasterio.open(out/'prediction.tif') as ds:
        assert ds.crs.to_epsg()==32645 and ds.nodata==255
        assert ds.transform.c==400000 and ds.transform.f==3100320
        assert int((ds.read(1)==2).sum())==32
    with (out/'exposure.csv').open() as f:
        rows=list(csv.DictReader(f));assert float(rows[0]['exposed'])==200
    assert '3200.00' in (out/'report-en.html').read_text()
    assert '3200.00' in (out/'report-ne.html').read_text()
    frozen=json.loads((out/'freeze.json').read_text())
    assert all(digest(out/name)==sha for name,sha in frozen['files'].items())
    assert json.loads((out/'sensitivity.json').read_text())['dilated_1px']['exposed_road_m']==60
    with pytest.raises(ValueError):run(m,out)


def test_tiled_no_seams():
    rng=np.random.default_rng(19);pre=rng.normal(-14,5,(2,37,55));post=rng.normal(-16,6,(2,37,55));valid=rng.random((37,55))>.1
    whole=sar_change(pre,post,valid)
    for size in (1,13,16,64):assert np.array_equal(whole,classify_tiled(pre,post,valid,size))


def test_hash_tamper_rejected(tmp_path):
    m=create(tmp_path/'input');(m.parent/'pre.tif').write_bytes(b'bad')
    with pytest.raises(ValueError,match='hash'):run(m,tmp_path/'out')


def test_grid_mismatch_rejected(tmp_path):
    m=create(tmp_path/'input');p=m.parent/'post.tif'
    with rasterio.open(p,'r+') as ds:ds.transform=ds.transform*rasterio.Affine.translation(1,0)
    cfg=json.loads(m.read_text());cfg['post']['sha256']=digest(p);m.write_text(json.dumps(cfg))
    with pytest.raises(ValueError,match='Grid mismatch'):run(m,tmp_path/'out')


def test_reference_infrastructure_rejected(tmp_path):
    m=create(tmp_path/'input');p=m.parent/'infrastructure.json';x=json.loads(p.read_text());x['role']='reference';p.write_text(json.dumps(x))
    cfg=json.loads(m.read_text());cfg['infrastructure_sha256']=digest(p);m.write_text(json.dumps(cfg))
    with pytest.raises(ValueError,match='provenance'):run(m,tmp_path/'out')

def test_repeat_is_reproducible(tmp_path):
    m=create(tmp_path/'input');a=tmp_path/'a';b=tmp_path/'b';ra=run(m,a);rb=run(m,b)
    assert ra['summary']==rb['summary']
    for name in ('prediction.tif','exposure.csv','connectivity.json','layers.geojson'):
        assert digest(a/name)==digest(b/name)

def test_all_invalid_rejected(tmp_path):
    m=create(tmp_path/'input');p=m.parent/'post.tif'
    with rasterio.open(p,'r+') as ds:ds.write(np.full((2,32,40),-9999,dtype='float32'))
    cfg=json.loads(m.read_text());cfg['post']['sha256']=digest(p);m.write_text(json.dumps(cfg))
    with pytest.raises(ValueError,match='No valid paired'):run(m,tmp_path/'out')
