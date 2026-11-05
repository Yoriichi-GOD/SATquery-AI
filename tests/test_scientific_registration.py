import importlib.util
import unittest
import numpy as np
from affine import Affine
from research.terrain_exposure.io import Grid
from research.registration.diagnostics import audit


@unittest.skipUnless(importlib.util.find_spec('cv2'),'Install research/requirements-scientific.txt')
class RegistrationTests(unittest.TestCase):
    def setUp(self):
        import cv2
        self.cv2=cv2
        rng=np.random.default_rng(42)
        self.a=cv2.GaussianBlur(rng.uniform(0,255,(256,256)).astype('float32'),(3,3),.7)
        self.grid=Grid(self.a.shape,Affine(10,0,300000,0,-10,3100000),'EPSG:32645')
        self.mask=np.ones_like(self.a,bool)
    def test_deliberate_shift_and_held_out_error(self):
        m=np.float32([[1,0,4],[0,1,-3]])
        b=self.cv2.warpAffine(self.a,m,(256,256))
        r=audit(self.a,b,self.mask,self.mask,self.grid,self.grid)
        self.assertEqual(r['status'],'MISALIGNED')
        np.testing.assert_allclose(r['estimated_translation_xy_px'],[4,-3],atol=.15)
        self.assertLess(r['post_fit_held_out_residual_median_px'],.15)
        self.assertFalse(r['corrected_raster_created'])
    def test_known_rotation_is_supported(self):
        m=self.cv2.getRotationMatrix2D((128,128),2,1)
        b=self.cv2.warpAffine(self.a,m,(256,256))
        r=audit(self.a,b,self.mask,self.mask,self.grid,self.grid)
        self.assertNotEqual(r['status'],'UNAVAILABLE')
        self.assertAlmostEqual(abs(r['estimated_rotation_deg']),2,delta=.1)
    def test_low_texture_nodata_clouds_and_cross_sensor(self):
        blank=np.ones_like(self.a)
        r=audit(blank,blank,self.mask,self.mask,self.grid,self.grid)
        self.assertEqual(r['reason'],'LOW_TEXTURE')
        r=audit(self.a,self.a,~self.mask,~self.mask,self.grid,self.grid)
        self.assertEqual(r['reason'],'INSUFFICIENT_VALID_SUPPORT')
        cloud=self.mask.copy();cloud[:200]=False
        r=audit(self.a,self.a,cloud,cloud,self.grid,self.grid)
        self.assertEqual(r['status'],'UNAVAILABLE')
        r=audit(self.a,self.a,self.mask,self.mask,self.grid,self.grid,modalities=('optical','SAR'))
        self.assertEqual(r['reason'],'CROSS_SENSOR_METHOD_NOT_AVAILABLE')
    def test_mismatched_resolution_is_not_silently_warped(self):
        other=Grid(self.a.shape,Affine(20,0,300000,0,-20,3100000),'EPSG:32645')
        r=audit(self.a,self.a,self.mask,self.mask,self.grid,other)
        self.assertEqual(r['status'],'UNAVAILABLE')
