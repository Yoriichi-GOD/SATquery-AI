# THE ROAD HOME — final Day 2 integration receipt

31 October 2026. Start: **05:41:30 UTC / 11:11:30 IST**. Hard deadline: **06:41:30 UTC / 12:11:30 IST**. Feature work is frozen; only demonstration-blocking corrections are allowed during final verification.

This work integrates the **existing** saved Syapru Besi water and possible debris/surface-change evidence into the main SATQuery application. It does not create a new debris classifier, rerun the source scientific pipeline, acquire new observations or establish disaster accuracy.

## Source and evidence

Starting source: `3586f471e85934a3fa953d1b437a9b38220eb0fb`, main. Frozen Day 1 commit: **`f3945347cf0f0a4581aa1480c8fa1501a25da4b4`**. Annotated `day1-final` object: **`a08d2706397d359edb060993ee3a14374b3d136f`**. Local ancestry and unchanged historical evidence were checked; no tag move, amend, rebase or force push was used.

Saved source: **`event-fe47db331390`**. Freeze SHA-256: **`ff6bb25ef3713d128bad95d9b44af0c33b0429ce6c767df6ac4c06524c3adb0e`**. All 15 allowlisted frozen artifacts downloaded and matched their recorded hashes. This is local saved-evidence integrity, not a signed external authenticity certificate.

| Independent signal | Candidate population | Valid population | Mapped infrastructure intersections |
|---|---|---|---|
| Water change | **95,600 m² = 9.56 ha; 956 pixels** | **99,858 paired SAR pixels** | **2 buildings; 185.8461137204373 m roads/bridges** |
| Possible debris / surface change | **104,100 m² = 10.41 ha; 1,041 pixels** | **30,239 debris pixels** | **71 buildings; 1458.9344344663516 m roads** |

Both prepared masks are 254×437 on the same EPSG:32645, 10 m grid. Equality of native grids was checked, not assumed. Water has 11,140 invalid pixels; debris has **80,759 invalid pixels**. These are different observation populations. No cross-layer feature/length totals are produced.

Actual SAR dates: **16 → 28 August 2026**. Optical debris-proxy dates: **22 → 27 August 2026**. OSM snapshot: **25 August 2026 UTC**. Terrain is the retained historical **90 m Copernicus DSM**, not concurrent flood-date elevation. Settlement connectivity is **NOT_ASSESSED**; the source's zero potentially-cut-off value is deliberately omitted when connectivity was not assessed.

| Artifact | SHA-256 |
|---|---|
| `debris-candidates.tif` | `d3f1849515bf76874a04988fc3d93fba8f21ee3b3f63bdae5f3ee5e0042e69d3` |
| `debris-exposure.csv` | `b0724b5bef28361b1b3e549e61a22d6c2d73309cb333f03fdf28ee9038d09f89` |
| `prediction.tif` | `b49b5b5978cd3606f2138306fa8bb687d65c268285f8816a660bbf0444d1ffa4` |
| `exposure.csv` | `d699e737d7c8e36a764cc2e6dddab789d66ea6146c8cf33bf812be156defb50c` |

## Implemented backend and API contract

- `jai_extension/flood_bridge.py`: validates and exposes all five debris summary fields; genuine availability requires complete source evidence. Bounded native TIFF decoding preserves 0 observed noncandidate / 1 candidate / 255 invalid. It cross-checks native candidate/valid counts and area against the saved summary, and separate CSV infrastructure aggregates against their saved totals. CSV headers, unique feature IDs, numerical finiteness, units, status/coverage consistency and 10,000-row cap are validated. Tampered/inconsistent evidence is withheld; missing debris is unavailable rather than numeric zero.
- `jai_extension/investigation.py`: deterministic `get_debris_evidence` routing for debris/landslide/surface-change questions, explicit source-linked claims and separate `review_rows_by_layer`. Missing debris abstains; water-only evidence is not substituted. Unsupported safety, depth, damage, evacuation, closure and forecast requests abstain before evidence claims. Existing cancellation and hash-chained recorded traces remain.
- `jai_extension/server.py`: additive `GET /api/flood/runs/{run_id}/debris` and `GET /api/flood/runs/{run_id}/debris-candidate.png`. Existing detail, water exposure, grid, verified artifacts, terrain and investigation routes remain registered. Water grid now includes its affine transform. Origins, loopback service configuration, transfer caps, allowlists and SHA checking remain enforced.
- `scripts/verify_road_home.py`: replayable local source/route/trace check for the genuine saved case, independent of displayed UI values. It does not recalculate a new scientific accuracy score.
- `tests/test_road_home.py`: 19 new focused Python integrity/contract regressions. `tests/test_road_home_ui.cjs`: five portable API/display-boundary checks, including the real string-vs-array source-limitations mismatch found during integration.

