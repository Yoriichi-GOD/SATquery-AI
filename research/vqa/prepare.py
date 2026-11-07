"""Prepare only official training support, before opening final evaluation labels."""
from collections import Counter
import json
from pathlib import Path

from .acquire import acquire_images
from .core import (balanced_rows, save_json, sha256, split_images, stable_key,
                   training_records, verify_disjoint)


def prepare(root, config, budget, progress=print):
    root = Path(root)
    local = root/'research/datasets/local/vqa-20261108'
    source = local/'source/VRSBench_train.json'
    corpus_path = local/'corpus.json'
    if corpus_path.exists():
        corpus = json.loads(corpus_path.read_text())
        if corpus['config_sha256'] != config['config_sha256']:
            raise ValueError('Prepared corpus uses another protocol')
        for receipt in corpus['images'].values():
            if sha256(receipt['path']) != receipt['sha256']:
                raise ValueError('Prepared native image changed')
        return corpus
    raw_rows = json.loads(source.read_text())
    rows, rejected = training_records(raw_rows)
    train_names, dev_names = split_images(rows, config['seed'], config['data']['train_images'], config['data']['dev_images'])
    save_json(local/'split-before-pixels.json', {'seed': config['seed'], 'train': train_names,
              'dev': dev_names, 'source_sha256': sha256(source), 'selection': 'Filename/provenance hash only; no model scores'})
    images = acquire_images(train_names+dev_names, local/'images/train', budget, progress)
    # Keep dev fixed. Remove training duplicates of it, and collapse duplicate native images.
    kept_dev, seen, duplicate_dev = [], set(), []
    for name in dev_names:
        digest = images[name]['sha256']
        if digest in seen: duplicate_dev.append(name)
        else: kept_dev.append(name); seen.add(digest)
    kept_train, duplicate_train = [], []
    for name in train_names:
        digest = images[name]['sha256']
        if digest in seen: duplicate_train.append(name)
        else: kept_train.append(name); seen.add(digest)
    training = [r for r in rows if r['image'] in set(kept_train)]
    train = balanced_rows([r for r in training if r['task'] == 'vqa'], config['data']['train_vqa_rows'], config['seed'])
    train += balanced_rows([r for r in training if r['task'] == 'caption'], config['data']['train_caption_rows'], config['seed'])
    dev = [r for r in rows if r['image'] in set(kept_dev) and r['task'] == 'vqa']
    captions = balanced_rows([r for r in rows if r['image'] in set(kept_dev) and r['task'] == 'caption'], 32, config['seed'])
    for row in train+dev+captions:
        row['image_path'] = images[row['image']]['path']
        row['image_sha256'] = images[row['image']]['sha256']
    if len(train) < 2048 or len(dev) < 200:
        raise ValueError('Insufficient eligible support after fixed quality filters')
    split = verify_disjoint(train, dev+captions)
    train.sort(key=lambda r: stable_key(config['seed'], r['id']))
    corpus = {'config_sha256': config['config_sha256'], 'source_sha256': sha256(source),
              'train': train, 'dev': dev, 'dev_captions': captions, 'images': images,
              'split': split, 'rejected_rows': rejected,
              'duplicate_pixel_images_removed': {'train': duplicate_train, 'dev': duplicate_dev}}
    save_json(corpus_path, corpus)
    public = {k: corpus[k] for k in ('config_sha256', 'source_sha256', 'split', 'rejected_rows', 'duplicate_pixel_images_removed')}
    public.update(corpus_sha256=sha256(corpus_path), train_rows=len(train), dev_vqa_rows=len(dev),
                  dev_caption_rows=len(captions), train_buckets=dict(Counter(r['category'] for r in train)),
                  dev_buckets=dict(Counter(r['category'] for r in dev)),
                  sampling_categories='Question-pattern buckets, not native official evaluation categories',
                  upstream_checkpoint_exposure='Not ruled out by local split checks',
                  raw_images_committed=False)
    save_json(root/'research/results/vqa-finetuning-20261108/DATA_AUDIT.json', public)
    return corpus


if __name__ == '__main__':
    from .acquire import Budget
    root = Path(__file__).resolve().parents[2]
    protocol = root/'research/experiments/vqa-finetuning-20261108.json'
    config = json.loads(protocol.read_text())
    config['config_sha256'] = sha256(protocol)
    budget = Budget(config['limits']['max_download_bytes'])
    def report(message):
        print(message, flush=True)
        save_json(root/'.runtime/vqa-20261108/data-status.json', {'message': message, 'transferred_bytes': budget.bytes})
    corpus = prepare(root, config, budget, report)
    save_json(root/'.runtime/vqa-20261108/data-status.json', {'state': 'complete',
              'train_rows': len(corpus['train']), 'dev_rows': len(corpus['dev']), 'transferred_bytes': budget.bytes})
    print('DATA_COMPLETE', len(corpus['train']), len(corpus['dev']), flush=True)
