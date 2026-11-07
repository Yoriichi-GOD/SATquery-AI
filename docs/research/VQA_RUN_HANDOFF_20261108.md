# VQA overnight execution receipt

Started **8 November 2026, 01:50 IST** (7 November 20:20 UTC).

Run identity: `overnight-20261108-v1`.

The user authorized overnight local GPU use. This receipt records launch and monitoring locations; it does **not** claim training success, improved accuracy or benchmark completion.

| Item | Location / identity |
|---|---|
| Branch | `codex/vqa-finetuning-20261108` |
| Training/evaluation implementation commit | `71b257b` |
| Base checkpoint | AdaptLLM remote-sensing Qwen2-VL-2B, revision `7f5dd71bf0f40c282193d50160e848a387a08ffe` |
| Frozen protocol | `research/experiments/vqa-finetuning-20261108.json` |
| Corpus | 9,216 training examples; 1,093 validation questions; disjoint native hashes and filename-source groups |
| Windows launcher PID at startup | 3900 |
| WSL worker PID at startup | 2317 |
| Current state | Re-read `.runtime/vqa-20261108/current-status.json`; never infer it from this static receipt |
| Worker output | `.runtime/vqa-20261108/overnight-20261108-v1.worker.log` |
| Detailed run artifacts | `.runtime/vqa-20261108/overnight-20261108-v1/` |
| Public research artifacts | `research/results/vqa-finetuning-20261108/overnight-20261108-v1/` |

The Windows launcher successfully requested temporary prevention of automatic system sleep; the laptop was on AC power at startup. Its request is released when the launcher exits. Keep the lid open and power connected.

The worker runs the baseline first, trains and chooses checkpoints on the official-training holdout, verifies adapter reload, freezes the candidate, and only then acquires final VQA references. Unlabelled native evaluation images may prefetch during training. Fixed model-only exact-match diagnostics are distinct from the benchmark's published GPT judging, which is not authorized or executed here.

Completed output must include `CANDIDATE_FREEZE.json`, `FINAL_RESULTS.json`, compact prediction exports and `REPORT.md`. A heartbeat, lower loss or a nonempty checkpoint is not sufficient. Preserve partial/error evidence if execution fails. Do not alter loaded `research/vqa/*.py` sources while this run is active; the worker checks their hashes.

The current production defaults, historical reports and immutable `day1-final` remain protected. Promote no adapter based on training loss alone. [Method and verification](VQA_FINE_TUNING_20261108.md).
