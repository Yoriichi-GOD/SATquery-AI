import unittest
from scene_description import is_scene_description, PROMPT
class SceneDescriptionTests(unittest.TestCase):
    def test_equivalent_whole_scene_requests(self):
        for q in ['Describe this image.','describe the image','Can you describe this image?', 'What is in this image?', 'What does the scene show?', 'Please describe this picture in detail.', 'Describe the major visible features.']:
            with self.subTest(q=q):self.assertTrue(is_scene_description(q))
        self.assertEqual(PROMPT,'Describe this image in detail.')
    def test_specific_questions_remain_specific(self):
        for q in ['How many cars are there?', 'Are there any buildings?', 'Is this rural or urban?', 'Describe the vegetation in this image.', 'Describe this image briefly.', 'Calculate NDVI', 'Describe changes between these images', 'Describe this image and count cars', 'Outline buildings']:
            with self.subTest(q=q):self.assertFalse(is_scene_description(q))
