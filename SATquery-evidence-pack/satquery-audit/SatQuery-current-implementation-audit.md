# SatQuery: current implementation audit

Audit date: 19 September 2026. Scope: the source at `C:\Users\nrgen\.codex\scratch\SATquery AI`, its preserved evaluation artifacts, and read-only inspection of its existing WSL runtime. This is an operational inventory for subsequent external comparison. It makes no claim of savings, superiority, procurement readiness, or commercial clearance.

## How to read this report

**IMPLEMENTED** means an executable, reachable code path exists; it does not mean scientifically validated. **PARTIALLY IMPLEMENTED** means only the specified subset exists. **NOT IMPLEMENTED** means no implementation was found in the audited active paths. **UNVERIFIED** means the available evidence cannot establish the claim. These labels describe different dimensions and can coexist.

References **S1–S22** and **E1–E9** resolve to exact local files in the evidence index at the end. Functions and endpoints are identified alongside the findings. All 154 requested questions are numbered below; shared matrices avoid repeating the same six pipelines throughout.

Verification performed in this audit: source tracing; inspection of saved results and tests; read-only HTTP status checks; hashes of selected installed checkpoints; ZIP integrity checks on eight preserved runs; independent recomputation of water counts, temporal classes/counts, and one NDVI threshold count from archived arrays. **No new inference, training, test suite, installation, upload, server restart, or application modification was performed.** Saved benchmarks are historical measurements, not fresh benchmarks. The running processes point to the correct checkout, but their loaded Python modules are not cryptographically attested against the files inspected.

Companion files: `recorded-measurements.csv` contains 1,508 extracted numerical timing/memory fields, including nested per-case, historical, duplicate, and superseded records. `runtime-verification.json` records this audit's read-only runtime checks. `source-evidence-inventory.json` hashes 587 selected source/evidence files; it is an audit inventory, not a complete deployable repository snapshot.

## Findings that change the interpretation of earlier reports

- The active paired temporal path is **MCI/Change-Agent**, called by `paired_lab/server.py:work`, not the older ChangeFormer implementation still present in `engine.py`.
- The paired interface now bridges **single-image VQA and NDVI**, as well as temporal and optical–SAR analysis. Grounding remains a separate manual lab.
- Temporal uploads receive a **pixel-content registration diagnostic** in addition to metadata checks. It detects some misalignment; it does not certify physical registration. Optical–SAR pairs do not receive an equivalent cross-modal content check.
- NDVI's current arithmetic and exported raster use **float64**. The old float32/float64 threshold inconsistency is not an accurate description of the inspected current path.
- Water segmentation reports **predicted water pixels and percentages**, not water area. MCI reports predicted changed pixels and coverage, not construction/demolition area or object counts.
- Baseline VQA currently preserves open model answers. Old claims that all unsupported descriptive answers are suppressed do not describe `present_open_answer`.
- Models and sample runs are installed locally, but the source folder alone is **not a reproducible full deployment**. Several required assets and dependency directories live outside it.

## A. What can SatQuery actually do today?

### 1. Current capability matrix

| Workflow / status | Required input; supported task | Active specialist | Automatic steps | Manual user work | Output and evidence | Principal limitation |
|---|---|---|---|---|---|---|
| Single-image VQA — IMPLEMENTED | One accepted image; visual question, scene description, presence, rural/urban, visual count | AdaptLLM remote-sensing Qwen2-VL-2B; optional local LoRA for bounded pilot modes | Decode/preview, lexical routing, model prompt/generation, answer formatting; extra count-description call where applicable | Select suitable image/query; main screen optionally select pilot mode; verify answer | Answer, raw answer, routing/model trace, timing, hash; separate count interpretation | Open VQA can hallucinate; generalization unverified; current service uses CUDA |
| NDVI — IMPLEMENTED within strict contract | Labeled RGB plus red/NIR GeoTIFF tagged surface reflectance; optional SCL; supported NDVI/vegetation query | Rasterio/NumPy; no model required | Read scale/offset, mask invalid/SCL pixels, calculate float64 NDVI, threshold/count, eligible projected area, render/export stages | Obtain/correct/tag data; choose scientifically suitable threshold; inspect exclusions | Statistics, denominators, quality warnings, PNG stages, float64 NDVI TIFF, JSON | Not a general spectral toolbox; trusts calibration metadata; no atmospheric correction |
| Temporal road/building change — IMPLEMENTED, narrow model domain | Two aligned, dated, 256×256 RGB uint8 optical GeoTIFFs, or bundled benchmark sample | MCI: SegFormer encoder + attentive encoder + caption decoder | Validate metadata and registration diagnostic, normalize, predict classes/caption, count pixels, render/package | Prepare aligned RGB crops, order dates, choose query, review masks and caption separately | Before/after, 3-class mask, overlay, scores/classes NPZ, caption, counts, JSON, original inputs, ZIP | No measured direction, physical area, object count, or arbitrary temporal reasoning |
| Optical–SAR water — IMPLEMENTED, narrow model domain | 512×512 Sentinel-1 VV/VH dB + all 13 Sentinel-2 L1C bands in required order, aligned | Local WaterUNet, same checkpoint run with SAR/optical/joint availability | Validate pair, normalize/zero invalid data, run three modes, threshold .5, count, render/package | Source/calibrate/register data and attach required metadata; interpret water vs flood | Three masks/counts, joint overlay, probabilities/validity NPZ, georeferenced joint TIFF, JSON, originals, ZIP | Predicts water, not flood extent relative to baseline; no cloud/speckle correction, no area |
| Optical–SAR land cover — IMPLEMENTED, patch classification only | 120×120 aligned 10 m Sentinel-1 VV/VH + 10 selected Sentinel-2 bands; required tags/units | Three BIFOLD BigEarthNet-v2 ResNet50 models: SAR, optical, joint | Validate, order/normalize channels, sigmoid scores, .5 labels, compare all three | Prepare correct patch; choose question; review scores and domain fit | 19-class scores for three models, labels, previews, JSON, originals, ZIP | Scene/patch labels, not segmentation/localization/area; thresholds not accuracy |
| Grounding — IMPLEMENTED in separate experimental lab | RGB image, one of six categories, optional threshold and boxes/both mode | Grounding DINO tiny; SAM base for masks | Detect, filter/NMS, optionally segment boxes, render/archive | Open separate lab; select category; tune/review proposals if needed | Boxes/scores, optional masks, objects/union pixel coverage, stage timing, PNG/NPZ/JSON/ZIP | No main-router grounding; no unrestricted query; model proposals not verified objects |

Evidence: S1–S15, S17. This matrix describes code-supported operations; scientific validity on arbitrary user data is UNVERIFIED.

### 2. Executable capabilities rather than README claims

**IMPLEMENTED:** the six workflows above through port 8765 (VQA/NDVI and `/grounding/`) and port 8767 (paired controller plus single-image bridge). Existing installed models and preserved successful runs support executability in this particular environment. Fresh-clone operation is PARTIALLY IMPLEMENTED; fresh inference this turn is UNVERIFIED. S1, S5, S13, S14; E1, E2.

### 3. Experiments and non-main capabilities

**IMPLEMENTED as experiments, not current automatic user capabilities:** old ChangeFormer temporal inference/evaluation; candidate-model trials and ablations; WaterUNet training; LoRA development/training and evaluation; grounding regional/tiling experiments. Grounding has a usable lab but remains outside the main/paired natural-language router. A coordinate conversion helper in `geo.coordinate` does not establish a user-facing coordinate-question workflow. No general index library, object-grounded natural-language controller, automatic mosaicking, or arbitrary multi-tool agent was found. S2, S6, S14–S16, S19; E3–E8.

### 4. External dependencies and missing assets

**IMPLEMENTED with external assets:** VQA needs the pinned Hugging Face base snapshot; pilot modes need `/root/satquery/experiments/lora-pilot-v1/adapter`; MCI needs its checkpoint and manifest under `/root/satquery/paired-lab/mci-model`; fusion needs three cached BIFOLD snapshots, `models.json`, ConfigILM source/constants and the external `deps` directory; grounding needs its model manifest and cached DINO/SAM weights. Water's checkpoint is inside `paired_lab/checkpoints`, but Python/runtime dependencies remain external. Training/evaluation additionally depend on source datasets/archives and splits. Installed assets were inspected; a source clone does not contain them all. S1, S6, S9, S10, S15, S18; E1.

### 5. Local, offline, CPU and GPU requirements

| Workflow | Current served device | Network during ordinary inference | CPU-only execution |
|---|---|---|---|
| VQA / pilot | CUDA GPU | Local cached model; no external inference API | NOT IMPLEMENTED in served path |
| NDVI | CPU | None required by analytical code | IMPLEMENTED |
| MCI temporal | CPU | Local weights | IMPLEMENTED; historical CPU results present |
| Water | CPU | Local weights | IMPLEMENTED; GPU available in training/experiments, not served path |
| Land cover | CPU | Local weights, `pretrained=False` | IMPLEMENTED |
| Grounding | CUDA GPU; detector and SAM sequential | Cached/local models | NOT IMPLEMENTED in lab worker |

Offline-capable code paths are IMPLEMENTED given complete caches/dependencies. A controlled air-gap test and all dependency telemetry behavior are UNVERIFIED. The paired process imports external model metadata/constants at startup even when only a single-image bridge is wanted. S1, S6, S9, S10, S13–S15.

## B. Complete user workflow

### 6. End-to-end traces, including preprocessing

**IMPLEMENTED — single-image VQA.** User selects file → `server.upload` enforces byte/type/dimension constraints → ordinary image: EXIF transpose/RGB PNG; GeoTIFF: `geo.ingest`, preserve raster plus stretched RGB preview → image UUID/raw-file hash returned → user submits question and optional mode → `server.analyze` checks input/question/mode, calls `routing.route`, handles refusals and pilot restrictions → reserve busy slot → `run_job` loads cached pinned base/optional adapter → processor resizes/tokenizes image and query → greedy generation → presentation function, and extra scene-description inference for count workflows → result/trace JSON saved and UI polls/display. Baseball count uses original and mirrored views with agreement/abstention before a separate interpretation. Single-image use from port 8767 first uploads via the bridge, then reuploads for execution, polls port 8765, copies evidence and packages original input. S1–S4, S12, S13, S17.

**IMPLEMENTED — NDVI.** Upload GeoTIFF → inspect labels, calibration tag, dimensions and metadata; create preview → submit supported query/threshold → router rejects unsupported combinations or inconsistent requested threshold → `run_ndvi` → `geo.analyse` reads masked red/NIR as float64, applies band scales/offsets, excludes invalid/nonfinite/negative/near-zero denominator pixels and optionally SCL outside 4/5/6/7 → calculate `(NIR−red)/(NIR+red)` → classify `>= threshold` → count valid/selected/excluded pixels and projected-metre area if eligible → save georeferenced float64 NDVI raster and overlay → `stages.create_stages` renders RGB, false colour, evidence and mask from the computed raster → format answer, save JSON, display/download. No VLM inference is called on this path. S1–S3.

**IMPLEMENTED — temporal.** User selects two prepared TIFFs or sample → paired `upload`/`inspect` stores arrays and metadata/hash → user supplies query, modality and dates if absent → `controller.plan` selects temporal → `validate(... enforce_content=True)` checks contract/date order/grid and runs `registration.diagnose` → `work` calls **`mci.temporal`** → normalize uint8 RGB using fixed training means/stds → cached CPU MCI encoder/attention → segmentation softmax scores and separate greedy caption decoding → argmax classes → road/building counts and total changed coverage (unchanged count is derivable) → write images/NPZ → server may prepend direction caveat based on query → attach checks/query/UTC/UUID → copy originals and ZIP → UI displays four images, measurements, caption/limitations. No image warp occurs. The user query routes the task; it is not passed into MCI caption inference. S5, S7, S8, S10, S11, S17.

**IMPLEMENTED — water.** User prepares/uploads optical and SAR TIFFs → `inspect` records sensor/bands/units/dates/CRS/affine and arrays → `plan` recognizes water-compatible 13-band optical pair/query → `validate` enforces water contract and finite overlap → `flood.prepare` normalizes two SAR and thirteen optical channels, establishes common finite mask, fills invalid values → availability flags and absent-modality channel zeroing → load CPU WaterUNet → three forward passes → softmax water probability, fixed .5 threshold and valid-mask intersection → counts/percentages, three PNG masks, joint overlay, scores+valid NPZ and georeferenced joint TIFF → checks/hash/trace/inputs/ZIP → UI joint views plus all three counts. S5, S7–S9, S17.

**IMPLEMENTED — land cover.** Upload prepared 10-band optical + 2-band SAR TIFFs → inspect/plan/validate patch contract, grid/dates/sensors/units/band set → build dictionary by band name → fixed band order and ConfigILM training normalization → three cached CPU ResNet50 forwards → sigmoid 19 labels per model → fixed .5 selection; optional query-specific water/built-up/forest wording → previews, all scores, trace, originals and ZIP → UI displays scores for all three modes. The internal nearest resize is not general upload preparation: upload validation already requires 120×120. S5–S8, S17.

**IMPLEMENTED — grounding lab.** Open separate `/grounding/` → upload RGB image and normalize EXIF/RGB → manually choose category, threshold, mode → validate selection and reserve shared GPU → persist job/request → clear main VQA cache → isolated worker checks CUDA/free memory, loads DINO → detect with category prompt → clip/filter boxes, NMS, cap proposals → release detector → optionally load SAM, segment accepted boxes in batches, select highest predicted-IoU mask per box → write overlays/instances/NPZ/result → archive allowlisted files → mark finished and release GPU → UI shows stages/objects/views. It does not call the main router. S1, S14, S15, S17.

### 7. Automatic versus human steps at every stage

**IMPLEMENTED automation:** everything after submission in the six traces except a refusal requiring new input or parameters. **Manual prerequisites:** sourcing/access rights, preprocessing required by each contract, choosing study area/dates/task, upload and final scientific review. No workflow automatically acquires a suitable real-world satellite scene, resolves missing calibration, or asks an expert to approve intermediate model outputs. S1–S15.

### 8. Knowledge required beforehand

**PARTIALLY IMPLEMENTED novice access:** VQA needs a suitable image and meaningful visual question; NDVI needs correctly identified calibrated bands and a meaningful threshold; temporal needs chronological, physically aligned RGB crops; water needs exact Sentinel sensor/product/bands/units and overlap; land cover needs the correct 10-band/2-band 10 m patch; grounding needs an applicable category and awareness of proposal thresholds. Metadata contracts reduce ambiguity after upload, but do not create those inputs. S2, S7, S9–S11, S14.

