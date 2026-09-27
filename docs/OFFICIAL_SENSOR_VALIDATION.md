# Official sensor checks — 27 September 2026

## Verified progress

The prepared official Cartosat-2E crop completed optical description inference in the preceding pass. [Actual run](../paired_lab/evidence/compliance-20260926/cartosat-vqa.json). This is a single-sample functional check, not a sensor accuracy benchmark.

This pass added an explicit EOS-04 calibration primitive and a sample preparation command. It follows the [NRSC EOS-04 Handbook](https://bhoonidhi.nrsc.gov.in/bhoonidhi_resources/help/docs/EOS-04_Handbook.pdf), section 4.5, printed pages 66-68:

`beta0_linear = (DN^2 - Image_Noise_Bias) / 10^(Calibration_Constant_Beta0 / 10)`

The implementation was executed on a native central 512 x 512 crop of the official FRS2 product 237516861, using the constants supplied for each polarization. It exports signed linear beta0 and positive-only beta0 in dB. Nonpositive corrected values remain in the linear raster; dB is NaN there. Native zero DN samples are conservatively excluded, explicitly recorded; none occurred in this crop.

| Polarization | Positive corrected pixels | Nonpositive corrected pixels |
| --- | ---: | ---: |
| HH | 261424 | 720 |
| HV | 229066 | 33078 |
| VH | 236024 | 26120 |
| VV | 261686 | 458 |

These counts describe calibration validity, not water/land classes or accuracy. Beta0 is not sigma0. The output is not passed to Sentinel-trained models. No terrain flattening, segmentation or fusion claim is made. This is currently a CLI preparation step, not an integrated UI workflow.

[Calibration report](../paired_lab/evidence/official-20260927/calibration.json), [native metadata](../paired_lab/evidence/official-20260927/BAND_META.txt), [linear GeoTIFF](../paired_lab/evidence/official-20260927/beta0-linear.tif), [dB GeoTIFF](../paired_lab/evidence/official-20260927/beta0-db.tif), [preparation script](../scripts/prepare_eos04_sample.py).

Validation: four new tests cover known power/dB values, noise bias and nonpositive values, uint16 overflow prevention, and invalid inputs. The full software suite passed 80/80. A scalar calculation was independently checked against each polarization's actual result. This verifies numerical implementation, not physical calibration against reference targets.

## Pair discovery result

Read metadata from five additional public EOS-04 archives and a second Cartosat multispectral archive. Combined with the previously downloaded products, two optical products and six SAR products form 12 possible combinations. All 12 have disjoint geographic bounding boxes. They cannot constitute a registered optical/SAR pair.

[Screening record](../paired_lab/evidence/official-20260927/pair-screening.json). New archive inspections used complete small metadata entries from incomplete ZIP prefixes; whole-archive integrity is not claimed for those. The two original fully downloaded archives have separate hash/CRC evidence.

The public PAN archive starts with a large TIFF. Its metadata was not available in the small prefix inspected, so it remains unassessed. This search does not establish that no compatible official products exist.

The [Bhoonidhi API documentation](https://bhoonidhi.nrsc.gov.in/bhoonidhi-api/) requires account authentication for catalogue search/download. No credentials were supplied or searched for. Access availability for high-resolution Cartosat products must also be confirmed; an account does not itself prove entitlement.

## Still open

- Obtain a compatible official optical/SAR pair with suitable dates and verified registration.
- Establish the inference path's sensor/band/radiometric compatibility. Matching files alone cannot make the current Sentinel specialists valid for EOS-04/Cartosat.
- Validate predictions against appropriate reference labels. Until then, report functional or numerical checks only.

No official paired accuracy result, full compliance, or competitive superiority is claimed.
