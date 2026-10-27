# Runtime assets

[RUNTIME_ASSETS.json](RUNTIME_ASSETS.json) records each active model's source, exact revision, known SHA256, required files, access and license qualifications. Null hashes mean no whole-asset checksum is asserted. Snapshot revisions and shard checks are not full byte verification or inference.

| Workflow | Assets/configuration | Acquisition |
| --- | --- | --- |
| VQA | AdaptLLM Qwen2-VL snapshot, tokenizer/processor | `python scripts/provision_assets.py --workflow vqa` |
| Rural/urban | VQA plus lora-pilot-v1 adapter | Maintainer supplies adapter_config.json and adapter_model.safetensors; no public release URL established |
| Grounding | DINO tiny, SAM base, grounding-lab/models.json | Provision `grounding`; serving requires CUDA |
| Temporal | MCI checkpoint, paired-lab/mci-model/manifest.json; vendored MCI source/vocabulary | Provision `temporal` |
| Optical/SAR land cover | Three BIFOLD snapshots, paired-lab/models.json, pinned ConfigILM normalization source | Provision `land-cover` |
| Single SAR | BIFOLD S1 and ConfigILM constants | Provision `sar-scene` |
| Water | Tracked paired_lab/checkpoints/water-v1.pt | Provision `water` verifies bundled hash |
| NDVI / spectral dates | Calibrated, labelled user rasters and quality metadata | No learned weights; preflight `numerical` |
| CDVQA | Maintainer paired-best.pt/release.json, public ResNet50 encoder | Provision `cdvqa` downloads encoder and reports missing manual release; see [release details](CDVQA_FINAL_REPORT.md#reproduction-and-saved-assets) |

Use the full provisioning command in the first row with the named workflow. Acquisition is explicit. Startup and preflight never download models. Public routes currently require no credentials; upstream availability/terms can change. The provisioner refuses conflicting existing snapshots/manifests. Use a new root rather than overwrite a working install.

## Locations

Set SATQUERY_ASSET_ROOT explicitly. Without it, existing /root/satquery is preserved; otherwise ~/.local/share/satquery is used.

| Environment override | Default |
| --- | --- |
| SATQUERY_PAIRED_DIR | asset root / paired-lab |
| SATQUERY_GROUNDING_DIR | asset root / grounding-lab |
| SATQUERY_APP_DATA | asset root / app-data |
| SATQUERY_VQA_MODEL | asset root / models/vqa, then pinned HF cache |
| SATQUERY_VQA_ADAPTER | asset root / experiments/lora-pilot-v1/adapter |
| SATQUERY_CDVQA_MODEL_DIR | asset root / cdvqa |
| SATQUERY_CDVQA_ENCODER | TORCH_HOME/hub/checkpoints/resnet50-11ad3fa6.pth (default TORCH_HOME is ~/.cache/torch) |
| SATQUERY_WATER_CHECKPOINT | repository / paired_lab/checkpoints/water-v1.pt |

Unified uploads/results live in paired-lab/app; grounding data lives under its configured directory. New manifests use paths relative to the manifest; historical absolute paths remain supported. Set HF_HOME and TORCH_HOME explicitly to isolate caches.

## Inputs, datasets and rights

Inference does not require training datasets. Tracked paired examples/manifests in paired_lab/samples cover MCI/LEVIR-MCI, BigEarthNet v2 and Sen1Floods11. They are development smoke samples, not new held-out evidence. Inspect each manifest for provenance/split. User inputs must pass inputs.py, spectral_pair.py, sar_single.py and specialist checks; RGB is not calibrated reflectance and matching dimensions do not prove registration.

Single-image convenience examples reference optional sample/scene files under the asset root. Model provisioning does not restore them; upload a suitable image instead. Evaluation labels/caches, official-sensor scenes, local LoRA and CDVQA releases are not all included in a clone. See the individual [evidence reports](../README.md) before rerunning evaluations.

Code licenses, model terms and imagery rights are separate. The JSON inventory preserves known statements and unresolved terms; it does not grant commercial clearance or redistribution rights. Historical bootstrap/training scripts retain their original assumptions and are not current installers. Legacy ChangeFormer is not provisioned because MCI serves temporal requests.
