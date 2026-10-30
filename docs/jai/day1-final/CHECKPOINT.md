# Official Day 1 checkpoint — Rule T4

The participant explicitly called the official Day 1 checkpoint on 30 October 2026 and instructed an immediate freeze. Feature work is paused. The immutable Git tag **day1-final** identifies the exact verified-progress commit. Its full SHA is recorded in the submission receipt after the tag is pushed; no backdating or history rewrite is performed. Work after this tag is Day 2 development.

> Mandatory Day 1 Checkpoint (Rule T4): At the official Day 1 checkpoint, commit and push all verified progress, create and push the Git tag day1-final on that exact commit, record its full SHA for submission to the organizers, and continue Day 2 development without altering or rewriting the Day 1 history.

## Implemented and verified progress

- Native black Terrain & flood workspace combines saved observations, the real cached 90 m DSM, grid-mapped candidate markers and adjacent source-based questions. Evidence and sources are folded. Elevation/slope colours were restored while the surrounding interface remains black.
- Private external-dataset intake uses 8 MiB HTTP chunks, streamed SHA-256, bounded native TIFF windows, source retention, disk/size caps, ZIP traversal/link/bomb rejection, isolated operations and Stop. Dataset/model compatibility is reported per parameter without implicit raster preparation.
- Independent segmentation, classification, multilabel and VQA metric code, immutable export runs and a verifier exist. The CLI can recompute exported metrics without the dashboard or model weights. Missing labels explicitly produce EVALUATION_NOT_POSSIBLE and no accuracy/IoU/F1.
- Latest checkpoint regression: 221 main tests passed. Both new external-workflow and terrain JavaScript syntax checks passed. This is software verification, not certification of every model/adapter.
- Genuine historical Ghana_313799 was streamed, inspected and executed through WaterUNet. Its unchanged prediction was then evaluated against the existing independent reference: water IoU 0.4667192046556741; F1 0.6364124819177516; TP 7699, FP 1563, TN 227968, FN 7234. Denominator 244464 pixels; 17680 excluded. Export hashes and metrics recomputed exactly. This previously evaluated chip is regression/reproduction evidence, not a new untouched benchmark or a claimed accuracy improvement.
- Synthetic 3 GiB resource fixture: 3221225472 bytes uploaded in 384 chunks; upload 83.9305 s; full inspection wall time 30.8984 s; sampled inspector peak RSS 105369600 bytes. Status requests remained responsive (maximum 0.00414 s in 12 samples). This is a sparse BigTIFF resource test with a physically written private upload, not real unfamiliar satellite data. The actual judge dataset remains unavailable.

## Honest open items for Day 2

- External browser flow is partly tested: actual file selection, role assignment, upload, inventory and complete mismatch/preflight panels were exercised. The final execution/evaluation/download click sequence and responsive screenshots are not closed. A browser-detected stale-result issue was fixed; further replay remains required.
- The existing optical Qwen service has no verifiable cancellation endpoint, so external Qwen execution is explicitly withheld. Arbitrary external Flood Lab event bundles are not executed; the original prepared event/OSM workflow and calculations are preserved.
- Runtime dependency checks initially disagreed with the engine's vendored dependency path. The audit now includes that path, but real execution proof for every MCI/BIFOLD/CDVQA adapter is pending. Model presence alone is not a pass.
- Actual unfamiliar 3 GB judge data, new independent evaluation population and broad model-specific acceptance remain untested. No retraining or tuning on judging labels occurred. Independent physical co-registration, validated flood depth, damage, safety, evacuation and forecasting are not established.
- The full external-readiness brief is not claimed complete. This tag freezes verified Day 1 progress and its explicit limitations. Original frozen scientific benchmarks and Flood Lab source remain unchanged.

## Independent verification

```sh
git checkout day1-final
python -m unittest discover -s tests -q
node --check paired_lab/web/external.js
node --check jai_extension/web/earth.js
python scripts/verify_external.py /absolute/path/to/exported/run
```

The private historical evaluation export remains at `.runtime/external/jobs/002e68240e68477da4a6b3b5146ba704/evidence` on the configured host; input/model assets are not redistributed in Git. See the copied receipts for exact denominators, source revision, hashes, timings and limits; the resource test predates the final metadata/preview hardening. Source hashes for the final checkpoint implementation are in SOURCE_HASHES.json.

## Day 2 history rule

Continue on the current event branch with new commits descended from day1-final. Never move, delete, recreate or force-push the Day 1 tag; never amend/rebase the frozen Day 1 commits. If later verification finds a problem, retain this history and record the correction in a new Day 2 commit.
