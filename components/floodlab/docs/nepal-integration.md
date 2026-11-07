# Nepal inputs integrated - 2026-10-14

## Completed
- Copied the acquisition kit into data/acquisition-kit; originals untouched.
- Copied both EMSR927 GeoPackages into evaluation_only/emsr; checked integrity and SHA-256. Reference files are excluded from Git and prediction paths.
- Extracted ONLY areaOfInterestA geometry into data/aoi/nepal-official-boundaries.geojson. Damage/transport/building outcomes were not inspected. Official geometry bounds differ from the kit's approximate rectangles.
- Queried and saved all eight public catalogues (2 AOIs x 2 sensors x pre/post). Initial HTTP 429 on two requests resolved with sequential requests and cached responses.
- Found 2 eligible SAR metadata pairs for Syapru Besi and 3 for Timure, requiring same platform, orbit/direction, full AOI footprint containment and approximately 12 days separation.
- First candidate for both: 2026-08-16T12:21:41Z -> 2026-08-28T12:21:41Z, Sentinel-1D, ascending relative orbit 85. Selection prioritizes earliest post-event acquisition, not agreement with damage labels. It is provisional until actual SAR quality/terrain coverage inspection.
- Added this register to Evidence > Detailed evaluations on 8770.

## Still required
1. Actual Sentinel-1 product pixels for the selected pair. CDSE_ACCESS_TOKEN is not set in the checked WSL process environment; no authenticated download attempted. Metadata is not imagery.
2. Terrain data and tested SAR preprocessing: calibration/noise removal/terrain correction, masks and aligned grids. Raw GRD COG does not imply analysis-ready calibrated dB.
3. Historical OSM download plus original-node road topology and buffered routing context. OHSOME_API_KEY is not set in the checked environment. Small AOIs alone cannot establish isolation from outside hubs. Parquet geometries alone do not guarantee original node connectivity; adapter remains required.
4. Optical scene selection/preparation with pixel-level cloud/shadow validity. L2A metadata discovered by kit; do not pass it into the existing L1C model unchanged.
5. Actual AI integration and real event run. Current fixed SAR heuristic is not the required trained AI component. Existing templates are not an AI copilot.
6. Freeze predictions, then inspect reference class semantics and build compatible raster/vector comparison. Existing binary-raster scorer does not directly score these GeoPackages or establish debris damage accuracy.
7. Required reports, demo and arbitrary-area/date orchestration.

Kit corrections: official organizer PDF has already been read; training dataset allowances are confirmed. 27 July is an acceptable pre-event snapshot, not the only allowed date. L2A-only is not an organizer requirement. No large training downloads are needed to complete acquisition.

Source of current facts: docs/dataset-readiness.json, saved public catalogue responses and metadata of supplied GeoPackages. No real flood accuracy has been measured.

## Verified real-data milestone
- Real run: nepal-syapru-002, 16/28 August Sentinel-1D, same orbit85 and 10m UTM45N grid; Copernicus DEM30 terrain processing through provider.
- Historical OSM acquisition succeeded: 39,311 corridor features; 405 infrastructure features intersecting Syapru AOI. Key remains ignored in .env.local.
- 31,838 valid paired pixels of 34,578 AOI pixels. Full rectangular raster has 123,123 pixels; outside AOI is invalid.
- Frozen heuristic produces 361 new-water candidate pixels (36,100 square metres), intersecting one building and 87.395m road/bridge geometry. These are NOT validated flood damage numbers.
- 43 regression tests pass. HTTP hash verification passed for all 12 files of this run; original 8767 also returns 200.
- After freezing prediction, reference class inspection found AOI01 observedEventA labelled Mass Movement / Landslide. No water-vs-landslide accuracy score is claimed.
- Road topology request returned HTTP406. Geometry-only extract lacks node IDs. Real connectivity remains unassessed; UI/report explicitly say so.
- Browser visual verification remains pending because access to its stale error tab was blocked by browser URL policy.
- Required outstanding work and demo instructions: DEMO.md and demo-status.json.
