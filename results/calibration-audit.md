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
