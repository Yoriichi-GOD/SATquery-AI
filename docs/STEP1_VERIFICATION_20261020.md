# Step 1 closure record - 2026-10-20

Outcome: evaluation rules and baseline identity frozen; bounded CDVQA browser integration verified. Full project acceptance remains incomplete. No model training, benchmark rescoring, source-feature changes, deployment or publication occurred.

## Executed checks

- Existing isolated Python 3.11 environment: 113 unittest checks passed in 2.323 seconds. Includes mocked and numerical checks, not 113 real-model accuracy tests. Non-failing rasterio/Affine deprecation warnings retained in tool output.
- JavaScript syntax check passed; existing check_cdvqa_dom.cjs passed dynamic templates, selection, mode switching, alignment reset, labels, saved real result, 19 scores and evidence link.
- Live in-app browser on http://127.0.0.1:8767: selected pair/CDVQA mode; uploaded tracked mci-test_000036 before.tif and after.tif using actual file choosers; selected the building-change template; missing-alignment request refused; confirmed alignment; real CPU run completed with answer yes.
- Browser run 8bf73ce1d9b9441eb675f16c693e907b: before/after views, all 19 uncalibrated scores, limitations and download were present. Expanded after image and closed dialog. Downloaded ZIP through the browser; CRC passed and both original files match tracked input bytes exactly.
- Unsupported question Count every changed car refused and cleared result/download links. Replacing the first file with a genuinely different file cleared alignment and result links. Selecting the identical file again did not trigger a change event; not classified as a replacement failure. Restored the correct ordered pair and completed another run for the screenshot.
- Retained evidence: .runtime/step1-20261020/browser-evidence.zip, browser-result.json, archive-verification.json. These ignored local artifacts are not supplied by a public clone.
- Screenshot of the final repeat run: .runtime/step1-20261020/browser-result.jpg. Specialist-only displayed timing is not end-to-end latency or a performance benchmark.

## Setup issue diagnosed

An initial temporary service on port 8877 loaded the page, but its POST requests were refused by the existing origin allowlist, which permits 8767. The older HTTP smoke did not send a browser Origin header and therefore could not catch this mismatch. Verification was moved to the documented port 8767; security checks were not relaxed. The initial 8877 process created for this task was stopped.

The acceptance service uses /var/tmp/satquery-repro-20261019/venv and SATQUERY_PAIRED_DIR=/var/tmp/satquery-step1-20261020/paired for new run storage. It uses existing maintainer CDVQA and encoder assets; this is not clean public restoration. Auxiliary single-image service was not started; its development/reliability endpoints returned 503 and are outside this bounded check. Responsive/mobile layouts and every other GUI workflow were not certified. The screenshot shows the current scrolled desktop layout, not a responsive-layout endorsement.

## Frozen deliverables

- EVALUATION_PROTOCOL_V1.md: evidence tiers, exposure register, exact-class metrics, denominators, validation-only selection, three confirmation seeds, controls, paired uncertainty, factuality-review requirements, latency methodology and promotion gates.
- EVALUATION_FREEZE_20261020.json: 22 source/protocol/historical-evidence SHA256 hashes, HEAD plus dirty-working-tree record, and observed checkpoint/encoder identities.

Definition-of-done assessment: historical evidence preserved; software checks passed; bounded browser flow passed; protocol and baseline identity frozen; outstanding dependencies explicitly registered. This closes the preparation and bounded integration scope, not all quality/acceptance gaps.

## Gates still open

1. A genuinely fresh scene/event acceptance manifest and corresponding labels. Existing evaluated datasets cannot be declared unseen again.
2. Independent factuality reviewers and task-specific frozen examples/aliases for semantic scoring.
3. Full prescribed VQA/grounding evaluation and stronger description-quality evidence.
4. Clean GPU restoration and real inference of all required specialists.
5. Corresponding Cartosat-2S/RISAT pairs and task references; the inspected official scenes are disjoint.
6. Full input-format/dataset-membership compliance and complete GUI workflow coverage.

Next permitted planning target: a small validation-only CDVQA spatial-detail experiment with a separate pre-run manifest and compute limit. No such training was executed in step 1. Do not claim unseen acceptance or expand features to hide these gaps.