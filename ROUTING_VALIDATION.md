# Routing and external scientific validation — 20 September 2026

## Implemented
Unified controller v4 refuses forecast/evacuation requests; paired NDVI; temporal vehicle/colour matching and length measurements; water requests combined with roads, depth or volume; pixel maps and coverage measurements from the scene classifier. Existing supported specialist paths remain available. Image inspection and pair validation still precede job dispatch. No new sensor support, automatic alignment or calibration is implied.

Input/request refusals now return structured detail containing message, next_steps, code and analysis_started=false. The interface displays the message and recovery steps as readable paragraphs. Clients previously assuming detail was always a string must accommodate the structured object. Actual inference failures still use the existing worker error path; this change concerns pre-execution refusals.

## Verification
58 regression tests passed. JavaScript parses successfully. Browser forecast request refused without inference and gave the supported alternative Map water. A message-rule bug that incorrectly requested dates for that refusal was corrected and covered by a regression test.

External scientific case: Sen1Floods11 Bolivia_129334, selected lexicographically from the published Bolivia split before inference, excluding app catalogue entries. Source: https://github.com/cloudtostreet/Sen1Floods11. This chip was absent from local train/validation lists but already belonged to the previously evaluated Bolivia holdout. It is NOT a new independent benchmark.

Original public TIFFs initially refused for missing required product metadata. Copies were annotated using published band order, sensor/units and event dates (2018-02-15 for both sensors). Pixel arrays, CRS and transform were asserted unchanged. This preparation was manual, not a new automatic product capability. The annotated pair was uploaded via /api/images and analysed through /api/analyze without a sample ID or trusted-benchmark bypass.

Six live refusals passed: missing product metadata; future flood spread; water plus roads; water depth; paired NDVI; deliberately mismatched grids. Refusals left the service ready and declared analysis_started=false.

Masks were scored independently from exported probability arrays at threshold 0.5 against valid reference labels. Input invalid pixels and label -1 pixels were excluded. Counts were independently recomputed and matched the returned statistics. ZIP integrity and byte-exact preservation of both uploaded inputs passed.

| Path | Water IoU | Water F1 |
|---|---:|---:|
| SAR only | 84.87% | 91.81% |
| Optical only | 93.65% | 96.72% |
| Joint | 93.34% | 96.56% |

Optical alone outperformed joint on this chip. Do not claim universal fusion superiority, overall accuracy, Cartosat/RISAT readiness, flooding-versus-permanent-water discrimination, or generalisation from this one case. Header agreement does not independently certify physical registration. The finite list of intent rules is not proof of universal natural-language safety.

Reproducible inputs, hashes, published metadata, exact runs, confusion counts, refusals and exported evidence: paired_lab/evidence/external-water-20260920/verification.json and sibling files.
