"""Bounded GeoTIFF ingestion and deterministic NDVI. No VLM-derived measurements."""
import math,hashlib
from pathlib import Path
import numpy as np
import rasterio
from rasterio.io import MemoryFile
from rasterio.enums import ColorInterp
from PIL import Image
from pyproj import CRS,Transformer
ALIASES={'b04':'red','b4':'red','b03':'green','b3':'green','b02':'blue','b2':'blue','b08':'nir','b8':'nir','scl':'scl','red':'red','green':'green','blue':'blue','nir':'nir'}
def bands(src):
    result={}
    for i,d in enumerate(src.descriptions,1):
        if d and d.strip().lower() in ALIASES:result[ALIASES[d.strip().lower()]]=i
    for i,c in enumerate(src.colorinterp,1):
        if c in [ColorInterp.red,ColorInterp.green,ColorInterp.blue]:result.setdefault(c.name,i)
    return result

def ingest(raw,target):
    if hashlib.sha256(raw).hexdigest()=='548f361711f37ec83a459d7d076944b33efb1888837b39ce4cfa619ce8b8dd79':
        raise ValueError('This obsolete sample has invalid calibration. Load the corrected Dehradun sample.')

    with MemoryFile(raw) as mem,mem.open() as src:
        if src.driver!='GTiff':raise ValueError('Only GeoTIFF is supported for geospatial ingestion.')
        if src.count>16 or src.width*src.height>4_194_304:raise ValueError('Use a GeoTIFF crop of at most 4 million pixels and 16 bands.')
        mapping=bands(src)
        if not all(n in mapping for n in ['red','green','blue']):raise ValueError('Band identities are missing. Label RGB bands red/green/blue or B04/B03/B02 before uploading; band order is never guessed.')
        rgb=[]
        for n in ['red','green','blue']:
            k=mapping[n];a=src.read(k,masked=True).astype('float32').filled(np.nan)*src.scales[k-1]+src.offsets[k-1]
            valid=np.isfinite(a);low,high=np.percentile(a[valid],[2,98]) if valid.any() else (0,1)
            rgb.append(np.where(valid,np.clip((a-low)/max(float(high-low),1e-6),0,1),0))
        preview=Image.fromarray((np.stack(rgb,-1)*255).astype('uint8'))
        crs=CRS.from_user_input(src.crs) if src.crs else None
        transform=list(src.transform)[:6]
        bounds=list(src.bounds);wgs=None
        if crs:
            from rasterio.warp import transform_bounds
            wgs=list(transform_bounds(src.crs,'EPSG:4326',*src.bounds,densify_pts=21))
        tags=src.tags()
        spectral=all(n in mapping for n in ['red','nir']) and tags.get('reflectance_units')=='surface_reflectance'
        metadata={'calibration_version':tags.get('calibration_version','user-supplied'),'crs':str(src.crs) if src.crs else None,'width':src.width,'height':src.height,'transform':transform,'bounds':bounds,'bounds_wgs84':wgs,'resolution':list(src.res),'bands':mapping,'band_descriptions':list(src.descriptions),'nodata':str(src.nodata),'scales':list(src.scales),'offsets':list(src.offsets),'acquired':tags.get('acquired'),'source_item':tags.get('source_item'),'attribution':tags.get('attribution'),'ndvi_supported':spectral,'quality_mask_available':'scl' in mapping,'preview_processing':'Per-channel 2nd–98th percentile RGB display stretch; analytical values are preserved.'}
    Path(target).write_bytes(raw)
    return preview,metadata

def calculate(red,nir,quality=None):
    # Keep threshold comparisons and exports in the same precision. Float32
    # rounded near-boundary pixels onto the threshold in multi-scene trials.
    red=np.asarray(red,dtype='float64');nir=np.asarray(nir,dtype='float64')
    valid=np.isfinite(red)&np.isfinite(nir)&(red>=0)&(nir>=0)&((nir+red)>1e-8)
    if quality is not None:valid&=np.isin(quality,[4,5,6,7])
    ndvi=np.full(red.shape,np.nan,dtype='float64')
    np.divide(nir-red,nir+red,out=ndvi,where=valid)
    return ndvi,valid

