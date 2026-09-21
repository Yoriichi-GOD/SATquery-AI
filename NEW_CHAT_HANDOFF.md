# SATquery AI — new-chat handoff
Updated 7 September 2026. Read this first; do not rediscover the whole repository.

## User and boundaries
User likes relaxed, direct conversation (homie), concise updates and honest evidence. They own UI direction and supplied all artwork. Act on authorized fixes, but discussion-only requests mean no implementation. Latest task is this handoff. No VQA training or grounding download has been authorized since the user explicitly said to discuss those next steps and not touch them. Ask what they want to pursue next after reading this.

Deadline: September 9. College internal presentation already submitted. User says internal round permits slide-count flexibility and later revisions; do not keep treating seven slides as a submission blocker.

## Project and execution
Project: C:/Users/nrgen/.codex/scratch/SATquery AI
The chat cwd may be C:/Users/nrgen/.gemini/antigravity-ide/scratch/warlord — this is an unrelated project. Do not edit it.
App: http://localhost:8765/ (URL layout query is only a refresh hint; static asset versions matter).
Python server: FastAPI + vanilla HTML/CSS/JS; no frontend build required.
WSL Ubuntu scientific Python: /root/satquery/.venv/bin/python
WSL project: /mnt/c/Users/nrgen/.codex/scratch/SATquery AI
Start: wsl.exe -d Ubuntu -- /root/satquery/.venv/bin/python -m uvicorn server:app --app-dir "/mnt/c/Users/nrgen/.codex/scratch/SATquery AI" --host 127.0.0.1 --port 8765
Last started server PID 369 (verify, may change), tool session 57889. Do not kill guessed PIDs.
Local data/models: /root/satquery; uploads/runs: /root/satquery/app-data; corrected scene: /root/satquery/scenes/dehradun-sentinel2-20211125.tif.
Hardware previously checked: RTX 5060 laptop GPU 8 GB, Ryzen 9 8940HX, roughly 24 GB system RAM. User can use only free Colab additionally; local-first.
Project is outside this chat's writable roots; writes and WSL commands have required require_escalated approval. Read-only PowerShell works. A previous usage-limit auto-review rejection later cleared. Never bypass a rejection.
Bundled Python path used: C:/Users/nrgen/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe. Read/write UTF-8 explicitly; default Windows encoding once damaged CSS arrows, which was corrected.

## Essential files
server.py — upload/API, model worker, dispatch, artifacts/evaluation endpoints.
routing.py — conservative rules-v1 intent grammar.
geo.py — calibration-aware ingestion and deterministic NDVI.
stages.py — RGB, false-colour, evidence composite, binary mask.
evaluation.py — saved paired development prediction verification/rescoring.
web/index.html, web/app.js, web/style.css — current UI.
UI/ — original user art; web/art assets are served versions.
manifesto.md, README.md — historical plan/project docs, may lag current state.
OVERNIGHT_CODEX_REPORT.md — historical implementation report, NOT latest verification status.
results/final-live-verification.json — current fresh HTTP responses and VQA quality caveat.
results/overnight-verification.json — older simulated tests; not evidence of current full runtime by itself.

## Verified progress and remaining scope
1 baseline VQA implemented, model limitations known.
2 LoRA pilot implemented; development improvement verified from saved predictions, not a new held-out result.
3 multispectral ingestion/calibrated NDVI implemented and independently cross-checked.
4 overlays + four processing stages live.
5 pixel coverage/denominators/projected area + downloads live.
6 deterministic routing live; narrow whole-question allowlist, explicit refusals.
7 grounding deferred after bounded local readiness inspection; not implemented or empirically benchmarked.
8 presentation submitted; demo rehearsal, source freeze and screenshot walkthrough saved. Working UI subsequently changed, so freeze is older.
Full PS also includes temporal and optical-SAR work, still unimplemented. Do not imply full problem-statement completion.