### 9. Remaining GIS/remote-sensing expertise

**NOT IMPLEMENTED as automatic judgment:** selecting sensor/resolution appropriate to the object; calibration/product-level interpretation; registration quality beyond the diagnostic; cloud/shadow/speckle/domain-shift assessment; temporal comparability; threshold suitability; validation against reference data. VQA/grounding hide more input mechanics but do not remove these scientific obligations. S2, S7, S9–S11, S15.

### 10. Required preprocessing before upload

**Manual:** obtain data; prepare correct crops/grids/channel lists; calibrate SAR to expected dB; supply optical units/product level; co-register all paired inputs; produce 256×256 RGB uint8 for MCI, 512×512 13+2 for water, 120×120 10+2 at 10 m for land cover. NDVI requires actual surface reflectance plus usable band labels/scales/offsets; supplied SCL is optional. None of these prerequisites is established by renaming a file or adding a tag. S2, S7, S9, S10.

### 11. Preprocessing SatQuery performs

**IMPLEMENTED:** decoding, EXIF correction/RGB conversion, preview stretches; NDVI mask/scale/offset/formula/SCL filtering; temporal fixed model normalization; water fixed channel normalization/clipping/invalid fill and modality flags; fusion channel ordering/training normalization; model image processors; grounding box filtering/NMS and SAM preprocessing. **NOT IMPLEMENTED:** raw-scene scientific calibration, atmospheric/terrain correction or pair alignment. S1–S3, S6, S9–S11, S15.

### 12. Manual and automatic parameters

**IMPLEMENTED:** main VQA exposes mode; paired single route chooses rural pilot automatically where recognized. NDVI exposes threshold (default .5). Paired upload exposes modality/date; API also units, while UI relies on embedded units. Grounding exposes category, score threshold (.3 default, .15–.8 allowed) and boxes/both. Model revisions, normalization, water/fusion .5 thresholds, MCI argmax/caption decoding, token limits, registration thresholds and grounding postfilters are automatically fixed in code. Fixed does not establish scientifically safe for every input. S1, S4–S15, S17.

### 13. Specialist routing

**IMPLEMENTED as deterministic rules:** main `routing.route` recognizes rural/urban, presence, NDVI grammar, count and general visual questions and blocks selected unsupported requests. Paired `controller.plan` considers input count/modality/bands/query, delegates single-image routing, and selects temporal, water or land-cover specialization. It includes road-to-building text normalization for the older paired rule helper. Grounding is manual. This is not an LLM planner or learned optimal-model selector. S4, S7, S8.

### 14. Natural language without knowing the specialist

**IMPLEMENTED within accepted grammar:** VQA/NDVI in both single-image entry points; temporal/water/land-cover selection from appropriate paired inputs. **PARTIALLY IMPLEMENTED overall:** user must choose the appropriate upload type and prepare specialist-compatible data. **NOT IMPLEMENTED for grounding:** category/mode selection in separate lab. Main port 8765 alone refuses paired requests. MCI produces its standard caption regardless of the precise routed question. S1, S4, S5, S8, S10, S14.

### 15. Manual actions after a result

**NOT AUTOMATED:** check source/domain/registration validity; compare predictions with imagery/reference data; assess cloud/shadow/NoData exclusions; distinguish water from inundation and changed pixels from construction/removal; review all modality outputs where relevant; validate counts/captions/detections; choose whether result is suitable for the intended decision; export/archive. Deterministic arithmetic can be recomputed from evidence, but does not validate the upstream model or source data. S2, S9, S10, S15; E1.

## C. Input preparation burden

### 16. Input assumptions by workflow

**IMPLEMENTED contracts, with physical truth partly UNVERIFIED:**

| Dimension | VQA / grounding | NDVI | MCI temporal | Water | Land cover |
|---|---|---|---|---|---|
| Grid/dimensions | Main ordinary images ≤25M pixels; grounding 64 minimum side/≤6M; image processors resize | GTiff ≤4,194,304 pixels, ≤16 bands | Exactly 256×256×3 uint8 | Exactly 512×512 optical13/SAR2 | Exactly 120×120 optical10/SAR2 |
| CRS/affine | Not required for visual reasoning | Read/preserved; projected metre CRS needed for area | Matching CRS/affine for user pairs; nonsingular/no shear rules | Matching CRS/affine; no explicit 10 m check | Matching projected metre CRS/affine and 10 m for uploads |
| Bands/order | RGB preview; no physical sensor verification | Recognized red/NIR; ingest also requires RGB labels; optional SCL | RGB descriptions for uploads | Strict 13 Sentinel-2 order plus VV/VH | Correct 10-band set plus VV/VH, reordered by name |
| Units/calibration | Display values only | Tag `reflectance_units=surface_reflectance`, band scale/offset | uint8 display-domain RGB, fixed learned normalization | Sentinel-1 GRD dB; Sentinel-2 L1C /3000 normalization | SAR dB; optical reflectance_x10000 |
| Dates | Not needed | Metadata recorded if supplied | Parsed dates, before<after | Parsed dates within 14 days | Parsed dates within 14 days for uploads |
| NoData | Ordinary visual content not scientifically masked | Masked/nonfinite/negative/denominator exclusions, optional SCL | Invalid data rejected | Common finite pixels retained; invalid channels filled zero | Invalid data rejected |
| Correction/registration | User responsibility | Surface correction trusted | User aligns; diagnostic only | User calibrates/registers; no content registration check | User calibrates/registers; no content registration check |
| Cloud/speckle | No scientific correction | Supplied SCL classes only | No cloud correction | No cloud/speckle filtering | No cloud/speckle filtering |

Bundled benchmark samples intentionally bypass parts of the user-upload CRS/date/grid checks in `_legacy_validate`; this distinction must accompany demo claims. S1, S2, S7, S11, S14.

### 17. Programmatically verified assumptions

**IMPLEMENTED:** byte/type/size limits; band number/names/order or set; declared modality/sensor/units; array shape/dtype; CRS and affine comparisons; finite/nonsingular/no-rotation checks as coded; dates/date separation; invalid/finite masks; temporal feature registration diagnostic. NDVI verifies presence of required labels/calibration tag and usable pixels, not the calibration procedure. S1, S2, S7, S11, S14.

### 18. Metadata trusted without physical verification

**UNVERIFIED physical claims:** sensor identity, acquisition time, calibration/reflectance units, band semantics, CRS/geolocation correctness, and source attribution. `inspect` can compare a supplied date against a tag; supplied units override the tag without an equivalent conflict test. Matching fields do not authenticate the physical data. S2, S7.

### 19. Refuse, warn, correct, or continue

**IMPLEMENTED refusals:** invalid files/contracts, unsupported query combinations, missing calibrated NDVI, zero valid NDVI pixels, bad dates/grids, detected temporal misalignment, insufficient registration evidence on untrusted temporal uploads. **Warnings/continuation:** missing SCL or unsupported area CRS, model limitations, unverified registration of trusted benchmark samples, NDVI stage-render failure. **Automatic transformations:** EXIF/RGB, scale/offset, masking, normalization, box postprocessing. **Silent scientific continuation risk:** plausible but wrong metadata, cloud-contaminated water/land-cover data, physically shifted optical–SAR pixels with matching metadata. S1–S3, S7, S11, S15.

### 20. Metadata equality versus physical registration

**PARTIALLY IMPLEMENTED:** temporal `registration.diagnose` uses grayscale SIFT matches, ratio .7, RANSAC similarity transform and a 1.5-pixel maximum-corner displacement threshold; low support is unverified. Identical arrays are recognized directly. This is stronger than metadata equality but is neither independent geolocation verification nor a general registration certificate. **NOT IMPLEMENTED:** equivalent cross-modal optical–SAR content registration. S7, S11.

### 21. Optical–SAR pre-upload work

**Manual:** obtain compatible sensor products; calibrate/convert SAR as needed to dB; select optical product/units/channels appropriate to water or land cover; co-register/reproject/resample/crop outside SatQuery; supply required dates, CRS, transforms, sensor tags and band descriptions. Resolve cloud/speckle/scene mismatch where scientifically necessary. SatQuery checks the resulting contract. S7, S9, S6.

### 22. Temporal pre-upload work

**Manual:** pick comparable dates and resolution/domain; register images; create matching 256×256 RGB uint8 GeoTIFF crops with required descriptions/metadata and chronological order. The content check may reject an otherwise metadata-compatible upload, but does not repair it. S7, S10, S11.

### 23. Specific preprocessing yes/no

| Operation | Finding / status | Evidence |
|---|---|---|
| Reproject analytical raster | NOT IMPLEMENTED; coordinate/bounds conversion is not raster reprojection | S2, S7 |
| Resample pair onto common geospatial grid | NOT IMPLEMENTED; dimensions must already match | S7 |
| Resize for model/display | IMPLEMENTED in image processors and fusion helper; not registration | S1, S6, S15 |
| Align/warp pair | NOT IMPLEMENTED; temporal diagnostic only | S11 |
| Radiometric calibration | PARTIAL: apply supplied NDVI scale/offset; no raw-sensor calibration | S2, S9 |
| Terrain correction | NOT IMPLEMENTED | S7, S9 |
| Atmospheric correction | NOT IMPLEMENTED; NDVI surface-reflectance tag trusted | S2 |
| Cloud masking | PARTIAL: optional supplied SCL filtering for NDVI only | S2 |
| Speckle filtering | NOT IMPLEMENTED | S9, S6 |

## D. User decisions eliminated

### 24. Automatic analytical decisions

**IMPLEMENTED:** supported task routing; single-image pilot choice in paired controller; declared band mapping; NDVI formula/invalid-pixel/SCL policy; threshold comparison; whether projected area can be computed; metadata-contract refusal; temporal registration acceptance/refusal; fixed model normalizations; MCI class argmax/caption decoding; three-mode water/land-cover execution; .5 water/class-label thresholds; count answer parsing and baseball agreement; grounding proposal suppression/NMS/mask choice; output packaging. These are SatQuery's decisions, not claims about competitors. S1–S15.

### 25. Decisions still left to users

**Manual / NOT IMPLEMENTED as automation:** task/study design; sensor/data access; acquisition dates; preprocessing/registration; domain suitability; file and upload mode; metadata correction; NDVI threshold; main pilot mode; grounding category/mode/threshold; interpreting uncertain or conflicting results; external validation and responsible use. S1, S7, S14, S17.

### 26. Defaults versus specialist choices

**IMPLEMENTED defaults:** NDVI .5, water .5, land-cover .5, grounding .3/both, fixed MCI preprocessing, main baseline VQA. **UNVERIFIED universal safety:** these defaults are not validated across all sensors/geographies/seasons/tasks. NDVI semantics, grounding threshold changes, input calibration and modality/date choices still require domain judgment. No evidence supports calling every default scientifically safe. S1–S15.

### 27. Prevention of wrong analyses

**IMPLEMENTED examples:** NDVI request on uncalibrated RGB refuses; main paired/SAR request refuses; temporal date reversal and content shift reject; water demands water-domain query and 13+2 contract; two SAR temporal inputs refuse; pair mismatches reject. **PARTIALLY IMPLEMENTED:** main unknown visual questions can fall through to VQA, and user-declared/encoded data can misrepresent sensor content. S4, S7, S8; E6.

### 28. Unsupported requests refused

**IMPLEMENTED:** see Q86 for the consolidated refusal inventory. Examples include unsupported quantitative/spatial/diagnostic main queries, wrong pilot question form, incompatible paired modalities, water counts/hectares or unsupported classes, unknown grounding category and invalid thresholds. Routing is lexical, so do not interpret this as complete semantic refusal coverage. S1, S4, S7, S8, S14.

### 29. Tested invalid-analysis cases

**IMPLEMENTED tests / historical execution evidence:** routing and dispatch refusals, count-format/abstention, NDVI precision/masking/stage agreement, paired dimensions/bands/units/grid/dates, temporal content shift and shear/cross-sensor checks, water input contracts, and grounding upload/selection/busy checks. `input-controller-tests.json` records 26 passing cases. Existing test source is not proof that the current full suite passes; no tests were executed in this audit. S20; E6, E8.

## E. Evidence and debugging

### 30. Inspectable intermediate artifacts

**IMPLEMENTED:**

| Workflow | Exposed evidence | Not exposed as a complete user artifact |
|---|---|---|
| VQA | Raw/final answer, input preview/hash, route, model/revision/adapter trace, generation settings/timing; count consistency and separate interpretation where used | Attention maps, calibrated uncertainty, token probability sequence, proof of object count |
| NDVI | RGB/false-colour/evidence/mask/overlay PNGs; float64 NDVI TIFF; formula/threshold, scale/offset metadata, exclusions/denominators/stats/eligible area in JSON | Full environment/code snapshot; raw red/NIR arrays absent from main's ordinary export set |
| Temporal | Before/after, class-coloured mask/overlay, classes and scores NPZ, raw caption, counts/coverage, checks/model trace, originals in paired ZIP | Internal feature tensors, caption probabilities, physical gain/loss ground truth |
| Water | SAR/optical previews, three masks/counts, joint overlay/TIFF, three probability maps and valid mask NPZ, normalization/checkpoint/input checks, originals | Calibration history, verified alignment, reference labels, area calculation |
| Land cover | Optical/SAR previews; 19 scores ×3 models, selected labels, threshold, normalization/model trace, originals | Pixel masks, spatial attribution, calibrated accuracy |
| Grounding | Source/boxes/outlines/masks/instances images as applicable, proposals/kept boxes/model scores/mask quality, masks NPZ, stage trace | Original unconverted upload in bundle; full job/request/log provenance inside bundle |

S1–S3, S5, S6, S9, S10, S12–S15, S17.

### 31. Visual processing stages

**IMPLEMENTED:** main NDVI four-stage view; paired NDVI/temporal/water/land-cover result views; grounding stage controls and overlays. **PARTIALLY IMPLEMENTED:** these mostly show selected input/output stages, not every transformation or live tensor computation. VQA shows image/result/trace, not spatial model reasoning. S17; S3, S15.

### 32. Numerical intermediate values

**IMPLEMENTED:** NDVI formula/threshold/scales/stats/exclusions; temporal softmax scores/classes/counts; water scores/validity/counts; land-cover scores; grounding box scores/mask quality/coverage; VQA timings/token counts/count consistency. **NOT IMPLEMENTED:** a unified calibrated-confidence field or complete per-layer model internals. S1, S2, S6, S9, S10, S12, S15.

### 33. Masks, metadata, identity and other evidence

