# SATquery AI — PPT evidence handoff
Snapshot: 6 September 2026. Start with PROJECT_STATUS.md, then EVALUATION_REPORT.md, NDVI_AUDIT.md and JUDGE_QA.md. REQUEST_COVERAGE.md maps every requested item.
This pack records current evidence, not the final SIH system. No final held-out adapter evaluation or natural-language router is present.

## Numbers safe to quote with their conditions
- Development exact-label score23/60→47/60;60questions/20images,matched protocol. Majority37/60. Format failures20→0;presence adapter15/20 below majority16/20.
- Corrected Dehradun NDVI>=.50:38761/262144pixels=14.79%;387.61ha projected grid area. Independent implementation has0mask disagreements.
- NDVI server-job median.049s over20warm-cache repetitions, excluding upload/download/rendering. See full timer scope.
- LoRA544768trainable;rank4;720steps;peak allocated4.454GiB. Recorded190.024s includes adapted dev evaluation/save, not isolated training.
INVALID historical NDVI46.75%/620.09ha is retained only as audit evidence. Do not put it on slides except to explain the correction.

## Evidence layout
metrics/: machine-readable CSV/JSON. raw/: saved records and source snapshot. examples/: real selected dev images/answers.
diagrams/: measured plots and labelled architecture. exports/: actual analytical rasters/PNGs. screenshots/: genuine browser captures plus labelled saved-record views.
Every claim should be identified as measured, code-inspected, inferred or planned in its report. No field-survey vegetation validation, blanket novelty claim or fabricated historical screenshot.
NEXT_UI_DISCUSSION.md retains the user's next requests without implementing them.

## Reproduction
All executed scripts are under scripts/ and original code snapshots under raw/source/. Runtime is the existing WSL environment. collect.py repeats20NDVIjobs and requires the local app; it does not retrain. Existing local paths are retained intentionally. Training must not be rerun merely to regenerate screenshots.
