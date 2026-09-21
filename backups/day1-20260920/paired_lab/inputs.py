"""Input contract and deterministic, auditable paired-workflow controller."""
import re,hashlib
from datetime import datetime
from pathlib import Path
import numpy as np
import rasterio

def inspect(path,modality,date='',units=''):
    path=Path(path)
    if modality not in ['optical','sar']:raise ValueError('Declare optical or SAR for each input.')
    with rasterio.open(path) as ds:
        if ds.driver!='GTiff':raise ValueError('Upload GeoTIFF/TIFF. Public benchmark samples are available separately.')
        if ds.width*ds.height>1024*1024 or ds.count>14:raise ValueError('Lab input limit: 1 megapixel and 14 bands.')
        arr=ds.read(masked=True)
        invalid=np.ma.getmaskarray(arr)|~np.isfinite(arr.data)
        if invalid.any():
            if ds.count not in [2,13] or ds.width!=512 or ds.height!=512:raise ValueError('Crop to a fully valid common region first: nodata/NaN pixels are not silently filled.')
            arr=np.ma.array(arr.data,mask=invalid).astype('float32');arr=np.ma.array(arr.filled(np.nan))
        tags=ds.tags();bands=list(ds.descriptions)
        tagged_date=tags.get('acquisition_date','')
        if date and tagged_date and date!=tagged_date:raise ValueError('Entered date conflicts with the TIFF acquisition date.')
        date=tagged_date or date
        return {'path':str(path),'modality':modality,'date':date,'units':units or tags.get('units',''),'sensor':tags.get('sensor',''),'bands':bands,'shape':[ds.height,ds.width],'count':ds.count,'dtype':str(arr.dtype),'crs':ds.crs.to_string() if ds.crs else None,'transform':list(ds.transform)[:6],'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'data':arr.data}

def route(query,records):
    q=' '.join(query.lower().split())
    if not q or len(q)>500:raise ValueError('Ask one question of up to 500 characters.')
    if len(records)!=2:raise ValueError('This isolated lab needs two images. Single-image VQA and NDVI remain in the main workspace.')
    temporal=bool(re.search(r'\b(chang\w*|before|after|dates?|increas\w*|decreas\w*|built|removed|construction)\b',q))
    cross=bool(re.search(r'\b(sar|radar|optical|fusion|sensors?|modalities)\b',q))
    modes=sorted(r['modality'] for r in records)
    if modes==['optical','sar']:
        if temporal:raise ValueError('These are different sensors, not a supported before/after pair. Split the temporal and cross-modal questions.')
        if re.search(r'\b(count|how many|outline|segment|highlight|where|hectares?|area in|regions?)\b',q):raise ValueError('This paired specialist predicts scene-level land-cover classes. It cannot map regions, count objects or measure area.')
        if not re.search(r'\b(land|cover|water|built-up|urban|forest|vegetation|class\w*|describe|identify|sar|radar|together|optical)\b',q):raise ValueError('Ask about land-cover classes from this optical–SAR pair.')
        return 'optical_sar'
    if modes==['optical','optical']:
        if cross:raise ValueError('SAR analysis requires a SAR input. Both supplied images are optical.')
        if not temporal:raise ValueError('Ask what changed between these two optical dates, or use the main workspace for a single-image question.')
        if re.search(r'\b(flood|water|forest|trees?|crop|vegetation|road|cars?|stadium)\b',q):raise ValueError('This initial temporal specialist detects building-related change only; this requested change category is not supported.')
        if re.search(r'\b(how many|count|hectares?)\b',q):raise ValueError('A change-pixel mask does not establish an object count or surveyed area.')
        return 'temporal'
    raise ValueError('Two-SAR temporal analysis is not implemented in this lab.')

def _legacy_validate(records,task,trusted_benchmark=False):
    a,b=records
    if a['shape']!=b['shape']:raise ValueError('Input grids differ in dimensions; align and crop them before analysis.')
    if not trusted_benchmark:
        if not a['crs'] or not b['crs']:raise ValueError('Uploaded pairs need a CRS and matching geographic grid. Use the supplied benchmark samples for trusted non-geographic paired crops.')
        if a['crs']!=b['crs'] or not np.allclose(a['transform'],b['transform'],rtol=0,atol=1e-7):raise ValueError('Geographic grids do not match. This lab does not silently register images.')
        times=[]
        for r in records:
            try:times.append(datetime.strptime(r['date'],'%Y-%m-%d'))
            except ValueError:raise ValueError('Provide the acquisition date for both images.')
        if task=='temporal' and times[0]>=times[1]:raise ValueError('The before date must precede the after date.')
        if task=='optical_sar' and abs((times[1]-times[0]).days)>14:raise ValueError('This initial cross-modal lab requires acquisitions within 14 days; closer dates are preferable.')
    if task=='temporal':
        if any(r['shape']!=[256,256] or r['count']!=3 or r['dtype']!='uint8' for r in records):raise ValueError('Use two corresponding 256 × 256, 8-bit RGB crops for this temporal checkpoint.')
        for r in records:
            if not trusted_benchmark and [str(x).lower() for x in r['bands']]!=['red','green','blue']:raise ValueError('RGB TIFF bands must be explicitly labelled red, green, blue in that order.')
    else:
        from engine import S1,S2
        for r in records:
            expected=S1 if r['modality']=='sar' else S2
            if len(r['bands'])!=len(expected) or set(r['bands'])!=set(expected):raise ValueError('Required bands: VV/VH for SAR; B02,B03,B04,B05,B06,B07,B08,B8A,B11,B12 for optical.')
            if r['shape']!=[120,120]:raise ValueError('This scene classifier requires 120 × 120 pixels at 10 m, matching its training footprint.')
            if not trusted_benchmark and (not rasterio.crs.CRS.from_string(r['crs']).is_projected or rasterio.crs.CRS.from_string(r['crs']).linear_units not in ['metre','meter']):raise ValueError('The 10 m grid must use a projected CRS in metres.')
            if not trusted_benchmark and (abs(abs(r['transform'][0])-10)>1e-6 or abs(abs(r['transform'][4])-10)>1e-6):raise ValueError('This classifier requires a 10 m projected grid; arbitrary pixel resizing changes its physical scope.')
            unit='dB' if r['modality']=='sar' else 'reflectance_x10000'
            sensor='Sentinel-1' if r['modality']=='sar' else 'Sentinel-2'
            if r['units']!=unit or r['sensor']!=sensor:raise ValueError(f'This checkpoint needs {sensor} data with units {unit}; no automatic sensor transfer or unit guessing.')
    return {'task':task,'pairing_basis':'publisher benchmark manifest' if trusted_benchmark else 'matching declared geographic grids and dates','warning':'Matching metadata is necessary but does not prove subpixel image registration.','inputs':[{k:v for k,v in r.items() if k not in ['data','path']} for r in records]}


def validate(records,task,trusted_benchmark=False,enforce_content=False):
    if len(records)!=2:raise ValueError('Exactly two images are required for paired analysis.')
    a,b=records
    for r in records:
        t=np.asarray(r['transform'],dtype=float)
        if t.shape!=(6,) or not np.isfinite(t).all() or abs(t[0]*t[4]-t[1]*t[3])<1e-15:raise ValueError('Invalid or singular geographic transform.')
        if r.get('crs') and (abs(t[1])>1e-10 or abs(t[3])>1e-10):raise ValueError('Rotated or sheared grids are not supported; reproject both inputs explicitly.')
    if task=='water_map':
        from flood import S2_BANDS
        if a['shape']!=b['shape'] or a['shape']!=[512,512]:raise ValueError('Water mapping currently requires corresponding 512 × 512 source grids.')
        if not a['crs'] or a['crs']!=b['crs'] or not np.allclose(a['transform'],b['transform'],rtol=0,atol=1e-10):raise ValueError('Water mapping requires matching georeferenced grids.')
        dates=[]
        for r in records:
            sar=r['modality']=='sar';expected=['VV','VH'] if sar else S2_BANDS
            if r['bands']!=expected:raise ValueError('Water mapping requires ordered VV/VH and all 13 Sentinel-2 L1C bands.')
            if r['sensor']!=('Sentinel-1 GRD' if sar else 'Sentinel-2 L1C'):raise ValueError('Water model requires Sentinel-1 GRD and Sentinel-2 L1C, not other processing levels or sensors.')
            if r['units']!=('dB' if sar else 'reflectance_x10000'):raise ValueError('Water mapping input units do not match training.')
            try:dates.append(datetime.strptime(r['date'],'%Y-%m-%d'))
            except ValueError:raise ValueError('Water mapping requires both acquisition dates.')
        if abs((dates[1]-dates[0]).days)>14:raise ValueError('Water mapping requires acquisitions within 14 days; flooding may change even within that interval.')
        valid=np.isfinite(a['data']).all(0)&np.isfinite(b['data']).all(0)
        if not valid.any():raise ValueError('No common finite input pixels.')
        checks={'task':task,'pairing_basis':'matching geographic grids and acquisition metadata','valid_pixels':int(valid.sum()),'full_pixels':int(valid.size),'warning':'Cross-sensor content registration is not independently certified. Time differences can move water boundaries.','inputs':[{k:v for k,v in r.items() if k not in ['data','path']} for r in records]}
    else:checks=_legacy_validate(records,task,trusted_benchmark)
    if task=='temporal':
        if not trusted_benchmark and a.get('sensor') and b.get('sensor') and a['sensor']!=b['sensor']:raise ValueError('This temporal checkpoint has not been validated across different sensors.')
        if enforce_content:
            from registration import diagnose
            diagnostics=diagnose(a['data'].transpose(1,2,0),b['data'].transpose(1,2,0));checks['registration']=diagnostics
            if diagnostics['status']=='misaligned':raise ValueError('Visible features are misaligned: estimated displacement exceeds 1.5 pixels. Align the pair explicitly.')
            if diagnostics['status']=='unverified' and not trusted_benchmark:raise ValueError('Could not verify shared optical features. Confirm location and registration before analysis.')
    return checks