**IMPLEMENTED, unevenly:** the Q30 matrix is the artifact inventory. NDVI has deterministic pixel measures and conditional area; MCI/water have model-derived masks/counts without area; land cover only patch scores; grounding pixel-space masks/boxes; VQA textual interpretation. Paired results attach input checks/hashes and model trace. Sensor/calibration tags describe declared input, not independently verified origin. S2, S5–S10, S15.

### 34. Download formats

**IMPLEMENTED:** main run JSON, NDVI `.tif` and accessible `.png` artifact endpoints; paired `.zip`, `.json`, `.png`, `.npz`, NDVI/water `.tif`, originals inside ZIP (`.tif` or `.original`); grounding `.zip`, `.json`, `.png`, `.npz`. No implemented Shapefile, GeoPackage, GeoJSON polygons or PDF analytical report export was found in these paths. S1:analytical_artifact; S5:artifact; S14:ARTIFACTS; S17.

### 35. Reconstructing a completed analysis

**PARTIALLY IMPLEMENTED:** paired ZIPs retain original inputs, checks/query, predictions and result, enough to recompute many post-prediction counts. NDVI original + recorded parameters can support independent arithmetic; main JSON/TIFF alone may not contain original band data. Grounding normalized source + arrays supports reviewing masks but not recovering original upload bytes. Exact historical inference additionally needs matching application/dependency/model/preprocessing versions; the packages are not self-contained environment snapshots. S1–S3, S5, S14; E1.

### 36. Run identity and provenance fields

**IMPLEMENTED:** main UUID, time, image identity/raw SHA-256, question, mode/routing, model/revision, trace, output/timing; paired UUID, UTC created_at, query/controller, input checks including original hashes/metadata, specialist trace; water checkpoint SHA-256/epoch; MCI manifest identity; fusion repo/revision; grounding job UUID/start/image raw hash/selection on disk and result model/stage trace. **PARTIALLY IMPLEMENTED:** grounding bundle omits job/request metadata; exact checkpoint hashing is not uniform; full OS/library/hardware/code hashes are not recorded on every user run. S1, S5, S6, S9, S10, S14, S15.

### 37. How far backward can an analyst inspect?

**IMPLEMENTED within saved stages:** VQA raw vs final text and original/mirror count estimates; NDVI source metadata → scale/exclusion policy → exported values → threshold mask/count; temporal source pair → registration checks → softmax scores/classes → counts and independent caption; water input contract/normalization → mode probabilities → masks → counts; land cover input checks → per-model class scores → selected text; grounding source → proposals/postfilters → selected boxes → SAM masks → union/count display. **UNVERIFIED root cause:** none guarantees that an analyst can diagnose learned representation errors or physically wrong source metadata from these artifacts alone. S1–S15.

### 38. Raw model output versus presentation

**IMPLEMENTED:** VQA raw answer and formatted answer; MCI raw caption plus softmax class-score arrays and presentation; water softmax scores plus thresholded masks; land-cover sigmoid scores plus labels/query wording; grounding detector proposals/kept boxes and SAM quality/masks. “Raw” here means exposed model-level predictions, not every internal tensor; softmax/sigmoid outputs are already transformations. NDVI has no model output. S1, S6, S9, S10, S12, S15.

### 39. Transformations before display

**IMPLEMENTED:** pilot answer bounding/open answer formatting/count parsing; separate count description; NDVI scaling/masking/formula/threshold/statistics; MCI argmax, class colouring/counts and optional direction caveat; water probability threshold/validity intersection; land-cover sigmoid/.5 label selection/query summary; grounding clipping, enclosing/frame proposal removal, NMS, cap, SAM mask selection/union/overlap rendering. S1–S3, S5, S6, S9, S10, S12, S15.

### 40. Useful evidence despite wrong interpretation

**IMPLEMENTED examples:** a wrong MCI caption does not erase the independently produced segmentation arrays/counts; a wrong VQA scene description is displayed separately from the count; land-cover summary text does not remove all 57 scores; water's three mode masks remain downloadable even if the joint interpretation is poor; NDVI output values remain available if a human interprets the threshold as an unjustified vegetation-health conclusion. These are inspectable outputs, not proof the intermediates themselves are correct. S2, S5, S6, S9, S10, S12.

### 41. Evidence gaps relative to NDVI

**PARTIALLY IMPLEMENTED:** VQA lacks directly recomputable semantic truth; land cover lacks pixel evidence; water/MCI lack NDVI-style deterministic physical measurement provenance and calibrated uncertainty; grounding lacks robust original-source/run provenance in its bundle. Conversely, paired ZIPs preserve originals more completely than main NDVI's standard downloads. Evidence is not a single ranking: NDVI arithmetic is particularly inspectable, while its input authenticity remains unverified. S1–S3, S5, S6, S9, S10, S14.

### 42. Common evidence schema

**PARTIALLY IMPLEMENTED:** paired server adds a common envelope (`id`, `query`, `input_checks`, `controller`, `created_at`) and ZIP mechanism. Specialist payloads/artifact names differ; main and grounding have separate job/result formats. No versioned common evidence schema and migration contract across all specialists was found. S1, S5, S13–S15.

## F. Human review burden

### 43. Expert judgment still required

**NOT AUTOMATED:** VQA factual grounding/count correctness; NDVI calibration, threshold meaning and quality exclusions; temporal real change versus acquisition/registration effects and caption direction; water cloud/domain/registration effects and flood versus permanent water; land-cover patch suitability and class interpretation; grounding missed/false objects and mask boundaries. Operational acceptance against reference truth is outside all six pipelines. S2, S7, S9–S12, S15.

### 44. Evidence beside the result

**IMPLEMENTED:** input preview and trace for VQA; NDVI stage views/stats; temporal before/after/mask/overlay/counts/caption; water optical/SAR/joint mask/overlay and all-mode counts; land-cover previews and three-model score table; grounding boxes/masks/object scores and stage views. Some provenance is collapsed or requires JSON/ZIP. S17.

### 45. Checks requiring another program or original imagery

**PARTIALLY IMPLEMENTED in-app review:** exact per-pixel NPZ/probability inspection, geospatial overlay against independent reference layers, calibration/source metadata verification, optical–SAR physical alignment, independent ground truth comparison, and full numerical recomputation generally require external GIS/array tools or the original source product. The app offers images/stats, not a complete GIS validation workbench. S2, S5, S9, S10, S15, S17.

### 46. Measurement versus interpretation

**PARTIALLY IMPLEMENTED explicitly:** count scene description is labeled model interpretation; temporal result limitations separate mask pixel counts from caption/direction; NDVI presents formula/threshold-based quantities; water describes predicted water; UI has limitations. However, model-derived pixel counts are deterministic *conditional on predictions*, not ground-truth measurements of real objects. No enforced common evidence type system guarantees that distinction everywhere. S2, S9, S10, S12, S17.

### 47. Model mask versus ground truth

**IMPLEMENTED labeling/limitations:** temporal and water outputs identify predictions; grounding labels proposals/segmentations. Reference labels belong to evaluation artifacts, not user-run truth. **UNVERIFIED user comprehension:** no usability evidence establishes that novices consistently understand this distinction. S9, S10, S15, S17; E3, E4.

### 48. Score versus accuracy

**IMPLEMENTED in relevant descriptions:** fusion scores and grounding detector/SAM scores are model scores; water limitations state uncalibrated scores; evaluation metrics are separate. **NOT IMPLEMENTED:** calibrated per-run correctness estimates. A .5 score threshold and SAM predicted IoU are not measured accuracy of the uploaded scene. S6, S9, S15, S17.

### 49. Optical/SAR/joint disagreement

**IMPLEMENTED exposure:** land-cover UI shows all three score sets; water UI shows all three counts and exports all three masks/probabilities, while its image panels emphasize the joint result. **NOT IMPLEMENTED:** automatic scientifically justified reconciliation, best-modality selection, or a dedicated spatial disagreement map. S6, S9, S17.

### 50. Temporal caption–mask disagreement

**IMPLEMENTED presentation of both; NOT IMPLEMENTED conflict detector:** caption and mask/counts are shown together. Direction-query wording triggers a caveat, not a consistency calculation. There is no automated suppression/reconciliation based on caption-versus-mask disagreement. S5:work, S10:temporal, S17.

### 51. Limitations close to outputs

**IMPLEMENTED but uneven:** main answer notes/trace; paired open limitations plus collapsible technical trace; grounding result limitations and score explanations. Stale historical reliability/evaluation material remains accessible and must not override current behavior. No new UI comprehension test was conducted. S1:reliability, S17; E8.

## G. Compute and resource economics — recorded measurements only

### 52. Device per workflow

**IMPLEMENTED:** VQA CUDA plus CPU decoding/tokenization; NDVI CPU; served MCI/water/fusion CPU; grounding CUDA plus CPU decoding/postprocessing/rendering. GPU experiment support for paired models is distinct from their current HTTP path. See Q5. S1–S3, S5, S6, S9, S10, S15.

### 53. Available latency measurements

**MEASURED HISTORICALLY; current distribution UNVERIFIED.** The CSV companion gives source file, JSON field and original value for every timing/memory scalar extracted by the audit collector from the selected JSON/JSONL evidence corpus. It includes per-case and superseded evidence, not just the following examples. It must not be averaged as one benchmark. This is not a claim that every timing mention in every unstructured log has been exhaustively parsed.

The preserved paired HTTP replay contains these eight runs (seconds, rounded here; originals retained in E2/CSV):

| Run | Specialist/result seconds | Caller elapsed seconds | Boundary |
|---|---:|---:|---|
| VQA before | 1.259 | 2.051 | Main work includes generation 1.128; paired caller includes bridge/polling/packaging |
| MCI temporal | 11.208 | 11.877 | CPU specialist plus its exports; outer elapsed larger |
| Water India | 1.044 | 1.702 | CPU three-mode water specialist; outer packaging separate |
| Water Bolivia | .845 | 1.129 | Same code, different source validity/content |
| Land cover | 1.001 | 1.606 | CPU three-model path |
| NDVI | .219 | 1.061 | Main analytical work; paired bridge/exports add elapsed time |
| VQA after | .995 | 1.524 | Generation .968 |
| Rural/urban pilot | 1.824 | 2.531 | Generation .731; not directly comparable to baseline query |

Other retained measurements: standalone water GPU inference 1.780 s; water training 319.219 s; served-precision CPU water evaluation 71.708 s; MCI GPU evaluation 47.358 s and CPU verification 39.773 s; historical isolated fusion GPU load+infer .731/.420/.433 s for SAR/optical/joint; old **inactive ChangeFormer** 6.672 s. Grounding cycle and VQA cold times are in Q55. Different inputs, warm/cold state, devices and timing scopes prevent direct ranking. E2–E5, E8.

### 54. Available RAM/VRAM measurements

**MEASURED HISTORICALLY:**

| Component/context | Recorded CUDA peak allocated | Recorded peak reserved | Interpretation |
|---|---:|---:|---|
| Paired replay baseline VQA | 4.244 GiB | Not supplied in that result | PyTorch allocated peak, not total process/device memory |
| Paired replay rural pilot | 4.177 GiB | Not supplied | Different token/generation path |
| Same-port grounding cycle | 2.678 GiB | See raw evidence where present | Sequential DINO/SAM, VQA unloaded |
| Standalone water GPU | 191.519 MiB | 264 MiB | Batch 1, 17×512×512; served path CPU |
| Water training | 1,001.482 MiB | 1,068 MiB | Training, not inference |
| MCI GPU evaluation | 582.931 MiB | 648 MiB | Historical GPU evaluation, served path CPU |
| Fusion SAR / optical / joint isolated | 113.098 / 113.633 / 113.767 MiB | 148 MiB each | Separate isolated loads; not combined residency |
| Inactive ChangeFormer isolated | 461.156 MiB | 624 MiB | Not active temporal service |

**UNVERIFIED:** peak process RAM/RSS for each currently served workflow; combined system RAM requirement; complete device memory including runtime/display/other processes. No suitable per-workflow peak CPU-RAM measurement was established. Exact additional historical fields are in the CSV. E2–E5, E8.

### 55. VQA cold load versus inference

**MEASURED in preserved same-port cycle:** before grounding, VQA load 6.241 s, generation 18.803 s, caller wall 27.907 s; after grounding evicts VQA, reload 14.965 s, generation 3.338 s, caller wall 18.401 s. These are individual observations, not cold-start averages or identical-generation-cost trials. Grounding caller wall was 23.570 s versus worker-reported 16.367 s. The paired replay's warm-looking short runs do not justify claiming all VQA responses take about one second. S1:run_job/prepare_lab_gpu; E8.

### 56. Does NDVI invoke GPU?

**NOT IMPLEMENTED/NOT REQUIRED for its computation:** `analyze` dispatches NDVI to `run_ndvi` before the VQA loading/generation branch; Rasterio/NumPy/stages perform the calculation. A previously cached VQA model may still occupy GPU memory, so “NDVI computation uses CPU” does not mean “GPU memory is necessarily empty.” S1–S3.

### 57. Router avoidance of GPU inference

**IMPLEMENTED for recognized NDVI:** `routing.route` → task ndvi → `ndvi_run` → `run_ndvi` → `geo.analyse`, without `run_job` or VLM generation. Unknown/general visual questions can still invoke the VLM. No automatic deterministic solver for every count/presence/area question exists. S1, S2, S4.

### 58. Loaded models and known sizes

**IMPLEMENTED residency behavior / measured file sizes:**

| Service | Models | Known size evidence |
|---|---|---|
| Main VQA | Cached AdaptLLM remote-sensing Qwen2-VL-2B; optional PEFT adapter | “2B” is checkpoint family name, not this audit's parameter census; adapter file 2,193,720 bytes; pilot training artifact reports 544,768 trainable parameters |
| NDVI | None required | Deterministic raster arrays only |
| Paired MCI | Cached encoder, attentive encoder, decoder | MCI checkpoint 913,762,855 bytes; file includes more than a bare inference parameter count |
| Paired water | WaterUNet loaded on each run, reused for its three passes | 1,966,130 parameters; checkpoint 7,879,873 bytes |
| Paired land cover | Three cached ResNet50 models | SAR 94,423,500; optical 94,523,860; joint 94,548,948 bytes |
| Grounding | DINO then SAM, explicitly released sequentially | DINO 689,359,096; SAM 374,979,480 bytes |

File bytes are not RAM/VRAM requirements. MCI/fusion may remain cached together in the paired CPU process after use; peak combined RAM is UNVERIFIED. Exact asset hashes and installed revisions are in E1 and S18. S1, S6, S9, S10, S15; E1, E3, E5, E7.

