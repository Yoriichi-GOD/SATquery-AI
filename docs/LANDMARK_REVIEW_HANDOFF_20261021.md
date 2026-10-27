# Development crop screening and reviewer package - 2026-10-21

Three additional 1024 x 1024 crop pairs were selected from an optical-only overview for settlement visibility, then inspected in optical and raw SAR. No labels or model scores informed selection. This expands development exposure only; it is not acceptance sampling.

All three provide broader settlement context but no six reliable static control pairs were established by assistant inspection. Accepted landmark count remains zero and displacement metrics remain null. This does not show that alignment is wrong. Repeating the same visual search is now stopped; independent specialist point correspondence review is the actionable dependency.

## Review-ready artifacts

`.runtime/alignment-20261021` contains the selection manifest, three candidate image pairs, full-tile optical overview, source-specific pixel-to-projected-coordinate transforms, SHA256 identities and an unfilled landmark template. All review images are development data.

Use `scripts/measure_landmarks.py INPUT.json NEW_OUTPUT.json` after review. At least six distinct stable correspondences, a projected metre CRS, reviewer identity and combined localization uncertainty per pair are required. The calculator reports signed displacement, median, p95, RMSE and a conservative uncertainty bound. It rejects too few points, nonfinite coordinates, repeated optical points, angular units and points used to fit a warp. It does not certify spatial distribution or CRS truth and never automatically approves alignment.

Agree on task-based tolerances before measuring review points; do not choose them to fit observed residuals. Independent source/feature identification and uncertainty remain reviewer responsibilities. Do not substitute water boundaries or bright SAR scatterers without ground correspondence.

Six synthetic tests passed, including the 3/4-metre shift yielding 5-metre RMSE. Candidate grid dimensions and transforms were checked. All 22 frozen reference files are unchanged. No downloads, training, model inference or serving changes occurred.

The conditional acceptance-sample freeze and modality comparisons remain unexecuted because alignment is not established. This package is ready for review; the larger acceptance objective is incomplete.
