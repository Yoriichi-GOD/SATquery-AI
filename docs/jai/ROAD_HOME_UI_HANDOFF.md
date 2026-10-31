# THE ROAD HOME — shared backend/UI handoff

Started 31 October 2026, 11:11 IST (05:41 UTC). Hard feature cutoff: 12:11 IST (06:41 UTC). Source baseline: `3586f471e85934a3fa953d1b437a9b38220eb0fb`, main. Immutable Day 1: `f3945347cf0f0a4581aa1480c8fa1501a25da4b4`.

## Coordination and ownership

Read the latest accessible **Redesign UI Space Sun Theme** design chat: Scientific Noir, original Saturn logo, real scientific views, illustrative assets never presented as observations. Located the actual active **Redesign SATquery AI interface** Work chat (`01a1907a-ae6e-7be3-a93d-63096a0dbb61`) after the user identified it. **Direct reply confirmed shared repository access, frontend ownership and no independent service restart/commit.** It is implementing the narrative wiring and global approved theme in parallel. First contact with the design-only chat was not code coordination; the Work chat acknowledgement is the coordination evidence.

Codex owns `jai_extension/flood_bridge.py`, `investigation.py`, `server.py`, focused tests, source verification and these contracts. UI collaborator owns art direction and primary `jai_extension/web/earth.js`, `earth.css` edits. No simultaneous UI edits. If design-only, confirm minimal Codex wiring is permitted. Preserve original Workspace, Evidence, Datasets, specialists and actual 3D terrain.

## Story and science

One guided workspace: **BEFORE → AFTER → WATER → DEBRIS → INFRASTRUCTURE → TERRAIN → EVIDENCE**. Authentic SAR dates from the verified run: 16 August → 28 August 2026. No synthetic optical comparison. Use synchronized views only on actually matching grids; otherwise dated side-by-side views.

Saved `event-fe47db331390` exists and result/manifest SHA verification passed on this host. Freeze SHA `ff6bb25ef3713d128bad95d9b44af0c33b0429ce6c767df6ac4c06524c3adb0e`.

| Signal | Native area/pixels | Valid population | Mapped intersections |
|---|---|---|---|
| Water candidates | 95,600 m² / 956 | 99,858 SAR pixels | 2 buildings; 185.8461137204373 m roads/bridges |
| Possible debris/surface change | 104,100 m² / 1,041 (SHA and raster counts verified) | 30,239 debris pixels | 71 buildings; 1458.9344344663516 m roads |

Do not sum features/lengths across masks. Water cyan; debris copper; invalid coverage stays visibly unknown. Debris is a fixed vegetation-to-bare + NDVI-loss + SAR-change proxy, not a validated classifier. Feature intersections are possible exposure, not confirmed damage, closure, safety or risk ranking. Settlement access remains `NOT_ASSESSED`. Terrain is the real historical 90 m Copernicus DSM, not flood depth.

## Registered existing API contracts

- `GET /api/flood/runs/{run_id}`: verified `summary`, `provenance`, `artifacts` with exact hashes/URLs; existing water keys remain unchanged.
- `GET /api/flood/runs/{run_id}/exposure`: water `rows`, `source_sha256`.
- `GET /api/flood/runs/{run_id}/candidate.png`: native water preview, `X-Source-SHA256`.
- `GET /api/flood/runs/{run_id}/grid`: water raster grid.
- `GET /api/flood/runs/{run_id}/artifact/{name}`: allowlisted verified source, `X-Artifact-SHA256`.
- `POST /api/investigations`: `{question,run_id,scene_id?,profile?}`; poll returned job ID; result contains `claims`, source indexes, `sources`, `review_rows`, `tool_outputs`, hash-chained `trace`. Cancel remains `POST /api/investigations/{job_id}/cancel`.
- Terrain `/api/terrain` and `/api/context/coverage` unchanged.

## Proven additive contract — live HTTP verified at 05:52 UTC

- `summary.debris_candidate_pixels`, `debris_candidate_m2`, `debris_valid_pixels`, `debris_intersected_buildings`, `debris_intersected_road_m`; absent data omitted, `debris_available=false`, `debris_status=NOT_ASSESSED` rather than zero. `debris_available=true` only after the mask/CSV/source summary are actually cross-checked. Tampered or inconsistent evidence is withheld with 409; malformed grids/tables yield 422.
- `GET /api/flood/runs/{run_id}/debris`: `{run_id,debris_available,status,summary,grid,coverage,rows,source_sha256,source_hashes,artifacts,provenance,semantics,limitations}`. `grid`: `{crs,transform,pixel_size,bounds,bbox_wgs84,width,height,source_sha256}`. `coverage`: `{candidate_pixels,valid_pixels,total_pixels,invalid_pixels,pixel_area_m2}`. Each row preserves `{id,kind,exposed,observed,total,unit,status}` from the separate source CSV. Source hashes map exact artifact names. Provenance retains actual optical **22→27 August** dates, separate from SAR **16→28 August**.
- `GET /api/flood/runs/{run_id}/debris-candidate.png`: bounded native copper preview from verified TIFF; 0 observed noncandidate, 1 candidate, 255 invalid.
- Deterministic `get_debris_evidence` tool for debris/landslide/surface-change queries; no hazard/safety inference. Result retains `review_rows_by_layer={water:[],debris:[]}` and source links; legacy `review_rows` remains water-only. All claims carry source index/JSON field; use `/summary/debris_*` and `/summary/exposed_*`, not string-label heuristics. Missing debris abstains instead of substituting water evidence.