### 59. Coexistence on an 8 GB GPU

**UNVERIFIED simultaneous residency.** Standalone measurements establish that individual tested components ran on the recorded roughly 8 GB device. The main/grounding controller demonstrates sequential eviction/reload, not coexistence. Paired HTTP paths use CPU. Adding isolated PyTorch peaks is not a valid demonstrated concurrency limit because allocator/context/activation/lifetime behavior differs. E5, E8; S1, S5, S15.

### 60. Cache, preload and reuse

**IMPLEMENTED:** lazy cache main VQA/processor and optional adapter; disable adapter for baseline reuse; cached MCI and three fusion models; sequential unload/reload for grounding; WaterUNet reloaded per water call. **NOT IMPLEMENTED:** result cache keyed by input/query, persistent model worker scheduler across services, startup preloading of all models, or general computation memoization. Uploads/results are stored, but storage is not automatic result reuse. S1, S6, S9, S10, S13–S15.

### 61. Cold versus loaded execution

**IMPLEMENTED:** first VQA/MCI/fusion use includes model construction/loading; later uses skip cached loading. Grounding forces subsequent VQA reload and starts a fresh subprocess for each grounding run. Water reloads each run. Main records load/generation trace; timing differences also include query/image/token variation. Warm/cold service-level percentiles are UNVERIFIED. S1, S6, S9, S10, S15; E2, E8.

### 62. Dominant compute costs evidenced by profiling

**MEASURED only for traced cases:** in the grounding cycle, detector load 3.080 s, detection 7.364 s, SAM load 1.913 s, segmentation 2.698 s, rendering .060 s; detection was the largest of those stages. VQA examples show both generation-dominant and reload-dominant runs. **UNVERIFIED finer attribution** for CPU paired operations: aggregate specialist seconds do not isolate decoding, normalization, forwards and exports. No monetary estimate follows from these records. E8; S1, S15.

### 63. Large VLM on deterministic answers

**NOT in NDVI. IMPLEMENTED in visual-count workflows:** final integer formatting is deterministic, but the count estimate comes from VLM generation and a separate description can invoke it again. MCI pixel counting is deterministic after neural inference, and caption generation still executes. Water/fusion do not call the large VQA VLM. S1, S2, S9, S10, S12.

### 64. Export/evidence expense

**UNVERIFIED as a general proportion.** Grounding records a render-stage duration in the cited run; paired specialist seconds versus caller elapsed leave unseparated loading, HTTP/polling, copying and ZIP overhead. The difference is not a measured export-only cost. NDVI stage creation is included in its work, without a comprehensive isolated export benchmark. S1, S5, S13, S15; E2, E8.

## H. Deployment burden

### 65. Clean-machine deployment requirements

**PARTIALLY IMPLEMENTED reproducibility.** Code requires: a Linux/WSL-compatible Python runtime; source plus static assets/vendor modules; Python packages including PyTorch, Transformers, PEFT, Pillow, NumPy, Rasterio/GDAL, pyproj, FastAPI/Uvicorn, requests and Hugging Face tooling; CUDA-compatible NVIDIA driver/runtime for VQA/grounding; cached base/adapter/grounding models; paired model manifests, checkpoints, ConfigILM constants/source and target dependency directory; writable hardcoded `/root/satquery` data paths; samples if using sample flows. Then start main and paired services. `paired_lab/bootstrap.py` restores pinned paired assets, but assumes foundational dependencies and layout already exist. `requirements-app.txt` pins only four app packages and is not a complete lockfile. No complete fresh-machine installation was demonstrated in this audit. S1, S6, S14, S15, S18, S19, S21; E1.

### 66. Separately started services

**IMPLEMENTED:** main Uvicorn port 8765; paired Uvicorn port 8767. `paired_lab/launch.py` checks health and starts missing processes. Grounding is mounted in main, spawning a temporary model worker per job. No separately required public cloud inference service. S1, S5, S14, S21.

### 67. Ports/processes/workspaces

**IMPLEMENTED and read-only observed:** main 8765 and paired 8767 processes reference this SatQuery checkout. Source is Windows filesystem; Python/env and data are WSL `/root/satquery`; paired runtime `/root/satquery/paired-lab`; grounding runtime `/root/satquery/grounding-lab`; caches `/root/.cache/huggingface`. Grounding worker adds a subprocess only while active. Other unrelated workspace applications were not audited. S1, S6, S14, S21; E1.

### 68. Python environments

**IMPLEMENTED current arrangement:** one shared `/root/satquery/.venv` interpreter plus separately installed paired dependencies in a directory inserted into `sys.path`. This is not evidence that two incompatible virtual environments are mandatory. **UNVERIFIED clean dependency resolution:** the combined arrangement is not captured by one complete lockfile. E1; S6, S18, S19, S21.

### 69. Fully offline deployment after provisioning

**PARTIALLY IMPLEMENTED / UNVERIFIED operationally:** active inference reads local weights and local files; VQA uses local-files-only cached snapshot, fusion constructs models without fetching pretrained weights, active MCI SegFormer branch uses local checkpoint, grounding uses installed assets. First setup needs downloads or manually transferred equivalent files. No network-disabled end-to-end test or complete offline installer was found. S1, S6, S10, S15, S19.

### 70. Third-party inference APIs

**NOT IMPLEMENTED in active workflows:** inference is local. The paired single-image bridge uses HTTP to `127.0.0.1:8765`, not an external provider. Download/bootstrap code contacts model/data hosts during setup. S1, S6, S9, S10, S13, S15, S19.

### 71. What user data leaves the machine?

**No explicit external transmission found in the inspected first-party inference paths.** Imagery/query moves through browser→local service, paired→local main service and local subprocess/files. **UNVERIFIED:** all dependency telemetry/network behavior, user browser extensions, remote mounting, and any future hosted configuration. Do not upgrade a source inspection to a network-isolation certification. S1, S5, S13–S15.

### 72. Air-gapped capabilities

**Code-supported given complete provisioning:** NDVI and all local model workflows; GPU remains necessary for served VQA/grounding. **UNVERIFIED in a real air gap:** startup with every dependency/cache already transferred and external network blocked. Model/data acquisition, external links and missing-file recovery would not function without supplied assets. S1, S6, S9, S10, S15, S19.

### 73. Minimum demonstrated hardware

**MEASURED host context, minimum UNVERIFIED:** evidence names an NVIDIA GeForce RTX 5060 Laptop GPU with 8,151 MiB device total; runtime is WSL2/Python 3.11.16. Paired CPU runs are archived. No systematic hardware downscaling establishes minimum CPU, system RAM, storage, GPU generation or a “simplest computer” requirement. E1, E5, E8.

### 74. Demonstrated 8 GB claims

**MEASURED:** VQA, adapter use, sequential VQA→grounding→VQA, and isolated paired-model GPU experiments on the recorded device. **UNVERIFIED:** all models simultaneously resident, multi-user concurrent throughput, long-running memory stability, arbitrary full-resolution scenes, or all 8 GB GPUs. Served paired CPU results are not evidence of simultaneous GPU operation. E2, E5, E8.

### 75. Undocumented/non-reproducible setup boundaries

**PARTIALLY IMPLEMENTED:** incomplete base dependency lock; hardcoded personal/root paths; external LoRA/cache/manifests/source constants; no complete main/grounding fresh-clone bootstrap demonstrated; `setup_models.py` resolves remote current metadata whereas the newer paired bootstrap uses pinned manifest revisions; evaluation regeneration scripts for some later CPU rescoring are not present as a clearly identified standalone reproducible command; source snapshot lacks a verified whole-application commit identity. Sample access and commercial rights are additional unresolved deployment facts. S18–S21; E1, E3, E4.

## I. Reproducibility and auditability

### 76. Determinism by workflow

**IMPLEMENTED deterministic arithmetic:** NDVI and post-prediction counts/thresholds/argmax/label formatting for fixed values and code. VQA uses greedy decoding (`do_sample=False`); MCI uses greedy decoding; water/fusion run evaluation inference; grounding uses fixed processing. **UNVERIFIED bitwise reproducibility across devices/library versions:** floating-point kernels and ties may differ. MCI evidence already records 52 class pixels differing CPU versus GPU across 6,553,600 pixels, despite identical captions. S1, S2, S6, S9–S12, S15; E4.

### 77. Fixed random seeds

**IMPLEMENTED in specific code:** WaterUNet training seeds Python/NumPy/Torch with 42 and disables cuDNN benchmark; registration RANSAC is seeded; MCI evaluation artifact reports sample-selection seed 42. **NOT a global guarantee:** no application-wide deterministic-kernel/environment contract was established. Greedy generation alone is not such a contract. S11, S16; E4.

### 78. Model/checkpoint version pinning

**PARTIALLY IMPLEMENTED:** base VQA revision hardcoded; paired runtime manifest pins three BIFOLD revisions, MCI checkpoint/source and old ChangeFormer; grounding installed manifest records revisions; WaterUNet SHA-256 checked in audit and reported per run. MCI reads a manifest hash rather than freshly hashing weights each user run; pilot external adapter path is not sufficient by itself to freeze bytes. Current audit hashes help identify installed files but do not retroactively attest every historical run. S1, S9, S10, S15, S18; E1.

### 79. Input hashing

**IMPLEMENTED:** main raw upload SHA-256, paired inspected TIFF SHA-256, grounding raw upload SHA-256. Main/grounding normalized PNGs may differ from hashed original bytes. Paired bundles preserve originals; grounding bundle omission of job metadata weakens portable hash linkage. S1, S7, S14.

### 80. Preprocessing parameter recording

**PARTIALLY IMPLEMENTED:** NDVI metadata/scales/formula/threshold/quality policy; paired checks and specialist normalization/threshold traces; grounding threshold/mode/category and processing trace. Some fixed implementation details require code, and package/library behavior is not fully captured per run. S1, S2, S5, S6, S9, S10, S14, S15.

### 81. Archiving model outputs

**IMPLEMENTED locally:** main run JSON; paired result plus arrays/images/ZIP; grounding result/artifacts/logs/job files. **PARTIALLY IMPLEMENTED retrieval:** main and paired job indexes are memory-only; see Q144. No immutable remote archive, retention policy, or migration mechanism. S1, S5, S14.

### 82. Frozen/hashed evaluation datasets

**PARTIALLY IMPLEMENTED:** flood manifest enumerates 1,338 files and splits (252 train, 89 validation, 90 test, 15 Bolivia); MCI artifact identifies archive revision, SHA-256 and 100 selected results; reliability artifacts contain hashes/verification paths. **UNVERIFIED universal freeze:** these do not establish every historical evaluation/training input and human tuning decision as immutable, or prove the same clean process was followed before each recorded result. E3, E4, E7; S16.

### 83. Historical reproducibility after changes

**PARTIALLY IMPLEMENTED:** originals/parameters/model identifiers and prediction arrays let an analyst reconstruct many numerical outputs. Missing full source/environment snapshot, mutable external assets, nonuniform model hash checking, GPU/CPU differences, missing run-index recovery and some missing evaluation executors prevent guaranteed exact replay. An artifact checksum proves bytes, not scientific independence or complete procedural provenance. S1, S5, S14, S18–S20; E1, E4.

### 84. Independently recomputable numerical outputs

**IMPLEMENTED:** NDVI count/percentage/eligible area from original bands or exported NDVI+validity/georeference+threshold; temporal counts from exported classes/argmax scores; water counts/percentages from scores and valid mask; fusion selected labels from score table/.5; grounding mask union coverage and retained proposal counts from arrays/records. **NOT independently established by this:** the semantic correctness of predictions/captions, the sensor's real calibration, or physical water/change area not calculated by code. Fresh archived-array checks confirmed two water runs, one MCI run and one NDVI run in E1.

### 85. Evidence only in logs/local metadata

**PARTIALLY IMPLEMENTED portable evidence:** grounding `job.json`, `request.json`, worker log/progress/errors and raw-upload identity live outside its allowlisted evidence ZIP; setup/download/load errors and development/training traces are not automatically attached to ordinary user runs; machine package state is absent from standard bundles; main full original raster is stored server-side but not included in a single main evidence package. Paired bridge retains additional main raw JSON and originals. S1, S5, S13–S15; E1.

## J. Failure prevention

### 86. Intentional refusals

**IMPLEMENTED inventory of audited guards:** disallowed host/origin; oversized/invalid/multiframe/unsupported image; invalid image/run ID; main query length/mode/pilot format; unsupported routed task; uncalibrated NDVI or incompatible query threshold; missing required raster bands; unusable NDVI pixels; obsolete specifically blocked sample hash; busy worker; paired wrong number/type of inputs; mixed single/paired uploader records; unsupported modality combination; required sensor/band/unit/shape/dtype mismatch; date conflict/reversal/excess separation; CRS/affine/resolution mismatch where enforced; singular/sheared/rotated transform checks; temporal misalignment or insufficient evidence on non-benchmark uploads; water no common finite pixels; unsupported water/land-cover task; unavailable/misloaded model; grounding invalid category/mode/threshold/size, missing CUDA or <3 GiB free memory, timeout. Some model failures are failed jobs rather than pre-execution refusals. This inventory is scoped to the active paths, not formal proof of every possible exception. S1, S2, S4–S11, S14, S15.

### 87. Warnings that continue

**IMPLEMENTED:** NDVI missing SCL/area-unavailable and stage-render warning; VQA model-answer limitations, response-length/format treatment and failed optional count description; temporal directional interpretation caveat and predicted-mask limitations; trusted benchmark unverified registration; water uncalibrated/domain/water-not-flood limitations; fusion below-threshold does not prove absence; grounding proposals/no-detection do not prove presence/absence and mask quality is not accuracy. Warning delivery is workflow-specific. S1–S3, S5–S12, S15.

### 88. Plausible but scientifically invalid output risks

**UNVERIFIED correctness despite successful execution:** wrong or forged metadata; misordered data falsely labeled with correct band names; physically shifted optical–SAR arrays with identical grid metadata; clouds/shadow or speckle outside model assumptions; water data at unsupported physical resolution that passes shape/tags; 14-day acquisitions spanning real change; inappropriate temporal imagery matching RGB shape but outside training domain; NDVI falsely tagged reflectance or threshold interpreted as health without validation; open VQA hallucination/count agreement on a shared error; low-confidence grounding false positives. These are code-supported risk paths, not a claim that every listed case was experimentally triggered this turn. S2, S4, S7, S9–S12, S15.

