import unittest
from vqa_answers import present_answer


class VQAAnswerTests(unittest.TestCase):
    def test_observed_dehradun_overclaim_is_withheld(self):
        raw = ('The major visible features are densely packed residential areas, roads and green spaces. '
               'The roads appear to be in good condition, with no signs of congestion or accidents. '
               'The green spaces are likely parks. Therefore, the answer is Dense Residential.')
        result = present_answer('Describe this image.', raw)
        self.assertIn('built-up', result['answer'])
        self.assertIn('roads', result['answer'])
        for word in ['congestion', 'accidents', 'good condition', 'parks', 'residential']:
            self.assertNotIn(word, result['answer'])
        self.assertFalse(result['withheld'])

    def test_sundarbans_season_and_health_not_presented(self):
        raw = ('The major visible features are winding rivers and surrounding greenery. '
               'The greenery suggests a healthy ecosystem. '
               'Snow indicates a colder season.')
        result = present_answer('Describe the scene.', raw)
        self.assertIn('winding rivers', result['answer'])
        self.assertNotIn('healthy', result['answer'])
        self.assertNotIn('Snow', result['answer'])

    def test_does_not_complete_truncated_description(self):
        result = present_answer('Describe this image.', 'The main features are a lake and', truncated=True)
        self.assertTrue(result['withheld'])
        self.assertNotIn('lake', result['answer'])

    def test_negative_sentence_not_converted_to_presence(self):
        result = present_answer('Describe the buildings.', 'No buildings are visible.')
        self.assertTrue(result['withheld'])

    def test_exact_terminal_label_only(self):
        result = present_answer('Is there a road?', 'A path is visible. Therefore, the answer is yes')
        self.assertEqual(result['answer'], 'Yes')
        self.assertFalse(result['withheld'])
        self.assertTrue(present_answer('Is there a road?', 'Yes, perhaps.')['withheld'])

    def test_conflicting_binary_output_withheld(self):
        self.assertTrue(present_answer('Is there water?', 'No, water is absent. Therefore, the answer is yes')['withheld'])

    def test_formatting_is_not_visual_verification(self):
        result = present_answer('Is this image rural or urban?', 'The region is open. Therefore, the answer is rural')
        self.assertEqual(result['answer'], 'Rural')
        self.assertIn('not independently verified', result['limitation'])
