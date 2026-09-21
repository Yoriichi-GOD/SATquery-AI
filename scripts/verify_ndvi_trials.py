"""Live HTTP NDVI vs an independent TIFF decoder and scalar float64 calculation."""
import hashlib
import json
import math
from pathlib import Path
import time
import requests
import tifffile
import numpy as np
from PIL import Image
import io

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'results/reliability-20260907'
BASE = 'http://127.0.0.1:8765'
cases = [(p.parent.name, p.parent / f'{p.parent.name}.tif') for p in sorted((OUT / 'scenes').glob('*/manifest.json'))]
cases.insert(0, ('dehradun', Path('/root/satquery/scenes/dehradun-sentinel2-20211125.tif')))
results = []
for name, source in cases:
    with tifffile.TiffFile(source) as tiff:
        data = tiff.asarray()
        if data.shape[0] == 5:
            data = np.moveaxis(data, 0, -1)
        dx, dy, _ = tiff.pages[0].tags['ModelPixelScaleTag'].value
        keys = tiff.pages[0].tags['GeoKeyDirectoryTag'].value
        geo_keys = {keys[i]: keys[i+3] for i in range(4, len(keys), 4)}
        assert geo_keys[3076] == 9001 and 32601 <= geo_keys[3072] <= 32660
    values = np.full(data.shape[:2], np.nan, dtype='float64')
    valid = np.zeros(data.shape[:2], dtype=bool)
    exclusions = dict(nodata_or_nonfinite=0, negative_reflectance=0, zero_denominator=0,
                      quality_after_reflectance_checks=0)
    for y in range(data.shape[0]):
        for x in range(data.shape[1]):
            red, _, _, nir, scl = map(float, data[y, x])
            if not (math.isfinite(red) and math.isfinite(nir)):
                exclusions['nodata_or_nonfinite'] += 1
            elif red < 0 or nir < 0:
                exclusions['negative_reflectance'] += 1
            elif red + nir <= 1e-8:
                exclusions['zero_denominator'] += 1
            elif scl not in (4, 5, 6, 7):
                exclusions['quality_after_reflectance_checks'] += 1
            else:
                valid[y, x] = True
                values[y, x] = (nir-red)/(nir+red)
    count = int(valid.sum())
    response = requests.post(BASE + '/api/images', files={'file': (source.name, source.read_bytes(), 'image/tiff')}, timeout=60)
    response.raise_for_status()
    upload = response.json()
    calibration = None
    if name != 'dehradun':
        manifest = json.loads((source.parent / 'manifest.json').read_text())
        raw = np.load(source.parent / 'source-dn.npz')
        errors = {}
        for index, band in enumerate(('red', 'green', 'blue', 'nir')):
            m = manifest['bands'][band]
            expected = raw[band].astype('float64') * m['scale'] + m['offset']
            errors[band] = float(np.nanmax(np.abs(expected - data[:, :, index])))
        calibration = dict(source_dn_to_reflectance_max_abs_error=errors,
                           checked='COG header/STAC matched before conversion; independent float64 DN conversion vs saved TIFF',
                           passed=all(value < 2e-7 for value in errors.values()))
    for threshold in (.3, .5, .7):
        response = requests.post(BASE + '/api/analyze', data=dict(image_id=upload['id'],
            question='Calculate NDVI coverage at the selected threshold.', threshold=threshold), timeout=30)
        response.raise_for_status()
        rid = response.json()['id']
        deadline = time.monotonic() + 120
        while True:
            response = requests.get(BASE + f'/api/runs/{rid}', timeout=30)
            response.raise_for_status()
            run = response.json()
            if run['state'] in ('complete', 'error'):
                break
            if time.monotonic() > deadline:
                raise TimeoutError(rid)
            time.sleep(.2)
        (OUT / f'{name}-{threshold:.1f}-live.json').write_text(json.dumps(run, indent=2), encoding='utf-8')
        if not count:
            results.append(dict(scene=name, threshold=threshold, no_valid_pixels=True,
                                passed=run['state']=='error', run_id=rid))
            continue
        if run['state'] != 'complete':
            raise RuntimeError(run)
        expected_mask = valid & (values >= threshold)
        selected = int(expected_mask.sum())
        stats = run['statistics']
        downloads = {}
        for artifact in ('overlay', 'ndvi', 'rgb', 'false-colour', 'evidence', 'mask'):
            response = requests.get(BASE + f'/api/runs/{rid}/{artifact}', timeout=30)
            response.raise_for_status()
            downloads[artifact] = response.content
        ndvi = tifffile.imread(io.BytesIO(downloads['ndvi']))
        overlay = np.asarray(Image.open(io.BytesIO(downloads['overlay'])))[:, :, 3] > 0
        mask_image = np.asarray(Image.open(io.BytesIO(downloads['mask'])))
        stage_mask = mask_image[:, :, :3].max(axis=2) > 0 if mask_image.ndim==3 else mask_image > 0
        mismatch = expected_mask != overlay
        row = dict(scene=name, source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                   threshold=threshold, run_id=rid, total_pixels=int(valid.size), valid_pixels=count,
                   excluded_pixels=int(valid.size-count), exclusion_counts=exclusions,
                   selected_pixels=selected, app_selected_pixels=stats['selected_pixels'],
                   percent_of_valid=100*selected/count, selected_hectares=selected*dx*dy/10000,
                   mask_disagreement_pixels=int(mismatch.sum()),
                   mismatch_max_threshold_distance=float(np.max(np.abs(values[mismatch]-threshold))) if mismatch.any() else 0,
                   stage_mask_disagreements=int((overlay!=stage_mask).sum()),
                   exported_valid_mask_disagreements=int((np.isfinite(ndvi)!=valid).sum()),
                   max_ndvi_absolute_difference=float(np.nanmax(np.abs(values-ndvi))),
                   calibration=calibration,
                   stats_valid_match=stats['valid_pixels']==count,
                   exclusions_match=stats['exclusion_counts']==exclusions,
                   selected_match=stats['selected_pixels']==selected,
                   area_match=math.isclose(stats['selected_area_m2'], selected*dx*dy, abs_tol=1e-6),
                   percentage_match=math.isclose(stats['selected_percent_of_valid'], 100*selected/count, abs_tol=1e-9),
                   artifacts_downloaded=list(downloads),
                   app_stats=stats)
        row['passed'] = all(row[key] for key in ('stats_valid_match', 'exclusions_match', 'selected_match', 'area_match', 'percentage_match')) and not row['mask_disagreement_pixels'] and not row['stage_mask_disagreements'] and not row['exported_valid_mask_disagreements'] and row['max_ndvi_absolute_difference'] < 3e-7 and (calibration is None or calibration['passed'])
        results.append(row)
        print(name, threshold, 'valid', count, 'selected', selected, 'app', stats['selected_pixels'], 'passed', row['passed'], flush=True)
        (OUT / 'ndvi-independent-summary.json').write_text(json.dumps(dict(
            method='Independent tifffile decoder, scalar Python float64 arithmetic, TIFF pixel-scale and CRS tags; no geo/rasterio analytical imports. Live HTTP upload, routing, statistics and all six artifacts.',
            limitation='Numerical and pipeline verification; not independent field validation of land cover or cloud-mask accuracy.',
            cases=results, passed=sum(r['passed'] for r in results), total=len(results)), indent=2), encoding='utf-8')
