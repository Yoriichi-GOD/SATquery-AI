# VQA fine-tuning cycle — 8 November 2026

The user authorized an overnight local training and VRSBench evaluation cycle. The current release and Day 1 tag are preserved; this work is isolated on `codex/vqa-finetuning-20261108`.

**Completed 8 November at 11:42 IST**, including recovery after a laptop shutdown. The full 37,409-question matched comparison produced 12,163 baseline versus 23,379 adapter matches: **32.51% versus 62.50% normalised whole-answer exact match**. The predeclared native-file overlap diagnostic identified two training/evaluation duplicate images, covering six questions. Excluding them leaves 37,403 questions and **32.51% versus 62.49%**. Full exports and both cohorts were independently recounted. [Final report and limitations](../../research/results/vqa-finetuning-20261108/overnight-20261108-v2/REPORT.md).

This is one configuration and one seed under a fixed short-answer prompt and 32-token output cap. The score includes answer-format effects; it is not the published GPT-judge metric or proof of improved visual reasoning, geographic transfer or end-to-end application accuracy. Foundation-model exposure remains unknown, historical benchmark inspection is disclosed, and production defaults remain unchanged.

## Definition of done

- [x] Verify the current model/data identities and disclose historical benchmark exposure and its unknowns.
- [x] Test split separation, target masking, scorer behavior and real GPU memory/backward execution before the long job.
- [x] Train a separate LoRA adapter on eligible official training data, with caption replay and validation-only checkpoint selection.
- [x] Freeze checkpoint and inference identities before acquiring final references; run both arms on all pinned VRSBench evaluation questions.
- [x] Retain raw predictions, full denominators, failures, resources, per-category results and paired uncertainty; verify adapter reload and independently recount both full and overlap-excluded results.
- [x] Preserve production defaults and the Day 1 tag. Keep exact-answer improvement distinct from visual-reasoning or application-integration claims.

The [frozen experiment configuration](../../research/experiments/vqa-finetuning-20261108.json) sets the data/label boundaries, seed, candidate/checkpoint budget, resource ceilings, inference controls and selection gates. Maximum budget: 12 elapsed hours for the worker, 6 GiB public downloads, one candidate configuration and no paid compute or paid evaluator. Native data and weights remain local and ignored by Git.

## Direct findings before training

- The served baseline is `AdaptLLM/remote-sensing-Qwen2-VL-2B-Instruct`, revision `7f5dd71bf0f40c282193d50160e848a387a08ffe`.
- The old rank-4 pilot used 720 optimization examples and narrow yes/no/rural–urban targets. Its 60-question development improvement does not demonstrate broad VQA generalization.
- The pinned official VRSBench training JSON contains 142,390 rows: 85,813 VQA, 20,264 caption and 36,313 referring-expression rows, over 20,262 image filenames. This run excludes referring-expression training.
- Splits are separated by filename-source groups and native image hashes. Filename grouping does not establish geographic independence, and upstream foundation-model exposure cannot be excluded.
- Historical VRSBench evaluation already exists, including the 45-question/12-image diagnostic. Its zero whole-presented-answer matches are not zero semantic accuracy. This cycle compares raw model answers and reports prompt-only gains separately.

## Scoring boundaries

