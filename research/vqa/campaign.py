"""Durable local train → freeze → complete VRSBench VQA prediction/evaluation run."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import gzip
import json
import os
from pathlib import Path
import platform
import shutil
import threading
import time
import traceback

from .acquire import BASE, Budget, fetch_file, fetch_native_evaluation_archive
from .core import image_name, paired_gain, save_json, scene_group, score, sha256


def now(): return datetime.now(timezone.utc).isoformat()


def run(root, run_id):
    from peft import PeftModel
    import peft
    import torch
    import transformers
    from .gpu import ImageStore, infer, infer_pair, input_rows, load
    from .train import fit

    root = Path(root)
    private = root/'.runtime/vqa-20261108'/run_id
    private.mkdir(parents=True, exist_ok=False)
    support = root/'research/results/vqa-finetuning-20261108'
    public = support/run_id
    public.mkdir(exist_ok=False)
    protocol = root/'research/experiments/vqa-finetuning-20261108.json'
    config = json.loads(protocol.read_text()); config['config_sha256'] = sha256(protocol)
    corpus_path = root/'research/datasets/local/vqa-20261108/corpus.json'
    corpus = json.loads(corpus_path.read_text())
    if corpus['config_sha256'] != config['config_sha256']:
        raise ValueError('Corpus does not match the frozen base protocol')
    resource_path = support/'RESOURCE_PLAN.json'
    resource = json.loads(resource_path.read_text())
    if resource['base_protocol_sha256'] != config['config_sha256'] or not resource['parity_passed']:
        raise ValueError('No approved resource/parity plan')
    if sha256(support/'NATIVE_BATCH_PARITY.json') != resource['parity_receipt_sha256']:
        raise ValueError('Resource parity receipt changed')
    effective = resource['effective']
    code_files = sorted(Path(__file__).parent.glob('*.py'))
    code_hashes = {p.name: sha256(p) for p in code_files}
    started, deadline = time.monotonic(), time.monotonic()+config['limits']['max_wall_seconds']
    status = {'run_id': run_id, 'state': 'running', 'phase': 'starting', 'started_utc': now(), 'pid': os.getpid()}
    status_lock = threading.Lock(); stopped = threading.Event()
    lock = root/'.runtime/vqa-20261108/worker.lock'
    with lock.open('x') as stream: json.dump({'pid': os.getpid(), 'run_id': run_id}, stream)

    def update(message, phase=None, verify_source=True):
        if verify_source and any(sha256(p) != code_hashes[p.name] for p in code_files):
            raise RuntimeError('Worker source changed during the frozen run')
        with status_lock:
            if phase: status['phase'] = phase
            status.update(message=message, updated_utc=now(), elapsed_seconds=time.monotonic()-started)
            save_json(root/'.runtime/vqa-20261108/current-status.json', status)
        print(now(), status['phase'], message, flush=True)

    def heartbeat():
        while not stopped.wait(20):
            with status_lock:
                save_json(private/'heartbeat.json', {'utc': now(), 'pid': os.getpid(), 'phase': status['phase'],
                          'elapsed_seconds': time.monotonic()-started})

    threading.Thread(target=heartbeat, daemon=True).start()
    pool = ThreadPoolExecutor(max_workers=1)
    try:
        metadata = json.loads((support/'SOURCE_RECEIPTS.json').read_text())
        archive_hash = metadata['files']['Images_val.zip']['sha256'].removeprefix('sha256:')
        previous = json.loads((root/'.runtime/vqa-20261108/data-status.json').read_text())['transferred_bytes']
        # Conservative reserve also accounts for the earlier metadata/training-annotation audit.
        budget = Budget(config['limits']['max_download_bytes'])
        budget.consume(previous+192*1024*1024)
        local = root/'research/datasets/local/vqa-20261108'
        if shutil.disk_usage(local).free < 8*1024**3:
            raise RuntimeError('Insufficient free workspace storage for the native archive and receipts')
        def archive_progress(message):
            save_json(private/'archive-status.json', {'updated_utc': now(), 'message': message,
                      'accounted_download_bytes': budget.bytes})
        # Unlabelled image bytes may transfer during training; no final QA/reference file is opened.
        download = pool.submit(fetch_native_evaluation_archive, local/'source/Images_val.zip', budget,
                               archive_hash, archive_progress, deadline, stopped)
        env = {'python': platform.python_version(), 'torch': torch.__version__, 'transformers': transformers.__version__,
               'peft': peft.__version__, 'gpu': torch.cuda.get_device_name(0), 'model': config['model'],
               'effective': effective, 'source_sha256': code_hashes, 'protocol_sha256': config['config_sha256'],
               'resource_plan_sha256': sha256(resource_path), 'corpus_sha256': sha256(corpus_path)}
        save_json(private/'environment.json', env)
        save_json(public/'RUN_ENVIRONMENT.json', env)
        store = ImageStore(directory=local/'images/train', receipts=corpus['images'])
        update('Starting matched baseline and validation-only adapter training', 'training')
        selection = fit(root, config, effective, corpus, store, private/'training', update, deadline)

        update('Reloading selected adapter before final-reference access', 'reload_verification')
        model, processor, snapshot = load(config, effective)
        adapter = Path(selection['selected']['adapter'])
        if sha256(adapter/'adapter_model.safetensors') != selection['selected']['adapter_sha256']:
            raise ValueError('Selected adapter bytes changed')
        model = PeftModel.from_pretrained(model, adapter).eval()
        expected_file = adapter.parent/'dev.jsonl'
        expected = {r['id']: r['raw_answer'] for r in map(json.loads, expected_file.read_text().splitlines())}
        verification = corpus['dev'][:32]
        replay = infer(model, processor, input_rows(verification), store, effective, private/'reload.jsonl',
                       {'adapter_sha256': selection['selected']['adapter_sha256'], 'purpose': 'Mechanical reload verification'}, update, deadline=deadline)
        differences = [r['id'] for r in replay if r['raw_answer'] != expected[r['id']]]
        if differences: raise RuntimeError('Reloaded adapter does not reproduce validation answers')
        base_weight_hash = sha256(Path(snapshot)/'model.safetensors')
        freeze = {'run_id': run_id, 'frozen_utc': now(), 'model': config['model'],
                  'base_weight_sha256': base_weight_hash, 'adapter_sha256': selection['selected']['adapter_sha256'],
                  'optimizer_step': selection['selected']['optimizer_step'], 'effective': effective,
                  'validation_gate': selection['gate'], 'validation_paired_gain': selection['paired_validation'],
                  'protocol_sha256': config['config_sha256'], 'source_sha256': code_hashes,
                  'selection_sha256': sha256(private/'training/selection.json'),
                  'reload_questions': len(replay), 'reload_answer_differences': differences,
                  'final_reference_opened_before_freeze': False, 'production_defaults_changed': False}
        save_json(public/'CANDIDATE_FREEZE.json', freeze)
        save_json(private/'CANDIDATE_FREEZE.json', freeze)

        update('Candidate frozen; preparing the full official VQA evaluation support', 'final_data')
        archive_path = download.result()
        labels_path = fetch_file('VRSBench_EVAL_vqa.json', local/'source/VRSBench_EVAL_vqa.json', budget, update)
        expected_labels = metadata['files']['VRSBench_EVAL_vqa.json']['sha256']
        if expected_labels and sha256(labels_path) != expected_labels.removeprefix('sha256:'):
            raise ValueError('Final reference source SHA-256 mismatch')
        native = json.loads(labels_path.read_text())
        references = []
        for row in native:
            name = image_name(row['image_id'])
            if not isinstance(row['question'], str) or not isinstance(row['ground_truth'], (str, int, float)):
                raise ValueError('Unsupported final-evaluation schema')
            references.append({'id': str(row['question_id']), 'image': name, 'group': scene_group(name),
                               'question': row['question'], 'reference': str(row['ground_truth']),
                               'category': row['type'], 'task': 'vqa'})
        if len({r['id'] for r in references}) != len(references): raise ValueError('Duplicate official question identity')
        if {r['image'] for r in corpus['train']} & {r['image'] for r in references}:
            raise ValueError('Official train/evaluation filename overlap; final inference withheld')
        # Byte-hash overlap is checked against the final native archive during actual image loading.
        reference_sha = sha256(labels_path)
        save_json(private/'final-reference-seal.json', {'source_url': BASE+'VRSBench_EVAL_vqa.json',
                  'sha256': reference_sha, 'n': len(references), 'candidate_freeze_sha256': sha256(public/'CANDIDATE_FREEZE.json')})
        prompts = input_rows(sorted(references, key=lambda r: (r['image'], int(r['id']))))
        final_store = ImageStore(archive=archive_path)
        if {r['image'] for r in references}-set(final_store.mapping):
            raise ValueError('Official final images absent from the native archive')
        update(f'Running all {len(prompts)} official VQA questions in both matched arms', 'final_inference')
        values = infer_pair(model, processor, prompts, final_store, effective, private/'final',
                  {'model': config['model'], 'adapter_sha256': freeze['adapter_sha256'],
                   'protocol_sha256': config['config_sha256'], 'reference_file_sha256': reference_sha}, update, deadline)
        seals = {name: sha256(private/'final'/(name+'.jsonl')) for name in values}
        save_json(private/'prediction-seal.json', {'files': seals, 'n_each_arm': len(prompts)})
        update('Prediction files sealed; computing fixed metrics and paired uncertainty', 'scoring')
        metrics = {name: score(references, predictions) for name, predictions in values.items()}
        comparison = paired_gain(references, values['base'], values['candidate'])
        prior = json.loads((root/'paired_lab/evidence/public-benchmarks-20260927/manifest.json').read_text())
        exposed = {Path(r['image']).name for r in prior['cases'] if r['dataset'] == 'VRSBench'}
        old_caption = json.loads((root/'paired_lab/evidence/benchmark-20260921/vrs-manifest.json').read_text())
        exposed.update(r['image_id'] for r in old_caption['cases'])
        exposure = {}
        for name, predictions in values.items():
            subset = [r for r in references if r['image'] in exposed]
            ids = {r['id'] for r in subset}
            exposure[name] = score(subset, [p for p in predictions if p['id'] in ids])
        train_hashes = {r['image_sha256'] for r in corpus['train']}
        pixel_overlap = sorted(name for name, digest in final_store.hashes.items() if digest in train_hashes)
        overlap_free = [r for r in references if r['image'] not in set(pixel_overlap)]
        overlap_free_ids = {r['id'] for r in overlap_free}
        clean_metrics = {name: score(overlap_free, [p for p in predictions if p['id'] in overlap_free_ids])
                         for name, predictions in values.items()}
        result = {'run_id': run_id, 'completed_utc': now(), 'scope': 'Full pinned model-only VRSBench VQA; deterministic whole-answer diagnostics, not the published GPT-judge metric or end-to-end application accuracy',
                  'metrics': metrics, 'paired_gain': comparison, 'known_reused_image_subset': exposure,
                  'exposure_registry_scope': 'Minimum known prior inspection from two saved manifests; not exhaustive, no untouched-test claim',
                  'excluding_detected_training_pixel_overlap': clean_metrics,
                  'native_images_decoded': len(final_store.hashes), 'training_pixel_overlap_images': pixel_overlap,
                  'independent_foundation_model_exposure': 'NOT_ESTABLISHED',
                  'validation_selection': selection['selected']['score'], 'validation_gate': selection['gate'],
                  'prediction_sha256': seals, 'reference_sha256': reference_sha,
                  'candidate_freeze_sha256': sha256(public/'CANDIDATE_FREEZE.json'),
                  'elapsed_seconds': time.monotonic()-started, 'accounted_download_bytes': budget.bytes,
                  'production_defaults_changed': False, 'official_gpt_judge': 'NOT_RUN'}
        save_json(public/'FINAL_RESULTS.json', result)
        for name in values:
            source = private/'final'/(name+'.jsonl')
            target = public/(name+'-predictions.jsonl.gz')
            with source.open('rb') as stream, target.open('xb') as raw:
                with gzip.GzipFile(filename='', mode='wb', fileobj=raw, mtime=0) as compressed:
                    shutil.copyfileobj(stream, compressed)
        lines = ['# VQA adaptation and full VRSBench evaluation', '', result['scope'], '',
                 '| Arm | Questions | Correct | Normalised exact match | Strict exact match | Errors | Truncated |',
                 '|---|---:|---:|---:|---:|---:|---:|']
        for name, metric in metrics.items():
            lines.append(f"| {name} | {metric['n']} | {metric['correct']} | {100*metric['accuracy']:.2f}% | {100*metric['strict_correct']/metric['n']:.2f}% | {metric['errors']} | {metric['truncated']} |")
        lines += ['', f"Paired gain: {100*comparison['gain']:.2f} percentage points; 95% filename-group bootstrap interval {comparison['ci95']}.", '',
                  'The candidate was selected on the official-training holdout and frozen before final references were acquired. Historical VRSBench inspection and unresolved upstream exposure are disclosed. This is one seed and one configuration, not replicated scientific superiority.', '',
                  'Published GPT judging was not executed. Production defaults are unchanged. All errors/truncations/missing attempts remain unsuccessful in the denominator. Any detected training/evaluation pixel overlap is retained in FINAL_RESULTS.json and limits independence claims.', '',
                  '[Detailed results](FINAL_RESULTS.json) · [Candidate freeze](CANDIDATE_FREEZE.json) · [Data audit](../DATA_AUDIT.json) · [Protocol](../../../experiments/vqa-finetuning-20261108.json)']
        (public/'REPORT.md').write_text('\n'.join(lines)+'\n', encoding='utf-8')
        with status_lock: status['state'] = 'complete'
        update('Full evaluation and fixed scoring complete', 'complete')
    except BaseException as error:
        with status_lock:
            status.update(state='failed', error_type=type(error).__name__)
        stopped.set()
        update(type(error).__name__+': '+str(error).split('?')[0][:300], 'failed', verify_source=False)
        (private/'failure.log').write_text(traceback.format_exc())
        raise
    finally:
        stopped.set()
        pool.shutdown(wait=True, cancel_futures=True)
        lock.unlink(missing_ok=True)


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser(); p.add_argument('--run-id', required=True)
    args = p.parse_args()
    if not args.run_id.replace('-', '').isalnum(): raise ValueError('Unsafe run identity')
    run(Path(__file__).resolve().parents[2], args.run_id)
