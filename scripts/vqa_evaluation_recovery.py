"""Resume a sealed VQA evaluation without retraining or changing its protocol."""
import argparse
from datetime import datetime, timedelta, timezone
import gzip
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import sys
import threading
import time
import traceback

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from research.vqa.core import image_name, paired_gain, prediction_map, save_json, scene_group, score, sha256


def remaining_seconds(started_utc, limit, current=None):
    """A restart never extends the registered wall-time ceiling."""
    current = current or datetime.now(timezone.utc)
    remaining = (datetime.fromisoformat(started_utc)+timedelta(seconds=limit)-current).total_seconds()
    if remaining <= 0:
        raise TimeoutError('Original campaign wall-time ceiling has expired')
    return remaining


def fingerprint(prompts):
    return hashlib.sha256(json.dumps(prompts, sort_keys=True).encode()).hexdigest()


def verify_reference(path, sealed_sha256, upstream_sha256=None):
    actual = sha256(path)
    if actual != sealed_sha256:
        raise ValueError('Sealed final-reference checksum mismatch')
    if upstream_sha256 and actual != upstream_sha256.removeprefix('sha256:'):
        raise ValueError('Upstream final-reference checksum mismatch')
    return actual


def require_full_attempts(references, values):
    """Errors/empty answers count as failures, never as missing attempted rows."""
    expected = {str(row['id']) for row in references}
    if len(expected) != len(references) or set(values) != {'base', 'candidate'}:
        raise ValueError('Registered paired question support is invalid')
    if any(set(prediction_map(rows)) != expected for rows in values.values()):
        raise ValueError('The resumed run is missing registered prediction attempts')


def public_invalid_batches(rows):
    return [{'batch': row['batch'], 'reason': row['reason'].split(':', 1)[0]} for row in rows]


def validate_batch(directory, group, identity, index, image_hashes=None):
    """Accept only complete, hash-sealed, correctly identified matched arms."""
    directory = Path(directory)
    receipt = json.loads((directory/'complete.json').read_text())
    if set(receipt['files']) != {'base.jsonl', 'candidate.jsonl'} or receipt['questions'] != len(group):
        raise ValueError('Paired completion receipt has the wrong support')
    seals = {}
    for arm in ('base', 'candidate'):
        path = directory/(arm+'.jsonl')
        seals[arm] = sha256(path)
        if seals[arm] != receipt['files'][path.name]:
            raise ValueError('Saved prediction checksum mismatch')
        expected = {**identity, 'arm': arm, 'batch_index': index,
                    'style': 'short', 'input_sha256': fingerprint(group)}
        if json.loads((directory/(arm+'.identity.json')).read_text()) != expected:
            raise ValueError('Saved arm protocol/input identity mismatch')
        values = [json.loads(line) for line in path.read_text().splitlines()]
        prediction_map(values)
        if [str(row['id']) for row in values] != [str(row['id']) for row in group]:
            raise ValueError('Saved batch question identities differ')
        for row, prompt in zip(values, group):
            if row['image'] != prompt['image'] or not isinstance(row['raw_answer'], str):
                raise ValueError('Saved image/answer schema differs')
            if image_hashes is not None and 'image_sha256' in row:
                if row['image_sha256'] != image_hashes[row['image']]:
                    raise ValueError('Saved native-image hash differs')
    return seals


