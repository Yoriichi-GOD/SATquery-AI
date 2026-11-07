"""Same drainage implementation across urban cases, with explicit resolution refusal."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np
import rasterio
from rasterio.warp import reproject,Resampling,transform_bounds
from affine import Affine

from research.datasets.acquire import download,discover
from research.terrain_exposure.hydrology import derive
from research.terrain_exposure.io import Grid,canonical_hash,save_json,sha256,write_raster,resolution_status,read_raster
from research.terrain_exposure.graph import Observation,build_graph,export_graph

LICENSE='https://registry.opendata.aws/copernicus-dem/'


def tiles(bbox):
    west,south,east,north=bbox
    values=[]
    for lat in range(math.floor(south),math.ceil(north)):
        for lon in range(math.floor(west),math.ceil(east)):
            name=f'Copernicus_DSM_COG_30_{"N" if lat>=0 else "S"}{abs(lat):02d}_00_{"E" if lon>=0 else "W"}{abs(lon):03d}_00_DEM'
            values.append((name,f'https://copernicus-dem-90m.s3.amazonaws.com/{name}/{name}.tif'))
    if len(values)>4:raise ValueError('Urban demo supports at most four public tiles')
    return values


def ingest_built_up(before,after,built_code,before_time,after_time):
    from datetime import datetime
    if datetime.fromisoformat(before_time.replace('Z','+00:00'))>=datetime.fromisoformat(after_time.replace('Z','+00:00')):
        raise ValueError('Strict temporal order required')
    a,va,ga,ma=read_raster(before);b,vb,gb,mb=read_raster(after)
    if ga!=gb:raise ValueError('Built-up source grids differ; no silent registration')
    if not np.issubdtype(a.dtype,np.integer) or not np.issubdtype(b.dtype,np.integer):
        raise ValueError('Categorical built-up inputs required; a spectral index is not a class map')
    valid=va&vb
    return Observation('built_up_change',(a!=built_code)&(b==built_code)&valid,valid,ga,
        {'sha256':canonical_hash([ma['sha256'],mb['sha256']]),'source_maps':[ma,mb],
         'dataset':'Operator-declared categorical maps; upstream classification accuracy not certified'},
        [before_time,after_time],'Explicit categorical non-built-to-built transition')


def run(config_path,cache,output,with_discovery=True):
    config=json.loads(Path(config_path).read_text());output=Path(output);cache=Path(cache)
    if output.exists():raise FileExistsError('Choose a new immutable case output')
    receipts=[];paths=[]
    for name,url in tiles(config['bbox_wgs84']):
        p=cache/(name+'.tif')
        expected=config.get('source_sha256',{}).get(name)
        if expected is None:raise ValueError('Pin the public terrain source hash before analytical replay')
        receipts.append(download(url,p,license_url=LICENSE,expected_sha256=expected));paths.append(p)
    bounds=transform_bounds('EPSG:4326',config['analysis_crs'],*config['bbox_wgs84'],densify_pts=21)
    resolution=config['resolution_m']
    left,bottom,right,top=bounds
    left=math.floor(left/resolution)*resolution;top=math.ceil(top/resolution)*resolution
    grid=Grid((math.ceil((top-bottom)/resolution),math.ceil((right-left)/resolution)),
              Affine(resolution,0,left,0,-resolution,top),config['analysis_crs'])
    z=np.full(grid.shape,np.nan)
    for filename in paths:
        candidate=np.full(grid.shape,np.nan)
        with rasterio.open(filename) as src:
            native=src.read(1,masked=True).astype('float64').filled(np.nan)
            reproject(native,candidate,src_transform=src.transform,src_crs=src.crs,src_nodata=np.nan,
                      dst_transform=grid.transform,dst_crs=grid.crs,dst_nodata=np.nan,resampling=Resampling.bilinear)
        use=~np.isfinite(z)&np.isfinite(candidate);z[use]=candidate[use]
    hydro=derive(z,np.isfinite(z),grid,config['stream_area_m2'])
    output.mkdir(parents=True)
    for name,array in [('original_dem',z),('conditioned_dem',hydro.filled),('fill_depth',hydro.filled-z),
                       ('hand_m',hydro.hand),('slope_deg',hydro.slope),('contributing_area_m2',hydro.accumulation*grid.area),
                       ('flow_direction_d8',hydro.d8),('catchment_outlet',hydro.catchment)]:
        write_raster(output/(name+'.tif'),array,grid,hydro.valid)
    discovery=[]
    if with_discovery:
        for interval in config['stac_intervals']:
            try:
                result=discover(config['bbox_wgs84'],interval)
                name='stac-'+interval[:10]+'.json';save_json(output/name,result)
                discovery.append({'file':name,'items':len(result['response']['features']),'truncated':result['truncated'],'status':'DISCOVERED_NOT_DOWNLOADED'})
            except Exception as error:
                discovery.append({'interval':interval,'status':'UNAVAILABLE','error_type':type(error).__name__,'reason':str(error)[:180]})
    summary={'case_id':config['case_id'],'population':'GENUINE_PUBLIC_DSM_COARSE_TRANSFER',
             'status':'COARSE_TERRAIN_COMPLETE_STREET_CONNECTIVITY_WITHHELD',
             'resolution':resolution_status(resolution,config['required_feature_width_m']),
             'hydrology':hydro.summary,'grid':grid.describe(),'sources':receipts,'discovery':discovery,
             'missing_inputs':config['missing_inputs'],'legal_claims':config['legal_claims'],
             'configuration':config,'configuration_sha256':canonical_hash(config),
             'urban_exposure':'UNAVAILABLE: no suitable surveyed drainage, receptor labels or high-resolution terrain',
             'built_up_change':'UNAVAILABLE: categorical temporal maps not supplied; ingestion API implemented',
             'limitations':['Same generic drainage algorithm, not a zero-shot validated urban model',
                            'DSM is not bare-earth and has no kerbs, culverts or drain capacity',
                            'Window edges are open artificial outlets, not verified municipal outlets',
                            'Temporal STAC discovery is not processed change-detection imagery',
                            'Two-cell scale gate is necessary screening, not a sufficient physics criterion']}
    save_json(output/'summary.json',summary)
    save_json(output/'manifest.json',{'state':'complete','files':{p.name:sha256(p) for p in sorted(output.iterdir()) if p.is_file()},
                                    'configuration_sha256':canonical_hash(config),'sources':receipts})
    return summary


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--config',required=True);p.add_argument('--cache',required=True);p.add_argument('--output',required=True)
    p.add_argument('--without-discovery',action='store_true');a=p.parse_args()
    result=run(a.config,a.cache,a.output,not a.without_discovery)
    print(json.dumps({k:result[k] for k in ['case_id','status','resolution','hydrology','discovery','missing_inputs']},indent=2))


if __name__=='__main__':main()
