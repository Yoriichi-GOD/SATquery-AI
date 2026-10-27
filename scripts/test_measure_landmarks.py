import copy,unittest
from measure_landmarks import measure
def fixture():
    return dict(coordinate_unit='metre',projected_crs='EPSG:32648',reviewer='synthetic test',used_to_fit_warp=False,
      points=[dict(id=str(i),optical_xy=[i*100,0],sar_xy=[i*100+3,4],localization_uncertainty_m=1,stable_ground_feature=True,description='synthetic') for i in range(6)])
class Tests(unittest.TestCase):
    def test_known_shift(self):
        r=measure(fixture());self.assertEqual(r['rmse_m'],5);self.assertEqual(r['median_m'],5);self.assertEqual(r['p95_m'],5);self.assertEqual(r['conservative_rmse_with_uncertainty_m'],6)
    def test_incomplete(self):
        d=fixture();d['points']=d['points'][:5]
        with self.assertRaises(ValueError):measure(d)
    def test_nonfinite(self):
        d=fixture();d['points'][0]['sar_xy'][0]=float('nan')
        with self.assertRaises(ValueError):measure(d)
    def test_fitted_points(self):
        d=fixture();d['used_to_fit_warp']=True
        with self.assertRaises(ValueError):measure(d)
    def test_units(self):
        d=fixture();d['coordinate_unit']='degrees'
        with self.assertRaises(ValueError):measure(d)
    def test_duplicate_location(self):
        d=fixture();d['points'][1]['optical_xy']=d['points'][0]['optical_xy']
        with self.assertRaises(ValueError):measure(d)
if __name__=='__main__':unittest.main()
