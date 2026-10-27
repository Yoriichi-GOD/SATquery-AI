# Scope and verification audit — 2026-10-19

Governing source: [original statement](../paired_lab/ORIGINAL_PROBLEM_STATEMENT.txt). Single-image understanding is mandatory; paired cross-modal and temporal reasoning remain central. This audit records implementation and evidence separately. It does not declare full compliance.

| Requirement | Implemented path | Existing evaluation / protocol | Remaining gap |
| --- | --- | --- | --- |
| Remote-sensing adaptation | Remote-sensing Qwen checkpoint, local rural/urban LoRA, trained water and CDVQA models | Training/source manifests and frozen CDVQA release; public/open-data adaptation permitted by saved statement | Full reproducible adapter release and dataset-rights review; BigEarthNet.txt image-text adaptation specifically not demonstrated |
| Optical VQA | Qwen single-image route | RSVQA-LR diagnostic: 32 reused-image questions, 12 whole-response exact matches; labels retained | Not full prescribed split or semantic accuracy; upstream exposure unknown |
| Caption/description | Same VQA route | 12 VRSBench images reviewed with references by coding assistant; omissions and disputed identities retained | No independent adjudication, caption metric or measured completeness improvement |
| Grounding | DINO/SAM for bounded categories | Functional checks; image/result artifacts | No prescribed VRSBench grounding IoU/localization benchmark; water-body referring expressions unsupported |
| SAR baseline | Sentinel-1 scene classification | Real single-SAR smoke; land-cover fixture labels | Scene classification is not general SAR VQA/captioning/grounding; RISAT transfer unsupported |
| Bi-temporal change | MCI masks/caption | 100 selected LEVIR-MCI test pairs, 50 changed/50 unchanged; pooled road/building IoU; masks available | Caption factuality separate; subset exposure/independence limitations |
| Change VQA | Frozen 19-answer CDVQA classifier, explicit browser-mode API integration | Test-1: 39,686 questions; Test-2: 31,036; same 968 pairs; answer exact-class accuracy, question-only control and 12-pair exclusion analysis | CPU/browser integration is not new benchmark accuracy; arbitrary-scene generalization and weak ratio/ranking categories remain |
| Cross-modal extraction | Water SAR/optical/joint masks; BIFOLD three-path scene labels | Sen1Floods11 90 test chips and 15 Bolivia replay; pooled valid-pixel IoU. BIFOLD 12 narrow fixtures, micro-F1 | No universal fusion benefit; joint optical/SAR built-up region segmentation unavailable |
| Agentic orchestration | Bounded registry, input checks, dispatch, execution trace, originals and ZIP | Software boundary/regression tests plus real HTTP CDVQA run | Multi-step open-ended task combination unsupported; confidence scores uncalibrated |
| Official sensors | Cartosat ingestion/description; EOS-04 calibration checks | Existing source-hash/numerical/refusal tests and one optical real execution | Inspected optical/SAR scenes are disjoint; no actual co-registered official pair or task reference labels; semantic accuracy unproved |
| Input policy | TIFF/GeoTIFF, plus generic optical and explicit prepared-RGB CDVQA uploads | Input contracts tested | Statement limits PNG/JPEG to prescribed benchmarks; current app does not authenticate dataset membership. Full operational format compliance not claimed |

Evidence: [benchmark report](../BENCHMARK_REPORT.md), [public diagnostic](../paired_lab/evidence/public-benchmarks-20260927/README.md), [CDVQA report](CDVQA_FINAL_REPORT.md), [official-sample report](OFFICIAL_SAMPLE_FINAL_REPORT.md).

## Evaluation decision

Preserve the VRSBench raw 0/45 whole-response exact-match diagnostic (42 completed, 3 refused); it is not 0% semantic accuracy. The rows were not rescored, normalized anew or edited in this pass. No expensive benchmark was rerun and no training occurred. A retrospective semantic review would require a separately versioned protocol defining answer extraction, aliases, contradictions, unsupported extra claims and refusal denominator before application; mere presence of the reference word must fail contradictory answers. That analysis remains open rather than inventing a replacement score.

