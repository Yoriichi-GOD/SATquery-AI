# Evaluation protocol v1 - frozen 2026-10-20

Status: rules frozen before new experiments. No new training or accuracy evaluation authorized by this document. This is a prospective protocol, not a claim of complete PS26167 compliance. Source identity is recorded in EVALUATION_FREEZE_20261020.json; the working tree is dirty and HEAD alone is insufficient.

## Definition of done for step 1

- Preserve historical predictions, checkpoints and reports unchanged.
- Re-run current software regression checks and close the bounded CDVQA browser acceptance flow.
- Register existing evidence, exposure and remaining blockers.
- Freeze scoring, candidate selection, comparison and reporting rules before model changes.
- Do not call missing acceptance data, clean GPU restoration, or full requirement coverage complete.

## Scope and evidence tiers

Follow paired_lab/ORIGINAL_PROBLEM_STATEMENT.txt: adapted remote-sensing models; single-image VQA plus description or grounding; temporal analysis; paired optical/SAR extraction; input validation, routing, visual evidence, confidence information and observable execution trace. BigEarthNet.txt-specific adaptation and prescribed sensor validity are separate evidence gaps. Generic PNG/JPEG dataset membership is not authenticated by the app.

Maintain separate evidence tiers: (1) software/unit tests including mocks; (2) real development-input execution; (3) historical benchmark scores; (4) prospective unseen acceptance. Never combine these into an overall accuracy claim. Do not combine IoU, VQA accuracy, caption scores and F1 without the external judging protocol's specified normalization and weights.

## Baseline and exposure register

| Track | Fixed historical reference | Exposure / limitation |
| --- | --- | --- |
| CDVQA | docs/CDVQA_FINAL_REPORT.md; paired_lab/evidence/cdvqa-trained-20260928 | Official Train 65,967 questions/1,600 pairs; Val 16,441/400. Test1 39,686 questions and Test2 31,036 share 968 pairs and overlap questions. Prior inspection of 12 pairs disclosed. All published tests are now exposed; no new pristine holdout claim. |
| Water | BENCHMARK_REPORT.md and existing water reports | 90 test chips and 15 Bolivia chips already evaluated/replayed. Bolivia is no longer unseen. Official test event overlap limits geographic generalization. |
| Temporal masks | Existing selected 100 LEVIR-MCI pairs | Selected 50 changed/50 unchanged; inherited Change-Agent checkpoint. Not an independently sampled population or new model contribution. |
| VQA/description | paired_lab/evidence/public-benchmarks-20260927; IMPROVEMENT_AUDIT.md | VRSBench 45-question diagnostic on 12 reused images: raw 0/45 whole-response exact matches, 42 completed, 3 refused. Not 0% semantic accuracy. RSVQA 32-question diagnostic is not full prescribed split. |
| Land cover | Existing BIFOLD fixture report | 12 narrow fixtures; not broad sensor validation. |
| Official sensor pairs | docs/OFFICIAL_SAMPLE_FINAL_REPORT.md | Disjoint inspected optical/SAR scenes; corresponding paired inputs and task references unavailable. |

No new test split is manufactured by moving previously inspected examples into another folder. Before unseen acceptance, record dataset revision/license, scene/event IDs, input hashes, split membership, exclusion rules, known exposure and annotation provenance. Exact-content duplicate checks do not prove geographic independence. Identify overlapping footprints and events where metadata permits; mark unresolved independence explicitly.

## Candidate selection and experiment budget

Use official training data for optimization and official validation for selection. Keep test outcomes out of checkpoint/hyperparameter selection. A later experiment motivated by published test weaknesses is transparently benchmark-informed; preserve that exposure history.

Each experiment requires a versioned manifest BEFORE execution: hypothesis, changed variable, baseline, data/label budget, splits and hashes, model/encoder IDs and hashes, preprocessing, software versions, seeds, optimizer/schedule, selection metric, maximum epochs/patience, inference settings, hardware, planned comparisons and resource ceiling. Exact compute ceiling is required in each experiment manifest; no blanket training authorization is provided here.

For the first CDVQA spatial-resolution experiment, retain existing training settings except the declared feature-grid variable; select checkpoints by validation OA, breaking ties by earlier epoch. Primary comparison is paired validation OA; AA and eight per-type accuracies are mandatory secondary metrics. Use seeds 20260928, 20260929, 20260930 for confirmation, with matched baseline runs; a single-seed pilot is exploratory. Freeze a separate manifest before any change to this selection rule. Do not run multiple unregistered variants and report only the winner.

Report all attempted configurations, failed runs and resources. Freeze the selected candidate and evaluator hashes before final test execution. Existing historical evaluation scripts write to fixed evidence paths and are NOT to be rerun for new experiments without separate output-path support. New evidence directories must not overwrite historical runs.

