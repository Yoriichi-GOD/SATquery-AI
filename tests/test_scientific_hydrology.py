"""Known geometries, not satellite accuracy trials."""
import unittest

import numpy as np
from affine import Affine

from research.terrain_exposure.hydrology import derive, path, delineate_catchment, topological_order
from research.terrain_exposure.io import Grid, resolution_status


class HydrologyTests(unittest.TestCase):
    def grid(self, shape=(5, 5)):
        return Grid(shape, Affine(10, 0, 300000, 0, -10, 3100000), "EPSG:32645")

    def test_known_east_plane_accumulation_hand_and_aspect(self):
        z = np.tile(np.arange(5, 0, -1), (5, 1)).astype(float)
        h = derive(z, np.ones_like(z, bool), self.grid(), 300)
        np.testing.assert_array_equal(h.accumulation, np.tile(np.arange(1, 6), (5, 1)))
        np.testing.assert_array_equal(h.hand, np.tile([2, 1, 0, 0, 0], (5, 1)))
        self.assertEqual(path(h, 10), [10, 11, 12, 13, 14])
        self.assertAlmostEqual(h.aspect[2, 2], 90)
        self.assertAlmostEqual(h.slope[2, 2], np.degrees(np.arctan(.1)))
        self.assertEqual(delineate_catchment(h, 14).sum(), 5)

    def test_fill_depression_and_preserve_original(self):
        z = np.full((5, 5), 10.0)
        z[2, 2] = 1
        h = derive(z, np.ones_like(z, bool), self.grid())
        self.assertEqual(h.filled[2, 2], 10)
        self.assertEqual(h.original[2, 2], 1)
        self.assertEqual(h.summary["filled_cells"], 1)
        self.assertEqual(h.summary["outlet_accumulation_sum_cells"], 25)
        self.assertTrue(np.isnan(h.hand[2, 2]))

    def test_unconditioned_sink_is_retained(self):
        z = np.full((5, 5), 10.0)
        z[2, 2] = 1
        h = derive(z, np.ones_like(z, bool), self.grid(), conditioning="none")
        self.assertEqual(h.downstream[2, 2], -1)
        self.assertEqual(h.filled[2, 2], 1)

    def test_flat_is_acyclic_and_deterministic(self):
        z = np.ones((5, 5))
        a = derive(z, np.ones_like(z, bool), self.grid())
        b = derive(z, np.ones_like(z, bool), self.grid())
        np.testing.assert_array_equal(a.downstream, b.downstream)
        for i in range(25):
            route = path(a, i)
            self.assertEqual(len(route), len(set(route)))
        self.assertTrue(np.isnan(a.aspect).all())

    def test_nodata_disconnects_basins_and_stays_unknown(self):
        z = np.tile(np.arange(5, 0, -1), (5, 1)).astype(float)
        v = np.ones_like(z, bool)
        v[:, 2] = False
        h = derive(z, v, self.grid(), 100)
        self.assertTrue(np.isnan(h.filled[:, 2]).all())
        self.assertEqual(h.accumulation[:, 2].sum(), 0)
        self.assertNotIn(13, path(h, 10))
        self.assertEqual(h.summary["outlet_accumulation_sum_cells"], 20)
        self.assertEqual(path(h, 12), [])

    def test_reject_invalid_grid_missing_terrain_and_cycle(self):
        with self.assertRaises(ValueError):
            Grid((5, 5), Affine.identity(), "EPSG:4326")
        with self.assertRaises(ValueError):
            Grid((5, 5), Affine(10, 1, 0, 0, -10, 0), "EPSG:32645")
        with self.assertRaises(ValueError):
            derive(np.ones((5, 5)), np.zeros((5, 5), bool), self.grid())
        with self.assertRaises(ValueError):
            topological_order(np.array([[1, 0]]), np.ones((1, 2), bool))
        self.assertEqual(resolution_status(90, 5)["status"], "INSUFFICIENT_RESOLUTION")
