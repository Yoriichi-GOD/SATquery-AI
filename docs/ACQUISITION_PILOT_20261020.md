# Compatible imagery acquisition pilot - 2026-10-20

## Outcome

Acquired and verified one optical/SAR pilot with all 13 original Sentinel-2 L1C bands, paired Sentinel-1 imagery, source cloud QA, hand-labelled sensor validity masks and water reference files. Created a fixed 512 x 512 crop and passed the existing water-model input preparation contract. **No model inference, training or water accuracy scoring.**

This closes the band-access and traceable annotation acquisition question for this pilot. It does not close physical alignment, independent acceptance or official-sensor validation.

## Identity and selection

S1S2-Water v1.0.1, scene 7; original dataset validation split. Selected the lowest numeric validation ID with one optical and one SAR source among the 12 metadata items in archive part1, before inspecting pixels or labels. This is an acquisition pilot, not a population sample. Metadata and source IDs are retained; the now-inspected pilot must not be relabelled untouched acceptance data.

- S2: S2A_MSIL1C_20190315T032531_N0207_R018_T48QUD_20190315T075928.
- S1: S1A_IW_GRDH_1SDV_20190315T111301_20190315T111326_026348_02F25C_3077.
- Fixed crop row/column 5120/5120; 512 x 512 on the supplied SAR grid.
- Dataset license from the versioned Zenodo API: CC BY 4.0. Original Sentinel source metadata and GCS object generations are retained.

## Actual measurements and limits

- Acquisition transferred 1,355,950,608 raster/metadata payload bytes in 595.4 seconds in the completed attempt. Earlier metadata extraction transferred 23,667 bytes; the stopped first raster attempt remains on disk and adds transfer overhead not included in that completed-attempt figure.
- 21 source files verified against ZIP CRC32 or GCS MD5, with SHA256 receipts. Crop verification independently rehashed every source file.
- Prepared input shape: [1, 17, 512, 512]; finite shared input fraction: 1.000000.
- Hand-labelled validity fractions: {'s1': 0.9985923767089844, 's2': 0.9985923767089844}. These combine invalid causes; they are not cloud-only classes.
- Source cloud QA has 0 polygons; rasterized crop fraction 0.000000. This is an automated provider result, not independently verified cloud absence.
- Crop footprint overlaps 0 local Sen1Floods11 chip footprints by bounding-box intersection in WGS84. This comparison alone does not prove complete exposure independence; it covers only local Sen1Floods11 chip footprints.
- Original SAR stored values divided by 100 to obtain dB. All 13 optical bands are real original L1C bands, not padded channels.
- Optical bands reprojected with bilinear resampling onto the SAR crop grid. Grid matching does not establish physical co-registration. Independent landmarks remain required.

## Failure and method change

The first single-stream SAR transfer was too slow to fit the declared ceiling and was interrupted; its partial file and manifest remain in `/root/satquery/acquisition/s1s2-water-7`. The second attempt used eight bounded byte ranges, preserving the same scene, crop and scientific scope. Serial optical transfer was subsequently interrupted and continued with eight parallel file requests inside the original second-attempt deadline; verified assets were retained, and its partial optical bytes are included in the completed-attempt transfer figure. The complete archive was never downloaded. Its 1,500 MiB payload ceiling and 900-second time ceiling are recorded before raster acquisition.

## Artifacts and next gate

Complete source files and crop: `/root/satquery/acquisition/s1s2-water-7-v2`.
Portable receipts, source metadata, verification and preview: `.runtime/acquisition-20261020`.
Scripts: `acquire_pair_metadata.py`, `acquire_pilot.py`, `prepare_acquisition_pilot.py` under `scripts/`.

Next: review spatially distributed independent landmarks and preprocessing compatibility; complete the wider exposure inventory; then freeze a separate metadata-selected acceptance sample and evaluator before inference. The present scene is a development acquisition pilot. No sensor-general or Cartosat/RISAT claim follows.

The 22 frozen reference files and serving CDVQA checkpoint remain hash-identical.

Sources: [versioned dataset](https://zenodo.org/records/11278238), [format and annotations](https://github.com/MWieland/s1s2_water), and exact GCS object URLs in `pilot-receipts.json`.
