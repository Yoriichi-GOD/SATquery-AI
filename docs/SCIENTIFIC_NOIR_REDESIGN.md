# SATquery AI Scientific Noir — implementation and verification

Implemented in the existing application at `C:/Users/nrgen/.codex/scratch/SATquery AI`. Open http://127.0.0.1:8768/ for the optional unified application. Original services on 8765/8767 remain owned by their launchers. No deployment was performed by this UI chat.

## Latest requested corrections

The header is clear and stays fixed. The footer stays fixed at 64–66px; the content viewport reserves its actual measured height. Desktop Workspace and Terrain each have independent left/right scrolling. Evidence has independently scrollable catalogue, layer/table pane and source inspector. On narrow screens only the content region scrolls between the fixed header and footer.

Window borders and opaque panel backgrounds are replaced by neutral translucent glass. Scientific imagery keeps original colours. Controls retain visible focus and functional borders. The supplied footer PNG is now used as an aria-hidden, clipped upper wave: CSS clips the non-text band around 42% of the original image, at a minimum rendered width of 1100px. Baked-in source names, coordinates and dates are excluded. Footer values remain real DOM metadata.

Tables have an **Open table in full view** action and a native modal with independent vertical/horizontal scrolling. Existing table values are copied for inspection; source downloads and scientific calculations are unchanged. The modal shows the rows loaded by the original table; bounded exposure previews remain bounded and retain their source CSV links.

A source-verified optical panel sits beside the original 3D renderer on wide screens, stacking on narrow screens. Before/after dates and source hashes come from `/visual-context`. Cyan water, copper debris and violet historical mapped buildings toggle independently and start off. These are display overlays, not damage classifications. Source changes clear old pixels immediately; grid/run mismatches and missing optical data are withheld. Optical and SAR dates differ, and grid equality does not prove physical co-registration.

## Route coverage

| Route | Installed behavior | Verification scope |
|---|---|---|
| Workspace | Saturn brand, galaxy idle state, actual query/result/event views, metadata footer, independent panes | Genuine NDVI run and earlier responsive/browser checks passed; latest fixed shell not rendered |
| Evidence | Real catalogue and raster/DSM products; source inspector; compare/zoom/opacity/order/visibility; real pixel populations; saved benchmarks retained; full table view | Core interactions and real source records passed browser checks; latest pane/table layout not rendered |
| Terrain & flood | Preserved Plotly 3D, SAR, water, profile, contextual analysis/trace/download; separate debris masks/intersections; seven-stage source navigation; genuine optional RGB and overlays | Core 3D/SAR/water/debris/compare/question/run-switch checks passed before latest layout; RGB event/contract tests passed; newest rendered UI pending |
| Datasets | Existing intake, preflight, specialist and independent-label evaluation preserved; shared theme and fixed shell | Earlier route/light/dark/size checks passed; full latest upload/Stop workflow not replayed |

The older standalone `/classic` and `/grounding/classic` reference applications were inspected and retained. Their primary entry points redirect into the unified application. Their separate legacy screens were not redesigned in this change.

## Evidence actually collected

- Baseline application suite: **234 tests passed** before edits.
- Shared backend final suite: **258 tests passed**, 34.999s, recorded in `.runtime/jai/road-home-optical-tests.log`. Backend additions and source safeguards were owned by the coordinated backend chat.
- **9 Node data-adapter tests** passed: real source values/hashes, missing products, independent pixel denominators, terrain values/CRS/NoData and source limitation types.
- **6 isolated DOM contract tests** passed for the optical panel: genuine dates/URLs, independent toggles, failed image handling, stale selection rejection, run/grid mismatch refusal and terrain-only missing state. These tests do not render CSS.
- **27 live HTTP/source checks** passed: active asset references and content versions, exact served bytes, original footer PNG identity, genuine dates, native 254×437 RGB/transparent overlays and independent valid populations.
- JavaScript syntax checks passed. No bundler/build/type/lint scripts exist for this plain JavaScript/CSS frontend. No dependencies or fonts were installed.
- Earlier real browser checks covered four unified routes × six sizes (1920×1080, 1440×900, 1366×768, 1280×720, 1024×1366, 390×844): **24 checks without document overflow**. These precede the latest fixed-shell correction and are not proof of its geometry.
- Earlier real Workspace NDVI run `e7778afbb613446a89298e4df0cb26c5` completed through the unchanged pipeline. The three-tool contextual run `investigation-6912a279aed84fa49fe6fa45761d143f` showed separate water/debris results and six source references. These are functional checks, not new scientific accuracy evidence.

## Rendered verification limit

**Latest glass/fixed-shell/table/RGB layout is installed but not screenshot-verified.** The browser tool stopped starting with a Windows helper setup-refresh error; reset and reconnect failed too. No alternate browser-control method was used. Final geometry, glass contrast, modal keyboard behavior and the complete failure/Stop/offline matrix remain open. The browser was working earlier; those captures are explicitly scoped to the earlier source checkpoint.

The confirmed earlier loaded mask capture is `scientific-noir-20261031/screenshots/terrain-final-both-loaded.png` in the project workspace. It was reopened and visually inspected. The earlier `terrain-final-both.png` capture was premature and is excluded as pass evidence. All screenshot hashes and exact installed source hashes are in `FINAL_UI_VERIFICATION.json` beside the staging files.

## Exact UI files changed

- `paired_lab/web/index.html`
- `paired_lab/web/app.js`
- `paired_lab/web/external.js`
- `paired_lab/web/noir-data.js`
- `paired_lab/web/noir.js`
- `paired_lab/web/noir.css`
- `jai_extension/web/earth.js`
- `paired_lab/web/noir-layout.css`
- `paired_lab/web/noir-layout.js`
- `paired_lab/web/visual-context.js`
- `paired_lab/web/noir/saturn-brand-logo.png`
- `paired_lab/web/noir/saturn-brand-icon-only.png`
- `paired_lab/web/noir/scientific-noir-background.png`
- `paired_lab/web/noir/floating-galaxy.png`
- `paired_lab/web/noir/satellite-earth-execution.png`
- `paired_lab/web/noir/thin-scientific-data-footer.png`

## Asset and numerical integrity

All six shipped PNGs are the supplied originals. Saturn logo and icon are used; no black-hole variant was imported. The nine evaluation crops and contact sheet were inspected as art-direction references and remain in the supplied kit. They are not rendered as observations or metrics. The Evidence page uses actual source outputs and a numerical DSM canvas, with genuine missing-data states.

The terrain renderer and original scientific colour scales are retained. No model weights, thresholds, masks, coordinates, scientific Python calculations or frozen benchmark results were modified by this UI work. Backend additions were independently coordinated and tested. Scores, masks, threshold candidates and possible infrastructure intersections keep their original interpretation limits; they do not establish damage, safety, flood depth or new accuracy.

The design uses existing Segoe UI/Consolas fallback fonts and the existing licensed Plotly bundle. Supplied imagery provenance is the implementation kit; no new third-party assets or packages were installed. No source file under the synced `sources/` mirror was edited.

## Definition of Done status

Implementation, source inventory, unit/contract tests and documentation are complete. **Rendered acceptance of the latest requested correction remains incomplete because browser verification is unavailable.** The new layout is a locally installed candidate, not a claim of fully verified completion. Latest layout changes remain uncommitted in this UI chat; prior coordinated commits were owned by the backend chat under its user instructions.
