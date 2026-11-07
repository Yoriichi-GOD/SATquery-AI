"""Synthetic software checks; these tests do not measure model quality."""
import unittest
from research.vqa.core import (balanced_rows, completion_labels, correct, image_name, normalise_answer,
                               paired_gain, score, split_images, training_records, verify_disjoint)


def source(name, question='How many planes?', answer='2', task='vqa'):
    return {'image': name, 'conversations': [{'from': 'human', 'value': f'<image>\n[{task}] {question}. A short answer to the question is'}, {'from': 'gpt', 'value': answer}]}


class VQATrainingTests(unittest.TestCase):
    def test_assistant_loss_excludes_image_prompt_and_padding(self):
        prefix = [1, 151655, 2]
        self.assertEqual(completion_labels(prefix, prefix+[8, 9, 0], [1, 1, 1, 1, 1, 0]), [-100, -100, -100, 8, 9, -100])

    def test_mismatched_chat_template_cannot_train_the_wrong_tokens(self):
        with self.assertRaises(ValueError): completion_labels([1, 2], [1, 3, 4], [1, 1, 1])
        with self.assertRaises(ValueError): completion_labels([1, 2], [1, 2], [1, 1])

    def test_image_paths_cannot_escape_the_dataset(self):
        for value in ('../scene.png', 'https://example/x.png', '/x.png', 'x/y.png', 'a\\b.png'):
            with self.subTest(value=value), self.assertRaises(ValueError): image_name(value)

    def test_strip_dataset_scaffolding_but_keep_the_actual_question(self):
        rows, _ = training_records([source('P0001_0000.png')])
        self.assertEqual(rows[0]['question'], 'How many planes?')
        self.assertEqual(rows[0]['reference'], '2')

    def test_grounding_is_not_accidentally_trained_as_vqa(self):
        rows, rejected = training_records([source('P0001_0000.png', task='refer')])
        self.assertEqual(rows, [])
        self.assertEqual(rejected['grounding_out_of_scope'], 1)

    def test_conflicting_targets_are_quarantined(self):
        rows, rejected = training_records([source('P0001_0000.png'), source('P0001_0000.png', answer='3')])
        self.assertEqual(rows, [])
        self.assertEqual(rejected['conflicting_targets'], 2)

    def test_unobservable_metadata_is_not_taught_as_visual_truth(self):
        rows, rejected = training_records([source('P0001_0000.png', question='What is the acquisition date?')])
        self.assertFalse(rows)
        self.assertEqual(rejected['unobservable_metadata_question'], 1)

    def test_splits_are_group_disjoint_and_reproducible(self):
        rows = [{'image': f'P{i:04d}_0000.png'} for i in range(200)]
        train, dev = split_images(rows, 42, 30, 10)
        self.assertEqual((train, dev), split_images(list(reversed(rows)), 42, 30, 10))
        self.assertFalse(set(train) & set(dev))

    def test_pixel_duplicates_block_training_validation_overlap(self):
        a = [{'image': 'a_1.png', 'group': 'a', 'image_sha256': 'same'}]
        b = [{'image': 'b_1.png', 'group': 'b', 'image_sha256': 'same'}]
        with self.assertRaisesRegex(ValueError, 'image_sha256'): verify_disjoint(a, b)

    def test_bucket_balancing_does_not_cherry_pick_reference_answers(self):
        rows = [{'id': str(i), 'category': 'presence' if i < 10 else 'quantity'} for i in range(12)]
        chosen = balanced_rows(rows, 4, 42)
        self.assertEqual(sum(r['category'] == 'quantity' for r in chosen), 2)

    def test_entire_answer_matching_rejects_explanations_and_contradictions(self):
        self.assertFalse(correct({'raw_answer': 'yes, but actually no'}, 'yes'))
        self.assertFalse(correct({'raw_answer': 'there are two planes'}, '2'))
        self.assertTrue(correct({'raw_answer': 'Two.'}, '2'))
        self.assertEqual(normalise_answer('swimming-pool'), normalise_answer('Swimming pool.'))

    def test_truncated_and_failed_outputs_never_count_as_correct(self):
        self.assertFalse(correct({'raw_answer': 'yes', 'truncated': True}, 'yes'))
        self.assertFalse(correct({'raw_answer': 'yes', 'error': 'execution failed'}, 'yes'))

    def test_missing_attempts_remain_in_denominator(self):
        refs = [{'id': '1', 'category': 'presence', 'reference': 'yes'}, {'id': '2', 'category': 'presence', 'reference': 'no'}]
        result = score(refs, [{'id': '1', 'raw_answer': 'yes'}])
        self.assertEqual((result['n'], result['correct'], result['missing'], result['accuracy']), (2, 1, 1, .5))
        self.assertIsNone(result['official_gpt_score'])

    def test_duplicate_or_foreign_predictions_are_rejected(self):
        refs = [{'id': '1', 'category': 'presence', 'reference': 'yes'}]
        with self.assertRaises(ValueError): score(refs, [{'id': '2', 'raw_answer': 'yes'}])
        with self.assertRaises(ValueError): score(refs, [{'id': '1'}, {'id': '1'}])

    def test_paired_intervals_use_source_groups_not_independent_questions(self):
        refs = [{'id': str(i), 'image': f'P{i//2}_0000.png', 'group': f'P{i//2}', 'reference': 'yes'} for i in range(6)]
        base = [{'id': r['id'], 'raw_answer': 'no'} for r in refs]
        improved = [{'id': r['id'], 'raw_answer': 'yes'} for r in refs]
        gain = paired_gain(refs, base, improved, repetitions=100)
        self.assertEqual((gain['gain'], gain['ci95'], gain['groups']), (1., [1., 1.], 3))


if __name__ == '__main__': unittest.main()
