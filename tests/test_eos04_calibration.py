import unittest
import numpy as np
from paired_lab.eos04_calibration import beta0

class EOS04CalibrationTests(unittest.TestCase):
 def test_known_power_and_db(self):
  linear,db=beta0(np.array([10,20],dtype=np.uint16),20,0)
  np.testing.assert_allclose(linear,[1,4]);np.testing.assert_allclose(db,[0,6.020599913279624])
 def test_noise_bias_and_nonpositive_preserved(self):
  linear,db=beta0([1,2,3],0,4)
  np.testing.assert_array_equal(linear,[-3,0,5]);self.assertTrue(np.isnan(db[:2]).all())
  self.assertAlmostEqual(db[2],6.989700043360188)
 def test_no_uint16_square_overflow(self):
  linear,_=beta0(np.array([65535],dtype=np.uint16),0,0)
  self.assertEqual(linear[0],4294836225)
 def test_invalid_inputs_refused(self):
  for dn,k,n in [([np.nan],0,0),([-1],0,0),([1],np.nan,0),([1],0,-1)]:
   with self.assertRaises(ValueError):beta0(dn,k,n)
