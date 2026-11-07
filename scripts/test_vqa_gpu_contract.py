"""Explicit Torch-only software contracts; not a model-accuracy evaluation."""
from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import torch
from research.vqa.vision import native_batch_reuse


class Encoder(torch.nn.Module):
    def __init__(self):
        super().__init__(); self.calls = 0
    def forward(self, pixels, grid_thw=None):
        self.calls += 1
        return pixels * 2


class Model(torch.nn.Module):
    def __init__(self):
        super().__init__(); self.visual = Encoder(); self.eval()


class NativeBatchReuseTests(unittest.TestCase):
    def test_exact_pixels_and_grid_reuse_the_actual_native_result(self):
        model = Model(); pixels = torch.arange(12).reshape(4, 3).float(); grid = torch.tensor([[1, 2, 2]])
        with native_batch_reuse(model) as memo, torch.inference_mode():
            first = model.visual(pixels, grid_thw=grid)
            second = model.visual(pixels.clone(), grid_thw=grid.clone())
            self.assertTrue(torch.equal(first, second)); self.assertEqual(model.visual.calls, 1)
            self.assertEqual(memo.reuses, 1)
        with torch.inference_mode(): model.visual(pixels, grid_thw=grid)
        self.assertEqual(model.visual.calls, 2, 'Native encoder restored on exit')

    def test_changed_pixels_are_rejected_even_with_the_same_shape(self):
        model = Model(); pixels = torch.ones(4, 3); grid = torch.tensor([[1, 2, 2]])
        with native_batch_reuse(model), torch.inference_mode():
            model.visual(pixels, grid_thw=grid)
            with self.assertRaisesRegex(ValueError, 'differ'): model.visual(pixels+1, grid_thw=grid)

    def test_changed_grid_is_rejected_even_with_the_same_pixels(self):
        model = Model(); pixels = torch.ones(4, 3)
        with native_batch_reuse(model), torch.inference_mode():
            model.visual(pixels, grid_thw=torch.tensor([[1, 2, 2]]))
            with self.assertRaisesRegex(ValueError, 'differ'): model.visual(pixels, grid_thw=torch.tensor([[1, 1, 4]]))

    def test_training_and_gradient_enabled_calls_cannot_reuse_inference_features(self):
        model = Model()
        with native_batch_reuse(model):
            with self.assertRaisesRegex(ValueError, 'inference-only'): model.visual(torch.ones(4, 3), grid_thw=torch.tensor([[1, 2, 2]]))

    def test_original_forward_restored_after_an_exception(self):
        model = Model()
        with self.assertRaises(RuntimeError):
            with native_batch_reuse(model): raise RuntimeError('fixture')
        with torch.inference_mode():
            self.assertTrue(torch.equal(model.visual(torch.ones(4, 3)), torch.ones(4, 3)*2))


if __name__ == '__main__': unittest.main(verbosity=2)
