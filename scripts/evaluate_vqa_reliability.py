"""Frozen paired diagnostic; no training, prompt search, or test-based selection."""
import collections
import hashlib
import json
from pathlib import Path
import random
import re
import sys
import time
import zipfile
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from vqa_policy import VERSION, effective_question
from routing import route
OUT = ROOT / 'results/reliability-20260907/vqa'
OUT.mkdir(parents=True, exist_ok=True)
DATA = Path('/root/satquery/evaluation')
MODEL = 'AdaptLLM/remote-sensing-Qwen2-VL-2B-Instruct'
REVISION = '7f5dd71bf0f40c282193d50160e848a387a08ffe'

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

manifest_path = OUT / 'frozen-cases.json'
if not manifest_path.exists():
    rng = random.Random(20260907)
    questions = [r for r in json.loads((DATA / 'LR_split_test_questions.json').read_text())['questions'] if r.get('active')]
    answers = {r['id']: r for r in json.loads((DATA / 'LR_split_test_answers.json').read_text())['answers'] if r.get('active')}
    images = {r['id']: r for r in json.loads((DATA / 'LR_split_test_images.json').read_text())['images'] if r.get('active')}
    previous = {json.loads(line)['image_id'] for line in (DATA / 'eval_v1.jsonl').read_text().splitlines()}
    training = [json.loads(line) for split in ('train', 'dev') for line in Path(f'/root/satquery/data/{split}.jsonl').read_text().splitlines()]
    train_scenes = {r['source_scene'] for r in training}
    train_hashes = {r['image_sha256'] for r in training}
    used = set(previous)
    cases = []
    # Presence includes some shape/size questions outside the app allowlist.
    # Keep that fact in the results, not silently expand public functionality.
    for category, answer in [('rural_urban', 'rural'), ('rural_urban', 'urban'), ('presence', 'no'), ('presence', 'yes')]:
        pool = [q for q in questions if q['type'] == category and answers[q['answers_ids'][0]]['answer'] == answer]
        rng.shuffle(pool)
        selected = []
        for q in pool:
            if q['img_id'] in used:
                continue
            if category == 'presence' and re.search(r'commercial|residential|left|right|top|bottom|medium|small|large', q['question']):
                continue
            source_scene = images[q['img_id']]['original_name'].rsplit('_', 1)[0]
            assert source_scene not in train_scenes
            question = 'Is this image rural or urban?' if category == 'rural_urban' else q['question']
            selected.append(dict(id=f'qa-{q["id"]}', question_id=q['id'], image_id=q['img_id'],
                                 question=question, original_question=q['question'], reference=answer,
                                 category=category, source_scene=source_scene,
                                 app_supported=route(question)['tool'] == 'vqa'))
            used.add(q['img_id'])
            if len(selected) == 6:
                break
        if len(selected) != 6:
            raise RuntimeError(f'Insufficient examples for {category}/{answer}: {len(selected)}')
        cases.extend(selected)
    with zipfile.ZipFile(DATA / 'Images_LR.zip') as z:
        for case in cases:
            target = OUT / f'image-{case["image_id"]}.png'
            with z.open(f'Images_LR/{case["image_id"]}.tif') as handle:
                Image.open(handle).convert('RGB').save(target)
            case.update(image=str(target), image_sha256=digest(target))
            assert case['image_sha256'] not in train_hashes
    # Qualitative cases are fixed before looking at either model's answers.
    descriptions = [dict(id=f'description-{c["image_id"]}', image=c['image'], image_sha256=c['image_sha256'],
                         category='description', question='Describe the major visible features briefly.',
                         reference=None, app_supported=True) for c in cases[:2] + cases[6:8]]
    import geo
    original_scene = Path('/root/satquery/scenes/dehradun-sentinel2-20211125.tif')
    preview, _ = geo.ingest(original_scene.read_bytes(), OUT / 'dehradun-copy.tif')
    preview.save(OUT / 'dehradun.png')
    descriptions.append(dict(id='description-dehradun', image=str(OUT / 'dehradun.png'),
                             image_sha256=digest(OUT / 'dehradun.png'), category='description',
                             question='Describe the major visible features briefly.', reference=None, app_supported=True))
    for name in ('punjab-farmland', 'bengaluru-lake-city', 'jaisalmer-arid', 'sundarbans-coast', 'assam-monsoon'):
        image_path = OUT.parent / 'scenes' / name / 'rgb.png'
        if not image_path.exists():
            raise RuntimeError(f'Finish fetching before freezing: {image_path}')
        descriptions.append(dict(id=f'description-{name}', image=str(image_path), image_sha256=digest(image_path),
                                 category='description', question='Describe the major visible features briefly.',
                                 reference=None, app_supported=True))
    cases.extend(descriptions)
    manifest = dict(seed=20260907, model=MODEL, revision=REVISION, policy_version=VERSION,
                    policy_source_sha256=digest(ROOT / 'vqa_policy.py'), cases=cases,
                    scope='24 QA on images excluded from prior 60-image diagnostic and adapter train/dev. '
                          'Official test source scene overlaps prior diagnostic; upstream pretraining exposure unknown. '
                          'Balanced custom subset, noisy published labels; not full benchmark or 90% quality claim. '
                          '10 descriptions require visual review and have no reference accuracy score. '
                          'Some presence questions are offline diagnostics outside the app allowlist.',
                    prior_evaluation_sha256=digest(DATA / 'eval_v1.jsonl'))
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding='utf-8')
manifest = json.loads(manifest_path.read_text())
assert manifest['policy_source_sha256'] == digest(ROOT / 'vqa_policy.py'), 'Do not tune against frozen cases'
print('Frozen', len(manifest['cases']), 'cases', digest(manifest_path), flush=True)

