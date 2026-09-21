# SATquery AI — Manifesto through September 9, 2026

Last updated: September 6, 2026.

## Our goal

Build a credible, working proof of concept for SIH26167: a remote-sensing assistant that accepts a satellite image and a natural-language question, uses a suitable specialist, and returns an answer with an understandable record of what actually ran.

By September 9, deliver one reliable single-image visual question-answering workflow, a measured baseline and adaptation experiment, a usable local demo, and a presentation grounded in evidence. A narrow working system is more valuable than unsupported claims about a complete platform.

## Where everything lives

- Central project planning folder: `C:\Users\nrgen\.codex\scratch\SATquery AI`.
- This plan: `manifesto.md` in that folder.
- Actual Python environment, GPU execution, downloaded checkpoint cache, and ML scripts currently run inside Ubuntu WSL2 on this same laptop. This is local computing, not a rented server or Colab session.
- Existing ML working directory: `/root/satquery` inside Ubuntu.
- Python environment: `/root/satquery/.venv`.
- Windows Explorer access to the ML directory: `\\wsl.localhost\Ubuntu\root\satquery`.
- Evaluation files: `/root/satquery/evaluation`.
- Windows copy of the evaluation and image review: `C:\Users\nrgen\.codex\visualizations\2026\09\05\01a072ef-1d2e-7520-8c5d-24411a4e24cd\satquery-evaluation`.
- Research outputs already staged: `C:\Users\nrgen\.codex\visualizations\2026\09\05\01a072ef-1d2e-7520-8c5d-24411a4e24cd\satquery-research`.

This document is the central index. Creating it does not move the existing environment, models, research, or evaluation. Keep the working Linux environment in place; add future project notes here and update this index when code or artifacts gain a new location. The Warscythe repository is a separate project and must not become SatQuery's source folder.

## Constraints

- Deadline: September 9, 2026. Confirm the precise college submission time and required deliverables separately.
- Main development runs on the laptop. Free Colab is an optional fallback, not a dependency for the demo.
- Previously checked hardware: RTX 5060 Laptop GPU with 8 GB VRAM, Ryzen 9 8940HX, approximately 23 GB usable system RAM.
- Work within measured memory limits. Do not assume that an inference fit proves that training will fit.
- Preserve the working environment rather than replacing its dependencies to match an older project blindly.
- Do not download full large datasets when a documented subset will support the experiment.

## What already works

- Local Ubuntu WSL GPU environment and forward/backward smoke checks completed in earlier setup.
- Selected specialist: `AdaptLLM/remote-sensing-Qwen2-VL-2B-Instruct`.
- Pinned checkpoint revision: `7f5dd71bf0f40c282193d50160e848a387a08ffe`.
- Local image-question inference works with the existing Qwen2-VL processor and model runner.
- Baseline runner: `/root/satquery/run_baseline.py`.
- Environment records: `/root/satquery/requirements-inference-tested.txt` and `/root/satquery/requirements-gpu-tested.txt`.

## First evaluation: completed, not a success claim

A fixed subset of the published RSVQA-LR test split contains 60 questions across 60 unique images. Selection used seed 26167 before model predictions were generated. Each category has 20 examples with balanced answer labels.

| Category | Strictly correct |
|---|---:|
| Presence | 10/20 |
| Comparison | 14/20 |
| Rural/urban | 0/20 |
| Total | 24/60 — 40% |

All 20 rural/urban outputs failed the requested single-label format. This score mixes format compliance and answer correctness; it is not evidence of zero rural/urban visual understanding. Some yes/no answers were also incorrect. The category-aware constant-label baseline on this balanced set is 50%, so the overall result is not yet evidence of useful benchmark performance.

Median model generation time was about 0.19 seconds per question; peak PyTorch allocated GPU memory was about 4.22 GiB. This is not end-to-end application latency or total GPU memory usage.

Scoring ignores case, collapses whitespace, and strips terminal punctuation, then requires exact equality. No substring matching or LLM judge. Generation was deterministic with a 16-token maximum; paragraphs can be truncated.

Reference labels are published dataset answers, not independently hand-verified truth. This small diagnostic is not the official full benchmark. Earlier exposure of the checkpoint to these images is unknown.

Files in `/root/satquery/evaluation`:

