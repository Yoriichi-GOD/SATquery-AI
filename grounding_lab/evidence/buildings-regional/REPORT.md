# Regional building grounding and segmentation — 12 September 2026

## Outcome
The existing general-purpose detector and SAM do not provide reliable individual-building counts or footprints on these regional Sentinel-2 RGB images. No new default was deployed. No accuracy percentage can be computed without reference boxes/masks.

## Controlled trials
Five 512x512 RGB scenes at thresholds 0.30 and 0.20 (10 runs). Four fixed 256x256 quadrants for Assam and Bengaluru at 0.20 (8 runs). Identical pretrained checkpoints and segmentation settings. No training or reconstruction of missing image detail. All runs completed. Zero proposals mean no retained detections, not no buildings.

| Scene / tile | Threshold | Proposals | Predicted mask coverage |
|---|---:|---:|---:|
| assam-monsoon | 0.3 | 0 | 0.00% |
| assam-monsoon | 0.2 | 0 | 0.00% |
| bengaluru-lake-city | 0.3 | 0 | 0.00% |
| bengaluru-lake-city | 0.2 | 3 | 75.99% |
| jaisalmer-arid | 0.3 | 0 | 0.00% |
| jaisalmer-arid | 0.2 | 1 | 3.44% |
| punjab-farmland | 0.3 | 0 | 0.00% |
| punjab-farmland | 0.2 | 0 | 0.00% |
| sundarbans-coast | 0.3 | 1 | 5.89% |
| sundarbans-coast | 0.2 | 2 | 73.80% |
| assam-monsoon-tile-0-0 | 0.2 | 1 | 48.63% |
| assam-monsoon-tile-256-0 | 0.2 | 0 | 0.00% |
| assam-monsoon-tile-0-256 | 0.2 | 0 | 0.00% |
| assam-monsoon-tile-256-256 | 0.2 | 0 | 0.00% |
| bengaluru-lake-city-tile-0-0 | 0.2 | 2 | 70.32% |
| bengaluru-lake-city-tile-256-0 | 0.2 | 3 | 64.33% |
| bengaluru-lake-city-tile-0-256 | 0.2 | 1 | 12.41% |
| bengaluru-lake-city-tile-256-256 | 0.2 | 0 | 0.00% |

## Visual findings
- Bengaluru lower-threshold full-frame predictions include the runway and large mixed land regions. The 75.99% coverage is not building cover.
- Jaisalmer prediction spans a neighbourhood-sized region, not an individual building.
- Sundarbans default prediction covers a river-bank/water-region corner, not an established building.
- Assam first tile includes broad vegetation/settlement land.
- Bengaluru tiles include some plausible large-roof shapes, but also runway and broad land-region predictions. No general improvement in counting was established.
- The 24-object cap was never reached, so the cap is not the cause of these low counts.

## Input limitations
The regional manifests record 10-metre pixel spacing: one pixel covers a 10 by 10 metre ground cell before projection nuances. Many small roofs span very few pixels. Cropping gives the detector a closer view but cannot recover missing boundaries. No validated building ground truth exists in this trial set.

## Next requirements
Use imagery with clearly resolved individual roofs, label reference boxes/masks, then compare a building-specific model on held-out scenes. Keep these failed trials as regression cases. Do not describe threshold lowering as an accuracy improvement.

Open comparison.html for original, box and mask views for every trial. Each case includes run.json and evidence.zip.
