# SATquery demo freeze — 7 September 2026

## Verified boundary
18 scientific unit/integration tests passed earlier in this session. Fresh live HTTP: descriptive VQA completed; NDVI selected 38,761 pixels and 387.61 ha at 0.50; eight unsupported/mismatched prompts and RGB-only NDVI refused. Development endpoint reproduces 23/60 vs 47/60. Browser rehearsed NDVI, calculation expansion, evaluation and refusal clearing. Raw responses: live-verification.json.

## Known model failure
The fresh descriptive VQA answer claimed road condition and absence of congestion/accidents without adequate evidence. Successful routing is not proof of semantic correctness. Preserve this error and explain it honestly. No fresh accuracy benchmark was run.

## Bounded grounding feasibility decision
Defer and explicitly refuse for this freeze. Inspection found only the existing AdaptLLM checkpoint installed; the server has no validated object detector, box/mask-output parser, grounding evaluation or specialist dispatch. geo.coordinate maps a supplied pixel coordinate to a geographic coordinate; it does not find an object. The NDVI mask is a spectral threshold mask, not text grounding. Live locate/count prompts refused. This is a readiness assessment, not a claim that grounding is impossible or that alternative models were benchmarked. Revisit with annotated boxes, a compatible checkpoint and localization evaluation after the demo.

## Three-minute rehearsal
1. Open the local app. Load Dehradun multispectral sample. Point out filename, date and labelled bands.
2. Ask exactly: Calculate NDVI coverage at the selected threshold. Keep threshold 0.50.
3. Explain 14.79% of valid pixels and 387.61 ha of projected grid area. Expand How this was calculated: 38,761 / 262,144; pixel grid area 100 m². Do not call it vegetation health.
4. Show RGB, false colour, overlay and binary mask. The display stretch does not alter the measured reflectance.
5. Ask Compare this to last year. Show refusal and cleared old result.
6. Open Evaluation: 23/60 to 47/60 on the same 60 development questions, 20 images, one scene. Mention two regressions and format effects; not final held-out accuracy.
7. If showing VQA, use Describe the major visible features briefly. Explain that generated descriptions may overclaim and must be reviewed. Do not present road-condition or traffic claims as verified.

## Backup
recorded-walkthrough.html is a portable, self-contained slideshow of actual browser captures with manual and timed playback. It is not a continuous screen video or live inference. screenshots/ retains original captures. live-verification.json retains actual fresh answers and refusal reasons.

## Restore
source/ holds the application and tests, not model weights, WSL environment, training corpus or installed dependencies. Existing /root/satquery runtime, pinned model and sample scene remain required. Stop the existing SATquery process before restoring source or starting another server. Refresh the browser and reload the image after a restart. Do not claim this source archive alone is a standalone installer.

## Freeze policy
Keep this snapshot immutable. Apply later changes to the working project and re-verify before replacing the demo version.
