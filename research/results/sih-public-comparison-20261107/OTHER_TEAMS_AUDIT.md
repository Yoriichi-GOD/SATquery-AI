# Additional current public source inspections — 7 November 2026

These are static source/artifact inspections, not executed competitor tests or a ranking of all SIH teams.
Author measurements remain author measurements. Public source can be incomplete; absence of a file
does not establish absence from a team's private system. Repository inactivity is not a submission freeze.

## nbsayan7-cell/SatQuery-AI

Pin: `884cdd6408fc6de48b3db959d150ffc954960301`, main, 8 September 2026 12:37:52UTC; unarchived.
The root/directory API was inspected because the recursive tree response was unavailable/oversized.
Scope: README, routes/services/tests directory listings, model adapters, query router, confidence module,
benchmark record and scientific-verification report. No full-tree absence assertion is made.

Strengths: substantial deterministic preprocessing/change code, pair-validation service, dedicated
fusion endpoint, evidence assembly, confidence-component implementation, many software tests, and
linked hosted presentation material. These go beyond a slide-only concept. Hosting/model behavior
was not independently exercised. [Current source](https://github.com/nbsayan7-cell/SatQuery-AI/tree/884cdd6408fc6de48b3db959d150ffc954960301).

Important limits visible in code:

- Main `QueryService.process_query` validates an optional second image but passes only the first image
  to `ModelRouter.route_query`; that router selects captioning versus VQA by lexical keywords.
  Dedicated change/fusion routes exist, so this is a general-query integration limit, not total absence
  of paired analysis. [Query service](https://github.com/nbsayan7-cell/SatQuery-AI/blob/884cdd6408fc6de48b3db959d150ffc954960301/backend/services/query_service.py),
  [router](https://github.com/nbsayan7-cell/SatQuery-AI/blob/884cdd6408fc6de48b3db959d150ffc954960301/ai/orchestrator.py).
- Several named specialists map to the same local class. Registering names such as DOFA/GeoChat is
  not evidence that each original model's weights executed. The fusion class uses CV feature extraction
  and optional Ollama vision/language synthesis, with fixed confidence assignments. This is different
  from a demonstrated jointly trained optical–SAR encoder. [Dispatcher](https://github.com/nbsayan7-cell/SatQuery-AI/blob/884cdd6408fc6de48b3db959d150ffc954960301/ai/specialists/dispatcher.py),
  [fusion adapter](https://github.com/nbsayan7-cell/SatQuery-AI/blob/884cdd6408fc6de48b3db959d150ffc954960301/ai/models/fusion.py).
- VQA has optional real inference and explicit fallback branches. Confidence constants such as0.95
  are not calibration results; failed inference does not imply that a model produced the fallback text.
  [VQA adapter](https://github.com/nbsayan7-cell/SatQuery-AI/blob/884cdd6408fc6de48b3db959d150ffc954960301/ai/models/vqa.py).
- The stored20/20benchmark explicitly identifies synthetic/curated reference scenarios. It must not
  be compared with scientific segmentation/VQA accuracy or counted as20independent real scenes.
  Our312software tests also are not scientific accuracy trials.
  [Benchmark artifact](https://github.com/nbsayan7-cell/SatQuery-AI/blob/884cdd6408fc6de48b3db959d150ffc954960301/docs/BENCHMARK-20-RESULTS.json).

Verdict: a substantial prototype with useful validation/product ideas; inspected evidence does not
establish the README's full specialist roster, calibrated confidence, or universal operational accuracy.
Our demonstrated learned-specialist paths and measured evidence are a defensible distinction; no
common-input performance comparison was run.

## Gowrav-M/satquery-ai-sih-2026-evidence — Team STARFORGE

Pin: `77042af4db679f62b1657b86133ca56a504c788c`, main, 27 September 2026 07:53:56UTC; unarchived.
The complete56-entry tree is a public evidence dossier that intentionally withholds production source
and private checkpoints. It is not a failed attempt at publishing a complete runnable system.
[Repository scope](https://github.com/Gowrav-M/satquery-ai-sih-2026-evidence/tree/77042af4db679f62b1657b86133ca56a504c788c).

Published strengths include explicit provenance/model manifests, task-specific benchmark summaries,
learned/deterministic/hybrid CDVQA ablations, calibration analysis and a documented policy to return
null confidence when uncalibrated. The dossier reports RSVQA-LR29.40% on500items, CDVQA59% on200
image-question cases (hybrid versus58% learned-only), and DLT0.6907mIoU on3,000tiles. These tasks and
denominators differ from ours. [Methodology](https://github.com/Gowrav-M/satquery-ai-sih-2026-evidence/blob/77042af4db679f62b1657b86133ca56a504c788c/benchmark-results/benchmark_notes.md),
[CDVQA summary](https://github.com/Gowrav-M/satquery-ai-sih-2026-evidence/blob/77042af4db679f62b1657b86133ca56a504c788c/benchmark-results/CDVQA_summary.json).

Their reported calibration metrics are a useful research dimension; we cannot erase that advantage
by counting our features. Conversely, summary JSON and screenshots do not let us rerun their private
pipeline or verify every claim. Category totals in the public RSVQA summary cover499rather than500
items; complete per-row predictions would be needed to reconcile that detail, not an accusation of
invalid results. Their VRSBench and private ISRO evaluations are explicitly not proved.
[RSVQA summary](https://github.com/Gowrav-M/satquery-ai-sih-2026-evidence/blob/77042af4db679f62b1657b86133ca56a504c788c/benchmark-results/RSVQA_summary.json).

Verdict: a serious evidence/validation comparator. Our public executable source is more inspectable;
our local terrain/exposure research is broader. We cannot rank private runtime quality or infer that
our full-split CDVQA numbers beat their200-case hybrid without matched inputs and scoring.

## Anindya-Dev/satquery-sih-final

Pin: `e72948f0c82140db0599fae4f7dedf1d8a6f20c9`, main, 11 September 2026 21:55:26UTC; unarchived.
The tree contains genuine task-spec schemas, deterministic/neural routing code, training-data
preparation, LoRA training scripts and router tests. A failing local-model load falls back to the semantic
parser; adapter metadata alone does not demonstrate successful neural inference.
[Router implementation](https://github.com/Anindya-Dev/satquery-sih-final/blob/e72948f0c82140db0599fae4f7dedf1d8a6f20c9/task_router/inference/router_engine.py).

The inspected application main is explicitly a placeholder. The SAR flood function literally returns
False; the optical/evidence/segmentation files in the tree are similarly small scaffolding. Thus a useful
router prototype exists, but the inspected default branch does not demonstrate an end-to-end satellite
analysis application. The name“final”is not proof of an official freeze.
[Application entry](https://github.com/Anindya-Dev/satquery-sih-final/blob/e72948f0c82140db0599fae4f7dedf1d8a6f20c9/app_platform/backend/app/main.py),
[flood placeholder](https://github.com/Anindya-Dev/satquery-sih-final/blob/e72948f0c82140db0599fae4f7dedf1d8a6f20c9/vision_pipeline/sar/flood_detection.py).

Verdict: our verified application is substantially further along than this public application snapshot;
no inference about another private branch or team submission is justified.

## Vivek-Maheshwari-07/SatQuery-AI-Research_SIH_2026

Pin: `b24c6d42348305413f394cb5341f16f93635a0bd`, main, 27 September 2026 16:53:47UTC.
The README describes a research-only repository, but the current tree also includes an actual Backend
and Frontend. Therefore the root README alone is insufficient to characterize it.
[Current tree](https://github.com/Vivek-Maheshwari-07/SatQuery-AI-Research_SIH_2026/tree/b24c6d42348305413f394cb5341f16f93635a0bd).

The executable LangGraph validates and produces typed single-image/change/cross-modal plans. Those
Layer2nodes terminate the graph; model execution Layer3is still pending in the implementation-status
document. This is real structured planning work, not measured specialist execution.
[Graph](https://github.com/Vivek-Maheshwari-07/SatQuery-AI-Research_SIH_2026/blob/b24c6d42348305413f394cb5341f16f93635a0bd/Backend/app/graph/builder.py),
[implementation status](https://github.com/Vivek-Maheshwari-07/SatQuery-AI-Research_SIH_2026/blob/b24c6d42348305413f394cb5341f16f93635a0bd/Backend/docs/2_IMPLEMENTATION_STATUS.md).

Verdict: our closed inference/evidence workflows are further along than the inspected execution layer.
Their research plans are not evidence of final metric performance; this may be a companion research
repo rather than the team's complete submission.