def context(root, run_id):
    root = Path(root)
    runtime = root/'.runtime/vqa-20261108'
    private = runtime/run_id
    public = root/'research/results/vqa-finetuning-20261108'/run_id
    local = root/'research/datasets/local/vqa-20261108'
    env = json.loads((private/'environment.json').read_text())
    freeze = json.loads((public/'CANDIDATE_FREEZE.json').read_text())
    seal = json.loads((private/'final-reference-seal.json').read_text())
    config_path = root/'research/experiments/vqa-finetuning-20261108.json'
    config = json.loads(config_path.read_text())
    config['config_sha256'] = sha256(config_path)
    if config['config_sha256'] != freeze['protocol_sha256'] or freeze['run_id'] != run_id:
        raise ValueError('Frozen protocol/run identity mismatch')
    if any(sha256(root/'research/vqa'/name) != digest for name, digest in freeze['source_sha256'].items()):
        raise ValueError('Registered training/inference/scoring source changed')
    if sha256(local/'corpus.json') != env['corpus_sha256']:
        raise ValueError('Training corpus changed')
    selection_path = private/'training/selection.json'
    if sha256(selection_path) != freeze['selection_sha256']:
        raise ValueError('Validation-only checkpoint selection changed')
    selection = json.loads(selection_path.read_text())
    if freeze['final_reference_opened_before_freeze'] or freeze['reload_answer_differences']:
        raise ValueError('Original candidate freeze/reload contract is not satisfied')
    if sha256(public/'CANDIDATE_FREEZE.json') != seal['candidate_freeze_sha256']:
        raise ValueError('Candidate freeze changed after final-reference access')
    references_path = local/'source/VRSBench_EVAL_vqa.json'
    metadata = json.loads((public.parent/'SOURCE_RECEIPTS.json').read_text())
    verify_reference(references_path, seal['sha256'], metadata['files']['VRSBench_EVAL_vqa.json']['sha256'])
    references = []
    for row in json.loads(references_path.read_text()):
        name = image_name(row['image_id'])
        references.append({'id': str(row['question_id']), 'image': name, 'group': scene_group(name),
                           'question': row['question'], 'reference': str(row['ground_truth']),
                           'category': row['type'], 'task': 'vqa'})
    if len(references) != seal['n'] or len({r['id'] for r in references}) != len(references):
        raise ValueError('Final-reference question support changed')
    prompts = [{k: row[k] for k in ('id', 'image', 'question', 'task')}
               for row in sorted(references, key=lambda row: (row['image'], int(row['id'])))]
    identity = {'model': config['model'], 'adapter_sha256': freeze['adapter_sha256'],
                'protocol_sha256': config['config_sha256'], 'reference_file_sha256': seal['sha256']}
    expected_identity = {**identity, 'effective': freeze['effective'], 'input_sha256': fingerprint(prompts)}
    if json.loads((private/'final/identity.json').read_text()) != expected_identity:
        raise ValueError('Original paired-evaluation identity changed')
    return {'root': root, 'runtime': runtime, 'private': private, 'public': public, 'local': local,
            'env': env, 'freeze': freeze, 'config': config, 'selection': selection,
            'references': references, 'prompts': prompts, 'identity': identity, 'metadata': metadata}


def audit(ctx, attempt_id):
    directory = ctx['private']/'recoveries'/attempt_id
    directory.mkdir(parents=True, exist_ok=False)
    archive = ctx['local']/'source/Images_val.zip'
    expected = ctx['metadata']['files']['Images_val.zip']['sha256'].removeprefix('sha256:')
    if sha256(archive) != expected:
        raise ValueError('Pinned native evaluation archive checksum mismatch')
    valid, invalid, questions = {}, [], 0
    size = ctx['freeze']['effective']['batch_size']
    arm_identity = {**ctx['identity'], 'effective': ctx['freeze']['effective']}
    for path in sorted((ctx['private']/'final/batches').iterdir()):
        if not path.is_dir() or not re.fullmatch(r'\d{6}', path.name):
            raise ValueError('Unexpected object in saved batch directory')
        index = int(path.name)
        group = ctx['prompts'][index*size:(index+1)*size]
        if not group:
            raise ValueError('Saved batch index exceeds registered question support')
        try:
            valid[path.name] = validate_batch(path, group, arm_identity, index)
            questions += len(group)
        except (ValueError, KeyError, FileNotFoundError, UnicodeDecodeError) as error:
            invalid.append({'batch': path.name, 'reason': type(error).__name__+': '+str(error)[:180]})
    receipt = {'run_id': ctx['freeze']['run_id'], 'attempt_id': attempt_id,
               'audited_utc': datetime.now(timezone.utc).isoformat(),
               'valid_questions_each_arm': questions, 'valid_batches': valid, 'invalid_batches': invalid,
               'total_questions_each_arm': len(ctx['prompts']), 'native_archive_sha256': expected,
               'candidate_freeze_sha256': sha256(ctx['public']/'CANDIDATE_FREEZE.json'),
               'resume_orchestration_sha256': sha256(Path(__file__)),
               'training_or_candidate_selection_changed': False}
    save_json(directory/'PRESTART_AUDIT.json', receipt)
    return receipt


