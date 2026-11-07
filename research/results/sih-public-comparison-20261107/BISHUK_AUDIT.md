# Public source audit: bishuk-dev/SIH-26167-SATQuery

Audit date: 2026-11-07. Scope: current public default-branch source and small committed evidence artifacts. This is a read-only source inspection; no competitor code, tests, models, notebooks, training, deployments, or hosted UI were executed. No repository was cloned and no model/data packages were downloaded.

## Snapshot and freeze status

| Field | Live observation |
| --- | --- |
| Repository | `bishuk-dev/SIH-26167-SATQuery`, public |
| Default branch / audited HEAD | `main` / `e260c9f41eb327832325db5d7bb505b27f2b4e78` |
| HEAD commit timestamp | 2026-09-10T23:01:06Z |
| HEAD description | Merge pull request #5, Frontend dev |
| Repository pushed / updated timestamps | 2026-09-10T23:10:06Z / 2026-09-11T12:50:10Z |
| Archived / disabled | false / false |
| Public release collection | empty |
| Public tag refs | empty array from `git/matching-refs/tags/` |
| Recursive tree | 538 entries; `truncated: false` |

These fields were read from the [repository metadata][metadata], [branch collection][branches], [HEAD commit][commit], [release collection][releases], [tag-ref namespace][tags], and [recursive tree][tree]. The ordinary tags endpoint was rejected by the connector; the allowed Git matching-refs endpoint succeeded.

**This is an inactive public snapshot, not a verified frozen project.** No explicit repository-wide freeze was established by this inspection. The source freezes particular model registrations and experiment contracts, which is a narrower claim than freezing all development. Archive-named branches also do not make the repository archived. [Model registry][models]; [branches][branches].

## Decision-useful conclusion

This is a substantial reference implementation, not merely a concept README. Its current source contains a real FastAPI transport, deterministic query interpretation and planning, registered tool execution, persistent jobs, immutable artifacts, inference services, and test files. However, the integrated natural-language execution path is much narrower than the broad research architecture: the planner currently has only SAR change localization and SAR change followed by area measurement policies. This supports a comparison of specific capabilities and evidence quality; it does not support a universal claim that either system is “far ahead.” [API initialization][main]; [planner][planner]; [adapter implementations][adapters].

The strongest public evidence here is its controlled, provenance-rich optical/SAR **land-cover classification** experiment work and its deliberate abstention/input-contract boundaries. That evidence must not be relabelled temporal VQA, flood segmentation, exposure accuracy, or a general autonomous agent benchmark. [Multisensor closeout][multiclose]; [joint validation][joint]; [temporal closeout][temporalclose].

## Executable paths: strengths and boundaries

