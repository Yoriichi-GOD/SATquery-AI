# SatQuery overnight report — 7 September 2026

## Outcome and verification boundary

Implemented conservative routing, the NDVI processing-stage viewer, loaded-image UI cleanup, and a side-by-side development comparison. Routing and worker dispatch pass local tests. Saved development predictions were re-scored successfully. **Full runtime and visual verification remain blocked; this is not a fully verified deployment.**

No training, new model inference, fresh benchmark, or PPT editing was performed. `geo.py` and all original analytical audit evidence remain byte-identical. Grounding remains **PLANNED**.

## Preserved state

- This workspace is not a Git repository. Before editing, copied server, geo, web, tests, results, scripts, README and launcher into `backups/20260907-000855/`, with `sha256.json`.
- Final verification confirms unchanged `geo.py`, `start.ps1`, all original `results/` files, and original training/calibration scripts.
- All 121 files in `ppt_handoff/` match their entries in the existing `SATquery-evidence-pack.zip`. Neither the handoff nor archive was edited.
- Invalid earlier NDVI evidence, including `results/ndvi-invalid-v1.json`, is preserved. It has not been replaced with corrected numbers.
- Corrected source TIFF hash verified from the local archived file: `55f3ca7b578e045594f8d54419b590c3ffeb99247ec5f74d7b1355d5bc4ec0f8`.
- No changes were made outside this workspace. A workspace `.venv/` was created, but dependency installation failed; it is not a working replacement for the existing WSL environment.

## Routing

`routing.py` implements a versioned, deterministic English intent grammar with `vqa`, `ndvi`, and `refuse` outcomes. Each result contains a rule identifier and reason, with no confidence score. Unsupported intents are rejected first; recognized requests must then match a whole-question allowlist. Compound or unknown requests fail closed.

Both `/api/analyze` and `/api/ndvi` enforce intent checks. Selecting an adapter cannot bypass routing. The UI submits all questions through `/api/analyze`; its dropdown selects the VQA model, not the analytical tool. Accepted jobs retain question, router version, rule and reason. Refusals return HTTP 422 with an explanation and schedule no worker; they do not create model run files.

| Example | Result |
|---|---|
| Describe this image. | VQA |
| Is there a river visible in this image? | VQA |
| Is there a water body visible in this image? | VQA |
| Describe the vegetation visible in this image. | VQA |
| Calculate NDVI | NDVI only with supported calibrated Red/NIR |
| What percentage of this image is vegetation? | NDVI threshold-selected coverage, explicitly qualified as a proxy |
| How green is this? | Refuse ambiguous green intent |
| Compare this to last year | Refuse temporal analysis |
| What changed? | Refuse temporal analysis |
| Analyze SAR with this optical image | Refuse unavailable SAR/fusion |
| Show the buildings / Locate the buildings | Refuse unavailable grounding |
| How many buildings are there? | Refuse unvalidated counting |
| Calculate NDVI for water / for buildings | Refuse wrong analytical target |
| Calculate NDVI and count buildings | Refuse compound unsupported request |
| Calculate NDVI on RGB-only input | Explain calibrated-band requirement; no calculation |
| NDVI >= 0.7 with control at 0.5 | Explain threshold mismatch; no calculation |

Explicit numerical thresholds must match the control. Unsupported NDVI statistics, health/species/density diagnoses, arbitrary spatial/area measurements, and comparison requests are deliberately refused. This includes some potentially answerable paraphrases: the router is intentionally narrow. The application still trusts ingestion's existing labelled surface-reflectance metadata contract; no new certification of user-supplied calibration is implied.

NDVI answers now state both selected percentage of valid pixels and selected percentage of the whole crop. These are existing statistics, not a changed calculation. The experimental yes/no and rural/urban modes also reject incompatible question formats instead of forcing a misleading label.

## UI changes