def finish(ctx, values, store, attempt_id, original_started, recovery):
    private, public = ctx['private'], ctx['public']
    if (public/'FINAL_RESULTS.json').exists():
        raise FileExistsError('Completed results already exist; do not overwrite')
    references = ctx['references']
    require_full_attempts(references, values)
    seals = {arm: sha256(private/'final'/(arm+'.jsonl')) for arm in values}
    save_json(private/'prediction-seal.json', {'files': seals, 'n_each_arm': len(references)})
    metrics = {arm: score(references, rows) for arm, rows in values.items()}
    paired = paired_gain(references, values['base'], values['candidate'])
    old = json.loads((ctx['root']/'paired_lab/evidence/public-benchmarks-20260927/manifest.json').read_text())
    exposed = {Path(row['image']).name for row in old['cases'] if row['dataset'] == 'VRSBench'}
    captions = json.loads((ctx['root']/'paired_lab/evidence/benchmark-20260921/vrs-manifest.json').read_text())
    exposed.update(row['image_id'] for row in captions['cases'])
    subset = [row for row in references if row['image'] in exposed]
    exposed_ids = {row['id'] for row in subset}
    corpus = json.loads((ctx['local']/'corpus.json').read_text())
    train_hashes = {row['image_sha256'] for row in corpus['train']}
    overlap = sorted(name for name, digest in store.hashes.items() if digest in train_hashes)
    clean = [row for row in references if row['image'] not in set(overlap)]
    clean_ids = {row['id'] for row in clean}
    archive_receipt = json.loads((private/'archive-status.json').read_text())
    result = {'run_id': ctx['freeze']['run_id'], 'completed_utc': datetime.now(timezone.utc).isoformat(),
              'scope': 'Full pinned model-only VRSBench VQA; deterministic whole-answer diagnostics, not the published GPT-judge metric or end-to-end application accuracy',
              'metrics': metrics, 'paired_gain': paired,
              'known_reused_image_subset': {arm: score(subset, [p for p in rows if p['id'] in exposed_ids]) for arm, rows in values.items()},
              'exposure_registry_scope': 'Minimum known prior inspection from two saved manifests; not exhaustive, no untouched-test claim',
              'excluding_detected_training_pixel_overlap': {arm: score(clean, [p for p in rows if p['id'] in clean_ids]) for arm, rows in values.items()},
              'native_images_decoded': len(store.hashes), 'training_pixel_overlap_images': overlap,
              'independent_foundation_model_exposure': 'NOT_ESTABLISHED',
              'validation_selection': ctx['selection']['selected']['score'], 'validation_gate': ctx['selection']['gate'],
              'prediction_sha256': seals, 'reference_sha256': ctx['identity']['reference_file_sha256'],
              'candidate_freeze_sha256': sha256(public/'CANDIDATE_FREEZE.json'),
              'elapsed_seconds': (datetime.now(timezone.utc)-datetime.fromisoformat(original_started)).total_seconds(),
              'accounted_download_bytes': archive_receipt['accounted_download_bytes']+(ctx['local']/'source/VRSBench_EVAL_vqa.json').stat().st_size,
              'production_defaults_changed': False, 'official_gpt_judge': 'NOT_RUN',
              'resumed_after_shutdown': {'attempt_id': attempt_id, 'retained_questions_each_arm': recovery['valid_questions_each_arm'],
                                         'preserved_invalid_batches': public_invalid_batches(recovery['invalid_batches']), 'original_wall_ceiling_preserved': True}}
    for arm in values:
        target = public/(arm+'-predictions.jsonl.gz')
        with (private/'final'/(arm+'.jsonl')).open('rb') as source, target.open('xb') as raw:
            with gzip.GzipFile(filename='', mode='wb', fileobj=raw, mtime=0) as stream:
                shutil.copyfileobj(source, stream)
    save_json(public/'FINAL_RESULTS.json', result)
    lines = ['# VQA adaptation and full VRSBench evaluation', '', result['scope'], '',
             '| Arm | Questions | Correct | Normalised exact match | Strict exact match | Errors | Truncated |',
             '|---|---:|---:|---:|---:|---:|---:|']
    for arm, metric in metrics.items():
        lines.append(f"| {arm} | {metric['n']} | {metric['correct']} | {100*metric['accuracy']:.2f}% | {100*metric['strict_correct']/metric['n']:.2f}% | {metric['errors']} | {metric['truncated']} |")
    lines += ['', f"Paired gain: {100*paired['gain']:.2f} percentage points; 95% filename-group bootstrap interval {paired['ci95']}.", '',
              'Selected only on the official-training holdout and frozen before final-reference access. Historical inspection and unresolved foundation-model exposure are disclosed. One seed and one configuration; no replicated scientific-superiority claim.', '',
              'Evaluation resumed after a laptop shutdown with the same frozen adapter, protocol, native inputs and source hashes. Valid completed batches were retained; invalid/incomplete batches were preserved and repeated in their original batch shapes. The original wall-time ceiling was retained.', '',
              'Published GPT judging was not executed. Production defaults are unchanged. All errors, truncations and missing predictions remain failures in the denominator. Native training/evaluation pixel overlap is reported in FINAL_RESULTS.json.', '',
              '[Detailed results](FINAL_RESULTS.json) · [Candidate freeze](CANDIDATE_FREEZE.json) · [Recovery](EVALUATION_RECOVERY.json) · [Protocol](../../../experiments/vqa-finetuning-20261108.json)']
    (public/'REPORT.md').write_text('\n'.join(lines)+'\n', encoding='utf-8')
    return result


