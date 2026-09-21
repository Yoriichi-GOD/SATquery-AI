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
