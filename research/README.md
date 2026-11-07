# Scientific development workspace

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
