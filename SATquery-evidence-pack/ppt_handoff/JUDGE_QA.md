# Judge Q&A — short, evidence-backed answers
**What did you train?** 544768 rank4 LoRA parameters on an existing AdaptLLM RS checkpoint;720RSVQA questions/120images. Base weights frozen. MODEL_LINEAGE/TRAINING_REPORT.
**Is this GeoChat/a wrapper?** We reuse prior model research. Our contribution is the local adaptation experiment and calibrated spectral evidence workflow. We have no head-to-head GeoChat comparison or unique-research claim. USP_EVIDENCE.
**Does47/60 prove improvement?** It improves exact-label dev score under matched prompts; 20images/one scene, not final generalization. EVALUATION_REPORT.
**Why37/60 majority?** Urban11 + presenceyes16 + comparison10. Computed descriptively from dev labels.
**Just formatting?** Fifteen gains involve prior invalid format;11 change a valid wrong label to correct;2regressions. Some rural/urban prose was already semantically right. EXAMPLES.
**Why LoRA?** Small trainable memory/adapter footprint, preserves base; we measured local feasibility, not universal superiority.
**Why were old NDVI figures wrong?** Legacy pixels already had offset removed; we applied it again. Independent source comparison proved a1000DN difference. Old46.75%/620.09ha invalid. NDVI_AUDIT.
**Current area?** 38761pixels*100m²/10000=387.61ha;14.79% of262144validpixels. Grid area, not vegetation survey.
**How verified?** Matching Collection1 calibration plus different TIFF decoder/scalar formula; zero mask disagreements; visual plausibility check. Independent report.
**What does0.049s median mean?**20 warm-cache CPU server jobs including TIFF decode, mask and output files; excludes upload/source download/browser/final JSON serialization. PERFORMANCE_BENCHMARKS.
**No NIR?** NDVI refuses; RGB VQA may still operate.
**Confidence?** No calibrated confidence. We show inputs/threshold/coverage, not invented certainty.
**Why no SAR?** This is an internal prototype, not full PS completion. Paired-sensor alignment/specialist evaluation remain planned.
**Temporal alignment?** Planned common footprint/CRS/grid, registration checks and cloud/quality masks before change inference; not implemented.
**Does natural language choose tools?** Not yet: manual mode. Current regex refuses some tasks but misses some wording.
**What could fail today?** Wrong VQA labels, format sensitivity, untrusted input calibration, unsupported temporal wording, absent timeout/cancel. FAILURE_MODES.
**What do you own?** Our code/adapter/splits/evidence, subject to upstream/data licenses. Not Qwen/AdaptLLM/LoRA/RSVQA/NDVI.