- Analysis Result includes four Processing Stages linked to the current run's generated artifacts: RGB, NIR/Red/Green false colour, NDVI evidence overlay and binary mask. Clicking a view opens that artifact.
- `stages.py` copies the actual ingested RGB, composites the actual analytical overlay, stretches source NIR/Red/Green for display only, and derives the mask from the completed NDVI GeoTIFF. It never rewrites the NDVI raster or overlay.
- Binary mask: white selected, black unselected, transparent invalid. It is not an object-grounding mask. No static contact sheet is substituted for run outputs.
- A job is not marked complete until stage generation finishes. A stage-generation failure preserves the analytical result and original exports and displays an explicit viewer error.
- The Dehradun action is in the empty image state and hidden after upload. The loaded filename remains in image metadata; the result's filename and actual threshold also appear under the stages.
- The dropdown groups Original and Experimental adapter options. Spacing, focus, option selection and theme colors were cleaned up while retaining native select behavior. Enhanced picker styling is progressive; fallback appearance depends on browser/OS.
- Old answer/stage/overlay content is cleared when a new request is refused.
- No screenshots were generated or claimed. Dark/light, mobile layout and native dropdown appearance still need visual QA.

## Evaluation and exact evidence

The main comparison is labelled **DEVELOPMENT ONLY**, with the same categories horizontally aligned for Original and SatQuery Adapter. It displays 60 questions / 20 images / one source scene, overall strict exact-match accuracy, format failures, regressions and the majority reference. No diagnostic and development values are pooled.

`evaluation.py` re-scores the original paired predictions using the original training script's normalization: lowercase, collapse whitespace, strip trailing spaces/dots/exclamation/question marks, exact label equality. Invalid formats count as incorrect. It checks paired question/image identities, the frozen development-input SHA-256, sample sizes, training-manifest identity and agreement with the saved experiment totals. It withholds the comparison on disagreement.

| Development category | Original | Adapter |
|---|---:|---:|
| Rural / urban | 0/20 | 15/20 |
| Presence | 10/20 | 15/20 |
| Comparison | 13/20 | 17/20 |
| Overall | 23/60 (38.3%) | 47/60 (78.3%) |
| Format failures | 20 | 0 |

Saved predictions contain 26 gains and **two regressions**: question 5440, “Is there a circular road?”, and question 1936, “Is there a rectangular grass area?”. Both references are `no`; Original answered `No`, adapter answered `yes`. The UI shows both. Category-majority reference: 37/60 (61.7%). The overall change is +40.0 percentage points; format compliance contributes to it.

Exact inputs, all preserved in place:

- `ppt_handoff/raw/baseline_dev_predictions.jsonl`
- `ppt_handoff/raw/adapted_dev_predictions.jsonl`
- `ppt_handoff/raw/dev.jsonl` — SHA-256 `c4ce050ea7fb352804e78032512a70dd5856ef7bcd695f9b56a1ef8861d87f77`
- `results/learning_manifest.json`
- `results/pilot-v1.json`
- `scripts/train_pilot.py` — original protocol, read only; never executed
- `ppt_handoff/raw/diagnostic-baseline_summary.json`
- `ppt_handoff/raw/diagnostic-manifest_metadata.json`

Download links expose these fixed evidence files and the scoring code through an allowlisted endpoint. Hashes are retained in `results/overnight-development-rescore.json` and the API response.

The earlier Original-only diagnostic remains a separate section: 24/60 (40.0%), 60 distinct images, balanced labels, no adapter result. Neither section is presented as an official external benchmark. Development caveats retain repeated images, one scene, label imbalance, unknown upstream exposure, possible spatial adjacency, noisy labels and format-confounded gains. Historical comparison-question scores do not enable counting/comparison in Explore.

**Fresh measured model results: none.** The development values above are re-scored saved predictions, not new inference. A genuinely fresh held-out evaluation was not attempted because model/runtime access is denied and no uninspected, leakage-audited set could be established in this session. No replacement “benchmark” was manufactured.

## Tests and recorded results

Run from the workspace: `python scripts/verify_overnight.py`. Full command output, return codes, routing examples and preservation hashes are saved in `results/overnight-verification.json`. The verifier returns nonzero while any suite remains blocked.

| Check | Result |
|---|---|
| `python -m unittest discover -s tests -p test_routing.py -v` | PASS: 4 methods, 37 prompt cases, calibrated/RGB variants, determinism, invalid/mismatched thresholds |
| `python -m unittest discover -s tests -p test_dispatch.py -v` | PASS: 7 methods |
| `python -m unittest discover -s tests -p test_evaluation.py -v` | PASS: 3 methods |
| `python -m unittest discover -s tests -v` | NOT GREEN: 14 passed, 2 module import errors (`test_geo`, `test_stages`: NumPy unavailable) |
| `python -m py_compile server.py routing.py stages.py evaluation.py` | PASS |
| `node --check web/app.js` | PASS |
| `node tests/test_ui.cjs` | PASS: DOM wiring tests |
| Protected-source/evidence hashes and 121 handoff-file comparisons | PASS |
| Real GPU inference / HTTP API integration / raster-stage execution / browser visual inspection | BLOCKED, not passed |

