# Paired lab — measured status, 12 September 2026

## What is implemented
An isolated app at http://localhost:8767. Main demo remains at http://localhost:8765 with no source changes.
Actual CPU inference: ChangeFormerV6 LEVIR for paired building-change masks and constrained change descriptions; jointly trained reBEN ResNet50 for optical–SAR scene classification, with same-family single-sensor ablations.
Automatic paired task selection, TIFF upload, metadata/grid/date/band/unit checks, visible evidence, uncalibrated score disclosure, execution trace and downloadable source+result ZIP.
Existing VQA, caption/description, LoRA adaptation, NDVI and grounding remain in the preserved main app. They are not automatically dispatched by this isolated lab yet.

## Actual evidence
Temporal: 7 public LEVIR demonstration crops, pooled changed-pixel F1 90.83%, IoU 83.20%. Per-crop IoU ranges from 60.93% to 97.38%. These are deliberately illustrative public demo images, not an unbiased sample. Upstream training script uses test for checkpoint selection, so these are NOT clean held-out results.
Temporal controls: original same-image control plus brightness-only, second identical scene and a real paired 128px reference-negative window resized to 256px. All produced zero changed pixels. The derived crop is not an independent test image; resizing changes its physical scale.

Cross-modal: 6 validation + 6 test-labelled public BigEarthNet v2 fixtures; all from one Austrian scene. Labels from the dataset, not manually invented. Fixed sigmoid threshold 0.5. Scores below are micro F1 across the 19 multi-label classes, not per-image accuracy.

| Split | SAR-only ResNet50 | Optical-only ResNet50 | Joint ResNet50 |
|---|---:|---:|---:|
| Validation (6) | 66.67% | 64.29% | 74.58% |
| Test-labelled fixtures (6) | 65.31% | 60.87% | 75.47% |

Refinement: initial joint ResNet18 validation F1 71.19%; selected joint ResNet50 74.58%. Selection used validation F1 only, before measuring candidate test scores. No threshold tuning or training on these labels. Both trials are preserved. Different model capacities also affect scores: do not interpret ResNet18→50 as solely a fusion effect.

Browser tests completed both actual model workflows, ZIP download, dark/light layouts and mobile layout, without JavaScript errors or horizontal overflow. HTTP tests check busy exclusion, input-file hashes inside ZIPs, format/metadata bypass rejection and wrong-workflow rejection. See JSON reports for exact final counts.
Main regression: 39 existing Python tests passed. This is functional regression evidence, not a new VQA accuracy benchmark. Main source hashes checked against the pre-work manifest.

## Original specification checklist
| Requirement | Current status and remaining boundary |
|---|---|
| Remote-sensing adaptation | Existing local RSVQA LoRA retained; new specialists inherit their publishers' remote-sensing training. No claim that we trained these new checkpoints. |
| Single-image VQA + description/grounding | Existing demo retained; isolated paired app links to it. No new single-SAR VQA validation. |
| Bi-temporal change description or change VQA | Implemented for building-related binary change, with location quadrants and pixel coverage. General semantic change and CDVQA answers remain unvalidated. |
| Optical–SAR complementary analysis | Implemented as genuine joint scene classification, with single-modality comparisons. Spatial built-up/water segmentation remains absent. |
| Automatic selection/execution | Implemented within paired lab from query + input modalities. A unified controller across old and new apps is deliberately not connected yet. |
| Input compatibility | Uploaded GeoTIFF/TIFF grids, CRS, dates, bands, units checked. Coregistration is required, not performed. Matching metadata is not proof of subpixel registration. |
| Evidence and confidence | Inputs, masks/previews, full class scores, numeric denominators, model/revision/parameters, ZIP and JSON. Scores are not calibrated probability of correctness. |
| Prescribed evaluation | Small development trials completed; full VRSBench/RSVQA/CDVQA evaluation still open. |
| ISRO/SAC Cartosat-2S/RISAT | NOT demonstrated. Sentinel-specific multispectral/VV-VH model cannot accept arbitrary Cartosat/RISAT pairs. Sensor-compatible adaptation remains necessary. |

## What must happen before claiming full specification completion
1. Broaden independent paired evaluation across geographic scenes and negative cases; retain fixed splits and publish failures.
2. Build and evaluate CDVQA/semantic change capability, including gain/loss only when direction is supported by labels and outputs.
3. Obtain the permitted sensor/band/unit contract for Cartosat-2S and RISAT; adapt a compatible joint model, rather than relabelling Sentinel bands.
4. Add spatial cross-modal extraction if claiming the representative built-up/water-region query.
5. Connect validated specialists to a unified controller only after a complete demo regression/replay.

The paired milestone is demonstrably running. The full ISRO problem is not yet solved; no "ISRO-grade" claim is warranted.
