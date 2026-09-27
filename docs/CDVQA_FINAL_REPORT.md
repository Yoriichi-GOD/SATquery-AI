# CDVQA trained specialist — final benchmark report

Measured 28 September 2026. Experimental paired-image answer classifier, evaluated separately from the served SatQuery controller.

## Results suitable for the presentation

| Official split | Questions | Image pairs | Paired model OA | Macro AA | Question-only OA | Gain over question-only |
|---|---:|---:|---:|---:|---:|---:|
| Test-1 | 39,686 | 968 | **69.90%** | 61.13% | 68.06% | +1.84 percentage points |
| Test-2 | 31,036 | 968 | **65.05%** | 61.19% | 63.24% | +1.81 percentage points |

**PPT wording:** “Dedicated change-question answering: 69.90% overall accuracy on the full CDVQA Test-1 split (39,686 questions, 968 pairs); 65.05% on Test-2 (31,036 questions, the same 968 pairs).”

**Required footnote:** Experimental specialist; official Train/Val split used for training and checkpoint selection. Test-1/Test-2 share imagery and overlap in questions, so they are not independent datasets and must not be pooled. This is not an overall SatQuery score, an ISRO acceptance score, a comparison with the competing team, or proof of official-sensor accuracy.

## What changed

Implemented and trained a new 19-answer paired RGB classifier. A frozen ImageNet ResNet50 extracts 4×4 spatial features from each date; a bidirectional GRU encodes the question; learned attention combines before, after and difference features to predict the answer. The answer model has 2,648,596 parameters; the frozen visual encoder has 23,508,032. It uses the images and question, not ground-truth masks, image names or test labels as model inputs.

Previously, the road/building temporal specialist did not implement the complete CDVQA answer vocabulary. This new result therefore establishes a CDVQA specialist baseline; it is not a before/after accuracy comparison against the old application. The paired-vs-question-only comparison below measures the contribution of visual inputs in this experiment.

The new specialist is runnable through `scripts/predict_cdvqa.py`, with original-input hashes, checkpoint identity, uncalibrated class scores, timing and a ZIP evidence package. It is **not yet wired into the main browser/router**. Language and paired-upload UI changes remain deferred as requested. The CLI accepts trained question templates listed in release.json and requires the user to confirm prepared, aligned RGB inputs.

## Protocol and integrity

- Official training: 65,967 questions / 1,600 image pairs. Validation: 16,441 questions / 400 pairs. Test: 968 separate pair filenames. Pair-content hashes also found no exactly duplicated ordered pair across the splits; this does not establish geographic independence between nearby scenes.
- Seed 20260928. AdamW, learning rate 0.001, weight decay 0.01, batch 128, maximum 35 epochs, early stopping after 7 validation epochs without improvement. One paired configuration and one question-only control were trained; no test-driven tuning.
- Highest validation OA selected checkpoints: paired epoch 8, 70.68%; question-only epoch 3, 68.33%. Model and evaluator hashes were frozen before reading final test answers in the evaluator.
- Full RGB images resized to 256×256 using bilinear interpolation, ImageNet normalization, frozen ResNet50 IMAGENET1K_V2 features, 4×4 pooling. Features cached as float16; answer-model GPU inference uses bfloat16. GPU numerical precision and batch shape can affect borderline decisions.
- OA is exact correct answers divided by all questions. AA is the unweighted mean of accuracies across the eight official question types. No substring grading, semantic leniency, cherry-picked accepted answers, or omitted failures.
- Test imagery was encoded ahead of evaluation for feature caching only, with the frozen encoder in evaluation mode. No test imagery statistics were used to update the encoder or classifier. ImageNet pretraining exposure was not independently audited.
- Twelve official test pairs were previously inspected in development probes; test question text also appeared in an earlier routing audit. Results excluding those 12 pairs are reported below. Do not call the whole test set a never-before-seen acceptance set.
- Independent release verification joined every prediction back to the official question, image and reference answer; recomputed correct counts and macro metrics; and checked unique question coverage.

## Previously inspected pairs excluded

| Split | Remaining questions / pairs | Paired OA | Question-only OA | 95% scene-bootstrap interval for gain |
|---|---:|---:|---:|---:|
| Test | 39,194 / 956 | 69.89% | 68.02% | +1.24 to +2.50 pp |
| Test2 | 30,661 / 956 | 65.03% | 63.22% | +1.17 to +2.50 pp |

Intervals use 1,000 resamples of image pairs, preserving within-pair question dependence. They describe this dataset/run; they do not establish geographical or official-sensor generalization.

## Image contribution controls

| Split | Correct paired images | Question only | Unrelated paired images |
|---|---:|---:|---:|
| Test | 69.90% | 68.06% | 63.69% |
| Test2 | 65.05% | 63.24% | 58.54% |

