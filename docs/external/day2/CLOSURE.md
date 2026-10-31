# Day 2 readiness closure — 31 October 2026

The existing external-dataset workflow is implemented and verified within the boundaries below. No judge dataset has been supplied. This is an intake, execution, evaluation and failure-recovery checkpoint; it is not a new scientific benchmark, an unseen-data acceptance result or a claim that arbitrary 3 GB scenes can run through every model.

Application source tested: **`f6fa44f8e3fbf284deb9fbca2898847453e300a7`**. The final HTTP/browser replay and downloaded-ZIP verification used that clean source revision. This closure and its receipts are a subsequent documentation-only commit. Earlier adapter/model receipts retain their actual revision, dirty-file list and source hashes rather than being relabelled as final-source runs.

Start with the [operator and judge guide](../README.md), including the complete working/blocked specialist matrix and resource limits. The [Day 2 plan](PLAN.md) records the original Definition of Done. The immutable [Day 1 checkpoint](../../jai/day1-final/CHECKPOINT.md) and its historical evidence remain separate.

## A. Implemented changes

Day 1 supplied the private intake, full raster inspection, machine-readable contracts, isolated execution, independent evaluators and evidence export. Day 2 closed the following verified gaps:

| Component | Change and purpose |
|---|---|
| `paired_lab/external_data/contracts.py` | Refuse unequal CDVQA image dimensions, truncated inspection metadata and scaled terrain rasters. Accept actual TIFF RGB colour interpretation without inventing band identities. Report explicit worker limits. |
| `paired_lab/external_data/store.py` | Explicitly restart only incomplete uploads; completed originals remain immutable. |
| `paired_lab/external_data/service.py` | Serialize uploads with worker submission; refuse incomplete/uninspected inputs before launch. Add restart endpoint and require available memory before starting a worker. |
| `paired_lab/external_data/common.py` | Bound inspector to 512 MiB; analysis normally 2 GiB, MCI 3 GiB based on measured cold execution. Validate explicit overrides and reserve 256 MiB free RAM. |
| `paired_lab/external_data/runner.py` | Independently verify a downloaded ZIP directly, with safe bounded extraction. Check copied reference against its recorded source hash and require matching selected inputs when reusing predictions. Return actual analysis output and evaluation scope. |
| `paired_lab/external_data/metrics.py` | Refuse fractional/boolean class IDs and ambiguous mappings; validate scene/exclusion IDs; bound native raster decode blocks to 16 MiB. |
| `paired_lab/web/external.js` | Working progress/Stop/restart, correct busy states, matching saved results, protocol/reference persistence, numerical outputs distinct from scores, and native previews. Dataset changes clear an unrelated previous answer. Full evidence remains in disclosures. |
| `paired_lab/web/index.html` | Version external assets so a cached Day 1 controller cannot obscure current behaviour. |
| `tests/test_external_day2.py` | Thirteen new regressions covering contracts, immutable restart, worker concurrency, downloaded ZIPs, source hashes, mappings, large native blocks, memory refusal and timeout recovery. |
| `scripts/verify_external_http.py` | Reusable local-only HTTP smoke/failure checker with clearly synthetic fixtures and retained receipts. |

Existing routes under `/api/datasets` include registration/list/inventory, contract registry, file registration/chunk upload/finish/role/preview, cancel-upload, inspect, JSON/CSV compatibility, analyze, evaluate, job status/cancel and named evidence exports. New Day 2 route: **`POST /api/datasets/{did}/files/{fid}/restart`**. HTTP accepts registered opaque IDs, not arbitrary filesystem paths. Intake remains local-only.

## B. Working and blocked paths