Exact JSON keys, source semantics, ownership and coordination history are in [ROAD_HOME_UI_HANDOFF.md](ROAD_HOME_UI_HANDOFF.md). Detailed receipts are in [road-home-day2](road-home-day2/).

## UI coordination and implementation

The active **Redesign SATquery AI interface** Work chat (`01a1907a-ae6e-7be3-a93d-63096a0dbb61`) acknowledged shared repository access and exclusive frontend/art-direction ownership. The design-only **Redesign UI Space Sun Theme** chat was read first but was not mistaken for the code-connected collaborator once the user identified the active Work chat.

The UI owner prepared the actual frontend changes and explicitly handed over exact ready files when its automatic write review repeatedly timed out. Backend integration copied only the seven reviewed frontend files, followed by four specifically reviewed source/display corrections; both installation receipts preserve exact source hashes. There were no simultaneous edits of the same UI files. Backend owner did not invent a competing design.

Installed frontend: seven-stage **BEFORE → AFTER → WATER → DEBRIS → INFRASTRUCTURE → TERRAIN → EVIDENCE** navigation; native separate mask comparison and legends; per-layer area/building/road counts; independent coverage; in-place source-based question and evidence; preserved real 3D terrain, profile controls and existing tabs. Scientific Noir, original Saturn branding and the supplied five artwork assets follow the UI owner's approved direction. The assets match the supplied kit bytes and are presentation artwork, never satellite evidence. No new framework, cloud service, font download or ML dependency was introduced.

Critical static fixes include invalidating late image loads on every view change, clearing comparison masks on source selection, falling back when a new run has no debris evidence, preserving source/view identity in asynchronous footer updates, accurate optical/SAR dates, readable string source limitations, comparison/source association and cache versions. A screenshot filename alone was not accepted as browser proof.

## Actual checks and limitations

| Check | Actual result and scope |
|---|---|
| Baseline | 234 tests passed before implementation. |
| Final backend Python suite | **258 tests passed in 34.999 s**, including five new optical source/grid/failure tests. Earlier frozen narrative source passed 253 in 33.919 s. Synthetic/software correctness, not new remote-sensing accuracy. |
| Portable frontend contract checks | **5 passed** on installed files. |
| UI owner's data adapters | **9 checks passed**, with retained real saved-source fixtures and explicit limitations handling. |
| JavaScript parsing | Five changed executable scripts passed `node --check`. |
| Genuine saved Nepal HTTP replay | **36 checks passed**, including all 15 original artifact hashes, exact independent populations/counts, native mask/preview properties, separate dates, missing-debris `NOT_ASSESSED`, actual supported question/trace and five unsupported-question refusals. |
| Existing saved-run regression | **17 real retained runs passed**, including runs without debris; no source runs modified. |
| Actual cancellation/recovery | Running job `investigation-1a736e67e8e049e5bb73586ef9fe48b8` reached cancelling → cancelled, no result and zero completed tool outputs. Owned optional upstream was briefly paused for 0.0325 s, resumed in `finally`, and returned health 200. **This is HTTP proof, not a browser Stop click.** |
| Static asset/cache checks | Eight content-version references matched actual files; five supplied PNGs matched original kit and served bytes; five application/static routes returned expected current bytes/status. Not a rendering test. |
| Original services | Original 8765/8767 processes preserved. Optional extension 8768 and Flood Lab 8770 available after coordinated restart. |
| Final browser replay | **Incomplete in the primary chat**: tool reports browser disabled in Work settings; user explicitly chose to finish with browser verification marked incomplete. Collaborator evidence is recorded separately with exact scope. No blanket final click-through pass is claimed. |

