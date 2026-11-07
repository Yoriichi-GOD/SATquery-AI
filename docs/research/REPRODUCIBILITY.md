# Scientific execution and reproducibility

Use Python 3.11 on Linux/WSL. This CPU scientific package does not require Torch, GPU,
model weights, a hosted account or modifications to the existing inference environments.
Full satellite acquisition and the original neural specialists retain their own provisioning requirements.

```sh
python3.11 -m venv .venv-scientific
. .venv-scientific/bin/activate
python -m pip install -r research/requirements-scientific-lock.txt
python -m unittest discover -s tests -v
python -m research.terrain_exposure.demo --output research/results/local-example/synthetic
```

The last command is explicitly synthetic software evidence. The genuine public examples below
are different populations. Existing benchmark scores are not recomputed by these commands.

## Public real-terrain examples

```sh
python -m research.cases.urban --config research/cases/varanasi.json \
  --cache .runtime/scientific/public-dem --output research/results/local-example/varanasi
python -m research.cases.urban --config research/cases/sangam-vihar.json \
  --cache .runtime/scientific/public-dem --output research/results/local-example/sangam-vihar
```

Each tile is capped at 16 MiB, uses a public HTTPS source with TLS verification and no credentials,
and must match the pinned source SHA-256. Partial downloads use ETag/Range verification where
the server supports it. Changed source versions fail closed. Caches without matching receipts are rejected.
STAC searches retain the exact query, response and truncation status. They do not download/process imagery.
Both cases withhold street-scale connectivity under the declared 5 m target-width gate.
The exploratory windows are not authoritative municipal or cadastral boundaries.

## Retained Nepal case

Set `FLOOD_ROOT` to an independently provisioned Flood Lab checkout containing the original
`artifacts/runs/event-fe47db331390`, its 15 frozen files and corresponding `data/automatic` sources.
Set `NEPAL_DSM` to the genuine retained public GLO-90 source tile; its required hash is in `research/cases/nepal.json`.
Use a fresh output directory for each run. The code refuses to overwrite a completed run.

```sh
export FLOOD_ROOT=/path/to/satquery-flood-lab
export NEPAL_DSM=/path/to/Copernicus_DSM_COG_30_N28_00_E085_00_DEM.tif
export OUT=research/results/local-replay
python -m research.terrain_exposure.replay --flood-root "$FLOOD_ROOT" \
  --terrain-source "$NEPAL_DSM" --output "$OUT/terrain-exposure-nepal"
python -m research.registration.diagnostics --flood-root "$FLOOD_ROOT" \
  --output "$OUT/registration-nepal.json"
python -m research.experiments.nepal --flood-root "$FLOOD_ROOT" --terrain-source "$NEPAL_DSM" \
  --prediction-run "$OUT/terrain-exposure-nepal" --registration-audit "$OUT/registration-nepal.json" \
  --output "$OUT/nepal-road-screening"
python scripts/verify_terrain_exposure.py "$OUT/terrain-exposure-nepal" \
  --experiment "$OUT/nepal-road-screening" --output "$OUT/independent-verification.json"
python -m research.evaluation.figures --experiment "$OUT/nepal-road-screening" \
  --terrain-run "$OUT/terrain-exposure-nepal" --output "$OUT/figures"
python -m research.experiments.analyst --flood-root "$FLOOD_ROOT" --terrain-source "$NEPAL_DSM" \
  --terrain-run "$OUT/terrain-exposure-nepal" --output "$OUT/analyst-scripted"
```

The experiment additionally requires the unchanged independent EMSR927 AOI01 GeoPackage in
`evaluation_only/emsr/`. Its required hash and class policy are frozen in
`research/experiments/nepal-road-screening.json`. This is road-grade screening association,
**not compatible water/debris extent validation**. A failed registration audit does not become a pass:
it remains in the report and prevents a validated-accuracy claim.

Source acquisition/provisioning remains documented in the existing [data-source guide](../jai/DATA_SOURCES.md)
and Flood Lab. A fresh CDSE response is not guaranteed to be byte-identical to the retained products.
Do not substitute a newer source or alter frozen hashes to force a replay to pass. Dataset/imagery
licenses are separate from the code license; no weights or restricted imagery are included here.

## Application integration

Use the existing extension startup instructions with this branch as `SATQUERY_BASELINE_ROOT`.
Add `JAI_TERRAIN_EXPOSURE_ROOT=/absolute/path/to/research/results/local-replay`.
Only operator-configured local runs are served. HTTP accepts opaque IDs and cannot fetch URLs,
choose local file paths or run an unfrozen scientific experiment.

Questions about catchments, HAND, drainage, pathways and flow accumulation use
`get_terrain_exposure`. Building/road-scale downstream questions abstain if the scale gate fails.
Use `python scripts/verify_scientific_http.py --base http://127.0.0.1:18868 --output /new/receipt.json`
against the isolated test service, or the documented primary port after deployment.

## Files and independence

`research/results/terrain-exposure-20261105/` contains small reviewable receipts and figures.
`research/results/local-20261105/` retains the complete local exports, original run manifests,
reference-unit rows and data products; it is Git-ignored. Raw third-party sources remain external.
Earlier development attempts are retained in ignored `.runtime/scientific`, including the oversized
first export and the preliminary D-score implementation. The final experiment explicitly calls
the shared graph engine. Neither preliminary result is used as the final metric source.

The Nepal data have been inspected in previous work: they are **development replay**, not untouched test data.
No train/test generalization, calibrated uncertainty or human productivity result is claimed.
Future calibration needs a separate development geography and untouched evaluation geography;
`reject_spatial_leakage` rejects intersecting support geometries. No such independent split is currently available.
