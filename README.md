<p align="center"><img src="web/art/logo.png" width="76" height="76" alt="SatQuery's Saturn emblem"></p>

<h1 align="center">SatQuery AI</h1>

<p align="center"><strong>Ask about Earth. Inspect the answer.</strong></p>

<p align="center">
  <a href="docs/REVIEWER_GUIDE.md">Product walkthrough</a> ·
  <a href="#measured-evidence">Measured evidence</a> ·
  <a href="docs/SETUP.md">Setup</a> ·
  <a href="docs/ARCHITECTURE.md">Architecture</a>
</p>

SatQuery helps remote-sensing researchers and analysts ask questions about **prepared satellite imagery**, compare observed dates, and inspect the evidence behind a result. It brings input checks, task selection, specialist execution, and review into one local interface.

**Status:** local research prototype for **SIH26167**. Working analytical paths and separate experiments are described below. Model assets require additional provisioning. Documentation reviewed **27 October 2026**; measurements retain their original evaluation dates.

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/images/workspace-water-dark.png">
  <source media="(prefers-color-scheme: light)" srcset="docs/images/workspace-water-light.png">
  <img src="docs/images/workspace-water-dark.png" alt="Actual SatQuery workspace: water overlay, three sensor-path masks, pixel counts and result for the supplied India example" width="1440">
</picture>

