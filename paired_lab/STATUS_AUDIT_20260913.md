# SATquery: seven-step status audit

Audit date: 13 September 2026. Requested destination was the literal placeholder `[path]`; this report is saved at `C:/Users/nrgen/.codex/scratch/SATquery AI/paired_lab/STATUS_AUDIT_20260913.md`.

This audit reads current code and preserved artifacts. No model inference, new test, implementation change, fix, server restart, or snapshot creation was performed for this audit. Previous test results below are historical artifacts, not tests rerun now.

Classification is against the requested seven-step scope and evidence requirements, not merely whether a narrow demo returns an answer. A functioning restricted path is not classified COMPLETE when material parts or requested evidence are missing.

| Step | Classification |
|---|---|
| 1. Baseline preserved | PARTIALLY BUILT |
| 2. Two-image input | PARTIALLY BUILT |
| 3. Data + models | PARTIALLY BUILT |
| 4. Temporal | PARTIALLY BUILT |
| 5. Optical–SAR | PARTIALLY BUILT |
| 6. Routing | PARTIALLY BUILT |
| 7. Evaluation | PARTIALLY BUILT |

## Step 1 — baseline preserved: PARTIALLY BUILT

There is no project Git commit hash: the SatQuery project has no `.git` directory. The saved pre-lab artifact is a SHA-256 manifest, **not a source snapshot**:
[evidence/demo-before.json](<C:/Users/nrgen/.codex/scratch/SATquery AI/paired_lab/evidence/demo-before.json>)

Manifest file SHA-256: `d6089a7d6c383fa63448b59434aeb5b7a1cf43d0e4d9bba3e6d915a89fb26876`.

The exact older snapshot path is `C:/Users/nrgen/.codex/scratch/SATquery AI/demo-freeze-20260907/source/`, with `C:/Users/nrgen/.codex/scratch/SATquery AI/demo-freeze-20260907/SHA256.json`. It is a 7 September freeze, not a demonstrated snapshot of the exact state immediately before paired-lab work.

The saved verification reports 35 tracked files, `changed: []`, and `passed: true`. The manifest covers top-level Python, main web files, grounding Python and grounding web files. It does not capture every model, data file, dependency or runtime state.
[evidence/validation-tests.json](<C:/Users/nrgen/.codex/scratch/SATquery AI/paired_lab/evidence/validation-tests.json>)

[evidence/demo-regression.json](<C:/Users/nrgen/.codex/scratch/SATquery AI/paired_lab/evidence/demo-regression.json>)

```json
{
  "tests": 39,
  "failures": [],
  "errors": []
}
```
Missing: a complete recoverable snapshot of the exact pre-lab baseline, including required runtime/model/data state. Why: this work saved hashes and left existing source in place; it did not create that complete snapshot. Hash agreement proves the listed files were unchanged when checked, not that an exact rollback bundle exists. The main service was started when found stopped; preservation does not mean uninterrupted uptime.

## Step 2 — two-image input: PARTIALLY BUILT

Actual implemented checks, not planned checks:

