"""Existing Qwen2-VL/PEFT stack; native images, answer-only loss and auditable outputs."""
from contextlib import nullcontext
from functools import lru_cache
import hashlib
import io
import json
from pathlib import Path
import random
import time
import zipfile

from PIL import Image
import torch
from transformers import AutoProcessor, Qwen2VLForConditionalGeneration
from huggingface_hub import snapshot_download
from peft import LoraConfig, get_peft_model

from .core import (ANSWER_INSTRUCTION, MODEL_ID, MODEL_REVISION, completion_labels,
                   image_name, prediction_map, save_json, sha256)
from .vision import cached_vision


class ImageStore:
    def __init__(self, directory=None, archive=None, receipts=None):
        self.directory = Path(directory) if directory else None
        self.archive = zipfile.ZipFile(archive) if archive else None
        self.receipts = receipts or {}
        self.hashes = {}
        self.mapping = {}
        if self.archive:
            for info in self.archive.infolist():
                name = Path(info.filename).name
                if name.endswith('.png'):
                    image_name(name)
                    if name in self.mapping:
                        raise ValueError('Ambiguous final-evaluation image basename')
                    if info.file_size > 16*1024*1024:
                        raise ValueError('Oversized native evaluation member')
                    self.mapping[name] = info.filename

    @lru_cache(maxsize=32)
    def image(self, name):
        image_name(name)
        if self.archive:
            raw = self.archive.read(self.mapping[name])
        else:
            raw = (self.directory/name).read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        expected = self.receipts.get(name, {}).get('sha256')
        if expected and expected != digest:
            raise ValueError('Native image hash changed')
        self.hashes[name] = digest
        with Image.open(io.BytesIO(raw)) as source:
            if source.width*source.height > 4_000_000:
                raise ValueError('Native image exceeds declared pixel limit')
            image = source.convert('RGB')
            image.load()
        return image


def load(config, effective):
    if not torch.cuda.is_available():
        raise RuntimeError('CUDA is required; no CPU/alternate-model substitution')
    torch.set_num_threads(4)
    torch.manual_seed(config['seed'])
    torch.cuda.manual_seed_all(config['seed'])
    torch.cuda.set_per_process_memory_fraction(.88)
    path = snapshot_download(MODEL_ID, revision=MODEL_REVISION, local_files_only=True)
    low, high = effective['min_visual_tokens']*28*28, effective['max_visual_tokens']*28*28
    processor = AutoProcessor.from_pretrained(path, use_fast=False, min_pixels=low, max_pixels=high,
                                               size={'shortest_edge': low, 'longest_edge': high})
    processor.tokenizer.padding_side = 'left'
    model = Qwen2VLForConditionalGeneration.from_pretrained(path, torch_dtype=torch.bfloat16,
              device_map={'': 'cuda:0'}, attn_implementation='sdpa').eval()
    return model, processor, path


def prompt_text(processor, row, style='short'):
    question = row['question']
    if style == 'short' and row.get('task', 'vqa') == 'vqa':
        question += '\n'+ANSWER_INSTRUCTION
    user = {'role': 'user', 'content': [{'type': 'image'}, {'type': 'text', 'text': question}]}
    return user, processor.apply_chat_template([user], tokenize=False, add_generation_prompt=True)


def supervise(processor, row, store, max_tokens):
    user, prefix = prompt_text(processor, row)
    full = processor.apply_chat_template([user, {'role': 'assistant', 'content': [
            {'type': 'text', 'text': row['reference']}]}], tokenize=False, add_generation_prompt=False)
    image = store.image(row['image'])
    before = processor(text=[prefix], images=[image], return_tensors='pt')
    batch = processor(text=[full], images=[image], return_tensors='pt')
    if batch.input_ids.shape[1] > max_tokens:
        raise ValueError('Training sequence exceeds fixed bound; no image-token truncation')
    labels = completion_labels(before.input_ids[0].tolist(), batch.input_ids[0].tolist(), batch.attention_mask[0].tolist())
    forbidden = {processor.tokenizer.convert_tokens_to_ids(x) for x in ['<|image_pad|>', '<|video_pad|>', '<|vision_start|>', '<|vision_end|>']}
    if any(token in forbidden for token in labels if token != -100):
        raise ValueError('A supervised target contains visual control tokens')
    batch['labels'] = torch.tensor([labels], dtype=torch.long)
    return batch.to('cuda')


