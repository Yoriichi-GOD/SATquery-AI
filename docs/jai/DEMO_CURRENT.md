# Current two-minute demonstration — 30 October 2026

Start the extension and Flood Lab; open http://127.0.0.1:8768/ . Use genuine saved `event-fe47db331390` and cached `terrain-45737e0da2983d9d`. These are previously inspected development inputs.

| Time | Click/action | Actual narration / expected output | Failure handling |
|---|---|---|---|
| 0–20s | Flood Intelligence; choose the run | Recorded August SAR observations: 9.56ha of heuristic candidates, two mapped-building intersections, 185.8m road intersections. Access NOT_ASSESSED. | Show unavailable/missing evidence explicitly. |
| 20–40s | Before/After SAR and candidate map; open exposure CSV | Actual saved images and feature calculations, with source/hash links. Intersections do not prove damage. | Missing artifact remains unavailable; don't substitute artwork. |
| 40–65s | Terrain; Align selected run; Show water candidates | 816/908 valid DEM cell centres share support; 601 native candidate locations have valid DSM support. Gold markers follow the real 90m Copernicus DSM. Grid mapping checked; physical co-registration not independently validated. | No overlap or invalid input refuses overlay. 2D fallback shows terrain without 3D markers. |
| 65–80s | Pick two surface points; Calculate cross-section | Real metric distance and gap-preserving interpolated height. Sampling density does not improve the 90m source. | Enter two in-bounds metric points if picking is awkward. Missing data stays a gap. |
| 80–105s | Investigate; combined roads/buildings/water/terrain question; Run investigation | Four actual tools; measured values, evidence links and recorded trace. UI states rule-based workflow, no AI model. | Missing sources fail; unsupported depth/safety/forecast questions abstain. |
| 105–120s | Expand actual tool output; download recorded trace | Inspect the calculation/source. Stop cancels pending work; no live acquisition or real-world decision is executed. | Recorded terminal job survives reload. A recording is a labelled backup only. |

All content is advisory review context. No flood-depth model, validated flood accuracy, evacuation service or operational warning system is claimed.