- `eval_v1.jsonl`: frozen question/image/reference-answer manifest.
- `manifest_metadata.json`: source, seed, hashes, and selection/scoring rules.
- `baseline_predictions.jsonl`: every prediction and timing.
- `baseline_summary.json`: scores and pinned model revision.
- `prepare_eval.py`: deterministic subset builder.
- `run_eval.py`: evaluation runner. It currently overwrites baseline result filenames, so preserve them before a subsequent run.

Manifest SHA-256: `69d15b5ed92c15e33f5e0a5ded5e2b18a6df2ed96567c159fdcaba3ead3a1699`.

Keep all official test images and overlapping source scenes out of adaptation. This subset is now an inspected diagnostic; use separate development images for prompt and implementation changes and reserve a fresh final evaluation for the final result.

## September 6 — Make the learning loop and vertical slice work

Deliverables:

1. Define the supported demo questions and input types. Start with single-image optical VQA. Clearly distinguish what the model can answer from tasks requiring other tools.
2. Prepare a bounded training subset and a separate development subset with a recorded source, license, image IDs, and answer schema. Check image and source-scene overlap against evaluation data.
3. Use development images to diagnose answer formatting and visual errors. Fix one shared inference/scoring protocol, then evaluate baseline and adapted models under the same protocol. Do not silently compare a newly prompted adapted model with the old baseline.
4. Run a small LoRA/PEFT training feasibility check, measuring GPU memory, loss, and whether the saved adapter reloads. If local training does not fit, try a smaller configuration or free Colab; preserve the local inference path.
5. If feasible, complete a first bounded adapter run and save its exact configuration and training data manifest. An improvement is an experiment outcome, not a promise.
6. Build the minimal path: upload image → ask question → run specialist → show answer and an execution record. Record model/adapter identity, processing time, and actual errors.

Nightly acceptance: a repeatable baseline run, documented data split, an adaptation feasibility result, and a working minimal inference path. Record unfinished items candidly.

## September 7 — Integrate and measure

Deliverables:

1. Complete or refine the first adaptation experiment using development data only.
2. Run the same evaluation protocol on preserved baseline and adapter. Report per-category scores, format failures, latency, memory, and representative failures.
3. Add a small, explicit task router. Route supported VQA to the specialist; clearly mark unsupported temporal, SAR, or grounding requests instead of fabricating execution.
4. Connect a simple local interface with input validation and clear loading/error states.
5. If GeoTIFF support is included, implement and test explicit RGB band selection and display conversion. A TIFF filename alone does not prove geospatial support; retain metadata and do not imply all bands enter an RGB model.

Acceptance: the UI reaches the real local model, the adapter can be enabled or disabled, and measured comparisons can be reproduced.

## September 8 — Freeze the demo and presentation evidence

Deliverables:

1. Freeze the preferred configuration based on development evidence. Keep the baseline available if adaptation is worse.
2. Run the reserved final evaluation once the configuration is fixed. Keep full outputs and report the sample size and limitations.
3. Prepare a small demonstration pack with known source images, expected behavior, and at least one honest limitation example. Label demonstration examples separately from evaluation results.
4. Prepare the six-slide SIH presentation using the prescribed structure: title; idea/solution; technical approach; feasibility/risks; impact; references. Verify the actual college submission requirements.
5. Complete the research decision note: checkpoint comparison, dataset formats, prior art, optical-SAR roadmap, and presentation sources. Existing research leads are not a finished report until consolidated.
6. Record a short fallback demo video and save the needed model, adapter, images, configuration, and launch instructions locally.

Acceptance: a rehearsable demo and an evidence-backed deck, with no dependence on a last-minute download.

## September 9 — Submit and demonstrate

Deliverables:

1. Perform a clean launch rehearsal using the saved instructions.
2. Check all submission fields, team details, PS ID, file format, and college cutoff time.
3. Export and inspect the final presentation PDF.
4. Submit the required artifacts before the confirmed cutoff and retain a copy/receipt.
5. Present what is implemented, what was measured, and what remains planned as separate statements.

Avoid architectural changes on submission day unless needed to fix a blocking failure.

## Definition of done

- A local user can submit a supported image and question and get a response from the actual specialist.
- The system exposes a truthful execution record and handles invalid input and unsupported tasks clearly.
- The baseline is preserved; adaptation settings, data, and outcomes are recorded, even if the adapter does not improve results.
- Evaluation separates training/development/test use and reports category-level failures as well as overall scores.
- The application can be started from written instructions, with a fallback recording available.
- The deck cites its models, datasets, and prior art and clearly separates implemented features from roadmap features.

