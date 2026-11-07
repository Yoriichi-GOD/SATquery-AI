import unittest
import numpy as np
from shapely.geometry import box
from research.evaluation.metrics import binary_metrics,ranking_metrics,paired_spatial_interval,reject_spatial_leakage


class ScientificMetricsTests(unittest.TestCase):
    def test_confusion_and_invalid_support(self):
        r=binary_metrics(np.array([1,1,0,0,1],bool),np.array([1,0,1,0,0],bool),np.array([1,1,1,1,0],bool))
        self.assertEqual([r[k] for k in ['tp','fp','fn','tn','ignored']],[1,1,1,1,1])
        self.assertEqual(r['f1'],.5);self.assertEqual(r['iou'],1/3)
        r=binary_metrics(np.zeros(2,bool),np.zeros(2,bool),np.zeros(2,bool))
        self.assertIsNone(r['iou']);self.assertEqual(r['status'],'UNAVAILABLE')
    def test_tied_rankings_do_not_depend_on_id_order(self):
        a=ranking_metrics([1,1,0],[1,0,1],ks=[1])
        b=ranking_metrics([1,1,0],[0,1,1],ks=[1])
        self.assertEqual(a,b)
        self.assertEqual(a['precision_at_1'],.5)
        self.assertAlmostEqual(a['average_precision'],7/12)
    def test_abstention_retains_reference_denominator(self):
        r=ranking_metrics([1,None],[0,1],ks=[1])
        self.assertEqual(r['n'],2);self.assertEqual(r['abstentions'],1)
        self.assertEqual(r['average_precision'],.5)
        self.assertEqual(r['recall_at_1'],0)
    def test_spatial_overlap_and_too_few_blocks(self):
        with self.assertRaises(ValueError):reject_spatial_leakage([box(0,0,2,2)],[box(1,1,3,3)])
        self.assertEqual(paired_spatial_interval([1,0],[0,1],[1,0],['a','a'])['status'],'UNAVAILABLE')
    def test_paired_bootstrap_reproducible_and_null_difference(self):
        a=[1,0]*5;y=[1,0]*5;blocks=list('aabbccddee')
        r=paired_spatial_interval(a,a,y,blocks,replicates=30)
        self.assertEqual(r['interval'],[0,0])
        self.assertEqual(r,paired_spatial_interval(a,a,y,blocks,replicates=30))
