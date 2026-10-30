# Alignment and investigation completion — 30 October 2026

This closes the two implementation items selected by the participant: terrain/flood grid alignment and the bounded multi-tool investigation workflow. The earlier DAY1_COMPLETION.md is a historical checkpoint.

## Definition of Done checked

| Requirement | Finished behaviour | Verification |
|---|---|---|
| Actual spatial mapping | Read and hash-check the selected prediction TIFF and DEM; reproject categorical labels with nearest neighbour onto the metric DEM grid. | Shifted/non-overlap, geographic-to-metric, NoData, corrupt raster and known-control tests; genuine Syapru replay. |
| Shared support and uncertainty | Report common valid cell centres, each input CRS/resolution/hash and coordinate roundtrips. Distinguish grid mapping from independently verified physical alignment. | 816/908 valid DEM centres share observed support; three coordinate checks roundtrip below 0.01m. These mathematical checks do not measure sensor alignment accuracy. |
| Small water patches remain inspectable | Preserve sampled native candidate centres, with bilinear DSM context and a declared +2m display offset. Keep nearest-class and observed-support-fraction fields separate. | 601 of the full run's 956 candidate centres have valid bilinear DSM support. The 90m nearest grid has 11 candidate cells. These are different supports and must not be pooled. |
| Real profile | Two surface picks or entered metric endpoints produce a distance/elevation cross-section; no interpolation across missing neighbours. | Known analytic profile tests and browser-picked ~805m transect, 128/128 valid display samples. Sampling density is not DEM resolution. |
| Source-based investigation | Deterministic topic planner executes up to four registered saved-data tools and composes measured fields with source pointers. | Predeclared 14-case replay; numerical/status facts checked against actual source fields. |
| Real trace | Record each actual tool output, duration, output SHA and previous-event hash; serve recorded derived outputs through job-specific endpoints. | Hash-chain and modified-history tests; live evidence-pointer replay. This is local integrity checking, not a signed audit certificate. |
| Stop/cancel | Stop sets cancellation; in-flight local HTTP reads have bounded timeout; no answer is completed after cancellation. | Unit race test initially failed, was fixed, then passed. Browser test with paused owned upstream reached CANCELLED in 8.02s with zero tool outputs and no result. Same upstream resumed successfully. |
| Honest failure | Unsupported depth/safety/forecast/external-action requests abstain; absent sources fail without a completed answer. | Replay includes wrong year, missing run/DEM, absent terrain selection, unsupported requests and injection. |
| Selection/reload | Changed flood selection clears previous overlay and synchronizes the context run. Recorded job survives reload; interrupted work is marked interrupted after restart. | Browser run-switch check and persisted-job tests. Updated assets are versioned to prevent older cached selection code. |
| Regression and closure | Main suite, helper checks, branch hygiene and real-source replay; retain prior evidence and prior failure. | Final records are linked below; no historic accuracy result is rewritten. |

## What a user can do

Open Terrain, choose a saved flood run and select **Align selected run**. Read common support and evidence, then select **Show water candidates**. Gold markers are satellite water candidates, not flood truth, water height or depth. A 2D fallback hides the 3D marker layer explicitly. Changing the saved run requires a new alignment.

Select **Pick surface points**, click two positions on the 3D surface, then **Calculate cross-section**. Alternatively enter two coordinates in the displayed metric CRS. Gaps remain gaps. The terrain source remains a historical 90m DSM.

Open **Investigate**, confirm the run and terrain identifiers, then ask about recorded water candidates, infrastructure intersections and terrain. A combined question runs get_run → get_exposed_assets → get_dem → analyze_coverage. **Current transect** uses the Terrain endpoints. Inspect each actual tool output or download the recorded job JSON. **Stop** cancels the current investigation; it cannot kill an already completed job.

This is visibly labelled a **rule-based tool workflow with no AI model**. There is no trained-agent, autonomous acquisition or unrestricted natural-language geospatial inference claim.

## Evidence and remaining limits

- [Replay protocol](INVESTIGATION_PROTOCOL_20261030.md), [final replay](investigation-replay-final.json), [live Stop receipt](investigation-cancel.json), [browser receipt](WORKFLOW_BROWSER_RECEIPT.json).
- Main full suite: 190 passed, including the cancellation/timeout race. Eleven existing measurement-helper checks are separate. Software correctness and source-value matching do not establish scientific flood accuracy.
- Existing Flood Lab suite remains 69 passed / 1 historical-state metadata failure / 31 warnings at the previous checkpoint; Flood Lab code was not changed in this work.
- Grid reprojection is implemented and verified mathematically. Physical optical/SAR/DEM co-registration has no independent landmark/survey validation. The 2021 DSM is context for later SAR observations, not a concurrent terrain measurement.
- No water-depth, dynamic flow, real damage/closure, evacuation, hazard probability or validated settlement isolation inference is added.
- No live source acquisition is performed by Investigate. Only the previously approved public terrain obtain route can download its one allowlisted demo. CDSE OAuth/30m authorization remains unverified.
- Runtime assets and job records are local and ignored. A new clone requires the original provisioned SATQuery/Flood Lab installations and real saved data. No cloud deployment, final presentation or organizer acceptance is implied.

The performance replay is a local API diagnostic on previously inspected inputs. Direct summary returns less information. Manual-equivalent API gathering excludes human click time. The orchestration adds overhead; no speed superiority is claimed.
