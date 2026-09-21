
from pathlib import Path
import json,csv
h=Path(__file__).resolve().parents[1]
def put(name,text):(h/name).write_text(text.strip()+'\n')
sys=json.loads((h/'metrics/system.json').read_text());r=json.loads((h/'raw/training_result.json').read_text())
put('PROJECT_STATUS.md', '''
# Current status — evidence snapshot, 6 September 2026

## Implemented and verified within stated scope
- Original local VQA: real pinned checkpoint; demonstrated image-question inference. Accuracy is limited.
- LoRA training execution and adapter reload: saved 720-step pilot, 544768 trainable parameters.
- Evaluation page: displays stored original diagnostic and separate development comparison, not live evaluation.
- Corrected NDVI: real red/NIR arithmetic; independent decoder/scalar verification agrees on all mask pixels for one scene.
- NDVI overlay: toggle, shared image transform, projected area and result/raster exports.
- Supported GeoTIFF ingestion: labelled RGB bands, original raster retention, CRS/affine/bounds/resolution metadata.
- Input tests: malformed, oversized, missing-NIR, zero denominator and nodata-heavy cases exercised.

## Implemented but not fully validated
- General GeoTIFF support: supported crop contract only; user-supplied reflectance tags are trusted, not independently authenticated.
- General projected area: determinant calculation, metre-based projected CRS. No terrain correction; geographic CRS gets no area.
- Run details: useful measurements/model IDs, not a full orchestrator trace. NDVI trace lacks a general tool registry.
- General input guardrails: keyword refusal exists but misses “Compare this to last year”; routed to VQA during failure testing.
- Pan/zoom alignment: visual/implementation checks, not a GIS registration benchmark.
- Local runtime: functional prototype, no timeout/cancel/recovery robustness guarantee.

## Experimental
- Adapted VQA: 23/60 to 47/60 on development, format failures 20 to 0. Not final held-out performance.
- Semantic improvement is against published labels; there is no independently annotated visual validation set.

## Planned / not implemented
Natural-language tool routing; text-guided grounding; temporal/change VQA; optical-SAR fusion; calibrated confidence; automatic source retrieval; arbitrary AOI/polygon analysis; full processing-stage viewer; final held-out adapter evaluation; fallback recording; final deck.
NDVI threshold masks are not text-guided grounding.
No React, hosted inference API, autonomous multi-agent backend or BigEarthNet training was added.

This is an internal prototype, not completion of the full SIH problem statement.
''')
put('TECH_STACK.md','# Technology and rationale\n\n| Layer | Exact implementation | Why |\n|---|---|---|\n'+
'| Frontend | HTML, CSS, vanilla JavaScript; no Node runtime/build | Small local app; image pan/zoom and theme control without a framework |\n'+
'| Backend | FastAPI '+sys['packages']['fastapi']+'; Uvicorn '+sys['packages']['uvicorn']+' | Local HTTP uploads, jobs and artifact endpoints |\n'+
'| VLM | AdaptLLM/remote-sensing-Qwen2-VL-2B-Instruct, revision 7f5dd71bf0f40c282193d50160e848a387a08ffe | Existing RS adaptation; measured fit on this laptop, not proven best checkpoint |\n'+
'| Training | Torch '+sys['packages']['torch']+'; Transformers '+sys['packages']['transformers']+'; Accelerate '+sys['packages']['accelerate']+' | Existing GPU inference and training stack |\n'+
'| Adaptation | PEFT '+sys['packages']['peft']+'; LoRA r4/alpha8/dropout0.05, q_proj/v_proj | Train a small adapter while freezing base weights |\n'+
'| Raster | Rasterio '+sys['packages']['rasterio']+' / GDAL '+sys['gdal']+' | GeoTIFF, masks, geotransforms and raster output |\n'+
'| NDVI | NumPy '+sys['packages']['numpy']+' | Deterministic CPU band arithmetic |\n'+
'| CRS | pyproj '+sys['packages']['pyproj']+' | CRS interpretation and coordinate transformation |\n'+
'| Images | Pillow '+sys['packages']['Pillow']+' | RGB previews, upload decode, overlay PNG |\n'+
'| Independent check | tifffile '+sys['packages']['tifffile']+' + scalar Python | Separate decoder/calculation for verification |\n'+
'| Evaluation | Custom exact-label scorer in scripts/train_pilot.py | Auditable scoring; no LLM judge |\n'+
'| Runtime | Python '+sys['python'].split()[0]+' in WSL2 Ubuntu; Torch CUDA build '+sys['cuda_torch_build']+' | Local execution |\n\n'+
'Checkpoint stored tensor elements: '+str(sys['checkpoint_tensor_elements'])+' (marketed 2B family; tensor-storage count, not a separately loaded deduplicated parameter audit). LoRA trainable: 544768. Node is not used; no WSL Node installed. Full machine/version dump: metrics/system.json.\n')
put('MODEL_LINEAGE.md', '''
# Model lineage and ownership
Qwen2-VL-2B → Qwen2-VL-2B-Instruct → AdaptLLM remote-sensing-Qwen2-VL-2B-Instruct → our lora-pilot-v1 adapter.

The starting checkpoint already contains remote-sensing post-training. We did not create Qwen's architecture, its pretraining, the upstream RS adaptation, LoRA, RSVQA or NDVI. The upstream model card describes its ancestry and links its RS instruction data: https://huggingface.co/AdaptLLM/remote-sensing-Qwen2-VL-2B-Instruct .

Our work: select/pin the checkpoint; construct a documented RSVQA-LR subset and source-scene-separated development split; train the adapter; measure paired development outputs; implement the local app and deterministic geospatial workflow; audit/calibrate the sample and independently reproduce its measurement.

We trained LoRA matrices attached to q_proj and v_proj, rank 4, 544768 trainable parameters. The original model weights remain frozen. No full-model finetune and no new foundation model.

Training inputs: RGB images with Qwen chat templates and restricted answer-label suffixes; assistant-answer-only loss. Inference loads pinned base, then PEFT adapter when selected. Baseline uses disable_adapter() after an adapter has been attached. Pilot modes use 64–128 visual tokens and max 16 output tokens; general baseline UI uses 256–512 and max 128, so those UI modes are not an apples-to-apples benchmark.
''')
put('TRAINING_REPORT.md',f'''
# Training dossier
Source: RSVQA LR v1.0, DOI 10.5281/zenodo.6344334, CC-BY-4.0 (Zenodo API checked). Published OSM-derived labels, not our manual annotations.
720 training Q&A / 120 images, six source scenes. 60 development Q&A / 20 images, one different source scene. Source images 256 x 256 RGB; TIFF-to-PNG RGB conversion; processor dynamically resizes into 64–128 visual-token bounds.
Categories: rural/urban 120 train, presence 240, comparison 360; dev 20 each.
Selection seed 26167; sample order shuffled once, then traversed once. Exact rows/hashes: raw/train.jsonl, raw/dev.jsonl, raw/learning_manifest.json.
Training/dev source scenes disjoint; official diagnostic test scene excluded; image hashes checked. This does not rule out adjacency or upstream checkpoint contamination.

One epoch/pass, 720 optimizer steps, batch 1, accumulation 1, effective batch 1.
AdamW, LR 0.0001, default betas (0.9,0.999), eps 1e-8, weight decay 0.01; no scheduler or warmup.
LoRA rank4 alpha8 dropout0.05, q_proj/v_proj, bias none; 544768 trainable.
BF16; SDPA; non-reentrant gradient checkpointing; clip grad norm 1; answer-only loss; no quantization.
GPU: RTX 5060 Laptop 8GB. Peak allocated recorded {r['peak_allocated_GiB']:.3f} GiB.
Recorded seconds: {r['seconds']:.3f}. IMPORTANT: timer starts before training and ends after adapted dev evaluation and save; it is NOT isolated training time. Baseline dev evaluation and reload are outside it.
First loss {r['losses'][0]['loss']:.8f}; final {r['losses'][-1]['loss']:.8f}. Different examples: this endpoint difference is not a controlled loss improvement metric. See all 720 values and moving-average curve.
Saved: final adapter and processor; no per-epoch/intermediate checkpoint archive. Reload succeeded.
Historical training-running/terminal screenshots were not saved. We provide raw logged values and honestly labelled plots, not reconstructed terminal screenshots.
''')
put('EVALUATION_REPORT.md','''
# Development evaluation, not final benchmark
| Category | Original | Adapter | Development majority |
|---|---:|---:|---:|
| Rural/urban | 0/20 | 15/20 | 11/20 urban |
| Presence | 10/20 | 15/20 | 16/20 yes |
| Comparison | 13/20 | 17/20 | 10/20 either |
| Total | 23/60 | 47/60 | 37/60 |

Original 38.33%, adapter 78.33%, majority 61.67%. The majority is a descriptive baseline computed from development labels, not a model selected without observing development labels.
Same prompts, RGB processor, 64–128 visual tokens, deterministic max16 output tokens. Normalize lower-case/whitespace, remove trailing space .!? characters, require exact reference equality. Invalid formatting counts wrong.
20 original format failures, zero adapted. Pair transitions: 11 valid-format wrong-label → correct-label, 15 invalid-format → correct-label, 2 regressions, 32 unchanged correctness.
Do not claim all 24 net gains prove better visual reasoning. All 20 rural/urban original outputs were format-invalid; some already named the correct class. The adapter underperforms the majority baseline on presence.
60 questions share only 20 images; samples are correlated and from one dev scene. Published labels may be noisy, upstream exposure unknown, no independent hand-label audit or statistical generalization claim.
Exact predictions: raw/*predictions.jsonl and metrics/all_prediction_comparisons.csv.

## Frozen diagnostic / final test
Earlier original-model diagnostic: 24/60 (40%), presence10/20, comparison14/20, rural0/20; 20 format failures. This uses a DIFFERENT 60-image set and must not be paired with 47/60.
It has already been inspected, so is not a fresh final test. No final held-out adapter test is available in this handoff; freeze configuration and reserve a fresh final split before running it.
''')
put('EXAMPLES.md','# Real development examples\n\nThese are cherry-picked explanatory examples, not an unbiased evaluation. “Correct” means agreement with published reference labels, not independent visual truth.\n\n')
with (h/'EXAMPLES.md').open('a') as f:
 for x in json.loads((h/'examples/selected.json').read_text()):
  reason={'semantic-label gain':'Original and adapter both use valid labels; adapter now matches the published label. This is not merely formatting.','regression':'Original matches the reference; adapter changes to the wrong label.','format-confounded gain':'Original violates the exact-label protocol. Inspect its wording before attributing this to semantic improvement.'}[x['kind']]
  f.write(f"## Q{x['question_id']} — {x['kind']}\n\n![Image {x['image_id']}]({x['image']})\n\nQuestion: {x['question']}\n\nReference: {x['reference']}\n\nOriginal: {x['base']}\n\nAdapter: {x['adapter']}\n\n{reason}\n\n")
