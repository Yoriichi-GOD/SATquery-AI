# Public adapter teams audit — 2026-11-07

Read-only inspection of public source, repository metadata, saved evaluation JSON, notebook cells and text model cards. No models, demos or tests were executed; no repository was cloned and no weights were downloaded. Arithmetic below checks saved-result consistency, not independent model accuracy. Comparison context supplied by the lead audit: our local research snapshot is `7277935`, while our public main is `fe8a038d1aebe84e1385e228749901c4a18f7f36`; these must not be treated as the same deliverable.

## Snapshots and freeze status

| Repository | Observed default branch / full HEAD | HEAD commit date (UTC) | Explicit status |
|---|---|---|---|
| [awdtyo/SatQueryAI-SIH26][a-head] | `main` / `c20b7a77817775f48d1f1ba2d435a9de9c97c3a9` | 2026-10-04 17:01:12 | GitHub metadata: `archived=false`. Tag `v0.1.0` points to the earlier `7b736c40121af1ff503ae155005777c155a9a426` (2026-09-29 13:19:31), not current HEAD. Releases API returned an empty list. No current-HEAD project freeze established. |
| [siddhtyagi18/SatQuery-AI][s-head] | `main` / `0d0cb3ba5ffc04eaa181111793a83352b670c581` | 2026-09-16 17:20:45 | GitHub metadata: `archived=false`; tags and releases API returned empty lists. A tracked Sept 7 report explicitly calls itself a demo freeze, but later HEAD changes mean that report is not evidence that current HEAD is frozen. [Report][s-acceptance] |

Metadata checked through GitHub connector and public API: [awdtyo metadata][a-meta], [tag list][a-tags], [releases][a-releases]; [siddhtyagi18 metadata][s-meta], [tag list][s-tags], [releases][s-releases].

## Strongest advantages to take seriously

- **awdtyo has concrete VLM adapter distribution and paired-image generation wiring.** Qwen2-VL-2B is loaded with PEFT; separate change and optical/SAR wrappers supply two images to the processor. Public, ungated Hugging Face metadata lists adapter configuration and safetensors for phase 2 and CDVQA, rather than merely promising future model files. This is stronger evidence for a distributable specialized VLM path than a deterministic workflow alone. It does not establish answer quality. [Config][a-config], [change wrapper][a-change], [fusion wrapper][a-fusion], [phase-2 files][a-hf2], [CDVQA files][a-hf3]
- **siddhtyagi18 has a substantially more concrete narrow building-change research record:** tracked checkpoint blobs, training configurations/logs, evaluation code, per-sample predictions/metrics, a baseline comparison and threshold sweeps. Our broader water/CDVQA/MCI/terrain scope and software test counts do not displace this evidence. Their internally comparable LEVIR-CD artifacts deserve acknowledgment on their own domain. [Experiment configuration][s-exp4-config], [baseline JSON][s-baseline], [experiment-04 JSON][s-exp4], [evaluation code][s-eval]
- **siddhtyagi18 also distributes an actual SmolVLM LoRA artifact and exposes limitations in saved audits.** Its saved validation result records 82 question-answer rows from four distinct patch IDs, with 21 correct answers (25.61% exact/soft match); 82 is not an independent-image denominator. That is useful negative evidence, not a reason to erase the model work or claim superiority over an unevaluated alternative. The Sept 7 acceptance report openly records insufficient temporal reasoning and only two optical/SAR smoke-test pairs. [Adapter tree][s-tree], [VQA result][s-vqa-eval], [acceptance report][s-acceptance]

## awdtyo: implementation versus claims

