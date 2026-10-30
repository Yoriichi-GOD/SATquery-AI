"""Numerical DSM context. No flood-depth or hydrological-routing calculation."""
from __future__ import annotations

import hashlib
import json
import math
import os
import re
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from .flood_bridge import BridgeError

# One declared public-data demo, never a client-supplied outbound URL.
TILE = "Copernicus_DSM_COG_30_N28_00_E085_00_DEM"
SOURCE = f"https://copernicus-dem-90m.s3.amazonaws.com/{TILE}/{TILE}.tif"
DEMO_BBOX = [85.3232, 28.1552, 85.3483, 28.1820]
MAX_DOWNLOAD = 16 * 1024 * 1024


def slope_degrees(z, valid, dx, dy):
    """Horn 3x3 derivative; every contributing neighbour must be valid."""
    z = np.asarray(z, dtype=np.float64)
    valid = np.asarray(valid, dtype=bool) & np.isfinite(z)
    if z.ndim != 2 or z.shape != valid.shape or min(z.shape) < 3:
        raise ValueError("At least a 3 by 3 elevation grid is required")
    if not all(math.isfinite(v) and v > 0 for v in (dx, dy)):
        raise ValueError("Positive metric pixel spacing is required")
    p = [z[i:z.shape[0]-2+i, j:z.shape[1]-2+j] for i in range(3) for j in range(3)]
    support = np.ones((z.shape[0]-2, z.shape[1]-2), dtype=bool)
    for i in range(3):
        for j in range(3):
            support &= valid[i:z.shape[0]-2+i, j:z.shape[1]-2+j]
    dzdx = ((p[2]+2*p[5]+p[8])-(p[0]+2*p[3]+p[6]))/(8*dx)
    dzdy = ((p[6]+2*p[7]+p[8])-(p[0]+2*p[1]+p[2]))/(8*dy)
    slope = np.full(z.shape, np.nan)
    slope[1:-1, 1:-1] = np.where(support, np.degrees(np.arctan(np.hypot(dzdx, dzdy))), np.nan)
    return slope


def grid_summary(z, valid, transform, crs):
    from rasterio.crs import CRS
    crs = CRS.from_user_input(crs)
    if not crs.is_projected or crs.linear_units != "metre":
        raise ValueError("Reproject to a metric CRS before derivatives")
    if transform.b != 0 or transform.d != 0 or transform.a <= 0 or transform.e >= 0:
        raise ValueError("A north-up metric analysis grid is required")
    valid = np.asarray(valid, dtype=bool) & np.isfinite(z)
    if not valid.any():
        raise ValueError("No valid elevation pixels")
    slope = slope_degrees(z, valid, transform.a, abs(transform.e))
    values = z[valid]
    slopes = slope[np.isfinite(slope)]
    if not slopes.size:
        raise ValueError("No complete valid slope neighbourhoods")
    stats = {"elevation_min_m": float(values.min()), "elevation_max_m": float(values.max()),
             "elevation_median_m": float(np.median(values)),
             "elevation_p05_m": float(np.percentile(values, 5)), "elevation_p95_m": float(np.percentile(values, 95)),
             "slope_median_deg": float(np.median(slopes)), "slope_p95_deg": float(np.percentile(slopes, 95)),
             "valid_cells": int(valid.sum()), "total_cells": int(valid.size),
             "valid_fraction": float(valid.mean()), "valid_area_m2": float(valid.sum()*abs(transform.a*transform.e)),
             "slope_valid_cells": int(slopes.size)}
    # Subsample cell centres; source-wide extrema above are kept separately.
    step = max(1, math.ceil(max(z.shape)/128))
    rows, cols = np.arange(0,z.shape[0],step), np.arange(0,z.shape[1],step)
    zz = z[np.ix_(rows,cols)].astype(float)
    mask = valid[np.ix_(rows,cols)]
    ss = slope[np.ix_(rows,cols)]
    nullable = lambda a, m: [[float(v) if ok and np.isfinite(v) else None for v,ok in zip(row,mrow)] for row,mrow in zip(a,m)]
    mesh = {"x_m": [float(transform.c+(c+.5)*transform.a) for c in cols],
            "y_m": [float(transform.f+(r+.5)*transform.e) for r in rows],
            "z_m": nullable(zz, mask), "slope_deg": nullable(ss,mask),
            "sampling": "strided native analysis cell centres; not extrema preserving", "stride": step,
            "display_shape": list(zz.shape), "analysis_shape": list(z.shape)}
    return stats, mesh