The [VRSBench authors](https://github.com/lx709/VRSBench) use GPT-based judging in their final published VQA results. Our deterministic scores are **not that metric**. Strict matching and the frozen normalization rules (Unicode/case/space, terminal punctuation, hyphen/underscore spacing, and standalone number words zero–twenty) compare the entire answer. No substring extraction, post-hoc synonym lists or answer-aware prompt selection is allowed. Truncated/failed/missing answers remain unsuccessful in the full denominator.

The [upstream model card](https://huggingface.co/AdaptLLM/remote-sensing-Qwen2-VL-2B-Instruct) and [training-data card](https://huggingface.co/datasets/AdaptLLM/remote-sensing-visual-instructions) identify its domain adaptation. The named upstream caption corpora are not proof that all VRSBench/foundation-model overlap is absent. VRSBench text annotations are CC-BY-4.0; source imagery has separate terms, including academic-only DOTA restrictions. No raw-image redistribution is introduced.

The existing tested Transformers/PEFT training path is reused; no TRL migration or quantized-model substitution is required. [Qwen2-VL documentation matching Transformers 4.51.3](https://huggingface.co/docs/transformers/v4.51.3/en/model_doc/qwen2_vl) describes the processor/model interface. All claimed gains must be supported by the new run's artifacts, not expected benefits of LoRA.

## Verified before the long worker

- 327 application regression tests passed, including 15 new pure split/scorer/target-mask contracts.
- Five Torch contracts passed for exact-pixel/grid cache invalidation, inference-only use and restoration of the native encoder.
- Eight actual training updates changed 224 LoRA tensors (2,179,072 trainable parameters), with finite losses and 4.90 GiB peak allocation at the selected 256–512 visual-token setting.
- A discarded closed-loop preflight wrote/evaluated two checkpoints and reproduced all eight answers after adapter reload. These are mechanical checks, not VQA accuracy results.
- The prepared corpus has 9,216 training examples (8,192 VQA plus 1,024 captions), 1,093 validation VQA questions and 32 caption examples on the training holdout. Train/dev native pixel hashes and filename-source groups are disjoint.
- A proposed per-image vision optimization changed 3/64 greedy answers and was rejected. The retained method reuses the **original native batch encoder result** only across identical pixel/grid tensors in the baseline and adapter passes. It matched all 32 baseline and all 32 smoke-adapter answers against separate native runs. Resource probes are not independent performance/accuracy benchmarks.

[Data audit](../../research/results/vqa-finetuning-20261108/DATA_AUDIT.json) ·
[GPU feasibility](../../research/results/vqa-finetuning-20261108/GPU_FEASIBILITY.json) ·
[Closed-loop check](../../research/results/vqa-finetuning-20261108/CYCLE_SMOKE.json) ·
[Native-path parity](../../research/results/vqa-finetuning-20261108/NATIVE_BATCH_PARITY.json) ·
[Rejected optimization](../../research/results/vqa-finetuning-20261108/VISION_PARITY.json) ·
[Source receipts](../../research/results/vqa-finetuning-20261108/SOURCE_RECEIPTS.json).

## Execute and inspect

Provision the pinned base model using the existing [asset instructions](../ASSETS.md) and activate a compatible Python 3.11 CUDA/PEFT environment. The model loader is local-only. Preparing the native data requires public network access; no paid API is used.

```sh
python -m research.vqa.prepare
python -m research.vqa.campaign --run-id a-fresh-run-id
```

Each run creates a fresh private runtime directory and a separate result subfolder beneath `research/results/vqa-finetuning-20261108/`. Existing run identities are never overwritten. Raw imagery, model weights and intermediate predictions remain ignored; completed compact prediction exports and measured summaries are written into the result subfolder. The final reference JSON is not acquired until the candidate/checkpoint/inference identities are frozen. Unlabelled final image bytes may prefetch during training without entering optimization.

On the current Windows/WSL host, `scripts/launch_vqa_overnight.py --run-id NAME` waits for the worker and temporarily requests that Windows remain awake. Use the documented existing `/root/satquery/.venv` GPU environment; this is a host-specific launcher, not a portable runtime claim. The request is released when the helper exits. Keep the laptop plugged in with its lid open.

Progress is recorded in `.runtime/vqa-20261108/current-status.json`, the run's `heartbeat.json`, its archive status, and the worker log. These are execution state, not measured model gains. A failed or incomplete run must not be reported as a completed benchmark. The worker does not change production model defaults or the Day 1 tag.

### Recover a frozen evaluation after power loss

Confirm worker/launcher processes are absent and the heartbeat is stale before preserving its old lock. Do not remove a live worker's lock. Preserve the interrupted status, heartbeat and lock as evidence. The recovery path applies only after a sealed candidate and final-reference identity exist; it never resumes or repeats training.

```sh
python scripts/vqa_evaluation_recovery.py --run-id EXISTING-RUN --attempt-id UNIQUE-ATTEMPT --audit-only
python scripts/launch_vqa_overnight.py --run-id EXISTING-RUN --resume-frozen-evaluation --attempt-id UNIQUE-ATTEMPT
```

Inspect the audit before launch. It checks the native archive and unchanged reference seal, then validates both arms' hashes, identities and support batch by batch. An unexpected pattern of widespread damage requires diagnosis rather than a blind restart. Preserve the stale lock before launching. The worker verifies the original model weights and runtime, reproduces 32 saved answers per arm, rechecks all native evaluation images and retained prediction hashes, and preserves invalid/incomplete batches before repeating them. The original wall-time ceiling, frozen model, scoring rules and full denominator remain unchanged. Empty/error attempts remain failures. No production promotion occurs automatically.