The [compatibility matrix](../README.md#compatibility-and-execution-boundaries) records exact sensor, product, calibration, grid, band, time and dimension constraints. Header compatibility is distinct from sensor authenticity and physical co-registration. Unknown metadata is not filled in to make a model eligible.

- Genuine retained Dehradun Sentinel-2 data ran the NDVI adapter. A genuine retained LEVIR RGB pair ran CDVQA with a supported exact question. Both lack suitable independent references for these runs, so neither receives an accuracy score.
- Historical Ghana WaterUNet evidence remains available as an already-examined regression case. It is not a new acceptance population.
- Retained MCI and BIFOLD publisher fixtures executed their actual original model calls. Those model-only checks do not establish external geographic compatibility. Missing geographic metadata is correctly refused by the external path; no CRS or date was fabricated.
- External Qwen execution remains withheld because the shared original service lacks a verified isolated cancellation boundary. Original Workspace functionality is preserved.
- Arbitrary external Flood Lab event bundles remain disabled. The existing prepared SAR event/OSM workflow, terrain integration and calculations are preserved.
- Spectral pair, SAR scene and terrain contracts remain available with existing numerical/regression checks. No new genuine two-date spectral or georeferenced external MCI/BIFOLD benchmark was run in this closure.

## C. Evaluation evidence

| Evidence | What was actually measured | Scope |
|---|---|---|
| Final browser dataset `11b7f8cb12004ac5af1615dda8a01104`, evaluation `fada694563774ff093ee28fbcb00e3bf` | 257,024 evaluated pixels, 5,120 ignored; each class support 128,512. Known-answer IoU/F1 1.0. A separately authored reference and frozen threshold/protocol exercise the evaluator. | **Hand-constructed software correctness fixture only. Not satellite ground truth, scientific performance or judge data.** |
| Dehradun NDVI and LEVIR CDVQA | Actual outputs, input/checkpoint/source hashes and timings retained in [adapter receipt](ADAPTER_RECEIPT.json). | Execution without compatible ground truth: `EVALUATION_NOT_POSSIBLE — COMPATIBLE_GROUND_TRUTH_NOT_PROVIDED`. |
| Historical Ghana case | Water TP 7,699; FP 1,563; TN 227,968; FN 7,234. IoU 0.4667192046556741; F1 0.6364124819177516; 244,464 evaluated, 17,680 excluded. | Previously evaluated Day 1 regression, not an untouched external test or Day 2 improvement. |
| BIFOLD model fixture | Actual optical, SAR and paired calls, 19-class outputs; no independent score. | Original publisher fixture, model-only smoke check. |
| MCI model fixture | Fresh isolated CPU call: 8.8113 s, 2,198,929,408 bytes observed peak RSS; 65,536 output pixels. | Model-only smoke check. This observed peak motivated a 3 GiB external worker ceiling; it does not establish accuracy. |

The final browser ZIP had **20 verified artifacts** and SHA-256 **`9e4b027ef8b56e0b3102b9205328984df22e4c1ddcc8716d34028ff019e4d3cd`**. The separate verifier accepted the actual downloaded ZIP, checked hashes/reference linkage and recomputed its metrics. See [final receipt](FINAL_VERIFICATION_RECEIPT.json) and the [software fixture protocol](FINAL_BROWSER_PROTOCOL.json).

The bundle is retained privately at the local browser download `evidence (2).zip`, and the run remains downloadable from the local dashboard. Source images, reference copies, private archives and model weights are not added to Git. A consistent bundle proves artifact/metric consistency, not independent acquisition authenticity or unseen-data accuracy.

Classification, multilabel and VQA evaluator correctness is covered by software tests. Their known-answer cases do not become scientific benchmark results.

## D. Large-data and resource evidence

The [frozen Day 1 large-data receipt](../../jai/day1-final/LARGE_DATA_RECEIPT.json) records a synthetic sparse/padded BigTIFF, **3,221,225,472 bytes (3 GiB)**, 40,000 × 40,000 pixels, one uint16 band and 256 × 256 native tiles. The uploaded private copy occupied 3,221,225,472 allocated bytes; the sparse source occupied 724,992 allocated bytes. Upload: 384 × 8 MiB chunks, **83.9305 s / 36.6017 MiB/s**. Full inspection wall time: **30.8984 s**, with metadata/native scan **10.1636 s**. Total measured sequence: **115.4284 s**. Sampled inspector peak RSS: **105,369,600 bytes**, below its 512 MiB ceiling; server RSS increase: 12,288 bytes. Sampling can miss brief peaks.

That synthetic resource result is preserved, not presented as a fresh unfamiliar 3 GB satellite-data run. Day 2 additionally stopped and restarted the actual browser transfer of that same registered 3 GiB fixture, observed restart at **20.05208396911621%**, then stopped again; temporary chunks were removed. It was deliberately not a second complete 3 GiB import. [Stop receipt](BROWSER_UPLOAD_STOP.json); [restart receipt](BROWSER_UPLOAD_RESTART.json).

The final defaults inspect up to 4 GiB / 256 files, but a single specialist case still selects at most two inputs and normally requires each input ≤20 MiB, ≤1,048,576 pixels and ≤14 bands, with tighter model constraints. Automatic large-scene tiling, arbitrary sensor conversion and inference batching are not implemented. The inspector and verifier reject native blocks above 16 MiB instead of trusting a small requested window to imply a small decompression.

The initial combined model smoke process contains cumulative memory; do not quote its later MCI peak as isolated MCI memory. [Initial combined receipt](MODEL_SMOKE_COMBINED_INITIAL.json), [fresh isolated MCI receipt](MODEL_SMOKE_MCI.json). Timing here is the model call, not upload-to-result latency.

## E. Failure engineering and corrections

The final **234-test suite passed in 14.000 s**. JavaScript syntax checks passed for the external controller and terrain controller. [All 11 final HTTP checks](HTTP_READINESS_RECEIPT.json) passed: foreign origin, wrong offset, oversized chunk, atomic rollback, upload cancellation/restart, corrupt TIFF, incompatible execution refusal, no checkpoint loading on refusal, supported actual numerical output and absence of fabricated scores without labels.

Defects found and closed include incomplete-upload restart, cached controller behaviour, stale results after source changes, omitted analysis values in the browser, dimension/scale contract gaps, ambiguous class coercion, native-block decompression bounds, downloaded-ZIP verification, reference hash linkage and an insufficient default MCI memory ceiling. Targeted regressions exercise each substantive boundary.

The actual browser Stop terminated inspection worker `cd7da6ac9fe346df8bb4d3e4a1ccb066`, recorded `CANCELLED`, preserved completed originals and observed 56,946,688 bytes peak RSS: [worker receipt](BROWSER_WORKER_STOP.json). Subsequent operations completed. Upload abort/restart cleanup was also verified. Unit tests cover timeout then a successful next worker, restart-to-completion, immutable completed files, low-RAM refusal and upload/worker exclusion.

Retained failure examples include corrupt TIFF (`063fc5a4ef47421cbbf88e18b26be12c`), interrupted upload (`96d398552a0f408d8780d1fa46c04490`) and genuine BIFOLD missing-georeference refusal in the adapter receipt. Failure records are expected, inspectable outputs rather than fabricated successes.

Open limitations: actual judge data and labels absent; external Qwen/arbitrary Flood Lab bundles withheld; no new genuine external georeferenced MCI/BIFOLD case; no automatic preparation/tiling/batching; no physical co-registration or source-authenticity certification. No model training, threshold tuning against judge labels, flood-depth/damage/safe-route/forecasting assertion or public ingestion deployment was performed.

## F. Browser proof and regression scope

On final clean application source: select files → assign independent reference role → import/full inspect → select input → preflight → actual NDVI execution without scores → load frozen protocol/reference → evaluate unchanged prediction → inspect native previews → download ZIP → independently verify ZIP. Reload retained the matching dataset, protocol, reference and result. Changing datasets cleared the previous result. Stop/restart checks are documented above.

- [Desktop evaluation](images/evaluation-desktop.jpg): 1280 × 720 viewport, full-page capture; no document horizontal overflow.
- [Mobile evaluation](images/evaluation-mobile.jpg): 390 × 844 viewport; no document horizontal overflow.
- [Terrain regression](images/terrain-regression.jpg): real retained 90 m DSM colours, saved water context, in-place question/result and collapsed evidence. 601 candidate locations were mapped to valid DSM support; those are water candidates, not depth or confirmed damage.
- [Browser receipt and image hashes](BROWSER_REGRESSION_RECEIPT.json): no captured warning/error logs in the final navigation check. Temporary viewport override was reset and Datasets left open.

Original services on ports 8765/8767 were preserved; extension 8768 and Flood Lab 8770 returned HTTP 200 in the final audit. This is route availability and the described browser regression, not exhaustive manual certification of every legacy screen. The software suite covers broader existing behaviour.

## G. Git and disclosure record

| Actual commit | Authentic author timestamp | Meaningful work |
|---|---|---|
| `f3945347cf0f0a4581aa1480c8fa1501a25da4b4` | Preserved in Day 1 record | Frozen `day1-final`, already merged into main before Day 2. |
| `b7402d583a4ec164a074b76844261e7c541f6e3f` | 2026-10-31T10:37:33+05:30 | Preflight, restart, saved browser state and direct independent ZIP verification. Pushed to `jai-day2-20261031`. |
| `f6fa44f8e3fbf284deb9fbca2898847453e300a7` | 2026-10-31T10:56:21+05:30 | Memory, strict evaluation mappings/native blocks, recovery checks, HTTP checker and operator guide. Pushed to `jai-day2-20261031`. |

The closeout adds reviewed documentation, small receipts and actual screenshots only. The [publication receipt](PUBLICATION_RECEIPT.json) records the reviewed documentation commit, remote-ref snapshot and unchanged Day 1 annotated tag object/peeled commit. The receipt itself is a subsequent additive commit; `git log origin/main` identifies the final published head. No amend, force push, timestamp fabrication or historical benchmark overwrite was used.

The user reports organizer clearance for extending the existing applications under open innovation and selected the main `Yoriichi-GOD/SATquery-AI` repository. That is user-supplied clearance, not independent organizer correspondence. Existing application/models/data remain disclosed baseline material. Codex assisted implementation, diagnostics, test execution and documentation. Dependencies, model source/checkpoints and dataset provenance remain in exported manifests, the [asset guide](../../ASSETS.md) and original benchmark records; this work adds no newly trained checkpoint.

## H. Judges' independent verification

In the provisioned environment from [setup](../../SETUP.md), from the repository root:

```sh
# No model weights are needed to check a supplied evaluated export.
python scripts/verify_external.py '/path/to/downloaded/evidence.zip'

# Full software regressions (no claim of new benchmark accuracy).
python -m unittest discover -s tests

# Optional live local HTTP failure/functional checks; creates synthetic QA data.
python scripts/verify_external_http.py --base http://127.0.0.1:8768 --output /path/to/new-http-receipt.json
```

To execute genuine data, use the intake/evaluation commands and declared contract in the [operator guide](../README.md#independent-commands), provide the required external weights/data lawfully, freeze a new protocol for the exact dataset revision and use a new run directory. The dashboard's generated `reproduce.md` names actual dependencies, source/checkpoint hashes and run parameters. Recomputed metrics can be checked without trusting the displayed score, but rerunning a model still requires its assets. No externally supplied judge dataset can be claimed as accepted until that dataset has actually passed this process.

## Definition of Done review

| Requirement | Evidence / disposition |
|---|---|
| Establish baseline and preserve services | 221-test start; 234-test final pass; original PIDs retained and four HTTP services available. |
| Browser import→preflight→supported output→independent evaluation→download verification | Completed final-source software fixture replay; actual ZIP verified; reload/mobile/source-change checks completed. |
| Refuse incompatible inputs before inference | Complete contract reports, actual genuine missing-georeference refusal and HTTP/unit regressions. |
| Genuine adapter execution with honest scope | Genuine Dehradun/CDVQA executed; MCI/BIFOLD model-only publisher fixtures; no new accuracy invented. |
| Failure/resource/cancel/recovery | Large sparse fixture receipt, actual worker Stop, actual partial upload Stop/restart, cleanup, timeout and resource regressions. |
| Accessible handoff and preserved history | Operator guide, this report, receipts, screenshots, additive pushed commits; immutable Day 1 tag. |
| Real unfamiliar judge-data acceptance | **Pending external dataset/labels. Not claimed complete.** |

Close this readiness milestone here. When real data arrives, inspect it, measure the supported case, verify the exported result, then decide whether a specific new adapter or preparation step is justified.
