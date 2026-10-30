import hashlib
import tempfile
import unittest
from pathlib import Path

import numpy as np
from rasterio.io import MemoryFile
from rasterio.transform import from_origin

from jai_extension.flood_bridge import BridgeError
from jai_extension.geo_context import GeoContext,register_rasters,sample_bilinear


def tif(data,affine,crs='EPSG:32645',nodata=None):
    with MemoryFile() as m:
        with m.open(driver='GTiff',count=1,width=data.shape[1],height=data.shape[0],dtype=data.dtype,crs=crs,transform=affine,nodata=nodata) as ds:ds.write(data,1)
        return m.read()


class RegistrationTests(unittest.TestCase):
    def setUp(self):
        self.labels=np.zeros((6,6),dtype='uint8');self.labels[2:4,2:4]=2
        self.pred=tif(self.labels,from_origin(0,60,10,10),nodata=255)
        self.z=np.full((3,3),100,dtype='float32')
        self.dem=tif(self.z,from_origin(0,60,20,20),nodata=-9999)

    def test_known_native_to_coarse_cell(self):
        value=register_rasters(self.pred,self.dem)
        self.assertEqual(value['classes_on_mesh'][1][1],2)
        self.assertEqual(value['common_valid_dem_cells'],9)
        self.assertEqual(len(value['candidate_points']),4)
        self.assertEqual(value['candidate_points'][0],{'x_m':25.,'y_m':35.,'height_m':100.})
        self.assertTrue(all(c['roundtrip_error_m']<1e-6 for c in value['controls']))

    def test_fraction_preserves_patch_missed_by_nearest(self):
        self.labels[:]=0;self.labels[2,2]=2
        value=register_rasters(tif(self.labels,from_origin(0,60,10,10),nodata=255),self.dem)
        self.assertEqual(value['classes_on_mesh'][1][1],0)
        self.assertAlmostEqual(value['candidate_fraction_on_mesh'][1][1],.25)
        self.assertEqual(len(value['candidate_points']),1)

    def test_shifted_nonoverlapping_rasters_refused(self):
        pred=tif(self.labels,from_origin(10000,60,10,10),nodata=255)
        with self.assertRaises(BridgeError) as cm:register_rasters(pred,self.dem)
        self.assertEqual(cm.exception.status,422)

    def test_degree_terrain_grid_refused(self):
        with self.assertRaises(BridgeError):register_rasters(self.pred,tif(self.z,from_origin(0,60,.001,.001),crs='EPSG:4326'))

    def test_nodata_terrain_hides_overlay(self):
        self.z[1,1]=-9999
        value=register_rasters(self.pred,tif(self.z,from_origin(0,60,20,20),nodata=-9999))
        self.assertEqual(value['classes_on_mesh'][1][1],255)
        self.assertIsNone(value['candidate_fraction_on_mesh'][1][1])
        self.assertEqual(value['candidate_points'],[])

    def test_all_invalid_source_refused(self):
        with self.assertRaises(BridgeError):register_rasters(tif(np.full((6,6),255,dtype='uint8'),from_origin(0,60,10,10),nodata=255),self.dem)

    def test_unknown_class_refused(self):
        self.labels[0,0]=7
        with self.assertRaises(BridgeError):register_rasters(tif(self.labels,from_origin(0,60,10,10)),self.dem)

    def test_valid_zero_elevation_is_not_missing(self):
        value=register_rasters(self.pred,tif(np.zeros((3,3),dtype='float32'),from_origin(0,60,20,20),nodata=-9999))
        self.assertEqual(value['candidate_points'][0]['height_m'],0)

    def test_geographic_source_reprojects_using_its_crs(self):
        from rasterio.warp import transform_bounds
        from rasterio.transform import from_bounds
        bounds=transform_bounds('EPSG:32645','EPSG:4326',335000,3116000,335600,3116600)
        labels=np.full((6,6),2,dtype='uint8')
        pred=tif(labels,from_bounds(*bounds,6,6),crs='EPSG:4326',nodata=255)
        dem=tif(np.full((6,6),100,dtype='float32'),from_origin(335000,3116600,100,100),nodata=-9999)
        value=register_rasters(pred,dem)
        self.assertGreater(value['common_valid_dem_cells'],0)
        self.assertLess(max(c['roundtrip_error_m'] for c in value['controls']),.01)


class FakeStore:
    def __init__(self,root,raw):
        self.root=Path(root);(self.root/'analysis.tif').write_bytes(raw)
        self.value={'hashes':{'analysis.tif':hashlib.sha256(raw).hexdigest()},'provenance':{'nominal_source_resolution_m':90}}
    def scene(self,sid):return self.value
    def scene_root(self,sid):return self.root


class ProfileTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.affine=from_origin(0,60,10,10)
        self.z=np.tile(np.arange(6)*10.+100,(6,1)).astype('float32')
        self.make()
    def make(self):self.geo=GeoContext(None,FakeStore(self.tmp.name,tif(self.z,self.affine,nodata=-9999)))

    def test_linear_plane_distance_and_height(self):
        profile=self.geo.transect('fixture',[5,25],[55,25],6)
        self.assertEqual(profile['length_m'],50)
        np.testing.assert_allclose(profile['height_m'],np.arange(6)*10+100)

    def test_no_interpolation_across_nodata(self):
        self.z[:,2]=-9999;self.make()
        profile=self.geo.transect('fixture',[5,25],[55,25],11)
        self.assertIsNone(profile['height_m'][3]);self.assertIsNone(profile['height_m'][4])
        self.assertLess(profile['valid_samples'],profile['samples'])

    def test_out_of_bounds_and_equal_points_refused(self):
        for start,end in [([-1,25],[55,25]),([5,25],[5,25])]:
            with self.subTest(start=start),self.assertRaises(BridgeError):self.geo.transect('fixture',start,end)

    def test_nonfinite_and_excessive_samples_refused(self):
        with self.assertRaises(BridgeError):self.geo.transect('fixture',[float('nan'),25],[55,25])
        with self.assertRaises(BridgeError):self.geo.transect('fixture',[5,25],[55,25],10000)

    def test_sample_corner_and_negative_heights(self):
        z=np.tile(np.arange(6)-3.,(6,1));values=sample_bilinear(z,np.ones_like(z,bool),self.affine,[5,55],[55,5])
        np.testing.assert_allclose(values,[-3,2])
