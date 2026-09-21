# Paired-image lab — isolated development
The existing demo at port 8765 is frozen: no imports, routing, package updates or UI changes there.
New lab uses its own data, workers and port 8767. CPU inference initially avoids competing for demo GPU memory.

## Definition of Done
- Validate count, modality, band names, units, dates, grid compatibility and provenance before inference.
- Temporal: execute an actual paired change model; preserve both inputs, change map, score, trace and supported textual answer.
- Cross-modal: execute a jointly trained Sentinel-1/2 classifier, with S1-only and S2-only ablations on identical samples.
- Automatic dispatch based on question AND input configuration, with explicit ambiguity and unsupported-task responses.
- Real labelled positive and negative trials; save predictions and metrics, including failures. Same-image controls are not independent benchmark results.
- Interface, downloadable evidence, regression tests, and unchanged-demo hash verification.

## Boundaries
ChangeFormer binary building changes do not establish gain versus loss. BigEarthNet scene classes do not produce pixel regions.
Sentinel-1/2 models do not establish Cartosat-2S/RISAT compatibility. CDVQA performance remains unproved until evaluated.
Publisher scores are not our scores. Development samples are not an untouched benchmark. Do not train on evaluation labels.
Grounding/building-count optimisation is paused. Existing VQA/NDVI/grounding demo remains separate.