import torch
from huggingface_hub import snapshot_download
from transformers import AutoProcessor, Qwen2VLForConditionalGeneration
path = snapshot_download(MODEL, revision=REVISION, local_files_only=True)
processor = AutoProcessor.from_pretrained(path, use_fast=False, min_pixels=256*28*28, max_pixels=512*28*28,
                                         size={'shortest_edge': 256*28*28, 'longest_edge': 512*28*28})
model = Qwen2VLForConditionalGeneration.from_pretrained(path, torch_dtype=torch.bfloat16,
            device_map={'': 'cuda:0'}, attn_implementation='sdpa').eval()
pred_path = OUT / 'paired-predictions.jsonl'
done = {(r['id'], r['policy']) for r in (json.loads(line) for line in pred_path.read_text().splitlines())} if pred_path.exists() else set()
for case in manifest['cases']:
    for policy in ('original', VERSION):
        if (case['id'], policy) in done:
            continue
        assert digest(Path(case['image'])) == case['image_sha256']
        question = case['question'] if policy == 'original' else effective_question(case['question'])
        messages = [{'role': 'user', 'content': [{'type': 'image'}, {'type': 'text', 'text': question}]}]
        prompt = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        inputs = processor(text=[prompt], images=[Image.open(case['image']).convert('RGB')], return_tensors='pt').to('cuda')
        torch.cuda.synchronize()
        started = time.perf_counter()
        with torch.inference_mode():
            output = model.generate(**inputs, max_new_tokens=128, do_sample=False, temperature=None, top_p=None, top_k=None)
        torch.cuda.synchronize()
        answer = processor.batch_decode(output[:, inputs.input_ids.shape[1]:], skip_special_tokens=True)[0]
        normalized = re.sub(r'[.!?]+$', '', ' '.join(answer.lower().strip().split()))
        row = dict(**case, policy=policy, effective_question=question, answer=answer,
                   seconds=round(time.perf_counter()-started, 3),
                   generated_tokens=int(output.shape[1]-inputs.input_ids.shape[1]), max_new_tokens=128,
                   exact_correct=normalized == case['reference'] if case['reference'] is not None else None,
                   abstained='cannot determine' in normalized)
        with pred_path.open('a', encoding='utf-8') as handle:
            handle.write(json.dumps(row) + '\n')
        print(case['id'], policy, repr(answer), flush=True)

rows = [json.loads(line) for line in pred_path.read_text().splitlines()]
summary = dict(scope=manifest['scope'], manifest_sha256=digest(manifest_path), predictions_sha256=digest(pred_path), policies={})
for policy in ('original', VERSION):
    group = [r for r in rows if r['policy'] == policy and r['reference'] is not None]
    summary['policies'][policy] = dict(total=len(group), correct=sum(r['exact_correct'] for r in group),
        abstentions=sum(r['abstained'] for r in group),
        by_category={category: dict(total=sum(r['category']==category for r in group),
                                   correct=sum(r['exact_correct'] for r in group if r['category']==category))
                     for category in ('rural_urban', 'presence')},
        app_supported_total=sum(r['app_supported'] for r in group),
        app_supported_correct=sum(r['exact_correct'] for r in group if r['app_supported']))
(OUT / 'paired-summary.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
print(json.dumps(summary, indent=2), flush=True)
