import tempfile
import unittest
from pathlib import Path
import numpy as np
import rasterio
from rasterio.transform import from_origin
from PIL import Image
import geo
from stages import create_stages


class NDVIPrecisionTests(unittest.TestCase):
    def test_real_punjab_pixels_do_not_round_onto_threshold(self):
        # Source values at (82,151) and (282,92) in the saved Punjab crop.
        red = np.array([[0.0575999990105629, 0.06480000168085098, 1.]], dtype='float32')
        nir = np.array([[0.3263999819755554, 0.36719998717308044, 3.]], dtype='float32')
        ndvi, valid = geo.calculate(red, nir)
        self.assertEqual((ndvi >= .7).tolist(), [[False, False, False]])
        self.assertEqual(ndvi[0, 2], .5)
        self.assertTrue((ndvi >= .5)[0, 2])

    def test_boundary_export_and_stage_mask_match_selected_count(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / 'source.tif'
            values = np.array([[[0.0575999990105629, 1., 0.]], [[.2, .2, 0.]],
                               [[.1, .1, 0.]], [[0.3263999819755554, 3., 0.]],
                               [[4., 4., 9.]]], dtype='float32')
            with rasterio.open(source, 'w', driver='GTiff', width=3, height=1, count=5,
                               dtype='float32', crs='EPSG:32643', transform=from_origin(500000, 3000000, 10, 10)) as dst:
                dst.write(values)
                dst.descriptions = ('red', 'green', 'blue', 'nir', 'scl')
                dst.update_tags(reflectance_units='surface_reflectance')
            Image.new('RGB', (3, 1)).save(root / 'rgb.png')
            output = root / 'run'
            stats = geo.analyse(source, output, .7)
            create_stages(source, root / 'rgb.png', output, .7)
            self.assertEqual(stats['selected_pixels'], 0)
            self.assertEqual(stats['valid_pixels'], 2)
            with rasterio.open(output / 'ndvi.tif') as src:
                self.assertEqual(src.dtypes[0], 'float64')
                self.assertEqual(int((src.read(1) >= .7).sum()), 0)
            with Image.open(output / 'mask.png') as im:
                self.assertFalse(np.asarray(im)[:, :, 0].any())
