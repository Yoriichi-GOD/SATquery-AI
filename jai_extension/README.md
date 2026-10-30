# SATQuery JAI 2026 extension

New event work: a read-only Flood Lab bridge and one native-black **Terrain & flood** workspace with questions beside the selected view and evidence in closed disclosures. See [current UI and verification](../docs/jai/UNIFIED_WORKSPACE.md). A real public Copernicus GLO-90 terrain sample, numerical slope and interactive 3D are connected; grid alignment, cross-sections and bounded investigation orchestration are connected.

This repository uses the prior applications as explicitly configured external baselines. It does not claim their models, acquisition pipelines or historical results were created at this event. See [baseline provenance](../docs/jai/BASELINE_PROVENANCE.md) and [rule status](../docs/jai/JAI_RULE_COMPLIANCE.md).

## Run on the configured host

`python start_jai.py` uses the existing Python environments and local source paths. It starts Flood Lab on loopback port 8770 and SATQuery with the extension on 8768 when JAI_PORT=8768. Both ports must be free. Open http://127.0.0.1:8768/#terrain . Stop with Ctrl+C in the launcher process.

For another installation, set `SATQUERY_BASELINE_ROOT`, `FLOODLAB_BASELINE_ROOT` and optionally `FLOODLAB_PYTHON`; run `python start_jai.py` with the configured main SATQuery interpreter. Restore the existing apps/assets according to their own setup guides. The extension alone does not provision models or acquire satellite data.

## Verification

Run `python -m unittest discover -s tests -v` and `node --check jai_extension/web/earth.js`. Tests use a clearly synthetic in-process HTTP fixture. Genuine saved-run HTTP/browser receipts are stored separately.

## Data and AI disclosure

OpenAI Codex assisted implementation and verification. Prior software and dataset terms remain applicable. The flood bridge retrieves saved files. Terrain obtains one explicitly approved public GLO-90 demo tile; it does not call an AI model or acquire new satellite flood scenes. Historical SAR thresholds and map agreement retain their original limitations. Intersections do not establish damage, closures or casualty estimates. Settlement access with missing assessment is displayed as `NOT_ASSESSED`.

The adapter accepts only a configured literal loopback HTTP origin, follows no redirects, restricts files and transfer sizes, checks saved SHA-256 hashes, and never forwards arbitrary acquisition requests. The freeze map is a local integrity reference, not a signed external authenticity certificate.

On the current host set JAI_PORT=8768 because the original SATQuery already occupies 8767. Runtime logs stay under .runtime/jai and are not committed. The root README describes the original app; this extension is optional.

## Real terrain checkpoint

Open Terrain & flood for the saved Syapru GLO-90 surface. The first acquisition requires the visible public-download consent control. On this host the approved tile is already cached under .runtime/jai/terrain; that ignored data is not shipped in Git. A fresh checkout truthfully starts without it. Read ../docs/jai/DAY1_COMPLETION.md and DATA_SOURCES.md for measured results and scope.

## Alignment and investigation

Open Terrain & flood and choose a saved run. Grid mapping and water candidate markers load automatically for matching coverage. Switch the same viewer between terrain, SAR previews and the water map; ask the question in its adjacent composer. Cross-section contains point picking and metric coordinates. Stop cancels pending work. The interface labels this deterministic tool workflow and does not call an AI model. Read [completion and limits](../docs/jai/ALIGNMENT_AND_INVESTIGATION.md), [actual architecture](../docs/jai/ARCHITECTURE_JAI.md) and [replay protocol](../docs/jai/INVESTIGATION_PROTOCOL_20261030.md). A fresh clone has no real cached data or recorded jobs.
