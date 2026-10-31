# External dataset intake and independent evaluation

This workflow inspects unfamiliar local datasets before offering a specialist. It preserves originals, reports every checked contract parameter and refuses unsupported analysis. It does not turn a 3 GB dataset into a model-ready crop, certify acquisition provenance or invent scores without reference labels.

## Start and inspect in the browser

Use the provisioned Linux/WSL Python environment described in [setup](../SETUP.md) and [asset dependencies](../ASSETS.md). On the configured host, start `start_jai.py` with `SATQUERY_BASELINE_ROOT`, `FLOODLAB_BASELINE_ROOT`, `FLOODLAB_PYTHON` and `JAI_PORT=8768` set as in [the extension guide](../../jai_extension/README.md). Open **http://127.0.0.1:8768/#datasets**.

1. Create a named dataset. Select TIFF files, a directory, or a supported ZIP. Assign label files the **reference** role; existing externally produced predictions use **prediction**. Companion metadata uses **metadata**. A reference is never substituted with a prediction.
2. Import and inspect. Transfers use chunks of at most 8 MiB. The private inventory shows original names, source hashes, raster properties, rejected files and native-pixel previews. No external path or download URL is accepted by the HTTP API.
3. Select the exact one or two input TIFFs for a case and run preflight. Expand each specialist to inspect all mismatches, missing values and suggested preparation steps. Download the same report as JSON or CSV. A diagnostic mismatch is a completed inspection, not a green analysis result.
4. Run an eligible specialist. Analysis stays separate from evaluation: without compatible labels, valid outputs are retained and the score status is `EVALUATION_NOT_POSSIBLE — COMPATIBLE_GROUND_TRUTH_NOT_PROVIDED`.
5. For evaluation, select an independently sourced reference and load an explicit protocol for the exact dataset revision. It must freeze task, population, split, prior exposure/exclusions, licence, reference provenance, class mapping, ignore rules and applicable thresholds/preprocessing. Reuse unchanged predictions in a new immutable evaluation run. Do not tune against judging labels.
6. Inspect native prediction/reference previews, class-specific metrics, evaluated/ignored counts and full source records. Download **evidence.zip** and verify it independently using the command below.

Stop aborts uploads or terminates the actual isolated worker. Incomplete temporary chunks are removed; completed originals remain. Re-importing the same incomplete file explicitly restarts its temporary bytes. It cannot overwrite a completed original. Selection, reference, protocol and matching recorded results survive reload; changing datasets clears the old visible answer.

## Independent commands

The command-line tools use the same inspector, contract registry, execution adapters and evaluators as the service. Operator-supplied paths are CLI-only; HTTP accepts opaque registered IDs.

```sh
# Register and fully inspect input files without the browser.
python scripts/external_intake.py --source /data/judges/inputs --root .runtime/external/datasets --name judge-evaluation

# Add labels with an explicit role. Use the dataset ID printed by the first command.
python scripts/external_intake.py --source /data/judges/reference.tif --root .runtime/external/datasets --name judge-evaluation --dataset DATASET_ID --role reference

# Execute the explicit request against the printed private dataset manifest.
python scripts/evaluate_external.py --dataset .runtime/external/datasets/DATASET_ID/dataset_manifest.json --request /data/frozen-request.json --output /data/results/new-run-id

# Verify a downloaded ZIP directly, or supply an extracted export directory.
python scripts/verify_external.py '/data/results/evidence.zip'

# Optional local HTTP correctness checks; creates clearly named synthetic fixtures.
python scripts/verify_external_http.py --base http://127.0.0.1:8768 --output /data/results/new-http-receipt.json
```

Replace the uppercase ID and paths with the actual import output. Choose a new run/receipt path each time. A prediction-only request has `specialist`, selected `inputs` IDs and explicit parameters such as `threshold`. An evaluated request additionally names `reference_id` and a complete `protocol`; imported predictions name `prediction_id`. The browser can evaluate its prior unchanged output using `prediction_job_id`. Do not reuse a prediction with different selected inputs.

For segmentation the protocol declares integer native-label mappings, `classes`, `ignore_values` and `prediction_semantics` (`water`, `road_building_change` or `ndvi_threshold` for those model outputs). A water/flood/vegetation label does not automatically have the same semantics as an NDVI threshold mask. Classification and multilabel use explicit case/class CSV tables. VQA uses case/answer tables and `exact` or `casefold_whitespace` normalization; arbitrary captions are not pixel-level ground truth.

