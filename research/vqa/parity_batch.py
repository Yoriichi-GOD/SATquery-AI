"""Keep native vision math; verify exact batch reuse for both model arms."""
import gc
import json
from pathlib import Path
import time
import torch
from peft import PeftModel

from .core import balanced_rows, save_json
from .gpu import ImageStore, infer, infer_pair, input_rows, load


def main():
    root = Path(__file__).resolve().parents[2]
    config = json.loads((root/'research/experiments/vqa-finetuning-20261108.json').read_text())
    corpus = json.loads((root/'research/datasets/local/vqa-20261108/corpus.json').read_text())
    rows = balanced_rows([r for r in corpus['train'] if r['task'] == 'vqa'], 32, config['seed'])
    effective = {**config['inference'], 'vision_mode': 'native'}
    output = root/'.runtime/vqa-20261108/native-batch-parity-v1'
    output.mkdir(exist_ok=False)
    model, processor, _ = load(config, effective)
    store = ImageStore(directory=root/'research/datasets/local/vqa-20261108/images/train', receipts=corpus['images'])
    start = time.monotonic()
    baseline = infer(model, processor, input_rows(rows), store, effective, output/'native-base.jsonl',
                     {'purpose': 'Training-only parity'}, print)
    base_seconds = time.monotonic()-start
    adapter = root/'.runtime/vqa-20261108/gpu-smoke-512-b4/discarded-adapter'
    model = PeftModel.from_pretrained(model, adapter).eval()
    start = time.monotonic()
    candidate = infer(model, processor, input_rows(rows), store, effective, output/'native-candidate.jsonl',
                      {'purpose': 'Discarded smoke adapter, training-only parity'}, print)
    candidate_seconds = time.monotonic()-start
    start = time.monotonic()
    paired = infer_pair(model, processor, input_rows(rows), store, effective, output/'paired',
                        {'purpose': 'Training-only exact native-batch reuse verification'}, print)
    pair_seconds = time.monotonic()-start
    expected = {'base': {r['id']: r['raw_answer'] for r in baseline},
                'candidate': {r['id']: r['raw_answer'] for r in candidate}}
    differences = {arm: [r['id'] for r in paired[arm] if r['raw_answer'] != expected[arm][r['id']]] for arm in paired}
    value = {'support': '32 training-only questions in both arms; smoke adapter, not an accuracy trial',
             'effective': effective, 'answer_differences': differences, 'passed': not any(differences.values()),
             'timings': {'native_base': base_seconds, 'native_candidate': candidate_seconds, 'paired_native_reuse': pair_seconds},
             'pair_questions_per_second': 2*len(rows)/pair_seconds,
             'vision_encoder_math': 'Original batched encoder output reused only for identical pixels/grids; no per-image recalculation',
             'production_weights_modified': False}
    save_json(output/'summary.json', value)
    save_json(root/'research/results/vqa-finetuning-20261108/NATIVE_BATCH_PARITY.json', value)
    print(json.dumps(value, indent=2), flush=True)
    if not value['passed']: raise RuntimeError('Exact native-batch reuse parity failed')


if __name__ == '__main__': main()
