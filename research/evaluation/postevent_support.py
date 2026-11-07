"""Quality-footprint support for unchanged Nepal candidates and mapped receptors."""
import argparse,json
from pathlib import Path
import numpy as np
import rasterio
from rasterio.warp import reproject,Resampling
from rasterio.features import shapes
from shapely.geometry import shape
from shapely.ops import unary_union
from research.terrain_exposure.io import candidate_raster,save_json,sha256
from research.terrain_exposure.graph import project,geometry_coverage
from research.terrain_exposure.replay import verify_freeze

def run(terrain,runfolder,output):
    terrain=Path(terrain);runfolder=Path(runfolder);output=Path(output)
    if output.exists():raise FileExistsError('Keep prior support assessments immutable')
    freeze=verify_freeze(runfolder)
    with rasterio.open(terrain/'quality-filtered-native.tif') as src:
        q=(src.read_masks(1)>0)&np.isfinite(src.read(1));transform=src.transform;crs=src.crs
    geoms=[shape(g) for g,v in shapes(q.astype('uint8'),mask=q,transform=transform) if v==1]
    footprint=unary_union(geoms);layers={}
    for layer,name,positive,valid_codes in [('water','prediction.tif',[2],[0,1,2]),('debris','debris-candidates.tif',[1],[0,1])]:
        candidate,valid,grid,meta=candidate_raster(runfolder/name,positive,valid_codes)
        hasterrain=np.zeros(grid.shape,'uint8')
        reproject(q.astype('uint8'),hasterrain,src_transform=transform,src_crs=crs,dst_transform=grid.transform,
            dst_crs=grid.crs,src_nodata=0,dst_nodata=0,resampling=Resampling.nearest)
        common=hasterrain==1
        layers[layer]={'source_sha256':meta['sha256'],'candidate_pixels':int(candidate.sum()),
            'candidate_area_ha':float(candidate.sum()*grid.area/10000),'candidate_pixels_with_terrain_quality':int((candidate&common).sum()),
            'candidate_area_with_terrain_quality_ha':float((candidate&common).sum()*grid.area/10000),
            'observation_valid_pixels':int(valid.sum()),'observation_valid_pixels_with_terrain_quality':int((valid&common).sum()),
            'sampling':'Native2m quality mask sampled nearest at frozen10m candidate-cell centres;notfractionalcellcoverage'}
    features=json.loads((runfolder/'layers.geojson').read_text());rows=[]
    for f in features['features']:
        kind=f['properties'].get('kind')
        if kind not in {'building','road','bridge','settlement','infrastructure'}:continue
        geom=project(shape(f['geometry']),'EPSG:4326',crs)
        fraction=geometry_coverage(geom,footprint)
        rows.append({'id':str(f['id']),'kind':kind,'terrain_quality_fraction':fraction,
            'status':'FULL_NATIVE_QUALITY_FOOTPRINT' if fraction is not None and fraction>=1-1e-9 else
                'PARTIAL_NATIVE_QUALITY_FOOTPRINT' if fraction is not None and fraction>0 else 'NO_NATIVE_QUALITY_FOOTPRINT'})
    from collections import Counter
    result={'source_run':'event-fe47db331390','frozen_run_hashes_verified':len(freeze['files']),
        'terrain_quality_sha256':sha256(terrain/'quality-filtered-native.tif'),'layers':layers,
        'mapped_receptors':len(rows),'receptor_terrain_support':dict(Counter(r['status'] for r in rows)),
        'rows':rows,'interpretation':'Coverageonly;posteventterrainandunverifiedalignmentprecludevalidatedexposureclaim',
        'infrastructure_source':'RetainedhistoricalOSM;notcompletefieldinventory','no_source_candidates_modified':True}
    save_json(output,result);print(json.dumps({k:v for k,v in result.items() if k!='rows'}));return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--terrain',required=True);p.add_argument('--run',required=True);p.add_argument('--output',required=True)
    a=p.parse_args();run(a.terrain,a.run,a.output)
