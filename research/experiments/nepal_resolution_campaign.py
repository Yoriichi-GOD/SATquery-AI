"""New GLO30 buffered replay, retaining original masks/receptors and development role."""
import argparse,json
from pathlib import Path
import rasterio
from rasterio.warp import transform_bounds
from research.datasets.cog import acquire
from research.terrain_exposure.io import save_json,sha256
from research.terrain_exposure.replay import replay,verify_freeze

def run(flood_root,sources,output):
    sources=Path(sources);output=Path(output);output.mkdir(parents=True,exist_ok=False)
    frozen=verify_freeze(Path(flood_root)/'artifacts/runs/event-fe47db331390')
    with rasterio.open(Path(flood_root)/'artifacts/runs/event-fe47db331390/prediction.tif') as src:
        l,b,r,t=src.bounds
        # 1900m source coverage encloses the declared1800m metric replay buffer plus edge interpolation.
        bbox=transform_bounds(src.crs,'EPSG:4326',l-1900,b-1900,r+1900,t+1900,densify_pts=64)
    amendment={'purpose':'Finite buffered DEM context for30/90m sensitivity; no parameter or label selection',
        'source_bbox_wgs84':list(bbox),'metric_replay_buffer_m':1800,'source_buffer_m':1900,
        'comparison':'Same native GLO30 source resampled to30m and90m; not a hydraulic or independent accuracy experiment',
        'source_masks_unchanged':frozen['files'],'role':'previously_inspected_development'}
    save_json(output/'protocol-amendment.json',amendment)
    tile='Copernicus_DSM_COG_10_N28_00_E085_00_DEM'
    source=sources/'nepal/dem30-buffer.tif'
    receipt=acquire(f'https://copernicus-dem-30m.s3.amazonaws.com/{tile}/{tile}.tif',bbox,source,
        license_url='https://registry.opendata.aws/copernicus-dem/',product='CopernicusGLO30',max_pixels=4_000_000)
    save_json(output/'source.json',receipt)
    base=json.loads(Path('research/cases/nepal.json').read_text());summaries={}
    for cell in [30,90]:
        config={**base,'dem_resolution_m':cell,'terrain_product':'Copernicus GLO-30 DSM / AWS2021 release',
            'terrain_source_sha256':sha256(source),'terrain_source_url':receipt['source_url'],
            'limitations':base['limitations']+['GLO30 does not resolve10m targets; this is a resolution sensitivity, not new validation']}
        config['limitations']=[s for s in config['limitations'] if 'Native 90m' not in s]
        cp=output/f'configuration-{cell}m.json';save_json(cp,config)
        summaries[str(cell)]=replay(flood_root,source,cp,output/f'replay-{cell}m')
        print(json.dumps({'grid_m':cell,'state':'REPLAY_COMPLETE','summary':summaries[str(cell)]['graph']}),flush=True)
    save_json(output/'summary.json',summaries)
    return summaries

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--flood-root',required=True);p.add_argument('--sources',required=True);p.add_argument('--output',required=True)
    a=p.parse_args();run(a.flood_root,a.sources,a.output)
