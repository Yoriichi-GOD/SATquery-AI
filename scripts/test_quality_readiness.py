import unittest
import numpy as np
from affine import Affine
from audit_quality_readiness import landmark_residuals,grid_error

class QualityTests(unittest.TestCase):
    def test_known_physical_shift(self):
        r=landmark_residuals([[0,0,3,4],[10,0,13,4],[0,10,3,14]])
        self.assertEqual(r["rmse_m"],5)
        self.assertEqual(r["mean_dx_m"],3)
    def test_missing_and_nonfinite_rejected(self):
        for p in ([],[[0,0,0,0]],[[0,0,0,0],[1,1,1,1],[2,2,np.nan,2]]):
            with self.assertRaises(ValueError):landmark_residuals(p)
    def test_identical_grid(self):
        a=Affine(10,0,100,0,-10,200)
        self.assertEqual(grid_error(a,a,512,512),0)
    def test_pixel_shift(self):
        a=Affine(10,0,100,0,-10,200)
        self.assertEqual(grid_error(a,a*Affine.translation(3,4),512,512),5)
    def test_tiny_roundoff(self):
        a=Affine(.0001,0,76,0,-.0001,19)
        self.assertLess(grid_error(a,Affine(.0001,0,76+1e-14,0,-.0001,19),512,512),1e-6)
if __name__=="__main__":unittest.main()
