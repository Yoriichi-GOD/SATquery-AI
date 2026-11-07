# Reuse audit

Source: C:/Users/nrgen/.codex/scratch/SATquery AI, commit 4045ce362c9df827e537f6d51f7ebf8b4c3db354. Working tree clean when inspected.

| Component | Evidence | Decision |
|---|---|---|
| paired_lab/flood.py | WaterUNet; 17-channel conditioned input; 2 SAR dB and 13 L1C optical bands; 0.5 threshold | Candidate reusable water-only model |
| water-v1.pt | 7,879,873 bytes present locally | Do not download new model |
| prepare | Intersects both sensor validity masks | Adapt per-mode validity in isolated code |
| segment | CPU; max 512; dimensions multiple of 16 | Do not copy wrapper unchanged for event imagery |
| LICENSE | MIT, copyright 2026 YoriichiGOD | Preserve notice in any copied code |
| sample Pakistan_849790 | Real Sen1Floods11 same-date 2017-06-28 SAR/optical, official-test sample already inspected previously | Development smoke only; not Nepal/pre-post flood proof |
| Existing scores | Previously measured water task | No transfer of numerical claims to this experiment |

No original SatQuery files changed. Keep separate inputs, runs, environment, service and history.
