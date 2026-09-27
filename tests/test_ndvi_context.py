import unittest
from routing import route

class NDVIContextTests(unittest.TestCase):
    def test_image_context_preserves_calibration_gate(self):
        for q in ['Compute NDVI for this raster.', 'Calculate NDVI on the image', 'NDVI in this crop']:
            with self.subTest(q=q):
                self.assertEqual(route(q,ndvi_supported=True)['tool'],'ndvi')
                self.assertEqual(route(q,ndvi_supported=False)['rule'],'calibrated_bands_required')
    def test_context_does_not_drop_compound_task_or_threshold(self):
        for q in ['Compute NDVI for this raster and predict rainfall', 'Compute NDVI for this raster and count buildings', 'Compute NDVI for both images']:
            self.assertEqual(route(q,ndvi_supported=True)['tool'],'refuse')
        self.assertEqual(route('Compute NDVI for this raster at threshold 0.7',ndvi_supported=True,threshold=.5)['rule'],'threshold_mismatch')
        self.assertEqual(route('Compute NDVI for this raster at threshold 0.7',ndvi_supported=True,threshold=.7)['tool'],'ndvi')