### 89. Incorrect-routing tests

**IMPLEMENTED test sources:** `tests/test_routing.py`, `test_presence_routing.py`, `test_rural_phrasing.py`, `test_dispatch.py`; paired input/controller checks and preserved `input-controller-tests.json`. Dispatch tests extract/mock selected functions and do not execute all live neural inference. Current suite execution is UNVERIFIED in this audit. S20; E6.

### 90. Invalid geospatial-input tests

**IMPLEMENTED test sources/evidence:** `test_geo.py`, `test_ndvi_precision.py`, `test_stages.py`; paired `test_inputs.py`, `test_controls.py`; resumed controller report covering shape/bands/grid/units/date, shear/cross-sensor/shift and water contracts. Some paired tests contact services or generate data; none was executed as part of this read-only audit. S20; E6.

### 91. Unavailable specialist fallback tests

**PARTIALLY IMPLEMENTED:** code raises/fails on missing assets, invalid checkpoints, upstream bridge errors and absent GPU; dispatch/refusal tests cover selected unsupported/busy paths. No comprehensive failure-injection suite removing each model/service and proving every UI response was found. Fail-closed behavior is supported by source for those paths; blanket tested coverage is UNVERIFIED. S1, S5, S9, S10, S13–S15; S20.

### 92. Heuristic/mock replacement on specialist failure

**NOT IMPLEMENTED in active inference paths:** exceptions produce error/failed jobs rather than synthetic masks/scores. Heuristic routing, answer parsing and postprocessing are implemented normally; they are not fallback scientific inference. Optional scene-description failure may preserve the count with a warning. NDVI stage failure may preserve its completed numerical analysis. S1, S5, S12–S15.

### 93. Success state despite scientific failure

**PARTIALLY PREVENTED:** thrown analytical/model errors mark error/failed; no completed mock substitute found. **Possible by design:** NDVI analytical success with failed optional stage images; count success with failed optional description; accepted but scientifically inappropriate input or a wrong neural prediction completes successfully because there is no ground-truth check. The bridge can fail the outer NDVI job if it cannot fetch a stage the main run treated as optional. Stale status metadata can also misdescribe adapter state. S1, S5, S12, S13, S17.

### 94. Fabricated scores/placeholders/demo outputs

**NOT IMPLEMENTED in the traced active paths:** fabricated analytical score/mask fallback was not found. Demo samples invoke real specialists; old evaluation tabs load preserved reports, not new user inference. Main status hardcodes “Baseline - no adapter,” which is a misleading status label rather than a measured model-state report. Reliability text and old evaluation material can be stale. Absence of fabricated fallback is scoped to traced source, not a certification of every historical/demo file. S1:status/reliability; S5:evaluation/work; S17.

### 95. Silent-failure risks identified

**PARTIALLY IMPLEMENTED prevention; unresolved risks:** metadata authenticity; units override; missing physical optical–SAR registration check; water resolution/domain mismatch; missing cloud/speckle correction; temporal diagnostics missing difficult registration errors; permissive general VQA fallback; lexical routing edge cases and road text substitution; same-model mirrored count agreement mistaken for verification; caption/mask conflict not detected; model score treated as accuracy; checkpoint bytes changing beneath recorded manifest; precision/version drift; old evaluation material mistaken for active-model evidence; process-local locks under multiple workers; forgotten run IDs after restart; storage accumulation; lost/missing portable provenance; no tenant boundary. No exhaustive silent-failure proof was possible. S1–S15, S17–S20.

## K. Optical–SAR water specifically

### 96. Actual archived water run

**IMPLEMENTED; archived outputs independently checked:** paired run `4e99304de67c43d9b8a9516b168965c7` (India) follows Q6 water path. The original input pair and result bundle exist. CPU specialist time was 1.044429 s; recorded caller elapsed 1.701675 s. It reports 134,387 SAR-only, 130,106 optical-only and 129,908 joint water pixels, on 262,144 valid pixels. This audit recomputed thresholded counts from the preserved scores/valid mask and checked ZIP integrity; all matched. This is validation of saved postprocessing, not a new forward pass or ground-truth accuracy test. S5, S9; E1, E2.

### 97. Exact SAR preprocessing

**IMPLEMENTED:** read expected VV/VH float arrays already in dB; compute `clip((SAR + 20) / 10, -3, 3)` as float32; common valid mask requires finite channels; invalid values are zero-filled for model input; absent SAR mode zeros its channels and changes availability flags. **NOT IMPLEMENTED:** raw SAR calibration, conversion from raw intensity to dB, terrain correction, geocoding, speckle filtering or co-registration. S9:prepare/available; S7:validate.

### 98. Exact optical preprocessing

**IMPLEMENTED:** required 13-band Sentinel-2 L1C order; float32 `clip(optical / 3000, 0, 4)`; common finite mask; invalid zero-fill; zero channels/availability flags for SAR-only mode; RGB preview uses selected visible channels and display scaling. **NOT IMPLEMENTED:** atmospheric correction, new cloud mask, resampling or physical alignment. S9:prepare/available/segment; S7.

### 99. Sen1Floods11 assumptions

**IMPLEMENTED/recorded:** two S1 bands, thirteen S2 bands, 512-pixel scene contract, fixed normalization, binary water/non-water labels and common validity policy; training uses official split lists, random 256 crops/augmentation and random modality availability, with validation-joint checkpoint selection. Manifest records 252 train, 89 validation, 90 test and 15 Bolivia samples. Official test shares event regions with training; Bolivia is the recorded separate-event holdout. It is not an ISRO sensor validation. S9, S16; E3.

### 100. Pre-registration required?

**YES, IMPLEMENTED contract, manual preparation.** Matching pixel grids are required; the application does not align the pair. Physical cross-modal co-registration remains UNVERIFIED. S7, S9.

### 101. Pair validation

**IMPLEMENTED:** modality count; 512×512 dimensions; optical13/SAR2; strict descriptions/order; declared Sentinel-1 GRD/Sentinel-2 L1C; expected units; matching CRS/affine; valid transform checks; acceptable dates/separation; common finite pixels. Trust of declared metadata remains. S7:inspect/validate.

### 102. Dimensions/CRS/transform disagreement

**IMPLEMENTED refusal** before water inference, through paired `prepare`/`validate`. No automatic reprojection, resampling or registration correction. S5:prepare; S7:validate.

### 103. Matching metadata but shifted pixels

**UNVERIFIED physically; can continue.** The water path lacks cross-modal image-content registration checking, so a shifted pair can pass metadata checks and generate plausible invalid predictions. The SIFT diagnostic is used for temporal optical pairs, not water. S7, S11.

### 104. Three inference outputs

**IMPLEMENTED:** `s1-water.png`, `s2-water.png`, `all-water.png`; per-mode probabilities in `water-scores.npz`, per-mode counts and denominator in JSON (UI computes percentages; answer includes joint percentage); joint `water-overlay.png` and georeferenced `water-mask.tif`. Modes use one WaterUNet checkpoint with different channels/flags, not three separately trained water models. S9.

### 105. Disagreement inspection

**PARTIALLY IMPLEMENTED:** three counts visible in UI, all masks/probabilities downloadable; joint mask emphasized visually. No dedicated disagreement raster or automatic causal explanation; spatial side-by-side comparison of separate mode masks requires opening their downloads/artifact URLs. S9, S17.

### 106. Counts and water areas

**IMPLEMENTED counts:** threshold softmax water probability `>= .5` and intersect valid mask; sum resulting booleans. Displayed per-mode percentages use the common valid-pixel denominator; full-image pixel count is also reported, but a full-image water percentage is not separately computed in the result. **NOT IMPLEMENTED water area:** no square-metres/hectares computation exists in this served specialist. S9:segment.

### 107. Pixel-area determination

**NOT IMPLEMENTED for water.** Output TIFF inherits source georeference, but that does not mean the service calculates pixel area. NDVI's projected affine-area computation is a separate code path. S9 versus S2:analyse.

### 108. Water provenance

**IMPLEMENTED:** checkpoint hash, selected epoch, model/tool name, normalization/bands/availability policy and CPU trace (path and architecture are additionally identifiable in source/runtime manifest); server adds query/controller/UTC/UUID and input hashes/checks; originals copied into bundle. **PARTIALLY IMPLEMENTED:** no verified calibration processing history, physical registration proof, full code/environment digest or ground truth. S5, S7, S9; E1.

### 109. Downloadable water evidence

**IMPLEMENTED:** original TIFF pair inside ZIP, result JSON, optical/SAR PNG previews, three water PNGs, joint overlay PNG, scores/valid-mask NPZ, joint georeferenced mask TIFF and ZIP. Artifact endpoint allowlist controls individual files; originals are obtained through the ZIP. S5:artifact/work; S9.

### 110. Missing scientifically relevant water evidence

**NOT IMPLEMENTED:** sensor calibration/terrain-correction lineage, cloud/speckle quality flags, physical registration assessment, validation labels for user uploads, calibrated uncertainty, area calculation, flood-versus-permanent-water baseline, automatic disagreement map/explanation, full per-run software environment. Model identity and three-mode predictions are present but do not supply these missing facts. S7, S9, S18.

Water evaluation context: preserved float32-CPU test IoU is SAR **.636437**, optical **.838969**, joint **.826440**; Bolivia IoU is **.640479**, **.814442**, **.815773** respectively. Thus the recorded official test does **not** show joint outperforming optical-only; Bolivia shows a small joint advantage. This is a specific split result, not a universal model ranking or ISRO accuracy. E3.

## L. Temporal road/building change specifically

### 111. Actual current MCI path and run

**IMPLEMENTED; archived output checked:** run `76962dace0d7402885d91ff1efe3c5b2` used `server.work → mci.temporal → infer`, with CPU specialist 11.207684 s and caller elapsed 11.876909 s. Caption describes houses being built; class counts are road 0, building 4,693. This audit recomputed argmax/classes/counts from archived NPZ and confirmed agreement. It did not rerun inference or validate the caption against ground truth. Old `engine.temporal`/ChangeFormer is not this endpoint's active branch. S5, S6, S10; E1, E2.

### 112. Exact input assumptions

**IMPLEMENTED:** two optical GeoTIFF RGB uint8 arrays, exactly 256×256×3; required RGB descriptions for uploads; same shape/grid/CRS for uploads, parsed chronological dates; finite acceptable affine; declared sensors cannot conflict when both are present; registration diagnostic acceptance. Trusted benchmark samples bypass selected legacy metadata checks. Sensor tags can be absent; shape compliance is not proof of model-domain suitability. S7, S11.

### 113. Automatic preprocessing

**IMPLEMENTED:** transpose band-first to HWC; fixed RGB normalization using means `[.39073,.38623,.32989]×255` and standard deviations `[.15329,.14628,.13648]×255`; tensor/model feature processing; no source raster warp. Source images and derived mask/overlay are rendered for review. S5:work; S10:infer/temporal.

### 114. Align or require alignment?

**Requires alignment; NOT IMPLEMENTED alignment correction.** SIFT/RANSAC checks consistency and may reject; it does not transform the source pair. S7, S11.

### 115. Output classes

**IMPLEMENTED:** class 0 unchanged, class 1 road change, class 2 building change. Evaluation ground-truth encoding is grayscale 0/128/255 mapped to those classes; an earlier incorrect palette evaluation is explicitly superseded. S10; E4.

### 116. Masks independent of caption text?

**IMPLEMENTED:** segmentation output and caption decoder are separate heads/operations using model features. Masks are not parsed from caption text. This is computational separation, not statistical independence of the shared model. S10:infer.

### 117. Construction versus demolition masks

**NOT IMPLEMENTED:** road/building change classes have no gain/loss direction label. Pixel counts do not establish newly built or removed area. S10.

### 118. Caption direction

**IMPLEMENTED model language; correctness UNVERIFIED per run:** decoder can say built/removed or directional phrases; preserved caption examples demonstrate generation. Segmentation does not prove direction, and the preserved lexical change/no-change metric is not a direction-accuracy benchmark. Server caveat is triggered for query words increase/decrease/gain/loss; it is not a general directional verification layer. S5:work; S10; E4.

### 119. Measurements directly from masks

**IMPLEMENTED:** stored road/building and total changed pixel counts, total denominator and total changed coverage percentage; unchanged count and class-specific percentages are derivable; derived class-coloured mask/overlay. **NOT IMPLEMENTED:** hectares, object number, road length, construction/demolition amounts. S10:temporal.

### 120. Separate inspectability

**IMPLEMENTED:** before, after, three-class colour mask and overlay; road/building pixel counts; generated/raw caption and score/class NPZ. Class-separated information is in the combined class raster/counts, not separate georeferenced road and building vector products. S10, S17.

### 121. Temporal exports

**IMPLEMENTED:** before/after PNG, `change-mask.png`, `overlay.png`, `scores.npz`, `result.json`, original input TIFFs inside `evidence.zip`. No georeferenced change TIFF or vector export is generated by current MCI function. S5:artifact/work; S10.

### 122. Deterministic after prediction

**IMPLEMENTED:** argmax on fixed scores, counts/coverage, fixed colour rendering and JSON summaries. Caption generation is a model operation; query-dependent caveat is deterministic text logic. Floating-point prediction differences across runtimes can still alter argmax upstream. S5, S10; E4.

### 123. Measurement versus model interpretation

**IMPLEMENTED distinction:** numerical counts measure the *predicted class raster*. Caption is generated interpretation. Neither establishes true changed objects or gain/loss without external verification. The app's limitations reflect this boundary. S10, S17.

### 124. Unchanged pair behavior

**MEASURED controls:** preserved identical and brightness/contrast control pairs returned zero changed pixels and “the scene is the same as before.” The 100-pair evaluation includes 50 unchanged pairs. **UNVERIFIED guarantee:** this does not prove every unchanged scene/acquisition condition yields zero false changes. S10; E4.

### 125. Caption versus mask inconsistency

**NOT IMPLEMENTED reconciliation:** both remain visible. There is no threshold-based contradiction detector, forced caption correction, or replacement of one output with the other. S5, S10, S17.

### 126. Current-path evaluation evidence

**MEASURED preserved evaluation:** 50 changed + 50 unchanged official LEVIR-MCI test pairs; current CPU-rescored IoU unchanged .982782, road .809739, building .819346; lexical caption change/no-change agreement 90/100 explicitly **not caption factual accuracy**. CPU verification records 0 differing captions and 52 differing class pixels against GPU across 6,553,600 pixels. Dataset archive revision/hash, per-case outputs, controls and required-tensor load checks are preserved. Earlier wrong-palette scoring must not be cited as current. These metrics were inspected, not regenerated from the dataset in this audit. E4; S10.