Dispatch tests execute endpoint and worker functions extracted from the actual source, with executor/HTTP/filesystem collaborators replaced by test doubles. They verify scheduling, refusal-before-work, saved reasons, adapter format restrictions, busy handling, denominator wording and completion after stage generation. They do **not** validate FastAPI transport or GPU execution.

The Node test uses DOM and fetch doubles, with existing NDVI evidence as an explicitly labelled fixture. It validates wiring, four current-run URLs, context, comparison values, regressions and refusal clearing. It is **not** a screenshot, fresh NDVI run or browser test.

The new raster integration test is ready for the existing scientific environment: it ingests the archived corrected TIFF, checks preserved counts/area, ensures the NDVI and overlay bytes are unchanged by stage generation, compares mask selection against the analytical overlay, checks dimensions and verifies a different threshold changes the mask. It could not execute here.

## Blockers, limitations and planned work

- WSL returned `Wsl/Service/E_ACCESSDENIED`. No attempt was made to bypass it or write into WSL by another route.
- Windows Python lacks NumPy, rasterio, PIL, pyproj and FastAPI. Workspace dependency installation was blocked by socket permissions (`WinError 10013`). No escalation or external-environment modification was attempted.
- The browser tool reported “No browser is available.” Visual inspection remains outstanding.
- The existing `start.ps1` and GPU/model loading path are preserved. Startup in the intended WSL runtime was not demonstrated this session; no server is left running by this work.
- Grounding implementation and empirical feasibility remain **PLANNED**, deferred until core raster/browser validation is complete. There is no shipped text-to-box/mask path. The NDVI overlay is spectral threshold evidence only. Temporal reasoning, paired-image analysis and optical/SAR fusion remain planned and refused.
- No confidence scores, timing benchmark, new model accuracy claim or new calibration claim was introduced.

## Files changed / added

Changed: `server.py`, `web/app.js`, `web/index.html`, `web/style.css`, `README.md`.

Added: `routing.py`, `stages.py`, `evaluation.py`, `tests/test_routing.py`, `tests/test_dispatch.py`, `tests/test_evaluation.py`, `tests/test_stages.py`, `tests/test_ui.cjs`, `scripts/verify_overnight.py`, `results/overnight-development-rescore.json`, `results/overnight-verification.json`, this report, the backup directory and incomplete workspace `.venv/`. Python checks also created normal bytecode caches.

## Morning manual verification

1. From this workspace, run the full suite in the existing WSL environment:

   ```powershell
   wsl.exe -d Ubuntu --cd "/mnt/c/Users/nrgen/.codex/scratch/SATquery AI" -- /root/satquery/.venv/bin/python -m unittest discover -s tests -v
   ```

   Investigate any failures before treating the viewer as verified. Do not train.
2. Start with `./start.ps1`, open `http://localhost:8765`, and hard-refresh. Check both themes and a narrow viewport, including keyboard selection in the model dropdown.
3. Load the Dehradun sample. Confirm the sample action disappears and the loaded TIFF filename is shown. Ask `Calculate NDVI` with threshold 0.50. Existing verified reference, not a new result: 38,761 selected / 262,144 valid pixels, 14.786148% coverage, 387.61 ha projected grid area.
4. Inspect all four views and their full-size links. Confirm alignment, false-colour band ordering, selected/invalid mask legend, and that the overlay follows pan/zoom. Change the control to 0.70, run again, and confirm the mask and result context actually change. Save JSON and download the GeoTIFF; check routing, threshold and calibration metadata.
5. Upload a TIFF under a different filename. Confirm that filename replaces the sample name. Upload ordinary RGB and request NDVI: expect a calibrated-band refusal with no numeric answer.
6. Try the refusal and VQA prompts in the routing table, especially `Compare this to last year`, `What changed?`, `Show the buildings`, counting, and a mixed NDVI/counting question. Refusals must clear the previous result and overlay. A river-presence question must use VQA even when the image has NIR bands.
7. Check Evaluation: 38.3% vs 78.3%, 60 questions / 20 images, two visible regressions, 37/60 reference, DEVELOPMENT ONLY, evidence downloads, and separate 40.0% Original-only diagnostic. Confirm no fresh adapter test score is implied.
