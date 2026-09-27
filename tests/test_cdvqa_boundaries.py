import unittest
from test_unified import controller,optical

class CDVQABoundaries(unittest.TestCase):
    def reject(self,questions):
        for q in questions:
            with self.subTest(question=q),self.assertRaises(ValueError):
                controller.plan(q,[optical(),optical()])

    def test_unsupported_land_classes(self):
        self.reject(['Did the areas of non-vegetated ground surface change?',
                     'Have the regions of playgrounds changed?',
                     'Did the bare ground decrease?',
                     'Show road changes and playground changes'])

    def test_semantic_transitions(self):
        self.reject(['What have the areas of buildings mainly changed to?',
                     'What did the building change into?',
                     'Which land-cover class replaced buildings?',
                     'What was converted to buildings?'])

    def test_multiclass_rankings(self):
        self.reject(['What is the largest change?',
                     'What type of change is the smallest?',
                     'Which class changed most?',
                     'Which land-cover category changed least?'])

    def test_supported_temporal_survives(self):
        for q in ['What changed between these dates?', 'Show road changes',
                  'Have the regions of buildings changed?',
                  'Describe building demolition']:
            with self.subTest(question=q):
                self.assertEqual(controller.plan(q,[optical(),optical()])['task'],'temporal')

    def test_semantic_change_ratios(self):
        self.reject(['What is the percentage of changed regions?',
                     'What is the percentage of unchanged areas?',
                     'How much area of buildings has changed in the first image?',
                     'What fraction of land changed?', 'What is the change proportion of buildings in the second image?'])

if __name__=='__main__':unittest.main()
