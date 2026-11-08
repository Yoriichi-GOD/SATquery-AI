# VQA adaptation and full VRSBench evaluation

Full pinned model-only VRSBench VQA; deterministic whole-answer diagnostics, not the published GPT-judge metric or end-to-end application accuracy

| Arm | Questions | Correct | Normalised exact match | Strict exact match | Errors | Truncated |
|---|---:|---:|---:|---:|---:|---:|
| base | 37409 | 12163 | 32.51% | 32.26% | 0 | 4741 |
| candidate | 37409 | 23379 | 62.50% | 61.85% | 0 | 0 |

Paired gain: 29.98 percentage points; 95% filename-group bootstrap interval [0.2912859007832898, 0.3086769783566797].

Selected only on the official-training holdout and frozen before final-reference access. Historical inspection and unresolved foundation-model exposure are disclosed. One seed and one configuration; no replicated scientific-superiority claim.

Evaluation resumed after a laptop shutdown with the same frozen adapter, protocol, native inputs and source hashes. Valid completed batches were retained; invalid/incomplete batches were preserved and repeated in their original batch shapes. The original wall-time ceiling was retained.

Published GPT judging was not executed. Production defaults are unchanged. All errors, truncations and missing predictions remain failures in the denominator. Native training/evaluation pixel overlap is reported in FINAL_RESULTS.json.

[Detailed results](FINAL_RESULTS.json) · [Candidate freeze](CANDIDATE_FREEZE.json) · [Recovery](EVALUATION_RECOVERY.json) · [Protocol](../../../experiments/vqa-finetuning-20261108.json)

## Exact native-file overlap

Two evaluation PNGs are byte-identical to actual training PNGs, covering six questions. The predeclared diagnostic excludes their questions from both arms. This is exact native-file deduplication, not proof of distinct geography or absent foundation-model exposure.

| Arm | Questions after exclusion | Correct | Normalised exact match |
|---|---:|---:|---:|
| base | 37403 | 12160 | 32.51% |
| candidate | 37403 | 23375 | 62.49% |

Gain after exclusion: 29.98 percentage points. Both full and overlap-excluded results were independently recounted from the sealed native references and prediction exports. [Recount](INDEPENDENT_RECOUNT.json) · [Exact duplicate verification](OVERLAP_AUDIT.json).

The minimum known historically inspected subset contains 45 questions; its separate scores remain in FINAL_RESULTS.json. Neither remaining cohort is claimed to be pristine or geographically independent. The all-question bootstrap above uses 5,167 filename-source groups, not independently verified geographic regions.

## Full-set results by native question category

| Native category | Questions | Base exact match | Adapter exact match | Gain (pp) |
|---|---:|---:|---:|---:|
| image | 1129 | 14.88% | 89.11% | +74.22 |
| object category | 5434 | 10.60% | 53.75% | +43.15 |
| object color | 3550 | 43.49% | 60.62% | +17.13 |
| object direction | 477 | 15.09% | 45.28% | +30.19 |
| object existence | 7789 | 67.15% | 89.88% | +22.74 |
| object position | 5828 | 18.19% | 50.65% | +32.46 |
| object quantity | 6374 | 36.62% | 51.57% | +14.95 |
| object shape | 1423 | 7.52% | 57.06% | +49.54 |
| object size | 1011 | 11.97% | 49.16% | +37.19 |
| reasoning | 902 | 31.82% | 63.08% | +31.26 |
| rural or urban | 295 | 30.85% | 78.98% | +48.14 |
| scene type | 3197 | 17.92% | 54.21% | +36.28 |

## Scope and remaining work

The same short-answer prompt, greedy decoding, 256–512 visual tokens and 32-token output cap were used in both arms. Whole-answer exact-match gains combine content and answer-format effects; they do not isolate better visual perception or reasoning. Published GPT judging, independent semantic review, geographic transfer and application integration remain unverified.

The official-training holdout used for selection improved from 368/1,093 (33.67%) to 665/1,093 (60.84%). Its score is selection evidence, not a second untouched final test. The adapter was frozen before this full evaluation. No production model switch occurred.

All 336 application regression tests passed, including nine shutdown-recovery contracts. The implementation CI passed. The worker exited successfully at 11:42 IST on 8 November 2026; all 31,156 pre-shutdown predictions per arm retained their original hashes.
