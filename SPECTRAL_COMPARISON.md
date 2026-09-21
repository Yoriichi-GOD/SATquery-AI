# Two-date spectral comparison — verified 21 September 2026

Status: implemented, experimental. This closes the first bounded multi-parameter comparison item. It does not establish general land-cover change accuracy.

## Supported behavior

Upload two compatible optical surface-reflectance TIFFs, ordered before/after. “Analyze these images” selects NDVI vegetation and Green/NIR NDWI water candidates. “Compare vegetation” and “Compare water” execute only their respective parameter. Results precede execution details; separate cards expose thresholds, common valid pixels, gain/loss, net coverage and calculations. Selectable maps sit in the image viewer. Broad analysis explicitly reports built-up expansion unavailable.

The CPU computes indices, not model inference. NDWI candidates are not WaterUNet output, confirmed water or flood extent. NDVI threshold changes do not establish vegetation health, land-cover conversion or urban growth.

## Input contract and manual preparation

Sentinel-2 surface reflectance, matching sensor tags, strictly ordered dated observations, matching projected metre CRS/grid/dimensions/affine transform, named Red/Green/NIR bands and genuine SCL quality labels. Band scales and offsets are applied. SCL is unscaled. Required bands depend on the requested parameter. Missing Green can leave vegetation available while water is unavailable.

Source preparation, calibration, reprojection and physical co-registration remain outside this workflow. Matching metadata does not prove physical alignment. The supplied SCL labels are trusted; no new cloud model runs. Each parameter uses common valid pixels at both dates: SCL 4/5/6/7, finite nonnegative bands and nonzero denominator. Defaults NDVI >= 0.5 and NDWI >= 0 are exposed controls. Inline threshold requests are refused with guidance to the controls rather than silently ignored.

## Verification and Definition of Done

- 64 regression tests passed, including known synthetic changes, numerical exports, quality masking, partial results, invalid dates/grid/sensor/calibration and routing.
- JavaScript syntax check passed.
- Three actual API runs on an external Varanasi crop completed: broad, vegetation-only, water-only. Independent calculations from the original input arrays matched exported changes; archive integrity and exact original input bytes were checked.
- Reversed dates, an inline threshold request and forecasting were refused.
- Browser upload/run completed; parameter cards, map selection and expanded calculations verified. Browser run 907e5dbbfb5245f18ce4c7de98f2e2cd reported 0.52 seconds specialist execution. This excludes upload, preparation and review and is not a performance benchmark.

## External reference case

Two 512 x 512 Sentinel-2 C1 L2A crops near 83.01 E, 25.30 N: 2024-11-30 and 2025-11-07, obtained through Earth Search. Scene identities, source STAC metadata, calibrated TIFFs and verification outputs are preserved in paired_lab/evidence/spectral-pair-20260921. These are a roughly 5.12 km square crop, not the whole city or a 2016–2026 study.

Common valid pixels: 261,312 / 262,144. At the default thresholds, vegetation-selected pixels changed 11,128 -> 49,093; water-candidate pixels changed 26,865 -> 47,776. These are threshold-selection observations, not labelled accuracy or verified environmental change. Different dates, season, illumination, source processing and registration may affect interpretation. No ground-truth evaluation of this pair was performed.

Downloadable evidence includes original inputs, run JSON, per-parameter three-band before/after/delta GeoTIFFs, numerical NPZ arrays and PNG change views. Source calibration checks and acquisition provenance are in the reference-case manifests. The fetch and verification scripts are archived as environment-specific verification records, not portable deployment tools.

## Code references

paired_lab/spectral_pair.py: requested, validate, analyse.
paired_lab/controller.py: spectral routing and request restrictions.
paired_lab/server.py: preflight validation, execution and artifact access.
paired_lab/inputs.py: tagged reflectance ingestion.
paired_lab/web/app.js and index.html: result cards and threshold controls.
tests/test_spectral_pair.py: numerical and compatibility regressions.

## Remaining scope

Built-up expansion, arbitrary sensor support, general multi-model composition, three-plus-image timelines and forecasting remain unimplemented in this path. Description reliability and broader independent scientific evaluation remain priorities. Preserve the existing VQA, temporal and optical-SAR specialists; this spectral path does not replace them.

Source-view follow-up: before/after RGB previews appear alongside change thumbnails when genuine Red/Green/Blue bands exist. Both dates use a fixed 0-0.3 reflectance display stretch; invalid pixels are black. Original TIFFs remain unchanged in the evidence archive. Missing RGB bands do not fabricate a colour preview.

Dated comparison follow-up: each parameter now has a three-panel before/after/change PNG, with acquisition dates and selected-pixel counts below each state. Both state panels share the same threshold and common-valid denominator; green means threshold-selected in those panels. The third panel retains green gain, pink loss, grey retained and black invalid. Individual change maps and RGB sources remain available. The overview stacks the requested parameter comparisons.
