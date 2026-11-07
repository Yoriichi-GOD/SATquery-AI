# Scientific development workspace

Latest: [validation closure and external test](results/validation-closure-20261107/REPORT.md),
[reproduction](../docs/research/VALIDATION_CLOSURE_20261107.md).
This adds native official Delhi drainage, genuine2m post-event Nepal terrain and a sealed six-event
external water-component test. It retains failed quality gates and the negative terrain-filter result.

Previous: [four-case acquired-data report](results/case-campaign-20261107/REPORT.md),
[actual measurement table](results/case-campaign-20261107/MEASUREMENTS.csv),
[figures](results/case-campaign-20261107/figures/) and
[reproduction/startup instructions](../docs/research/CASE_CAMPAIGN_20261107.md).
The new campaign acquired37 native raster windows and processed Nepal, historical Kedarnath,
Varanasi and southern Sangam Vihar. Private local source windows are in
`research/datasets/local/campaign-20261107/`; their portable checksum manifest is in the report folder.

This branch adds terrain-conditioned, inspectable exposure screening to the existing SATquery system.
**The scientific mission remains partial: independent exposure validation is not established.**

- [Measured implementation/evaluation report](results/terrain-exposure-20261105/REPORT.md)
- [Machine-readable completion gates](results/terrain-exposure-20261105/completion.json)
- [Portable commands and setup](../docs/research/REPRODUCIBILITY.md)
- [Graph/API contract and scientific limits](../docs/research/TERRAIN_EXPOSURE_API.md)
- [Reference compatibility and method sources](../docs/research/SOURCES_AND_METHODS.md)
- [Dataset acquisition inventory](datasets/registry.json)

| Directory | Contents |
|---|---|
| `terrain_exposure/` | Metric contracts, conditioning/D8/HAND, typed graph, exports, Nepal replay, synthetic example |
| `registration/` | Mask-aware optical diagnostic; no automatic source correction |
| `datasets/` | Source records, bounded resumable downloads and STAC discovery |
| `cases/` | Nepal, Varanasi and Sangam Vihar configurations; urban processing/ingestion |
| `experiments/` | Frozen reference-road screening and scripted analyst tasks |
| `evaluation/` | Metrics, spatial resampling and figures generated from actual results |
| `results/terrain-exposure-20261105/` | Small derived review receipts, actual CSV and PNG/PDF/SVG figures |
| `results/local-20261105/` | Git-ignored complete local graph/raster/reference-unit exports |

New source lives in this isolated worktree. Older private research in the original checkout was not
copied, modified or published. Existing benchmark records and model weights remain separate.
No synthetic fixture is a satellite accuracy result; no reference grade is silently relabelled as exposure.
