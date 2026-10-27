# Step 2 results - 2026-10-20

Completed the bounded CDVQA spatial-detail experiment and retrospective water-fusion diagnostics. No serving model, historical prediction file or benchmark score was replaced. No CDVQA test evaluation was run.

## CDVQA decision

Do not promote grid8 under frozen guardrails.

| Seed | Question-only validation OA | 4x4 validation OA | 8x8 validation OA | 8x8 minus 4x4 | 4x4 AA | 8x8 AA |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 20260928 | 68.33% | 70.73% | 69.20% | -1.53 pp | 62.29% | 60.00% |
| 20260929 | 68.51% | 70.41% | 69.79% | -0.62 pp | 62.38% | 60.85% |
| 20260930 | 68.46% | 70.21% | 70.13% | -0.09 pp | 61.58% | 61.08% |

Mean paired OA difference: **-0.746 percentage points**. 95% paired scene-bootstrap interval for mean-seed difference: [-1.297, -0.169] pp.
The interval resamples 400 validation scenes, preserving their questions and averaging matched seeds. It is conditional on validation-selected checkpoints and does not remove selection optimism or establish unseen generalization.

### Per-type change

| Official question type | Mean 8x8 minus 4x4 accuracy |
| --- | ---: |
| change_or_not | +0.052 pp |
| change_ratio | -4.208 pp |
| change_ratio_types | +0.581 pp |
| change_to_what | -2.663 pp |
| decrease_or_not | -0.330 pp |
| increase_or_not | -1.042 pp |
| largest_change | -2.472 pp |
| smallest_change | -1.417 pp |

### Resource accounting

| Variant | Mean completed head-training stage | Maximum PyTorch allocation across runs |
| --- | ---: | ---: |
| question_only | 38.13 s | 416.9 MiB |
| grid4 | 54.37 s | 631.2 MiB |
| grid8 | 110.57 s | 2250.7 MiB |

Shared feature extraction: 180.17 seconds for 4,000 Train/Val images. Recorded experiment execution: 793.16 seconds, 9 runs.
Per-run stages include validation and artifact work; early-stopping epochs differ. Allocation includes the active feature cache and head, not the entire application, driver or CPU RAM. These are experiment costs, not end-to-end serving latency benchmarks. Both feature caches occupy 1.221 GiB on disk.

### What was held fixed

Frozen ImageNet ResNet50; RGB images resized to 256x256; identical normalization; the same 2,648,596-parameter answer head; AdamW lr0.001/weight decay0.01; batch128; maximum35 epochs; patience7; validation OA selection with earlier-epoch tie break. Only pooled visual token grid changes from 4x4 to native 8x8. Both caches derive from the same encoder pass. Three matched seeds were run for question-only, 4x4 and 8x8.
Official Train: 65,967 questions/1,600 pairs; Val: 16,441/400. No test labels or predictions were parsed for training/selection. Historical evidence was byte-hashed to verify preservation. No additional labels, masks, downloads or encoder fine-tuning were used.
The 4x4 models are freshly trained experimental baselines, not the historical deployed checkpoint. Feature extraction used only Train/Val images; numerical execution can differ from the older cache. The first question-only run reproduces the recorded 68.33% validation OA. Exact historical paired checkpoint reproduction is not claimed.

### Verification and controls

Every saved prediction was independently joined to the official validation image/question/answer IDs; exact OA and eight-type AA were recomputed. Best checkpoints match validation selection and recorded hashes. Question-only and cyclic unrelated-pair controls are saved for every seed; completion coverage is 100% within this closed-set validation evaluation, not the general application.
Scoring sanity checks cover unequal question-type weighting and zero/constant paired-bootstrap gains. A later verifier amendment added the independent official-label join; scoring and selection rules were unchanged, and both verifier hashes are retained.
All 113 existing software regression checks passed. Serving checkpoint and encoder hashes match the step-1 freeze.

## Fusion diagnosis

See [the full fusion report](FUSION_DIAGNOSTICS_20261020.md). Saved CPU test IoU is 83.8969% optical versus 82.6440% joint (-1.2529 pp). Joint loses on 55 chips, wins on 25, ties on 3; 7 comparisons are undefined. Pakistan's major regression is missed water; the USA regression is predominantly extra false positives. The scene/event intervals include zero, so this is not proof of universal modality superiority.
Four inspected Ghana chips have no scored labels; Paraguay_34417 has no shared valid inputs. Apparent grid differences are negligible numeric precision, not evidence of misregistration. Clouds, physical registration and acquisition gaps remain unmeasured causes.

## Closure and next decision

Definition of done: fixed baseline verified; manifest frozen before execution; all nine bounded runs completed; independent scoring and uncertainty finished; fusion counts reconciled; regression suite passed; reports and raw predictions retained. No serving promotion.
The spatial-detail finding applies to this encoder/head/training recipe. Do not add more token scales or tune on the observed test scores to rescue it. The next separate hypothesis can examine visual representation adaptation; fusion work should first collect validation-only quality/disagreement evidence. Both require their own pre-run manifest and resource limit.
Fresh acceptance data, independent factuality review, complete prescribed grounding evaluation, clean GPU restoration of all specialists, and corresponding Cartosat-2S/RISAT task data remain open.

## Local reproduction and evidence

- Runner: scripts/experiment_cdvqa_grid.py; independent scorer: scripts/analyze_cdvqa_grid.py; fusion audit: scripts/audit_fusion_counts.py.
- Original run: /root/satquery/experiments/grid-20261020-v1 (feature caches and experimental checkpoints).
- Portable raw prediction/history copy: .runtime/step2-20261020/cdvqa; independent comparison: .runtime/step2-20261020/cdvqa-analysis/comparison.json.
- Final fusion evidence: .runtime/step2-20261020/fusion-complete.
- Frozen experiment manifest SHA256: 9488888980471ed1d2e2a4d00af19b11d16cb2f5ea31d6bf23cddc67d30d454e.
- These local ignored artifacts and maintainer assets are not supplied by a public clone. New runs require new output directories. Existing experiment and historical evidence must not be overwritten.
