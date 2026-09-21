"""Small real Sentinel-2 C1 crops with preserved DN and calibration provenance."""
import hashlib
import json
from pathlib import Path
import sys
import requests
import numpy as np
import rasterio
from rasterio.windows import Window
from rasterio.vrt import WarpedVRT
from rasterio.enums import Resampling
from pyproj import Transformer

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import geo

OUT = ROOT / 'results/reliability-20260907'
SCENES = OUT / 'scenes'
SCENES.mkdir(parents=True, exist_ok=True)
BANDS = ['red', 'green', 'blue', 'nir', 'scl']
# Fixed locations and selection rules, chosen before calculating NDVI.
SPECS = [
    ('punjab-farmland', 75.65, 30.90, '2024-10-01T00:00:00Z/2024-11-30T23:59:59Z', 10),
    ('bengaluru-lake-city', 77.67, 12.94, '2024-01-01T00:00:00Z/2024-03-31T23:59:59Z', 10),
    ('jaisalmer-arid', 70.90, 26.92, '2024-10-01T00:00:00Z/2024-11-30T23:59:59Z', 10),
    ('sundarbans-coast', 88.85, 21.95, '2024-01-01T00:00:00Z/2024-03-31T23:59:59Z', 10),
    ('assam-monsoon', 91.73, 26.16, '2024-07-01T00:00:00Z/2024-08-31T23:59:59Z', 90),
]

for name, lon, lat, dates, max_cloud in SPECS:
    folder = SCENES / name
    folder.mkdir(exist_ok=True)
    if (folder / 'manifest.json').exists():
        print('Already fetched', name, flush=True)
        continue
    request = dict(collections=['sentinel-2-c1-l2a'],
                   intersects=dict(type='Point', coordinates=[lon, lat]), datetime=dates,
                   query={'eo:cloud_cover': {'lt': max_cloud}}, limit=10,
                   sortby=[{'field': 'properties.eo:cloud_cover', 'direction': 'asc'}])
    response = requests.post('https://earth-search.aws.element84.com/v1/search', json=request, timeout=60)
    response.raise_for_status()
    items = response.json()['features']
    if not items:
        raise RuntimeError(f'No scene for {name}')
    item = items[0]
    (folder / 'source-item.json').write_text(json.dumps(item, indent=2), encoding='utf-8')
    arrays, dn_arrays, meta_bands = [], [], {}
    with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN='EMPTY_DIR',
                      CPL_VSIL_CURL_ALLOWED_EXTENSIONS='.tif', GDAL_HTTP_TIMEOUT='45',
                      GDAL_HTTP_MAX_RETRY='2'):
        for band in BANDS:
            asset = item['assets'][band]
            with rasterio.open(asset['href']) as src:
                if band == 'red':
                    x, y = Transformer.from_crs(4326, src.crs, always_xy=True).transform(lon, lat)
                    row, col = src.index(x, y)
                    window = Window(col - 256, row - 256, 512, 512)
                    assert 0 <= window.col_off <= src.width - 512 and 0 <= window.row_off <= src.height - 512
                    transform, crs = src.window_transform(window), src.crs
                with WarpedVRT(src, crs=crs, transform=transform, width=512, height=512,
                               resampling=Resampling.nearest) as vrt:
                    raw = vrt.read(1, masked=True).astype('float32').filled(np.nan)
                metadata = asset['raster:bands'][0]
                scale, offset = metadata.get('scale', 1), metadata.get('offset', 0)
                if not np.isclose(src.scales[0], scale) or not np.isclose(src.offsets[0], offset):
                    raise ValueError(f'COG/STAC calibration conflict: {name}/{band}')
                dn_arrays.append(raw)
                arrays.append(raw * scale + offset if band != 'scl' else raw)
                meta_bands[band] = dict(source=asset['href'], scale=scale, offset=offset,
                                       source_resolution=list(src.res), source_nodata=src.nodata,
                                       resampling='nearest to red-band 10 m grid')
            print(name, band, flush=True)
    target = folder / f'{name}.tif'
    attribution = 'Contains modified Copernicus Sentinel data (2024), accessed through Element 84 Earth Search / AWS.'
    with rasterio.open(target, 'w', driver='GTiff', width=512, height=512, count=5,
                       dtype='float32', crs=crs, transform=transform, nodata=np.nan, compress='deflate') as dst:
        dst.write(np.stack(arrays))
        dst.descriptions = tuple(BANDS)
        dst.update_tags(acquired=item['properties']['datetime'], source_item=item['id'],
                        reflectance_units='surface_reflectance', calibration_version='c1-header-verified-v2',
                        attribution=attribution,
                        processing='COG header and STAC calibration matched; applied once; SCL nearest 20 m to 10 m.')
    np.savez_compressed(folder / 'source-dn.npz', **dict(zip(BANDS, dn_arrays)))
    preview, metadata = geo.ingest(target.read_bytes(), folder / 'ingested.tif')
    preview.save(folder / 'rgb.png')
    manifest = dict(name=name, file=str(target), source_item=item['id'], acquired=item['properties']['datetime'],
                    scene_cloud_percent=item['properties']['eo:cloud_cover'], selection=request,
                    centre_lon_lat=[lon, lat], crs=str(crs), transform=list(transform)[:6],
                    sha256=hashlib.sha256(target.read_bytes()).hexdigest(), bands=meta_bands,
                    attribution=attribution, metadata=metadata)
    (folder / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    print('Saved', name, manifest['sha256'], flush=True)
