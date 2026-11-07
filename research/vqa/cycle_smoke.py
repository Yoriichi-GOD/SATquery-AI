"""Discarded, training-only closed-loop checkpoint/save/reload preflight."""
import json
from pathlib import Path
import time
from peft import PeftModel

from .core import save_json, sha256
from .gpu import ImageStore, infer, input_rows, load
from .train import fit


def main():
    root = Path(__file__).resolve().parents[2]
    path = root/'research/experiments/vqa-finetuning-20261108.json'
    config = json.loads(path.read_text()); config['config_sha256'] = sha256(path)
    config['train'].update(max_optimizer_steps=2, max_epochs=1, checkpoint_steps=[1, 2])
    local = root/'research/datasets/local/vqa-20261108'
    corpus = json.loads((local/'corpus.json').read_text())
    chosen, images = [], set()
    for row in corpus['train']:
        if row['task'] != 'vqa' or row['image'] in images: continue
        chosen.append(row); images.add(row['image'])
        if len(chosen) == 24: break
    tiny = {'train': chosen[:16], 'dev': chosen[16:24]}
    effective = {**config['inference'], 'vision_mode': 'native'}
    output = root/'.runtime/vqa-20261108/closed-loop-smoke-v1'
    store = ImageStore(directory=local/'images/train', receipts=corpus['images'])
    selection = fit(root, config, effective, tiny, store, output, print, time.monotonic()+600)
    model, processor, _ = load(config, effective)
    model = PeftModel.from_pretrained(model, selection['selected']['adapter']).eval()
    expected = {r['id']: r['raw_answer'] for r in map(json.loads,
                (Path(selection['selected']['adapter']).parent/'dev.jsonl').read_text().splitlines())}
    replay = infer(model, processor, input_rows(tiny['dev']), store, effective, output/'reload.jsonl',
                   {'purpose': 'Training-only closed-loop reload check'}, print)
    differences = [r['id'] for r in replay if r['raw_answer'] != expected[r['id']]]
    value = {'purpose': 'Training-only mechanical preflight; discarded adapters and no VQA accuracy claim',
             'optimizer_steps': selection['optimizer_steps'], 'micro_steps': selection['micro_steps'],
             'checkpoints_written_and_evaluated': len(selection['checkpoints']),
             'reloaded_questions': len(replay), 'answer_differences': differences,
             'passed': not differences, 'production_model_changed': False}
    save_json(root/'research/results/vqa-finetuning-20261108/CYCLE_SMOKE.json', value)
    print(json.dumps(value, indent=2), flush=True)
    if not value['passed']: raise RuntimeError('Closed-loop mechanical preflight failed')


if __name__ == '__main__': main()