| Area | What the inspected source actually implements | Boundary |
| --- | --- | --- |
| Query routing | `DeterministicQueryInterpreter` normalizes text and applies finite lexical rules. `BoundedPlanner` validates tool/input/parameter bindings, dependencies and hashes. | Deterministic routing; no autonomous model-driven planning/replanning loop is established. Only two planner policies are present: SAR change, and SAR change → area. [Interpreter][interpreter]; [planner][planner]. |
| Tool execution | Code-owned constructors cover SAR change, mask area and diagnostic mask agreement; the engine orders plan steps and checks registered adapters. Source assets and mask assets are hash-checked. | A registry entry or library primitive is not automatically an end-to-end routed capability. [Tools YAML][toolyaml]; [adapters][adapters]; [engine][engine]. |
| Temporal/SAR analytics | Explicit dB absolute differences or linear-power absolute log-ratios, named polarizations, nonfinite handling and explicit threshold. The adapter requires ordered distinct observations, matching SAR semantics, common grid, sensor identity and georeference. | The emitted phenomenon is `sar_backscatter_change`, `symmetric_change`, not a learned semantic flood mask. [SAR formulas][sar]; [SAR adapter][adapters]. |
| Geospatial foundation | Common-grid preparation hash-checks sources and can produce mask-aware reprojection derivatives; source bytes are preserved. | This is a library implementation. The backend contract explicitly marks automatic common-grid preparation, spectral indices, temporal difference and threshold workflows NOT_IMPLEMENTED as backend capabilities. [Temporal implementation][temporal]; [backend contract][contract]. |
| Single-image VQA | A real lazy local Transformers SmolVLM-256M backend loads a pinned revision, checks checkpoint SHA-256 and performs deterministic generation. It emits structured provenance and explicit domain-shift warnings. | Generic baseline on a display derivative, not remote-sensing-adapted spectral reasoning. SAR receives an additional “not specialized” warning. There is no calibrated answer confidence. [VQA service][vqa]; [model registry][models]. |
| Optical/SAR model work | Frozen BIFOLD S1-only, S2-only and 12-channel joint registrations; a guarded validation runner checks channel/class order, exact checkpoint identity, materialization packages and manifest hashes. | These are land-cover experiment lanes, not proof of accessible joint inference in the canonical query API. [Models][models]; [joint evaluation runner][jointrunner]. |
| Learned temporal/flood specialists | The phase closeout explicitly keeps ChangerEx, Chg2Cap and STURM blocked/unpromoted; no learned-specialist canonical evaluation ran. | No completed learned structural-change, change-captioning or flood-specialist benchmark is established by that closeout. This is an explicit recorded limit, not a negative inferred from silence. [Temporal closeout][temporalclose]. |
| User workflow | The main frontend uploads one selected GeoTIFF and submits its one backend-issued observation ID to the canonical query endpoint. | Its main landing flow cannot itself supply the two observations required for temporal or optical/SAR pair analysis. The integration report acknowledges this remaining product work. [HomePage source][home]; [single-file input][input]; [integration report][integration]. |

### Two current integration observations

1. **Learned experiment success is separated from canonical backend availability.** `create_app` calls `load_runtime_capabilities(tool_registry, model_registry=model_registry)` without either a model root or model readiness probe. The registry code sets model-backed capabilities to `UNAVAILABLE_RUNTIME` when those inputs are absent; its known runtime task allowlist contains only single-image VQA and text-guided grounding. Thus committed BIFOLD validation artifacts do not establish a runnable canonical BIFOLD query path. Legacy VQA and grounding routes separately instantiate services, so it would also be wrong to claim no model inference code exists. [Initialization lines 98–102 and 155–165][main]; [readiness derivation][toolcode].

2. **Source-derived NoData risk, not a reproduced failure.** The SAR execution adapter reads each raster band with `dataset.read(band_index)` and does not propagate `read_masks` or numeric NoData into the analytics call. The dB scorer masks nonfinite numbers only; the linear scorer additionally rejects negative values. A finite NoData sentinel or a masked finite pixel could therefore be counted as valid change. The inspected SAR adapter tests use no-NoData metadata; the SAR formula tests cover NaN and negative linear power. This warrants a focused regression before trusting uploaded-raster area results. It has **not** been reproduced by executing this project. The separate grid-reprojection library does contain mask-aware handling, so the issue is this execution handoff rather than an absence of masking everywhere. [Adapter lines 168–184, 280–285][adapters]; [SAR validity logic][sar]; [adapter tests][adaptertests]; [SAR tests][sartests]; [mask-aware reprojection][temporal].

## Committed evaluation artifacts

These are repository-authored records inspected at the audited HEAD. I did not rerun their models, recalculate all predictions, independently verify external package/checkpoint bytes, or audit the full large data manifests. Revisions, hashes, denominators and run environments are recorded in the linked artifacts.

