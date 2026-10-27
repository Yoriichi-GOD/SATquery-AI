# Step 3 results - 2026-10-20

Completed bounded balanced-loss, final encoder-projection adaptation and simple fusion-quality experiments. No serving model was replaced and no new test-set score was produced. Step 2 remains closed; its rejected 8x8 candidate was not revived.

## Balanced-loss comparison

Weights are N/(8 * training question-type count), applied to per-example cross-entropy before taking the batch mean. Only the loss changes relative to the prior same-seed 4x4 training. This tests one weighting recipe, not every balancing method. Checkpoints still use validation OA, as declared; choosing by AA after seeing outcomes would be a different experiment.

| Seed | Baseline OA | Balanced OA | Baseline AA | Balanced AA | OA change |
| --- | ---: | ---: | ---: | ---: | ---: |
| 20260928 | 70.73% | 70.53% | 62.29% | 61.61% | -0.201 pp |
| 20260929 | 70.41% | 70.06% | 62.38% | 61.50% | -0.353 pp |
| 20260930 | 70.21% | 70.66% | 61.58% | 61.94% | +0.444 pp |

## Final encoder-projection adaptation

This is genuine partial adaptation of ResNet50 layer4.2.conv3 weights and bn3 affine parameters. Earlier encoder layers and the residual input stay frozen; batch-normalization running statistics stay frozen. It is not full encoder fine-tuning, a new remote-sensing pretrained encoder, or an architecture replacement.
Both branches start from the matching step-2 4x4 best head. Head learning rate is 1e-4; encoder-projection learning rate is 1e-5 where enabled. Each branch receives five epochs; epoch0 is eligible, so a worse continuation cannot erase the initial checkpoint. The frozen-projection branch is the fair control for numerical reconstruction and additional training.
Encoder intermediates are extracted from the same hashed Train/Val images. Float16 reconstruction matches the original encoder output exactly; subsequent projection/head training uses bfloat16 in both branches.

| Seed | Frozen continuation OA | Adapted projection OA | Frozen AA | Adapted AA | OA change | Selected epoch (frozen/adapted) |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| 20260928 | 71.10% | 71.07% | 62.62% | 62.51% | -0.036 pp | 1/1 |
| 20260929 | 70.52% | 70.54% | 62.35% | 62.46% | +0.012 pp | 2/2 |
| 20260930 | 70.61% | 70.48% | 61.79% | 61.63% | -0.128 pp | 1/1 |

## Predeclared decision gates

- balanced: mean OA difference -0.036 pp; paired scene-bootstrap 95% interval [-0.519, +0.459] pp. Frozen screen: **FAIL; do not promote**.
- encoder_projection: mean OA difference -0.051 pp; paired scene-bootstrap 95% interval [-0.130, +0.037] pp. Frozen screen: **FAIL; do not promote**.

Intervals use 1,000 scene resamples with seed20261020, preserving within-scene questions and averaging matched seeds. These are conditional on validation-selected checkpoints; selection optimism remains. Per-type changes and individual seed intervals are preserved in comparison.json. A primary gain does not override a >1pp AA or per-type regression under the frozen guardrail.

## Fusion quality baseline

Used only the 89 existing validation chips and their saved float32 CPU modality confusion counts. Features: shared finite-input fraction, optical RGB brightness fraction above 2500 DN, and SAR clipping fraction. Brightness is a proxy, not a verified cloud label. A fixed rule selects joint if at least 10% of valid pixels are bright, otherwise optical.
The fitted depth-one rule leaves one named event out, selects a rule using pooled IoU on the other validation events, then applies it to that event using image features only. Thresholds and leaf choices were fixed before execution. The model itself was already selected on validation; this does not create a fresh event-independent acceptance set.

| Strategy | Validation water IoU | Difference from optical | 95% paired event interval |
| --- | ---: | ---: | --- |
| s2 | 83.2289% | +0.0000 pp | [+0.0000, +0.0000] pp |
| all | 83.1284% | -0.1004 pp | [-0.7235, +0.6935] pp |
| s1 | 59.4547% | -23.7742 pp | [-33.9165, -16.9804] pp |
| fixed_quality | 83.1467% | -0.0821 pp | [-0.3287, +0.1789] pp |
| cross_event_stump | 83.0420% | -0.1869 pp | [-0.4911, +0.1265] pp |

