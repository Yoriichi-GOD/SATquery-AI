# Setup and reproducibility

## Verified scope

The tested deployment is Linux under WSL with Python 3.11, an existing `/root/satquery` asset tree and NVIDIA CUDA for VQA/grounding. The launcher is checkout-relative; asset provisioning is not yet a fully portable clone/install/run process.

## Software checks without models

From the repository root, create and activate a Python 3.11 virtual environment, then run:

```sh
python -m pip install -r requirements-test.txt
python scripts/check_publication.py
python -m unittest discover -s tests -v
```

The [GitHub workflow](../.github/workflows/software-tests.yml) runs both checks and uploads their logs. Keep Git history available: the publication checker defaults to comparing `HEAD^` with `HEAD`; CI supplies its push/PR base through `CI_BASE_SHA`. It checks newly committed files and recomputes saved CDVQA metrics, not uncommitted-file hygiene or GPU inference. Software tests include stubs/mocks and synthetic arrays; passing them does not establish model quality.

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
| Experimental CDVQA CLI | Trained checkpoint and release manifest under `/root/satquery/cdvqa/`, plus the pretrained ResNet50 encoder; [reproduction details and explicit-path example](CDVQA_FINAL_REPORT.md#reproduction-and-saved-assets). Separate from browser serving |

`paired_lab/bootstrap.py` restores pinned paired assets but also downloads the **legacy ChangeFormer** model. It is not a complete application installer. `setup_sources.py` and `setup_models.py` are historical construction scripts: do not treat them as reproducible current setup commands.

Some active modules still use absolute `/root/satquery` asset/data paths, and manifests contain resolved cache paths. A differently located asset tree requires a separate configuration migration. The `-Python` launcher option changes the interpreter, not those paths.

## Start a provisioned runtime

From an activated, provisioned Python environment in the Linux/WSL repository directory:

```sh
python paired_lab/launch.py --check
python paired_lab/launch.py
```

`--check` only probes the two services; it succeeds when both are already running. The second command starts missing services and stays running until Ctrl+C. These commands do not provision model assets.

The existing PowerShell wrapper accepts `./start.ps1 -Distribution Ubuntu -Python /root/satquery/.venv/bin/python` and `-Check`, but the 27 October presentation check hit a `wslpath` translation failure from PowerShell in a Windows checkout. Use the Linux/WSL commands above if that occurs. The wrapper is retained unchanged; its portability is not established by this documentation pass.

Services bind to loopback: 8765 single-image/grounding, 8767 unified interface. Launcher logs default to repository `.runtime/logs/`; override with `SATQUERY_LOG_DIR`. No weights are downloaded by the launcher. Saved known artifact URLs can survive restart; the in-memory job index does not.

## Release gate

Clean-machine full inference, asset restoration, commercial licensing review, authentication and multi-user isolation remain open. Do not describe this repository as turnkey SaaS or certified for official sensors.

## Byte-exact evidence on Windows

Frozen text evidence is hashed as bytes. A Windows checkout with automatic CRLF conversion can fail the development-manifest hash check when read from WSL, even though the stored Git blob is unchanged. Use a native Linux checkout with LF files for the documented Linux checks. For a separate new clone, `git -c core.autocrlf=false clone https://github.com/Yoriichi-GOD/SATquery-AI.git satquery` keeps the recorded text bytes. Do not rewrite a frozen manifest or regenerate outputs to hide a line-ending mismatch. This does not change the need to provision runtime assets.
