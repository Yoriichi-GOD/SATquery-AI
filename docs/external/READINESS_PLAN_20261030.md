# External dataset readiness — 30 October 2026

User supplied the external-readiness brief and authorized implementation. Prior organizer clearance for extending SATQuery/Flood Lab and use of the main SATquery-AI repository remain recorded in docs/jai/JAI_RULE_COMPLIANCE.md. No official checkpoint time/tag is assumed.

Starting source: 8513ac3a7290b2aa19c312dd18c9486cd27f4769 on jai-flood-terrain-20261030; clean before this task. Original services on 8765/8767 and Flood Lab source/evidence are preserved. Local optional extension runs on 8768 and its owned Flood Lab on 8770.

## Definition of Done

1. Inspect TIFF/directories/multi-file input and validated ZIPs in private storage, with chunked hashing, bounded native raster reads, disk/size/concurrency controls, resumable upload, cancellation and interrupted-state recovery.
2. Emit every inspected compatibility requirement and every blocking reason for ten actual specialist contracts. No inference from file readability alone; source authenticity stays separate.
3. Execute only an eligible, explicitly selected specialist through existing code; preserve original bytes and refuse implicit preparation.
4. Freeze an evaluation protocol before using labels. Compute independent segmentation, classification, multilabel or exact/declared-normalized VQA metrics; no compatible labels means no accuracy/IoU/F1.
5. Export immutable runs, hashes, software/model/input provenance and executable independent metric verification.
6. Demonstrate browser intake/preflight/execution/evaluation/export and failure/cancel behavior. Measure a roughly 3 GB sparse/tiled fixture separately from real scientific data; report actual logical/allocated size and peak RSS.
7. Run regression checks, retain failures and make authentic incremental pushes. Report what remains unverified. Do not create an official day1-final tag without a verified checkpoint.

## Evidence so far

- Read actual server, input, controller, WaterUNet, BIFOLD, MCI, SAR, CDVQA, spectral/NDVI and terrain code, current architecture/acceptance protocols, and preserved Flood Lab core/pipeline contracts.
- Existing paired upload reads an entire small file (20 MB cap); the new dataset path stays separate and preserves those specialist bounds.
- Existing full suite: 190 passed. New bounded-intake/security/metric correctness checks: 25 passed. Combined 215 passed at the first implementation milestone.
- GDAL substitutes identity for a missing/all-zero transform. The inspector now distinguishes numerical transform validity from actual georeferencing; a retained singular matrix is tested separately.
- Model audit: CUDA available; WaterUNet, MCI, CDVQA and encoder file hashes match their pinned inventory. Qwen/BIFOLD/grounding assets are present but not all independently hashed/executed by that audit. The installed-package audit reports timm/einops missing for MCI/BIFOLD; do not declare those paths ready without further runtime verification.
- No external judge dataset or independent judge labels were supplied. Synthetic known-answer checks are software correctness, not new scientific benchmarks.
- No Copernicus credential variable names exist in the current WSL launch environment. Existing Flood Lab configuration is examined by names/presence only; no token scope/access or acquisition is claimed.
- Terrain colour is restored with green/olive/brown elevation and yellow/orange/red slope. Only the analytical colour scale changed; black UI panels and original numerical values remain.

## Execution boundary

No retraining, public deployment, automatic source acquisition, silent resampling/reprojection, fake quality masks, benchmark rewriting or tuning on evaluation labels. Flood Lab retains its event/OSM requirements; an arbitrary TIFF is not a substitute for a prepared event bundle.

The first milestone contains the intake/contract/metric foundation. API/worker/CLI/export/browser/resource closure follows; this document is not a claim that the full Definition of Done already passed.
