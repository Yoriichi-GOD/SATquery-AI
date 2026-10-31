# THE ROAD HOME — judge demonstration

Open **http://127.0.0.1:8768/#terrain**, choose saved **event-fe47db331390** and real **terrain-45737e0da2983d9d**. This is the existing saved Syapru Besi investigation, integrated during Day 2; the candidate science predates this integration.

| Time | Show | Say / verify |
|---|---|---|
| 0:00–0:30 | THE ROAD HOME, Syapru Besi, Nepal | “After a disaster, people need to know which roads and homes may need inspection. This workspace keeps the observations and their limits together.” |
| 0:30–1:00 | Before → After | Genuine Sentinel-1 displays: **16 → 28 August 2026**. They are recorded radar views, not optical photographs or live feeds. |
| 1:00–1:40 | Water → Debris → Both | Water: **9.56 ha**, **956 candidates / 99,858 valid SAR pixels**. Possible debris/surface change: **10.41 ha**, **1,041 candidates / 30,239 valid debris pixels**. Optical proxy dates **22 → 27 August**. Gray means invalid, not observed absence. |
| 1:40–2:20 | Infrastructure evidence | Water intersects **2 mapped buildings** and **185.846 m roads/bridges**. Debris proxy intersects **71 mapped buildings** and **1,458.934 m roads**. Read source IDs and observed/total coverage. These are separate possible-exposure populations; never sum them. No closure or damage is confirmed. |
| 2:20–3:00 | Terrain | Real historical **90 m Copernicus DSM**, opaque surface, slope and existing cross-section. Candidate markers on this surface are not water/debris height or depth. Grid reprojection is checked; physical co-registration is not independently validated. |
| 3:00–4:00 | Ask, then evidence/tool trace | “Which mapped buildings and roads intersect water or possible debris-change candidates, and what can we verify?” Verify `get_run`, `get_exposed_assets`, `get_debris_evidence` and separately linked sources. Download source TIFF/CSV and recorded trace. |
| 4:00–4:40 | Unsupported question / missing evidence | Ask “Which road is safe for evacuation?” The workflow abstains. Settlement access is **NOT_ASSESSED**. Missing evidence never becomes a fabricated zero. |
| 4:40–5:00 | Return to connected observations | “We help investigators see where the evidence points and where uncertainty remains. Field confirmation is still needed to establish whether there is a road home.” |

## Three-minute version

Spend 30 seconds on before/after; 60 seconds on separate water/debris and infrastructure values; 30 seconds on real terrain; 60 seconds on the supported question and trace. Leave the detailed protocol/reference discussion for cross-examination.

## Defensible statements

- The Nepal question workflow is deterministic saved-evidence orchestration. It does **not** call an AI model. Existing specialist ML routes remain available elsewhere in the app; do not call this a newly trained debris agent.
- Debris is a fixed vegetation-to-bare, NDVI-loss and SAR-change proxy, **not a trained or independently validated debris classifier**. Clearing/agriculture can be confused and already-bare deposits missed. SCL support is resampled from 20 m. EMSR927 is class-mismatched checking evidence, not debris accuracy.
- Infrastructure comes from a historical OSM snapshot **25 August 2026**; missing assets are not counted. Feature intersections are possible exposure, not destroyed buildings or verified road closures. Connectivity was not assessed.
- Hash verification checks the local saved freeze map, source artifact linkage and reproducible calculations. It is not a signed external source-authenticity certificate.
- No retraining, source acquisition, new accuracy benchmark, damage estimation, forecast, evacuation routing or model download is part of this one-hour integration.
- The provisioned local demonstration uses retained inputs and existing services. A clean clone still requires the documented external assets; do not promise arbitrary universal offline acquisition.

## Fallback if the narrative frontend cannot load

The existing main application remains the demo. Inspect actual source JSON at `/api/flood/runs/event-fe47db331390`, then `/api/flood/runs/event-fe47db331390/debris`, the two verified native candidate previews and their artifact downloads. The independent debris endpoint retains all feature IDs, coverage, source hashes, dates and limitations; do not replace a failed view with illustrative screenshots. Final receipt states which browser steps actually passed.