Native water/debris masks both use EPSG:32645, 254×437, affine `[10,0,335340,0,-10,3119190,0,0,1]`. This equality is verified for this run, not assumed for other runs. `/grid` now also exposes the water affine. BOTH may compare on this proven grid, but invalid populations remain distinct. Debris preview: observed noncandidate `(25,30,33)`, candidate copper `(191,116,74)`, invalid gray `(110,110,110)`. Existing water preview preserves its historical palette; recolouring it cyan is a display-only operation. Do not cover unknowns with an opaque other-layer mask and imply both were observed.

Actual source hashes: `debris-candidates.tif=d3f1849515bf76874a04988fc3d93fba8f21ee3b3f63bdae5f3ee5e0042e69d3`; `debris-exposure.csv=b0724b5bef28361b1b3e549e61a22d6c2d73309cb333f03fdf28ee9038d09f89`. Both download through the registered artifact route with `X-Artifact-SHA256`; the derived PNG returns `X-Source-SHA256`. No new data stubs or feature flags are used.

Backend baseline: 234 tests. Existing JAI checks: 73 pass. New debris checks: 18 pass. Live genuine-run check: **23 pass**, including exact counts, native grid/counts, separate dates/coverage, downloadable hashes, actual question/trace and safety/depth/damage/forecast abstention. Current source-only receipt is retained under `.runtime/jai/road-home/HTTP_RECEIPT.json`; final commit/hash receipt follows after source commit. Optional extension restarted by backend owner; current 8768 PID9656 / 8770 PID9655. Original 8765/8767 preserved. UI owner should signal ready before the final integrated restart/browser test.

## Added optical context contract — user-requested 06:22 UTC

`GET /api/flood/runs/{run_id}/visual-context` is live. Returns `{run_id,optical_available,before,after,grid,overlays,coverage,limitations}`. Before/after are `{date,source_sha256,grid,display,url}`. A known local read-only TIFF must match the frozen run's optical source hash, seven-band preparation and exact native water grid. No HTTP client path is accepted. Missing compatible files return `optical_available=false` and a reason; no SAR-to-RGB substitution or new acquisition.

`GET /api/flood/runs/{run_id}/visual/{kind}.png`, kind `before|after|water|debris|buildings`, returns bounded native PNG and `X-Source-Hashes` JSON. RGB = B04/B03/B02, fixed 0–0.3 reflectance stretch, cloudy pixels retained, dataMask-invalid gray. Transparent overlays: **cyan water candidates**, **copper possible debris candidates**, **violet mapped-building outlines**. Buildings come from the hash-verified historical OSM `layers.geojson`, rasterized on the native projected grid, not detected damage. Every overlay is independently switchable in the UI. Uncoloured RGB does not mean verified absence; native masks retain gray unknown coverage. Coverage reports separate water/debris valid counts.

Backend `dfdafa7` passed 258 Python tests. Live preview checks confirm native 254×437 RGB and 956/1,041 candidate overlay pixels plus actual historical building outlines. UI installation/browser verification for this latest panel is recorded separately; the API pass alone is not a toggle click-through pass. Original one-hour backend deadline remains 06:41 UTC; the collaborator's separately requested new shell/layout work is its own active scope and must not be silently declared finished here.

## Immediate integration ask

Confirm code ownership/access. Wire a distinct debris layer and both-layer comparison with separate legends/coverage; source counts come from API, never constants. Keep before/after, real 3D terrain and evidence drawers. Use question: **Which mapped buildings and roads intersect water or possible debris-change candidates, and what can we verify?** Clear pending answers/images on run switch; reject stale async results; preserve Stop/reload/mobile. No temporary fake data, no stub score, no competing app.

If cross-chat reply is unavailable, paste: “Read `docs/jai/ROAD_HOME_UI_HANDOFF.md` in the main SATquery AI repo. Backend is integrating verified event-fe47db331390 water and debris evidence. Please confirm earth.js/earth.css ownership, use documented proven APIs, and connect the seven-stage Nepal story while preserving existing screens.”
