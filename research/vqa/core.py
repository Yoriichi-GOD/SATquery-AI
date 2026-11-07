"""Data boundaries and fixed diagnostic scoring, independent of GPU libraries."""
from collections import Counter, defaultdict, deque
import hashlib
import json
import math
from pathlib import Path
import random
import re
import unicodedata

MODEL_ID = 'AdaptLLM/remote-sensing-Qwen2-VL-2B-Instruct'
MODEL_REVISION = '7f5dd71bf0f40c282193d50160e848a387a08ffe'
DATASET_REVISION = '6cee2968fd752a6d51c6cb2d18dded2bc0baa218'
ANSWER_INSTRUCTION = ('Answer using only a brief phrase, or a number for a count. '
                      'Do not explain. If the image cannot establish the answer, answer unknown.')
SCORER_VERSION = 'vrs-normalised-whole-answer-v1'


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def save_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n', encoding='utf-8')
    temporary.replace(path)


def stable_key(seed, text):
    return hashlib.sha256(f'{seed}/{text}'.encode()).hexdigest()


def image_name(value):
    if not isinstance(value, str) or not re.fullmatch(r'[A-Za-z0-9_-]+\.png', value):
        raise ValueError('Expected a plain official PNG filename')
    return value


def scene_group(name):
    # Filename provenance group, not a claim of geographic independence.
    return image_name(name).split('_')[0].removesuffix('.png')


def normalise_answer(value, aliases=True):
    value = ' '.join(unicodedata.normalize('NFKC', str(value)).lower().split())
    value = value.rstrip(' .!?')
    if aliases:
        value = re.sub(r'[-_]+', ' ', value)
        value = ' '.join(value.split())
        words = ('zero one two three four five six seven eight nine ten eleven twelve '
                 'thirteen fourteen fifteen sixteen seventeen eighteen nineteen twenty').split()
        if value in words:
            value = str(words.index(value))
    return value


def question_bucket(question):
    """Sampling heuristic only; final benchmark uses native category annotations."""
    q = question.lower()
    for name, pattern in [
        ('quantity', r'\bhow many\b|\bnumber of\b'),
        ('colour', r'\bcolou?r\b'), ('shape', r'\bshape\b'),
        ('size', r'\b(?:larger|smaller|biggest|smallest|size|bigger)\b'),
        ('direction', r'\b(?:direction|facing|oriented|orientation)\b'),
        ('position', r'\b(?:where|position|located|leftmost|rightmost|topmost|bottommost)\b'),
        ('presence', r'^(?:is|are|does|do|can you see)\b'),
        ('scene', r'\b(?:scene|landscape|rural|urban|surrounds)\b'),
        ('category', r'\b(?:type|kind|main structure|main object)\b'),
    ]:
        if re.search(pattern, q):
            return name
    return 'other'


def training_records(raw_rows):
    """Accept only two-turn VQA/caption training rows; quarantine conflicting targets."""
    candidates = []
    rejected = Counter()
    for original_index, row in enumerate(raw_rows):
        name = image_name(row['image'])
        turns = row.get('conversations', [])
        if len(turns) != 2 or [x.get('from') for x in turns] != ['human', 'gpt']:
            raise ValueError('Unexpected training conversation schema')
        text, answer = turns[0]['value'], turns[1]['value']
        if not isinstance(text, str) or not isinstance(answer, str):
            raise ValueError('Question and target must be strings')
        match = re.fullmatch(r'<image>\s*\[(vqa|caption|refer)\]\s*(.+)', text, re.S)
        if not match:
            raise ValueError('Unexpected training task prefix')
        task, question = match.groups()
        if task == 'refer':
            rejected['grounding_out_of_scope'] += 1
            continue
        question = re.sub(r'\s*\.?\s*A short answer to the question is\s*$', '', question, flags=re.I).strip()
        question = re.sub(r'\?\.$', '?', question)
        if re.search(r'\b(?:source of (?:the|this) image|image (?:source|provider)|'
                     r'which (?:company|satellite)|who (?:provided|captured)|'
                     r'acquisition date|exact (?:latitude|longitude|resolution))\b', question, re.I):
            rejected['unobservable_metadata_question'] += 1
            continue
        if not question or not answer.strip() or len(question) > 1000 or len(answer) > 2400:
            rejected['empty_or_oversized_text'] += 1
            continue
        identity = stable_key('vrs-train', f'{name}/{task}/{question}')[:24]
        candidates.append(dict(id=identity, image=name, group=scene_group(name), task=task,
                               question=question, reference=answer.strip(),
                               category=question_bucket(question) if task == 'vqa' else 'caption',
                               original_index=original_index, source_split='train'))
    keyed = defaultdict(list)
    for row in candidates:
        keyed[(row['image'], row['task'], normalise_answer(row['question'], False))].append(row)
    clean = []
    for values in keyed.values():
        if len({normalise_answer(v['reference'], False) for v in values}) != 1:
            rejected['conflicting_targets'] += len(values)
        else:
            clean.append(values[0])
            rejected['exact_duplicate_rows'] += len(values) - 1
    return clean, dict(rejected)


