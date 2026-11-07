# VQA fine-tuning cycle — 8 November 2026

The user authorized an overnight local training and VRSBench evaluation cycle. The current release and Day 1 tag are preserved; this work is isolated on `codex/vqa-finetuning-20261108`.

## Definition of done

1. Verify the current model/data identities and historical benchmark exposure.
2. Test split separation, target masking, scorer behavior and real GPU memory/backward execution before the long job.
3. Train a separate LoRA adapter on eligible official training data, with caption replay and validation-only checkpoint selection.
4. Freeze checkpoint and inference identities before acquiring final references; run baseline and candidate on the pinned VRSBench evaluation questions.
5. Retain raw predictions, every eligible denominator, failures, resources, per-category results and paired uncertainty. Reload the adapter and verify genuine inference before any integration decision.
6. Keep production defaults unchanged until review of the measured result. A running job, lower training loss or answer-format improvement alone is not completion or proof of better visual reasoning.

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
