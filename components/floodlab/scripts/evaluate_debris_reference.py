from pathlib import Path
import json,sqlite3,hashlib
import rasterio,numpy as np
from rasterio.features import rasterize
from shapely import from_wkb
from shapely.ops import transform,unary_union
from pyproj import Transformer
B=Path(__file__).resolve().parents[1];run=B/'artifacts/runs/nepal-syapru-004';freeze=json.loads((run/'freeze.json').read_text())
for name,digest in freeze['files'].items():
 if hashlib.sha256((run/name).read_bytes()).hexdigest()!=digest:raise ValueError('Frozen prediction changed')
ref=B/'evaluation_only/emsr/EMSR927_AOI01_GRA_PRODUCT_v1.gpkg';c=sqlite3.connect(ref.as_uri()+'?mode=ro',uri=True)
def geom(blob):
 env=(blob[3]>>1)&7;return from_wkb(blob[8+{0:0,1:32,2:48,3:48,4:64}[env]:])
def read(layer,where=''):
 col=c.execute('SELECT column_name FROM gpkg_geometry_columns WHERE table_name=?',(layer,)).fetchone()[0]
 return [geom(r[0]) for r in c.execute(f'SELECT "{col}" FROM "{layer}" '+where)]
labels=read('observedEventA_v1');footprints=read('imageFootprintA_v1','WHERE or_src_id=2')
with rasterio.open(run/'debris-candidates.tif') as ds:
 arr=ds.read(1);proj=Transformer.from_crs(4326,ds.crs,always_xy=True).transform
 truth=rasterize([(transform(proj,g),1) for g in labels],out_shape=arr.shape,transform=ds.transform,fill=0,dtype='uint8',all_touched=False)>0
 footprint=rasterize([(transform(proj,g),1) for g in footprints],out_shape=arr.shape,transform=ds.transform,fill=0,dtype='uint8',all_touched=False)>0
 valid=(arr!=255)&footprint;pred=arr==1
 tp=int((pred&truth&valid).sum());fp=int((pred&~truth&valid).sum());fn=int((~pred&truth&valid).sum());tn=int((~pred&~truth&valid).sum())
 div=lambda a,b:a/b if b else None
 out={'run':'nepal-syapru-004','role':'post-freeze diagnostic reference agreement; not validated debris accuracy','reference':ref.name,'reference_sha256':hashlib.sha256(ref.read_bytes()).hexdigest(),'prediction_sha256':freeze['files']['debris-candidates.tif'],'classes':{'prediction':'vegetation-to-bare plus SAR-change debris candidates','reference':'6-Mass Movement / Landslide'},'reference_post_date':'2026-08-27T05:05:00Z','reference_pre_date':'2025-11-29T05:11:00Z','reference_source_resolution_m':0.3,'comparison_grid_m':10,'valid_pixels':int(valid.sum()),'tp':tp,'fp':fp,'fn':fn,'tn':tn,'iou':div(tp,tp+fp+fn),'f1':div(2*tp,2*tp+fp+fn),'precision':div(tp,tp+fp),'recall':div(tp,tp+fn),'events':1,'areas':1,'thresholds_changed_after_scoring':False,'limitations':['Vegetation-loss proxy is narrower than mapped landslide extent and misses debris over already bare surfaces.','Reference baseline image is November 2025; prediction optical baseline is August 2026.','Cloud/terrain-invalid pixels excluded; results do not apply to excluded area.','Reference 0.3m source is rasterized at 10m with pixel-centre rule; boundary differences matter.','No model training or threshold tuning used this reference.']}
p=B/'evaluation_only/results';p.mkdir(exist_ok=True);(p/'syapru-debris-agreement.json').write_text(json.dumps(out,indent=2));(B/'web/debris-reference-agreement.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
