"""Grid registration and bounded profiles; no physical flood-depth inference."""
from __future__ import annotations

import hashlib
import math
from pathlib import Path

import numpy as np
import rasterio
from rasterio.io import MemoryFile
from rasterio.warp import reproject, Resampling, transform, transform_bounds

from jai_extension.flood_bridge import BridgeError


def read_dem(store, scene_id):
    scene = store.scene(scene_id)
    raw = (store.scene_root(scene_id) / 'analysis.tif').read_bytes()
    if hashlib.sha256(raw).hexdigest() != scene['hashes']['analysis.tif']:
        raise BridgeError(409, 'Terrain raster changed during access')
    return scene, raw


def checked_grid(ds, cap):
    if ds.count != 1 or not 3 <= ds.width or not 3 <= ds.height or ds.width*ds.height > cap or ds.crs is None:
        raise BridgeError(422, 'Invalid or excessive geospatial grid')
    if not all(math.isfinite(v) for v in ds.transform) or ds.transform.b or ds.transform.d or ds.transform.a <= 0 or ds.transform.e >= 0:
        raise BridgeError(422, 'A finite north-up geospatial grid is required')


def sample_bilinear(z, valid, affine, xs, ys):
    """Sample cell-centre coordinates, never bridging a missing neighbour."""
    xs, ys = np.asarray(xs, float), np.asarray(ys, float)
    cols = (xs-affine.c)/affine.a-.5
    rows = (ys-affine.f)/affine.e-.5
    c0, r0 = np.floor(cols).astype(int), np.floor(rows).astype(int)
    # Exact final-row/column centres have a valid inward neighbourhood.
    c0 = np.where(np.isclose(cols,z.shape[1]-1,rtol=0,atol=1e-8),z.shape[1]-2,c0)
    r0 = np.where(np.isclose(rows,z.shape[0]-1,rtol=0,atol=1e-8),z.shape[0]-2,r0)
    inside = (r0>=0)&(r0<z.shape[0]-1)&(c0>=0)&(c0<z.shape[1]-1)
    out = np.full(xs.shape,np.nan)
    positions = np.flatnonzero(inside)
    if positions.size:
        rr,cc=r0[positions],c0[positions]
        good=valid[rr,cc]&valid[rr,cc+1]&valid[rr+1,cc]&valid[rr+1,cc+1]
        positions=positions[good];rr,cc=r0[positions],c0[positions]
        fx,fy=cols[positions]-cc,rows[positions]-rr
        out[positions]=(z[rr,cc]*(1-fx)*(1-fy)+z[rr,cc+1]*fx*(1-fy)+z[rr+1,cc]*(1-fx)*fy+z[rr+1,cc+1]*fx*fy)
    return out


def register_rasters(prediction_raw, dem_raw, stride=1):
    if type(stride) is not int or stride<1 or stride>128:
        raise BridgeError(422,'Invalid display mesh stride')
    try:return _register_rasters(prediction_raw,dem_raw,stride)
    except (rasterio.errors.RasterioError,ValueError,TypeError):
        raise BridgeError(422,'Invalid geospatial raster; overlay withheld') from None


