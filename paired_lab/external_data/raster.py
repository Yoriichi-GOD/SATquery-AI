"""Metadata plus bounded native-pixel windows. Analytical pixels are never repaired."""
import math
import time
from pathlib import Path
import numpy as np
import rasterio
from rasterio.windows import Window
from .common import CHUNK, DataError, fail

WINDOW = 256
MAX_BLOCK_BYTES = 16 * CHUNK
ENV = dict(GDAL_CACHEMAX=16 * CHUNK, GDAL_DISABLE_READDIR_ON_OPEN='EMPTY_DIR', GDAL_PAM_ENABLED='NO')


def windows(width, height):
    for row in range(0, height, WINDOW):
        for col in range(0, width, WINDOW):
            yield Window(col, row, min(WINDOW, width-col), min(WINDOW, height-row))


def finite(value):
    return float(value) if value is not None and math.isfinite(float(value)) else None


def inspect_raster(path, check=lambda: None, progress=lambda value: None, full=True):
    start = time.perf_counter()
    with Path(path).open('rb') as stream:
        magic = stream.read(4)
    if magic not in (b'II*\0', b'MM\0*', b'II+\0', b'MM\0+'):
        fail('NOT_A_TIFF', 'The file does not have a TIFF or BigTIFF signature.')
    try:
        with rasterio.Env(**ENV), rasterio.open(path, driver='GTiff') as ds:
            if ds.count > 64 or ds.width * ds.height > 10**11:
                fail('RASTER_STRUCTURE_LIMIT', 'Inspection supports at most 64 bands and 100 billion pixels; use staged input.')
            if any(np.dtype(t).kind not in 'uif' for t in ds.dtypes):
                fail('UNSUPPORTED_DTYPE', 'Complex or non-numerical rasters need an explicit external preparation step.')
            largest = max(h*w*np.dtype(t).itemsize*ds.count for (h,w),t in zip(ds.block_shapes,ds.dtypes))
            if largest > MAX_BLOCK_BYTES:
                fail('UNSAFE_RASTER_BLOCK', 'A native TIFF block exceeds 16 MiB. Retile explicitly before inspection; no implicit conversion is performed.')
            t = list(ds.transform)[:6]
            determinant = t[0]*t[4]-t[1]*t[3]
            valid_transform = all(math.isfinite(v) for v in t) and abs(determinant)>1e-15
            crs = ds.crs
            raw_tags=ds.tags();priority=['sensor','units','reflectance_units','acquisition_date','acquired','source_item','source_id','vertical_units','vertical_datum','terrain_corrected','relative_orbit','orbit_state','scene_id']
            keys=list(dict.fromkeys([k for k in priority if k in raw_tags]+sorted(raw_tags)))[:64]
            tags={str(k):str(raw_tags[k])[:1024] for k in keys}
            metadata_truncated=len(keys)<len(raw_tags) or any(len(str(raw_tags[k]))>1024 for k in keys) or any(len(str(v or ''))>128 for v in ds.descriptions)
            del raw_tags
            metadata = dict(driver=ds.driver, tiff_subtype='BigTIFF' if magic[2] in (43,0) and b'+' in magic else 'TIFF',
                bytes=Path(path).stat().st_size, width=ds.width, height=ds.height, count=ds.count,
                dtypes=list(ds.dtypes), bands=[v[:128] if v else v for v in ds.descriptions],metadata_truncated=metadata_truncated, colorinterp=[v.name for v in ds.colorinterp],
                scales=[finite(v) for v in ds.scales], offsets=[finite(v) for v in ds.offsets],
                compression=ds.compression.name if ds.compression else None, tiled=ds.is_tiled,
                blocks=[list(v) for v in ds.block_shapes], largest_decode_block_bytes=largest,
                overviews=[ds.overviews(i) for i in ds.indexes], layout=ds.tags(ns='IMAGE_STRUCTURE').get('LAYOUT'),
                crs=crs.to_string() if crs else None, epsg=crs.to_epsg() if crs else None,
                projected=bool(crs and crs.is_projected), linear_units=crs.linear_units if crs and crs.is_projected else None,
                transform=t, valid_transform=valid_transform, georeferencing_valid=bool(crs and valid_transform and not ds.transform.is_identity), rotated_or_sheared=abs(t[1])+abs(t[3])>1e-10,
                north_up=valid_transform and t[0]>0 and t[4]<0 and abs(t[1])+abs(t[3])<1e-10,
                resolution=[finite(v) for v in ds.res], bounds=[finite(v) for v in ds.bounds],
                nodata=[finite(v) for v in ds.nodatavals], nodata_repr=[str(v) for v in ds.nodatavals], tags=tags,
                authenticity='Declared metadata only; sensor identity and physical registration are not independently certified.')
            statistics = [dict(min=None,max=None,valid=0,invalid=0,nan=0,infinity=0) for _ in ds.indexes]
            total_windows = math.ceil(ds.width/WINDOW)*math.ceil(ds.height/WINDOW)
            chosen = set([0,total_windows//4,total_windows//2,3*total_windows//4,total_windows-1])
            scanned = common = processed = 0
            preview = np.zeros((min(512,ds.height),min(512,ds.width),3),dtype='uint8')
            for wi, window in enumerate(windows(ds.width, ds.height)):
                if not full and wi not in chosen:
                    continue
                check()
                shared = np.ones((int(window.height),int(window.width)),dtype=bool)
                for index in ds.indexes:
                    arr = ds.read(index, window=window, masked=True)
                    raw = np.asarray(arr.data)
                    mask = ~np.ma.getmaskarray(arr) & np.isfinite(raw)
                    shared &= mask
                    row = statistics[index-1]
                    row['valid'] += int(mask.sum())
                    row['invalid'] += int(mask.size-mask.sum())
                    row['nan'] += int(np.isnan(raw).sum())
                    row['infinity'] += int(np.isinf(raw).sum())
                    if mask.any():
                        lo, hi = float(raw[mask].min()), float(raw[mask].max())
                        row['min'] = lo if row['min'] is None else min(row['min'],lo)
                        row['max'] = hi if row['max'] is None else max(row['max'],hi)
                    if index <= 3 and window.row_off < preview.shape[0] and window.col_off < preview.shape[1]:
                        # Display only: bounded native top-left window; no inference uses this stretch.
                        ph=min(int(window.height),preview.shape[0]-int(window.row_off));pw=min(int(window.width),preview.shape[1]-int(window.col_off))
                        values=raw[:ph,:pw];usable=mask[:ph,:pw]
                        lo,hi=np.percentile(values[usable],[2,98]) if usable.any() else (0,1)
                        display=np.zeros((ph,pw),dtype='uint8')
                        display[usable]=(np.clip((values[usable].astype('float64')-lo)/max(hi-lo,1e-9),0,1)*255).astype('uint8')
                        preview[int(window.row_off):int(window.row_off)+ph,int(window.col_off):int(window.col_off)+pw,index-1]=display
                common += int(shared.sum());scanned += shared.size;processed += 1
                if wi%16==0:progress(dict(stage='Reading bounded raster windows',windows_done=processed,windows_total=total_windows,scanned_pixels=scanned))
            if ds.count==1:preview[:,:,1:]=preview[:,:,:1]
            metadata.update(statistics=statistics, common_valid_pixels=common, inspected_pixels=scanned,
                full_pixels=ds.width*ds.height, valid_fraction=common/scanned if scanned else None,
                scan_scope='all native pixels' if full else 'five sampled native windows; other blocks unverified',
                all_blocks_read=bool(full), max_read_window=[WINDOW,WINDOW,1], seconds=time.perf_counter()-start)
            from PIL import Image
            Image.fromarray(preview).save(Path(path).with_name('preview.png'))
            metadata['preview']='Top-left native window, up to 512×512; first three bands or single-band grayscale, independent 2–98% display stretch. Band meaning is not guessed; original analysis pixels unchanged.'
            return metadata
    except DataError:
        raise
    except Exception as exc:
        fail('UNREADABLE_RASTER', 'TIFF metadata or a scanned block is unreadable: '+str(exc)[:300])