## Critical server mismatch lesson
Overnight code was written but old uvicorn process stayed alive. New static JS then talked to old Python API: NDVI went through VQA and evaluation showed undefined/Unavailable. Confirmed old /api/development shape, restarted actual process, then verified live. Python edits require restart; static edits require refresh/cache version. Do not blame model/router until checking running code. Restart loses in-memory image/job indices; reupload image. Saved files remain.

## Current verified numerical evidence
Pinned model: AdaptLLM/remote-sensing-Qwen2-VL-2B-Instruct
revision: 7f5dd71bf0f40c282193d50160e848a387a08ffe
BF16, local CUDA, no quantization. LoRA r4 alpha8 dropout0.05 q_proj/v_proj, 544,768 trainable parameters; 720 one-pass training QA from 120 images/6 scenes. Dev: 60 QA /20 images/one other source scene. No final fresh held-out adapter benchmark.
Matched dev scoring: original23/60 (38.3%), adapter47/60 (78.3%); format failures20->0; category-majority37/60. Rural urban0->15/20; presence10->15/20; comparison13->17/20. 26 gains, two regressions: question5440 circular road and1936 rectangular grass, reference no, original No, adapter yes. Includes formatting effects. Original diagnostic24/60 is a DIFFERENT 60-image/60-question run, not comparable to adapter47/60.

NDVI corrected scene: Sentinel-2 Collection1 S2A_T43RGP_20211125T053958_L2A; acquisition2021-11-25T05:40:34.501Z. 512x512, 10m, EPSG32643; bands red/green/blue/NIR/SCL. Affine [10,0,788360,0,-10,3359030]. TIFF SHA256 55f3ca7b578e045594f8d54419b590c3ffeb99247ec5f74d7b1355d5bc4ec0f8.
At threshold0.50: 38,761 /262,144 valid pixels =14.786148% =>14.79%; all crop pixels valid; 387.61ha selected; full footprint2621.44ha. Pixel grid area100m2. At0.70 selected6899,68.99ha; at0.30 selected92841.
Old46.75%/620.09ha figures INVALID due double offset; never reuse. Legacy vsC1 raw DN differed1000 across every red/NIR pixel; calibration corrected, then independently checked using tifffile/scalar float64 vsrasterio/NumPy float32: zero selected-mask differences, tiny NDVI floating differences. Visual alignment is corroboration, not ground truth. geo.py rejects known bad raster SHA.
Area is projected grid area, not terrain/survey area; NDVI threshold coverage not vegetation health/density/species diagnosis. Quality SCL4/5/6/7 retained; all valid does not prove perfect cloud removal.

## Most recent live checks
18 scientific tests passed in WSL including actual stage alignment/mask counts/unchanged analytical exports/threshold change. Command from project: /root/satquery/.venv/bin/python -m unittest discover -s tests -v.
Fresh HTTP VQA Describe the major visible features briefly. routed to vqa and completed BUT claimed good road condition/no congestion or accidents without evidence. Retained in final-live-verification.json. Do not claim semantic quality passed. No mitigation/training performed yet.
Fresh NDVI Calculate NDVI coverage at the selected threshold. matched numbers above and four images.
Nine refusal cases passed: Compare this to last year; Count the buildings; Locate the buildings; Analyze SAR backscatter; What is vegetation health?; How green is this?; Describe vegetation and tell me its percentage; NDVI >=0.7 with control0.5; Calculate NDVI on RGB-only input.
Evaluation HTTP and browser restored23/60 vs47/60. Real browser NDVI, formulas, processing views and refusal clearing checked.
These checks predate latest UI fullscreen changes; do not claim latest full-suite rerun.

## Grounding decision
Only existing AdaptLLM checkpoint found installed. No validated detector, bbox parser, grounding evaluation set or specialist worker. geo.coordinate converts supplied pixel position to geographic coords; it does not locate objects. NDVI mask is not text grounding. Count/location requests deliberately refused. Bounded readiness assessment only; no candidate downloads or comparative grounding trials done. User wants discussion about improving VQA and adding grounding next, not automatic large downloads/training.

