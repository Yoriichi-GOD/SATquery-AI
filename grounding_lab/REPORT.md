# Grounding + segmentation verification — 12 September 2026

This is development/demo evidence, not held-out benchmark accuracy. Expected object counts do not establish box or mask correctness. No independent expert mask annotations or geographically broad evaluation were performed.

## Live pipeline checks

| Case | Objects | Masks | Pipeline seconds |
|---|---:|---:|---:|
| stadium (both) | 1 | 1 | 6.453 |
| car (both) | 1 | 1 | 7.163 |
| farmland (both) | 0 | 0 | 3.04 |
| stadium (boxes) | 1 | 0 | 3.969 |
| mountain-car | 1 | 1 | 7.318 |
| river-negative | 0 | 0 | 2.908 |
| blank-negative | 0 | 0 | 2.958 |

Across six distinct source images the final selected-category object counts matched the stated demo references: stadium 1, car 1, farmland stadiums 0, second car 1, river stadiums 0, blank cars 0. The first three examples informed development; the three additional expected counts were recorded before their grounding runs. This tiny set does not measure broad recognition accuracy.

Four HTTP runs each checked eight artifact endpoints (32 successful downloads), ZIP CRC integrity, box bounds, mask union counts, instance-label consistency and per-object mask counts. Concurrent jobs were rejected before scheduling. Invalid category/mode/threshold/ID/image and cross-origin submission checks passed. All nine protected main-app source files remain SHA-256 identical.

## Preserved failures

The initial stadium run included a false whole-frame proposal alongside the stadium. The initial farmland-negative run proposed the whole frame as a stadium, even with a high model score. These motivated explicit frame/enclosure filtering; the original predictions were not deleted. The sports-complex and dense-building trials still produced merged boxes. Those categories are exploratory.

## Visual checks

Real headless Edge interaction: upload built-in sample, submit, wait for actual model output, switch processing views, open/close full-screen image, dark/light theme and mobile layout. The image panel stays fixed while controls scroll. JavaScript error capture and horizontal-overflow checks are saved with screenshots. Additional car browser verification covers settings changes clearing old results.

## Runtime

Pinned Grounding DINO Tiny + SAM Base; float32 on the RTX 5060 Laptop 8 GB. Measured peak framework allocation around 2.678 GiB in the inspected combined runs. First startup can be about 20 seconds; later model-pipeline runs were generally several seconds, excluding browser polling and worker startup. Models exit after each run.

## Next validation before routing

Collect independently annotated aerial examples across locations and resolutions. Evaluate detection precision/recall and box overlap separately from segmentation mask overlap. Improve weak classes, then freeze settings and run a fresh untouched set. Do not promote the lab to the production router based on this demo set.