def _register_rasters(prediction_raw, dem_raw, stride):
    with MemoryFile(prediction_raw) as pm,pm.open() as source,MemoryFile(dem_raw) as dm,dm.open() as dem:
        checked_grid(source,1_000_000);checked_grid(dem,16384)
        if not dem.crs.is_projected or dem.crs.linear_units != 'metre':
            raise BridgeError(422,'Terrain analysis must use projected metres')
        labels=source.read(1)
        if not np.isin(labels,[0,1,2,255]).all():
            raise BridgeError(422,'Unknown prediction class; overlay refused')
        z=dem.read(1).astype(float);valid=np.isfinite(z)&(dem.read_masks(1)>0)
        bounds=transform_bounds(source.crs,dem.crs,*source.bounds,densify_pts=21)
        intersection=[max(bounds[0],dem.bounds.left),max(bounds[1],dem.bounds.bottom),min(bounds[2],dem.bounds.right),min(bounds[3],dem.bounds.top)]
        if intersection[0]>=intersection[2] or intersection[1]>=intersection[3]:
            raise BridgeError(422,'Selected flood and terrain do not overlap')
        aligned=np.full(z.shape,255,dtype='uint8')
        args=dict(src_transform=source.transform,src_crs=source.crs,dst_transform=dem.transform,dst_crs=dem.crs)
        reproject(labels,aligned,src_nodata=255,dst_nodata=255,resampling=Resampling.nearest,**args)
        shared=valid&(aligned!=255)
        if not shared.any():
            raise BridgeError(422,'No common valid terrain/flood cell centres')
        aligned[~shared]=255
        # This average is a fraction of valid observed source support, not a
        # categorical label, full-cell inundation fraction or depth estimate.
        indicator=np.where(labels==255,np.nan,(labels==2).astype(float)).astype('float32')
        fraction=np.full(z.shape,np.nan,dtype='float32')
        reproject(indicator,fraction,src_nodata=np.nan,dst_nodata=np.nan,resampling=Resampling.average,**args)
        fraction[~shared]=np.nan
        # Preserve small candidates as their original source cell centres, with
        # heights sampled from the DSM; no invented 10m elevation resolution.
        rr,cc=np.nonzero(labels==2);candidate_total=int(len(rr));step=max(1,math.ceil(candidate_total/5000))
        rr,cc=rr[::step],cc[::step]
        sx,sy=rasterio.transform.xy(source.transform,rr,cc)
        xx,yy=transform(source.crs,dem.crs,sx,sy) if len(rr) else ([],[])
        heights=sample_bilinear(z,valid,dem.transform,xx,yy) if len(rr) else np.array([])
        points=[{'x_m':float(x),'y_m':float(y),'height_m':float(h)} for x,y,h in zip(xx,yy,heights) if np.isfinite(h)]
        controls=[]
        rows,cols=np.nonzero(shared)
        for index in sorted(set([0,len(rows)//2,len(rows)-1])):
            r,c=int(rows[index]),int(cols[index]);x,y=dem.xy(r,c)
            sx,sy=transform(dem.crs,source.crs,[x],[y]);backx,backy=transform(source.crs,dem.crs,sx,sy)
            source_col,source_row=(~source.transform)*(sx[0],sy[0])
            err=math.hypot(backx[0]-x,backy[0]-y)
            controls.append({'dem_cell':[r,c],'dem_xy_m':[x,y],'source_pixel_fractional':[source_row-.5,source_col-.5],'roundtrip_error_m':err})
        if max(v['roundtrip_error_m'] for v in controls)>0.01:
            raise BridgeError(422,'Coordinate roundtrip check failed')
        nullable=lambda a:[[float(v) if np.isfinite(v) else None for v in row] for row in a[::stride,::stride]]
        return {'status':'GRID_REPROJECTED','physical_registration':'NOT_INDEPENDENTLY_VALIDATED',
                'source_crs':str(source.crs),'terrain_crs':str(dem.crs),
                'source_pixel_size':list(source.res),'terrain_pixel_size_m':list(dem.res),
                'common_valid_dem_cells':int(shared.sum()),'terrain_valid_cells':int(valid.sum()),
                'common_fraction_of_valid_dem':float(shared.sum()/valid.sum()),
                'nearest_candidate_dem_cells':int((aligned==2).sum()),'overlap_bounds_terrain_crs':intersection,
                'categorical_method':'nearest neighbour; 255 unknown; cell-centre support',
                'fraction_method':'area-weighted average of binary candidates over valid source support; partial-edge support may be smaller than a full terrain cell',
                'classes_on_mesh':aligned[::stride,::stride].tolist(),
                'candidate_fraction_on_mesh':nullable(fraction),
                'candidate_points':points,'native_candidate_pixels_full_run':candidate_total,
                'candidate_sampling_stride':step,'candidate_point_height_method':'bilinear DSM; all four neighbours valid',
                'controls':controls,'limitations':['Coordinate reprojection does not prove physical co-registration.',
                  'A coarse nearest-neighbour grid can omit small water patches; native-centre markers preserve sampled locations.',
                  'Markers follow the DSM surface; they do not estimate water surface height, inundation depth or damage.']}


class GeoContext:
    def __init__(self,bridge,terrain):self.bridge,self.terrain=bridge,terrain

    def coverage(self,run_id,scene_id,run=None):
        run=run or self.bridge.detail(run_id)
        if run['population']!='FROZEN_REAL_OBSERVATION':
            raise BridgeError(422,'Synthetic flood fixtures cannot be combined with real terrain')
        scene,dem_raw=read_dem(self.terrain,scene_id)
        prediction,digest=self.bridge.verified(run_id,'prediction.tif')
        expected=next((a['sha256'] for a in run.get('artifacts',[]) if a['name']=='prediction.tif'),None)
        if expected and digest!=expected:raise BridgeError(409,'Prediction snapshot changed during access')
        value=register_rasters(prediction,dem_raw,scene['mesh']['stride'])
        value.update(run_id=run_id,scene_id=scene_id,source_hashes={'prediction.tif':digest,**scene['hashes']},
                     observation_dates=[v.get('datetime') for v in run['provenance']['inputs']],
                     terrain_time_basis=scene['provenance']['release'],
                     temporal_use='Static historical DSM context; not a concurrent flood-date observation')
        return value

    def transect(self,scene_id,start,end,samples=128):
        if type(samples) is not int or not 2<=samples<=512:
            raise BridgeError(422,'Use 2 to 512 profile samples')
        try:
            if len(start)!=2 or len(end)!=2 or not all(type(v) in (int,float) and math.isfinite(v) for v in [*start,*end]):raise ValueError()
        except (TypeError,ValueError):raise BridgeError(422,'Use two finite projected metric points') from None
        scene,raw=read_dem(self.terrain,scene_id)
        with MemoryFile(raw) as memory,memory.open() as ds:
            checked_grid(ds,16384)
            if not ds.crs.is_projected or ds.crs.linear_units!='metre':raise BridgeError(422,'Metric terrain CRS required')
            z=ds.read(1).astype(float);valid=(ds.read_masks(1)>0)&np.isfinite(z)
            for x,y in (start,end):
                c,r=(~ds.transform)*(x,y)
                if not .5-1e-8<=c<=ds.width-.5+1e-8 or not .5-1e-8<=r<=ds.height-.5+1e-8:
                    raise BridgeError(422,'Profile points must be inside the terrain cell-centre domain')
            distance=math.dist(start,end)
            if distance<=0:raise BridgeError(422,'Choose distinct profile endpoints')
            t=np.linspace(0,1,samples);xs=start[0]+t*(end[0]-start[0]);ys=start[1]+t*(end[1]-start[1])
            heights=sample_bilinear(z,valid,ds.transform,xs,ys)
            if not np.isfinite(heights).any():raise BridgeError(422,'Profile has no complete valid interpolation neighbourhoods')
        return {'scene_id':scene_id,'crs':str(ds.crs),'start_m':list(start),'end_m':list(end),'length_m':distance,
                'distance_m':(t*distance).tolist(),'height_m':[float(h) if np.isfinite(h) else None for h in heights],
                'valid_samples':int(np.isfinite(heights).sum()),'samples':samples,'method':'bilinear; all four neighbours valid; gaps preserved',
                'source_sha256':scene['hashes']['analysis.tif'],'nominal_source_resolution_m':scene['provenance']['nominal_source_resolution_m'],
                'notice':'Sample spacing is display interpolation, not improved DEM resolution or surveyed ground elevation.'}
