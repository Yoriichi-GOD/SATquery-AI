# Public-image regression: read the metric before using the numbers

**VRSBench: 45 attempted questions on 12 previously used images; 42 completed and 3 refused. The recorded 0/45 is whole-response exact matching, not 0% semantic VQA accuracy. Semantic accuracy was not measured.**

This is a reused-image diagnostic subset, not the complete VRSBench benchmark or an untouched acceptance test. The published VRSBench judging protocol was not run. Completion means execution completed, not that its answer was correct. All 45 attempts remain in the exact-match denominator, including refusals.

## What `exact_match` actually measures

The scorer lowercases text, collapses whitespace and removes terminal `.`, `!` and `?`. It then compares the **entire presented answer** with the short reference. It does not extract an answer, normalize hyphenated synonyms, judge meaning, or remove the appended `Model interpretation; may be inaccurate.` notice. Consequently, explanatory prose or that notice can prevent an otherwise matching short answer from passing.

The original `exact_match` fields and counts are preserved for compatibility and auditability. `scoring_context` now states their definition beside the numbers, with `semantic_accuracy: null`. This annotation does not change any prediction or rescore the experiment. The same whole-response diagnostic limitation applies to the RSVQA-LR rows in this directory.

## Illustrative recorded cases — not a rescoring rubric

| VRSBench question ID | Short reference | Recorded behavior | What it illustrates |
|---|---|---|---|
| 7314 | `swimming-pool` | Answer identifies a swimming pool within a long explanation | The expected concept can appear without whole-response equality; accompanying assertions have not been validated |
| 6463 | `grayscale` | Answer begins “The image is in grayscale” and continues explaining | Correct reference term in prose still fails this diagnostic |
| 456 | `harbor` | Answer identifies a bridge and speculates further | A substantive reference disagreement, not merely formatting |
| 457 | `forested` | “What kind of area surrounds the harbor?” was refused | An execution/routing failure in the recorded revision |
| 6465 | `top-right` | Angular-bridge position question was refused | A routing refusal rather than a model answer |
| 10050 | `top` | Roundabout position question was refused | A second position-query refusal |

These examples are checked against saved text/reference pairs, not a fresh image-level adjudication. Finding the expected word is insufficient to certify an entire response as correct. Wrong answers, unsupported explanations, contradictions and truncation must remain visible.

## Reporting and future evaluation

Use: **“45-question VRSBench diagnostic; 42 completed, 3 refused. Whole-response exact match: 0/45; semantic correctness not scored.”** Do not label this `VRSBench accuracy: 0%`, and do not replace it with a guessed semantic score or treat completion rate as accuracy.

A future semantic review must define answer extraction, accepted aliases, contradiction handling and refusal denominators before scoring. Reviewing these already-inspected rows would be retrospective diagnostic analysis. Freeze the protocol before applying it to an unseen evaluation. No such replacement score is supplied here.

## Audit trail

- [Raw predictions and execution records](rows.jsonl): unchanged.
- [Summary with inline scoring context](summary.json): original numerical fields unchanged.
- [Original manifest and scoring definition](manifest.json): unchanged.
- [Annotation integrity record](interpretation-note.json): original row hash and unchanged-count checks.
- [Runner](../../../scripts/run_public_regression.py): future summaries receive the same explanatory metadata; inference and scoring logic are unchanged.