## Current UI — preserve user decisions
Dark: black main background, dark grey cards, white actions, gold accents. Light: beige/brown, black actions, gold accents. Decorative user art in header/footer/loading/empty state; analytical images unchanged.
Fixed viewport shell: header80px, footer100px desktop; main content between. Desktop image stays pinned, right Ask panel independently scrolls. Evaluation independently scrolls. Mobile stacked main scroll with fixed shell. Thin muted brown/gold scrollbars, transparent tracks.
User explicitly rejects image-panel scroll. Latest fix removed it, reduced globe (~55–95px), fonts and spacing, centered empty-state contents. Verified screenshot no clipping or image scrollbar at current desktop size. Very short/mobile heights not systematically tested.
NDVI result cards: coverage prominent, area and valid-data coverage; expandable How this was calculated with actual run counts, denominators, affine determinant pixel area and hectares; Source and limitations; processing views beneath. VQA plain answer preserves line breaks, no invented reasoning/evidence.
Latest static version: workspace-8 in index.html. Actual address may still say ?layout=workspace-6; harmless.
Latest additions: full-screen in-page native dialog image-viewer, img full-image, Close/Escape. Main image click (ignore drag) and new Open image full screen toolbar button; stage image links intercepted to same viewer. Full-screen means fills app browser viewport, not OS/browser fullscreen API. Main image expand chooses evidence composite when overlay shown and run artifact exists, otherwise source preview. Decorative images do not open fullscreen.
Verified main fullscreen button opens dialog and closes, compact empty state screenshot. Stage fullscreen wiring implemented but not live-click-tested yet. No fresh VQA run after these purely UI changes.
Potential test maintenance: latest app.js uses addEventListener for main image click and dialog.showModal. tests/test_ui.cjs uses simple DOM doubles that may lack addEventListener/showModal; update mocks if running this test, don't mistake a mock limitation for runtime bug. Existing test suite ran before these additions.

## Freeze/evidence artifacts
ppt_handoff/ — original comprehensive evidence snapshot (121 files in original ZIP), reports, raw predictions, calibration/independent check, figures, screenshots. Do not rewrite historical evidence to imply new runs.
SATquery-evidence-pack.zip — original snapshot.
demo-freeze-20260907/ — source snapshot BEFORE fixed-layout/scrollbar/globe/fullscreen changes, SHA256 manifest, live-verification.json, screenshots, DEMO-GUIDE.md, recorded-walkthrough.html.
SATquery-demo-freeze-20260907.zip — matching older freeze, tested ZIP integrity. NOT current working UI.
recorded-walkthrough.html is self-contained manual/timed screenshot slideshow of real UI captures; not a continuous video or live inference. No MP4 recording made. Source ZIP excludes model weights/runtime/data, not standalone installer.
backups/ contains result-layout/fixed-workspace and older copies. Do not revert whole project blindly.

## Presentation
C:/Users/nrgen/Downloads/SATQueryAI  -  TeamSN.pdf submitted, seven slides. College flexible internal rules. Our review identified outdated router-planned labels, overbroad every-answer evidence/geographic claims, blank TeamID, high text density; save for later revision, no need relitigate submission. Template C:/Users/nrgen/OneDrive/Documents/sih presentation format.pdf.

## Suggested next discussion
Improve semantic VQA safely: define annotated failure cases and a truly unseen evaluation protocol; test concise evidence-limited prompting first, then adaptation/data changes only if justified. Existing binary/rural pilot does not establish reliable free-form descriptions.
Choose grounding candidate with explicit GPU/runtime/license/RS suitability checks, then small annotated localization trial; never claim a downloaded checkpoint equals verified grounding. User will choose next scope.
Before updating demo freeze, finish targeted fullscreen/stage/mobile checks and include current source; preserve original freeze.
