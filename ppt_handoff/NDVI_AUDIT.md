# Calibration audit — 6 September 2026

Confirmed double-offset bug in the first sample preparation. Legacy sentinel-2-l2a COG values were already offset-corrected, despite nonzero STAC offsets. Every one of 262144 compared red pixels and every one of 262144 NIR pixels differed by exactly 1000 DN from the matching Collection 1 assets. For example red minimum: legacy 111, Collection 1 1111. Correct reflectance: 111*0.0001 = 1111*0.0001 - 0.1 = 0.0111. The previous pipeline produced -0.0889.

The corrected sample uses sentinel-2-c1-l2a, S2A_T43RGP_20211125T053958_L2A. All four spectral COG headers match their STAC scale 0.0001 and offset -0.1. Preparation refuses header/STAC disagreement. Scale and offset are applied once to raw values; the packaged physical-reflectance TIFF has identity scale/offset.

Corrected result at NDVI >= 0.5: 38761 selected / 262144 valid / 262144 total pixels. 14.786148% of valid pixels and crop. Zero exclusions from nodata, negative reflectance, zero denominator or the selected SCL policy. This does not certify an absence of all cloud contamination. Grid area: 387.61 hectares. Full crop: 5120 m x 5120 m = 2621.44 hectares.

Old 46.75%, 50.60% valid and 620.09 hectares are INVALID and must not be used in slides or reports. Original invalid run retained as ndvi-invalid-v1.json for traceability; known invalid TIFF uploads are rejected. Exclusion counts now report mutually exclusive reasons.

Sources:
- https://github.com/Element84/earth-search/blob/main/README.md
- /root/satquery/scenes/reference-item.json
- /root/satquery/scenes/scene-manifest.json
- results/calibration-comparison.json

# Independent analytical verification — 6 September 2026

## Result
PASS for the corrected sample at NDVI >= 0.50. A separate TIFF decoder (tifffile 2026.3.3), scalar Python float64 arithmetic and direct TIFF geospatial-tag reading reproduced 262144 valid pixels, 38761 selected pixels, 14.786148071289062 percent and 387.61 hectares of projected grid area. No application geo.py or rasterio functions were imported.

The independently computed mask agrees with the exported application overlay at every pixel (0 disagreements). Maximum absolute NDVI difference from the application's float32 export is 0.00000010469680333802245. Pixel-scale tags read 10 x 10 m; projected CRS key is EPSG:32643, metre units. Full crop area independently reproduces 2621.44 ha. Source SHA256: 55f3ca7b578e045594f8d54419b590c3ffeb99247ec5f74d7b1355d5bc4ec0f8.

## Visual inspection
The four-panel sheet contains RGB, NIR/red/green false color, the independent mask over RGB, and the binary mask. Display stretches are used only for viewing.

Observed: the large central and south-central selected patches coincide with dark-green RGB patches and red false-color patches. The upper-central dense bright built-up region is mostly excluded. The broad winding pale/dark corridor toward the left of centre is largely excluded, while adjacent green patches are selected. These observations support gross alignment and plausibility; no obvious whole-image shift or inverted mask is visible.

## What this establishes
Together with the previous pixel-by-pixel Collection 1 calibration comparison, this supplies a source calibration check and a separately implemented numerical reproduction. The visual inspection is an additional qualitative check.

It does NOT establish independently surveyed vegetation acreage, health, species, ecological condition or a validated optimal NDVI threshold. Both computational checks ultimately concern the same satellite observation. False color also uses NIR and is not independent ground truth. RGB greenness is not a substitute for NDVI.

Slide-safe wording: “For this 25 November 2021 Dehradun crop, 14.79% of pixels meet NDVI >= 0.50, corresponding to 387.61 ha of projected grid area. Calibration cross-checked; independently reproduced.”

Artifacts: independent-ndvi-check.json, ndvi-visual-validation.png.
Reproduction: scripts/independent_ndvi_check.py. Requires the saved corrected run's local exports.

## Exact chain
Sentinel2A Collection1 L2A → 2021-11-25T05:40:34.501Z / S2A_T43RGP_20211125T053958_L2A → B04 red / B08 NIR at10m → COG/STAC agree: raw DN*.0001-.1 once → float32 physical-reflectance package with identity scales → finite/nonnegative/positive-denominator checks → SCL4/5/6/7 → (NIR-red)/(NIR+red) → >=.50.
262144 total=valid; 38761 selected; 14.786148% valid and crop. Zero exclusions under stated rules; not a perfect-cloud-mask claim.
EPSG32643, affine[10,0,788360,0,-10,3359030];100m²/pixel;3876100m²=387.61ha;crop2621.44ha.
Old values were 62009/132645=46.75% and132645/262144=50.60%, different denominators. All old exclusions were erroneous negative reflectance, not cloud/nodata. Old numbers INVALID.
Ten pixel checks: metrics/ndvi_audit.csv. Thresholds .30=35.416031%, .50=14.786148%, .70=2.631760%; monotonicity holds. Independent reproduction checks calculation, not field-survey vegetation truth.
