import unittest
from unittest.mock import patch
import evaluation


class EvaluationTests(unittest.TestCase):
    def test_saved_predictions_and_regressions(self):
        result = evaluation.development()
        self.assertEqual((result['questions'], result['images'], result['source_scenes']), (60, 20, 1))
        self.assertEqual(result['baseline_dev']['correct'], 23)
        self.assertEqual(result['adapted_dev']['correct'], 47)
        self.assertEqual(result['gains'], 26)
        self.assertEqual({r['question_id'] for r in result['regressions']}, {5440, 1936})
        self.assertEqual(result['majority_correct'], 37)
        self.assertTrue(all(len(v['sha256']) == 64 for v in result['evidence'].values()))

    def test_exact_match_not_substrings(self):
        rows = [dict(category='presence', answer='yes', prediction=p) for p in [' YES! ', 'yes indeed', 'not yes']]
        summary, scored = evaluation.score(rows)
        self.assertEqual(summary['correct'], 1)
        self.assertEqual(summary['invalid_format'], 2)

    def test_disagreement_with_saved_score_fails_closed(self):
        original = evaluation.score
        def altered(rows):
            summary, scored = original(rows)
            summary['correct'] += 1
            return summary, scored
        with patch.object(evaluation, 'score', altered), self.assertRaises(ValueError):
            evaluation.development()
