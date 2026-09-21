# Actual function-level data paths
NDVI upload: web/app.js upload → POST/api/images → server.upload → geo.ingest → labelled-band checks/original TIFF retained/RGB display stretch → image record.
Explicit mode submit (question text NOT interpreted) → POST/api/ndvi(image_id,threshold) → server.ndvi_run validation/queue → run_ndvi → geo.analyse read/scales → geo.calculate validity/NDVI → threshold/count/determinant area → overlay.png+ndvi.tif → templated answer/statistics → GET/api/runs/id polling → showTrace/ndvi-overlay → shared pan/zoom.
Original source calibration happens earlier in scripts/fetch_scene.py. Browser Save run exports JSON; analytical_artifact serves raster/overlay.
VQA: same image upload/PNG preview → question/mode → POST/api/analyze → server.analyze limited regex refusal → run_job local pinned snapshot → AutoProcessor/Qwen2VL → optional PeftModel → RGB chat template/tensors → generate/decode → run JSON → polling/answer/showTrace.
Baseline uses disable_adapter after attachment. No grounding in VQA branch.
