import unittest
from test_unified import controller,optical
from routing import route

class PromptRegressionTests(unittest.TestCase):
    def test_scene_area_is_not_measurement(self):
        for q in ['Describe this area.','Please describe the area briefly.','What is visible in this area?','What do you see in the area?']:
            with self.subTest(q=q):self.assertEqual(route(q)['tool'],'vqa')
    def test_spatial_description_not_detector(self):
        for q in ['Where are the buildings in this image?','Where is the river located in the scene?']:
            with self.subTest(q=q):self.assertEqual(controller.plan(q,[optical()])['task'],'vqa')
    def test_measurement_and_compound_controls(self):
        for q in ['Measure this area in hectares','Describe this area and calculate its size','Where are buildings and measure their area','Where are buildings in this image and count them']:
            with self.subTest(q=q),self.assertRaises(ValueError):controller.plan(q,[optical()])
    def test_explicit_grounding_preserved(self):
        self.assertEqual(controller.plan('Outline buildings',[optical()])['task'],'grounding')
    def test_broad_rgb_comparison_explains_choices(self):
        with self.assertRaisesRegex(ValueError,'Choose what to compare'):controller.plan('Compare these images',[optical(),optical()])
