# SatQuery · Flood Impact

Local IIT Mandi Track B workspace at http://localhost:8770. Original SatQuery remains on 8767. **Real Nepal evidence is available; full Track B completion is still pending.** Nothing has been published or submitted.

## Current response implementation — 5 November 2026

The isolated development checkout adds a **Response** screen: directed before/after route witnesses,
explicit unknown-coverage bounds, ranked single/joint road repairs, and a hashed KML/GeoJSON/bilingual
field kit. It reuses SATQuery's cosmic Scientific Noir identity and bundles the font licenses locally.
Open http://127.0.0.1:18870/#response while this checkout's demo service is running. The original dirty
Flood Lab checkout and SATQuery Day 1 checkpoint remain untouched.

For `nepal-syapru-004`, a four-road model repair creates **one possible route through unknown observations**;
it does not confirm physical road access. The 9.56 ha example is a separate run and remains not assessed
for routes because its saved graph has no usable service destinations.

The full suite passed **86 tests**. Live API/export checks and the core browser demo passed. The final
phone Evidence-only layout correction is not rendered-verified because browser control became disabled.
See [implementation, limitations and demo](docs/lifeline/DELIVERY.md),
[measured graph comparison](docs/lifeline/network-contract-benchmark-final.json), and
[remaining scientific work](docs/lifeline/COMPETITION_PLAN.md).

The graph comparison is synthetic directionality evidence, not improved flood accuracy or overall
superiority to Lifeline. Native matched competitor raster predictions are missing. Do not call the
scientific comparison complete. Prepared/frozen inputs are Git-ignored: a clean clone lacks the saved
demo data until the registered artifacts are installed.

## Run locally

Windows source: `C:\Users\nrgen\.codex\scratch\satquery-flood-lab`.
Run `./start-demo.ps1` in PowerShell. The current machine uses the flood Python environment at `/root/satquery-flood-lab/venv`; the optional local AI worker uses `/root/satquery/.venv`. These are machine-specific paths, not a portable installation claim.

Portable core setup: Python 3.11, install `requirements-lock.txt`, then run `python -m uvicorn floodlab.server:app --host 127.0.0.1 --port 8770`. Satellite and historical OSM acquisition require `CDSE_CLIENT_ID`, `CDSE_CLIENT_SECRET`, and `OHSOME_API_KEY` in Git-ignored `.env.local`. Never commit this file or paste credentials into reports. The AI worker additionally needs its pinned Qwen3 model and compatible Torch/Transformers runtime; see `docs/copilot-model.json`.

## Workspace workflow

Open **Analyze an area and date**, supply west/south/east/north coordinates and a past UTC flood date, then run. The bounded automatic path discovers a same-platform, same-orbit 12-day VV/VH pair, requests terrain-corrected SAR, validates scene identity and alignment, acquires a pre-event OSM snapshot, computes water candidates and infrastructure intersections, and freezes downloadable evidence. Progress reconnects after page reload; server interruption is reported as interrupted. Only one acquisition job runs at a time.

Maximum automatic area: one million 10 m pixels and 2500 pixels per side. No antimeridian support. Missing scene coverage and catalogue pagination fail closed. Automatic optical/debris proxy and historical road topology are connected and verified on a fresh Workspace API run. Empty access results do not mean no isolated settlements.

For the more complete prepared Nepal case, select `nepal-syapru-004`: SAR August 16/28, optical August 12/27, historical OSM July 27, 2026. It includes a debris proxy and a historical-node road graph. Settlement access remains unknown because of coverage/boundary and snapping limitations.

Use the copilot for evidence-backed English/Nepali answers. A local Qwen3-0.6B model selects a topic; templates insert saved calculations with source pointers. Topic selection scored 9/12 development questions before guardrails, not an independent benchmark. Select a topic explicitly when routing is wrong. Nepali wording needs human review.

## Evidence boundaries

Water baseline: VV below -17 dB after the event and a drop of at least 3 dB; fixed uncalibrated defaults. Two-date water is not proof of permanent water. Invalid pixels are excluded. All arrays load into RAM; pixelwise tiling tests do not validate tiled neural-network inference.

Debris proxy: vegetation loss to bare ground with SAR change. It can confuse clearing/agriculture and miss deposits on already bare ground. Diagnostic agreement with one EMSR927 landslide AOI: IoU 0.3279, F1 0.4939, recall 0.3285. Reference dates, resolution and class differ. This is not independent validated debris accuracy. Water accuracy has no compatible reference score.

EMSR damage labels remain evaluation-only and are not prediction inputs or threshold-tuning data. Historical road nodes preserve crossings; turn restrictions are not modelled. Exposure does not establish damage, actual closures, casualties or evacuation instructions.

## Verification

Run `python -m pytest -q --junitxml=docs/test-results.xml --disable-warnings` in the flood environment. Latest machine test report is in `docs/test-results.xml`; live download checks are in `docs/live-verification.json`. Frozen results cannot overwrite existing run IDs. SHA-256 evidence hashes are downloadable with each run.

## Remaining acceptance work

- Validate on additional compatible independent events; current automatic success covers one Nepal rectangle.
- Core saved-response browser workflow is verified; final phone Evidence correction, projector sizing,
  and the redesigned cold acquisition workflow remain unverified.
- Independent validation, meaningful operational timings, Nepali review.
- One-page sitrep and two-page technical report are rendered and checked in output/pdf; record the three-minute demo.
- Public repository/submission require separate authorization. Existing-code reuse must be disclosed; organizer permission was not established.

Attribution: Copernicus Sentinel data and Copernicus DEM; OpenStreetMap contributors (ODbL), HeiGIT/ohsome historical extraction; Copernicus EMS reference products (evaluation only); Qwen/Qwen3-0.6B (pinned revision in model record). Retain upstream license terms and acquisition provenance when distributing data or software.

Comparison attribution: [kinnuworks/lifeline](https://github.com/kinnuworks/lifeline), pinned revision
`2945725810d6088317f65e3edb72db578c0b9528`, MIT copyright Dhiraj Kavuri 2026. Its audited numerical
kernel is exercised only by the comparison harness; new response code is independently implemented.
The original MIT notice is retained in `docs/lifeline/LIFELINE_LICENSE.txt`. SATQuery's user-supplied
identity artwork and locally reused Fontsource binaries are inventoried in `docs/lifeline/UI_ASSETS.json`.

AI assistance: Codex assisted the response implementation, tests, source audit, comparison, cosmic UI
integration and documentation. The pre-existing dirty baseline was preserved separately in `1ec2a11`;
it is not represented as newly created work. The copilot remains topic routing plus saved-value templates,
not an autonomous flood-mapping model. No messages were sent, models trained, new satellite data acquired,
or scientific superiority demonstrated by this implementation.
