# Flood integration verification — 30 October 2026

New adapter/origin suite: 24 passing tests in the existing WSL Python 3.11 environment. Synthetic HTTP fixtures cover path traversal, loopback restrictions, redirects, transfer caps, invalid metadata, NaN, changed hashes, unknown runs, missing service and truthful connectivity status.

Actual HTTP receipt: 28 passing checks at loopback port 8768; all 15 artifacts of genuine historical `event-fe47db331390` matched their existing saved hashes through the new adapter. Original `/api/status` and `/api/samples` returned 200; allowed extension origin returned 200 and a foreign origin returned 403. Values matched the saved summary, not hardcoded UI figures. See `live-flood.json`.

Browser: native Flood Intelligence tab displayed the real saved summary, candidate map and source provenance. After-SAR preview completed with natural width 254. Switching to `nepal-syapru-004` changed the title; Workspace navigation restored the original lab; returning retained the selected run. No console warnings/errors were captured at this checkpoint. Screenshots checked at 1280×720 and 390×844; no document-level horizontal overflow. This is bounded flood-panel verification, not a complete browser regression or scientific accuracy benchmark.

Known limits at this checkpoint: unavailable-service and corrupted artifacts are covered by software tests; their browser states have not yet been driven. Candidate/source images share the recorded raster display but are not overlaid on a physical basemap. Range requests are not forwarded; artifacts have a 16 MiB maximum. Local freeze metadata is trusted, not cryptographically signed. Existing 8767 service is left running; extension uses 8768 and validates its own origin before adapting to the baseline 8767 policy.

## Full baseline suites at the extension checkpoint

Main application: 141/141 passed (117 existing + 24 extension). Flood Lab: 69 passed, 1 failed, 31 warnings. The unchanged test tests/test_nepal_registration.py expects damage_features_inspected=False, while the existing current dataset-readiness.json records True following earlier reference inspection. This historical-state assertion is not green; no saved reference record or old test was rewritten to conceal it. The original source audit hashes still match.
