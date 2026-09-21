import unittest
from vqa_answers import present_count_answer
class FocusedCountTests(unittest.TestCase):
 def test_counts(self):
  for raw,expected in [('1',1),('0',0),('4.',4),('Twenty',20),('42',42)]:
   self.assertEqual(present_count_answer(raw)['count'],expected)
 def test_no_contradictory_prose_or_truncation(self):
  for raw in ['No stadiums. A large stadium is visible. Therefore, the answer is 0','1 or 2','uncertain','-1','1.5','']:
   self.assertTrue(present_count_answer(raw)['withheld'])
  self.assertTrue(present_count_answer('1',truncated=True)['withheld'])
