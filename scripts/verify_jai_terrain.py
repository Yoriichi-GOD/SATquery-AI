"""Real terrain input/output receipt, without acquiring a second tile."""
import hashlib,json,time
from datetime import datetime,timezone
from pathlib import Path
import requests,numpy as np,rasterio
from pyproj import Transformer

base='http://127.0.0.1:8768';session=requests.Session();session.trust_env=False
checks=[]
def request(method,path,expected=200,**kwargs):
    start=time.perf_counter();r=session.request(method,base+path,timeout=20,headers={'Origin':base},**kwargs)
    checks.append({'method':method,'path':path,'status':r.status_code,'seconds':time.perf_counter()-start,'bytes':len(r.content)})
    assert r.status_code==expected,(r.status_code,r.text[:200]);return r
status=request('GET','/api/terrain/status').json();scene_id=status['scenes'][0]['id']
scene=request('GET','/api/terrain/scenes/'+scene_id).json()
raw=request('GET','/api/terrain/scenes/'+scene_id+'/raster').content
assert hashlib.sha256(raw).hexdigest()==scene['hashes']['analysis.tif']
request('POST','/api/terrain/obtain',422,json={'confirmed':False})
request('POST','/api/terrain/obtain',422,json={'confirmed':'true'})
request('GET','/api/terrain/scenes/unknown',404)
root=Path('/mnt/c/Users/nrgen/.codex/scratch/SATquery AI/.runtime/jai/terrain')/scene_id
points=[]
with rasterio.open(root/'analysis.tif') as derived,rasterio.open(root/'source.tif') as source:
    data=derived.read(1);converter=Transformer.from_crs(derived.crs,source.crs,always_xy=True)
    for row,col in [(7,7),(15,14),(25,20)]:
        x,y=derived.xy(row,col);assert derived.index(x,y)==(row,col)
        assert scene['mesh']['z_m'][row][col]==float(data[row,col])
        lon,lat=converter.transform(x,y)
        native=float(next(source.sample([(lon,lat)]))[0])
        points.append({'analysis_cell':[row,col],'metric_cell_centre':[x,y],'wgs84':[lon,lat],
                       'native_nearest_height_m':native,'bilinear_analysis_height_m':float(data[row,col]),
                       'difference_due_to_sampling_m':float(data[row,col])-native})
    assert scene['statistics']['valid_cells']==int((data!=derived.nodata).sum())
receipt={'recorded_utc':datetime.now(timezone.utc).isoformat(),'population':'NEW_REAL_DEM','scene_id':scene_id,
         'statistics':scene['statistics'],'hashes':scene['hashes'],'controls':points,'http_checks':checks,
         'interpretation':'Three real metric-cell roundtrips and raster/mesh matches. Native nearest and bilinear-reprojected heights use different sampling; their difference is not independent elevation accuracy.',
         'source_provenance':scene['provenance']}
out=Path('tests/receipts/real-terrain.json');out.write_text(json.dumps(receipt,indent=2))
print(json.dumps({'http_checks':len(checks),'controls':points,'valid_cells':scene['statistics']['valid_cells']},indent=2))