1. **Controller and validation are executable, but deterministic.** Routing follows input mode and query keywords; it is not an autonomous planner. Validation checks supported file extensions, decodability and image count, converts to RGB, and optionally reads TIFF bands/CRS. It does not establish optical/SAR sensor identity or pair co-registration; the nonzero-band check is not a full modality/domain validation. Traces include real/stub and latency fields. Grounding is aliased to VQA by default, so the unused grounding stub must not be mistaken for the active default route. [Controller, lines 49–219][a-controller], [config, lines 132–146][a-config]
2. **Current fusion means a two-image VLM call using the same phase-2 adapter as optical VQA.** The chart uses only the optical image. The stage-4 notebook explicitly proposes replacing that reused optical-only adapter with dedicated paired optical/SAR training; its training cell has no saved execution/output and its Hub destination is empty. Therefore this is implemented multimodal prompting, not demonstrated trained SAR fusion or a measured fusion benefit. [Fusion, lines 240–294 and 422–455][a-fusion], [stage-4 notebook][a-stage4]
3. **The adapters exist; their asserted training lineage remains NOT VERIFIED.** Phase-2 revision `f572b6334ca4b9eb7fdd0bf20dc6420f0c11f3a4` and CDVQA revision `baa5d2fd9336b74007fc39cb24724bc1880e9b91` have LoRA `r=16`, alpha 32 configs targeting Qwen2-VL-2B. Their text cards leave training data and evaluation sections unfilled. Current stage-1/2/3 notebooks load an external cache or build synthetic random chips with templated answers; real-data loader examples are commented out, and the training cells have no saved execution. This prevents verification of the README's named-data curriculum, without proving that published weights were trained only on synthetic data elsewhere. [Phase-2 config][a-hf2-config], [card][a-hf2-card], [CDVQA config][a-hf3-config], [card][a-hf3-card], [stage-1 notebook][a-stage1], [stage-2 notebook][a-stage2], [stage-3 notebook][a-stage3]
4. **Confidence is not validated correctness probability.** The wrappers map geometric mean generated-token probability through `0.35 + 0.6p`; when scores are unavailable they use 0.72, add 0.08 for longer answers and cap apologetic text. No held-out calibration protocol was found in inspected artifacts. [VQA, lines 580–629][a-vqa], [fusion, lines 350–394][a-fusion]
5. **“Measured” charts remain RGB heuristics.** Five color-threshold classes on 256×256 imagery drive charts/coarse spatial context; temporal charts subtract class shares, while a separate 128×128 RGB difference above 30 supplies a changed-pixel description. These are not independently validated land-cover/change truth. Four tracked test modules cover controller/registry/wrapper/location behavior using mocks; they do not provide task-accuracy benchmarks. README sample confidence/latency and live-status claims were not reproduced. [Chart code][a-chart], [change, lines 423–474][a-change], [test tree][a-tests], [README][a-readme]

## siddhtyagi18: research evidence and current-source limits

**The best supported change result is specific.** The evaluator opens each matched test triplet and takes one centered 256×256 crop. Thus “128 full test pairs” means all 128 filenames, not all 1024×1024 pixels: the saved denominator is 8,388,608 pixels. It evaluates test at the requested threshold, then sweeps thresholds separately on validation. Experiment configuration records 445 training / 64 validation pairs. [Evaluation, lines 172–285 and 517–623][s-eval], [experiment-04 config][s-exp4-config]

| Saved artifact, same 128 filenames / 256×256 crop protocol | Threshold | Micro IoU | Micro F1 | Precision | Recall |
|---|---:|---:|---:|---:|---:|
| Baseline, epoch 48 | 0.50 | 0.3619 | 0.5315 | 0.9299 | 0.3721 |
| Experiment 03, epoch 58 | 0.50 | 0.5677 | 0.7242 | 0.6871 | 0.7657 |
| Experiment 04, epoch 73 | 0.50 | 0.5702 | 0.7263 | 0.6954 | 0.7600 |

Sources: [baseline][s-baseline], [experiment 03][s-exp3], [experiment 04][s-exp4]. Each JSON contains 128 unique filenames; summed per-sample confusion counts agree with its global counts. Experiment-04 TP/FP/FN/TN are 319,818 / 140,081 / 100,976 / 7,827,733. This supports an internally documented recall–precision tradeoff and improvement over its baseline, not independent reproduction, an optical/SAR benchmark, or comparison against us.