### 127. Untouched test data?

**UNVERIFIED as an absolute claim.** The artifact states official test selection, seed 42 and no local tuning; source uses a pretrained model and no local MCI training path was found. That supports a documented protocol, but cannot establish upstream checkpoint training exclusions, all prior human/model-selection exposure, or an immutable tuning history. A manifest/hash alone cannot prove complete test independence. E4; S10, S18.

## M. UI/workforce interaction

### 128. Minimum logical user actions

**IMPLEMENTED UI topology; not a timed usability study.** The counts below treat choosing a file as one logical file-selection operation, not the operating-system dialog's individual mouse clicks. They start with the relevant screen open, services ready, and suitable files already prepared. They exclude all sourcing/preprocessing and required scientific review. S17.

| Flow | File selections | Configuration choices | Query/text entry | Execution | Result delivery |
|---|---:|---|---:|---:|---|
| Main VQA | 1 | 0 if baseline appropriate; optional 1 mode choice | 1 | 1 submit | Automatic polling |
| Main NDVI | 1 | 0 with .5 default; otherwise 1 threshold edit | 1 | 1 submit | Automatic polling |
| Paired screen single VQA/NDVI | 1 | Select single-image input mode; optional NDVI threshold | 1 | 1 submit | Automatic polling |
| Paired own temporal pair | 2 | Select own-pair input mode; optical defaults may suffice; 0–2 date fields if absent in tags | 1 | 1 submit | Automatic polling |
| Paired own water/land-cover pair | 2 | Select own-pair input mode; declare optical/SAR; 0–2 date fields if absent | 1 | 1 submit | Automatic polling |
| Paired bundled sample | 0 | 0 for current/default sample or 1 sample selection | 0 if supplied query accepted, otherwise 1 | 1 submit | Automatic polling |
| Grounding | 1 | 0 if default category/mode/threshold suitable; otherwise category and optional mode/threshold changes | 0 free-form question | 1 submit | Automatic polling |

This counts visible field operations, not a fixed universal minimum across every existing UI state. A sample with a prefilled question demonstrates a different burden from preparing a new scientific pair.

### 129. Review and export actions, counted separately

**IMPLEMENTED:** primary result appears without another execution action; opening a collapsed trace/technical detail is an additional review action; switching an image stage/tab or zooming is another; paired/grounding bundle export is one download action; main JSON save and NDVI TIFF download are separate actions. Water separate-mode spatial inspection adds opening relevant artifacts. **UNVERIFIED:** the number of review actions needed for responsible acceptance; it depends on task/error/data and cannot be derived from button count. No conversion into time/labor savings is justified. S17; S1, S5, S14.

### 130. Hidden technical parameters available in evidence

**PARTIALLY IMPLEMENTED:** model/revision/adapter and routing trace; NDVI formula/threshold/calibration/quality/denominators; paired normalization, class thresholds, input-grid checks, water checkpoint identity and temporal registration; grounding stage timings/model scores/threshold trace. Some fixed constants exist only in source, not expandable UI. See Q30/Q80. S1–S3, S5, S6, S9–S15, S17.

### 131. Expert information shown on demand

**IMPLEMENTED:** collapsible execution/provenance traces, evaluation views, detailed JSON/ZIP/NPZ, grounding object/stage details. Primary result emphasizes images, answer/counts and limitations. Exact arrays and complete metadata require downloads/API rather than every field being rendered. S17.

### 132. Switching programs

**NOT required for an already compatible supported inference:** browser plus running local services suffice. **Manual external work remains:** obtaining/calibrating/registering/preparing arbitrary source products and certain advanced evidence checks. Grounding requires a different page, not necessarily another program. Deployment uses launcher/terminal outside the analytical page. S7, S14, S17, S21.

### 133. Writing code

**NOT required for supported UI execution with ready data.** Code may be needed for custom input preparation, independent recomputation, batch orchestration or rebuilding the environment; the app does not supply every such workflow. A no-code inference interface does not prove no-code preparation from raw satellite products. S1, S5, S14, S17–S21.

### 134. Manual specialist-to-specialist transfer

**NOT required within the six implemented workflows:** controller/bridge packages each flow automatically. **NOT IMPLEMENTED:** a user-defined pipeline where, for example, a grounding mask automatically constrains NDVI or water predictions feed temporal change. Doing such a composite today would require manual/external work and is outside the supported controller. S5, S8, S13.

### 135. Same interface/controller?

**PARTIALLY IMPLEMENTED integration:** port 8767 paired UI/controller can execute single-image VQA/NDVI through the port 8765 bridge, plus temporal/water/land cover locally. Port 8765's main router itself still rejects paired workflows. Grounding remains a separate `/grounding/` manual page and API. Two service processes exist even when one page exposes the connected workflows. S1, S5, S8, S13, S14, S17.

### 136. Review locations

**IMPLEMENTED topology, adequate-review count UNVERIFIED:** main result panel/stages + trace + downloaded JSON/TIFF for deeper verification; paired primary result/limitations + expandable trace/score table + one ZIP for complete saved inputs/arrays; grounding result/stages/objects + trace + ZIP, with additional job/log provenance only server-side. Roughly three UI/evidence layers recur, but not three universally sufficient expert checks. Complete environmental/source validation requires additional external evidence. S17; S1, S5, S14.

## N. Existing automation and APIs

### 137. Analysis endpoints

**IMPLEMENTED:** main `POST /api/images`, `POST /api/analyze`, direct `POST /api/ndvi`; paired `POST /api/images`, `POST /api/single-images`, `POST /api/analyze`; grounding (mounted prefix `/grounding`) `POST /api/images`, `POST /api/runs`. Poll/export endpoints below complete programmatic use. No new endpoint design is proposed. S1, S5, S14.

### 138. Current request/response contracts

**IMPLEMENTED contract summary** (optional defaults shown; structured result fields vary by task):

| Service / endpoint | Request | Response / follow-up |
|---|---|---|
| Main `POST /api/images` | Multipart `file` | Image record with UUID/name/dimensions/hash/preview and GeoTIFF metadata if applicable |
| Main `POST /api/analyze` | Form `image_id`, `question`, `mode=baseline`, `threshold=.5` | Job record/ID; poll `GET /api/runs/{id}` for queued/running/complete/error fields, answer/trace and statistics where applicable |
| Main `POST /api/ndvi` | Form `image_id`, `threshold=.5`, `question="Calculate NDVI"` | NDVI job, same polling family |
| Main `GET /api/images/{id}` | Known in-memory image UUID | PNG preview |
| Main `GET /api/runs/{id}/{artifact}` | Completed known job; artifact key such as `ndvi` or stage name | Allowlisted TIFF/PNG; keys are mapped to filenames by handler |
| Paired `POST /api/images` | Multipart `file`, required `modality`, optional `date`, `units` | Inspected metadata/hash/UUID; arrays/path omitted |
| Paired `POST /api/single-images` | Multipart `file` | Bridge image record/UUID, main ID/metadata |
| Paired `POST /api/analyze` | JSON `{images:[id] or [id1,id2], query, threshold?}` OR `{sample:sample_id, query, threshold?}` | `{id, task, checks}`; poll `GET /api/jobs/{id}` |
| Paired `GET /api/jobs/{id}` | In-memory UUID | Processing stage, complete result, or failed error |
| Paired `GET /api/runs/{id}/{filename}` | UUID and allowlisted actual filename | Saved artifact, e.g. `evidence.zip`, `result.json`, `water-scores.npz` |
| Grounding `POST /grounding/api/images` | Multipart `file` | UUID/name/dimensions/raw hash/preview |
| Grounding `POST /grounding/api/runs` | JSON `{image_id, category, threshold:.3, mode:"both"}` | Saved job metadata; poll `GET /grounding/api/runs/{id}` |
| Grounding `GET /grounding/api/runs/{id}/{artifact}` | Logical alias `source`, `boxes`, `outlines`, `masks`, `instances`, `arrays`, `record`, `bundle` | Allowlisted completed artifact |

Read-only status/sample/evaluation endpoints also exist. Host/origin restrictions apply to these local services. This is a code-derived contract, not a versioned public API stability promise. S1:upload/analyze/ndvi_run/result/analytical_artifact; S5:upload/upload_single/analyze/job/artifact; S14:Selection/run/get_run/artifact.

### 139. Scripted submit → analyze → download

**IMPLEMENTED:** an HTTP client can upload, submit, poll and retrieve artifacts. `single_bridge.py` itself performs this sequence; preserved live replay artifacts support prior execution. Main export needs a live in-memory job; paired downloads use known IDs and disk paths; grounding recovery uses disk records. No new scripted inference was run in this audit. S13; S1, S5, S14; E2.

### 140. Automatic operation chaining

**PARTIALLY IMPLEMENTED fixed chains:** upload/route/preprocess/infer/postprocess/export; VQA count plus description; grounding detection then segmentation; water/fusion three modes; paired bridge to main. **NOT IMPLEMENTED:** arbitrary user-defined task graph, automatic iterative scientific investigation, conditional cross-specialist planning or a general agent tool loop. S1, S5, S8, S9, S13–S15.

### 141. Batch input

**NOT IMPLEMENTED in analysis API:** one image or one pair per job. Two images forming a pair are not a batch. Evaluation/training scripts iterate datasets, but that does not establish a production batch endpoint. S1, S5, S14, S16, S19.

### 142. Safe concurrent requests

**PARTIALLY IMPLEMENTED:** process-local locks/busy flags serialize analysis and reject additional jobs with 409; single-worker executors run jobs; grounding shares main's GPU reservation. Separate paired CPU service may operate while main GPU is busy, except bridge calls contend with main. **UNVERIFIED/NOT IMPLEMENTED at deployment scale:** distributed locks, multiprocess worker safety, tenant-aware resource scheduling, stress-tested concurrency and bounded persistent backlog. Main NDVI also occupies the common busy slot, despite CPU arithmetic. S1, S5, S14.

### 143. Persistent job queue

**NOT IMPLEMENTED:** Python executor plus memory state/busy rejection is not a durable queue. Grounding saves job files but does not resume interrupted compute. No retry/cancel scheduler, durable worker broker or admission accounting was found. S1, S5, S14.

### 144. Persistence across restart

**PARTIALLY IMPLEMENTED, different by service:** main writes JSON/artifacts but its images/jobs dictionaries are lost; normal polling/artifact routes require them. Paired saves complete run directories/ZIPs; jobs/images dictionaries are lost, but artifact-by-known-UUID works from disk. Grounding reconstructs completed job status from saved files; interrupted jobs can be marked error, not resumed. No common run library/list endpoint restores all prior work.

**Fresh observation:** all eight preserved paired run folders and valid ZIPs were present, while their current `/api/jobs/{id}` calls returned 404. This establishes “files exist but job index unavailable now”; it does not itself date or prove which restart caused the loss. S1, S5, S14; E1.

### 145. CPU versus GPU separation

**IMPLEMENTED:** main NDVI dispatch bypasses VLM; paired neural specialists explicitly use CPU; main VQA uses CUDA; grounding runs isolated sequential GPU worker and evicts main cached model. **PARTIALLY IMPLEMENTED resource scheduling:** all main analyses share a busy gate, and no generalized device pool/cost scheduler exists. S1–S3, S5, S6, S9, S10, S14, S15.

## O. Data ownership and enterprise boundaries

### 146. Authentication/accounts

**NOT IMPLEMENTED:** no user accounts, login or tenant identity in audited active APIs. Localhost binding, TrustedHost and Origin filters limit exposure; they are not authentication. S1, S5, S14, S21.

### 147. User isolation

**NOT IMPLEMENTED:** shared directories and process state with UUID identifiers, no per-user ownership/authorization checks. An unguessable ID is not a tenant access policy. This implementation must not be described as a demonstrated multi-tenant SaaS. S1, S5, S14.

### 148. Upload location and retention

**IMPLEMENTED storage:** main `/root/satquery/app-data/images` and `runs`; paired `/root/satquery/paired-lab/app/uploads` and `runs`; grounding `/root/satquery/grounding-lab/app-data/{uuid}`. Main TIFF originals and previews, paired originals/copies and grounding normalized inputs are saved. **NOT IMPLEMENTED retention expiry:** no normal time-based deletion policy was found. E1; S1, S5, S14.

### 149. Automatic temporary-file deletion

**PARTIALLY IMPLEMENTED:** invalid paired uploads are deleted on the handled inspection failure path; selected error cleanup/release exists. **NOT IMPLEMENTED general lifecycle cleanup:** successful uploads, run bundles and most runtime artifacts remain indefinitely absent external/manual deletion. Grounding model unloading is memory cleanup, not user-data deletion. S5:upload/upload_single; S1, S14.

### 150. User deletion

**NOT IMPLEMENTED in API/UI:** no authenticated delete-own-run or upload deletion endpoint/control found. Local filesystem deletion is possible administratively but is not a user data-management workflow. S1, S5, S14, S17.

### 151. Sensitive content in logs/artifacts

**IMPLEMENTED recording can contain sensitive content:** queries/raw answers, image names/hashes/metadata/geography, original imagery/derived masks and checkpoint/runtime paths in JSON/ZIP; grounding worker/error logs and paired traceback files may include local paths/errors. Launcher disables HTTP access logs for its spawned services, but that does not sanitize saved analytical records or all library errors. No structured redaction policy was found. S1, S5, S13–S15, S21.

### 152. Telemetry

**No first-party analytics/telemetry sender found in inspected active code. UNVERIFIED for full deployment:** no packet capture/network-denied test or exhaustive third-party dependency telemetry audit was performed. Setup downloads are explicit external traffic. “No external inference API” is supported; “zero possible outgoing telemetry” is not established. S1, S5, S13–S15, S19; E1.

### 153. Licenses established from local metadata only

**PARTIALLY IMPLEMENTED inventory, not legal clearance:**

