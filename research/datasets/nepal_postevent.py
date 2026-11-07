"""Native2m post-event terrain crop through stored ZIP/COG range access."""
import argparse,json,logging
from pathlib import Path
import numpy as np
import rasterio
from rasterio.warp import transform_bounds,Resampling
from research.datasets.cog import native_window
from research.cases.process_campaign import roi,metric_grid,warp,safe_stats
from research.terrain_exposure.io import save_json,sha256,write_raster,resolution_status
from research.terrain_exposure.hydrology import derive

ROOT=Path(__file__).resolve().parents[2]
PROTOCOL=ROOT/'research/experiments/nepal-postevent-2m-20261107.json'
URL='https://zenodo.org/records/22842746/files/rasuwa_post_vantor_composites.zip'

def quality_mask(elevation,count,inside):
    if elevation.shape!=count.shape or count.shape!=inside.shape:raise ValueError('Native DEM/count grids differ')
    return inside&np.isfinite(elevation)&(elevation!=-9999)&np.isfinite(count)&(count>=2)

def run(output):
    out=Path(output)
    if out.exists():raise FileExistsError('Keep previous post-event terrain acquisitions immutable')
    out.mkdir(parents=True);cfg=json.loads(PROTOCOL.read_text());save_json(out/'protocol.json',cfg)
    logging.getLogger('rasterio').setLevel(logging.CRITICAL)
    records={};arrays={};ref=None
    for key,suffix in [('elevation','ordered'),('input_count','count')]:
        member=f'composites/rasuwa_post_vantor_20260827-20260908_2m_{suffix}_v1.0.tif'
        virtual=f'zip+{URL}!{member}'
        with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN='EMPTY_DIR',GDAL_HTTP_TIMEOUT='40',GDAL_HTTP_MAX_RETRY='2',
            GDAL_CACHEMAX=64,CPL_VSIL_CURL_CHUNK_SIZE=16384,GDAL_INGESTED_BYTES_AT_OPEN='16384'):
            with rasterio.open(virtual) as src:
                if src.count!=1 or src.crs.to_epsg()!=32645 or src.res!=(2.,2.) or not src.is_tiled:
                    raise ValueError('Unexpected native2m terrain contract')
                window=native_window(transform_bounds('EPSG:4326',src.crs,*cfg['bbox'],densify_pts=21),src.transform,src.width,src.height)
                if window.width*window.height>cfg['limits']['native_window_maxpixels']:raise ValueError('Native terrain pixel budget exceeded')
                transform=src.window_transform(window);grid=(int(window.height),int(window.width),transform,src.crs.to_string())
                if ref is not None and ref!=grid:raise ValueError('Native2m DEM/count grid identity differs')
                ref=grid;values=src.read(1,window=window);valid=src.read_masks(1,window=window)>0
                metadata={'source_archive_url':URL,'member':member,'native_shape':list(src.shape),'native_crs':src.crs.to_string(),
                    'native_resolution_m':list(src.res),'source_nodata':src.nodata,'source_vertical_reference':'WGS84ellipsoid',
                    'source_epoch':'2026-08-27through2026-09-08postevent','window':list(window.flatten()),'transform':list(transform)[:6],
                    'license':'CC-BY-NC4.0;originalLevel1Bimagerycopyright2026Vantor','full_archive_hash':'NOT_VERIFIED_WINDOWED_ACCESS',
                    'source_record':'https://doi.org/10.5281/zenodo.22842746','resampling':'None;native2mwindow'}
        path=out/(key+'.tif')
        with rasterio.Env(GDAL_TIFF_INTERNAL_MASK=True):
            with rasterio.open(path,'w',driver='GTiff',height=values.shape[0],width=values.shape[1],count=1,
                crs=ref[3],transform=transform,nodata=-9999,dtype=str(values.dtype),compress='deflate') as dst:
                dst.write(values,1);dst.write_mask(valid.astype('uint8')*255)
        metadata.update(sha256=sha256(path),bytes=path.stat().st_size)
        records[key]=metadata;arrays[key]=values.astype(float);arrays[key][~valid]=np.nan
        save_json(out/(key+'.source.json'),metadata)
        print(json.dumps({'asset':key,'state':'NATIVE2M_WINDOW_ACQUIRED','pixels':int(values.size),'bytes':metadata['bytes']}),flush=True)
    inside=roi(cfg['bbox'],arrays['elevation'].shape,ref[2],ref[3]);quality=quality_mask(arrays['elevation'],arrays['input_count'],inside)
    raw=inside&np.isfinite(arrays['elevation'])&(arrays['elevation']!=-9999)
    from affine import Affine
    # Grid contract limits analysis size; native input remains a bounded3millionpixel source.
    with rasterio.Env(GDAL_TIFF_INTERNAL_MASK=True):
        with rasterio.open(out/'quality-filtered-native.tif','w',driver='GTiff',height=quality.shape[0],width=quality.shape[1],
            crs=ref[3],transform=ref[2],count=1,dtype='float32',nodata=-9999,compress='deflate') as dst:
            dst.write(np.where(quality,arrays['elevation'],-9999).astype('float32'),1);dst.write_mask(quality.astype('uint8')*255)
    context={}
    for cell in cfg['analysis_pixel_m']:
        g=metric_grid({'bbox':cfg['bbox'],'crs':'EPSG:32645'},cell);z=warp([out/'quality-filtered-native.tif'],g,Resampling.bilinear)
        valid=roi(cfg['bbox'],g.shape,g.transform,g.crs)&np.isfinite(z)
        if not valid.any():context[str(cell)]={'state':'NO_VALID_QUALITY_TERRAIN'};continue
        h=derive(z,valid,g,cfg['hydrology']['stream_area_m2'],cfg['hydrology']['conditioning'])
        write_raster(out/f'dem-{cell}m.tif',z,g,valid);write_raster(out/f'slope-{cell}m.tif',h.slope,g,valid)
        write_raster(out/f'hand-{cell}m.tif',h.hand,g,np.isfinite(h.hand)&valid)
        context[str(cell)]={'grid':g.describe(),'hydrology':h.summary,'slope_degrees':safe_stats(h.slope[valid]),
            'hand_m':safe_stats(h.hand[valid]),'necessary_sampling_gate':resolution_status(cell,10),
            'exposure_readiness':'NOT_VALIDATED:posteventvintage,registration,accuracyandphysicaladequacyunresolved'}
    result={'source_record':cfg['source'],'protocol_sha256':sha256(PROTOCOL),'sources':records,
        'population':'ACTUAL_POSTEVENT_OPTICAL_STEREO_DEM_NOT_PREEVENT_TERRAIN','roi_native2m_pixels':int(inside.sum()),
        'native_valid_pixels':int(raw.sum()),'native_valid_fraction':float(raw.sum()/inside.sum()),
        'quality_count_ge2_pixels':int(quality.sum()),'quality_valid_fraction':float(quality.sum()/inside.sum()),
        'case_quality_gate':'COVERAGE_GATE_PASSED_ONLY' if quality.sum()/inside.sum()>=.95 else 'INSUFFICIENT_CASE_COVERAGE',
        'reported_input_count':safe_stats(arrays['input_count'][raw]),'terrain':context,
        'full_event_exposure_accuracy':'NOT_ASSESSED','vertical_datum_comparison':'NO_ELEVATION_DIFFERENCING_WITH_EGM2008_GLO30',
        'interpretation':'Highresolutionposteventmorphologicalcontext;cannotvalidatepre-eventhazardpredictionorconfirmdamage',
        'limitations':['PublishedsouthernmostWorldView3stripmaybebiased;inputcountdoesnotcertifylocalquality',
            'Native2mpostingnot2mverticalaccuracy','Providerstablegroundcoregistrationisnotlocalsurveycontrol',
            'Posteventtopographycanencodeconsequences;mustnotleakintoaprior-eventcausalbenchmark','FinitewindowandNoDataperimetersopentopographicboundaries']}
    save_json(out/'summary.json',result);save_json(out/'manifest.json',{'files':{p.name:sha256(p) for p in out.iterdir() if p.is_file()}})
    print(json.dumps({'roi_pixels':result['roi_native2m_pixels'],'quality_fraction':result['quality_valid_fraction'],
        'case_gate':result['case_quality_gate']}),flush=True)
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',required=True);a=p.parse_args();run(a.output)