- **Published 58.06% IoU / 73.47% F1 is not reconciled to its linked raw evidence.** The README repeats an Experiment-01 report claiming those values at 0.70. That report links root `test_full_results.json`, which instead records epoch 48, threshold 0.30, IoU 0.3848 / F1 0.5557. Its linked validation sweep peaks in micro F1 at 0.30, while the report calls 0.70 optimal. Preserve these as conflicting published records; do not substitute the unsupported headline for the traceable experiment-04 JSON. [README][s-readme], [Experiment-01 report][s-exp1-report], [linked root result][s-root-result], [linked validation sweep][s-root-sweep]
- **Checkpoint selection is configurable and needs care.** Git tree blob equality shows root `checkpoints/best_model.pt` equals experiment 04, while `experiment_01/best_model.pt` equals `baseline_epoch48_best_model.pt`. The config default and candidate resolver prefer experiment 01; `.env.example` instead sets root best model. The README calls epoch 73 active. These are different launch configurations, so the score cannot be assigned to every API run. No deployed environment or actual checkpoint loading was checked. [Tree][s-tree], [config][s-config], [resolver, lines 63–99][s-model], [example environment][s-env], [experiment-04 report][s-exp4-report]
- **SAR processing is substantial; learned fusion quality is not established.** The code reads metadata, computes overlap and radar representation statistics, handles VV/VH ratios and builds a false-color composite. The neural factory seeds freshly initialized weights and loads no trained checkpoint. Its “ablation” measures embedding cosine/L2 differences, not downstream accuracy against optical-only/SAR-only controls. The semantic answer uses threshold telemetry plus an optional VLM over the handcrafted composite, with deterministic prose fallback; it does not decode a trained fused task model. The source states that no supervised benchmark has been trained and that trained optical/SAR inference is unavailable. [Fusion factory, lines 277–398][s-fusion], [analysis, lines 874–1079][s-sar]
- **Historical integrity reports do not certify current HEAD.** Specialists return null confidence, but the inspected orchestrator falls back to 0.88 when no confidence exists and clips averaged scores into 0.72–0.98. The router persists that value; validation accepts values inside 0–1. This conflicts with the Sept 7 report and authored regression tests requiring null aggregate confidence. Separately, the temporal VLM validation checks transition wording, not visual correctness, and its VLM-fallback path derives semantic prose from changed-area bands yet labels it real. These are static source findings, not executed failures. [Orchestrator, lines 479–496][s-orchestrator], [router, lines 355–403][s-router], [validator, lines 145–171][s-validation], [confidence tests][s-confidence-tests], [Change VQA, lines 165–246 and 666–727][s-change-vqa]

## Comparison boundary

Neither repository supplies a matched head-to-head protocol against our local `7277935` or public `fe8a038...`: common imagery, splits, labels, preprocessing, checkpoints, task definitions and scoring are absent. Consequently **overall accuracy leadership, universal sensor reliability, deployment reliability and current test pass counts are NOT VERIFIED**. Larger scope, newer commits, model size, polished UI, test badges and published adapter files do not settle those questions. The defensible finding is that these teams have real implementation and research assets, with stronger narrow published building-change evidence in siddhtyagi18 and a distributable paired Qwen adapter path in awdtyo, alongside material source/claim gaps.