def run(ctx, attempt_id):
    import peft
    from peft import PeftModel
    import torch
    import transformers
    from research.vqa.gpu import ImageStore, infer, infer_pair, input_rows, load
    runtime, private = ctx['runtime'], ctx['private']
    attempt = private/'recoveries'/attempt_id
    recovery = json.loads((attempt/'PRESTART_AUDIT.json').read_text())
    if recovery['resume_orchestration_sha256'] != sha256(Path(__file__)):
        raise ValueError('Recovery orchestration changed after its audit')
    original = json.loads((runtime/'current-status.json').read_text())
    original_started = original['started_utc']
    deadline = time.monotonic()+remaining_seconds(original_started, ctx['config']['limits']['max_wall_seconds'])
    status = {**original, 'state': 'running', 'phase': 'recovery_verification', 'pid': os.getpid(),
              'recovery_attempt': attempt_id, 'retained_questions_each_arm': recovery['valid_questions_each_arm']}
    lock = runtime/'worker.lock'
    with lock.open('x') as stream: json.dump({'pid': os.getpid(), 'run_id': ctx['freeze']['run_id'], 'attempt_id': attempt_id}, stream)
    stopped = threading.Event()
    mutex = threading.Lock()
    def update(message, phase=None):
        if any(sha256(ctx['root']/'research/vqa'/name) != value for name, value in ctx['freeze']['source_sha256'].items()):
            raise RuntimeError('Original frozen module source changed')
        if sha256(ctx['public']/'CANDIDATE_FREEZE.json') != recovery['candidate_freeze_sha256']:
            raise RuntimeError('Original candidate freeze changed')
        with mutex:
            if phase: status['phase'] = phase
            status.update(message=message, updated_utc=datetime.now(timezone.utc).isoformat(),
                          elapsed_seconds=(datetime.now(timezone.utc)-datetime.fromisoformat(original_started)).total_seconds())
            save_json(runtime/'current-status.json', status)
        print(status['updated_utc'], status['phase'], message, flush=True)
    def heartbeat():
        while not stopped.wait(20):
            with mutex:
                save_json(private/'heartbeat.json', {'utc': datetime.now(timezone.utc).isoformat(), 'pid': os.getpid(),
                          'phase': status['phase'], 'recovery_attempt': attempt_id})
    threading.Thread(target=heartbeat, daemon=True).start()
    try:
        update('Verifying runtime, base weights and frozen adapter before resuming')
        actual_env = {'python': platform.python_version(), 'torch': torch.__version__,
                      'transformers': transformers.__version__, 'peft': peft.__version__}
        if any(actual_env[key] != ctx['env'][key] for key in actual_env):
            raise ValueError('Runtime versions differ from the frozen evaluation')
        model, processor, snapshot = load(ctx['config'], ctx['freeze']['effective'])
        if sha256(Path(snapshot)/'model.safetensors') != ctx['freeze']['base_weight_sha256']:
            raise ValueError('Base checkpoint checksum changed')
        adapter = Path(ctx['selection']['selected']['adapter'])
        if sha256(adapter/'adapter_model.safetensors') != ctx['freeze']['adapter_sha256']:
            raise ValueError('Frozen adapter checksum changed')
        model = PeftModel.from_pretrained(model, adapter).eval()
        corpus = json.loads((ctx['local']/'corpus.json').read_text())
        store = ImageStore(directory=ctx['local']/'images/train', receipts=corpus['images'])
        for arm, expected_path in [('base', private/'training/base-dev.jsonl'), ('candidate', adapter.parent/'dev.jsonl')]:
            replay = infer(model, processor, input_rows(corpus['dev'][:32]), store, ctx['freeze']['effective'], attempt/(arm+'-reload.jsonl'),
                           {'adapter_sha256': ctx['freeze']['adapter_sha256'], 'purpose': 'Post-shutdown mechanical reload verification', 'arm': arm},
                           update, baseline=arm == 'base', deadline=deadline)
            expected = {row['id']: row['raw_answer'] for row in map(json.loads, expected_path.read_text().splitlines())}
            if len(replay) != 32 or any(row.get('error') or row['raw_answer'] != expected[row['id']] for row in replay):
                raise ValueError(arm+' does not reproduce saved validation answers')
        final_store = ImageStore(archive=ctx['local']/'source/Images_val.zip')
        names = sorted({row['image'] for row in ctx['references']})
        for index, name in enumerate(names, 1):
            if time.monotonic() >= deadline: raise TimeoutError('Original campaign ceiling reached during recovery')
            final_store.image(name)
            if index % 512 == 0 or index == len(names): update(f'Native evaluation images decoded and rehashed: {index}/{len(names)}')
        batch_size = ctx['freeze']['effective']['batch_size']
        identity = {**ctx['identity'], 'effective': ctx['freeze']['effective']}
        for name, hashes in recovery['valid_batches'].items():
            index = int(name)
            group = ctx['prompts'][index*batch_size:(index+1)*batch_size]
            if validate_batch(private/'final/batches'/name, group, identity, index, final_store.hashes) != hashes:
                raise ValueError('An audited completed batch changed before resume')
        for bad in recovery['invalid_batches']:
            source = private/'final/batches'/bad['batch']
            target = attempt/'preserved-invalid-batches'/bad['batch']
            if not source.resolve().is_relative_to((private/'final/batches').resolve()) or not target.resolve().is_relative_to(attempt.resolve()):
                raise ValueError('Unsafe batch preservation target')
            target.parent.mkdir(parents=True, exist_ok=True)
            source.rename(target)
        public_recovery = {key: value for key, value in recovery.items() if key != 'valid_batches'}
        public_recovery['invalid_batches'] = public_invalid_batches(recovery['invalid_batches'])
        public_recovery.update(reloaded_validation_answers_matched_per_arm=32, native_images_redecoded=len(names),
                               new_training_steps=0, original_started_utc=original_started,
                               original_deadline_utc=(datetime.fromisoformat(original_started)+timedelta(seconds=ctx['config']['limits']['max_wall_seconds'])).isoformat())
        save_json(ctx['public']/'EVALUATION_RECOVERY.json', public_recovery)
        update(f'Resuming {len(ctx["prompts"])} questions per arm; {recovery["valid_questions_each_arm"]} each already validated', 'final_inference')
        values = infer_pair(model, processor, ctx['prompts'], final_store, ctx['freeze']['effective'], private/'final', ctx['identity'], update, deadline)
        for name, hashes in recovery['valid_batches'].items():
            directory = private/'final/batches'/name
            if any(sha256(directory/(arm+'.jsonl')) != value for arm, value in hashes.items()):
                raise ValueError('A retained original prediction changed')
        update('Full prediction files sealed; computing the registered metrics', 'scoring')
        result = finish(ctx, values, final_store, attempt_id, original_started, recovery)
        with mutex: status['state'] = 'complete'
        update('Full paired VRSBench evaluation, registered scoring and report complete', 'complete')
        save_json(attempt/'COMPLETION.json', {'completed_utc': result['completed_utc'], 'prediction_sha256': result['prediction_sha256']})
    except BaseException as error:
        with mutex: status.update(state='failed', phase='failed', error_type=type(error).__name__)
        try: update(type(error).__name__+': '+str(error)[:240])
        finally: (attempt/'failure.log').write_text(traceback.format_exc())
        raise
    finally:
        stopped.set()
        if lock.exists() and json.loads(lock.read_text()).get('pid') == os.getpid(): lock.unlink()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--run-id', required=True)
    parser.add_argument('--attempt-id', required=True)
    parser.add_argument('--audit-only', action='store_true')
    args = parser.parse_args()
    if not all(re.fullmatch(r'[A-Za-z0-9-]+', value) for value in (args.run_id, args.attempt_id)):
        raise ValueError('Unsafe recovery identity')
    ctx = context(ROOT, args.run_id)
    if args.audit_only:
        receipt = audit(ctx, args.attempt_id)
        print(json.dumps({key: value for key, value in receipt.items() if key != 'valid_batches'}, indent=2))
    else:
        run(ctx, args.attempt_id)