| Component | Local evidence | What can be established |
|---|---|---|
| SatQuery application | No top-level license file identified in inspected source folder | Redistribution/commercial grant not established by this audit |
| Active BIFOLD ResNet50 SAR/optical/joint | Installed model cards, captured in runtime verification | Metadata declares MIT; no further legal conclusion inferred |
| Grounding DINO tiny / SAM base | Installed model cards and grounding models manifest | Metadata declares Apache-2.0 |
| Active MCI / Change-Agent | Bundled `mci_vendor/LICENSE.txt` MIT; runtime manifest records checkpoint card Apache-2.0 and source academic-use statement | Preserve/reconcile relevant source/card statements; checkpoint grant not independently fully resolved here |
| Old ChangeFormer | Installed README line 224; runtime manifest note | Explicit non-commercial/research-only code statement; inactive in current temporal serving, still present/downloadable in project tooling |
| AdaptLLM VQA base and local adapter | Base model identity/pinned revision and adapter config/weights | Complete applicable license text not established from inspected local metadata; do not infer from model family name |
| Local WaterUNet checkpoint | Local training code/checkpoint and Sen1Floods11 manifest | No standalone full commercialization clearance established; training data provenance is recorded, complete rights review absent |
| Sen1Floods11, LEVIR-MCI, BigEarthNet/source scenes and example imagery | Dataset URLs/revisions/manifests/source attribution in evidence | Provenance is not a commercial-use license inventory; all relevant product/data terms not bundled/verified |
| Python packages and copied/vendor dependencies | Partial version pins, vendor license, runtime metadata | No complete dependency license/SBOM review found; no specific additional restriction invented |

Evidence: S18, S19, S22; E1, E3, E4. These are repository metadata observations, not legal advice or an external terms verification.

### 154. Third-party models needing explicit commercial review

**UNVERIFIED commercial clearance:** AdaptLLM base/adapter lineage; MCI checkpoint plus source/card statements; local WaterUNet's training-data/license chain; BIFOLD and grounding model notices/obligations and associated data/source terms. **Known explicit issue if retained/used commercially:** old ChangeFormer non-commercial statement. Its inactivity in serving does not automatically settle distribution of code/tooling that still includes it. No claim is made that MIT/Apache declarations themselves prohibit commercial use; the finding is that a complete applicable-terms review is absent. S18, S22; E1.

## What this audit proves and leaves open

The source contains executable routes for six bounded workflows, with meaningful input checks and saved model/numerical evidence. Existing local assets and archived runs support actual execution in the inspected installation. Recomputed saved arrays agree with the selected reported counts. None of those facts establishes general accuracy, time or labor savings against another tool, complete raw-data preparation, multi-user SaaS operation, or ISRO sensor readiness.

The next external comparison can legitimately use workflow topology, explicit preprocessing prerequisites, artifact availability, fixed device choices and the labeled measurements here. It must separately establish baseline tools, comparable inputs/tasks, human preparation/review time, failure rates and acceptable scientific quality. No additional feature is justified merely by this audit, and nothing was implemented during it.

## Evidence index

The following references identify the exact source files/functions used above. Line links point to inspected definitions; they are not a substitute for preserving this source snapshot when code later changes.

### S1 — Main service

- [server.py](<C:/Users/nrgen/.codex/scratch/SATquery AI/server.py>) — [local_requests](<C:/Users/nrgen/.codex/scratch/SATquery AI/server.py:29>), [status](<C:/Users/nrgen/.codex/scratch/SATquery AI/server.py:39>), [upload](<C:/Users/nrgen/.codex/scratch/SATquery AI/server.py:41>), [preview](<C:/Users/nrgen/.codex/scratch/SATquery AI/server.py:63>), [sample](<C:/Users/nrgen/.codex/scratch/SATquery AI/server.py:67>), [analyze](<C:/Users/nrgen/.codex/scratch/SATquery AI/server.py:69>), [run_job](<C:/Users/nrgen/.codex/scratch/SATquery AI/server.py:96>), [result](<C:/Users/nrgen/.codex/scratch/SATquery AI/server.py:164>), [evaluation](<C:/Users/nrgen/.codex/scratch/SATquery AI/server.py:168>), [development](<C:/Users/nrgen/.codex/scratch/SATquery AI/server.py:170>), [evaluation_evidence](<C:/Users/nrgen/.codex/scratch/SATquery AI/server.py:175>), [index](<C:/Users/nrgen/.codex/scratch/SATquery AI/server.py:180>), [scene_sample](<C:/Users/nrgen/.codex/scratch/SATquery AI/server.py:184>), [ndvi_run](<C:/Users/nrgen/.codex/scratch/SATquery AI/server.py:188>), [run_ndvi](<C:/Users/nrgen/.codex/scratch/SATquery AI/server.py:206>), [analytical_artifact](<C:/Users/nrgen/.codex/scratch/SATquery AI/server.py:234>), [reliability](<C:/Users/nrgen/.codex/scratch/SATquery AI/server.py:244>), [reliability_evidence](<C:/Users/nrgen/.codex/scratch/SATquery AI/server.py:255>), [reserve_lab_gpu](<C:/Users/nrgen/.codex/scratch/SATquery AI/server.py:262>), [prepare_lab_gpu](<C:/Users/nrgen/.codex/scratch/SATquery AI/server.py:268>), [release_lab_gpu](<C:/Users/nrgen/.codex/scratch/SATquery AI/server.py:275>)

### S2 — GeoTIFF/NDVI

- [geo.py](<C:/Users/nrgen/.codex/scratch/SATquery AI/geo.py>) — [bands](<C:/Users/nrgen/.codex/scratch/SATquery AI/geo.py:11>), [ingest](<C:/Users/nrgen/.codex/scratch/SATquery AI/geo.py:19>), [calculate](<C:/Users/nrgen/.codex/scratch/SATquery AI/geo.py:46>), [analyse](<C:/Users/nrgen/.codex/scratch/SATquery AI/geo.py:56>), [coordinate](<C:/Users/nrgen/.codex/scratch/SATquery AI/geo.py:87>)

### S3 — NDVI stages

- [stages.py](<C:/Users/nrgen/.codex/scratch/SATquery AI/stages.py>) — [create_stages](<C:/Users/nrgen/.codex/scratch/SATquery AI/stages.py:10>)

### S4 — Main routing

- [routing.py](<C:/Users/nrgen/.codex/scratch/SATquery AI/routing.py>) — [route](<C:/Users/nrgen/.codex/scratch/SATquery AI/routing.py:12>)

### S5 — Paired HTTP service

- [paired_lab/server.py](<C:/Users/nrgen/.codex/scratch/SATquery AI/paired_lab/server.py>) — [local_only](<C:/Users/nrgen/.codex/scratch/SATquery AI/paired_lab/server.py:24>), [home](<C:/Users/nrgen/.codex/scratch/SATquery AI/paired_lab/server.py:33>), [status](<C:/Users/nrgen/.codex/scratch/SATquery AI/paired_lab/server.py:35>), [list_samples](<C:/Users/nrgen/.codex/scratch/SATquery AI/paired_lab/server.py:37>), [resumed_evaluation](<C:/Users/nrgen/.codex/scratch/SATquery AI/paired_lab/server.py:39>), [evaluation](<C:/Users/nrgen/.codex/scratch/SATquery AI/paired_lab/server.py:44>), [sample_file](<C:/Users/nrgen/.codex/scratch/SATquery AI/paired_lab/server.py:46>), [sample_preview](<C:/Users/nrgen/.codex/scratch/SATquery AI/paired_lab/server.py:51>), [upload](<C:/Users/nrgen/.codex/scratch/SATquery AI/paired_lab/server.py:59>), [upload_single](<C:/Users/nrgen/.codex/scratch/SATquery AI/paired_lab/server.py:69>), [single_preview](<C:/Users/nrgen/.codex/scratch/SATquery AI/paired_lab/server.py:80>), [prepare](<C:/Users/nrgen/.codex/scratch/SATquery AI/paired_lab/server.py:84>), [work](<C:/Users/nrgen/.codex/scratch/SATquery AI/paired_lab/server.py:108>), [analyze](<C:/Users/nrgen/.codex/scratch/SATquery AI/paired_lab/server.py:146>), [job](<C:/Users/nrgen/.codex/scratch/SATquery AI/paired_lab/server.py:157>), [artifact](<C:/Users/nrgen/.codex/scratch/SATquery AI/paired_lab/server.py:161>)

### S6 — Fusion and inactive ChangeFormer engine

- [paired_lab/engine.py](<C:/Users/nrgen/.codex/scratch/SATquery AI/paired_lab/engine.py>) — [load_temporal](<C:/Users/nrgen/.codex/scratch/SATquery AI/paired_lab/engine.py:22>), [temporal](<C:/Users/nrgen/.codex/scratch/SATquery AI/paired_lab/engine.py:35>), [normalize](<C:/Users/nrgen/.codex/scratch/SATquery AI/paired_lab/engine.py:63>), [load_fusion](<C:/Users/nrgen/.codex/scratch/SATquery AI/paired_lab/engine.py:73>), [fusion](<C:/Users/nrgen/.codex/scratch/SATquery AI/paired_lab/engine.py:87>)

### S7 — Paired input contracts

- [paired_lab/inputs.py](<C:/Users/nrgen/.codex/scratch/SATquery AI/paired_lab/inputs.py>) — [inspect](<C:/Users/nrgen/.codex/scratch/SATquery AI/paired_lab/inputs.py:8>), [route](<C:/Users/nrgen/.codex/scratch/SATquery AI/paired_lab/inputs.py:25>), [_legacy_validate](<C:/Users/nrgen/.codex/scratch/SATquery AI/paired_lab/inputs.py:45>), [validate](<C:/Users/nrgen/.codex/scratch/SATquery AI/paired_lab/inputs.py:75>)

### S8 — Unified paired controller

- [paired_lab/controller.py](<C:/Users/nrgen/.codex/scratch/SATquery AI/paired_lab/controller.py>) — [plan](<C:/Users/nrgen/.codex/scratch/SATquery AI/paired_lab/controller.py:8>)

### S9 — Water specialist

- [paired_lab/flood.py](<C:/Users/nrgen/.codex/scratch/SATquery AI/paired_lab/flood.py>) — [Block](<C:/Users/nrgen/.codex/scratch/SATquery AI/paired_lab/flood.py:15>), [WaterUNet](<C:/Users/nrgen/.codex/scratch/SATquery AI/paired_lab/flood.py:19>), [prepare](<C:/Users/nrgen/.codex/scratch/SATquery AI/paired_lab/flood.py:34>), [available](<C:/Users/nrgen/.codex/scratch/SATquery AI/paired_lab/flood.py:43>), [load](<C:/Users/nrgen/.codex/scratch/SATquery AI/paired_lab/flood.py:52>), [segment](<C:/Users/nrgen/.codex/scratch/SATquery AI/paired_lab/flood.py:59>)

### S10 — Active MCI specialist

- [paired_lab/mci.py](<C:/Users/nrgen/.codex/scratch/SATquery AI/paired_lab/mci.py>) — [load](<C:/Users/nrgen/.codex/scratch/SATquery AI/paired_lab/mci.py:10>), [infer](<C:/Users/nrgen/.codex/scratch/SATquery AI/paired_lab/mci.py:33>), [temporal](<C:/Users/nrgen/.codex/scratch/SATquery AI/paired_lab/mci.py:45>)

### S11 — Optical registration diagnostic

- [paired_lab/registration.py](<C:/Users/nrgen/.codex/scratch/SATquery AI/paired_lab/registration.py>) — [diagnose](<C:/Users/nrgen/.codex/scratch/SATquery AI/paired_lab/registration.py:5>)

### S12 — VQA answer/count processing

- [vqa_answers.py](<C:/Users/nrgen/.codex/scratch/SATquery AI/vqa_answers.py>) — [_generalize](<C:/Users/nrgen/.codex/scratch/SATquery AI/vqa_answers.py:27>), [present_answer](<C:/Users/nrgen/.codex/scratch/SATquery AI/vqa_answers.py:42>), [present_open_answer](<C:/Users/nrgen/.codex/scratch/SATquery AI/vqa_answers.py:113>), [present_count_answer](<C:/Users/nrgen/.codex/scratch/SATquery AI/vqa_answers.py:124>)
- [counting.py](<C:/Users/nrgen/.codex/scratch/SATquery AI/counting.py>) — [parse_count](<C:/Users/nrgen/.codex/scratch/SATquery AI/counting.py:14>), [count_fields](<C:/Users/nrgen/.codex/scratch/SATquery AI/counting.py:24>)
- [count_description.py](<C:/Users/nrgen/.codex/scratch/SATquery AI/count_description.py>) — [add_count_description](<C:/Users/nrgen/.codex/scratch/SATquery AI/count_description.py:5>)

### S13 — Paired single-image bridge

- [paired_lab/single_bridge.py](<C:/Users/nrgen/.codex/scratch/SATquery AI/paired_lab/single_bridge.py>) — [request](<C:/Users/nrgen/.codex/scratch/SATquery AI/paired_lab/single_bridge.py:4>), [upload](<C:/Users/nrgen/.codex/scratch/SATquery AI/paired_lab/single_bridge.py:12>), [run](<C:/Users/nrgen/.codex/scratch/SATquery AI/paired_lab/single_bridge.py:14>)

### S14 — Grounding service

- [grounding_lab/app.py](<C:/Users/nrgen/.codex/scratch/SATquery AI/grounding_lab/app.py>) — [local_only](<C:/Users/nrgen/.codex/scratch/SATquery AI/grounding_lab/app.py:23>), [directory](<C:/Users/nrgen/.codex/scratch/SATquery AI/grounding_lab/app.py:29>), [page](<C:/Users/nrgen/.codex/scratch/SATquery AI/grounding_lab/app.py:34>), [status](<C:/Users/nrgen/.codex/scratch/SATquery AI/grounding_lab/app.py:37>), [upload](<C:/Users/nrgen/.codex/scratch/SATquery AI/grounding_lab/app.py:40>), [image](<C:/Users/nrgen/.codex/scratch/SATquery AI/grounding_lab/app.py:55>), [sample](<C:/Users/nrgen/.codex/scratch/SATquery AI/grounding_lab/app.py:61>), [Selection](<C:/Users/nrgen/.codex/scratch/SATquery AI/grounding_lab/app.py:65>), [run](<C:/Users/nrgen/.codex/scratch/SATquery AI/grounding_lab/app.py:72>), [worker](<C:/Users/nrgen/.codex/scratch/SATquery AI/grounding_lab/app.py:95>), [get_run](<C:/Users/nrgen/.codex/scratch/SATquery AI/grounding_lab/app.py:117>), [artifact](<C:/Users/nrgen/.codex/scratch/SATquery AI/grounding_lab/app.py:130>)

### S15 — Grounding worker

- [grounding_lab/engine.py](<C:/Users/nrgen/.codex/scratch/SATquery AI/grounding_lab/engine.py>) — [suppress](<C:/Users/nrgen/.codex/scratch/SATquery AI/grounding_lab/engine.py:10>), [process](<C:/Users/nrgen/.codex/scratch/SATquery AI/grounding_lab/engine.py:23>)

