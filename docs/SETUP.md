# Setup and reproducibility

Verified target: Linux/WSL, Python 3.11. Use a new environment and explicit asset/cache roots. Keep the working installation intact. See the [asset inventory](ASSETS.md) for public downloads and manual releases.

## Software first

From the repository root:

```sh
python3.11 -m venv .venv-repro
. .venv-repro/bin/activate
python -m pip install -r requirements-test.txt
python -m unittest discover -s tests -v
python scripts/check_publication.py
```

Publication checks compare committed history (HEAD^ to HEAD, or CI_BASE_SHA) and saved metrics, not all uncommitted files or GPU inference. Software tests include mocks and synthetic arrays; passing them does not prove model quality.

## Fresh CPU inference

```sh
export SATQUERY_ASSET_ROOT="$HOME/satquery-assets"
export HF_HOME="$SATQUERY_ASSET_ROOT/hf-cache"
export TORCH_HOME="$SATQUERY_ASSET_ROOT/torch-cache"
python -m pip install torch==2.8.0 torchvision==0.23.0 --index-url https://download.pytorch.org/whl/cpu
python -m pip install -r requirements-runtime.txt
python -m pip check
python scripts/preflight.py --workflow water --verify-hashes
python scripts/smoke_runtime.py --workflow water --out .runtime/water-smoke
python scripts/provision_assets.py --workflow temporal
python scripts/smoke_runtime.py --workflow temporal --out .runtime/temporal-smoke
python scripts/provision_assets.py --workflow land-cover
python scripts/smoke_runtime.py --workflow land-cover --out .runtime/land-cover-smoke
python scripts/preflight.py --workflow sar-scene --verify-hashes
```

Each output must be a new directory. Smoke outputs include originals, hashes, predictions, environment metadata and a checked evidence ZIP. These are development checks, not accuracy benchmarks. Downloads need internet and several GB of disk space.

requirements-runtime.txt describes the active environment. requirements-inference-tested.txt and requirements-paired.txt preserve older benchmark inventories; do not overlay them on this environment.

## GPU and manual assets

VQA/grounding serving requires CUDA. Install compatible CUDA builds of pinned torch/torchvision in a separate environment, then requirements-runtime.txt. Provision vqa or grounding, then run `python scripts/preflight.py --workflow vqa --check-cuda` (or grounding). Driver compatibility is machine-specific; CPU smoke success does not certify GPU workflows.

Rural/urban LoRA and CDVQA releases require maintainer provision; see [ASSETS.md](ASSETS.md). `python scripts/preflight.py --workflow all --verify-hashes --check-cuda --json` deliberately fails if a selected asset/dependency is missing. Select one workflow for a partial install. Presence/provenance/hash checks are not execution; run real inputs before claiming deployment readiness.

## Start the interface

With the environment and asset variables above: `python paired_lab/launch.py`.

Windows PowerShell:

```powershell
./start.ps1 -Distribution Ubuntu -Python /absolute/path/to/venv/bin/python -AssetRoot /absolute/path/to/assets
```

Add -Check to probe without launching. Loopback ports: 8765 single-image/grounding, 8767 unified. Logs default to .runtime/logs (SATQUERY_LOG_DIR overrides). Startup does not require every optional model; invoking a missing specialist fails. Saved artifact URLs can survive restart; the in-memory job index does not.

## Verification limits

See [executed verification](REPRODUCIBILITY_VERIFICATION.md). Isolated environment verification on an existing WSL host is not a new OS or independent researcher replication. GPU restoration, manual release availability, commercial licensing, authentication and multi-user isolation remain separate gates.