[a-head]: https://github.com/awdtyo/SatQueryAI-SIH26/commit/c20b7a77817775f48d1f1ba2d435a9de9c97c3a9
[a-meta]: https://api.github.com/repos/awdtyo/SatQueryAI-SIH26
[a-tags]: https://api.github.com/repos/awdtyo/SatQueryAI-SIH26/tags
[a-releases]: https://github.com/awdtyo/SatQueryAI-SIH26/releases
[a-readme]: https://github.com/awdtyo/SatQueryAI-SIH26/blob/c20b7a77817775f48d1f1ba2d435a9de9c97c3a9/README.md
[a-config]: https://github.com/awdtyo/SatQueryAI-SIH26/blob/c20b7a77817775f48d1f1ba2d435a9de9c97c3a9/backend/config.py
[a-controller]: https://github.com/awdtyo/SatQueryAI-SIH26/blob/c20b7a77817775f48d1f1ba2d435a9de9c97c3a9/backend/controller/__init__.py
[a-vqa]: https://github.com/awdtyo/SatQueryAI-SIH26/blob/c20b7a77817775f48d1f1ba2d435a9de9c97c3a9/backend/models/vqa.py
[a-change]: https://github.com/awdtyo/SatQueryAI-SIH26/blob/c20b7a77817775f48d1f1ba2d435a9de9c97c3a9/backend/models/change.py
[a-fusion]: https://github.com/awdtyo/SatQueryAI-SIH26/blob/c20b7a77817775f48d1f1ba2d435a9de9c97c3a9/backend/models/fusion.py
[a-chart]: https://github.com/awdtyo/SatQueryAI-SIH26/blob/c20b7a77817775f48d1f1ba2d435a9de9c97c3a9/backend/utils/chart.py
[a-tests]: https://github.com/awdtyo/SatQueryAI-SIH26/tree/c20b7a77817775f48d1f1ba2d435a9de9c97c3a9/tests
[a-stage1]: https://github.com/awdtyo/SatQueryAI-SIH26/blob/c20b7a77817775f48d1f1ba2d435a9de9c97c3a9/training/notebooks/satquery_ai_qlora_finetune.ipynb
[a-stage2]: https://github.com/awdtyo/SatQueryAI-SIH26/blob/c20b7a77817775f48d1f1ba2d435a9de9c97c3a9/training/notebooks/vrsbench_rsvqa_sft.ipynb
[a-stage3]: https://github.com/awdtyo/SatQueryAI-SIH26/blob/c20b7a77817775f48d1f1ba2d435a9de9c97c3a9/training/notebooks/cdvqa_change_sft.ipynb
[a-stage4]: https://github.com/awdtyo/SatQueryAI-SIH26/blob/c20b7a77817775f48d1f1ba2d435a9de9c97c3a9/training/notebooks/stage4_optical_sar_fusion.ipynb
[a-hf2]: https://huggingface.co/imadityasarkar/satquery-phase2-vrsbench/tree/f572b6334ca4b9eb7fdd0bf20dc6420f0c11f3a4
[a-hf3]: https://huggingface.co/imadityasarkar/cdvqa_change/tree/baa5d2fd9336b74007fc39cb24724bc1880e9b91
[a-hf2-config]: https://huggingface.co/imadityasarkar/satquery-phase2-vrsbench/blob/f572b6334ca4b9eb7fdd0bf20dc6420f0c11f3a4/adapter_config.json
[a-hf3-config]: https://huggingface.co/imadityasarkar/cdvqa_change/blob/baa5d2fd9336b74007fc39cb24724bc1880e9b91/adapter_config.json
[a-hf2-card]: https://huggingface.co/imadityasarkar/satquery-phase2-vrsbench/blob/f572b6334ca4b9eb7fdd0bf20dc6420f0c11f3a4/README.md
[a-hf3-card]: https://huggingface.co/imadityasarkar/cdvqa_change/blob/baa5d2fd9336b74007fc39cb24724bc1880e9b91/README.md
[s-head]: https://github.com/siddhtyagi18/SatQuery-AI/commit/0d0cb3ba5ffc04eaa181111793a83352b670c581
[s-meta]: https://api.github.com/repos/siddhtyagi18/SatQuery-AI
[s-tags]: https://api.github.com/repos/siddhtyagi18/SatQuery-AI/tags
[s-releases]: https://github.com/siddhtyagi18/SatQuery-AI/releases
[s-readme]: https://github.com/siddhtyagi18/SatQuery-AI/blob/0d0cb3ba5ffc04eaa181111793a83352b670c581/README.md
[s-tree]: https://api.github.com/repos/siddhtyagi18/SatQuery-AI/git/trees/0d0cb3ba5ffc04eaa181111793a83352b670c581?recursive=1
[s-acceptance]: https://github.com/siddhtyagi18/SatQuery-AI/blob/0d0cb3ba5ffc04eaa181111793a83352b670c581/backend/data/results/FINAL_SIH_ACCEPTANCE_REPORT.json
[s-exp4-config]: https://github.com/siddhtyagi18/SatQuery-AI/blob/0d0cb3ba5ffc04eaa181111793a83352b670c581/backend/checkpoints/experiment_04/experiment_config.json
[s-baseline]: https://github.com/siddhtyagi18/SatQuery-AI/blob/0d0cb3ba5ffc04eaa181111793a83352b670c581/evaluation_results/baseline_run/test_full_results.json
[s-exp3]: https://github.com/siddhtyagi18/SatQuery-AI/blob/0d0cb3ba5ffc04eaa181111793a83352b670c581/evaluation_results/experiment_03_eval/test_full_results.json
[s-exp4]: https://github.com/siddhtyagi18/SatQuery-AI/blob/0d0cb3ba5ffc04eaa181111793a83352b670c581/evaluation_results/experiment_04_eval/test_full_results.json
[s-eval]: https://github.com/siddhtyagi18/SatQuery-AI/blob/0d0cb3ba5ffc04eaa181111793a83352b670c581/backend/scripts/evaluate_full_test_and_val.py
[s-vqa-eval]: https://github.com/siddhtyagi18/SatQuery-AI/blob/0d0cb3ba5ffc04eaa181111793a83352b670c581/backend/checkpoints/vqa_lora_experiment_01/evaluation_results.json
[s-exp1-report]: https://github.com/siddhtyagi18/SatQuery-AI/blob/0d0cb3ba5ffc04eaa181111793a83352b670c581/evaluation_results/EXPERIMENT_01_RESULTS.md
[s-root-result]: https://github.com/siddhtyagi18/SatQuery-AI/blob/0d0cb3ba5ffc04eaa181111793a83352b670c581/evaluation_results/test_full_results.json
[s-root-sweep]: https://github.com/siddhtyagi18/SatQuery-AI/blob/0d0cb3ba5ffc04eaa181111793a83352b670c581/evaluation_results/val_threshold_sweep.json
[s-exp4-report]: https://github.com/siddhtyagi18/SatQuery-AI/blob/0d0cb3ba5ffc04eaa181111793a83352b670c581/evaluation_results/EXPERIMENT_04_RESULTS.md
[s-config]: https://github.com/siddhtyagi18/SatQuery-AI/blob/0d0cb3ba5ffc04eaa181111793a83352b670c581/backend/app/config.py
[s-env]: https://github.com/siddhtyagi18/SatQuery-AI/blob/0d0cb3ba5ffc04eaa181111793a83352b670c581/backend/.env.example
[s-model]: https://github.com/siddhtyagi18/SatQuery-AI/blob/0d0cb3ba5ffc04eaa181111793a83352b670c581/backend/app/services/model_inference.py
[s-fusion]: https://github.com/siddhtyagi18/SatQuery-AI/blob/0d0cb3ba5ffc04eaa181111793a83352b670c581/backend/app/services/models/optical_sar_fusion.py
[s-sar]: https://github.com/siddhtyagi18/SatQuery-AI/blob/0d0cb3ba5ffc04eaa181111793a83352b670c581/backend/app/services/optical_sar.py
[s-orchestrator]: https://github.com/siddhtyagi18/SatQuery-AI/blob/0d0cb3ba5ffc04eaa181111793a83352b670c581/backend/app/services/orchestrator.py
[s-router]: https://github.com/siddhtyagi18/SatQuery-AI/blob/0d0cb3ba5ffc04eaa181111793a83352b670c581/backend/app/routers/analysis.py
[s-validation]: https://github.com/siddhtyagi18/SatQuery-AI/blob/0d0cb3ba5ffc04eaa181111793a83352b670c581/backend/app/services/result_validation.py
[s-confidence-tests]: https://github.com/siddhtyagi18/SatQuery-AI/blob/0d0cb3ba5ffc04eaa181111793a83352b670c581/backend/tests/test_confidence_integrity.py
[s-change-vqa]: https://github.com/siddhtyagi18/SatQuery-AI/blob/0d0cb3ba5ffc04eaa181111793a83352b670c581/backend/app/services/change_vqa.py
