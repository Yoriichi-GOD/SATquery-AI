"""Read-only, hash-linked local optical context and optional native-grid overlays."""
from pathlib import Path
import hashlib,io,re
import numpy as np
import rasterio
from rasterio.io import MemoryFile
from rasterio.features import rasterize
from rasterio.warp import transform_geom
from PIL import Image,ImageFilter
from .flood_bridge import BridgeError,MAX_FILE,parse_json


class VisualContext:
    def __init__(self,bridge,root=None):
        self.bridge=bridge;self.root=Path(root).resolve() if root else None

    def optical(self,run,role):
        p=run.get('provenance',{}).get('debris',{});day=p.get(role+'_date')
        expected=p.get('source_hashes',{}).get(day)
        if self.root is None or not isinstance(day,str) or not re.fullmatch(r'20\d\d-\d\d-\d\d',day) or not expected:
            raise BridgeError(404,'Verified local optical RGB is unavailable for this example')
        candidates=[self.root/'data/automatic'/run['id']/'optical'/day/'default.tif',self.root/'data/optical'/day/'default.tif']
        grid=self.bridge.grid(run['id'])
        for source in candidates:
            source=source.resolve()
            if not source.is_relative_to(self.root) or not source.is_file():continue
            if source.stat().st_size>MAX_FILE:raise BridgeError(413,'Optical context exceeds bounded preview limit')
            raw=source.read_bytes()
            if hashlib.sha256(raw).hexdigest()!=expected:continue
            try:
                with MemoryFile(raw) as memory,memory.open() as ds:
                    if (ds.count!=7 or ds.width*ds.height>1_000_000 or str(ds.crs)!=grid['crs'] or
                        ds.width!=grid['width'] or ds.height!=grid['height'] or list(ds.transform)!=grid['transform'] or
                        any(h*w*4>16*1024*1024 for h,w in ds.block_shapes)):
                        raise ValueError()
                    rgb=ds.read([3,2,1]);data=ds.read(7);valid=np.isfinite(rgb).all(0)&(data==1)
                    # Display only. No source mutation, independent band scaling or cloud removal.
                    rgba=np.full((ds.height,ds.width,4),110,dtype='uint8');rgba[:,:,3]=255
                    scaled=np.moveaxis(np.clip(rgb/0.3,0,1)*255,0,-1).astype('uint8')
                    rgba[valid,:3]=scaled[valid]
                return rgba,{'date':day,'source_sha256':expected,'grid':{**grid,'source_sha256':expected},'display':'RGB = B04/B03/B02; fixed reflectance 0–0.3 stretch; cloudy pixels retained; dataMask-invalid gray.'}
            except (ValueError,rasterio.errors.RasterioError):
                raise BridgeError(422,'Optical context grid or band contract failed; RGB withheld') from None
        raise BridgeError(404,'No retained optical source matches this run\'s frozen source hash')

    def catalogue(self,run_id):
        run=self.bridge.detail(run_id);base='/api/flood/runs/'+run_id+'/visual/'
        value={'run_id':run_id,'optical_available':False,'before':None,'after':None,'overlays':[],
               'limitations':['Optical dates differ from SAR; grid equality is not independent physical co-registration.',
                              'Mapped building footprints are historical OSM context, not detected debris or confirmed damage.',
                              'Candidate overlays mark positives only. Uncoloured RGB is not evidence of absence; inspect native masks for gray unknown coverage.',
                              'Water and debris support differ; turning overlays off changes display only, never measurements.'],
               'coverage':{'water_valid_pixels':run['summary'].get('valid_pixels'),'debris_valid_pixels':run['summary'].get('debris_valid_pixels')}}
        try:
            for role in ('pre','post'):
                rgba,meta=self.optical(run,role);value['before' if role=='pre' else 'after']={**meta,'url':base+('before' if role=='pre' else 'after')+'.png'}
            value['optical_available']=True;value['grid']=meta['grid']
        except BridgeError as error:
            if error.status!=404:raise
            value.update(before=None,after=None,reason=error.message)
        artifacts={a['name']:a['sha256'] for a in run['artifacts']}
        for kind,label,colour,name in [('water','Water-change candidates','cyan','prediction.tif'),('debris','Possible debris / surface-change candidates','copper','debris-candidates.tif'),('buildings','Mapped building outlines','violet','layers.geojson')]:
            if name in artifacts and (kind!='debris' or run.get('debris_available')):
                value['overlays'].append({'id':kind,'label':label,'colour':colour,'url':base+kind+'.png','source_hashes':{name:artifacts[name]},'semantics':'Mapped context / possible exposure, not damage or closure'})
        return value

    def preview(self,run_id,kind):
        if kind not in ('before','after','water','debris','buildings'):raise BridgeError(404,'Unknown visual layer')
        run=self.bridge.detail(run_id)
        if kind in ('before','after'):
            rgba,meta=self.optical(run,'pre' if kind=='before' else 'post');hashes={'optical.tif':meta['source_sha256']}
        elif kind in ('water','debris'):
            if kind=='debris' and not run['debris_available']:raise BridgeError(404,'Debris is NOT_ASSESSED')
            mask,grid,coverage,sha=self.bridge.mask(run_id,kind)
            rgba=np.zeros((*mask.shape,4),dtype='uint8')
            rgba[mask==(1 if kind=='debris' else 2)]=(191,116,74,210) if kind=='debris' else (40,210,230,210)
            hashes={('debris-candidates.tif' if kind=='debris' else 'prediction.tif'):sha}
        else:
            raw,sha=self.bridge.verified(run_id,'layers.geojson');payload=parse_json(raw)
            features=payload.get('features') if isinstance(payload,dict) else None
            if not isinstance(features,list) or len(features)>10000:raise BridgeError(422,'Invalid mapped feature collection')
            grid=self.bridge.grid(run_id);geometries=[]
            try:
                for f in features:
                    if f.get('properties',{}).get('kind')!='building':continue
                    g=f['geometry']
                    if g['type'] not in ('Polygon','MultiPolygon'):raise ValueError()
                    geometries.append((transform_geom('EPSG:4326',grid['crs'],g),1))
                from affine import Affine
                a=rasterize(geometries,out_shape=(grid['height'],grid['width']),transform=Affine(*grid['transform'][:6]),fill=0,dtype='uint8') if geometries else np.zeros((grid['height'],grid['width']),dtype='uint8')
                image=Image.fromarray(a*255);inner=np.asarray(image.filter(ImageFilter.MinFilter(3)))
                outline=(a>0)&(inner==0);rgba=np.zeros((*a.shape,4),dtype='uint8');rgba[outline]=(190,145,255,230)
                hashes={'layers.geojson':sha}
            except (ValueError,KeyError,TypeError,rasterio.errors.RasterioError):
                raise BridgeError(422,'Mapped building geometry invalid; overlay withheld') from None
        out=io.BytesIO();Image.fromarray(rgba).save(out,format='PNG');return out.getvalue(),hashes
