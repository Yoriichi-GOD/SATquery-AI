import unittest
import numpy as np
from affine import Affine
from shapely.geometry import Point, box

from research.terrain_exposure.graph import Observation, Receptor, build_graph
from research.terrain_exposure.hydrology import derive
from research.terrain_exposure.io import Grid


class GraphTests(unittest.TestCase):
    def setUp(self):
        self.grid=Grid((5,5),Affine(10,0,300000,0,-10,3100000),'EPSG:32645')
        z=np.tile(np.arange(5,0,-1),(5,1)).astype(float)
        self.h=derive(z,np.ones_like(z,bool),self.grid,300)
        candidate=np.zeros((5,5),bool);candidate[2,1]=True
        self.o=Observation('water',candidate,np.ones((5,5),bool),self.grid,
                           {'sha256':'a'*64},['2026-08-16','2026-08-28'],'synthetic known mask')
    def receptor(self,name,index):
        return Receptor(name,'building',Point(self.grid.centre(index)),self.grid.crs,{'sha256':'b'*64},'2026-08-25')
    def graph(self,receptors):
        return build_graph(self.h,[self.o],receptors,{'sha256':'c'*64},target_width_m=5)
    def test_direction_is_not_proximity_and_direct_is_separate(self):
        g=self.graph([self.receptor('upstream',10),self.receptor('downstream',14),self.receptor('direct',11)])
        rows={r['receptor_id']:r for r in g['relationships']}
        self.assertEqual(rows['upstream']['status'],'NOT_CONNECTED_WITHIN_DOMAIN')
        self.assertEqual(rows['downstream']['status'],'POTENTIAL_DOWNSTREAM_CONNECTION')
        self.assertEqual(rows['downstream']['along_network_distance_m'],30)
        self.assertEqual(rows['direct']['status'],'DIRECT_GEOMETRIC_INTERSECTION')
        self.assertEqual(rows['downstream']['resolution_status'],'INSUFFICIENT_RESOLUTION')
        self.assertEqual(rows['downstream']['registration_status'],'UNVERIFIED')
    def test_unknown_coverage_not_zero_and_layer_denominators_separate(self):
        self.o.valid[2,4]=False
        g=self.graph([self.receptor('unknown',14)])
        row=g['relationships'][0]
        self.assertEqual(row['status'],'UNAVAILABLE_EVIDENCE')
        self.assertIsNone(row['ordinal_screening_tier'])
        self.assertIsNone(row['along_network_distance_m'])
        self.assertEqual(g['observations']['water']['valid_pixels'],24)
    def test_identity_and_graph_are_deterministic(self):
        a=self.graph([self.receptor('x',14)])
        b=self.graph([self.receptor('x',14)])
        self.assertEqual(a,b)
        self.assertEqual(len({n['id'] for n in a['nodes']}),len(a['nodes']))
        ids={n['id'] for n in a['nodes']}
        self.assertTrue(all(e['source'] in ids and e['target'] in ids for e in a['edges']))
    def test_same_cell_is_unresolved_not_connected(self):
        g=self.graph([Receptor('subpixel','building',Point(300019,3099971),self.grid.crs,
                              {'sha256':'b'*64},'2026-08-25')])
        # Both are in the same candidate pixel, so use finer native observation support.
        fine=Grid((10,10),Affine(5,0,300000,0,-5,3100000),self.grid.crs)
        a=np.zeros(fine.shape,bool);a[4,2]=True
        o=Observation('water',a,np.ones(fine.shape,bool),fine,{'sha256':'a'*64},['2026-08-28'],'synthetic')
        g=build_graph(self.h,[o],[Receptor('x','building',Point(300019,3099971),self.grid.crs,
                                          {'sha256':'b'*64},'2026-08-25')],{'sha256':'c'*64})
        self.assertEqual(g['relationships'][0]['status'],'UNRESOLVED_WITHIN_DEM_CELL')
    def test_candidate_in_unknown_support_is_rejected(self):
        with self.assertRaises(ValueError):
            Observation('bad',np.ones((5,5),bool),np.zeros((5,5),bool),self.grid,
                        {'sha256':'a'*64},['2026-08-28'],'synthetic')