def split_images(rows, seed, train_count, dev_count, max_train_per_group=4):
    names = sorted({r['image'] for r in rows}, key=lambda n: stable_key(seed, n))
    train, dev, used = [], [], Counter()
    for name in names:
        group = scene_group(name)
        validation = int(stable_key(seed, group)[:8], 16) % 8 == 0
        destination, limit = (dev, 1) if validation else (train, max_train_per_group)
        count = dev_count if validation else train_count
        if len(destination) < count and used[group] < limit:
            destination.append(name)
            used[group] += 1
    if len(train) != train_count or len(dev) != dev_count:
        raise ValueError('Not enough provenance groups for the frozen split sizes')
    assert not {scene_group(n) for n in train} & {scene_group(n) for n in dev}
    return train, dev


def balanced_rows(rows, maximum, seed):
    buckets = defaultdict(list)
    for row in rows:
        buckets[row['category']].append(row)
    queues = {k: deque(sorted(v, key=lambda r: stable_key(seed, r['id']))) for k, v in buckets.items()}
    selected = []
    while len(selected) < maximum and any(queues.values()):
        for key in sorted(queues):
            if queues[key] and len(selected) < maximum:
                selected.append(queues[key].popleft())
    return selected


def verify_disjoint(train, dev):
    for key in ('image', 'group', 'image_sha256'):
        a, b = {r[key] for r in train}, {r[key] for r in dev}
        if a & b:
            raise ValueError(f'Train/dev overlap in {key}')
    return {'train_images': len({r['image'] for r in train}),
            'dev_images': len({r['image'] for r in dev}),
            'train_groups': len({r['group'] for r in train}),
            'dev_groups': len({r['group'] for r in dev})}


def prediction_map(predictions):
    result = {}
    for row in predictions:
        identity = str(row['id'])
        if identity in result:
            raise ValueError('Duplicate prediction identity')
        result[identity] = row
    return result


def completion_labels(prefix, full, attention):
    """Supervise only the completed assistant turn; never image, user or pad tokens."""
    if full[:len(prefix)] != prefix or len(full) != len(attention):
        raise ValueError('Chat prefix/attention does not match the supervised sequence')
    labels = [-100 if i < len(prefix) or not attention[i] else token for i, token in enumerate(full)]
    if not any(value != -100 for value in labels):
        raise ValueError('No assistant target remains')
    return labels


def correct(prediction, reference, aliases=True):
    return bool(prediction and not prediction.get('error') and not prediction.get('truncated')
                and prediction.get('raw_answer', '').strip()
                and normalise_answer(prediction['raw_answer'], aliases) == normalise_answer(reference, aliases))


def score(references, predictions):
    pred = prediction_map(predictions)
    identities = {str(r['id']) for r in references}
    if len(identities) != len(references) or set(pred) - identities:
        raise ValueError('Duplicate references or foreign prediction identities')
    categories = defaultdict(lambda: {'n': 0, 'correct': 0})
    result = dict(n=len(references), completed=0, correct=0, strict_correct=0, missing=0, errors=0, truncated=0)
    for row in references:
        p = pred.get(str(row['id']))
        hit = correct(p, row['reference'])
        result['correct'] += hit
        result['strict_correct'] += correct(p, row['reference'], False)
        result['missing'] += p is None
        result['errors'] += bool(p and p.get('error'))
        result['truncated'] += bool(p and p.get('truncated'))
        result['completed'] += bool(p and not p.get('error') and p.get('raw_answer', '').strip())
        categories[row['category']]['n'] += 1
        categories[row['category']]['correct'] += hit
    result['accuracy'] = result['correct'] / result['n'] if result['n'] else None
    result['per_category'] = dict(categories)
    result['scorer'] = SCORER_VERSION
    result['official_gpt_score'] = None
    return result


def paired_gain(references, baseline, candidate, seed=20261108, repetitions=1000):
    a, b = prediction_map(baseline), prediction_map(candidate)
    groups = defaultdict(lambda: [0, 0])
    for row in references:
        key = row.get('group', scene_group(row['image']))
        groups[key][0] += int(correct(b.get(str(row['id'])), row['reference'])) - int(correct(a.get(str(row['id'])), row['reference']))
        groups[key][1] += 1
    if not groups:
        raise ValueError('No paired support')
    rng = random.Random(seed)
    values = list(groups.values())
    draws = []
    for _ in range(repetitions):
        selected = rng.choices(values, k=len(values))
        draws.append(sum(v[0] for v in selected) / sum(v[1] for v in selected))
    draws.sort()
    return {'gain': sum(v[0] for v in values) / sum(v[1] for v in values),
            'ci95': [draws[math.floor(.025*(repetitions-1))], draws[math.ceil(.975*(repetitions-1))]],
            'groups': len(values), 'repetitions': repetitions, 'seed': seed,
            'scope': 'Filename-source-group bootstrap; not proven geographic independence'}