Both simple quality selectors underperform fixed optical in point estimates and do not establish a gain. Neither is deployed. This rejects these proxies/rules under this evaluation; it does not disprove quality-aware fusion generally.
Every selected confusion-count row matches an original modality result. All aggregates were independently recomputed, and valid-pixel denominators are identical across strategies. Three all-unlabelled Ghana validation chips remain explicit zero-scored entries, not successful predictions. No test or Bolivia result was used to choose the gates.
Remaining causal evidence: actual cloud/quality labels, physical registration residuals, acquisition gaps and disagreement maps. Do not substitute the brightness heuristic for those measurements.

## Cost and verification

Nine CDVQA results completed: three balanced runs retained from v1 and six encoder-comparison runs in v2. Attempt v1 consumed 294.86 seconds; v2 consumed 541.97 seconds; combined recorded execution is 836.83 seconds. The resumed attempt had a 30-minute ceiling; combined allowed execution remained below the original 40-minute budget. The declared PyTorch allocation ceiling was 6 GiB. Stage times are not application serving latency.

| Variant | Mean recorded run seconds | Maximum PyTorch allocation |
| --- | ---: | ---: |
| balanced | 47.08 | 631.3 MiB |
| continuation | 54.33 | 2084.5 MiB |
| encoder_projection | 77.06 | 2099.0 MiB |

All 113 existing regression tests passed during this step. The experiment scripts compiled; an actual GPU smoke verified gradients reach the intended final encoder projection. Independent scoring joins all 16,441 predictions per run to official validation question/image/answer identities, verifies selected epochs, checkpoint hashes and shuffled controls. The serving model and frozen historical baseline must remain hash-identical; final closure-checks.json records that verification.

## Scope and next decision

Step 3 completes these bounded experiments, not every possible encoder/balancing method. No large pretrained model was downloaded. No combined balanced-plus-adapted model was trained: combining variables before isolated evidence would obscure attribution.
Use the frozen decision results above before proposing another experiment. A failed quality selector calls for better quality measurements, not more threshold searching on exposed data. Any future representation experiment needs a new hypothesis and budget. No model is automatically deployed even if it passes this validation screen.
The pre-existing acceptance dependencies remain open: fresh scene/event labels, independent description adjudication, complete prescribed grounding evaluation, clean GPU restoration of all specialists and corresponding Cartosat-2S/RISAT task references. They cannot be closed by further training on these existing data.

## Reproduction and artifacts

- scripts/experiment_cdvqa_step3.py; scripts/analyze_cdvqa_step3.py; scripts/experiment_fusion_quality.py.
- /root/satquery/experiments/step3-20261020-v2 contains the final manifest, histories, checkpoints and predictions; v1 retains the failed attempt.
- .runtime/step3-20261020/cdvqa contains portable JSON evidence; cdvqa-analysis/comparison.json contains independent scores.
- .runtime/step3-20261020/fusion contains the frozen selector manifest, input hashes, fold rules, per-chip counts and verification.
- CDVQA manifest SHA256: c6dba650d4e4b20b74bfba16d324d7fd031bc9d6e6e1e9c4adf0afe5f8477988.
- All experiment output directories are new; historical evidence is preserved. Local ignored data/checkpoints are not public clone assets.

## Failed attempt and recovery

Attempt v1 completed all balanced runs and exact float16 encoder reconstruction, then failed before encoder training. Deep-copying the projection before removing extraction hooks retained a closure referencing a deleted capture buffer. The original script and failure record are preserved. The fix removes hooks before copying and asserts none remain; a targeted forward/backward test passed after deleting the capture buffer. No learning rate, loss, split, selection metric or epoch limit changed. Attempt v2 reused hash-verified balanced checkpoints instead of retraining them. Extraction was repeated and its cost is included above.