class TerrainStore:
    def __init__(self, root):
        self.root = Path(root)
        self.lock = threading.Lock()

    def status(self):
        scenes = []
        for path in sorted(self.root.glob("terrain-*/scene.json")):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                scenes.append({"id":data["id"], "source":data["provenance"]["dataset"], "population":data["population"]})
            except (ValueError, KeyError):
                continue
        return {"scenes":scenes, "available_datasets":["COPERNICUS_90_PUBLIC_COG"],
                "cdse_authorization":"NOT_CHECKED", "network_requires_confirmation":True,
                "demo_bbox_wgs84":DEMO_BBOX, "max_download_bytes":MAX_DOWNLOAD,
                "notice":"Public GLO-90 DSM demo. CDSE 30m authorization is not inferred from account approval."}

    def scene_root(self, scene_id):
        if not re.fullmatch(r"terrain-[a-f0-9]{16}", scene_id):
            raise BridgeError(404,"Unknown terrain scene")
        root = self.root/scene_id
        if not (root/"scene.json").is_file():
            raise BridgeError(404,"Unknown terrain scene")
        return root

    def scene(self, scene_id):
        root = self.scene_root(scene_id)
        try:
            if (root/"scene.json").stat().st_size>4*1024*1024:
                raise ValueError()
            data = json.loads((root/"scene.json").read_text(encoding="utf-8"),parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))
            if data['id']!=scene_id or data['population']!='NEW_REAL_DEM' or set(data['hashes'])!={'source.tif','analysis.tif'}:
                raise ValueError()
            for name, digest in data["hashes"].items():
                if not isinstance(digest,str) or not re.fullmatch('[a-f0-9]{64}',digest):
                    raise ValueError()
                if not (root/name).is_file() or hashlib.sha256((root/name).read_bytes()).hexdigest()!=digest:
                    raise BridgeError(409,"Terrain evidence integrity check failed")
        except (ValueError,KeyError,TypeError):
            raise BridgeError(422,'Invalid saved terrain metadata') from None
        return data

    def obtain(self, confirmed=False):
        if confirmed is not True:
            raise BridgeError(422,"Confirm the bounded public GLO-90 download first")
        if not self.lock.acquire(blocking=False):
            raise BridgeError(409,"A terrain acquisition is already running")
        try:
            return self._obtain()
        finally:
            self.lock.release()

    def _obtain(self):
        import requests
        import rasterio
        from rasterio.io import MemoryFile
        from rasterio.windows import from_bounds
        from rasterio.warp import calculate_default_transform,reproject,Resampling
        from rasterio.transform import array_bounds
        start=time.perf_counter()
        for existing in self.status()['scenes']:
            saved=self.scene(existing['id'])
            if saved['provenance'].get('bbox_requested_wgs84')==DEMO_BBOX:
                return saved
        session=requests.Session();session.trust_env=False
        try:
            with session.get(SOURCE,stream=True,timeout=(5,25),allow_redirects=False) as response:
                if response.status_code==429:
                    raise BridgeError(429,"DEM provider quota; wait before retrying")
                if response.status_code!=200:
                    raise BridgeError(503,"Public DEM tile unavailable; no source substituted")
                size=0;chunks=[]
                for block in response.iter_content(65536):
                    size+=len(block)
                    if size>MAX_DOWNLOAD:
                        raise BridgeError(413,"DEM download exceeded 16 MiB cap")
                    chunks.append(block)
                raw=b"".join(chunks)
        except requests.RequestException:
            raise BridgeError(503,"Public DEM download failed; retry explicitly") from None
        digest=hashlib.sha256(raw).hexdigest()
        scene_id="terrain-"+hashlib.sha256((digest+json.dumps(DEMO_BBOX)).encode()).hexdigest()[:16]
        out=self.root/scene_id
        if (out/"scene.json").is_file():
            return self.scene(scene_id)
        try:
            with MemoryFile(raw) as memory,memory.open() as ds:
                if ds.count!=1 or ds.crs is None or ds.width*ds.height>2_000_000 or ds.dtypes[0]!='float32':
                    raise ValueError("Unexpected DEM raster")
                if ds.crs.to_epsg()!=4326 or not (ds.bounds.left<=DEMO_BBOX[0]<DEMO_BBOX[2]<=ds.bounds.right and ds.bounds.bottom<=DEMO_BBOX[1]<DEMO_BBOX[3]<=ds.bounds.top):
                    raise ValueError("Unexpected source coverage")
                window=from_bounds(*DEMO_BBOX,ds.transform).round_offsets().round_lengths()
                source=ds.read(1,window=window,masked=True).astype('float32')
                source_mask=np.ma.getmaskarray(source)|~np.isfinite(source.data)
                src=np.where(source_mask,-9999,source.data).astype('float32')
                src_transform=ds.window_transform(window)
                bounds=array_bounds(*source.shape,src_transform)
                transform,width,height=calculate_default_transform(ds.crs,'EPSG:32645',source.shape[1],source.shape[0],*bounds,resolution=90)
                if width*height>16384:
                    raise ValueError("Analysis grid exceeds cap")
                target=np.full((height,width),-9999,dtype='float32')
                reproject(src,target,src_transform=src_transform,src_crs=ds.crs,src_nodata=-9999,dst_transform=transform,dst_crs='EPSG:32645',dst_nodata=-9999,resampling=Resampling.bilinear)
                profile=dict(driver='GTiff',dtype='float32',count=1,width=width,height=height,crs='EPSG:32645',transform=transform,nodata=-9999)
                native_spacing=list(ds.res)
            valid=np.isfinite(target)&(target!=-9999)
            stats,mesh=grid_summary(target,valid,transform,'EPSG:32645')
        except (ValueError,rasterio.errors.RasterioError):
            raise BridgeError(422,"Invalid DEM or geospatial contract; terrain withheld") from None
        out.mkdir(parents=True,exist_ok=False)
        (out/'source.tif').write_bytes(raw)
        with rasterio.open(out/'analysis.tif','w',**profile) as ds:ds.write(target,1)
        data={"id":scene_id,"population":"NEW_REAL_DEM","statistics":stats,"mesh":mesh,
              "hashes":{"source.tif":digest,"analysis.tif":hashlib.sha256((out/'analysis.tif').read_bytes()).hexdigest()},
              "provenance":{"dataset":"COPERNICUS_90_PUBLIC_COG","source_url":SOURCE,"tile":TILE,
                            "downloaded_utc":datetime.now(timezone.utc).isoformat(),"bbox_requested_wgs84":DEMO_BBOX,
                            "native_spacing_degrees":native_spacing,"nominal_source_resolution_m":90,
                            "analysis_crs":"EPSG:32645","analysis_pixel_size_m":[90,90],
                            "resampling":"bilinear; nodata retained","slope":"Horn 3x3; all neighbours valid; borders excluded",
                            "units":"metres; Copernicus DSM orthometric height EGM2008",
                            "release":"AWS Copernicus DEM 2021 release; not an event-date acquisition",
                            "software_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                            "attribution":"Copernicus Digital Elevation Model accessed 30 October 2026 from AWS Registry of Open Data",
                            "license_url":"https://registry.opendata.aws/copernicus-dem/"},
              "limitations":["DSM includes buildings and vegetation; not a field elevation survey.",
                             "Terrain and flood are shown separately; no physical overlay registration or flood depth is inferred.",
                             "Source 90m spacing is not improved by mesh rendering or interpolation.",
                             "No independent vertical accuracy reference was evaluated."],
              "seconds_download_and_processing":time.perf_counter()-start}
        (out/'scene.json').write_text(json.dumps(data,indent=2,allow_nan=False),encoding='utf-8')
        return data
