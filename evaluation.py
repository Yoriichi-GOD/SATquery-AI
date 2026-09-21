"""Re-score saved development predictions only. Does not train or infer."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RAW = ROOT / 'ppt_handoff' / 'raw'
EVIDENCE = {
    'baseline': RAW / 'baseline_dev_predictions.jsonl',
    'adapter': RAW / 'adapted_dev_predictions.jsonl',
    'development-inputs': RAW / 'dev.jsonl',
    'manifest': ROOT / 'results' / 'learning_manifest.json',
    'experiment': ROOT / 'results' / 'pilot-v1.json',
    'scoring': Path(__file__),
    'protocol': ROOT / 'scripts' / 'train_pilot.py',
    'diagnostic': RAW / 'diagnostic-baseline_summary.json',
    'diagnostic-manifest': RAW / 'diagnostic-manifest_metadata.json',
}


def score(rows):
    scored = []
    for row in rows:
        clean = ' '.join(row['prediction'].strip().lower().split()).rstrip(' .!?')
        valid = clean in (['rural', 'urban'] if row['category'] == 'rural_urban' else ['yes', 'no'])
        scored.append(dict(row, correct=clean == row['answer'].lower(), valid_format=valid))
    summary = dict(correct=sum(r['correct'] for r in scored), total=len(scored),
                   invalid_format=sum(not r['valid_format'] for r in scored), per_category={})
    for category in ['rural_urban', 'presence', 'comp']:
        subset = [r for r in scored if r['category'] == category]
        summary['per_category'][category] = dict(correct=sum(r['correct'] for r in subset), total=len(subset))
    return summary, scored


def development():
    rows = {key: [json.loads(line) for line in EVIDENCE[key].read_text().splitlines()] for key in ['baseline', 'adapter']}
    base, b = score(rows['baseline'])
    adapter, a = score(rows['adapter'])
    identity = ['question_id', 'image_id', 'image_sha256', 'question', 'answer', 'category', 'source_scene', 'split']
    if len(b) != len(a) or len({r['question_id'] for r in b}) != len(b):
        raise ValueError('Development predictions are not a unique paired run.')
    if any(any(x[k] != y[k] for k in identity) for x, y in zip(b, a)):
        raise ValueError('Development prediction identities do not align.')
    saved = json.loads(EVIDENCE['experiment'].read_text())
    if base != saved['baseline_dev'] or adapter != saved['adapted_dev']:
        raise ValueError('Re-scored predictions disagree with the preserved experiment. Comparison withheld.')
    manifest = json.loads(EVIDENCE['manifest'].read_text())
    if hashlib.sha256(EVIDENCE['development-inputs'].read_bytes()).hexdigest() != manifest['dev']['sha256']:
        raise ValueError('Development inputs disagree with the frozen manifest hash.')
    inputs = [json.loads(line) for line in EVIDENCE['development-inputs'].read_text().splitlines()]
    if len(inputs) != len(b) or any(any(x[k] != y[k] for k in identity) for x, y in zip(inputs, b)):
        raise ValueError('Predictions do not correspond to the frozen development inputs.')
    if saved['train_manifest'] != manifest['train']['sha256']:
        raise ValueError('Training manifest does not match the saved experiment.')
    if len(b) != manifest['dev']['questions'] or len({r['image_id'] for r in b}) != manifest['dev']['images']:
        raise ValueError('Development sample size disagrees with the manifest.')
    regressions = [dict(question_id=x['question_id'], question=x['question'], reference=x['answer'],
                        original=x['prediction'], adapter=y['prediction'], category=x['category'])
                   for x, y in zip(b, a) if x['correct'] and not y['correct']]
    return dict(label='DEVELOPMENT ONLY', run='lora-pilot-v1', baseline_dev=base, adapted_dev=adapter,
                questions=len(b), images=len({r['image_id'] for r in b}), source_scenes=len({r['source_scene'] for r in b}),
                regressions=regressions, gains=sum(not x['correct'] and y['correct'] for x, y in zip(b, a)),
                evidence={k: dict(url=f'/api/evidence/{k}', sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for k, p in EVIDENCE.items()},
                protocol=dict(visual_tokens=saved['visual_tokens'], max_new_tokens=16, do_sample=False,
                              scoring='Lowercase, collapse whitespace, strip trailing space/dot/exclamation/question mark; exact label match. Invalid formats count as incorrect.'),
                majority_correct=sum(max(v for k, v in manifest['dev']['answers'].items() if k.startswith(c+':')) for c in base['per_category']))