def analyse(path,output,threshold=0.5):
    if not math.isfinite(threshold) or not -1<=threshold<=1:raise ValueError('NDVI threshold must be between -1 and 1.')
    output=Path(output);output.mkdir(exist_ok=True)
    with rasterio.open(path) as src:
        m=bands(src)
        if not all(k in m for k in ['red','nir']) or src.tags().get('reflectance_units')!='surface_reflectance':raise ValueError('NDVI requires labelled red/NIR bands and confirmed surface-reflectance units. An RGB image is not sufficient.')
        def read(name):
            k=m[name];return src.read(k,masked=True).astype('float64').filled(np.nan)*src.scales[k-1]+src.offsets[k-1]
        red,nir=read('red'),read('nir');quality=read('scl') if 'scl' in m else None
        ndvi,valid=calculate(red,nir,quality);selected=valid&(ndvi>=threshold);count=int(valid.sum())
        if not count:raise ValueError('No valid pixels remain after quality and reflectance checks.')
        area=None;area_method='Unavailable: a supported projected CRS in metres is required.'
        if src.crs:
            c=CRS.from_user_input(src.crs)
            if c.is_projected and len(c.axis_info)>=2 and all(abs(a.unit_conversion_factor-1)<1e-9 for a in c.axis_info[:2]):
                pixel_area=abs(src.transform.a*src.transform.e-src.transform.b*src.transform.d)
                if math.isfinite(pixel_area) and pixel_area>0:
                    area=float(selected.sum()*pixel_area);area_method='Projected grid area from affine determinant; not terrain surface area.'
        overlay=np.zeros((*red.shape,4),dtype='uint8');overlay[selected]=[61,211,118,210]
        Image.fromarray(overlay).save(output/'overlay.png')
        profile=src.profile.copy();profile.update(count=1,dtype='float64',nodata=np.nan,compress='deflate')
        with rasterio.open(output/'ndvi.tif','w',**profile) as dst:dst.write(ndvi,1);dst.set_band_description(1,'NDVI');dst.update_tags(formula='(NIR-Red)/(NIR+Red)',threshold=str(threshold))
        finite=np.isfinite(red)&np.isfinite(nir)
        nonnegative=finite&(red>=0)&(nir>=0)
        denominator=nonnegative&((red+nir)>1e-8)
        rejected_quality=denominator&~np.isin(quality,[4,5,6,7]) if quality is not None else np.zeros(valid.shape,dtype=bool)
        exclusions={'nodata_or_nonfinite':int((~finite).sum()),'negative_reflectance':int((finite&~nonnegative).sum()),'zero_denominator':int((nonnegative&~denominator).sum()),'quality_after_reflectance_checks':int(rejected_quality.sum())}
        assert sum(exclusions.values())+count==valid.size
        summary={'numerical_precision':'float64 reflectance arithmetic, threshold comparison and NDVI export','calibration_version':src.tags().get('calibration_version','user-supplied'),'exclusion_counts':exclusions,'excluded_pixels':int(valid.size-count),'selected_percent_of_crop':float(100*selected.sum()/valid.size),'threshold':threshold,'valid_pixels':count,'total_pixels':int(valid.size),'selected_pixels':int(selected.sum()),'valid_coverage_percent':float(100*count/valid.size),'selected_percent_of_valid':float(100*selected.sum()/count),'selected_area_m2':area,'area_method':area_method,'ndvi_min':float(ndvi[valid].min()),'ndvi_max':float(ndvi[valid].max()),'ndvi_mean':float(ndvi[valid].mean()),'quality_mask_available':quality is not None,'quality_rule':'SCL 4,5,6,7 retained; other classes excluded.' if quality is not None else 'No cloud classification supplied; clouds may affect results.','interpretation':'Pixels meeting the stated NDVI threshold; not a vegetation health, density, or species diagnosis.'}
    return summary

def coordinate(metadata,col,row):
    from affine import Affine
    if not metadata['crs']:raise ValueError('No CRS is available.')
    if not (0<=col<metadata['width'] and 0<=row<metadata['height']):raise ValueError('Pixel is outside the raster.')
    x,y=Affine(*metadata['transform'])*(col+.5,row+.5)
    lon,lat=Transformer.from_crs(metadata['crs'],4326,always_xy=True).transform(x,y)
    return {'column':col,'row':row,'x':x,'y':y,'longitude':lon,'latitude':lat,'reference':'pixel centre'}
