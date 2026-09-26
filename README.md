# SatQuery AI

Query-driven analysis of prepared Earth-observation imagery, with input compatibility checks and inspectable evidence. Current repository guide: 26 September 2026. Scientific results below retain their 21 September evaluation scope.

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

The unified interface at `http://localhost:8767` selects eligible specialists from the query and input metadata. It refuses unsupported requests rather than inventing a fallback. Prepared examples and user uploads are separate. Forecasting is outside scope.

## Evidence

On the frozen 90-chip Sen1Floods11 test replay: **SAR IoU 63.64% · optical 83.90% · joint 82.64%**. Fusion is not assumed to outperform each modality.

On a selected 100-pair LEVIR-MCI test subset (50 changed / 50 unchanged): **road IoU 80.99% · building IoU 81.69%**. These are bounded task results, not overall system accuracy or official-sensor validation.

- [Benchmark methodology and findings](BENCHMARK_REPORT.md)
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
python -m unittest discover -s tests -v
```

For an already provisioned WSL runtime, run `./start.ps1` from PowerShell. The script derives the checkout path and accepts `-Python` and `-Distribution`; it does not install models. Native Linux: `python paired_lab/launch.py` in the provisioned environment.

## Repository map and scope

[Repository contents](REPOSITORY_CONTENTS.md) identifies active code, current evidence and historical snapshots. Historical archives are retained for provenance, not deployment.

This is a local research prototype. Authentication, multi-user isolation, deployment scalability and official Cartosat/RISAT model accuracy are not established. Review third-party model and dataset terms before redistribution or commercial use.
