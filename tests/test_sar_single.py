import unittest
import numpy as np
from test_unified import controller
import sar_single

def record():
    return dict(modality='sar',sensor='Sentinel-1',units='dB',shape=[120,120],bands=['VV','VH'],crs='EPSG:32632',transform=[10,0,500000,0,-10,5000000],data=np.full((2,120,120),-12.))
class SARSingleTests(unittest.TestCase):
    def test_scene_route(self):
        self.assertEqual(controller.plan('Describe this SAR image',[record()])['task'],'sar_scene')
    def test_wrong_sensor_units_and_grid(self):
        for key,value in [('sensor','EOS-04'),('units','DN'),('shape',[512,512]),('bands',['VH','VV']),('transform',[4.5,0,0,0,-4.5,0])]:
            r=record();r[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):sar_single.validate(r)
    def test_no_fake_vqa_grounding_or_measurements(self):
        for q in ['How many cars are there?','Outline water','Estimate water depth','What changed?','Describe this SAR image and predict floods']:
            with self.subTest(q=q),self.assertRaises(ValueError):controller.plan(q,[record()])
    def test_invalid_pixels(self):
        r=record();r['data'][0,0,0]=np.nan
        with self.assertRaises(ValueError):sar_single.validate(r)
