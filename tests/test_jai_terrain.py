import unittest
import tempfile,json,hashlib
from pathlib import Path
import numpy as np
from rasterio.transform import from_origin

from jai_extension.terrain import slope_degrees,grid_summary,TerrainStore
from jai_extension.flood_bridge import BridgeError


class TerrainTests(unittest.TestCase):
    def setUp(self):
        self.valid=np.ones((7,7),bool)
        self.transform=from_origin(500000,3000000,10,10)

    def test_flat_100m_plane(self):
        s=slope_degrees(np.full((7,7),100.),self.valid,10,10)
        np.testing.assert_allclose(s[1:-1,1:-1],0)
        self.assertTrue(np.isnan(s[0]).all())

    def test_45_degree_east_plane(self):
        z=np.tile(np.arange(7)*10.+100,(7,1))
        s=slope_degrees(z,self.valid,10,10)
        np.testing.assert_allclose(s[1:-1,1:-1],45)

    def test_north_and_diagonal_gradient(self):
        yy,xx=np.mgrid[:7,:7]
        s=slope_degrees((xx+yy)*10.,self.valid,10,10)
        np.testing.assert_allclose(s[1:-1,1:-1],np.degrees(np.arctan(np.sqrt(2))))

    def test_nodata_invalidates_entire_horn_neighbourhood(self):
        self.valid[2,2]=False
        s=slope_degrees(np.zeros((7,7)),self.valid,10,10)
        self.assertTrue(np.isnan(s[1:4,1:4]).all())
        self.assertEqual(s[4,4],0)

    def test_zero_and_negative_heights_remain_valid(self):
        z=np.tile(np.arange(7)-3.,(7,1))
        stats,mesh=grid_summary(z,self.valid,self.transform,'EPSG:32645')
        self.assertEqual(stats['valid_cells'],49)
        self.assertEqual(stats['elevation_min_m'],-3)
        self.assertEqual(mesh['z_m'][3][3],0)

    def test_degrees_are_rejected_before_gradient(self):
        with self.assertRaises(ValueError):grid_summary(np.zeros((7,7)),self.valid,self.transform,'EPSG:4326')

    def test_empty_region_rejected(self):
        with self.assertRaises(ValueError):grid_summary(np.zeros((7,7)),~self.valid,self.transform,'EPSG:32645')

    def test_cell_centres_and_coverage_area(self):
        stats,mesh=grid_summary(np.zeros((7,7)),self.valid,self.transform,'EPSG:32645')
        self.assertEqual(mesh['x_m'][0],500005)
        self.assertEqual(mesh['y_m'][0],2999995)
        self.assertEqual(stats['valid_area_m2'],4900)

    def test_mesh_cap_and_separate_source_extrema(self):
        z=np.zeros((300,300));z[1,1]=999
        stats,mesh=grid_summary(z,np.ones_like(z,bool),self.transform,'EPSG:32645')
        self.assertLessEqual(max(mesh['display_shape']),128)
        self.assertEqual(stats['elevation_max_m'],999)
        self.assertIn('not extrema preserving',mesh['sampling'])

    def test_invalid_spacing_and_rotated_transform(self):
        with self.assertRaises(ValueError):slope_degrees(np.zeros((7,7)),self.valid,0,10)
        with self.assertRaises(ValueError):grid_summary(np.zeros((7,7)),self.valid,self.transform.rotation(10),'EPSG:32645')

    def test_network_requires_explicit_confirmation(self):
        with self.assertRaises(BridgeError) as cm:TerrainStore('/unused').obtain(False)
        self.assertEqual(cm.exception.status,422)

    def test_scene_path_traversal_refused(self):
        with self.assertRaises(BridgeError):TerrainStore('/unused').scene('../../etc/passwd')

    def test_modified_cached_raster_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            name='terrain-'+'a'*16;root=Path(tmp)/name;root.mkdir()
            for f in ['source.tif','analysis.tif']:(root/f).write_bytes(b'original')
            data={'id':name,'population':'NEW_REAL_DEM','hashes':{f:hashlib.sha256(b'original').hexdigest() for f in ['source.tif','analysis.tif']}}
            (root/'scene.json').write_text(json.dumps(data))
            store=TerrainStore(tmp);self.assertEqual(store.scene(name)['id'],name)
            (root/'analysis.tif').write_bytes(b'tampered')
            with self.assertRaises(BridgeError) as cm:store.scene(name)
            self.assertEqual(cm.exception.status,409)

    def test_empty_hash_map_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            name='terrain-'+'a'*16;root=Path(tmp)/name;root.mkdir()
            (root/'scene.json').write_text(json.dumps({'id':name,'population':'NEW_REAL_DEM','hashes':{}}))
            with self.assertRaises(BridgeError) as cm:TerrainStore(tmp).scene(name)
            self.assertEqual(cm.exception.status,422)