| Check | Exact code path | Actual behavior and boundary |
|---|---|---|
| Exactly two inputs | [inputs.py](<C:/Users/nrgen/.codex/scratch/SATquery AI/paired_lab/inputs.py:22>) | Rejects any count other than two. server.prepare also requires two known upload IDs at server.py:70–72. |
| Declared modality | [inputs.py](<C:/Users/nrgen/.codex/scratch/SATquery AI/paired_lab/inputs.py:10>) | Accepts only optical/SAR labels; route uses the labels at lines 25–37. It does not infer the sensor from image content. |
| File format and size | [server.py](<C:/Users/nrgen/.codex/scratch/SATquery AI/paired_lab/server.py:50>) | Reads at most 20 MiB + 1 and rejects larger uploads, lines 52–53. inputs.py:12 requires the rasterio GTiff driver; line 13 caps one megapixel and 14 bands. |
| Nodata and nonfinite pixels | [inputs.py](<C:/Users/nrgen/.codex/scratch/SATquery AI/paired_lab/inputs.py:14>) | Rejects any masked, NaN or infinite pixel at line 15. |
| Location | [inputs.py](<C:/Users/nrgen/.codex/scratch/SATquery AI/paired_lab/inputs.py:44>) | No independent image-location verification. Equal CRS, six affine coefficients and dimensions imply the same declared footprint. Incorrect but matching metadata can pass. |
| CRS | [inputs.py](<C:/Users/nrgen/.codex/scratch/SATquery AI/paired_lab/inputs.py:43>) | Uploaded pairs require both CRS values; line 44 compares their strings for equality. |
| Pixel grid/alignment | [inputs.py](<C:/Users/nrgen/.codex/scratch/SATquery AI/paired_lab/inputs.py:41>) | Dimensions must match; line 44 requires affine coefficients equal within absolute 1e-7, relative tolerance zero. No feature matching, subpixel residual measurement or actual registration runs. |
| Date | [inputs.py](<C:/Users/nrgen/.codex/scratch/SATquery AI/paired_lab/inputs.py:47>) | User-supplied acquisition dates must parse as YYYY-MM-DD. Before < after for temporal (49); optical/SAR difference <=14 days (50). Dates are not independently recovered or authenticated from the imagery. |
| Temporal dimensions/type/bands | [inputs.py](<C:/Users/nrgen/.codex/scratch/SATquery AI/paired_lab/inputs.py:52>) | Requires 256×256, three channels, uint8. Uploaded RGB band descriptions must be red, green, blue in that order (54). |
| Cross-modal bands | [inputs.py](<C:/Users/nrgen/.codex/scratch/SATquery AI/paired_lab/inputs.py:56>) | Requires exact band-name set and count: SAR VV/VH; optical B02,B03,B04,B05,B06,B07,B08,B8A,B11,B12 (59). Tensor order is explicitly rebuilt in engine.py:77 and 91. |
| Cross-modal grid scale | [inputs.py](<C:/Users/nrgen/.codex/scratch/SATquery AI/paired_lab/inputs.py:60>) | Requires 120×120; uploaded CRS projected in metres (61); absolute affine x/y diagonal scales each 10 (62). No separate rejection of shared shear/rotation or measurement of image registration error. |
| Cross-modal sensor | [inputs.py](<C:/Users/nrgen/.codex/scratch/SATquery AI/paired_lab/inputs.py:63>) | Requires sensor tag exactly Sentinel-1 for SAR and Sentinel-2 for optical (65). Cartosat/RISAT are not accepted. Temporal sensor/resolution is not checked against the training sensor domain. |
| Units | [inputs.py](<C:/Users/nrgen/.codex/scratch/SATquery AI/paired_lab/inputs.py:63>) | Requires dB for SAR and reflectance_x10000 for optical. Metadata is trusted; physical calibration is not independently validated. inspect() can take an explicitly supplied units value over a TIFF tag. |
| Trusted-sample exception | [server.py](<C:/Users/nrgen/.codex/scratch/SATquery AI/paired_lab/server.py:64>) | Catalog sample IDs set trusted_benchmark=True at line 74. inputs.py:42 then skips CRS/affine/date checks; temporal band names and cross-modal projected-grid checks also have this exception. Publisher correspondence is assumed, not independently measured. |

Missing: independent location/registration verification; broader sensor/format/resolution support; calibration verification; and a real uploaded geospatial-pair success trace covering every metadata check. The existing successful paired runs use catalog samples with geographic/date checks bypassed. Why: the implementation is a fixed-checkpoint lab relying on declared metadata and publisher pairing, not a general paired geospatial ingestion system. These are boundaries in the current code, not proposed fixes.

## Step 3 — data + models: PARTIALLY BUILT

### Actual paired datasets present

1. **LEVIR-CD samples distributed with ChangeFormer**. Dataset: https://justchenhao.github.io/LEVIR/ . Downloaded source: https://github.com/wgcban/ChangeFormer/tree/afd1b7ed640aa265a2c730de958416ae7356a2f9/samples_LEVIR . Local directory: `/root/satquery/paired-lab/ChangeFormer/samples_LEVIR/`. Inventory: **12 A images + 12 B images; 11 reference masks**. Exactly **7 test-named 256×256 pairs** were evaluated and exported into the lab catalog. The extra `test_113_0256.png` has no corresponding label in this directory. Three train pairs and one validation pair were not included in those seven metrics.

2. **BigEarthNet v2 / reBEN real-data subset supplied by ConfigILM**. Dataset: https://bigearth.net/ . Exact fixture source: https://github.com/lhackel-tub/ConfigILM/tree/d5a6c64bee268e71f12e130bd839ab9dfe53cc08/configilm/extra/mock_data/BENv2 . Local directory: `/root/satquery/paired-lab/ConfigILM/configilm/extra/mock_data/BENv2/`. Despite the `mock_data` directory name, the repository's `gen_mock_data_BENv2.py` copies real paired data from its source LMDB. Inventory: **24 unique paired samples, 48 LMDB entries**. Main metadata: 18 pairs (6 train, 6 validation, 6 test); extra snow/cloud metadata: 6 pairs (2 each split). **12 clear validation/test pairs** were evaluated; six train and six extra snow/cloud pairs were not evaluated. The evaluated fixtures are concentrated in one Austrian source scene.

BigEarthNet.txt text annotations, CDVQA, and ISRO/SAC Cartosat/RISAT paired evaluation data were not acquired or used in these new trials. Existing regional optical RGBs are not substituted for real optical–SAR pairs.

The lab catalog contains **19 paired examples: 7 temporal + 12 optical–SAR**. Each entry has filenames and a provenance manifest. TIFF exports do not invent a geographic transform absent from the fixture.
[samples/catalog.json](<C:/Users/nrgen/.codex/scratch/SATquery AI/paired_lab/samples/catalog.json>)

### Exact checkpoints downloaded and loaded

All seven checkpoints below have saved CPU inference evidence. This is not evidence of a GPU load.

