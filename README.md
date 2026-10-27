# SatQuery AI

Query-driven analysis of prepared Earth-observation imagery, with input compatibility checks and inspectable evidence. Repository guide reviewed 18 October 2026; benchmark results retain their recorded evaluation dates and scopes.

Start with [measured results](#evidence), [setup and required assets](docs/SETUP.md), or the [code and evidence map](REPOSITORY_CONTENTS.md).

## Current workflows

| Input / task | Active implementation | Boundary |
| --- | --- | --- |
| Single image: VQA, descriptions and bounded visual counts | Qwen2-VL remote-sensing model; query-specific policies | Descriptions can omit or invent details; counts are model estimates |
| Calibrated red/NIR GeoTIFF: NDVI | CPU numerical processing | Surface reflectance required; thresholded pixels are not vegetation health |
| Two registered RGB dates: road/building change | MCI masks and caption | Prepared 256 × 256 crops; caption and mask evidence are separate |
| Compatible optical/SAR: water | WaterUNet SAR-only, optical-only, joint | Sentinel-1/2 training contract; single-date water is not automatically flood extent |
| Compatible optical/SAR: land-cover classes | BIFOLD ResNet50 | Scene labels, not spatial segmentation |
| Single image: category grounding | Grounding DINO + SAM, experimental | Supported categories; not unrestricted referring-expression accuracy |
| Two calibrated Sentinel-2 dates: NDVI / NDWI comparison | CPU spectral comparison, experimental | Common valid grid and quality mask; no general urban-expansion measurement |
| Two aligned RGB dates: CDVQA change-question answering | Experimental [CLI and explicit RGB-pair mode](docs/IMPROVEMENT_AUDIT.md#cdvqa-integration-evidence) | Exact trained templates; backend integration verified; browser interaction check remains open |

The unified interface at `http://localhost:8767` selects eligible specialists from the query and input metadata. It refuses unsupported requests rather than inventing a fallback. Prepared examples and user uploads are separate. Forecasting is outside scope.

## Evidence

On the frozen 90-chip Sen1Floods11 test replay: **SAR IoU 63.64% · optical 83.90% · joint 82.64%**. Fusion is not assumed to outperform each modality.

On a selected 100-pair LEVIR-MCI test subset (50 changed / 50 unchanged): **road IoU 80.99% · building IoU 81.69%**. These are bounded task results, not overall system accuracy or official-sensor validation.

On the official CDVQA Test-1 / Test-2 splits, the experimental specialist recorded **69.90% / 65.05% overall answer accuracy** on 39,686 / 31,036 questions, respectively (28 September 2026). Both splits use the same 968 image pairs and overlap in questions; do not pool them. Question-only controls scored 68.06% / 63.24%. Twelve pairs had previously been inspected; see the [full report, controls and exclusion analysis](docs/CDVQA_FINAL_REPORT.md) and [saved numerical summary](paired_lab/evidence/cdvqa-trained-20260928/final-test-summary.json). These are saved benchmark results, not a fresh model evaluation.

- [Benchmark methodology and findings](BENCHMARK_REPORT.md)
- [Public VQA diagnostic: why whole-response exact match is not semantic accuracy](paired_lab/evidence/public-benchmarks-20260927/README.md)
- [Claim register](docs/CLAIM_REGISTER.md) and [priority closure](docs/PRIORITY_CLOSURE.md)
- [Presentation findings](PPT_FINDINGS.md)
- [Numerical tables](paired_lab/evidence/benchmark-20260921/metrics.csv)
- [Description review](paired_lab/evidence/benchmark-20260921/DESCRIPTION_REVIEW.md)

## Run and verify

See [setup and remaining reproduction requirements](docs/SETUP.md) before installing model assets. A fresh clone does **not** contain every runtime asset.

Software-only checks (Python 3.11, no checkpoint download):

```sh
python -m venv .venv-tests
# Activate the environment using your shell's activation command.
python -m pip install -r requirements-test.txt
python scripts/check_publication.py
python -m unittest discover -s tests -v
```

These are the checks used by [software CI](.github/workflows/software-tests.yml). The publication checker recomputes CDVQA metrics from saved predictions and checks newly committed files; it does not scan uncommitted files. Tests use mocks and synthetic inputs and do not establish model accuracy. CI retains verification logs as run artifacts.

For an already provisioned WSL runtime, run `./start.ps1` from PowerShell. The script derives the checkout path and accepts `-Python` and `-Distribution`; it does not install models. Native Linux: `python paired_lab/launch.py` in the provisioned environment.

## Repository map and scope

[Repository contents](REPOSITORY_CONTENTS.md) identifies active code, current evidence and historical snapshots. Historical archives are retained for provenance, not deployment.

[Evidence storage](docs/EVIDENCE_STORAGE.md) explains which assets remain outside Git; [claim boundaries](docs/CLAIM_REGISTER.md) separate measured results from unsupported extrapolations.

This is a local research prototype. Authentication, multi-user isolation, deployment scalability and official Cartosat/RISAT model accuracy are not established. Review third-party model and dataset terms before redistribution or commercial use.