| Lane | Reported result | Correct interpretation |
| --- | --- | --- |
| SmolVLM Phase 2A RSVQA-LR smoke test | 6 questions / 3 scenes; normalized exact match 0.0; majority-answer baseline 0.6667 | Tiny baseline diagnostic, not a publishable VQA estimate or proof of every later candidate's performance. [Result artifact][vqaresult]. |
| Grounding DINO final observational test | 16 references / 8 scenes; mean IoU 0.17385757; accuracy at IoU 0.5 = 0.1875; 2 no-detections | A real committed small held-out result, with limited grounding quality and denominator. It is not the same metric as classification mAP. [Final metrics][groundresult]. |
| Official BIFOLD S1 validation | 3,000 samples; macro AP 0.64300838; micro F1 0.65214921; macro F1 0.54543673 | Frozen validation-only multilabel land cover. [Closeout][multiclose]. |
| Official BIFOLD S2 validation | 3,000 samples; macro AP 0.74203215; micro F1 0.73258224; macro F1 0.64528435 | Primary optical control for the joint comparison. [Closeout][multiclose]. |
| Official BIFOLD S1+S2 validation | 3,000 samples; macro AP 0.74251037; micro F1 0.73407500; macro F1 0.63903236 | Versus S2: macro AP +0.00047822 (+0.0478 percentage points), micro F1 +0.00149276, macro F1 −0.00625199. This is marginal and mixed, not broad fusion superiority. [Joint result][joint]; [paired report][paired]. |
| S2 classifier-head adaptation | Reported validation macro AP 0.74965520 | One seed; secondary comparison; not a statistical replication or evidence SAR is unnecessary. [Adaptation closeout][adaptclose]; [multisensor closeout][multiclose]. |
| Deterministic temporal closeout | Formula/grid/measurement lanes: 5 + 4 + 2 synthetic checks; overall learned-specialist phase BLOCKED | Arithmetic and fixture evidence, not real-scene temporal or flood accuracy. [Temporal closeout][temporalclose]. |

The multisensor report records joint improvement over S2 in 12 class APs and degradation in 7; paired label “rescues” 1,494 versus harms 1,488. It explicitly warns that output comparisons do not establish causal attribution to SAR. Its final test remains sealed/unexecuted, with no joint adaptation, missing-modality, cloud-simulation or final-test experiment reported. These candid limits are a strength of its evidence reporting. [Paired complementarity][paired]; [closeout][multiclose].

The Phase 2B/2C tree contains training/evaluation code, manifests and a question-prior diagnostic, but no committed final comparison result was established by this audit. The diagnostic itself says Phase 2B comparison predictions are unavailable there. Do not report the 6-example Phase 2A smoke result as the performance of an adapted Phase 2B/2C model. [Phase 2B definition][vqab]; [Phase 2C diagnostic][vqadiag]; [complete tree][tree].

## Tests, CI and observed-vs-run distinction

The complete recursive tree contains **64 Python `test_*.py` files**, including analytics, execution, persistence, API integration, model-adapter and evaluation-harness tests. This count is files, not collected tests or passes. For example, an integration test constructs two 4×4 SAR rasters, submits SAR-area analysis, waits for the worker, asserts 0.16 ha and checks the persisted evidence edge. Other tests exercise prompt-injection-like text, queue failure, model unavailability and structured evidence. VQA endpoint tests inject a stub backend, which validates the API/evidence contract but not actual model accuracy. [Tree][tree]; [query submission tests][querytests]; [VQA tests][vqatests].

The Actions API returned all **51** listed workflow runs (one page requested with 100), all named “pages build and deployment.” The latest run at the audited SHA reports success. No `.github/` files appear in the complete tree. Accordingly this audit establishes a published Pages pipeline, **not** a passing Python/model CI result. It cannot rule out private/local CI outside the inspected public surface. [Workflow runs][runs]; [latest Pages run][pages]; [tree][tree].

The first-party frontend integration report claims build/lint and 22 backend integration tests passed and describes browser verification with generated data. It also explicitly says the exercised analysis ended in MODEL_UNAVAILABLE/ABSTAIN and did not demonstrate successful model inference. Those are authored historical claims, not checks rerun for this audit. [Integration report][integration].

