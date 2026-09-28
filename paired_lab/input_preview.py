"""Display-only preview; original values are never modified or deemed valid."""
import io
import numpy as np
from PIL import Image
from rasterio.io import MemoryFile
from rasterio.enums import Resampling

def render(raw, modality='optical'):
    if modality not in ('optical','sar'):raise ValueError('Declare optical or SAR.')
    with MemoryFile(raw) as mem, mem.open() as ds:
        if ds.count < 1:raise ValueError('No raster bands.')
        bands=[(x or '').lower() for x in ds.descriptions]
        indexes=None
        for names in [('red','green','blue'),('b04','b03','b02')]:
            if all(n in bands for n in names):indexes=[bands.index(n)+1 for n in names];break
        if modality=='sar':indexes=[1];label='SAR band 1 display; not true colour'
        elif indexes:label='Labelled RGB display'
        elif ds.count==3:indexes=[1,2,3];label='First three bands display; colour order unverified'
        else:indexes=[1];label='Band 1 grayscale display; RGB bands unavailable'
        scale=min(1,900/max(ds.width,ds.height));h=max(1,round(ds.height*scale));w=max(1,round(ds.width*scale))
        data=ds.read(indexes,out_shape=(len(indexes),h,w),masked=True,resampling=Resampling.nearest).astype('float32')
    channels=[]
    for band in data:
        valid=~np.ma.getmaskarray(band)&np.isfinite(band.data)
        canvas=np.zeros((h,w),dtype='uint8')
        if valid.any():
            lo,hi=np.percentile(band.data[valid],[2,98])
            if hi>lo:canvas[valid]=(255*np.clip((band.data[valid]-lo)/(hi-lo),0,1)).astype('uint8')
        channels.append(canvas)
    pixels=np.stack(channels,-1) if len(channels)==3 else channels[0]
    output=io.BytesIO();Image.fromarray(pixels).save(output,format='PNG')
    return output.getvalue(),label+'; per-band 2-98 percentile stretch; invalid pixels black; no analysis'
