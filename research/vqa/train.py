"""One registered supervised candidate, selected only on official-training holdout."""
import gc
import json
import math
from pathlib import Path
import random
import time

import torch

from .core import balanced_rows, paired_gain, save_json, score, sha256
from .gpu import add_adapter, infer, input_rows, load, prompt_text, supervise


def candidate_gate(baseline, candidate, rule):
    decline = []
    for name, control in baseline['per_category'].items():
        if control['n'] < rule['bucket_min_questions']:
            continue
        value = candidate['per_category'][name]
        change = value['correct']/value['n']-control['correct']/control['n']
        if change < -rule['max_bucket_decline']:
            decline.append({'bucket': name, 'gain': change, 'n': value['n']})
    gain = candidate['accuracy']-baseline['accuracy']
    return {'passed': gain >= rule['required_gain'] and not decline,
            'gain': gain, 'bucket_regressions': decline,
            'scope': 'Validation point-estimate gate; not independent scientific or production approval'}


def fit(root, config, effective, corpus, store, output, progress, deadline):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    model, processor, snapshot = load(config, effective)
    common = {'model': config['model'], 'protocol_sha256': config['config_sha256'],
              'phase': 'heldout-official-training-validation'}
    dev = corpus['dev']
    control = infer(model, processor, input_rows(dev), store, effective, output/'base-dev.jsonl',
                    common, progress, deadline=deadline)
    baseline = score(dev, control)
    save_json(output/'base-dev-score.json', baseline)
    progress('Baseline validation complete: '+json.dumps({k: baseline[k] for k in ('n', 'correct', 'accuracy', 'truncated')}))
    diagnostic = balanced_rows(dev, 64, config['seed'])
    raw = infer(model, processor, input_rows(diagnostic), store, effective, output/'raw-prompt-dev.jsonl',
                common, progress, style='raw', deadline=deadline)
    diagnostic_ids = {r['id'] for r in diagnostic}
    save_json(output/'prompt-diagnostic.json', {'scope': 'Same 64 validation questions/settings; prompt effect, not fine-tuning gain',
              'raw': score(diagnostic, raw), 'short': score(diagnostic, [p for p in control if p['id'] in diagnostic_ids])})

    # Conservatively screen sequence length using the maximum possible image-token count.
    # Targets that do not fit are excluded and counted, never silently truncated.
    usable, excluded = [], []
    for row in corpus['train']:
        user, _ = prompt_text(processor, row)
        text = processor.apply_chat_template([user, {'role': 'assistant', 'content': [
                   {'type': 'text', 'text': row['reference']}]}], tokenize=False, add_generation_prompt=False)
        upper = len(processor.tokenizer(text).input_ids)+effective['max_visual_tokens']-1
        if upper <= config['train']['max_sequence_tokens']:
            usable.append(row)
        else:
            excluded.append({'id': row['id'], 'upper_sequence_tokens': upper})
    if len(usable) < min(2048, len(corpus['train'])):
        raise ValueError('Too little training support within fixed sequence bounds')
    save_json(output/'token-audit.json', {'eligible_rows': len(usable), 'excluded': excluded,
              'rule': 'Text tokens plus maximum visual tokens must fit; no visual/target truncation'})

    model, parameters = add_adapter(model, config)
    model.train(); c = config['train']
    optimizer = torch.optim.AdamW(parameters, lr=c['learning_rate'], weight_decay=c['weight_decay'])
    optimizer.zero_grad(set_to_none=True)
    best, checkpoints, losses, micro, step = None, [], [], 0, 0
    torch.cuda.reset_peak_memory_stats()
    start = time.monotonic()

    def checkpoint():
        nonlocal best
        directory = output/f'step-{step:05d}'
        directory.mkdir(exist_ok=False)
        model.save_pretrained(directory/'adapter')
        adapter_hash = sha256(directory/'adapter/adapter_model.safetensors')
        predictions = infer(model, processor, input_rows(dev), store, effective, directory/'dev.jsonl',
                      {**common, 'optimizer_step': step, 'adapter_sha256': adapter_hash}, progress, deadline=deadline)
        metric = score(dev, predictions)
        record = {'optimizer_step': step, 'micro_steps': micro, 'adapter_sha256': adapter_hash,
                  'adapter': str((directory/'adapter').resolve()), 'score': metric,
                  'seconds': time.monotonic()-start}
        save_json(directory/'checkpoint.json', record)
        checkpoints.append(record)
        if best is None or metric['accuracy'] > best['score']['accuracy']:
            best = record
        progress('Validation checkpoint: '+json.dumps({'step': step, 'accuracy': metric['accuracy'],
                  'correct': metric['correct'], 'n': metric['n']}))

    with (output/'training.jsonl').open('x') as stream:
        for epoch in range(c['max_epochs']):
            order = list(usable)
            random.Random(config['seed']+epoch).shuffle(order)
            for row in order:
                if time.monotonic() >= deadline:
                    raise TimeoutError('Campaign ceiling reached during training; checkpoint artifacts retained')
                batch = supervise(processor, row, store, c['max_sequence_tokens'])
                loss = model(**batch).loss
                if not torch.isfinite(loss): raise ValueError('Nonfinite training loss')
                scalar = float(loss.detach())
                (loss/c['gradient_accumulation']).backward()
                losses.append(scalar); micro += 1
                del loss, batch
                if micro % c['gradient_accumulation']:
                    continue
                step += 1
                if step <= c['warmup_steps']:
                    fraction = step/max(1, c['warmup_steps'])
                else:
                    phase = (step-c['warmup_steps'])/max(1, c['max_optimizer_steps']-c['warmup_steps'])
                    fraction = .1+.9*.5*(1+math.cos(math.pi*min(1., phase)))
                for group in optimizer.param_groups: group['lr'] = c['learning_rate']*fraction
                norm = torch.nn.utils.clip_grad_norm_(parameters, c['gradient_clip'])
                if not torch.isfinite(norm): raise ValueError('Nonfinite adapter gradient norm')
                optimizer.step(); optimizer.zero_grad(set_to_none=True)
                item = {'optimizer_step': step, 'micro_steps': micro, 'epoch': epoch+1,
                        'loss': sum(losses)/len(losses), 'learning_rate': optimizer.param_groups[0]['lr'],
                        'gradient_norm': float(norm), 'seconds': time.monotonic()-start,
                        'peak_allocated_GiB': torch.cuda.max_memory_allocated()/2**30}
                stream.write(json.dumps(item)+'\n'); stream.flush(); losses.clear()
                if step % 16 == 0: progress('Training: '+json.dumps(item))
                if step in c['checkpoint_steps']:
                    checkpoint()
                if step >= c['max_optimizer_steps']: break
            if step >= c['max_optimizer_steps']: break
    if not checkpoints or checkpoints[-1]['optimizer_step'] != step:
        checkpoint()
    if best is None: raise RuntimeError('No validated checkpoint')
    best_predictions = [json.loads(x) for x in (Path(best['adapter']).parent/'dev.jsonl').read_text().splitlines()]
    selection = {'selected': best, 'baseline': baseline, 'checkpoints': checkpoints,
                 'gate': candidate_gate(baseline, best['score'], config['selection']),
                 'paired_validation': paired_gain(dev, control, best_predictions),
                 'optimizer_steps': step, 'micro_steps': micro, 'eligible_training_rows': len(usable),
                 'unapplied_tail_micro_steps': micro % c['gradient_accumulation'],
                 'trainable_parameters': sum(p.numel() for p in parameters),
                 'peak_allocated_GiB': torch.cuda.max_memory_allocated()/2**30,
                 'snapshot': snapshot, 'protocol_sha256': config['config_sha256'],
                 'effective': effective, 'final_evaluation_opened': False,
                 'production_defaults_changed': False}
    save_json(output/'selection.json', selection)
    del optimizer, parameters, model, processor
    gc.collect(); torch.cuda.empty_cache()
    return selection