## Fair comparison rule

Compare SATquery with this repository along separate axes: shipped paired-image workflow, routed tool breadth, benchmark task/denominator, held-out policy, scientific limits, and current runnable evidence. A stronger deterministic flood/water workflow or larger locally passing suite can establish an advantage in that lane. It does not erase the competitor's controlled optical/SAR classification evidence, and neither classification results nor test counts establish universal scientific superiority. No shared benchmark execution was conducted here.

[metadata]: https://api.github.com/repos/bishuk-dev/SIH-26167-SATQuery
[branches]: https://api.github.com/repos/bishuk-dev/SIH-26167-SATQuery/branches
[commit]: https://github.com/bishuk-dev/SIH-26167-SATQuery/commit/e260c9f41eb327832325db5d7bb505b27f2b4e78
[releases]: https://api.github.com/repos/bishuk-dev/SIH-26167-SATQuery/releases
[tags]: https://api.github.com/repos/bishuk-dev/SIH-26167-SATQuery/git/matching-refs/tags/
[tree]: https://api.github.com/repos/bishuk-dev/SIH-26167-SATQuery/git/trees/e260c9f41eb327832325db5d7bb505b27f2b4e78?recursive=1
[models]: https://github.com/bishuk-dev/SIH-26167-SATQuery/blob/e260c9f41eb327832325db5d7bb505b27f2b4e78/models/registry.yaml
[main]: https://github.com/bishuk-dev/SIH-26167-SATQuery/blob/e260c9f41eb327832325db5d7bb505b27f2b4e78/apps/api/app/main.py#L98-L165
[interpreter]: https://github.com/bishuk-dev/SIH-26167-SATQuery/blob/e260c9f41eb327832325db5d7bb505b27f2b4e78/satquery/agent/interpreter.py
[planner]: https://github.com/bishuk-dev/SIH-26167-SATQuery/blob/e260c9f41eb327832325db5d7bb505b27f2b4e78/satquery/agent/planner.py#L104-L162
[adapters]: https://github.com/bishuk-dev/SIH-26167-SATQuery/blob/e260c9f41eb327832325db5d7bb505b27f2b4e78/satquery/execution/adapters.py
[engine]: https://github.com/bishuk-dev/SIH-26167-SATQuery/blob/e260c9f41eb327832325db5d7bb505b27f2b4e78/satquery/execution/engine.py
[toolyaml]: https://github.com/bishuk-dev/SIH-26167-SATQuery/blob/e260c9f41eb327832325db5d7bb505b27f2b4e78/satquery/registry/tools.yaml
[toolcode]: https://github.com/bishuk-dev/SIH-26167-SATQuery/blob/e260c9f41eb327832325db5d7bb505b27f2b4e78/satquery/registry/tools.py#L300-L337
[sar]: https://github.com/bishuk-dev/SIH-26167-SATQuery/blob/e260c9f41eb327832325db5d7bb505b27f2b4e78/satquery/analytics/sar.py#L111-L178
[temporal]: https://github.com/bishuk-dev/SIH-26167-SATQuery/blob/e260c9f41eb327832325db5d7bb505b27f2b4e78/satquery/analytics/temporal.py
[contract]: https://github.com/bishuk-dev/SIH-26167-SATQuery/blob/e260c9f41eb327832325db5d7bb505b27f2b4e78/experiments/phase5_backend/backend_contract.yaml
[vqa]: https://github.com/bishuk-dev/SIH-26167-SATQuery/blob/e260c9f41eb327832325db5d7bb505b27f2b4e78/satquery/inference/vqa.py
[jointrunner]: https://github.com/bishuk-dev/SIH-26167-SATQuery/blob/e260c9f41eb327832325db5d7bb505b27f2b4e78/ml/evaluation/phase5a_bifold_joint.py#L118-L190
[temporalclose]: https://github.com/bishuk-dev/SIH-26167-SATQuery/blob/e260c9f41eb327832325db5d7bb505b27f2b4e78/experiments/phase4_temporal_analytics/PHASE_4_CLOSEOUT.json
[multiclose]: https://github.com/bishuk-dev/SIH-26167-SATQuery/blob/e260c9f41eb327832325db5d7bb505b27f2b4e78/experiments/phase3_multisensor_closeout.json
[joint]: https://github.com/bishuk-dev/SIH-26167-SATQuery/blob/e260c9f41eb327832325db5d7bb505b27f2b4e78/experiments/phase4_bigearthnet_multisensor/phase5a/results/phase5a_joint_validation_result.json
[paired]: https://github.com/bishuk-dev/SIH-26167-SATQuery/blob/e260c9f41eb327832325db5d7bb505b27f2b4e78/experiments/phase4_bigearthnet_multisensor/phase5a/results/phase5a_complementarity_report.json
[adaptclose]: https://github.com/bishuk-dev/SIH-26167-SATQuery/blob/e260c9f41eb327832325db5d7bb505b27f2b4e78/experiments/phase4_bigearthnet_multisensor/phase4f_closeout.json
[vqaresult]: https://github.com/bishuk-dev/SIH-26167-SATQuery/blob/e260c9f41eb327832325db5d7bb505b27f2b4e78/experiments/phase2a_smolvlm_rsvqa_lr/results.json
[groundresult]: https://github.com/bishuk-dev/SIH-26167-SATQuery/blob/e260c9f41eb327832325db5d7bb505b27f2b4e78/experiments/phase3b_grounding_threshold_calibration/results/final_test_metrics.json
[vqab]: https://github.com/bishuk-dev/SIH-26167-SATQuery/blob/e260c9f41eb327832325db5d7bb505b27f2b4e78/experiments/phase2b_smolvlm_rsvqa_lr/README.md
[vqadiag]: https://github.com/bishuk-dev/SIH-26167-SATQuery/blob/e260c9f41eb327832325db5d7bb505b27f2b4e78/experiments/phase2c_visual_contrast/diagnostic.json
[home]: https://github.com/bishuk-dev/SIH-26167-SATQuery/blob/e260c9f41eb327832325db5d7bb505b27f2b4e78/apps/web/src/pages/HomePage.tsx#L30-L39
[input]: https://github.com/bishuk-dev/SIH-26167-SATQuery/blob/e260c9f41eb327832325db5d7bb505b27f2b4e78/apps/web/src/components/ui/ruixen-moon-chat.tsx#L110-L130
[integration]: https://github.com/bishuk-dev/SIH-26167-SATQuery/blob/e260c9f41eb327832325db5d7bb505b27f2b4e78/docs/FRONTEND_BACKEND_INTEGRATION_REPORT.md
[querytests]: https://github.com/bishuk-dev/SIH-26167-SATQuery/blob/e260c9f41eb327832325db5d7bb505b27f2b4e78/tests/integration/test_query_submission.py#L145-L218
[vqatests]: https://github.com/bishuk-dev/SIH-26167-SATQuery/blob/e260c9f41eb327832325db5d7bb505b27f2b4e78/tests/inference/test_vqa.py
[adaptertests]: https://github.com/bishuk-dev/SIH-26167-SATQuery/blob/e260c9f41eb327832325db5d7bb505b27f2b4e78/tests/execution/test_adapters.py
[sartests]: https://github.com/bishuk-dev/SIH-26167-SATQuery/blob/e260c9f41eb327832325db5d7bb505b27f2b4e78/tests/analytics/test_sar.py
[runs]: https://api.github.com/repos/bishuk-dev/SIH-26167-SATQuery/actions/runs?per_page=100
[pages]: https://github.com/bishuk-dev/SIH-26167-SATQuery/actions/runs/34540208112
