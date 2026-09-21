# Technology and rationale

| Layer | Exact implementation | Why |
|---|---|---|
| Frontend | HTML, CSS, vanilla JavaScript; no Node runtime/build | Small local app; image pan/zoom and theme control without a framework |
| Backend | FastAPI 0.115.12; Uvicorn 0.34.2 | Local HTTP uploads, jobs and artifact endpoints |
| VLM | AdaptLLM/remote-sensing-Qwen2-VL-2B-Instruct, revision 7f5dd71bf0f40c282193d50160e848a387a08ffe | Existing RS adaptation; measured fit on this laptop, not proven best checkpoint |
| Training | Torch 2.8.0+cu128; Transformers 4.51.3; Accelerate 1.6.0 | Existing GPU inference and training stack |
| Adaptation | PEFT 0.15.2; LoRA r4/alpha8/dropout0.05, q_proj/v_proj | Train a small adapter while freezing base weights |
| Raster | Rasterio 1.4.4 / GDAL 3.10.3 | GeoTIFF, masks, geotransforms and raster output |
| NDVI | NumPy 2.4.6 | Deterministic CPU band arithmetic |
| CRS | pyproj 3.7.2 | CRS interpretation and coordinate transformation |
| Images | Pillow 12.3.0 | RGB previews, upload decode, overlay PNG |
| Independent check | tifffile 2026.3.3 + scalar Python | Separate decoder/calculation for verification |
| Evaluation | Custom exact-label scorer in scripts/train_pilot.py | Auditable scoring; no LLM judge |
| Runtime | Python 3.11.16 in WSL2 Ubuntu; Torch CUDA build 12.8 | Local execution |

Checkpoint stored tensor elements: 2442359296 (marketed 2B family; tensor-storage count, not a separately loaded deduplicated parameter audit). LoRA trainable: 544768. Node is not used; no WSL Node installed. Full machine/version dump: metrics/system.json.
