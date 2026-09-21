import unittest
from test_unified import controller,optical
from recovery import detail
class RequestBoundaryTests(unittest.TestCase):
    def test_forecasts_refused_for_all_input_modes(self):
        variants=[[optical()],[optical(),optical()],[{**optical(),'count':13},{'modality':'sar','count':2}]]
        for records in variants:
            for q in ['Where will flooding spread next?', 'Predict water extent tomorrow', 'Suggest evacuation zones', 'Forecast road changes next year']:
                with self.subTest(q=q,records=records),self.assertRaisesRegex(ValueError,'not implemented'):controller.plan(q,records)
    def test_scene_classifier_cannot_pretend_to_map(self):
        records=[{**optical(),'count':10},{'modality':'sar','count':2}]
        for q in ['Map water','Segment urban land','Water coverage percentage','Identify land cover and calculate NDVI']:
            with self.subTest(q=q),self.assertRaises(ValueError):controller.plan(q,records)
        self.assertEqual(controller.plan('Identify land-cover classes',records)['task'],'optical_sar')
    def test_water_cannot_answer_other_measurements(self):
        records=[{**optical(),'count':13},{'modality':'sar','count':2}]
        for q in ['Map water and roads','What is the water depth?', 'Measure water volume']:
            with self.subTest(q=q),self.assertRaises(ValueError):controller.plan(q,records)
        self.assertEqual(controller.plan('Map water',records)['task'],'water_map')
    def test_temporal_not_general_object_matching(self):
        for q in ['Which vehicle increased?', 'Which colour of car changed?', 'How much highway length increased?', 'Compare NDVI before and after']:
            with self.subTest(q=q),self.assertRaises(ValueError):controller.plan(q,[optical(),optical()])
        self.assertEqual(controller.plan('Show road changes',[optical(),optical()])['task'],'temporal')
    def test_recovery_does_not_claim_automatic_repair(self):
        for m,fragment in [('Missing CRS','outside SatQuery'),('Provide acquisition date','Do not invent dates'),('Missing bands','do not rename'),('NDVI requires calibrated Red/NIR bands','RGB-only')]:
            d=detail(m);self.assertFalse(d['analysis_started']);self.assertEqual(d['message'],m);self.assertIn(fragment,' '.join(d['next_steps']))

    def test_forecast_recovery_does_not_request_dates(self):
        d=detail('Forecasting and evacuation advice are not implemented. Ask about observed dates.')
        self.assertEqual(d['code'],'unsupported_task')
        self.assertNotIn('acquisition',' '.join(d['next_steps']))
