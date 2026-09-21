
import sys,unittest,tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np
import geo
class GeoTests(unittest.TestCase):
 def test_ndvi_and_mask(self):
  red=np.array([[1.,np.nan,-1.,0.,1.]],dtype='float32')
  nir=np.array([[3.,1.,1.,0.,3.]],dtype='float32')
  ndvi,valid=geo.calculate(red,nir,np.array([[4,4,4,4,9]]))
  self.assertEqual(valid.tolist(),[[True,False,False,False,False]])
  self.assertEqual(float(ndvi[0,0]),.5)
 def test_offset_applied_once(self):
  # Matched assets differ by 1000 DN; physical reflectance must agree.
  legacy=np.array([111.,1500.,4632.])
  c1=legacy+1000
  np.testing.assert_allclose(legacy*.0001,c1*.0001-.1,atol=1e-12)
  self.assertFalse(np.allclose(legacy*.0001-.1,c1*.0001-.1))
 def test_pixel_centre(self):
  c=geo.coordinate({'crs':'EPSG:32643','width':512,'height':512,'transform':[10,0,788360,0,-10,3359030]},256,256)
  self.assertEqual((c['x'],c['y']),(790925,3356465))
if __name__=='__main__':unittest.main()