Unrelated-image control cyclically assigns another test pair to each question, keeping that replacement pair internally ordered. These results support a contribution from imagery, while the strong question-only results show substantial dataset answer priors. They do not prove the model reasons correctly on every question.

## Per-question-type results

| Type | Test-1 n | Test-1 paired | Test-1 question-only | Test-2 n | Test-2 paired |
|---|---:|---:|---:|---:|---:|
| Change presence | 13,882 | 83.25% | 82.49% | 5,126 | 82.68% |
| Overall change ratio | 1,936 | 39.05% | 29.80% | 1,936 | 38.64% |
| Class-specific change ratio | 5,811 | 71.31% | 71.31% | 11,616 | 71.24% |
| Transition destination | 2,991 | 55.60% | 56.94% | 2,991 | 55.80% |
| Class decrease | 4,658 | 77.89% | 74.09% | 1,754 | 78.79% |
| Class increase | 4,600 | 76.04% | 73.72% | 1,805 | 76.29% |
| Largest change class | 2,904 | 56.54% | 48.62% | 2,904 | 56.85% |
| Smallest change class | 2,904 | 29.37% | 30.30% | 2,904 | 29.27% |

The model remains weak on overall change ratios and smallest-change classification. Transition-destination and smallest-change scores are below the question-only control on Test-1. Predicted ratio bins are model interpretations, not measured areas. Do not cherry-pick change-presence accuracy as the full CDVQA score.

## Runtime and functional verification

- Hardware: NVIDIA GeForce RTX 5060 Laptop GPU. Visual feature extraction for 5,936 images took 96.83 seconds; paired head training took 71.92 seconds after feature caching. These are recorded stages, not complete acquisition/setup/training time.
- CUDA raw-image replay: 16/16 sampled validation answers matched their cached-feature inference. Five negative controls refused: unconfirmed alignment, unsupported question, unequal dimensions, grayscale input, empty question.
- Replay PyTorch peak allocated memory: 162.00 MiB; reserved: 174.00 MiB. This covers the isolated specialist, not the whole application, GPU driver or simultaneous services.
- CPU CLI smoke run completed with the same validation answer. Measured model/import load 5.462 s, encoder + classifier 0.131 s, runner through answer 5.678 s. One run only; runner time excludes subsequent JSON/ZIP writing and Python process startup.
- Evidence ZIP CRC and the hashes of both archived original images verified. JSON in ZIP equals the standalone result.
- Existing software regression suite: 85 passed in 2.632 seconds. This suite includes mocks and is separate from real-model evaluation.
- No full CPU accuracy benchmark, concurrent serving test, calibrated-confidence claim, geospatial-registration guarantee or operational certification.

## Reproduction and saved assets

Source scripts: [model](../paired_lab/cdvqa_model.py), [training](../scripts/train_cdvqa.py), [evaluation](../scripts/evaluate_cdvqa.py), [inference](../scripts/predict_cdvqa.py), [independent verification](../scripts/verify_cdvqa_release.py). Training/evaluation paths currently refer to this WSL workspace; recreating them elsewhere requires editing those paths. The inference runner accepts explicit paths and environment variables.

Runtime dependencies are captured in `environment-freeze.txt` alongside the evidence. External assets: official SECOND paired RGB archive, pinned CDVQA labels, PyTorch ResNet50 IMAGENET1K_V2 encoder. Repository Apache license text for CDVQA does not by itself settle redistribution rights for all underlying imagery; this release bundle excludes the dataset and pretrained encoder.

Local checkpoint: `/root/satquery/cdvqa/paired-best.pt`; release manifest and question templates: `/root/satquery/cdvqa/release.json`. The separate release ZIP preserves both trained checkpoints, release manifest and source scripts. No weights need downloading to run on this existing machine.

```bash
/root/satquery/.venv/bin/python scripts/predict_cdvqa.py \
  --before /path/to/before.png --after /path/to/after.png \
  --question 'Did the areas of non-vegetated ground surface change?' \
  --aligned --device cpu --out /path/to/new-result-directory
```

Canonical evidence directory: [cdvqa-trained-20260928](../paired_lab/evidence/cdvqa-trained-20260928). See final-test-summary.json, Test-predictions.json, Test2-predictions.json, candidate-freeze.json, release-verification.json, protocol.json and input-hashes.json. Training and validation manifests and source hashes are preserved. The published evaluator refuses to overwrite an existing final-test-summary.json.

Primary dataset references: [CDVQA authors](https://github.com/YZHJessica/CDVQA), [paper](https://arxiv.org/abs/2112.06343), [SECOND author page](https://captain-whu.github.io/SCD/). Label revision `cc5893123dd32326de38745b65d2ffe45055937b`; source archive SHA256 `5ee2a82b5824b3f5e3c5bfaf018835862e7623993ff9ac5ce57fd11fcfad2b4e` (SECOND_train_set.rar, not the outer Google Drive ZIP).