*Actual product screen, captured 27 October 2026 from a new run of the supplied India example. The 49.56% shown is predicted water coverage in this crop, not accuracy. [Walk through this example](docs/REVIEWER_GUIDE.md#1-map-water-and-inspect-three-pathways) · [Capture provenance](docs/images/README.md).*

## JAI 2026 submission, attribution and AI disclosure

**The Road Home** investigates existing saved Syapru Besi, Nepal observations: separate water-change and possible debris/surface-change candidates, mapped infrastructure intersections and historical terrain context. This is a local research prototype, not an operational warning, damage, evacuation or prediction service. [Submission index](docs/jai/submission/SUBMISSION_INDEX.md) · [Presentation](docs/jai/submission/SATQuery_The_Road_Home_JAI2026.pptx) · [Demo script](docs/jai/DEMO_ROAD_HOME.md) · [Final implementation and limits](docs/jai/ROAD_HOME_DAY2_60MIN_RECEIPT.md).

**Setup and execution:** use [Python 3.11 / WSL setup](docs/SETUP.md), [model/data provisioning](docs/ASSETS.md), and [extension startup](jai_extension/README.md). The extension uses `python start_jai.py` with the documented SATQuery/Flood Lab roots and loopback port 8768. Existing data and model assets must be provisioned; a clone alone is not a complete inference install. Run `python -m unittest discover -s tests`, `node tests/test_road_home_ui.cjs`, and `python scripts/verify_road_home.py` in the provisioned environment. The final RGB/layout rendered browser check remains incomplete; software and HTTP checks are not new scientific accuracy.

**Third-party libraries:** Python, NumPy, Rasterio/GDAL, Pillow, FastAPI, Pydantic, Requests, Uvicorn, PyTorch, torchvision, Transformers, timm, einops, SciPy, OpenCV and Plotly power the application; Flood Lab also uses Shapely and NetworkX. Exact pinned dependencies and licenses/provenance are retained in [runtime requirements](requirements-runtime.txt), [test requirements](requirements-test.txt), [asset inventory](docs/RUNTIME_ASSETS.json), [Plotly attribution](docs/jai/THIRD_PARTY.json) and the prior projects' notices. This short submission deck was exported using OpenAI Artifact Tool; no new application dependency was introduced.

**Models and datasets:** existing specialists include Qwen2-VL, MCI, BIFOLD/ResNet50, WaterUNet, GroundingDINO/SAM and the experimental CDVQA model; attribution, checkpoint revisions and license limitations are in [assets](docs/ASSETS.md) and [runtime inventory](docs/RUNTIME_ASSETS.json). Existing benchmark data include LEVIR-MCI/LEVIR-derived pairs, BigEarthNet v2 and Sen1Floods11. Nepal uses retained Copernicus Sentinel-1, Sentinel-2 L2A, Copernicus GLO-90 DSM and historical OpenStreetMap data. [Nepal data sources and terms](docs/jai/DATA_SOURCES.md) and individual manifests retain dates, hashes and attribution. Dataset/model licenses are separate from the code MIT license. Do not infer unrestricted redistribution rights. Nepal debris is a fixed, unvalidated proxy, not a trained classifier; EMSR927 checking evidence is not debris accuracy.

**AI assistance:** OpenAI Codex assisted repository inspection, implementation, debugging, tests, documentation and this submission package. A separate Codex UI chat implemented the Scientific Noir interface; supplied presentation artwork is illustrative and is not satellite evidence. AI-generated work was checked against actual source artifacts and tests. The Nepal investigation itself uses deterministic saved-evidence tools with no LLM invocation; the other preserved specialist routes use their named existing models. No new model training or judge-label tuning was performed in this event integration.

**Prior work versus JAI contributions:** prior SATQuery specialists, research/benchmarks, Flood Lab calculations, models and saved Nepal observations predate this hackathon integration. New JAI work adds the protected hash-verifying bridge, real terrain context, deterministic source/trace investigation, private external-data intake and independent evaluation, the Nepal narrative, verified RGB context and independent overlays. [Baseline provenance](docs/jai/BASELINE_PROVENANCE.md) and [authentic incremental history](https://github.com/Yoriichi-GOD/SATquery-AI/commits/main/) preserve that distinction. Organizer clearance for extending prior work under Open Innovation was reported directly by the participant; written organizer confirmation and teammate collaborator access still require the team's own records. No written approval or collaborator membership is invented here.

**Immutable Day 1:** `day1-final` remains at `f3945347cf0f0a4581aa1480c8fa1501a25da4b4` (annotated tag object `a08d2706397d359edb060993ee3a14374b3d136f`). No history rewrite, backdating or tag movement is used. [Security scan receipt](docs/jai/submission/SECURITY_SCAN.json) records the actual scan scope; it is not a security certification.

## JAI 2026 — The Road Home

The Nepal demonstration connects separate saved water and possible debris-change evidence, infrastructure intersections and real terrain. [Demo flow](docs/jai/DEMO_ROAD_HOME.md) · [Implementation receipt and verification limits](docs/jai/ROAD_HOME_DAY2_60MIN_RECEIPT.md) · [UI/API handoff](docs/jai/ROAD_HOME_UI_HANDOFF.md). Existing scientific results remain separate from this integration.

## From an observation to a reviewable result

1. **Supply prepared imagery.** Upload one image or a compatible pair, or choose a supplied example. Declare the required modality and dates.
2. **Ask a supported question.** Input checks and the controller select an eligible specialist. Unsupported or ambiguous requests receive requirements or suggestions.
3. **Inspect the result.** Review the final output, switch between inputs and processing views, then inspect calculations, limitations, and downloadable evidence.

Sensor calibration, quality masks, and spatial correspondence depend on the workflow. Matching metadata alone does not prove physical co-registration. See [input contracts](docs/ARCHITECTURE.md#input-contracts).

## What you can run

These paths are connected in the main interface once their assets are provisioned:

| Input | Supported analysis | Execution |
| --- | --- | --- |
| One optical image | Visual questions, descriptions, estimated counts | Qwen2-VL; local CUDA |
| Calibrated red/NIR GeoTIFF | NDVI and thresholded pixel coverage | CPU numerical processing |
| Two prepared RGB dates | Road/building change masks and a separate caption | MCI; CPU |
| Compatible optical/SAR pair | SAR-only, optical-only, and joint water masks | WaterUNet; CPU |
| Compatible optical/SAR pair | Scene-level land-cover labels from three pathways | BIFOLD ResNet50; CPU |

**Experimental browser paths:** category grounding, single Sentinel-1 scene classification, and paired Sentinel-2 NDVI/NDWI comparison. See [capabilities and boundaries](docs/ARCHITECTURE.md#capability-status).

**Experimental CDVQA mode:** answer one of 300 supported change-question templates on an aligned, ordered RGB pair through the browser or [CLI](scripts/predict_cdvqa.py). Alignment declaration and input checks are required. The browser integration does not change the historical benchmark scores. [Report](docs/CDVQA_FINAL_REPORT.md) · [Integration review](docs/PENDING_RELEASE_REVIEW_20261027.md).

## Measured evidence

Each task has its own metric and scope. These results do not form an overall SatQuery accuracy score.

| Evaluation | Recorded result | Denominator and scope |
| --- | --- | --- |
| [CDVQA Test-1](docs/CDVQA_FINAL_REPORT.md) | **69.90%** answer accuracy | 39,686 questions / 968 pairs; experimental specialist, 28 Sep 2026 |
| [CDVQA Test-2](docs/CDVQA_FINAL_REPORT.md) | **65.05%** answer accuracy | 31,036 questions / the **same 968 pairs**, 28 Sep 2026 |
| [Water mapping](BENCHMARK_REPORT.md#water-retain-the-three-pathways) | SAR **63.64%** · optical **83.90%** · joint **82.64%** IoU | 90 Sen1Floods11 test chips; previously evaluated split, 21 Sep 2026 |
| [Road/building change](BENCHMARK_REPORT.md#temporal-segmentation-and-captions-are-separate) | Road **80.99%** · building **81.69%** IoU | 100 selected LEVIR-MCI pairs: 50 changed / 50 unchanged; inherited checkpoint, 21 Sep 2026 |

CDVQA splits overlap in questions and share imagery; **do not pool them**. Question-only controls scored 68.06% / 63.24%. Twelve pairs were previously inspected; [controls and exclusion analysis](docs/CDVQA_FINAL_REPORT.md#previously-inspected-pairs-excluded) disclose that exposure. Joint water fusion did not exceed optical-only on this test set.

[Benchmark findings](BENCHMARK_REPORT.md) · [Numerical tables](paired_lab/evidence/benchmark-20260921/metrics.csv) · [CDVQA predictions](paired_lab/evidence/cdvqa-trained-20260928/) · [Claim register](docs/CLAIM_REGISTER.md)

<details>
<summary><strong>See the in-app Evidence page</strong> — overview and detailed evaluations</summary>

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/images/evidence-overview-dark.png">
  <source media="(prefers-color-scheme: light)" srcset="docs/images/evidence-overview-light.png">
  <img src="docs/images/evidence-overview-dark.png" alt="Actual Evidence page showing CDVQA question counts and separate SAR, optical and joint water IoU cards" width="1440">
</picture>

This capture predates CDVQA browser integration. It displays saved evaluations; opening the page does not rerun the models. [Reviewer guide](docs/REVIEWER_GUIDE.md) · [Screenshot provenance](docs/images/README.md).

</details>

## Run and verify

**Start with [setup and required assets](docs/SETUP.md).** The tested target is Linux/WSL with Python 3.11. A clone does not include every asset needed for full inference.

For software checks in an activated **Python 3.11** environment:

```sh
python -m pip install -r requirements-test.txt
python scripts/check_publication.py
python -m unittest discover -s tests -v
python scripts/test_measure_landmarks.py -v
python scripts/test_quality_readiness.py -v
```

[GitHub Actions](https://github.com/Yoriichi-GOD/SATquery-AI/actions/workflows/software-tests.yml) runs these checks. Tests include mocks and synthetic inputs. Publication checks cover newly committed files and recompute saved CDVQA metrics; they do not run model inference or scan all uncommitted files.

For a provisioned runtime, follow the [launch instructions](docs/SETUP.md#start-a-provisioned-runtime) and open **http://localhost:8767**. This is a local address, not a hosted demo.

## Explore the project

| I want to… | Open |
| --- | --- |
| See the product and strongest examples | [Reviewer walkthrough](docs/REVIEWER_GUIDE.md) |
| Understand services and supported inputs | [Architecture and capabilities](docs/ARCHITECTURE.md) |
| Install dependencies and identify missing assets | [Setup](docs/SETUP.md) |
| Find active code and historical material | [Repository map](REPOSITORY_CONTENTS.md) |
| Audit measured results | [Benchmark report](BENCHMARK_REPORT.md), [CDVQA report](docs/CDVQA_FINAL_REPORT.md), [claim register](docs/CLAIM_REGISTER.md) |
| Check official-product work | [Official sample report](docs/OFFICIAL_SAMPLE_FINAL_REPORT.md) |
| Find presentation material and remaining gates | [Presentation findings](PPT_FINDINGS.md), [priority closure](docs/PRIORITY_CLOSURE.md) |
| Understand omitted assets | [Evidence storage](docs/EVIDENCE_STORAGE.md) |
| Check recent improvements and verification | [Implementation review](docs/PENDING_RELEASE_REVIEW_20261027.md), [presentation verification](docs/PRESENTATION_VERIFICATION.md) |

## Current boundaries

- **Expert review remains necessary.** Descriptions and counts can be wrong. Masks and scores are predictions. Index thresholds do not establish vegetation health or flood extent.
- **Official checks have limited scope.** Downloaded samples supported Cartosat ingestion/description execution and EOS-04 numerical calibration checks. Paired Cartosat/RISAT semantic accuracy remains unvalidated. [Exact scope](docs/OFFICIAL_SAMPLE_FINAL_REPORT.md).
- **Operational readiness is open.** Authentication, multi-user isolation, full fresh-machine inference reproduction, and deployment scalability are not established. Forecasting is outside scope.

Historical evidence and deliverables retain their existing paths. The [MIT license](LICENSE) covers repository code; model and dataset terms require their own review.

## JAI 2026 Flood & Terrain extension

Verified JAI work is merged into `main`; the original event branch and immutable Day 1 tag preserve the progression. The optional [Terrain & flood workspace](docs/jai/UNIFIED_WORKSPACE.md) combines genuine saved Flood Lab evidence, terrain and adjacent questions in the native black interface, with sources and tool traces folded until needed. [Run the extension](jai_extension/README.md). [Verification and open failures](docs/jai/REGRESSION.md) distinguish new software checks from historical scientific results. Real public Copernicus GLO-90 terrain, numerical slope, grid-mapped water markers, cross-sections and a [source-based investigation workflow](docs/jai/ALIGNMENT_AND_INVESTIGATION.md) are connected.

## External dataset readiness

The [external dataset workflow](docs/external/README.md) adds private streamed intake, full TIFF compatibility reports, bounded specialist execution and independent evaluation/export verification. Open the optional local extension at **http://127.0.0.1:8768/#datasets**. Large-file inspection is separate from the models' small prepared-input limits. Missing compatible labels produce no accuracy score. The [Day 2 closure record](docs/external/day2/CLOSURE.md) separates genuine adapter runs, synthetic software checks and open scientific limits.
