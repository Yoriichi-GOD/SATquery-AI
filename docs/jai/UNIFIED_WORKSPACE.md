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

Initial baseline: 190 passing main checks. Browser verification in progress is recorded separately at closeout. Required checks cover in-context combined and terrain-only answers, source/view switching, collapsed evidence, original Workspace/Evidence navigation, reload, mobile no-overflow, fallback, Stop and upstream failure recovery.

UI quality is established through actual rendered checks, not inferred from the numerical suite. Preserve prior dated screenshots as historical records; the current screenshot receipt identifies the new source revision.
