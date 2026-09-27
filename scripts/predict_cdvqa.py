"""Experimental CDVQA inference on prepared, ordered RGB pairs. No test labels needed."""
import argparse
import hashlib
import json
import os
import sys
import time
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'paired_lab'))

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

class Predictor:
    def __init__(self, model_dir, encoder_path, device='cpu'):
        import torch
        from torch import nn
        from torchvision.models import resnet50
        from torchvision import transforms
        from cdvqa_model import PairedAnswerModel
        self.torch = torch
        self.device = device
        torch.set_num_threads(4)
        model_dir = Path(model_dir)
        self.manifest = json.loads((model_dir / 'release.json').read_text())
        checkpoint = model_dir / 'paired-best.pt'
        if sha(checkpoint) != self.manifest['checkpoint_sha256']:
            raise ValueError('Checkpoint hash differs from frozen release.')
        if sha(encoder_path) != self.manifest['encoder_sha256']:
            raise ValueError('Encoder hash differs from frozen release.')
        self.ckpt = torch.load(checkpoint, map_location='cpu', weights_only=True)
        self.model = PairedAnswerModel(len(self.ckpt['vocab']) + 2, len(self.ckpt['answers']))
        self.model.load_state_dict(self.ckpt['state_dict'])
        self.model.to(device).eval()
        base = resnet50(weights=None)
        base.load_state_dict(torch.load(encoder_path, map_location='cpu', weights_only=True))
        self.encoder = nn.Sequential(*list(base.children())[:-2]).to(device).eval()
        self.transform = transforms.Compose([
            transforms.Resize((256, 256), interpolation=transforms.InterpolationMode.BILINEAR),
            transforms.ToTensor(), transforms.Normalize([.485, .456, .406], [.229, .224, .225])])

    def predict(self, before, after, question, aligned=False):
        from PIL import Image
        from cdvqa_model import tokens, encode_questions
        from contextlib import nullcontext
        if not aligned:
            raise ValueError('Confirm that the ordered RGB inputs cover the same area and are already aligned.')
        canonical = ' '.join(tokens(question))
        if canonical not in self.manifest['supported_questions']:
            raise ValueError('Question is outside the trained CDVQA templates. See release.json supported_questions; this experimental CLI is not free-form VQA.')
        images = []
        sizes = []
        for path in [before, after]:
            with Image.open(path) as im:
                if im.mode != 'RGB':
                    raise ValueError('Supply prepared three-channel RGB images, not raw spectral/SAR bands.')
                if im.width * im.height > 16_777_216 or min(im.size) < 32:
                    raise ValueError('Input dimensions outside the experimental limit.')
                sizes.append(im.size)
                images.append(self.transform(im))
        if sizes[0] != sizes[1]:
            raise ValueError('Pair dimensions differ. This runner does not align or register images.')
        torch = self.torch
        if self.device == 'cuda':
            torch.cuda.synchronize()
        start = time.perf_counter()
        with torch.inference_mode():
            with torch.autocast('cuda', dtype=torch.float16) if self.device == 'cuda' else nullcontext():
                f = self.encoder(torch.stack(images).to(self.device))
                f = torch.nn.functional.adaptive_avg_pool2d(f, (4, 4)).flatten(2).transpose(1, 2)
            # Match the benchmark cache's float16 storage before answer inference.
            f = f.half()
            q = encode_questions([question], self.ckpt['vocab']).to(self.device)
            with torch.autocast('cuda', dtype=torch.bfloat16) if self.device == 'cuda' else nullcontext():
                logits = self.model(f[0:1], f[1:2], q)
            probabilities = logits.float().softmax(-1)[0].cpu().tolist()
        if self.device == 'cuda':
            torch.cuda.synchronize()
        seconds = time.perf_counter() - start
        index = max(range(len(probabilities)), key=probabilities.__getitem__)
        return {
            'status': 'experimental_model_output', 'answer': self.ckpt['answers'][index],
            'question': question, 'model': self.ckpt['architecture'],
            'checkpoint_sha256': self.manifest['checkpoint_sha256'],
            'encoder_sha256': self.manifest['encoder_sha256'],
            'inputs': [{'role': role, 'filename': Path(p).name, 'sha256': sha(p), 'size': size}
                       for role, p, size in zip(['before', 'after'], [before, after], sizes)],
            'alignment': 'User-declared; physical co-registration is not verified',
            'preprocessing': 'Full image bilinear resize to 256x256; ImageNet normalization; frozen ResNet50 4x4 spatial features',
            'class_scores_uncalibrated': dict(zip(self.ckpt['answers'], probabilities)),
            'device': self.device, 'encoder_and_classifier_seconds': seconds,
            'limitations': ['Benchmark-trained 19-answer classifier; not general-purpose VQA.',
                            'Ratio answers are predicted bins, not geospatial measurements.',
                            'Scores are not calibrated confidence or accuracy.',
                            'No masks, localization, official-sensor or arbitrary-scene validation.',
                            'CPU precision differs from CUDA benchmark; exact answer parity is not guaranteed.']}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--before', required=True, type=Path)
    p.add_argument('--after', required=True, type=Path)
    p.add_argument('--question', required=True)
    p.add_argument('--aligned', action='store_true')
    p.add_argument('--model-dir', type=Path, default=Path(os.environ.get('SATQUERY_CDVQA_MODEL_DIR', '/root/satquery/cdvqa')))
    p.add_argument('--encoder', type=Path, default=Path(os.environ.get('SATQUERY_CDVQA_ENCODER', '/root/.cache/torch/hub/checkpoints/resnet50-11ad3fa6.pth')))
    p.add_argument('--device', choices=['cpu', 'cuda'], default='cpu')
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    if a.out.exists():
        p.error('Output directory already exists; use a new path to preserve prior evidence.')
    start = time.perf_counter()
    predictor = Predictor(a.model_dir, a.encoder, a.device)
    loaded = time.perf_counter()
    result = predictor.predict(a.before, a.after, a.question, a.aligned)
    result.update(model_load_seconds=loaded-start, runner_seconds=time.perf_counter()-start)
    a.out.mkdir(parents=True)
    (a.out / 'result.json').write_text(json.dumps(result, indent=2))
    with zipfile.ZipFile(a.out / 'evidence.zip', 'w', zipfile.ZIP_DEFLATED) as z:
        z.write(a.out / 'result.json', 'result.json')
        z.write(a.before, 'before' + a.before.suffix)
        z.write(a.after, 'after' + a.after.suffix)
    print(json.dumps(result, indent=2))

if __name__ == '__main__':
    main()