The collaborator's narrative-checkpoint screenshots show the real dated SAR views, source hashes and independent water/debris measurements. An early purported “both” screenshot showed an empty water view; it was flagged and replaced only after DOM/image completion checks and visual inspection confirmed both loaded 254-pixel-wide native masks. Corrected `terrain-final-both-loaded.png` shows the real joint question and answer. The collaborator checked 24 route/viewport combinations (four routes at six sizes, including 1280×720 and 390×844) with no document horizontal overflow. It reported benchmark tables preserved, layer visibility/opacity/order, real 3D context and source-selection clearing. These checks apply to the narrative checkpoint before the later separately requested shell/RGB panel changes.

The full narrative click-through, final 1280×720/mobile replay, stale-selection/reload/Stop interaction and corrupted-source UI fallback must not be inferred from software/HTTP checks. Where not explicitly recorded by the collaborator against final file hashes, they remain unverified. Backend malformed/missing/tampered-source handling and cancellation are covered by tests and actual API checks.

## Scientific boundaries

Debris is the existing **fixed vegetation-to-bare + NDVI loss + SAR-change proxy**, not a trained or independently validated debris classifier. Clearing/agriculture can be confused; already-bare deposits may be missed; SCL support is resampled from 20 m. **EMSR927 remains a class-mismatched checking reference, not debris accuracy.** No reference labels were merged into predictions and no proxy thresholds were tuned here.

Mapped intersections indicate **possible exposure**, not confirmed damage, casualties, closure, evacuation safety, hazard probability or prediction. Missing OSM assets are not counted. Mathematical grid mapping is not independent physical optical/SAR/DEM co-registration validation. Existing scientific benchmark reports, original data, model assets and Day 1 history are unchanged.

The Nepal investigation is **deterministic saved-evidence orchestration with no AI model invocation**. Other preserved SATQuery specialist routes use their existing models; this integration does not transfer their benchmark scores to Nepal.

## Authentic incremental commits

| Full SHA | Actual author timestamp | Change |
|---|---|---|
| `5213dfa2f341af68112ce48b2f804c92b53950c3` | 2026-10-31T11:23:30+05:30 | Verified debris bridge, endpoints, deterministic tool and initial integrity tests/handoff. |
| `433fa134c9b245b9dfb77e103792fcb2a8944f89` | 2026-10-31T11:31:14+05:30 | Safety wording refusal, bounded CSV checks and actual demonstration guide. |
| `19764d6c30762ac604fec4918eb78106b90c0569` | 2026-10-31T11:43:37+05:30 | UI-owned narrative/Evidence integration, reviewed critical fixes and runnable checks. |

Later commits, if any, are listed in the machine-readable [final receipt](road-home-day2/FINAL_RECEIPT.json). Documentation records its reviewed source commit rather than pretending to contain its own SHA.

**Publication issue and recovery:** initial Windows/WSL Git pushes failed TLS trust verification; the GitHub connector also failed transport. A later push succeeded using Git's standard OpenSSL certificate backend with verification enabled. Remote main was verified at `19764d6c30762ac604fec4918eb78106b90c0569`, then the optical backend `dfdafa7` was pushed successfully. No certificate bypass or untrusted certificate installation was used. Final remote refs are recorded in `FINAL_RECEIPT.json`.

## User-requested optical RGB and overlay extension

At 06:22 UTC, the user requested optical RGB alongside 3D terrain, separate building/debris colours, independent overlay switches and a demo flow. Backend `dfdafa7` adds `jai_extension/visual_context.py`, `/visual-context` and `/visual/{kind}.png`. A retained seven-band TIFF must match the selected frozen manifest's dated optical source hash and native grid; otherwise RGB remains unavailable. Every example is eligible for this check, but SAR-only examples do not acquire invented RGB. No acquisition or scientific source rewrite was used.

