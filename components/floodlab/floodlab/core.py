"""Fail-closed contracts and a fixed, uncalibrated SAR-change baseline."""
from datetime import datetime
import hashlib
from pathlib import Path
import numpy as np
import rasterio
from pyproj import CRS


def utc(value):
    d=datetime.fromisoformat(value.replace('Z','+00:00'))
    if d.tzinfo is None: raise ValueError('Timestamp must include timezone')
    return d


def validate_manifest(m):
    event=utc(m['event_time'])
    if not utc(m['pre']['datetime']) < event < utc(m['post']['datetime']):
        raise ValueError('Require pre < event < post')
    if utc(m['osm_snapshot']) >= event: raise ValueError('OSM must precede event')
    for key in ('pre','post'):
        x=m[key]
        if x.get('role')!='observation' or x.get('source')!='Sentinel-1':
            raise ValueError('Only Sentinel-1 observations are accepted by this baseline')
        if x.get('units')!='dB' or x.get('bands')!=['VV','VH']:
            raise ValueError('Require calibrated dB VV/VH, not raw DN or linear power')
        if x.get('terrain_corrected') is not True: raise ValueError('Terrain correction required')
        if not x.get('scene_id') or not x.get('sha256'): raise ValueError('Source identity and hash required')
        if x.get('relative_orbit') is None or x.get('orbit_state') not in ('ascending','descending'):
            raise ValueError('Orbit metadata required')
    for key in ('relative_orbit','orbit_state'):
        if m['pre'][key]!=m['post'][key]: raise ValueError('SAR orbit mismatch')
    if m.get('infrastructure_role')!='historical_osm': raise ValueError('Historical OSM required')


def metric_crs(crs):
    c=CRS.from_user_input(crs)
    if not c.is_projected or any(a.unit_conversion_factor!=1 for a in c.axis_info[:2]):
        raise ValueError('Use a projected CRS with metre units')
    return c


def read_pair(m, root):
    arrays=[]; profiles=[]; masks=[]
    for key in ('pre','post'):
        path=Path(root)/m[key]['path']
        if hashlib.sha256(path.read_bytes()).hexdigest()!=m[key]['sha256']:
            raise ValueError('Input hash mismatch')
        with rasterio.open(path) as ds:
            if ds.count!=2: raise ValueError('Two SAR bands required')
            metric_crs(ds.crs)
            arrays.append(ds.read().astype('float32')); profiles.append(ds.profile)
            masks.append((ds.read_masks()>0).all(0))
    a,b=profiles
    if any(a[k]!=b[k] for k in ('crs','transform','width','height')):
        raise ValueError('Grid mismatch: explicit alignment required before inference')
    return arrays[0],arrays[1],masks[0]&masks[1],a


def sar_change(pre,post,valid,water_db=-17.,drop_db=3.):
    if pre.shape!=post.shape or pre.ndim!=3 or pre.shape[0]!=2 or valid.shape!=pre.shape[1:]:
        raise ValueError('Array shape mismatch')
    if not np.isfinite(water_db) or not np.isfinite(drop_db) or drop_db<=0: raise ValueError('Invalid threshold')
    valid=np.asarray(valid,dtype=bool)&np.isfinite(pre).all(0)&np.isfinite(post).all(0)
    # VV-only heuristic: VH is retained and validated, not used as a tuned feature.
    before=pre[0]<water_db; after=post[0]<water_db
    new=after&~before&((post[0]-pre[0])<=-drop_db)&valid
    persistent=before&after&valid
    out=np.zeros(valid.shape,dtype='uint8'); out[persistent]=1; out[new]=2; out[~valid]=255
    return out
