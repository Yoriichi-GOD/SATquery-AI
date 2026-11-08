"""Power-loss recovery must never accept torn, foreign or extended runs."""
from datetime import datetime, timezone
import json
from pathlib import Path
import tempfile
import unittest

from scripts.vqa_evaluation_recovery import fingerprint, remaining_seconds, require_full_attempts, validate_batch, verify_reference
from research.vqa.core import sha256


class FrozenEvaluationRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.fixture_root = Path(__file__).resolve().parents[1]/'.runtime/test-vqa-recovery'
        self.fixture_root.mkdir(parents=True, exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(prefix='recovery-', dir=self.fixture_root)
        self.directory = Path(self.temporary.name)
        assert self.directory.resolve().is_relative_to(self.fixture_root.resolve())
        self.group = [{'id': '42', 'image': 'source_1.png', 'question': 'How many?', 'task': 'vqa'}]
        self.identity = {'adapter_sha256': 'fixed', 'effective': {'batch_size': 4}, 'protocol_sha256': 'registered'}
        files = {}
        for arm in ('base', 'candidate'):
            path = self.directory/(arm+'.jsonl')
            path.write_text(json.dumps({'id': '42', 'image': 'source_1.png', 'raw_answer': '2', 'image_sha256': 'pixels'})+'\n')
            files[path.name] = sha256(path)
            (self.directory/(arm+'.identity.json')).write_text(json.dumps({**self.identity, 'arm': arm,
                    'batch_index': 0, 'style': 'short', 'input_sha256': fingerprint(self.group)}))
        (self.directory/'complete.json').write_text(json.dumps({'questions': 1, 'files': files}))

    def tearDown(self):
        assert self.directory.resolve().is_relative_to(self.fixture_root.resolve())
        self.temporary.cleanup()

    def test_valid_completed_batch_and_image_identity_survive(self):
        seals = validate_batch(self.directory, self.group, self.identity, 0, {'source_1.png': 'pixels'})
        self.assertEqual(set(seals), {'base', 'candidate'})

    def test_torn_prediction_rejected_even_with_complete_marker(self):
        (self.directory/'candidate.jsonl').write_bytes(b'\0'*100)
        with self.assertRaisesRegex(ValueError, 'checksum'):
            validate_batch(self.directory, self.group, self.identity, 0)

    def test_different_adapter_rejected_despite_valid_payload_hash(self):
        with self.assertRaisesRegex(ValueError, 'identity'):
            validate_batch(self.directory, self.group, {**self.identity, 'adapter_sha256': 'other'}, 0)

    def test_missing_second_arm_never_counts_as_complete(self):
        (self.directory/'candidate.jsonl').unlink()
        with self.assertRaises(FileNotFoundError):
            validate_batch(self.directory, self.group, self.identity, 0)

    def test_changed_native_image_rejected(self):
        with self.assertRaisesRegex(ValueError, 'image hash'):
            validate_batch(self.directory, self.group, self.identity, 0, {'source_1.png': 'changed'})

    def test_restart_keeps_original_wall_ceiling(self):
        now = datetime(2026, 11, 8, 4, 0, tzinfo=timezone.utc)
        self.assertEqual(remaining_seconds('2026-11-07T20:00:00+00:00', 43200, now), 14400)
        with self.assertRaises(TimeoutError):
            remaining_seconds('2026-11-07T15:00:00+00:00', 43200, now)

    def test_absent_upstream_digest_still_requires_original_reference_seal(self):
        source = self.directory/'source.json'
        source.write_text('original')
        sealed = sha256(source)
        self.assertEqual(verify_reference(source, sealed, None), sealed)
        source.write_text('changed')
        with self.assertRaisesRegex(ValueError, 'Sealed'):
            verify_reference(source, sealed, None)

    def test_upstream_digest_is_checked_when_available(self):
        source = self.directory/'source.json'
        source.write_text('original')
        with self.assertRaisesRegex(ValueError, 'Upstream'):
            verify_reference(source, sha256(source), 'sha256:wrong')

    def test_failed_attempts_remain_in_full_benchmark_denominator(self):
        values = {'base': [{'id': '42', 'raw_answer': '', 'error': 'OSError'}],
                  'candidate': [{'id': '42', 'raw_answer': ''}]}
        require_full_attempts(self.group, values)
        values['candidate'] = []
        with self.assertRaisesRegex(ValueError, 'missing'):
            require_full_attempts(self.group, values)


if __name__ == '__main__': unittest.main()
