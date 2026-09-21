"""Raster integration tests for the existing WSL scientific Python environment."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
import numpy as np
import rasterio
from PIL import Image
import geo
from stages import create_stages


class StageTests(unittest.TestCase):
    def test_corrected_sample_preserved_and_views_aligned(self):
        source = Path('ppt_handoff/exports/source-calibrated.tif')
        original = source.read_bytes()
        self.assertEqual(hashlib.sha256(original).hexdigest(), '55f3ca7b578e045594f8d54419b590c3ffeb99247ec5f74d7b1355d5bc4ec0f8')
        with tempfile.TemporaryDirectory(dir='.') as tmp:
            root = Path(tmp)
            preview, meta = geo.ingest(original, root/'source.tif')
            preview.save(root/'preview.png')
            output = root/'run'
            stats = geo.analyse(root/'source.tif', output, .5)
            before = (output/'ndvi.tif').read_bytes()
            overlay = (output/'overlay.png').read_bytes()
            names = create_stages(root/'source.tif', root/'preview.png', output, .5)
            self.assertEqual(names, ['rgb', 'false-colour', 'evidence', 'mask'])
            self.assertEqual((output/'ndvi.tif').read_bytes(), before)
            self.assertEqual((output/'overlay.png').read_bytes(), overlay)
            expected = json.loads(Path('results/ndvi-integration.json').read_text())['statistics']
            for key in ['selected_pixels', 'valid_pixels', 'total_pixels', 'selected_area_m2']:
                self.assertEqual(stats[key], expected[key])
            with Image.open(output/'mask.png') as im:
                mask = np.array(im)
            with Image.open(output/'overlay.png') as im:
                analytical = np.array(im)
            np.testing.assert_array_equal(mask[:, :, 0] == 255, analytical[:, :, 3] > 0)
            self.assertEqual(int((mask[:, :, 0] == 255).sum()), 38761)
            for name in ['rgb', 'false-colour', 'evidence', 'mask']:
                with Image.open(output/f'{name}.png') as im:
                    self.assertEqual(im.size, preview.size)
            # A second threshold must produce a different mask, never a static sample.
            other = root/'other'
            geo.analyse(root/'source.tif', other, .7)
            create_stages(root/'source.tif', root/'preview.png', other, .7)
            self.assertNotEqual((output/'mask.png').read_bytes(), (other/'mask.png').read_bytes())
        self.assertEqual(source.read_bytes(), original)