## Scope boundaries and pitch

Not required for the first prototype: trained optical-SAR fusion, temporal change detection, accurate bounding-box grounding, unrestricted geospatial analysis, or a large autonomous multi-agent system.

Do not call an RGB overlay optical-SAR fusion. Do not generate confidence percentages or coordinates without a validated method. Do not promise improvements, disaster savings, or geographic generalization without measurements.

Existing remote-sensing assistants and agents already exist. Our defensible contribution must be demonstrated execution: a constrained local workflow, our documented adaptation experiment, transparent task handling, and reproducible evidence. A router or a Qwen wrapper alone is not a research novelty claim.

## Sources and next research references

- Selected model: https://huggingface.co/AdaptLLM/remote-sensing-Qwen2-VL-2B-Instruct
- First evaluation source: https://zenodo.org/records/6344334
- RSVQA project: https://rsvqa.sylvainlobry.com/
- VRSBench: https://github.com/lx709/VRSBench
- BigEarthNet.txt: https://huggingface.co/datasets/BIFOLD-BigEarthNetv2-0/BigEarthNet.txt
- Dataset loader reference: https://github.com/isaaccorley/torchrs

## Working agreement

Use this folder as the planning home. Update this manifesto when scope or measured results change. Keep source, evaluation, demo, and presentation paths discoverable here. Never replace an unsuccessful measurement with a success claim; use it to decide the next experiment.


## Build milestone — September 6

- Working app source now lives beside this manifesto: `server.py`, `web/`, `scripts/`, and `start.ps1`.
- Open the running app at http://localhost:8765. Launch/restart instructions are in `README.md`. The model still executes inside WSL on this laptop.
- Implemented image upload, pan/zoom, real local inference, loading stages, elapsed time, run JSON export, dark/light-gray themes, and an evaluation screen. Original decorative artwork is pending; references and decisions are in `design/`.
- Baseline mode is preserved. Experimental yes/no and rural/urban modes use the first saved adapter. They are explicit choices and do not claim support for SAR, temporal analysis or geospatial measurements.
- Prepared 720 training questions on 120 images and 60 development questions on 20 images from a separate source scene. Dataset details/hashes: `results/learning_manifest.json`; actual data: `/root/satquery/data`.
- Eight-step LoRA feasibility passed, including adapter reload, at 4.43 GiB peak PyTorch allocation.
- A fresh one-pass pilot then completed: development baseline 23/60 versus adapter 47/60; format failures 20 versus zero; peak allocation 4.45 GiB. Compact evidence: `results/pilot-v1.json`. This is a development comparison, not a final test result. Original held-out evaluation remains unchanged.
- Browser and API integration checks passed, including adapter-to-baseline switching. Saved evidence: `results/integration-check.json`.

Still open: original art assets, a broader reliability/error review, final untouched evaluation after the protocol is frozen, presentation and fallback recording, consolidated research report, and submission rehearsal.


### Completed 6 September: first measured remote-sensing workflow
Real Dehradun Sentinel-2 crop → retained GeoTIFF metadata → calibrated red/NIR NDVI → quality mask → aligned threshold overlay → projected area and raster/JSON exports. Results and limitations are in README.md and results/ndvi-integration.json. This is a deterministic spectral tool, not arbitrary grounding. Next: natural-language routing, final held-out adapter evaluation, bounded object grounding.

Calibration audit completed: double offset fixed using header-verified Collection 1 input. Earlier 620.09 ha is invalid; corrected NDVI >=0.5 area is 387.61 ha (14.79% of the crop). See results/calibration-audit.md.

Independent verification completed: separate TIFF decoder/scalar calculation agrees on all 38761 selected pixels, zero mask disagreements; qualitative RGB/false-color inspection supports alignment. See results/independent-validation.md. This validates the threshold measurement, not surveyed vegetation acreage.

PPT evidence handoff completed: ppt_handoff/README.md and COMPLETE_HANDOFF.md; archive SATquery-evidence-pack.zip. Includes20run NDVI benchmark, independent checks,9real examples,raw records and17browser captures. Open temporal-refusal gap documented; requested UI changes remain deferred for discussion.
