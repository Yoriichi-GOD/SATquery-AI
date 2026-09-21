# SATquery AI — local prototype

## Start

Open PowerShell in this folder and run `./start.ps1`. Leave that terminal running and open http://localhost:8765. Stop with Ctrl+C. The first analysis loads the cached checkpoint; subsequent requests reuse it. The app listens only on this laptop.

Requires the existing Ubuntu WSL environment at `/root/satquery/.venv` and its cached model. Additional app dependencies are recorded in `requirements-app.txt`; this file alone does not recreate the GPU environment. See `/root/satquery/requirements-inference-tested.txt` for that environment.

## What works

- Optical RGB image upload and preview, with zoom, pan and reset.
- Local Qwen2-VL inference with real loading status, elapsed time and a saved run record.
- Light-gray and dark themes, persisted locally; the satellite image itself is never theme-adjusted.
- Saved baseline evaluation screen, with limitations and category scores.
- Reduced-motion support and a stacked layout for narrow screens.
- Basic rule-based routing rejects explicit SAR, temporal and geographic-measurement requests. It is not a learned agent or complete intent detector.

The app defaults to the preserved baseline for general questions. Optional experimental yes/no and rural/urban modes use our saved LoRA pilot. These modes use the pilot's lower image-token budget and 16-token answer limit. The seven user-supplied transparent illustrations are integrated. Originals remain in UI/; served copies live in web/art/. Header and footer artwork switch with the theme.

## Inputs and limitations

PNG/JPEG/WebP and single-frame RGB TIFF, up to 20 MB and 25 million pixels. Non-RGB TIFF requires explicit band selection and is rejected. This is image VQA, not complete GeoTIFF/GIS support. No geographic scale, compass, bounding boxes or confidence scores are inferred. Uploads are converted to RGB with EXIF orientation applied. Model preprocessing bounds the image token count, so fine details can be lost.

Answers can be wrong or truncated after 128 tokens in general mode, or 16 in experimental modes. The 60-question diagnostic used a different 16-token label protocol; interactive responses are not benchmark scores.

Images and run JSON stay in `/root/satquery/app-data/`. Upload files persist on disk; the server's image/job index is in memory, so re-upload after restarting. There is no automatic retention cleanup yet. Do not expose this prototype publicly.

The sample is the GeoChat demo image from https://raw.githubusercontent.com/mbzuai-oryx/GeoChat/main/demo_images/04133.png. It is a demonstration, not our evaluation set. Model: https://huggingface.co/AdaptLLM/remote-sensing-Qwen2-VL-2B-Instruct.

## Learning artifacts

`/root/satquery/data/train.jsonl`: 720 questions / 120 images.

`/root/satquery/data/dev.jsonl`: 60 questions / 20 images from one separate source scene. Both are drawn from the official RSVQA-LR training split. The official test scene is excluded. Label counts and hashes are recorded in `learning_manifest.json`. The learning sample is not class-balanced; report per-type results and compare with majority baselines.

`scripts/prepare_learning.py` reproduces the subset from downloaded official annotations and the image archive. It refuses to change an existing manifest.

`scripts/lora_trial.py` runs eight steps and verifies adapter reload. Completed locally: peak PyTorch allocation 4.43 GiB; 544,768 trainable parameters. This only proves feasibility.

`scripts/train_pilot.py` performs a fresh one-pass pilot with rank 4, learning rate 1e-4, answer-only loss, and 64–128 visual tokens. It compares baseline and adapter on development data with the same 16-token label protocol. It does not consume the held-out test. Both experiment scripts refuse to overwrite an existing experiment directory.

Do not run training while the web server holds the model on the GPU. Stop the server first, run the experiment, then restart it.

## Verification so far

Real browser test: sample upload → question about baseball fields → local model returned `4` → answer and timing displayed. Both themes and saved evaluation were inspected. The experimental adapter answered `no` to the sample water question, and switching back to baseline returned `4` for baseball fields. These are integration checks, not an accuracy evaluation. API checks covered invalid files, empty questions, unsupported routes, and external Origin rejection. GPU environment dependency check passed after app dependencies were installed. Mobile layout is implemented but not yet separately browser-validated.

## Next work

Improve input/answer handling on development data and validate the experimental modes beyond this small scene. Complete the final evaluation protocol, presentation and clean-start rehearsal. See manifesto.md for the September 9 plan.

## First pilot result — September 6

One fresh 720-step pass completed. On the separate 60-question development set, original model 23/60 (38.3%), adapter 47/60 (78.3%). Format failures fell from 20 to zero. Per-type adapter results: rural/urban 15/20, presence 15/20, comparison 17/20. Peak PyTorch allocated memory 4.45 GiB. The adapter saved and reloaded successfully. Full experiment: `/root/satquery/experiments/lora-pilot-v1`; compact result: `results/pilot-v1.json`.

This is development evidence, with repeated images across questions and only one development source scene. A per-category majority baseline scores 37/60. Improvements include answer-format compliance. Do not describe 78.3% as a final test score or general satellite understanding. The original frozen test files have not been changed.


## Multispectral milestone — 6 September 2026
The app now supports labelled RGB/red/NIR GeoTIFF crops (up to 20 MB, 4,194,304 pixels, 16 bands), retains original rasters and metadata, and calculates deterministic NDVI on CPU. Use **Load Dehradun multispectral sample**, then **Analyze image**. The threshold is adjustable; the evidence overlay follows the RGB preview's pan and zoom. Export the result JSON and NDVI GeoTIFF.

Sample: Sentinel-2A, S2A_T43RGP_20211125T053958_L2A, 25 November 2021, EPSG:32643, 512 x 512 pixels at 10 m. Source and calibration manifest: /root/satquery/scenes/scene-manifest.json. Fetch script: scripts/fetch_scene.py. Source: https://earth-search.aws.element84.com/v1 . Contains modified Copernicus Sentinel data (2021).

NDVI requires labelled bands and reflectance_units=surface_reflectance metadata. Arbitrary unlabelled stacks are rejected, not guessed. SCL classes 4/5/6/7 are retained when supplied; class 7 is unclassified, so this is not a guarantee of cloud-free imagery. Negative/nonfinite reflectance and zero denominator pixels are excluded. RGB display stretch never changes analytical values. Area is projected grid area in supported metre-based CRSs, not terrain surface area. The overlay identifies threshold-selected pixels, not vegetation health or arbitrary object grounding.

Verified: known NDVI and invalid-pixel cases, affine pixel centre, 100 m2 pixel area, real TIFF upload, raster/overlay export, RGB rejection and invalid threshold rejection. Evidence: results/ndvi-integration.json. Corrected after calibration audit: at threshold 0.5, 38761 selected / 262144 valid pixels; 262144 total; 387.61 hectares grid area. Earlier 620.09 ha result is invalid; see results/calibration-audit.md.

Remaining: natural-language tool routing, richer evidence controls, object-grounding feasibility and final untouched-test evaluation. The explicit NDVI mode currently runs the selected calculation; it does not interpret arbitrary question text.
Dependencies added: rasterio==1.4.4, pyproj==3.7.2.
