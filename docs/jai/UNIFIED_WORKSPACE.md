# Unified Terrain & flood workspace — 30 October 2026

The participant requested the native black Workspace design, questions beside the visible terrain, folded evidence and flood/terrain context in one place. The prior three-panel extension is superseded by a single native workspace.

## Current product flow

- **Terrain & flood** is one navigation entry. Older #terrain, #flood and #investigate entry links open this workspace.
- The viewer shows real cached terrain with the selected saved run's candidate markers after automatic, verified grid mapping. View buttons switch to the actual before-SAR, after-SAR and categorical water map using the same selection.
- The question composer sits beside the viewer. Answers and measured fields appear there; no separate Investigate page is required. The viewer's Ask action focuses that composer, including on mobile.
- Sources, dates, downloads, intersections, methods and tool traces are closed disclosures until requested. Raw IDs/hashes and detailed parameter records are inside those disclosures.
- Native black/graphite surfaces and gold controls replace the earlier blue panels. The terrain uses a labelled grayscale elevation ramp and warm slope ramp; source SAR images and categorical prediction pixels are not filtered or modified.
- Terrain-only selection is explicit and survives reload. Run changes immediately hide old geometry/images/results while fetching the new context. The question and recorded answer restore only when their source IDs match the current selection.
- The original Workspace and Evidence pages keep their original handlers and source. A compatibility guard leaves extension selectors native, so the baseline's snapshot dropdown helper cannot freeze their changing options.

## Code and behaviour boundary

The home response loads only `jai_extension/web/earth.js` and `earth.css`, using content hashes in asset URLs. Previous extension UI files remain historical source; their separate tabs are no longer loaded. Numerical, registration, inference and orchestration methods are unchanged. A job JSON download response adds an explicit safe Content-Disposition header; it returns the same recorded job.

No new dataset, model, acquisition, accuracy or hazard inference is introduced by this UI change. Source masks and existing frozen evidence remain intact.

## Verification

Final application revision: `9573886a1ce3fb2c930a46f027d5e48a7d2c5058`. All **190 main tests** passed (2.689 s); JavaScript syntax and whitespace checks passed. These software checks do not establish scientific accuracy.

Actual browser checks on genuine saved sources:

- A combined roads/buildings/water/terrain question executed four tools in place and displayed 9.56 ha, two building intersections, 185.8 m road intersections and 34.6° median slope. The source IDs matched the visible selection. Reload restored that question and answer.
- Terrain-only questions, explicit terrain-only reload, source switching, before/after SAR, categorical water map, slope/elevation and height controls worked. Source changes cleared old measurements, image, overlay and answer immediately.
- A fast first question exposed a loading race. Analyze is now disabled until the selected context is ready, with a matching submission guard. The replay with a paused upstream verified the disabled state, then normal readiness/recovery.
- Live Stop produced “Analysis stopped. No completed answer was produced.” The same owned Flood Lab process was resumed. A separate paused-upstream refresh retained terrain, cleared flood metrics and disabled flood image views; refresh and run reselection restored the genuine combined context.
- The explicit 2D fallback hides and disables water markers; returning to 3D restores the control. A 2,160 m profile returned 128/128 valid samples from the real 90 m DSM.
- Unsupported depth/safety questions abstained without carrying prior numerical answer cards into the refusal.
- Original Workspace and Evidence navigation and reload worked. Default 961×871, compact 1280×720 and mobile 390×844 layouts had no document-level horizontal overflow. The mobile Ask action focused the visible composer. Sources and answer evidence remained closed.
- Native sidebar/viewer backgrounds measured rgb(16,16,16) and rgb(8,8,8). No warnings/errors were captured in the final browser log check.
- The analysis download endpoint returned HTTP 200, explicit attachment/no-store/nosniff headers and JSON identical to the recorded job. In-app browser file-save automation timed out; an actual browser-saved file is **not verified**.

The machine-readable [UI receipt](UNIFIED_WORKSPACE_RECEIPT.json) records source hashes and screenshot provenance. [Full desktop capture](images/unified-desktop-1280.jpg), [default viewport](images/unified-desktop.jpg), [mobile terrain](images/unified-mobile-terrain.jpg) and [mobile composer](images/unified-mobile-question.jpg) are real application captures. Prior dated screenshots remain historical evidence.

UI quality is established through actual rendered checks, not inferred from the numerical suite. Preserve prior dated screenshots as historical records; the current screenshot receipt identifies the new source revision.
