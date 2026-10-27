# Isolated setup verification — 2026-10-19

Baseline: cafdb8055c063c5d9f283a2d71d404d0c5830a8b. Source working tree contains the reproducibility changes described here; it is not a new published release.

A new Python 3.11.16 virtual environment was created at /var/tmp/satquery-repro-20261019/venv, without system-site packages. Packages were freshly installed from requirements-test.txt and requirements-runtime.txt, with torch 2.8.0+cpu / torchvision 0.23.0+cpu. Asset, HF and Torch cache roots were explicitly isolated under the same /var/tmp directory. The existing host OS, interpreter base and network were shared; this was not a fresh OS.

| Check | Executed result |
| --- | --- |
| Baseline software suite | 96 passed |
| Isolated software suite after path/preflight changes | 102 passed |
| Dependency consistency | pip check: no broken requirements |
| Both server imports with empty asset root | Passed; optional land-cover assets no longer prevent unrelated service startup |
| Water, tracked Bolivia_103757 | Real CPU inference passed; bundled checkpoint SHA verified; three modality outputs and evidence ZIP checked |
| Temporal, tracked MCI test_000036 | Real CPU inference passed; checkpoint freshly downloaded at pinned revision and SHA verified; evidence ZIP checked |
| Land cover, tracked BEN test-27-55 | Real CPU inference passed; three newly provisioned BIFOLD models, pinned ConfigILM constants; evidence ZIP checked |
| Single SAR upload route | Blocked: tracked BEN crop has no CRS. Correctly refused. Requires an actual projected 10 m 120x120 VV/VH dB source crop; no invented metadata added |
| VQA/grounding fresh CUDA execution | Not executed in the CPU environment; requires CUDA packages/driver and model provisioning |
| Local LoRA/CDVQA clean public restoration | Manual releases remain required; not publicly restored by this run |

Water, temporal and land-cover evidence is under repository .runtime/repro-20261019/{water,temporal,land-cover}/smoke.json and evidence.zip. Installation/test/download logs are under /var/tmp/satquery-repro-20261019. These local ignored paths are retained execution evidence, not files supplied by a public clone. Reproduce them using [SETUP.md](SETUP.md).

The SAR model itself executed inside the three-modality land-cover run; that does not establish the separate single-SAR upload contract. Run `scripts/smoke_runtime.py --workflow sar-scene --sar-input /path/to/compatible.tif --out /new/output` when a suitable source is available.

Before: setup depended on eager /root/satquery manifest reads and separate package overlays. After: configurable locations, lazy optional assets, a pinned public provisioner, actionable preflight and three demonstrated CPU workflows. No learned model, benchmark result or historical archive was changed. All real runs above reuse development examples and establish executability only, not new accuracy, general runtime or official-sensor validity.

Follow-up: the original georeferenced SAR crop was recovered byte-for-byte from paired_lab/evidence/compliance-20260926/sar-live-evidence.zip. Its recorded preparation used explicit nearest-neighbour reprojection to EPSG:32720 at 10 m; no metadata was invented in this pass. Real single-SAR inference then passed in the fresh environment with newly downloaded BIFOLD weights. Evidence: .runtime/repro-20261019/sar-verified. This supersedes the missing-compatible-input blocker above, while preserving the refusal of the non-georeferenced BEN fixture. Four CPU workflows are now demonstrated.

After CDVQA integration and targeted routing corrections, the full suite passed 113 tests. CDVQA used the explicitly configured existing maintainer release and encoder, not a public restoration claim; see IMPROVEMENT_AUDIT.md. GPU and visual browser acceptance remain open.


## Step 1 follow-up - 2026-10-20

The bounded CDVQA browser upload, refusal, inference, image-view and evidence-download checks now pass on the documented port 8767. This supersedes only the prior browser-unverified status above. See [closure evidence](STEP1_VERIFICATION_20261020.md) and [frozen evaluation protocol](EVALUATION_PROTOCOL_V1.md). No model accuracy claim changed; fresh acceptance data, full GPU restoration and other requirement gaps remain open.
