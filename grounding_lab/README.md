# SATquery Grounding Lab — 12 September 2026

## Start and use
Open http://localhost:8765 and click Grounding Lab, or visit http://localhost:8765/grounding/. One server starts both pages. Grounding remains a manual experiment, outside the question router. Hosting and navigation were updated on 12 September.

Open PowerShell:

```powershell
cd "C:\Users\nrgen\.codex\scratch\SATquery AI\grounding_lab"
.\start-lab.ps1
```

Keep the terminal open. Choose an image, choose the object category, select Find objects + trace outlines, then Run selected tools. Try stadium and Try car provide inspected starting examples. PNG/JPEG/WebP/RGB TIFF only; multispectral data should be exported to an RGB preview. Changing category, mode or score clears the previous result. Original, boxes, outlines and coloured masks are actual run artifacts; click a processing card for full view. Expand the calculation and run details, or download the evidence ZIP.

Models run locally in separate worker processes and release memory after each job. The main workspace and lab share a busy gate. Starting a lab run releases the idle VQA model; the next VQA request reloads it. The detector is released before SAM loads. Other applications are not stopped. The worker requires at least 3 GiB free GPU memory at startup. Initial process/CUDA setup is slower than subsequent runs. Run one GPU task at a time for a predictable demo.

## What was added
Grounding DINO Tiny finds text-conditioned boxes. SAM Base receives the retained boxes and predicts three masks per box; the highest model-predicted IoU candidate is selected. Both are pinned pretrained Apache-2.0 checkpoints. No model training, fine-tuning, new shared-library installation or paid API was used.

Models:
- https://huggingface.co/IDEA-Research/grounding-dino-tiny — a2bb814dd30d776dcf7e30523b00659f4f141c71
- https://huggingface.co/facebook/sam-vit-base — 70c1a07f894ebb5b307fd9eaaee97b9dfc16068f

The existing local transformers 4.51.3, torch 2.8.0+cu128 and torchvision 0.23.0+cu128 environment is used. Model download manifests are at /root/satquery/grounding-lab/models.json. App uploads/results persist at /root/satquery/grounding-lab/app-data.

## Filtering and measurements
Default detector threshold 0.30; text threshold 0.25; overlap suppression IoU 0.50; maximum 24 retained objects. Boxes are clipped to image dimensions. A proposal covering at least 97% of the frame is excluded. A proposal covering at least 90% is also excluded if it encloses a much smaller same-category proposal (less than 60% of its area, at least 98% contained). This is an explicit development heuristic: it can suppress a real object filling the frame. All raw boxes, scores, filter settings and rejected indices remain in Run JSON.

Mask coverage = pixels in the union of predicted masks / all image pixels * 100. Overlapping mask pixels count once. This is not NDVI or geographic/surveyed area. Bounding boxes are [left, top, right, bottom] in image pixels. Detector scores and SAM predicted IoU are model scores, not calibrated confidence or measured accuracy.

The instances PNG contains integer object IDs; overlaps go to the first score-ranked object. masks.npz preserves each overlapping boolean mask independently. Coloured masks are a visualisation of the ID PNG. The worker records raw output metadata, timings, GPU allocation, source hash, model revisions and settings. Source pixels are not overwritten.

## Honest current result
Stadium and distinct cars are useful starting demonstrations. Dense buildings and a baseball complex did not work reliably: one coarse merged proposal was produced instead of separate objects. Those trials are retained. Aircraft, ships, buildings and sports fields are exploratory dropdown options, not validated capabilities. A separate fine-tuning or better remote-sensing detector may be needed for dense/small objects.

This is a functional experimental pipeline, not a benchmarked grounding system. No comparison with ChatGPT, VQA accuracy, or external localisation benchmarks is claimed. Do not connect it to the main router yet.

## Judge explanation
We choose the object manually. One model proposes boxes; a second uses those boxes to trace outlines. We show both, keep the model scores and raw records, and calculate only image-pixel coverage from the masks. We have checked some demo examples and retained failure cases. A convincing outline alone does not prove the box found the right object.

## Evidence
See REPORT.md, evidence/http, evidence/additional, evidence/browser and evidence/browser-car. Historical first-attempt failures remain under evidence/stadium-first and other v2 trial folders. The main-source preservation manifest is preserved-main-sha256.json. The source archive excludes model weights and the Python runtime; it is not a standalone installer.
