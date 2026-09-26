# Setup and reproducibility

## Verified scope

The tested deployment is Linux under WSL with Python 3.11, an existing `/root/satquery` asset tree and NVIDIA CUDA for VQA/grounding. The launcher is checkout-relative; asset provisioning is not yet a fully portable clone/install/run process.

## Software checks without models

From the repository root, create a Python 3.11 virtual environment, install `requirements-test.txt`, then run `python -m unittest discover -s tests -v`. The GitHub workflow runs the same command. Software tests include stubs/mocks and synthetic arrays; passing them does not establish model quality.

## Inference environment

`requirements-inference-tested.txt` reproduces the package/version inventory from the frozen benchmark baseline; its CUDA wheel index is explicit. `requirements-paired.txt` records the isolated dependencies from the paired runtime manifest. These are recorded constraints, not a claim that a clean installation has been demonstrated. `requirements-app.txt` is only the historical API overlay, not the complete environment.

In an isolated Linux Python 3.11 environment:

```sh
python -m pip install -r requirements-inference-tested.txt
python -m pip install -r requirements-paired.txt
```

Do not replace a working environment before validating a new one. Driver compatibility, package-index availability and grounding dependencies must be checked separately.

## External assets and remaining gaps

| Component | Required assets / restoration evidence |
| --- | --- |
| VQA | Hugging Face remote-sensing Qwen weights and cache; local LoRA adapter under `/root/satquery/experiments/lora-pilot-v1/adapter`; adapter restoration is not automated |
| MCI | `/root/satquery/paired-lab/mci-model/manifest.json` and checkpoint; revision/hash in `paired_lab/runtime-manifest.json`; vendored model source is in `mci_vendor/` |
| Land cover | Three BIFOLD snapshots, ConfigILM source/constants, `models.json`, isolated `deps/`; pinned revisions in runtime manifest |
| Water | `paired_lab/checkpoints/water-v1.pt`; manifest SHA256 must match |
| Grounding | `/root/satquery/grounding-lab/models.json` and referenced DINO/SAM assets; separate provisioning remains necessary |
| Demonstration/evaluation | Sample catalogues, scenes and labels under the runtime tree; not all supplied by a clone |

`paired_lab/bootstrap.py` restores pinned paired assets but also downloads the **legacy ChangeFormer** model. It is not a complete application installer. `setup_sources.py` and `setup_models.py` are historical construction scripts: do not treat them as reproducible current setup commands.

Some active modules still use absolute `/root/satquery` asset/data paths, and manifests contain resolved cache paths. A differently located asset tree requires a separate configuration migration. The `-Python` launcher option changes the interpreter, not those paths.

## Start a provisioned runtime

PowerShell: `./start.ps1 -Distribution Ubuntu -Python /root/satquery/.venv/bin/python`; add `-Check` to probe both services without launching them. Linux: `python paired_lab/launch.py`.

Services bind to loopback: 8765 single-image/grounding, 8767 unified interface. Launcher logs default to repository `.runtime/logs/`; override with `SATQUERY_LOG_DIR`. No weights are downloaded by the launcher. Saved known artifact URLs can survive restart; the in-memory job index does not.

## Release gate

Clean-machine full inference, asset restoration, commercial licensing review, authentication and multi-user isolation remain open. Do not describe this repository as turnkey SaaS or certified for official sensors.