def add_adapter(model, config):
    c = config['train']
    model = get_peft_model(model, LoraConfig(r=c['rank'], lora_alpha=c['alpha'],
            lora_dropout=c['dropout'], target_modules=c['target_modules'], task_type='CAUSAL_LM', bias='none'))
    model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={'use_reentrant': False})
    model.enable_input_require_grads()
    model.config.use_cache = False
    trainable = [(name, p) for name, p in model.named_parameters() if p.requires_grad]
    if not trainable or any('lora_' not in name or 'visual' in name for name, _ in trainable):
        raise ValueError('Adapter target/freeze contract failed')
    return model, [p for _, p in trainable]


def input_rows(references):
    return [{k: r[k] for k in ('id', 'image', 'question', 'task') if k in r} for r in references]


def infer(model, processor, prompts, store, effective, destination, identity, progress=lambda message: None,
          baseline=False, style='short', deadline=None):
    """The inference input contract explicitly excludes references and answer labels."""
    for row in prompts:
        if set(row)-{'id', 'image', 'question', 'task'}:
            raise ValueError('Inference prompts contain labels or unsupported fields')
        if not isinstance(row['question'], str) or len(row['question']) > 1000:
            raise ValueError('Question exceeds declared input bound')
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    sidecar = destination.with_suffix('.identity.json')
    identity = {**identity, 'effective': effective, 'style': style,
                'input_sha256': hashlib.sha256(json.dumps(prompts, sort_keys=True).encode()).hexdigest()}
    if sidecar.exists():
        if json.loads(sidecar.read_text()) != identity:
            raise ValueError('Cannot append predictions for a different model/input protocol')
    else:
        if destination.exists(): raise ValueError('Prediction file has no identity receipt')
        save_json(sidecar, identity)
    existing = [json.loads(line) for line in destination.read_text().splitlines()] if destination.exists() else []
    completed = prediction_map(existing)
    if set(completed)-{str(r['id']) for r in prompts}:
        raise ValueError('Foreign saved prediction identity')
    pending = [r for r in prompts if str(r['id']) not in completed]
    was_training = model.training
    model.eval(); model.config.use_cache = True
    started = time.monotonic()
    try:
        with destination.open('a', encoding='utf-8') as stream, cached_vision(model, effective.get('vision_mode') == 'per_image_cache') as vision:
            for offset in range(0, len(pending), effective['batch_size']):
                if deadline and time.monotonic() >= deadline: raise TimeoutError('Campaign wall-time ceiling reached')
                group = pending[offset:offset+effective['batch_size']]
                begin = time.perf_counter()
                captions = any(r.get('task') == 'caption' for r in group)
                limit = effective['caption_max_new_tokens'] if captions else effective['max_new_tokens']
                try:
                    texts = [prompt_text(processor, r, style)[1] for r in group]
                    batch = processor(text=texts, images=[store.image(r['image']) for r in group], padding=True, return_tensors='pt').to('cuda')
                    if vision is not None:
                        vision.keys = [store.hashes[r['image']] for r in group]
                    torch.cuda.synchronize()
                    generation_started = time.perf_counter()
                    context = model.disable_adapter() if baseline and hasattr(model, 'peft_config') else nullcontext()
                    with torch.inference_mode(), context:
                        generated = model.generate(**batch, max_new_tokens=limit, do_sample=False,
                                                   temperature=None, top_p=None, top_k=None, use_cache=True,
                                                   num_beams=1, num_return_sequences=1)
                    torch.cuda.synchronize()
                    output = generated[:, batch.input_ids.shape[1]:]
                    answers = processor.batch_decode(output, skip_special_tokens=True)
                    eos = model.generation_config.eos_token_id
                    eos = set(eos if isinstance(eos, list) else [eos])
                    rows = []
                    for source, answer, tokens in zip(group, answers, output.tolist()):
                        ended = any(token in eos for token in tokens)
                        rows.append({'id': str(source['id']), 'image': source['image'], 'raw_answer': answer,
                                     'truncated': not ended and len(tokens) >= limit,
                                     'generated_tokens': next((i+1 for i, token in enumerate(tokens) if token in eos), len(tokens)),
                                     'seconds_per_question_batch_average': (time.perf_counter()-begin)/len(group),
                                     'generation_seconds_batch_average': (time.perf_counter()-generation_started)/len(group),
                                     'image_sha256': store.hashes[source['image']]})
                    del batch, generated, output
                except torch.cuda.OutOfMemoryError:
                    torch.cuda.empty_cache()
                    raise RuntimeError('Unexpected inference OOM; retain partial outputs without silently changing measured settings') from None
                except (OSError, ValueError, KeyError) as error:
                    rows = [{'id': str(r['id']), 'image': r['image'], 'raw_answer': '',
                             'error': type(error).__name__, 'truncated': False} for r in group]
                for row in rows:
                    stream.write(json.dumps(row)+'\n')
                    existing.append(row)
                stream.flush()
                if (offset//effective['batch_size']) % 20 == 0 or offset+len(group) == len(pending):
                    progress(f'{destination.name}: {len(existing)}/{len(prompts)} predictions; {time.monotonic()-started:.1f}s this phase')
    finally:
        if was_training:
            model.train(); model.config.use_cache = False
    return existing


def smoke(root, config, effective, output):
    """Discarded training-only feasibility adapter, never a selected candidate."""
    from .core import training_records
    root, output = Path(root), Path(output)
    output.mkdir(parents=True, exist_ok=False)
    local = root/'research/datasets/local/vqa-20261108'
    split = json.loads((local/'split-before-pixels.json').read_text())
    available = {p.name for p in (local/'images/train').glob('*.png')} & set(split['train'])
    records, _ = training_records(json.loads((local/'source/VRSBench_train.json').read_text()))
    rows, used = [], set()
    for row in records:
        if row['task'] == 'vqa' and row['image'] in available and row['image'] not in used:
            rows.append(row); used.add(row['image'])
            if len(rows) == 8: break
    if len(rows) < 8: raise ValueError('Wait for eight native training images before GPU smoke')
    store = ImageStore(directory=local/'images/train')
    model, processor, snapshot = load(config, effective)
    probes = input_rows(rows[:effective['batch_size']])
    predictions = infer(model, processor, probes, store, effective, output/'base-probe.jsonl',
                        {'purpose': 'training-only resource feasibility; not accuracy evaluation'}, print)
    torch.cuda.reset_peak_memory_stats()
    model, parameters = add_adapter(model, config)
    model.train()
    optimizer = torch.optim.AdamW(parameters, lr=config['train']['learning_rate'])
    losses = []
    before = [p.detach().clone() for p in parameters]
    start = time.monotonic()
    for row in rows:
        batch = supervise(processor, row, store, config['train']['max_sequence_tokens'])
        loss = model(**batch).loss
        if not torch.isfinite(loss): raise ValueError('Nonfinite training loss')
        loss.backward(); torch.nn.utils.clip_grad_norm_(parameters, 1.)
        optimizer.step(); optimizer.zero_grad(set_to_none=True)
        losses.append(float(loss.detach()))
        del loss, batch
    changed = sum(not torch.equal(old, new.detach()) for old, new in zip(before, parameters))
    if not changed: raise ValueError('No adapter tensor changed during real optimization')
    model.save_pretrained(output/'discarded-adapter')
    value = {'purpose': 'Eight real training updates and batch inference; discarded adapter, no VQA gain claim',
             'effective': effective, 'steps': len(rows), 'finite_losses': losses, 'updated_parameter_tensors': changed,
             'trainable_parameters': sum(p.numel() for p in parameters), 'seconds': time.monotonic()-start,
             'peak_allocated_GiB': torch.cuda.max_memory_allocated()/2**30,
             'gpu': torch.cuda.get_device_name(0), 'snapshot': snapshot,
             'training_only_images': sorted(used), 'batch_predictions': len(predictions)}
    save_json(output/'summary.json', value)
    print(json.dumps(value, indent=2), flush=True)
    return value


def profile(root, config, effective, output):
    from .core import balanced_rows, training_records
    root, output = Path(root), Path(output)
    output.mkdir(parents=True, exist_ok=False)
    local = root/'research/datasets/local/vqa-20261108'
    split = json.loads((local/'split-before-pixels.json').read_text())
    available = {p.name for p in (local/'images/train').glob('*.png')} & set(split['train'])
    records, _ = training_records(json.loads((local/'source/VRSBench_train.json').read_text()))
    rows = balanced_rows([r for r in records if r['task'] == 'vqa' and r['image'] in available], 32, config['seed'])
    if len(rows) < 32: raise ValueError('Not enough native training support for throughput probe')
    store = ImageStore(directory=local/'images/train')
    model, processor, _ = load(config, effective)
    torch.cuda.reset_peak_memory_stats()
    start = time.monotonic()
    predictions = infer(model, processor, input_rows(rows), store, effective,
                        output/'predictions.jsonl', {'purpose': 'Training-only throughput probe, no accuracy selection'}, print)
    elapsed = time.monotonic()-start
    value = {'purpose': 'Resource-only probe on training questions; not a VQA score', 'effective': effective,
             'n': len(predictions), 'seconds': elapsed, 'questions_per_second': len(predictions)/elapsed,
             'peak_allocated_GiB': torch.cuda.max_memory_allocated()/2**30,
             'truncated': sum(r['truncated'] for r in predictions),
             'total_generation_seconds': sum(r.get('generation_seconds_batch_average', 0) for r in predictions)}
    save_json(output/'summary.json', value)
    print(json.dumps(value, indent=2), flush=True)
    return value


def infer_pair(model, processor, prompts, store, effective, output, identity, progress=print, deadline=None):
    """Matched arms, immutable completed batches, and exact native vision reuse."""
    from .vision import native_batch_reuse
    import uuid
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    fingerprint = {**identity, 'effective': effective,
                   'input_sha256': hashlib.sha256(json.dumps(prompts, sort_keys=True).encode()).hexdigest()}
    receipt = output/'identity.json'
    if receipt.exists():
        if json.loads(receipt.read_text()) != fingerprint:
            raise ValueError('Paired evaluation identity changed')
    else:
        save_json(receipt, fingerprint)
    model.eval(); model.config.use_cache = True
    all_rows = {'base': [], 'candidate': []}
    reused, started = 0, time.monotonic()
    for offset in range(0, len(prompts), effective['batch_size']):
        if deadline and time.monotonic() >= deadline: raise TimeoutError('Campaign ceiling reached during paired inference')
        index = offset//effective['batch_size']
        directory = output/'batches'/f'{index:06d}'
        complete = directory/'complete.json'
        group = prompts[offset:offset+effective['batch_size']]
        if directory.exists() and not complete.exists():
            # Preserve incomplete attempts; rerun their original full batch shape.
            interrupted = output/'interrupted'/f'{index:06d}-{uuid.uuid4().hex[:8]}'
            interrupted.parent.mkdir(parents=True, exist_ok=True)
            if not interrupted.resolve().is_relative_to(output.resolve()): raise ValueError('Unsafe recovery target')
            directory.rename(interrupted)
        if complete.exists():
            hashes = json.loads(complete.read_text())['files']
            if any(sha256(directory/name) != digest for name, digest in hashes.items()):
                raise ValueError('Completed paired batch changed')
        else:
            directory.mkdir(parents=True, exist_ok=False)
            with native_batch_reuse(model) as memo:
                for arm in ('base', 'candidate'):
                    infer(model, processor, group, store, effective, directory/(arm+'.jsonl'),
                          {**identity, 'arm': arm, 'batch_index': index}, lambda message: None,
                          baseline=arm == 'base', deadline=deadline)
                reused += memo.reuses
            save_json(complete, {'questions': len(group), 'files': {
                      name: sha256(directory/name) for name in ('base.jsonl', 'candidate.jsonl')}})
        for arm in all_rows:
            values = [json.loads(line) for line in (directory/(arm+'.jsonl')).read_text().splitlines()]
            if set(prediction_map(values)) != {str(r['id']) for r in group}:
                raise ValueError('Completed paired batch is missing expected identities')
            all_rows[arm].extend(values)
        if index % 8 == 0 or offset+len(group) == len(prompts):
            progress(f'Paired predictions: {offset+len(group)}/{len(prompts)} each arm; {time.monotonic()-started:.1f}s')
    for arm, values in all_rows.items():
        target = output/(arm+'.jsonl')
        raw = ''.join(json.dumps(row)+'\n' for row in values)
        if target.exists():
            if target.read_text() != raw: raise ValueError('Completed aggregate predictions differ')
        else:
            target.write_text(raw, encoding='utf-8')
    save_json(output/'completion.json', {'n_each_arm': len(prompts), 'native_vision_reuses_this_invocation': reused,
              'seconds_this_invocation': time.monotonic()-started,
              'files': {arm+'.jsonl': sha256(output/(arm+'.jsonl')) for arm in all_rows}})
    return all_rows


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser(); p.add_argument('--output', type=Path, required=True)
    p.add_argument('--max-visual-tokens', type=int, default=512); p.add_argument('--batch-size', type=int, default=4)
    p.add_argument('--profile', action='store_true')
    args = p.parse_args()
    root = Path(__file__).resolve().parents[2]
    config = json.loads((root/'research/experiments/vqa-finetuning-20261108.json').read_text())
    effective = {**config['inference'], 'max_visual_tokens': args.max_visual_tokens,
                 'min_visual_tokens': args.max_visual_tokens//2, 'batch_size': args.batch_size}
    (profile if args.profile else smoke)(root, config, effective, args.output)