The next useful quality work is independent description/grounding evaluation on the prescribed protocol and fresh inputs, after resolving runtime and data access. Additional water/temporal reruns would not close those gaps. Official paired evaluation requires genuine corresponding sensor inputs and appropriate references; changing metadata cannot create them.

## Development routing evidence

Before: 'Describe this area' and 'What is visible in this area?' refused as measurements. After: bounded whole-question description forms select VQA. Before: 'Where are the buildings in this image?' was not treated as a descriptive context question. After: explicit image-relative wording selects VQA. Physical-area requests, compound requests, explicit object outlines and forecasting retain their boundaries. Broad RGB comparisons already explain available choices and were left unchanged. Five added regression tests cover paraphrases and negative controls; all 113 software tests pass.

These are routing improvements, not demonstrated improvements to generated image answers. Existing 12-image description review still records omissions/unsupported context; model prompts were not changed without a real before/after image study. That portion remains open.

## CDVQA integration evidence

Choose Image pair, then Experimental CDVQA, upload two prepared RGB images, confirm correspondence/order/alignment and select an exact question. No arbitrary paraphrase is coerced. This explicit mode preserves existing MCI and spectral dispatch. New uploads are limited to one megapixel and preserve original bytes. Release identity, actual checkpoint/encoder hashes, preprocessing, uncalibrated scores, input hashes and limitations are exported.

Real HTTP run 3e4613dd10d84779ba090c984d8c0f63 completed in the isolated CPU environment with explicitly configured existing maintainer weights. It uploaded the previously inspected MCI test_000036 pair, answered the supported building-change question, rejected missing alignment and an unsupported question, and downloaded a CRC-checked ZIP containing both originals. This is development integration evidence, not CDVQA accuracy or clean public restoration of manual weights. Evidence: .runtime/repro-20261019/cdvqa-http. Six added tests cover dispatch, mixed modes, unsupported/compound requests, RGB, dimensions, alignment and unavailable assets.

Browser automation was disabled by Work settings. JavaScript syntax and HTTP integration passed; visual interaction/rendering remains unverified. Integration is therefore implemented and backend-verified, with the browser acceptance check still open.

## UI verification follow-up

Browser inventory again returned no enabled browser connections and the Work-settings restriction. No browser restriction was bypassed. A DOM-only check using isolated jsdom 26.1.0 found and closed a real integration defect: the existing custom picker captured options before asynchronous CDVQA questions arrived. The two new selectors now remain native labelled controls, so all loaded templates remain selectable. Mode switching refreshes the existing modality labels and clears prior results/alignment confirmation. Replacing either input also clears alignment confirmation.

Executed `node scripts/check_cdvqa_dom.cjs`: passed dynamic template loading, selection-to-question copy, mode transitions, no duplicate options, alignment reset for either input, modality-label synchronization, and presentation of the saved real HTTP result (19 score rows, before/after views, limitations, evidence link). This script requires the isolated `.runtime/ui-check` jsdom installation and the real saved `.runtime/repro-20261019/cdvqa-http/verification.json`; it is a local integration check, not a clean CI-only test. Install its test dependency with `npm install --prefix .runtime/ui-check --no-audit --no-fund --package-lock=false jsdom@26.1.0` after reproducing the HTTP smoke.

JavaScript syntax and diff whitespace checks pass. All 113 Python tests still pass. DOM execution verifies application state and element contents, not CSS layout, screenshots, accessibility behavior in an actual browser or physical click-through. Those visual browser acceptance checks remain open. No new feature or benchmark score was added.


## Step 1 follow-up - 2026-10-20

The bounded CDVQA browser upload, refusal, inference, image-view and evidence-download checks now pass on the documented port 8767. This supersedes only the prior browser-unverified status above. See [closure evidence](STEP1_VERIFICATION_20261020.md) and [frozen evaluation protocol](EVALUATION_PROTOCOL_V1.md). No model accuracy claim changed; fresh acceptance data, full GPU restoration and other requirement gaps remain open.