## Metric rules

### CDVQA

Use active official questions, the frozen 19-class vocabulary and exact answer-class equality. OA denominator includes every eligible question; errors/refusals count as unsuccessful for end-to-end accuracy. Separately report conditional model accuracy, completion rate and refusal rate. AA is the unweighted mean across all eight official types. Report Test1/Test2 independently; never pool their shared imagery. Publish paired, question-only and fixed unrelated-pair controls. Temporal swapping requires question/label-consistent controls and is not an automatic augmentation.

Report paired gains and 95% paired scene-bootstrap intervals (1,000 resamples, fixed bootstrap seed 20261020), preserving questions within scenes. Show seed variability separately; do not treat repeated seeds or individual questions as independent scenes. Preserve the existing 12-pair exclusion analysis as historical context, not a fresh acceptance set. No substring scoring or post-hoc answer aliases.

### Water / masks / land cover

Retain official label encoding, valid-data masks, thresholds and denominators from the versioned baseline evaluator. Water primary metric: pooled valid-pixel IoU; also report per-event/per-scene IoU, precision, recall and fixed SAR/optical/joint results. Report undefined empty-union cases and counts explicitly according to the baseline evaluator; do not silently exclude them. Bootstrap at scene/event level as supported by the sampling design, never independent pixels. Few events cannot support broad geographic confidence claims.

A proposed quality selector uses only inference-available inputs, never reference labels or an oracle best modality. Compare against each fixed modality and a simple predeclared quality heuristic. Grounding requires its own box/mask protocol with IoU and accuracy at a predeclared threshold; detection category matching is not automatically referring-expression grounding. Land-cover reporting must fix label mapping and thresholds and include micro/macro F1. Do not compare those numbers with water IoU.

### Open-ended answers and descriptions

Keep original raw outputs and historical exact-match scores. Any retrospective semantic analysis is a separately labelled result. Before scoring, freeze dataset IDs, questions, references, allowed aliases, scorer version and rubric. A correct keyword inside a contradiction fails. Missing answers and refusals remain in the denominator. Report ambiguity/disputed references separately, with both all-case and adjudicated outcomes; never silently repair references to favor predictions.

Rubric: answer correctness (correct/partial/incorrect/refused), supported factual claims, unsupported claims, contradictions and material omissions. Score atomic claims and report counts alongside rates. Two independent human reviewers and documented adjudication are required for an independent factuality claim; assistant-only review remains a diagnostic. Freeze precise task-specific scoring examples and aliases before that evaluation, since this framework alone is not a ready-made semantic scorer.

### Reliability and performance

Fit calibration and refusal thresholds only on validation data. Report Brier score, calibration bins fixed in the experiment manifest, risk/coverage curves, all-case correctness and completion. A refusal-induced increase in answered-only accuracy is not a raw model gain.

For a latency experiment, record model initialization separately from warm inference and full upload-to-evidence latency; measure 5 cold runs and 30 warm sequential runs on the same fixed development input list. Report median/p95, peak memory, hardware and all excluded stages. Concurrency requires a separate test. Cache keys include exact input bytes, model and preprocessing identity. No cross-hardware speedup claims.

## Promotion gate

For a model-quality claim: the predeclared primary metric improves consistently across confirmation seeds, paired uncertainty is reported, and the paired 95% interval for the primary gain excludes zero before calling the gain established. Secondary regressions remain visible. For initial CDVQA screening, a drop greater than 1 percentage point in AA or any per-type accuracy blocks automatic promotion and requires an explicit tradeoff decision; these are engineering guardrails, not statistical laws. Latency/memory limits must be set in the experiment manifest before running.

Software boundary tests, evidence integrity and required refusals must pass. A candidate may improve a benchmark yet remain unapproved for serving. No outcome is called sensor-general or operationally validated without appropriate paired sensor data. No statistically unresolved gain is marketed as superiority. Protocol amendments receive a new version, rationale and exposure disclosure; never rewrite v1 after seeing outcomes.

## Outstanding gates

Fresh scene/event acceptance manifest and labels: NOT AVAILABLE / not frozen here.
Independent description adjudicators and task-specific rubric examples: NOT ASSIGNED.
Full prescribed grounding evaluation: NOT EXECUTED.
Clean GPU model restoration and inference: NOT VERIFIED in the isolated CPU environment.
Paired Cartosat-2S/RISAT task evaluation: BLOCKED on corresponding inputs and references.
Publication/deployment: not part of this step.

These do not prevent a clearly labelled validation-only development experiment. They prevent claims of unseen acceptance, complete requirement coverage or production readiness.