# Same-port integration — 12 September 2026

Current entry: http://localhost:8765/ ; Grounding Lab: http://localhost:8765/grounding/ . Start root start.ps1 or grounding_lab/start-lab.ps1, not both. The standalone 8766 service was stopped. Main navigation and manual lab navigation were browser-tested.

This shares hosting, not question routing. routing.py, geo.py, counting.py and model-answer code are unchanged by this integration. server.py mounts the lab and coordinates resource use; web/index.html adds navigation; web/app.js limits view-switch handlers to actual data-view buttons. Lab asset/API paths are relative to its mount.

One busy gate serializes main analysis and lab work. Starting a lab run releases the idle main VQA model and clears its CUDA cache. Grounding DINO is unloaded before SAM loads; the worker exits afterward. The next VQA request reloads its checkpoint. Other GPU applications are not stopped. The lab checks for 3 GiB free at worker startup. Setup/worker failures release the busy gate. No claim that three models coexist on the GPU is made.

## Verification
- Existing main suite: 39 tests passed.
- New coordination checks: 3 passed, including busy visibility and setup/worker failure cleanup.
- Mounted HTTP: stadium both=1, car both=1, farmland asked stadium=0, stadium boxes-only=1. Eight artifacts checked per run (32 downloads), ZIP integrity and mask/ID/pixel-total consistency passed. Input and cross-origin checks passed.
- Browser: main link to lab, sample upload and real stadium inference, image views, fullscreen, fixed image panel, light theme, 390x844 mobile without horizontal overflow; no JavaScript errors. evidence/same-port-browser.
- Real VQA -> lab -> VQA cycle completed, with cross-page concurrent submissions correctly rejected. The same stadium was used throughout. End-to-end times: 27.907 s, 23.570 s, 18.401 s. Both VQA answers identified a stadium; lab proposed one stadium. These are individual runs, not latency percentiles or an accuracy benchmark. evidence/same-port-cycle.
- Worker peak PyTorch allocation for the stadium: 2.678 GiB. This is not whole-device VRAM. Whole-device snapshots include desktop/other allocations and are saved in cycle summary.json.

## Interpretation
26.3583% = 34,793 union-mask pixels / (500*264 full source pixels) *100. No denominator crop or physical-area conversion. Visual/geometric plausibility does not validate mask boundaries.

Earlier farmland false-positive whole-frame proposal was removed by a development heuristic; this scene informed the filter and is not held-out evidence. River asked stadium and blank asked car also returned zero in preserved additional tests. No manually labeled bounding-box/mask benchmark is loaded. No mAP, measured mask IoU or general accuracy claim is supported. Dense-building and baseball-complex failures are preserved.

The original v1 ZIP and MANIFEST are historical standalone snapshots, not packages of this integration. Current source plus this report and same-port evidence describe the updated app.
