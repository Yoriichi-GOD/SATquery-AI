"""Display artifacts derived from a completed NDVI export; never recalibrates NDVI."""
from pathlib import Path
import shutil
import numpy as np
import rasterio
from PIL import Image
from geo import bands


def create_stages(source, rgb_preview, output, threshold):
    output = Path(output)
    # Reuse the exact ingested RGB and analytical overlay, with no reprojection.
    shutil.copyfile(rgb_preview, output / 'rgb.png')
    with Image.open(rgb_preview) as rgb, Image.open(output / 'overlay.png') as overlay:
        Image.alpha_composite(rgb.convert('RGBA'), overlay.convert('RGBA')).save(output / 'evidence.png')
    with rasterio.open(source) as src:
        mapping = bands(src)
        channels = []
        for name in ['nir', 'red', 'green']:
            k = mapping[name]
            a = src.read(k, masked=True).astype('float32').filled(np.nan) * src.scales[k-1] + src.offsets[k-1]
            finite = np.isfinite(a)
            low, high = np.percentile(a[finite], [2, 98]) if finite.any() else (0, 1)
            channels.append(np.where(finite, np.clip((a-low)/max(float(high-low), 1e-6), 0, 1), 0))
        Image.fromarray((np.stack(channels, -1)*255).astype('uint8')).save(output / 'false-colour.png')
    with rasterio.open(output / 'ndvi.tif') as src:
        ndvi = src.read(1)
        valid = np.isfinite(ndvi)
        selected = valid & (ndvi >= threshold)
        # Binary values: white selected, black unselected; invalid pixels transparent.
        mask = np.zeros((*ndvi.shape, 4), dtype='uint8')
        mask[selected, :3] = 255
        mask[valid, 3] = 255
        Image.fromarray(mask).save(output / 'mask.png')
    return ['rgb', 'false-colour', 'evidence', 'mask']
