import unittest
from engine import suppress
class BoxProcessingTests(unittest.TestCase):
 def test_duplicate_suppression_keeps_highest_score(self):
  indices,capped=suppress([[0,0,10,10],[0,0,10,10],[20,20,30,30]],[.3,.8,.5]);self.assertEqual(indices,[1,2]);self.assertFalse(capped)
 def test_degenerate_boxes(self):
  self.assertEqual(suppress([[1,1,1,5],[0,0,1,1]],[.9,.8])[0],[])
 def test_cap(self):
  b=[[i*10,0,i*10+5,5] for i in range(30)];indices,capped=suppress(b,[.5]*30);self.assertEqual(len(indices),24);self.assertTrue(capped)
if __name__=='__main__':unittest.main()
