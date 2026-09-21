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
