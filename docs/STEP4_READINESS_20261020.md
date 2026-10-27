# Step 4 - quality evidence and fresh-data readiness

## Status

Input audit and review handoff implemented and exercised. Fresh acceptance is **not ready**:
cloud labels, independent physical alignment measurements and compatible independent paired inputs remain missing.
No new training, model inference, model changes or benchmark scores.

## Measured on local assets

- Audited all 89 existing Sen1Floods11 validation pairs, with per-input SHA256.
- All 10 named validation events also appear in training and historical test. None of the 446 enumerated local split members is a new untouched candidate.
- Matched event-level acquisition dates for 83 chips; 6 Mekong chips have no exact event metadata match. No Cambodia/Mekong alias was invented.
- Available absolute date gaps range from 0 to 2 days. These are event-level metadata, not authenticated per-chip sensing times.
- All 89 pairs share CRS and shape. Maximum grid-corner discrepancy is 2.34642582605e-10 pixels. This is metadata agreement, **not measured physical co-registration**.
- Zero verified cloud fractions and zero physical landmark residuals. Missing measurements remain null.
- Sensor-specific and shared finite-pixel coverage are recorded separately. Finite pixels are not automatically cloud-free.

An 89-row review queue records required cloud-mask provenance, independent landmark coordinates, projected CRS and reviewer identity. It contains no invented annotations.

## Fresh-data candidate and compatibility check

[S1S2-Water v1.0.1](https://zenodo.org/records/11278238) has a downloaded, SHA256-pinned catalog with 65 item links. Only the 11,717-byte catalog was downloaded; individual metadata and raster archives are not present. Catalog links refer to files inside the dataset distribution, not independently downloadable files at those relative web addresses.

The [authors' format specification](https://github.com/MWieland/s1s2_water) describes six optical bands and SAR values scaled by 100. The current water model explicitly requires 13 optical bands and unscaled dB. Direct inference would be invalid. Missing bands must be acquired from authenticated original L1C products; filling them with zeros would change the experiment and is not approved by this protocol.

The provided validity masks combine cloud, shadow and nodata: they are useful coverage annotations but not separate cloud labels. The task is surface-water segmentation; it cannot certify flood-only, temporal-change or official Cartosat/RISAT performance.

No candidate is labelled unseen until its scene IDs, dates, footprints and hashes have been compared with the full exposure inventory. Dataset novelty alone is insufficient.

## Review protocol

For physical alignment, select at least six stable corresponding landmarks distributed across the common footprint, away from water changes, cloud and SAR layover. Record source image hashes, pixel coordinates, conversion to the same projected metre CRS, reviewer and selection rationale. Use independent points not used to fit a warp. Record ambiguity; do not force a match. The measurement helper reports signed displacement, median, p95 and RMSE and does not estimate a corrective warp. Three points are its computational minimum, not the review sampling target.

For cloud quality, acquire a source QA mask or independent reviewed cloud/shadow annotations; record product/version, encoding, timestamp, footprint and source hashes. Automated QA is a proxy unless validated. Keep masks and water references separate and preserve the baseline common-valid denominator.

Before scoring fresh data, close every requirement in `.runtime/step4-20261020/fresh-candidate.json`; then freeze sampling, evaluator and resource limits. No tuning on acceptance outcomes.

## Verification and recovery

Five targeted tests passed: known 3/4-metre displacement gives 5-metre RMSE; missing/nonfinite landmarks fail; identical grids, known pixel shifts and floating-point roundoff behave correctly. Full real-input audit completed after a missing-event fix.

The first audit stopped on the unrecognised Mekong name. Its pre-run manifest remains in `quality/`; the corrected run in `quality-v2/` leaves those dates null. This prevents a silent, unverified join.

Existing serving assets and the 22 frozen reference files are checked again in `closure.json`. No production code changed. This step adds experiment tooling and evidence only.

## Reproduction

`python scripts/audit_quality_readiness.py --data /root/satquery/paired-lab/sen1floods11 --out NEW_DIRECTORY`

`cd scripts && python -m unittest test_quality_readiness -v`

Evidence: `.runtime/step4-20261020/quality-v2/manifest.json`, `measurements.json`, `review-queue.csv`, `fresh-candidate.json`, and `s1s2-water-catalog.json`. The utility refuses to overwrite an output directory.
