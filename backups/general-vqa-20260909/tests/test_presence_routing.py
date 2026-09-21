import unittest
from routing import route
class PresenceRoutingTests(unittest.TestCase):
 def test_natural_presence(self):
  for q in ['is there a mountain in this image ?', 'Is there a mountain in this image?', 'Are there any cars in this picture?', 'Is a snowy mountain visible in this image?', 'Does this image show a mountain?', 'Can you see a green car in this photo?', 'Do you see a lake?', 'Is there a bridge in this image ?!']:
   with self.subTest(q=q): self.assertEqual(route(q)['tool'],'vqa')
 def test_unsupported_still_refused(self):
  for q in ['Is there a mountain in this image and calculate its height?', 'Is there more water than vegetation?', 'Is there a mountain in this image? Locate it.', 'Is there a mountain compared to last year?', 'Show the mountain', 'How many mountains are there?', 'Is there vegetation health in this image?', 'Calculate NDVI']:
   with self.subTest(q=q): self.assertEqual(route(q)['tool'],'refuse')