The verifier reads the exported prediction and reference, checks artifact hashes and the recorded reference source hash, and recomputes metrics. It requires no model weights or dashboard. A consistent export does not prove independent source authenticity. Do not redistribute source/reference copies without the dataset's permission; model weights remain external.

## Compatibility and execution boundaries

| Specialist | Actual external contract / current evidence |
|---|---|
| Qwen2-VL | Optical RGB interpretation; external execution is withheld because the original shared service lacks a verifiable cancellation boundary. Original Workspace remains available. |
| NDVI | Labelled Red/NIR and declared surface-reflectance calibration, finite scale/offset and usable pixels. Genuine retained Dehradun scene executed; no classification accuracy inferred. |
| Spectral pair | Two dated Sentinel-2 surface-reflectance observations, required bands and genuine SCL, matching projected grids. Existing numerical checks retained; no new genuine two-date external benchmark claimed. |
| MCI | Corresponding 256×256 uint8 labelled RGB, equal grids/CRS and ordered dates; existing registration diagnostic still applies. Real model executed on its retained publisher crop. That crop lacks geographic metadata and is refused by the external geographic path. |
| WaterUNet | Matched 512×512 Sentinel-1 GRD VV/VH dB plus all 13 ordered Sentinel-2 L1C bands in reflectance×10000, matching grid and acquisitions within 14 days. Historical Ghana case executed/evaluated on Day 1; not new untouched acceptance evidence. |
| BIFOLD / SAR scene | Prepared 120×120, north-up projected 10 m grid; correct VV/VH and optical band order, declared sensors, units and dates where paired. Retained BIFOLD model-only publisher fixture executed; missing georeferencing is explicitly refused externally. |
| CDVQA | Equal-size prepared uint8 RGB (explicit band names or actual RGB colour interpretation), supported exact question and explicit alignment/order declaration. Genuine retained RGB pair executed without suitable reference answers; no accuracy reported. |
| Flood Lab | Existing prepared SAR event/OSM workflow is preserved. Arbitrary external TIFFs do not replace that event bundle; its external arbitrary-bundle adapter remains disabled. |
| Terrain | One georeferenced north-up metric elevation raster with known metre units and identity native scale/offset. No silent reprojection or vertical-unit conversion. Existing genuine GLO-90 context remains separate from flood depth or hazard inference. |

Matching headers establish compatibility, not sensor authenticity or physical co-registration. Numerical ranges are measured without guessing units. Unknown metadata stays unknown. The registry and per-file report are authoritative for the selected inputs.

## Resource and failure limits

- Default dataset cap: 4 GiB, including archive expansion, with at most 256 registered files. One analysis case selects at most two rasters; automatic large-scene tiling/batched inference is not implemented.
- TIFF inspection reads native windows of at most 256×256 pixels, one band at a time, with a 16 MiB maximum native decode block. Fully scanned rasters may be larger than a model can accept. Sampled inspection explicitly cannot enable inference.
- The existing small specialist limits remain: at most 1,048,576 pixels, 14 bands and 20 MiB per selected input in this external workflow, with tighter specialist dimensions as above. Originals are outside public static directories under `.runtime/external` by default.
- One isolated external operation runs at a time. Inspector ceiling: 512 MiB RSS. Analysis/evaluation default: 2 GiB; MCI defaults to 3 GiB because the measured cold model fixture exceeded 2 GiB. The service checks free RAM against the ceiling plus 256 MiB before launch and monitors actual RSS. `SATQUERY_DATA_WORKER_RSS_MIB` can explicitly set a 128–8192 MiB analysis ceiling; reducing it may produce a retained memory-limit failure.
- ZIP paths/links, excessive expansion, unsupported/corrupt files, partial uploads, missing assets, unmatched grids, unknown classes, no valid pixels, timeouts and cancellations have explicit failure records. The independent verifier also bounds native raster blocks and ZIP extraction.

The Day 1 synthetic **3 GiB** upload measured 83.93 s upload, 30.90 s full inspection wall time and 105,369,600 bytes observed inspector peak RSS. It was a resource fixture, not unfamiliar real satellite data. See the immutable [Day 1 receipt](../jai/day1-final/LARGE_DATA_RECEIPT.json). No real judge dataset has been supplied for this checkpoint.

## Evidence and current closure

The [Day 2 closure record](day2/CLOSURE.md) links source revisions, software/HTTP checks, real adapter and refusal receipts, browser proof and known limitations. Historical benchmark reports and the immutable `day1-final` tag are preserved. No retraining, source acquisition, new scientific accuracy claim, public ingestion service or deployment was introduced.
