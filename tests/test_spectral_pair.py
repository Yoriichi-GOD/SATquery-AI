import unittest,tempfile
from pathlib import Path
import numpy as np,rasterio
from rasterio.transform import from_origin
from test_unified import controller
import spectral_pair
from inputs import inspect

def fixture(path,date,after=False,missing_green=False,cloud=False):
    # Four known cells: vegetation gain, water gain, stable vegetation, stable water.
    red=np.full((2,2),.2);nir=np.array([[.2,.2],[.8,.1]]);green=np.array([[.2,.1],[.2,.8]])
    if after:nir[0,0]=.8;green[0,1]=.8
    scl=np.full((2,2),4.)
    if cloud:scl[0,0]=9
    bands=[('red',red),('nir',nir),('scl',scl)]
    if not missing_green:bands.insert(1,('green',green))
    with rasterio.open(path,'w',driver='GTiff',width=2,height=2,count=len(bands),dtype='float64',crs='EPSG:32644',transform=from_origin(500000,2800000,10,10)) as ds:
        for i,(name,a) in enumerate(bands,1):ds.write(a,i);ds.set_band_description(i,name)
        ds.update_tags(sensor='Sentinel-2',reflectance_units='surface_reflectance',acquisition_date=date,source='SYNTHETIC arithmetic fixture, not satellite imagery')

class SpectralPairTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name);self.a=self.root/'a.tif';self.b=self.root/'b.tif';fixture(self.a,'2020-01-01');fixture(self.b,'2021-01-01',True)
    def records(self):return [inspect(self.a,'optical'),inspect(self.b,'optical')]
    def run_pair(self,tasks=['vegetation','water']):return spectral_pair.analyse(self.records(),tasks,.5,0,self.root)
    def test_scalar_truth_and_exports(self):
        r=self.run_pair();v=r['parameters']['vegetation'];w=r['parameters']['water']
        self.assertEqual((v['before_pixels'],v['after_pixels'],v['gain_pixels'],v['loss_pixels']),(1,2,1,0))
        self.assertEqual((w['before_pixels'],w['after_pixels'],w['gain_pixels'],w['loss_pixels']),(2,2,1,1))
        self.assertEqual(v['net_percentage_points'],25);self.assertEqual(v['net_grid_area_m2'],100)
        a=np.load(self.root/'comparison-arrays.npz');self.assertAlmostEqual(a['vegetation_delta'][0,0],.6)
        with rasterio.open(self.root/'vegetation-indices.tif') as ds:self.assertEqual(ds.count,3);np.testing.assert_allclose(ds.read(3),a['vegetation_delta'])
    def test_common_quality_denominator(self):
        fixture(self.b,'2021-01-01',True,cloud=True);r=self.run_pair();v=r['parameters']['vegetation'];self.assertEqual(v['valid_pixels'],3);self.assertEqual(v['net_pixels'],0)
    def test_partial_result_missing_green(self):
        fixture(self.b,'2021-01-01',True,missing_green=True);r=self.run_pair();self.assertEqual(r['parameters']['vegetation']['status'],'complete');self.assertEqual(r['parameters']['water']['status'],'unavailable')
    def test_dates_and_grids_refuse(self):
        with self.assertRaises(ValueError):spectral_pair.validate(list(reversed(self.records())))
        with rasterio.open(self.b,'r+') as ds:ds.transform=from_origin(500010,2800000,10,10)
        with self.assertRaisesRegex(ValueError,'exact CRS'):spectral_pair.validate(self.records())
    def test_calibration_quality_and_sensor_refuse(self):
        for tags in [{'reflectance_units':'DN'},{'sensor':'Landsat-8'}]:
            fixture(self.b,'2021-01-01',True)
            with rasterio.open(self.b,'r+') as ds:ds.update_tags(**tags)
            with self.subTest(tags=tags),self.assertRaises(ValueError):spectral_pair.validate(self.records())
        fixture(self.b,'2021-01-01',True)
        with rasterio.open(self.b,'r+') as ds:ds.set_band_description(4,'not_quality')
        with self.assertRaisesRegex(ValueError,'SCL'):spectral_pair.validate(self.records())
    def test_query_selected_parameters_and_no_forecast(self):
        records=self.records()
        self.assertEqual(controller.plan('Analyze these images',records)['parameters'],['vegetation','water'])
        self.assertEqual(controller.plan('Compare vegetation',records)['parameters'],['vegetation'])
        self.assertEqual(controller.plan('Compare water',records)['parameters'],['water'])
        with self.assertRaises(ValueError):controller.plan('Predict water tomorrow',records)
        with self.assertRaises(ValueError):controller.plan('Compare vegetation health',records)
