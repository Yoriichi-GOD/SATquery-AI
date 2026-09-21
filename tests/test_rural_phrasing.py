import unittest
from routing import route
class RuralPhrasingTests(unittest.TestCase):
 def test_variants(self):
  for q in ['is this a rural/urban area ?', 'Is this image rural or urban?', 'Is this area rural or urban?', 'Is this rural or urban?', 'Classify this image as rural or urban', 'rural/urban?']:
   with self.subTest(q=q):
    result=route(q);self.assertEqual(result['rule'],'rural_urban_classification');self.assertEqual(result['canonical_question'],'Is this image rural or urban?')
 def test_no_measurement_or_temporal_bypass(self):
  for q in ['Is this a rural/urban area and measure it?', 'Is this area rural or urban compared to last year?', 'Calculate rural/urban area']:
   self.assertEqual(route(q)['tool'],'refuse')
