"""Training-only native/optimized/native-repeat inference equivalence and timing."""
import json
from pathlib import Path
import time
import torch

from .core import balanced_rows, save_json, sha256
from .gpu import ImageStore, infer, input_rows, load


def main():
    root = Path(__file__).resolve().parents[2]
    config = json.loads((root/'research/experiments/vqa-finetuning-20261108.json').read_text())
    corpus = json.loads((root/'research/datasets/local/vqa-20261108/corpus.json').read_text())
    rows = balanced_rows([r for r in corpus['train'] if r['task'] == 'vqa'], 64, config['seed'])
    effective = {**config['inference'], 'batch_size': 16}
    output = root/'.runtime/vqa-20261108/vision-parity-v1'
    output.mkdir(exist_ok=False)
    model, processor, _ = load(config, effective)
    store = ImageStore(directory=root/'research/datasets/local/vqa-20261108/images/train', receipts=corpus['images'])
    predictions, results = {}, {}
    vision_timings = []
    def before(module, args):
        torch.cuda.synchronize(); module._satquery_profile_started = time.perf_counter()
    def after(module, args, result):
        torch.cuda.synchronize(); vision_timings.append(time.perf_counter()-module._satquery_profile_started)
    a = model.visual.register_forward_pre_hook(before)
    b = model.visual.register_forward_hook(after)
    try:
        for name, mode in [('native', 'native'), ('per-image', 'per_image_cache'), ('native-repeat', 'native')]:
            settings = {**effective, 'vision_mode': mode}
            vision_timings.clear(); torch.cuda.reset_peak_memory_stats(); start = time.monotonic()
            values = infer(model, processor, input_rows(rows), store, settings, output/(name+'.jsonl'),
                           {'purpose': 'Training-only numerical parity; no accuracy/checkpoint selection'}, print)
            elapsed = time.monotonic()-start
            predictions[name] = {r['id']: r['raw_answer'] for r in values}
            results[name] = {'seconds': elapsed, 'vision_seconds': sum(vision_timings),
                             'peak_allocated_GiB': torch.cuda.max_memory_allocated()/2**30}
        differences = {name: [key for key in predictions['native'] if predictions['native'][key] != values[key]]
                       for name, values in predictions.items() if name != 'native'}
        result = {'support': '64 training-only questions; native and optimized greedy outputs, no reference accuracy',
                  'n': len(rows), 'effective': effective, 'timings': results,
                  'answer_differences': differences, 'passed': not any(differences.values()),
                  'encoder_weights_changed': False, 'library_source_modified': False,
                  'source_sha256': {p.name: sha256(p) for p in Path(__file__).parent.glob('*.py')}}
        save_json(output/'summary.json', result)
        save_json(root/'research/results/vqa-finetuning-20261108/VISION_PARITY.json', result)
        print(json.dumps(result, indent=2), flush=True)
        if not result['passed']: raise RuntimeError('Native inference parity gate failed')
    finally:
        a.remove(); b.remove()


if __name__ == '__main__': main()
