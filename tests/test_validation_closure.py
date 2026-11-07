import tempfile,unittest
from pathlib import Path
import numpy as np
from shapely.geometry import Polygon,LineString,Point
from research.experiments.delhi_drainage import esri_geometry,coverage_near_gain
from research.cases.kedarnath_quality import strict_alignment
from research.experiments.worldfloods_component import central_window,spectral_predictions,confusion,ratios
from scripts.verify_validation_closure import band_index
from research.datasets.nepal_postevent import quality_mask

class ValidationClosureTests(unittest.TestCase):
    def test_two_metre_unknown_low_count_and_outside_roi_excluded(self):
        z=np.array([[200.,-9999,220.,240.,np.nan]])
        c=np.array([[2.,3,1,3,2]])
        inside=np.array([[True,True,True,False,True]])
        self.assertEqual(quality_mask(z,c,inside).tolist(),[[True,False,False,False,False]])
    def test_saved_band_names_control_order_not_sorted_json_keys(self):
        order=['MNDWI0','NDWI0','MNDWI0_slope15','all_land','all_water','valid']
        self.assertEqual(band_index(order,'MNDWI0_slope15',6),2)
        self.assertEqual(band_index(order,'NDWI0',6),1)
        with self.assertRaises(ValueError):band_index(order+['NDWI0'],'NDWI0',7)
    def test_external_test_window_is_fixed_not_label_selected(self):
        w=central_window((921,857));self.assertEqual(tuple(w.flatten()),(172,204,512,512))
        with self.assertRaises(ValueError):central_window((300,900))
    def test_all_water_terrain_ablation_on_common_support(self):
        data=np.array([[[10,10,0]],[[4,12,4]],[[4,4,4]]],dtype=float)
        predictions,valid=spectral_predictions(data,np.array([[5,20,5]]))
        self.assertEqual(valid.tolist(),[[True,True,False]])
        self.assertEqual(predictions['MNDWI0'].tolist(),[[True,True,False]])
        self.assertEqual(predictions['MNDWI0_slope15'].tolist(),[[True,False,False]])
        self.assertEqual(predictions['NDWI0'].tolist(),[[True,False,False]])
    def test_confusion_unknown_excluded_and_empty_positive_not_perfect(self):
        c=confusion(np.array([True,True,False,False]),np.array([True,False,True,False]),np.array([True,True,True,False]))
        self.assertEqual(c,{'tp':1,'fp':1,'fn':1,'tn':0});self.assertAlmostEqual(ratios(c)['iou'],1/3)
        self.assertIsNone(ratios({'tp':0,'fp':0,'fn':0,'tn':10})['iou'])
    def test_multipart_drain_and_polygon_hole_preserved(self):
        g=esri_geometry({'paths':[[[0,0],[3,4]],[[0,0],[0,5]]]},'esriGeometryPolyline')
        self.assertAlmostEqual(g.length,10)
        # Clockwise shell and counterclockwise hole under nativeArcGIS convention.
        p=esri_geometry({'rings':[[[0,0],[0,10],[10,10],[10,0],[0,0]],[[2,2],[4,2],[4,4],[2,4],[2,2]]]},'esriGeometryPolygon')
        self.assertAlmostEqual(p.area,96);self.assertFalse(p.covers(Point(3,3)))
    def test_exact_drain_buffer_area_and_no_reference_unknown(self):
        gain=Polygon([(0,0),(100,0),(100,100),(0,100)])
        drain=LineString([(0,-100),(0,200)])
        r=coverage_near_gain(gain,drain,[10,20])
        self.assertAlmostEqual(r['10']['area_ha'],.1);self.assertAlmostEqual(r['20']['fraction'],.2)
        self.assertIsNone(coverage_near_gain(gain,LineString(),[10])['10']['fraction'])
    def test_postfit_success_does_not_pass_uncorrected_alignment(self):
        r=strict_alignment({'status':'PARTIALLY_VERIFIED','held_out_matches':20,
            'post_fit_held_out_residual_p95_px':.1,'pre_correction_displacement_p95_px':4})
        self.assertEqual(r['status'],'MISALIGNED_UNCORRECTED')
    def test_missing_control_and_unknown_cannot_pass(self):
        self.assertEqual(strict_alignment({'status':'UNAVAILABLE','reason':'NO_TIES'})['status'],'UNAVAILABLE')
        self.assertEqual(strict_alignment({'status':'PARTIALLY_VERIFIED','held_out_matches':3})['status'],'UNAVAILABLE')
    def test_only_relative_alignment_claim_with_sufficient_support(self):
        r=strict_alignment({'status':'PARTIALLY_VERIFIED','held_out_matches':8,'pre_correction_displacement_p95_px':.9})
        self.assertEqual(r['status'],'RELATIVE_VISIBLE_FEATURE_ALIGNMENT_ONLY')
        self.assertEqual(r['absolute_geolocation'],'NOT_VALIDATED')

if __name__=='__main__':unittest.main()
