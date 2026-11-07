"""Bounded native COG window acquisition with public signing and explicit source identity."""
from __future__ import annotations
from datetime import datetime,timezone
import math,time
from pathlib import Path
from urllib.parse import urlsplit,urlunsplit
import requests
import numpy as np
import rasterio
from rasterio.warp import transform_bounds
from rasterio.windows import Window,from_bounds
from research.terrain_exposure.io import sha256,save_json

HOSTS={'planetarycomputer.microsoft.com','ai4edataeuwest.blob.core.windows.net','landsateuwest.blob.core.windows.net',
       'nasadem.blob.core.windows.net','nasademeuwest.blob.core.windows.net','copernicus-dem-30m.s3.amazonaws.com','copernicus-dem-90m.s3.amazonaws.com',
       'esa-worldcover.s3.eu-central-1.amazonaws.com','s3.waw4-1.cloudferro.com'}

def public_url(url):
    p=urlsplit(url)
    if p.scheme!='https' or p.hostname not in HOSTS or p.username or p.password:
        raise ValueError('Unapproved public raster source')
    return urlunsplit((p.scheme,p.netloc,p.path,'',''))

def get_json(url,params=None):
    if urlsplit(url).hostname!='planetarycomputer.microsoft.com':raise ValueError('Only declared PC metadata/signing API')
    for attempt in range(4):
        response=requests.get(url,params=params,timeout=40)
        if response.status_code!=429 or attempt==3:break
        delay=response.headers.get('Retry-After','15')
        time.sleep(min(60,max(1,int(delay))) if delay.isdigit() else 15)
    response.raise_for_status()
    return response.json()

_TOKENS={}

def sign(url):
    url=public_url(url)
    if urlsplit(url).hostname.endswith('.blob.core.windows.net'):
        account=urlsplit(url).hostname.split('.')[0];container=urlsplit(url).path.split('/')[1]
        key=(account,container)
        if key not in _TOKENS:
            _TOKENS[key]=get_json(f'https://planetarycomputer.microsoft.com/api/sas/v1/token/{account}/{container}')['token']
        signed=url+'?'+_TOKENS[key].lstrip('?')
        if public_url(signed)!=url:raise ValueError('Signer changed the source identity')
        return signed
    return url

def native_window(bounds,transform,width,height):
    raw=from_bounds(*bounds,transform=transform)
    left=max(0,math.floor(raw.col_off));top=max(0,math.floor(raw.row_off))
    right=min(width,math.ceil(raw.col_off+raw.width));bottom=min(height,math.ceil(raw.row_off+raw.height))
    if right<=left or bottom<=top:raise ValueError('Source has no coverage for requested window')
    return Window(left,top,right-left,bottom-top)

def acquire(url,bbox,destination,*,license_url,product,role='input',nodata=None,max_pixels=4_000_000):
    base=public_url(url);destination=Path(destination);receipt_path=destination.with_suffix('.source.json')
    if len(bbox)!=4 or not(-180<=bbox[0]<bbox[2]<=180 and -90<=bbox[1]<bbox[3]<=90):raise ValueError('Invalid bbox')
    if destination.exists():
        if not receipt_path.exists():raise ValueError('Cached window lacks provenance')
        saved=__import__('json').loads(receipt_path.read_text())
        if saved['source_url']!=base or saved['bbox_wgs84']!=list(bbox) or saved['sha256']!=sha256(destination):
            raise ValueError('Cached window source/request/hash mismatch')
        return saved
    signed=sign(base)
    head=requests.head(signed,timeout=40);head.raise_for_status()
    if 'bytes' not in head.headers.get('Accept-Ranges','').lower():
        with requests.get(signed,headers={'Range':'bytes=0-15'},timeout=40,stream=True) as probe:
            if probe.status_code!=206:raise ValueError('Native source does not support range reads')
            probe.raw.read(16)
    etag=head.headers.get('ETag');size=head.headers.get('Content-Length')
    with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN='EMPTY_DIR',GDAL_HTTP_TIMEOUT='40',GDAL_HTTP_MAX_RETRY='2',
                      CPL_VSIL_CURL_ALLOWED_EXTENSIONS='.tif',GDAL_CACHEMAX=64):
        with rasterio.open(signed) as src:
            if src.count!=1 or src.crs is None:raise ValueError('One declared georeferenced raster band required')
            bounds=transform_bounds('EPSG:4326',src.crs,*bbox,densify_pts=21)
            window=native_window(bounds,src.transform,src.width,src.height)
            if window.width*window.height>max_pixels:raise ValueError('Native case window exceeds pixel budget')
            data=src.read(1,window=window);valid=src.read_masks(1,window=window)>0
            source_nodata=src.nodata if nodata is None else nodata
            if source_nodata is not None:valid&=data!=source_nodata
            valid&=np.isfinite(data)
            transform=src.window_transform(window)
            metadata={'crs':src.crs.to_string(),'transform':list(transform)[:6],'native_resolution':list(src.res),
                'native_shape':[src.height,src.width],'window_col_row_width_height':list(map(int,window.flatten())),
                'dtype':str(data.dtype),'nodata':source_nodata,'units':src.units[0],'scale':src.scales[0],'offset':src.offsets[0]}
    check=requests.head(signed,timeout=40);check.raise_for_status()
    if etag and check.headers.get('ETag')!=etag:raise ValueError('Source version changed during window read')
    destination.parent.mkdir(parents=True,exist_ok=True)
    with rasterio.Env(GDAL_TIFF_INTERNAL_MASK=True):
        with rasterio.open(destination,'w',driver='GTiff',height=data.shape[0],width=data.shape[1],count=1,
                           dtype=data.dtype,crs=metadata['crs'],transform=transform,nodata=source_nodata,compress='deflate') as dst:
            dst.write(data,1);dst.write_mask(valid.astype('uint8')*255)
    receipt={'source_url':base,'product':product,'role':role,'license_url':license_url,
        'retrieved_utc':datetime.now(timezone.utc).isoformat(),'source_etag':etag,'source_content_length':None if size is None else int(size),
        'bbox_wgs84':list(bbox),'native_window':metadata,'pixels':int(data.size),'valid_pixels':int(valid.sum()),
        'sha256':sha256(destination),'bytes':destination.stat().st_size,'resampling':'none; native source pixel window',
        'source_full_file_sha256':'UNAVAILABLE_WINDOWED_REMOTE_SOURCE','account_credentials_used':False,
        'public_sas_token_persisted':False,'limitations':['Requested geographic bbox enclosed by native pixel window; analysis must apply its exact ROI',
            'Derived window hash plus remote ETag identify input; no full-global-tile checksum is asserted']}
    save_json(receipt_path,receipt);return receipt
