# Development evaluation, not final benchmark
| Category | Original | Adapter | Development majority |
|---|---:|---:|---:|
| Rural/urban | 0/20 | 15/20 | 11/20 urban |
| Presence | 10/20 | 15/20 | 16/20 yes |
| Comparison | 13/20 | 17/20 | 10/20 either |
| Total | 23/60 | 47/60 | 37/60 |

Original 38.33%, adapter 78.33%, majority 61.67%. The majority is a descriptive baseline computed from development labels, not a model selected without observing development labels.
Same prompts, RGB processor, 64–128 visual tokens, deterministic max16 output tokens. Normalize lower-case/whitespace, remove trailing space .!? characters, require exact reference equality. Invalid formatting counts wrong.
20 original format failures, zero adapted. Pair transitions: 11 valid-format wrong-label → correct-label, 15 invalid-format → correct-label, 2 regressions, 32 unchanged correctness.
Do not claim all 24 net gains prove better visual reasoning. All 20 rural/urban original outputs were format-invalid; some already named the correct class. The adapter underperforms the majority baseline on presence.
60 questions share only 20 images; samples are correlated and from one dev scene. Published labels may be noisy, upstream exposure unknown, no independent hand-label audit or statistical generalization claim.
Exact predictions: raw/*predictions.jsonl and metrics/all_prediction_comparisons.csv.

## Frozen diagnostic / final test
Earlier original-model diagnostic: 24/60 (40%), presence10/20, comparison14/20, rural0/20; 20 format failures. This uses a DIFFERENT 60-image set and must not be paired with 47/60.
It has already been inspected, so is not a fresh final test. No final held-out adapter test is available in this handoff; freeze configuration and reserve a fresh final split before running it.
