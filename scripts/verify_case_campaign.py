"""Separate arithmetic, source-copy and repeatability checks; never field validation."""
import argparse,json,sys,shutil
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np
import rasterio
from rasterio.features import geometry_mask
from rasterio.warp import transform_geom
from research.terrain_exposure.io import sha256,save_json

def without_timing(v):
    if isinstance(v,dict):return {k:without_timing(x) for k,x in v.items() if k!='seconds'}
    if isinstance(v,list):return [without_timing(x) for x in v]
    return v

def verify(work,pack):
    work=Path(work);pack=Path(pack);protocol=json.loads((pack/'protocol.json').read_text());checks={}
    a=json.loads((work/'measurements-v1/summary.json').read_text());b=json.loads((work/'measurements-v3/summary.json').read_text())
    assert without_timing(a)==without_timing(b),'Repeat changed numeric results'
    checks['four_case_numeric_repeat_identical']=True
    for case in ['varanasi','sangam-vihar']:
        folder=work/'sources'/case
        with rasterio.open(folder/'lulc-2017.tif') as before,rasterio.open(folder/'lulc-2023.tif') as after:
            x,y=before.read(1),after.read(1);w,s,e,n=protocol['cases'][case]['bbox']
            # Independent ROI ring construction and categorical count arithmetic.
            edge=np.linspace(0,1,64);ring=[(w+t*(e-w),s) for t in edge]+[(e,s+t*(n-s)) for t in edge]
            ring += [(e-t*(e-w),n) for t in edge]+[(w,n-t*(n-s)) for t in edge]+[(w,s)]
            geometry=transform_geom('EPSG:4326',before.crs,{'type':'Polygon','coordinates':[ring]})
            inside=geometry_mask([geometry],x.shape,before.transform,invert=True)
            ok=inside&(before.read_masks(1)>0)&(after.read_masks(1)>0)&~np.isin(x,[0,10])&~np.isin(y,[0,10])
            labels,counts=np.unique(x[ok].astype(int)*100+y[ok],return_counts=True)
            matrix=dict(zip(labels.tolist(),counts.tolist()));u=a[case]['urban']
            assert int(counts.sum())==u['common_pixels']
            assert matrix=={int(k.split(':')[0])*100+int(k.split(':')[1]):v for k,v in u['transition_pixels'].items() if v}
            area=abs(before.transform.a*before.transform.e)/10000
            net=(np.count_nonzero((y==7)&ok)-np.count_nonzero((x==7)&ok))*area
            assert abs(net-u['net_built_difference_ha'])<1e-8
            checks[case]={'independently_counted_common_pixels':int(ok.sum()),'net_built_ha':net,'transition_matrix_exact':True}
    manifest=json.loads((pack/'LOCAL_DATA_MANIFEST.json').read_text());raw=pack.parents[1]/'datasets/local/campaign-20261107'
    # pack is research/results/<release>, hence parents[1] is research.
    for name,expected in manifest['files'].items():assert sha256(raw/name)==expected,name
    checks['local_source_files_verified']=len(manifest['files'])
    corpus=Path(__file__).resolve().parents[1]/'components/FLOODLAB_SOURCE_MANIFEST.json'
    pins=json.loads(corpus.read_text())
    for name,expected in pins['files'].items():assert sha256(corpus.parent/'floodlab'/name)==expected,name
    checks['pinned_component_files_verified']=len(pins['files'])
    # Improve plot scales/RGB only after verifying the repeat is numerically identical.
    for case in a:
        for p in (work/'measurements-v3'/case).glob('*.png'):shutil.copyfile(p,pack/'cases'/case/p.name)
    checks['updated_plot_rendering']='Binary panels fixed at0/1; measured summaries retained byte-identical fromv1; true LandsatRGB added fromv3'
    checks['failed_repeat_v2']='Retained as rejected:undeclared buffered DEM was accidentally globbed into Nepal context; fixed manifest-only source selection and regression test'
    checks['scope']='Arithmetic, repeatability, hashes and software contracts; no field, exposure or independent accuracy validation'
    save_json(pack/'verification/numerical-and-source-verification.json',checks)
    print(json.dumps(checks));return checks

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--work',required=True);p.add_argument('--pack',required=True);a=p.parse_args();verify(a.work,a.pack)