### S16 — Water training

- [paired_lab/train_water.py](<C:/Users/nrgen/.codex/scratch/SATquery AI/paired_lab/train_water.py>) — [read](<C:/Users/nrgen/.codex/scratch/SATquery AI/paired_lab/train_water.py:12>), [TrainSet](<C:/Users/nrgen/.codex/scratch/SATquery AI/paired_lab/train_water.py:18>), [metrics](<C:/Users/nrgen/.codex/scratch/SATquery AI/paired_lab/train_water.py:27>), [score](<C:/Users/nrgen/.codex/scratch/SATquery AI/paired_lab/train_water.py:29>)

### S17 — Current user interfaces

- [web/app.js](<C:/Users/nrgen/.codex/scratch/SATquery AI/web/app.js>)
- [web/index.html](<C:/Users/nrgen/.codex/scratch/SATquery AI/web/index.html>)
- [paired_lab/web/app.js](<C:/Users/nrgen/.codex/scratch/SATquery AI/paired_lab/web/app.js>)
- [paired_lab/web/index.html](<C:/Users/nrgen/.codex/scratch/SATquery AI/paired_lab/web/index.html>)
- [grounding_lab/web/lab.js](<C:/Users/nrgen/.codex/scratch/SATquery AI/grounding_lab/web/lab.js>)
- [grounding_lab/web/index.html](<C:/Users/nrgen/.codex/scratch/SATquery AI/grounding_lab/web/index.html>)

### S18 — Pinned paired manifest

- [paired_lab/runtime-manifest.json](<C:/Users/nrgen/.codex/scratch/SATquery AI/paired_lab/runtime-manifest.json>)

### S19 — Setup/evaluation/experiment programs

- [paired_lab/bootstrap.py](<C:/Users/nrgen/.codex/scratch/SATquery AI/paired_lab/bootstrap.py>)
- [paired_lab/setup_models.py](<C:/Users/nrgen/.codex/scratch/SATquery AI/paired_lab/setup_models.py>)
- [paired_lab/setup_sources.py](<C:/Users/nrgen/.codex/scratch/SATquery AI/paired_lab/setup_sources.py>)
- [paired_lab/evaluate.py](<C:/Users/nrgen/.codex/scratch/SATquery AI/paired_lab/evaluate.py>)
- [paired_lab/compare_candidate.py](<C:/Users/nrgen/.codex/scratch/SATquery AI/paired_lab/compare_candidate.py>)

### S20 — Test source

- [tests/test_baseball_counting.py](<C:/Users/nrgen/.codex/scratch/SATquery AI/tests/test_baseball_counting.py>)
- [tests/test_dispatch.py](<C:/Users/nrgen/.codex/scratch/SATquery AI/tests/test_dispatch.py>)
- [tests/test_evaluation.py](<C:/Users/nrgen/.codex/scratch/SATquery AI/tests/test_evaluation.py>)
- [tests/test_focused_count.py](<C:/Users/nrgen/.codex/scratch/SATquery AI/tests/test_focused_count.py>)
- [tests/test_geo.py](<C:/Users/nrgen/.codex/scratch/SATquery AI/tests/test_geo.py>)
- [tests/test_ndvi_precision.py](<C:/Users/nrgen/.codex/scratch/SATquery AI/tests/test_ndvi_precision.py>)
- [tests/test_open_vqa.py](<C:/Users/nrgen/.codex/scratch/SATquery AI/tests/test_open_vqa.py>)
- [tests/test_presence_routing.py](<C:/Users/nrgen/.codex/scratch/SATquery AI/tests/test_presence_routing.py>)
- [tests/test_routing.py](<C:/Users/nrgen/.codex/scratch/SATquery AI/tests/test_routing.py>)
- [tests/test_rural_phrasing.py](<C:/Users/nrgen/.codex/scratch/SATquery AI/tests/test_rural_phrasing.py>)
- [tests/test_stages.py](<C:/Users/nrgen/.codex/scratch/SATquery AI/tests/test_stages.py>)
- [tests/test_vqa_answers.py](<C:/Users/nrgen/.codex/scratch/SATquery AI/tests/test_vqa_answers.py>)
- [paired_lab/test_inputs.py](<C:/Users/nrgen/.codex/scratch/SATquery AI/paired_lab/test_inputs.py>)
- [paired_lab/test_controls.py](<C:/Users/nrgen/.codex/scratch/SATquery AI/paired_lab/test_controls.py>)
- [paired_lab/test_live.py](<C:/Users/nrgen/.codex/scratch/SATquery AI/paired_lab/test_live.py>)

### S21 — Deployment files

- [requirements-app.txt](<C:/Users/nrgen/.codex/scratch/SATquery AI/requirements-app.txt>)
- [start.ps1](<C:/Users/nrgen/.codex/scratch/SATquery AI/start.ps1>)
- [paired_lab/start.ps1](<C:/Users/nrgen/.codex/scratch/SATquery AI/paired_lab/start.ps1>)
- [paired_lab/launch.py](<C:/Users/nrgen/.codex/scratch/SATquery AI/paired_lab/launch.py>) — [healthy](<C:/Users/nrgen/.codex/scratch/SATquery AI/paired_lab/launch.py:5>), [main](<C:/Users/nrgen/.codex/scratch/SATquery AI/paired_lab/launch.py:8>)

### S22 — Bundled source license

- [paired_lab/mci_vendor/LICENSE.txt](<C:/Users/nrgen/.codex/scratch/SATquery AI/paired_lab/mci_vendor/LICENSE.txt>)

### E2 — Archived HTTP replay

- [paired_lab/evidence/resumed/live/01-vqa-before.json](<C:/Users/nrgen/.codex/scratch/SATquery AI/paired_lab/evidence/resumed/live/01-vqa-before.json>)
- [paired_lab/evidence/resumed/live/02-temporal.json](<C:/Users/nrgen/.codex/scratch/SATquery AI/paired_lab/evidence/resumed/live/02-temporal.json>)
- [paired_lab/evidence/resumed/live/03-water-india.json](<C:/Users/nrgen/.codex/scratch/SATquery AI/paired_lab/evidence/resumed/live/03-water-india.json>)
- [paired_lab/evidence/resumed/live/04-water-bolivia.json](<C:/Users/nrgen/.codex/scratch/SATquery AI/paired_lab/evidence/resumed/live/04-water-bolivia.json>)
- [paired_lab/evidence/resumed/live/05-scene-fusion.json](<C:/Users/nrgen/.codex/scratch/SATquery AI/paired_lab/evidence/resumed/live/05-scene-fusion.json>)
- [paired_lab/evidence/resumed/live/06-ndvi.json](<C:/Users/nrgen/.codex/scratch/SATquery AI/paired_lab/evidence/resumed/live/06-ndvi.json>)
- [paired_lab/evidence/resumed/live/07-vqa-after.json](<C:/Users/nrgen/.codex/scratch/SATquery AI/paired_lab/evidence/resumed/live/07-vqa-after.json>)
- [paired_lab/evidence/resumed/live/08-rural-urban.json](<C:/Users/nrgen/.codex/scratch/SATquery AI/paired_lab/evidence/resumed/live/08-rural-urban.json>)
- [paired_lab/evidence/resumed/live/checks.json](<C:/Users/nrgen/.codex/scratch/SATquery AI/paired_lab/evidence/resumed/live/checks.json>)
- [paired_lab/evidence/resumed/live/replay.json](<C:/Users/nrgen/.codex/scratch/SATquery AI/paired_lab/evidence/resumed/live/replay.json>)

### E3 — Water dataset/training/evaluation

- [paired_lab/evidence/resumed/water-evaluation.json](<C:/Users/nrgen/.codex/scratch/SATquery AI/paired_lab/evidence/resumed/water-evaluation.json>)
- [paired_lab/evidence/resumed/flood-data-manifest.json](<C:/Users/nrgen/.codex/scratch/SATquery AI/paired_lab/evidence/resumed/flood-data-manifest.json>)
- [paired_lab/evidence/resumed/water-gpu-memory.json](<C:/Users/nrgen/.codex/scratch/SATquery AI/paired_lab/evidence/resumed/water-gpu-memory.json>)

### E4 — MCI evaluation

- [paired_lab/evidence/resumed/mci/evaluation.json](<C:/Users/nrgen/.codex/scratch/SATquery AI/paired_lab/evidence/resumed/mci/evaluation.json>)
- [paired_lab/evidence/resumed/mci/evaluation-gpu.json](<C:/Users/nrgen/.codex/scratch/SATquery AI/paired_lab/evidence/resumed/mci/evaluation-gpu.json>)
- [paired_lab/evidence/resumed/mci/evaluation-incorrect-palette-superseded.json](<C:/Users/nrgen/.codex/scratch/SATquery AI/paired_lab/evidence/resumed/mci/evaluation-incorrect-palette-superseded.json>)

### E5 — Isolated GPU/ablation evidence

- [paired_lab/evidence/resumed/gpu-and-ablation.json](<C:/Users/nrgen/.codex/scratch/SATquery AI/paired_lab/evidence/resumed/gpu-and-ablation.json>)
- [paired_lab/evidence/resumed/water-gpu-memory.json](<C:/Users/nrgen/.codex/scratch/SATquery AI/paired_lab/evidence/resumed/water-gpu-memory.json>)

### E6 — Recorded contract/restore tests

- [paired_lab/evidence/resumed/input-controller-tests.json](<C:/Users/nrgen/.codex/scratch/SATquery AI/paired_lab/evidence/resumed/input-controller-tests.json>)
- [paired_lab/evidence/resumed/restore-test.json](<C:/Users/nrgen/.codex/scratch/SATquery AI/paired_lab/evidence/resumed/restore-test.json>)

### E7 — Historical main reliability/development

- [results/pilot-v1.json](<C:/Users/nrgen/.codex/scratch/SATquery AI/results/pilot-v1.json>)
- [ppt_handoff/raw/training_result.json](<C:/Users/nrgen/.codex/scratch/SATquery AI/ppt_handoff/raw/training_result.json>)
- [results/reliability-20260907/public-summary.json](<C:/Users/nrgen/.codex/scratch/SATquery AI/results/reliability-20260907/public-summary.json>)
- [results/reliability-20260907/ndvi-independent-summary.json](<C:/Users/nrgen/.codex/scratch/SATquery AI/results/reliability-20260907/ndvi-independent-summary.json>)
- [results/reliability-20260907/vqa/existing-adapter-fresh-summary.json](<C:/Users/nrgen/.codex/scratch/SATquery AI/results/reliability-20260907/vqa/existing-adapter-fresh-summary.json>)
- [demo run/evidence-20260908/reliability.json](<C:/Users/nrgen/.codex/scratch/SATquery AI/demo run/evidence-20260908/reliability.json>)
- [demo run/evidence-20260908/reliability-evidence.json](<C:/Users/nrgen/.codex/scratch/SATquery AI/demo run/evidence-20260908/reliability-evidence.json>)
- [evaluation.py](<C:/Users/nrgen/.codex/scratch/SATquery AI/evaluation.py>) — [score](<C:/Users/nrgen/.codex/scratch/SATquery AI/evaluation.py:21>), [development](<C:/Users/nrgen/.codex/scratch/SATquery AI/evaluation.py:35>)

### E8 — Grounding run/test evidence

- [grounding_lab/evidence/same-port-cycle/summary.json](<C:/Users/nrgen/.codex/scratch/SATquery AI/grounding_lab/evidence/same-port-cycle/summary.json>)
- [grounding_lab/evidence/same-port-cycle/lab.json](<C:/Users/nrgen/.codex/scratch/SATquery AI/grounding_lab/evidence/same-port-cycle/lab.json>)
- [grounding_lab/evidence/same-port-cycle/vqa-before.json](<C:/Users/nrgen/.codex/scratch/SATquery AI/grounding_lab/evidence/same-port-cycle/vqa-before.json>)
- [grounding_lab/evidence/same-port-cycle/vqa-after.json](<C:/Users/nrgen/.codex/scratch/SATquery AI/grounding_lab/evidence/same-port-cycle/vqa-after.json>)
- [grounding_lab/evidence/same-port-http/safety-checks.json](<C:/Users/nrgen/.codex/scratch/SATquery AI/grounding_lab/evidence/same-port-http/safety-checks.json>)
- [grounding_lab/evidence/buildings-regional/summary.json](<C:/Users/nrgen/.codex/scratch/SATquery AI/grounding_lab/evidence/buildings-regional/summary.json>)
- [grounding_lab/evidence/additional/predictions.json](<C:/Users/nrgen/.codex/scratch/SATquery AI/grounding_lab/evidence/additional/predictions.json>)

### E9 — Preserved UI verification, not repeated this audit

- [paired_lab/evidence/resumed/browser/report.json](<C:/Users/nrgen/.codex/scratch/SATquery AI/paired_lab/evidence/resumed/browser/report.json>)
- [grounding_lab/evidence/same-port-browser/verification.json](<C:/Users/nrgen/.codex/scratch/SATquery AI/grounding_lab/evidence/same-port-browser/verification.json>)

### E1 — Fresh read-only audit artifacts

- [runtime-verification.json](<C:/Users/nrgen/.codex/visualizations/2026/09/19/01a0b9f9-b20e-71a2-b139-ca9ab926b94e/satquery-audit/runtime-verification.json>)
- [recorded-measurements.csv](<C:/Users/nrgen/.codex/visualizations/2026/09/19/01a0b9f9-b20e-71a2-b139-ca9ab926b94e/satquery-audit/recorded-measurements.csv>)
- [source-evidence-inventory.json](<C:/Users/nrgen/.codex/visualizations/2026/09/19/01a0b9f9-b20e-71a2-b139-ca9ab926b94e/satquery-audit/source-evidence-inventory.json>)
- [collection-notes.json](<C:/Users/nrgen/.codex/visualizations/2026/09/19/01a0b9f9-b20e-71a2-b139-ca9ab926b94e/satquery-audit/collection-notes.json>)

Audit collection excludes generated/backed-up trees as documented by the inventory/collector. Historical reports remain historical even when their files are intact. Installed-model license metadata and asset paths are recorded in runtime-verification.json; no remote terms were substituted for the requested repository-only evidence.

Final report checks: all 154 question numbers are present exactly once; all indexed reference files existed at checking time; 108 indexed source/UI/launcher files were rehashed and matched their initial audit hashes. See [report-validation.json](<C:/Users/nrgen/.codex/visualizations/2026/09/19/01a0b9f9-b20e-71a2-b139-ca9ab926b94e/satquery-audit/report-validation.json>).