Genuine Syapru RGB uses **22 and 27 August 2026**, actual B04/B03/B02, fixed 0–0.3 reflectance display stretch, cloudy pixels retained and dataMask-invalid gray. Transparent source-derived overlays use **cyan water**, **copper debris** and **violet historical mapped-building outlines**. Buildings are context, not a debris class or damage estimate. Five native PNGs were checked over actual HTTP; candidate overlay populations remain exactly 956 and 1,041. Positive-only overlays must not imply uncoloured RGB is observed negative; native masks show gray unknown coverage.

The UI collaborator owns the latest RGB panel/toggles and its separately requested fixed shell/glass/scroll changes. Installation and click results are appended only if actually available before this task's deadline. Backend availability does not prove every latest UI control. [Demo cues](DEMO_ROAD_HOME.md) now include original RGB → individual overlays on/off → native coverage → question/trace.

All **17 retained real examples** were checked through the live visual-context API: **10 provide verified compatible RGB**, and **7 explicitly report unavailable**. The UI owner installed an adjacent dated RGB panel and independent default-off cyan/copper/violet checkboxes, with exact-grid checks, abort/selection guards and honest missing-source handling. Latest browser startup then failed in the UI chat too; those new RGB controls and the newly requested fixed shell were **not click-through verified**. The earlier narrative comparison remains supported by its retained screenshot and checks. See [per-example availability](road-home-day2/OPTICAL_EXAMPLES_RECEIPT.json).

The UI collaborator's [27-check final HTTP receipt](road-home-day2/FINAL_UI_HTTP_RECEIPT.json) confirms the new scripts/styles are referenced and served byte-exactly, cache versions match, the footer asset matches the supplied original, real dated RGB loads, and all three native RGBA overlays contain actual source-linked pixels. It explicitly records **no rendered latest-layout verification** and no CSS-parser pass. The [closeout supplement](road-home-day2/CLOSEOUT_SUPPLEMENT.json) distinguishes committed source, later UI candidate hashes, remote refs and remaining browser limits.

**Final installed UI checkpoint: `bc07854`**, committed and pushed after the UI owner explicitly released its six finished paths for this task's authorized closure. Six isolated optical DOM contract tests passed: true dates/URLs, independent default-off overlays, off-state removal, failed RGB base handling, immediate source clearing/late-response refusal, mismatched run/grid refusal and honest terrain-only state. These tests do not render CSS. The latest fixed shell/RGB/table view remains a **committed implementation candidate with rendered QA incomplete**, not an uncommitted file handoff. Source/APIs, supplied imagery, original terrain and saved measurements remain unchanged by this final UI commit.

## Judge commands and demonstration

In the documented provisioned Linux/WSL environment, from the repository root with existing local services/data available:

```sh
python -m unittest discover -s tests
node tests/test_road_home_ui.cjs
python scripts/verify_road_home.py
```

The last command performs local integration checks and creates new clearly scoped investigation jobs/receipts. It requires the existing authorized Flood Lab saved run and terrain, not model downloads. The independent external dataset evaluator remains available; no new judge dataset has been supplied for scientific acceptance.

Demo route: **http://127.0.0.1:8768/#terrain**. If that view is not functioning, use the genuine **Evidence** catalogue and verified source routes; never replace failed views with concept images. [Five-minute cues and three-minute version](DEMO_ROAD_HOME.md). [Shared UI contract](ROAD_HOME_UI_HANDOFF.md).

## Acceptance disposition

1. **PASS — source/API:** correct separate SHA-verified summaries, masks, coverage and source-linked intersection rows.
2. **PASS — deterministic investigation:** genuine supported debris question/trace and unsupported/missing-source refusals.
3. **PARTIAL — interface:** implementation and collaborator evidence exist; exhaustive final narrative browser replay is not claimed.
4. **PARTIAL — preservation/interaction:** software/API regressions and service preservation pass; final browser interaction coverage is explicitly bounded.
5. **PASS:** authentic additive commits, preserved Day 1 history and reviewed handoff; trusted GitHub publication recovered. Latest remote refs are recorded in the final receipt.

This is a verified local integration candidate with explicit open gates, not a claim that all five acceptance gates are fully closed.
