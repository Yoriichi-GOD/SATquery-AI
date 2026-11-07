# Validation campaign: reproduce the measured prerequisites

Read [the report and limitations](../../research/results/validation-closure-20261107/REPORT.md) before
quoting metrics. This adds research CLI/data-adapter work; it does not change UI, application APIs,
model inference, original case measurements, or the immutable Day1 checkpoint.

Use a Python3.11 environment with `research/requirements-scientific-lock.txt`. The locally tested
persistent environment is `.runtime/validation-env` in WSL; the earlier `/tmp` environment disappeared
between runs. No training, model download, paid call or authentication credential is needed for these
commands. Dataset access may fail independently of the software. Use new output folders; never
delete an existing experiment to conceal a failed acquisition or score.

The protocols are in `research/experiments/`:

- `validation-closure-20261107.json`: Delhi extraction/measurement and Kedarnath QA-only selection.
- `worldfloods-blind-20261107.json`: consumed six-event component test. Repeating this is a replay.
- `nepal-postevent-2m-20261107.json`: post-event2m suitability and quality gates.
- `worldfloods-reserve-20261107.json`: four unopened activations. **Do not execute during development.**

## Official drainage

```bash
python -m research.datasets.delhi_reference --output research/datasets/local/NEW/delhi-official
python -m research.experiments.delhi_drainage \
  --sources research/datasets/local/campaign-20261107/sangam-vihar \
  --reference research/datasets/local/NEW/delhi-official \
  --output .runtime/NEW/delhi-analysis
```

Public GSDL native feature IDs and geometry are queried by the frozen envelope, with count/batch/hash
checks. A feature returned by an envelope query may only touch the boundary; analysis clips its actual
geometry to the ROI. Unknown feature epochs stay unknown. The source is not complete surveyed ground
truth and no native redistribution license was established. Raw vectors remain private locally.

## Historical quality-only selection

```bash
python -m research.cases.kedarnath_quality \
  --baseline research/datasets/local/campaign-20261107/kedarnath \
  --output research/datasets/local/NEW/kedarnath-quality
```

The actual run found no eligible scene. Catalogue footprint and common QA-clear gates are checked
before reflectance change or registration. The strict25% threshold was not reduced after observing
19.56% coverage. A later experiment may rationally use a different predefined ROI/coverage policy, but
must be versioned as a new protocol, not silently substitute a convenient scene into this result.
`strict_alignment()` in the new module requires an uncorrected held-out p95 displacement threshold;
post-fit error alone cannot pass an uncorrected product. It does not certify ground control/SAR alignment.

## Consumed external component test

```bash
python -m research.experiments.worldfloods_component \
  --output research/datasets/local/NEW/worldfloods-component-v1
```

This command executes the same already consumed six-event protocol, not the unopened reserve.
It uses author-hosted WorldFloodsv2 at the frozen Hugging Face commit, reads native centre windows,
and seals all predictions before reference acquisition. It does not install or train a model. Reference
labels are curated total water with clear/cloud/invalid masks, not new water or exposure. Input
reflectance indices and30m-native slope are computed without labels. Only final metrics use reference
clear support. Large global tiles/full archives are not downloaded. Output raster band order is saved
explicitly; JSON key order must never be substituted for it.

```bash
python scripts/verify_validation_closure.py \
  --sources research/datasets/local/validation-20261107 \
  --output .runtime/NEW/independent-recount
```

The verification tool recounts persisted prediction/reference arrays independently and obtains source
metadata only after prediction/scoring. The reviewed receipt lives under the research report's
`verification/independent-recount/`. It is independent arithmetic code, not an independent expert review.

## Finer Nepal terrain

```bash
python -m research.datasets.nepal_postevent \
  --output research/datasets/local/NEW/nepal-postevent2m
python -m research.evaluation.postevent_support \
  --terrain research/datasets/local/NEW/nepal-postevent2m \
  --run components/floodlab/artifacts/runs/event-fe47db331390 \
  --output .runtime/NEW/postevent-support.json
```

The terrain adapter uses HTTP-range native windows inside stored ZIP/COG members. The native2m
DEM/count grids must match. Reported count≥2 is a conservative engineering screen, not calibrated
accuracy or independent stereo-pair support. Native masks are kept separate from modeled5m/30m
terrain derivatives. Post-event ellipsoidal heights cannot be differenced with EGM2008 heights without
datum harmonization, nor treated as pre-event inputs. Full-case quality coverage fails the95% gate.

## Acceptance and integrity

```bash
python -m unittest discover -s tests -q
# Separate Flood Lab environment, from components/floodlab:
python -m pytest -q
```

This campaign passed312 main and86 component tests. The changed source did not modify browser flows;
browser checks and fresh specialist inference were not run. The prior evidence pack and day1-final are
hash/commit checked separately. Small derived report artifacts are tracked; acquired raw rasters,
reference geometry and environments are ignored. AI assistance: Codex implemented acquisition,
measurement, independent arithmetic checks and documentation; no expert certification is implied.
