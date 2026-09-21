import unittest
from routing import route
from vqa_answers import present_open_answer
class OpenVQATests(unittest.TestCase):
 def test_counts_and_visual_questions(self):
  for q in ['how many cars are there in this image?', 'Count the buildings', 'How many baseball fields and buildings are there?', 'What colour is the car?', 'Describe the snowy mountain.', 'What is the car doing?', 'Is there more water than vegetation?']:
   with self.subTest(q=q): self.assertEqual(route(q)['tool'], 'vqa')
 def test_measurement_and_tools(self):
  for q in ['Calculate NDVI', 'What is average NDVI?', 'Count cars and calculate NDVI', 'Locate the cars', 'Compare this to last year', 'Analyse SAR', 'How many unhealthy trees are there?']:
   with self.subTest(q=q): self.assertEqual(route(q)['tool'], 'refuse')
 def test_preserve_counts_snow_and_uncertainty(self):
  for raw in ['There is one red car.', 'A snowy mountain is visible.', 'There may be two cars, but one is obscured.', 'No cars are visible.']:
   result=present_open_answer(raw,count=True)
   self.assertIn(raw,result['answer']);self.assertFalse(result['withheld'])
