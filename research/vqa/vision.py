"""Inference-only native per-image vision encoding; no weight or library-source edits.

Transformers 4.51.3 VisionSdpaAttention uses a dense block-diagonal attention mask
over concatenated images. Images are mathematically independent in that mask.
This bounded cache calls the original encoder on each image and reuses its result
for repeated questions. Native-path parity must pass before campaign use.
"""
from collections import OrderedDict
from contextlib import contextmanager
import math
import torch


class VisionMemo:
    def __init__(self, module, maximum=16):
        self.module, self.original, self.maximum = module, module.forward, maximum
        self.cache, self.keys = OrderedDict(), []
        self.encoded = self.hits = 0

    def forward(self, hidden_states, grid_thw=None, **kwargs):
        if torch.is_grad_enabled() or self.module.training:
            return self.original(hidden_states, grid_thw=grid_thw, **kwargs)
        grids = grid_thw.tolist()
        if len(grids) != len(self.keys) or any(g[0] != 1 for g in grids):
            raise ValueError('Vision cache requires hash-identified single optical images')
        if sum(math.prod(g) for g in grids) != hidden_states.shape[0]:
            raise ValueError('Vision patch partition does not match native input')
        outputs, start = [], 0
        for index, grid in enumerate(grids):
            size = math.prod(grid)
            key = (self.keys[index], tuple(grid), str(hidden_states.dtype), str(hidden_states.device))
            if key not in self.cache:
                encoded = self.original(hidden_states[start:start+size], grid_thw=grid_thw[index:index+1], **kwargs)
                self.cache[key] = encoded.detach()
                self.encoded += 1
            else:
                self.hits += 1
            outputs.append(self.cache[key])
            self.cache.move_to_end(key)
            while len(self.cache) > self.maximum:
                self.cache.popitem(last=False)
            start += size
        return torch.cat(outputs, dim=0)


@contextmanager
def cached_vision(model, enabled=False):
    if not enabled:
        yield None
        return
    base = model.get_base_model() if hasattr(model, 'get_base_model') else model
    memo = VisionMemo(base.visual)
    base.visual.forward = memo.forward
    try:
        yield memo
    finally:
        base.visual.forward = memo.original
        memo.cache.clear()


class NativeBatchMemo:
    """Reuse one exact native encoder result across matched baseline/adapter passes.

    Unlike per-image re-encoding, this preserves the native batched calculation.
    Pixel tensors and grid tensors must compare exactly before any reuse.
    """
    def __init__(self, module):
        self.module, self.original = module, module.forward
        self.pixels = self.grid = self.encoded = None
        self.reuses = 0

    def forward(self, hidden_states, grid_thw=None, **kwargs):
        if torch.is_grad_enabled() or self.module.training:
            raise ValueError('Native batch reuse is inference-only')
        if self.encoded is None:
            self.encoded = self.original(hidden_states, grid_thw=grid_thw, **kwargs)
            self.pixels, self.grid = hidden_states.detach().clone(), grid_thw.detach().clone()
        else:
            if not torch.equal(self.pixels, hidden_states) or not torch.equal(self.grid, grid_thw):
                raise ValueError('Cached native vision inputs differ between paired arms')
            self.reuses += 1
        return self.encoded


@contextmanager
def native_batch_reuse(model):
    base = model.get_base_model() if hasattr(model, 'get_base_model') else model
    memo = NativeBatchMemo(base.visual)
    base.visual.forward = memo.forward
    try:
        yield memo
    finally:
        base.visual.forward = memo.original
        memo.pixels = memo.grid = memo.encoded = None
