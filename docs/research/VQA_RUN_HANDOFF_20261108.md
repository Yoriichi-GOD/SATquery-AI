# VQA overnight execution receipt

## Latest: frozen evaluation resumed after laptop shutdown

On 8 November the laptop shut down during the full paired evaluation. The last status flag still said running, but launcher/worker processes were absent and the heartbeat was stale. Training had completed all 1,536 updates and the candidate had already been frozen. Its official-training holdout score is **665/1,093 (60.84%)**, compared with **368/1,093 (33.67%)** for the matched-prompt base model; truncations fell from 167 to zero. These are selection-validation diagnostics, not the final benchmark result. [Measured training results](../../research/results/vqa-finetuning-20261108/overnight-20261108-v2/TRAINING_RESULTS.json).

Recovery attempt `power-recovery-20261108-verified` retained **31,156 hash-verified predictions per arm** and identified two damaged/incomplete tail batches. The native archive, original source, corpus, final-reference seal, candidate freeze and model weights remain fixed. Both model arms must reproduce 32 saved validation answers before new benchmark inference proceeds. Invalid batches are preserved and repeated with their original batch shapes; valid predictions must retain their original hashes. No retraining or checkpoint reselection occurs.

The original **14:21 IST** wall-time ceiling is retained, including downtime. Current state remains `.runtime/vqa-20261108/current-status.json`; the resumed log is `.runtime/vqa-20261108/overnight-20261108-v2-power-recovery-20261108-verified.worker.log`. Software recovery contracts cover torn data, foreign identities, missing arms, reference seals, failed-attempt denominators and the original deadline. Final benchmark results remain pending until `FINAL_RESULTS.json`, both full prediction exports and `REPORT.md` are complete.

## Earlier launch and recovery records

**Active recovery run: `overnight-20261108-v2`, launched 8 November 2026 at 02:21 IST.** The machine restarted during v1 after 29 retained optimizer updates, before a saved training-validation checkpoint. The interrupted run is preserved and disclosed; no tuning gain or completed full benchmark is claimed.

The replacement uses identical training code, protocol and corpus hashes. All 2,304 native training images were rehashed. The complete 3,976,656,690-byte evaluation-image archive matches the pinned upstream SHA-256 `67f99c1dd437fdab94fea1f54e049ad56d198c3c873237c79d9b944200d248b1`. Cumulative conservative download accounting, including the interrupted transfer, is 5,184,033,359 bytes against the unchanged 6 GiB ceiling.

Current worker PID at recovery launch: **370** in WSL; Windows launcher **31404**. Read `.runtime/vqa-20261108/current-status.json` for live state. Recovery output is `.runtime/vqa-20261108/overnight-20261108-v2.worker.log`; public results will be under `research/results/vqa-finetuning-20261108/overnight-20261108-v2/`. The replacement repeats baseline measurement before optimization and keeps the 12-hour per-run ceiling.

Git references and the zero-filled worktree index were restored from backed-up evidence after read-only verification of all 14 reference objects. Working files, Git objects, reflogs, remote history and `day1-final` were not rewritten. Full Git object verification with reflog checking excluded and all 15 VQA contract tests passed after recovery. The original damaged metadata and interrupted data remain in ignored recovery storage.

See the [interruption receipt](../../research/results/vqa-finetuning-20261108/overnight-20261108-v1/INTERRUPTION.json) and [recovery verification](../../research/results/vqa-finetuning-20261108/overnight-20261108-v2/RECOVERY_VERIFICATION.json). Completed output is still required before any improvement claim.

## Original launch record

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

## First completed measurement

This measurement belongs to v1's completed baseline phase. The replacement run measures its own matched baseline again before training; these figures are not substituted for its results.

The complete official-training holdout baseline produced **368/1,093 normalised whole-answer matches (33.67%)** and 363 strict matches, with zero missing predictions, zero execution errors and 167 output-limit truncations. These are diagnostic exact-match scores under the fixed 32-token inference limit, not the published VRSBench GPT-judge metric.

On the same 64-question diagnostic subset, the raw prompt produced 5 matches and 56 truncations; the short-answer instruction produced 19 matches and 12 truncations. This is a prompt effect, not a fine-tuning gain. Both measured model arms use the same short-answer instruction.

All 9,216 training examples passed the fixed sequence-length audit. Optimizer updates have begun; lower loss is not evidence of improved VQA. Saved checkpoint evaluation, candidate freeze and the full benchmark are still pending at this progress receipt. Re-read live status for the current phase.

Aggregate baseline evidence and hashes are retained in [`BASELINE_VALIDATION.json`](../../research/results/vqa-finetuning-20261108/overnight-20261108-v1/BASELINE_VALIDATION.json), [`PROMPT_DIAGNOSTIC.json`](../../research/results/vqa-finetuning-20261108/overnight-20261108-v1/PROMPT_DIAGNOSTIC.json) and [`BASELINE_RECEIPT.json`](../../research/results/vqa-finetuning-20261108/overnight-20261108-v1/BASELINE_RECEIPT.json).
