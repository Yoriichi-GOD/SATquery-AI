# Final downloaded-official-sample test report — 27 September 2026

**Downloaded-sample testing completed. Full Cartosat–RISAT solution compliance is not established.** Paid acquisition has been stopped at the user's direction; no purchase/order was submitted. A saved priced-cart entry is not an order.

## Final results

| Check | Result | Scope |
| --- | --- | --- |
| Both complete source ZIPs | PASS | SHA-256 and full archive CRC verified |
| Cartosat crop preservation | PASS | 1,048,576 native band values and geographic grid compared with original archive |
| Cartosat RGB input | PASS | Verified blue/green/red/NIR identities; 512 x 512 native crop |
| Cartosat actual description inference | PASS (execution) | Fresh HTTP upload and pinned model run completed; no reference-label accuracy score |
| EOS-04 FRS2 calibration | PASS (numerical) | 1,048,576 saved values independently recomputed across HH/HV/VH/VV |
| Unsafe analysis prevention | PASS | DN-based NDVI, unsupported EOS-04 model transfer and geographically unrelated water pair refused |
| Software regression | PASS | 80 tests, 2.872 s; no failures |

The detailed artifact has nine executable official-sample checks. The separate model run and software suite are reported separately; these counts are not accuracy measurements.

## Model run

Question: Describe this image.

Raw answer: Many buildings and green trees are in a dense residential area.

Fresh run: 23.831 s total; checkpoint loading 9.925 s; answer generation 8.526 s; peak allocated GPU memory 4.243 GiB. These are one-run measurements. Earlier execution of the same crop took 17.137 s and produced the same text; neither run establishes a latency distribution or independent generalization. Description completeness remains limited and was not scored by an independent annotator.

## Calibration verification

The implementation uses product beta0 constants and polarization-specific noise bias from the official metadata. An independent expression recomputed the saved float32 outputs from original DN values. Largest absolute difference across all four bands: 2.351e-7 in linear beta0 and 1.762e-6 dB, within the predefined numerical tolerances. Geographic grid and undefined dB locations were also checked.

Nonpositive noise-corrected values: HH 720; HV 33,078; VH 26,120; VV 458. These remain in signed linear output; their logarithmic values are invalid. This is beta0 calibration, not water segmentation, field-reference calibration validation or sigma0/terrain normalization. The preparation remains a CLI step.

## What this closes

Official Cartosat optical ingestion/inference smoke testing, official EOS-04 product calibration verification, source integrity/provenance, and incompatible-input refusal checks.

## What this does not close

- The downloaded Cartosat and EOS-04 images depict different locations and dates. They cannot validate paired fusion.
- The current Sentinel specialists do not support semantic EOS-04/RISAT inference. Correct refusal is a safety result, not implementation of the missing capability.
- No official labeled reference masks or answers were supplied. Official-sensor accuracy, IoU, F1 and end-to-end compliance cannot be reported.
- One crop per official product is limited coverage; no hidden ISRO evaluation performance is implied.

## Evidence and reproducibility

[Executable check results](../paired_lab/evidence/official-final-20260927/checks.json), [fresh model output](../paired_lab/evidence/official-final-20260927/cartosat-vqa.json), [source calibration report](../paired_lab/evidence/official-20260927/calibration.json), [verification script](../scripts/verify_official_samples.py), [calibration preparation](../scripts/prepare_eos04_sample.py).

Run the verification script with the directory containing the complete cartosat-mx.zip and eos04-frs2.zip archives (plus the previously preserved native EOS-04 crop) and an output directory. The script relies on the prepared artifacts linked above. Checkpoint-based verification requires the existing provisioned inference runtime; no clean-machine inference reproduction is claimed.

Presentation-safe statement: **Tested official NRSC Cartosat-2E optical ingestion and description execution, and independently verified EOS-04 FRS2 calibration with traceable source metadata. Paired official-sensor accuracy remains unvalidated.**
