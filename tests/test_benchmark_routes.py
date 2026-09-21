import unittest
from test_unified import controller,optical

class BenchmarkRouteRegressions(unittest.TestCase):
    def test_unavailable_physical_measurements(self):
        for q in ['Estimate water depth','Compare water and temperature','Identify water and soil moisture']:
            for records in [[optical()],[{**optical(),'reflectance_units':'surface_reflectance'}]*2]:
                with self.subTest(q=q),self.assertRaises(ValueError):controller.plan(q,records)
    def test_water_does_not_silently_drop_vegetation(self):
        pair=[{**optical(),'count':13},{'modality':'sar','count':2}]
        with self.assertRaises(ValueError):controller.plan('Map water and vegetation',pair)
        self.assertEqual(controller.plan('Map water',pair)['task'],'water_map')
    def test_classifier_does_not_locate(self):
        pair=[{**optical(),'count':10},{'modality':'sar','count':2}]
        with self.assertRaises(ValueError):controller.plan('Identify building locations',pair)
    def test_natural_road_comparison(self):
        self.assertEqual(controller.plan('Compare the roads between these images',[optical(),optical()])['task'],'temporal')
    def test_visual_counts_remain_estimates(self):
        self.assertEqual(controller.plan('How many cars are there?',[optical()])['task'],'vqa')

    def test_area_noun_presence_is_not_measurement(self):
        for q in ["Is there a grass area?", "Is a square water area present?"]:
            self.assertEqual(controller.plan(q,[optical()])["task"],"vqa")
        with self.assertRaises(ValueError):controller.plan("Measure the grass area in hectares",[optical()])