| Checkpoint repository | Pinned revision | Saved load/inference evidence |
|---|---|---|
| [BIFOLD-BigEarthNetv2-0/resnet18-s1-v0.2.0](https://huggingface.co/BIFOLD-BigEarthNetv2-0/resnet18-s1-v0.2.0) / `model.safetensors` | `20e3c3ba8143ae600d7cf8e70d01a4278e6b0279` | [evidence/first-trials/ben-validation-33-69/result.json](<C:/Users/nrgen/.codex/scratch/SATquery AI/paired_lab/evidence/first-trials/ben-validation-33-69/result.json>): trace includes `device: cpu` and scores for s1 |
| [BIFOLD-BigEarthNetv2-0/resnet18-s2-v0.2.0](https://huggingface.co/BIFOLD-BigEarthNetv2-0/resnet18-s2-v0.2.0) / `model.safetensors` | `511825fd73a3c7b3c5353a2ba2f8d8c8c79bc806` | [evidence/first-trials/ben-validation-33-69/result.json](<C:/Users/nrgen/.codex/scratch/SATquery AI/paired_lab/evidence/first-trials/ben-validation-33-69/result.json>): trace includes `device: cpu` and scores for s2 |
| [BIFOLD-BigEarthNetv2-0/resnet18-all-v0.2.0](https://huggingface.co/BIFOLD-BigEarthNetv2-0/resnet18-all-v0.2.0) / `model.safetensors` | `ef959b5f06e98860945e3b7fe4749b1d609b123a` | [evidence/first-trials/ben-validation-33-69/result.json](<C:/Users/nrgen/.codex/scratch/SATquery AI/paired_lab/evidence/first-trials/ben-validation-33-69/result.json>): trace includes `device: cpu` and scores for all |
| [BIFOLD-BigEarthNetv2-0/resnet50-s1-v0.2.0](https://huggingface.co/BIFOLD-BigEarthNetv2-0/resnet50-s1-v0.2.0) / `model.safetensors` | `d417b3c32f2172cbceb14e5b106dd9aa7b77c647` | [evidence/selected-trials/ben-validation-33-69/result.json](<C:/Users/nrgen/.codex/scratch/SATquery AI/paired_lab/evidence/selected-trials/ben-validation-33-69/result.json>): trace includes `device: cpu` and scores for s1 |
| [BIFOLD-BigEarthNetv2-0/resnet50-s2-v0.2.0](https://huggingface.co/BIFOLD-BigEarthNetv2-0/resnet50-s2-v0.2.0) / `model.safetensors` | `f5a590cd5876845f62702260ff62ea5a325433bb` | [evidence/selected-trials/ben-validation-33-69/result.json](<C:/Users/nrgen/.codex/scratch/SATquery AI/paired_lab/evidence/selected-trials/ben-validation-33-69/result.json>): trace includes `device: cpu` and scores for s2 |
| [BIFOLD-BigEarthNetv2-0/resnet50-all-v0.2.0](https://huggingface.co/BIFOLD-BigEarthNetv2-0/resnet50-all-v0.2.0) / `model.safetensors` | `762acdc186cce6b31ecbc896ddab1721847d4c5e` | [evidence/selected-trials/ben-validation-33-69/result.json](<C:/Users/nrgen/.codex/scratch/SATquery AI/paired_lab/evidence/selected-trials/ben-validation-33-69/result.json>): trace includes `device: cpu` and scores for all |
| ChangeFormerV6 LEVIR `best_ckpt.pt`, locally `changeformer-levir.pt` | Source `afd1b7ed640aa265a2c730de958416ae7356a2f9`; checkpoint SHA-256 `db0dd783c3c3f27d02f55f24fa8199d2b2b47c422c7f7bd2e4d96e2fa65d69f2` | [evidence/first-trials/levir-test_102_0512_0000/result.json](<C:/Users/nrgen/.codex/scratch/SATquery AI/paired_lab/evidence/first-trials/levir-test_102_0512_0000/result.json>) |

Exact temporal checkpoint download URL:

https://github.com/wgcban/ChangeFormer/releases/download/v0.1.0/CD_ChangeFormerV6_LEVIR_b16_lr0.0001_adamw_train_test_200_linear_ce_multi_train_True_multi_infer_False_shuffle_AB_False_embed_dim_256.zip

Current load paths and revisions:

```json
{
  "models": {
    "all": {
      "repo": "BIFOLD-BigEarthNetv2-0/resnet50-all-v0.2.0",
      "revision": "762acdc186cce6b31ecbc896ddab1721847d4c5e",
      "path": "/root/.cache/huggingface/hub/models--BIFOLD-BigEarthNetv2-0--resnet50-all-v0.2.0/snapshots/762acdc186cce6b31ecbc896ddab1721847d4c5e"
    },
    "s1": {
      "repo": "BIFOLD-BigEarthNetv2-0/resnet50-s1-v0.2.0",
      "revision": "d417b3c32f2172cbceb14e5b106dd9aa7b77c647",
      "path": "/root/.cache/huggingface/hub/models--BIFOLD-BigEarthNetv2-0--resnet50-s1-v0.2.0/snapshots/d417b3c32f2172cbceb14e5b106dd9aa7b77c647"
    },
    "s2": {
      "repo": "BIFOLD-BigEarthNetv2-0/resnet50-s2-v0.2.0",
      "revision": "f5a590cd5876845f62702260ff62ea5a325433bb",
      "path": "/root/.cache/huggingface/hub/models--BIFOLD-BigEarthNetv2-0--resnet50-s2-v0.2.0/snapshots/f5a590cd5876845f62702260ff62ea5a325433bb"
    },
    "temporal": {
      "repo": "https://github.com/wgcban/ChangeFormer",
      "revision": "afd1b7ed640aa265a2c730de958416ae7356a2f9",
      "path": "/root/satquery/paired-lab/changeformer-levir.pt",
      "sha256": "db0dd783c3c3f27d02f55f24fa8199d2b2b47c422c7f7bd2e4d96e2fa65d69f2",
      "license_note": "README restricts code to non-commercial research; review before commercial distribution."
    }
  },
  "configilm_revision": "d5a6c64bee268e71f12e130bd839ab9dfe53cc08",
  "temporal_revision": "afd1b7ed640aa265a2c730de958416ae7356a2f9",
  "dependency_versions": {
    "timm": "1.0.19",
    "einops": "0.8.1",
    "lmdb": "1.7.3",
    "pandas": "2.3.2",
    "pyarrow": "21.0.0",
    "python-dateutil": "2.9.0.post0",
    "pytz": "2025.2",
    "tzdata": "2025.2",
    "scipy": "1.16.1"
  }
}
```
**Measured GPU memory footprint: NOT AVAILABLE for any of these paired specialists.** The actual load/inference path is CPU; engine.py:30 uses map_location='cpu', and fusion models/tensors remain on CPU (engine.py:73–95). There is no saved GPU-load allocator/device-memory measurement. Disk size, an unloaded GPU reading, an old grounding memory measurement, or the string `device: cpu` would not satisfy the requested measurement. No GPU load was performed for this audit.

Missing: the requested measured GPU-load evidence, representative geographically diverse paired data, BigEarthNet.txt/CDVQA evaluation coverage, and Cartosat/RISAT-compatible data/model validation. Why: the current work uses a small public fixture subset and CPU-only pretrained specialists. No new paired model fine-tuning was performed.

## Step 4 — temporal: PARTIALLY BUILT

Actual pair: `test_102_0512_0000.png` in the A and B folders of the pinned ChangeFormer LEVIR sample directory. Exported inputs:
[samples/levir-test_102_0512_0000/before.tif](<C:/Users/nrgen/.codex/scratch/SATquery AI/paired_lab/samples/levir-test_102_0512_0000/before.tif>)

[samples/levir-test_102_0512_0000/after.tif](<C:/Users/nrgen/.codex/scratch/SATquery AI/paired_lab/samples/levir-test_102_0512_0000/after.tif>)

Full saved answer text, unedited:

```text
The model marks possible building-related changes across 20.63% of the full crop, with the most marked pixels in the upper right. This binary map does not distinguish construction from removal.
```

This text is generated by a deterministic template from the model mask in [engine.py](<C:/Users/nrgen/.codex/scratch/SATquery AI/paired_lab/engine.py:53>); it is **not** a freely generated change-VQA model answer.

[evidence/first-trials/levir-test_102_0512_0000/result.json](<C:/Users/nrgen/.codex/scratch/SATquery AI/paired_lab/evidence/first-trials/levir-test_102_0512_0000/result.json>)

```json
{
  "task": "temporal",
  "answer": "The model marks possible building-related changes across 20.63% of the full crop, with the most marked pixels in the upper right. This binary map does not distinguish construction from removal.",
  "changed_pixels": 13521,
  "denominator_pixels": 65536,
  "coverage_percent": 20.63140869140625,
  "quadrant_pixels": {
    "upper left": 968,
    "upper right": 9940,
    "lower left": 1229,
    "lower right": 1384
  },
  "direction": "not determined",
  "seconds": 5.704302506999994,
  "confidence": {
    "kind": "uncalibrated model scores",
    "mean_marked_score": 0.986036479473114
  },
  "trace": [
    {
      "tool": "ChangeFormerV6 LEVIR",
      "revision": "afd1b7ed640aa265a2c730de958416ae7356a2f9",
      "device": "cpu",
      "input_shape": [
        256,
        256,
        3
      ],
      "normalization": "RGB / 127.5 - 1",
      "threshold": 0.5,
      "output": "last decoder head; two-class softmax",
      "checkpoint_sha256": "db0dd783c3c3f27d02f55f24fa8199d2b2b47c422c7f7bd2e4d96e2fa65d69f2"
    }
  ],
  "limitations": [
    "Building-change specialist; not general change VQA.",
    "No increase/decrease or surveyed-area claim.",
    "LEVIR development evidence does not establish CDVQA or ISRO/SAC performance."
  ]
}
```
Spatial evidence: [evidence/first-trials/levir-test_102_0512_0000/change-mask.png](<C:/Users/nrgen/.codex/scratch/SATquery AI/paired_lab/evidence/first-trials/levir-test_102_0512_0000/change-mask.png>), [evidence/first-trials/levir-test_102_0512_0000/overlay.png](<C:/Users/nrgen/.codex/scratch/SATquery AI/paired_lab/evidence/first-trials/levir-test_102_0512_0000/overlay.png>), [evidence/first-trials/levir-test_102_0512_0000/reference.png](<C:/Users/nrgen/.codex/scratch/SATquery AI/paired_lab/evidence/first-trials/levir-test_102_0512_0000/reference.png>).

Missing: general semantic change answers, increase/decrease inference, CDVQA results, wider geographies/sensors and calibrated confidence. Why: the loaded checkpoint outputs binary building-change logits; the application describes mask coverage and quadrants. It has no direction/class-change model or temporal language-model adaptation.

## Step 5 — optical–SAR: PARTIALLY BUILT

Actual paired sample: `ben-validation-33-69`. Optical patch `S2A_MSIL2A_20170613T101031_N9999_R022_T33UUP_33_69`; SAR patch `S1B_IW_GRDH_1SDV_20170612T165809_33UUP_33_69`.
[samples/ben-validation-33-69/optical.tif](<C:/Users/nrgen/.codex/scratch/SATquery AI/paired_lab/samples/ben-validation-33-69/optical.tif>)

[samples/ben-validation-33-69/sar.tif](<C:/Users/nrgen/.codex/scratch/SATquery AI/paired_lab/samples/ben-validation-33-69/sar.tif>)

[samples/ben-validation-33-69/manifest.json](<C:/Users/nrgen/.codex/scratch/SATquery AI/paired_lab/samples/ben-validation-33-69/manifest.json>)

Full saved answer text, unedited:

```text
The jointly trained optical–SAR model suggests Arable land, Broad-leaved forest, Inland waters, Land principally occupied by agriculture, with significant areas of natural vegetation. These are scene-level land-cover labels, not mapped regions or measured area.
```

The answer is a thresholded-class template in [engine.py](<C:/Users/nrgen/.codex/scratch/SATquery AI/paired_lab/engine.py:101>). The joint model actually receives a 12-channel tensor; the two other outputs come from separately trained two-channel and ten-channel checkpoints, not from hiding a channel in the same joint model.

[evidence/selected-trials/ben-validation-33-69/result.json](<C:/Users/nrgen/.codex/scratch/SATquery AI/paired_lab/evidence/selected-trials/ben-validation-33-69/result.json>)

```json
{
  "task": "optical_sar",
  "answer": "The jointly trained optical\u2013SAR model suggests Arable land, Broad-leaved forest, Inland waters, Land principally occupied by agriculture, with significant areas of natural vegetation. These are scene-level land-cover labels, not mapped regions or measured area.",
  "classes": [
    "Arable land",
    "Broad-leaved forest",
    "Inland waters",
    "Land principally occupied by agriculture, with significant areas of natural vegetation"
  ],
  "scores": {
    "s1": {
      "Agro-forestry areas": 0.0006278280052356422,
      "Arable land": 0.9377546310424805,
      "Beaches, dunes, sands": 0.0006239524227567017,
      "Broad-leaved forest": 0.8506443500518799,
      "Coastal wetlands": 0.0016960098873823881,
      "Complex cultivation patterns": 0.3493921458721161,
      "Coniferous forest": 0.0811297670006752,
      "Industrial or commercial units": 0.012265682220458984,
      "Inland waters": 0.8778409957885742,
      "Inland wetlands": 0.047660160809755325,
      "Land principally occupied by agriculture, with significant areas of natural vegetation": 0.5030713677406311,
      "Marine waters": 0.0023255234118551016,
      "Mixed forest": 0.14888162910938263,
      "Moors, heathland and sclerophyllous vegetation": 0.001565479440614581,
      "Natural grassland and sparsely vegetated areas": 0.0003892703098244965,
      "Pastures": 0.27541491389274597,
      "Permanent crops": 0.008861884474754333,
      "Transitional woodland, shrub": 0.2647920548915863,
      "Urban fabric": 0.08245094865560532
    },
    "s2": {
      "Agro-forestry areas": 1.4760137673874851e-05,
      "Arable land": 0.9799021482467651,
      "Beaches, dunes, sands": 0.00011036421346943825,
      "Broad-leaved forest": 0.44339871406555176,
      "Coastal wetlands": 9.813486940402072e-06,
      "Complex cultivation patterns": 0.2349083423614502,
      "Coniferous forest": 0.07316344231367111,
      "Industrial or commercial units": 0.005778060294687748,
      "Inland waters": 0.9127276539802551,
      "Inland wetlands": 0.000961205514613539,
      "Land principally occupied by agriculture, with significant areas of natural vegetation": 0.6851519346237183,
      "Marine waters": 6.708117871312425e-05,
      "Mixed forest": 0.42887815833091736,
      "Moors, heathland and sclerophyllous vegetation": 0.0005563828744925559,
      "Natural grassland and sparsely vegetated areas": 6.428036431316286e-05,
      "Pastures": 0.18080119788646698,
      "Permanent crops": 0.0047535463236272335,
      "Transitional woodland, shrub": 0.001303222612477839,
      "Urban fabric": 0.3166227638721466
    },
    "all": {
      "Agro-forestry areas": 5.776958914793795e-06,
      "Arable land": 0.9968761205673218,
      "Beaches, dunes, sands": 0.00010745402687462047,
      "Broad-leaved forest": 0.8771324753761292,
      "Coastal wetlands": 9.32026614464121e-06,
      "Complex cultivation patterns": 0.4643104672431946,
      "Coniferous forest": 0.1069587767124176,
      "Industrial or commercial units": 0.020035533234477043,
      "Inland waters": 0.9928283095359802,
      "Inland wetlands": 0.009865177795290947,
      "Land principally occupied by agriculture, with significant areas of natural vegetation": 0.5170260667800903,
      "Marine waters": 6.259763176785782e-05,
      "Mixed forest": 0.4799323081970215,
      "Moors, heathland and sclerophyllous vegetation": 0.0007586826686747372,
      "Natural grassland and sparsely vegetated areas": 0.0005802324158139527,
      "Pastures": 0.3834201395511627,
      "Permanent crops": 0.0009109170641750097,
      "Transitional woodland, shrub": 0.00626936461776495,
      "Urban fabric": 0.4384154677391052
    }
  },
  "seconds": 2.834320944999945,
  "trace": [
    {
      "tool": "BIFOLD-BigEarthNetv2-0/resnet50-s1-v0.2.0",
      "revision": "d417b3c32f2172cbceb14e5b106dd9aa7b77c647",
      "device": "cpu",
      "bands": [
        "VV",
        "VH"
      ],
      "normalization": "reBEN 120_nearest training mean/std",
      "input_shape": [
        1,
        2,
        120,
        120
      ],
      "threshold": 0.5
    },
    {
      "tool": "BIFOLD-BigEarthNetv2-0/resnet50-s2-v0.2.0",
      "revision": "f5a590cd5876845f62702260ff62ea5a325433bb",
      "device": "cpu",
      "bands": [
        "B02",
        "B03",
        "B04",
        "B05",
        "B06",
        "B07",
        "B08",
        "B8A",
        "B11",
        "B12"
      ],
      "normalization": "reBEN 120_nearest training mean/std",
      "input_shape": [
        1,
        10,
        120,
        120
      ],
      "threshold": 0.5
    },
    {
      "tool": "BIFOLD-BigEarthNetv2-0/resnet50-all-v0.2.0",
      "revision": "762acdc186cce6b31ecbc896ddab1721847d4c5e",
      "device": "cpu",
      "bands": [
        "VV",
        "VH",
        "B02",
        "B03",
        "B04",
        "B05",
        "B06",
        "B07",
        "B08",
        "B8A",
        "B11",
        "B12"
      ],
      "normalization": "reBEN 120_nearest training mean/std",
      "input_shape": [
        1,
        12,
        120,
        120
      ],
      "threshold": 0.5
    }
  ],
  "confidence": {
    "kind": "uncalibrated sigmoid scores; not accuracy",
    "threshold": 0.5
  },
  "limitations": [
    "Sentinel-1 VV/VH and Sentinel-2 multispectral only; no demonstrated Cartosat/RISAT transfer.",
    "Scene classification cannot locate built-up/water regions.",
    "Fusion superiority must be tested; more sensors do not guarantee a better answer."
  ]
}
```
Missing: mapped built-up/water regions, arbitrary optical/SAR sensors, Cartosat/RISAT compatibility, robust multisensor generalisation, calibrated scores, and a causal ablation that changes/removes SAR while holding the joint checkpoint fixed. Why: the implemented tool is a Sentinel-specific scene classifier. Different outputs from separately trained models do not by themselves prove how strongly the joint checkpoint depends on SAR.

## Step 6 — routing: PARTIALLY BUILT

The original demo router was not changed. A separate controller, `paired-rules-v1`, exists in the new lab. It uses regex checks plus declared modalities, not an LLM planner. It selects one paired workflow, validates the pair, then dispatches the worker.
[inputs.py](<C:/Users/nrgen/.codex/scratch/SATquery AI/paired_lab/inputs.py:19>); [server.py](<C:/Users/nrgen/.codex/scratch/SATquery AI/paired_lab/server.py:60>); [server.py](<C:/Users/nrgen/.codex/scratch/SATquery AI/paired_lab/server.py:78>); [server.py](<C:/Users/nrgen/.codex/scratch/SATquery AI/paired_lab/server.py:110>).

Real saved HTTP executions, extracted without altering their field values from [evidence/live-checks.json](<C:/Users/nrgen/.codex/scratch/SATquery AI/paired_lab/evidence/live-checks.json>):

```json
{
  "id": "1436232b2d7a4bd5b66c4f62fad1ea0f",
  "query": "What changed between the dates?",
  "task": "temporal",
  "controller": "paired-rules-v1",
  "trace": [
    {
      "tool": "ChangeFormerV6 LEVIR",
      "revision": "afd1b7ed640aa265a2c730de958416ae7356a2f9",
      "device": "cpu",
      "input_shape": [
        256,
        256,
        3
      ],
      "normalization": "RGB / 127.5 - 1",
      "threshold": 0.5,
      "output": "last decoder head; two-class softmax",
      "checkpoint_sha256": "db0dd783c3c3f27d02f55f24fa8199d2b2b47c422c7f7bd2e4d96e2fa65d69f2"
    }
  ]
}
```

```json
{
  "id": "bca2394b5ba547628271b9536869b8ab",
  "query": "Describe land cover using optical and SAR together",
  "task": "optical_sar",
  "controller": "paired-rules-v1",
  "trace": [
    {
      "tool": "BIFOLD-BigEarthNetv2-0/resnet50-s1-v0.2.0",
      "revision": "d417b3c32f2172cbceb14e5b106dd9aa7b77c647",
      "device": "cpu",
      "bands": [
        "VV",
        "VH"
      ],
      "normalization": "reBEN 120_nearest training mean/std",
      "input_shape": [
        1,
        2,
        120,
        120
      ],
      "threshold": 0.5
    },
    {
      "tool": "BIFOLD-BigEarthNetv2-0/resnet50-s2-v0.2.0",
      "revision": "f5a590cd5876845f62702260ff62ea5a325433bb",
      "device": "cpu",
      "bands": [
        "B02",
        "B03",
        "B04",
        "B05",
        "B06",
        "B07",
        "B08",
        "B8A",
        "B11",
        "B12"
      ],
      "normalization": "reBEN 120_nearest training mean/std",
      "input_shape": [
        1,
        10,
        120,
        120
      ],
      "threshold": 0.5
    },
    {
      "tool": "BIFOLD-BigEarthNetv2-0/resnet50-all-v0.2.0",
      "revision": "762acdc186cce6b31ecbc896ddab1721847d4c5e",
      "device": "cpu",
      "bands": [
        "VV",
        "VH",
        "B02",
        "B03",
        "B04",
        "B05",
        "B06",
        "B07",
        "B08",
        "B8A",
        "B11",
        "B12"
      ],
      "normalization": "reBEN 120_nearest training mean/std",
      "input_shape": [
        1,
        12,
        120,
        120
      ],
      "threshold": 0.5
    }
  ]
}
```

Missing: a unified automatic controller over old VQA/NDVI/grounding and new paired tools; arbitrary multi-tool composition; general natural-language intent understanding. Why: the new controller is deliberately isolated and recognizes a restricted grammar. Single-image requests are rejected with a main-workspace instruction rather than automatically dispatched. Broader orchestration has not been implemented.

## Step 7 — evaluation: PARTIALLY BUILT

The following numbers are recalculated by adding preserved confusion counts, not by running models again.

### Temporal mask trials

| Existing sample | TP | FP | FN | IoU | F1 |
|---|---:|---:|---:|---:|---:|
| levir-test_102_0512_0000 | 13357 | 164 | 196 | 0.9737551943 | 0.9867031100 |
| levir-test_121_0768_0256 | 10131 | 721 | 2698 | 0.7476752768 | 0.8556226511 |
| levir-test_2_0000_0000 | 15465 | 1087 | 1037 | 0.8792427085 | 0.9357415139 |
| levir-test_2_0000_0512 | 11197 | 773 | 805 | 0.8764774951 | 0.9341732021 |
| levir-test_55_0256_0000 | 8096 | 376 | 549 | 0.8974614788 | 0.9459601566 |
| levir-test_77_0512_0256 | 9151 | 3519 | 2349 | 0.6092948931 | 0.7572196938 |
| levir-test_7_0256_0512 | 8531 | 628 | 430 | 0.8896652414 | 0.9416114790 |

Pooled: TP=75928, FP=7268, FN=8064; F1=0.908294853698 (90.8295%); IoU=0.831996493535 (83.1996%).

[evidence/first-trials/summary.json](<C:/Users/nrgen/.codex/scratch/SATquery AI/paired_lab/evidence/first-trials/summary.json>)

These seven public demo crops are not representative independent test evidence. The upstream script selects checkpoints using test data. No clean held-out temporal score is established here.

The saved identical-image control has zero predicted changed pixels. Additional saved controls follow verbatim; these were not rerun for this audit. The real-pair negative is a derived/resized crop, not an independent scene. The evaluator encodes all-negative F1/IoU as 1 by convention; that is not positive-class detection evidence and is not included in the seven-pair aggregate above.
[evidence/controls/summary.json](<C:/Users/nrgen/.codex/scratch/SATquery AI/paired_lab/evidence/controls/summary.json>)

```json
[
  {
    "name": "brightness-only",
    "kind": "synthetic-no-change-control",
    "changed_pixels": 0,
    "denominator": 65536,
    "seconds": 4.335012775999985
  },
  {
    "name": "identical-second-scene",
    "kind": "synthetic-no-change-control",
    "changed_pixels": 0,
    "denominator": 65536,
    "seconds": 0.891491751999979
  },
  {
    "name": "real-pair-negative-crop",
    "kind": "derived real pair; reference has zero building change",
    "source": "test_77_0512_0256.png",
    "source_window": [
      0,
      0,
      128,
      128
    ],
    "resize": "128 to 256 bilinear; changed physical scale; not independent benchmark",
    "changed_pixels": 0,
    "denominator": 65536,
    "seconds": 0.9640275540000403
  }
]
```
### Optical–SAR classification trials

Fixed threshold 0.5. Micro F1 across 19 scene labels, not image accuracy. Six validation and six test-labelled fixtures from one Austrian scene.

| Checkpoint family | Split | Input | TP | FP | FN | Micro F1 |
|---|---|---|---:|---:|---:|---:|
| ResNet18 | validation | s1 | 21 | 7 | 11 | 0.700000000000 (70.0000%) |
| ResNet18 | validation | s2 | 23 | 7 | 9 | 0.741935483871 (74.1935%) |
| ResNet18 | validation | all | 21 | 6 | 11 | 0.711864406780 (71.1864%) |
| ResNet18 | test | s1 | 17 | 6 | 10 | 0.680000000000 (68.0000%) |
| ResNet18 | test | s2 | 18 | 6 | 9 | 0.705882352941 (70.5882%) |
| ResNet18 | test | all | 16 | 6 | 11 | 0.653061224490 (65.3061%) |
| ResNet50 | validation | s1 | 19 | 6 | 13 | 0.666666666667 (66.6667%) |
| ResNet50 | validation | s2 | 18 | 6 | 14 | 0.642857142857 (64.2857%) |
| ResNet50 | validation | all | 22 | 5 | 10 | 0.745762711864 (74.5763%) |
| ResNet50 | test | s1 | 16 | 6 | 11 | 0.653061224490 (65.3061%) |
| ResNet50 | test | s2 | 14 | 5 | 13 | 0.608695652174 (60.8696%) |
| ResNet50 | test | all | 20 | 6 | 7 | 0.754716981132 (75.4717%) |

Initial evidence: [evidence/first-trials/summary.json](<C:/Users/nrgen/.codex/scratch/SATquery AI/paired_lab/evidence/first-trials/summary.json>). Selected-model evidence: [evidence/selected-trials/summary.json](<C:/Users/nrgen/.codex/scratch/SATquery AI/paired_lab/evidence/selected-trials/summary.json>). Selection artifact: [evidence/refinement.json](<C:/Users/nrgen/.codex/scratch/SATquery AI/paired_lab/evidence/refinement.json>).

The selection artifact compares joint ResNet18 validation F1 0.711864406779661 with joint ResNet50 validation F1 0.7457627118644068, and records `promote: true`. There was no local training or threshold fitting. This narrow model selection does not establish cross-geography generalisation.

### Functional checks already saved

- [evidence/validation-tests.json](<C:/Users/nrgen/.codex/scratch/SATquery AI/paired_lab/evidence/validation-tests.json>): 33/33 passed.
- [evidence/live-checks.json](<C:/Users/nrgen/.codex/scratch/SATquery AI/paired_lab/evidence/live-checks.json>): 10/10 passed.
- [evidence/demo-regression.json](<C:/Users/nrgen/.codex/scratch/SATquery AI/paired_lab/evidence/demo-regression.json>): 39 tests, zero errors, zero failures. These are existing functional tests, not a new VQA quality score.
- Final browser artifact: `C:/Users/nrgen/.codex/visualizations/2026/09/07/01a07bbd-eff2-7ec3-b6ae-8886a03bfb57/paired-browser.json` records no JavaScript errors, successful evidence ZIP download, desktop width 1600/scroll width 1600, mobile width 390/scroll width 390, and footer bottom 993.734375 within a 1000px-high viewport. The copied `paired_lab/evidence/browser/report.json` predates that final footer adjustment; do not treat the copy as the final screenshot record.

Missing: full prescribed benchmark evaluation, broader independent geographical test sets, confidence calibration, sensor-transfer testing, measured GPU memory, full live VQA/NDVI→paired→VQA/NDVI replay, and a controlled within-joint-model SAR ablation. Why: the saved evaluations are limited to small public fixtures, lightweight functional checks and isolated CPU/browser runs. The original specification's evaluation coverage is not complete.

## Audit boundary

The artifacts establish real restricted CPU workflows, not merely placeholders. They do not establish completion of the full seven-step scope or the full ISRO specification. No missing component was implemented and no failed or incomplete component was fixed while writing this report.
