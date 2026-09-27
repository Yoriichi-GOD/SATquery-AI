# Compliance progress — 26 September 2026

This records verified progress, not certification against the full problem statement.

## Implemented and checked in this pass

- Added a single-image Sentinel-1 VV/VH scene-description route using the existing SAR-only BIFOLD classifier. The upload UI selects optical or SAR; the controller checks compatibility before choosing the specialist.
- Required 120 x 120 pixels, ordered VV/VH, dB units, a north-up projected 10 m grid and finite values. EOS-04/RISAT is explicitly unsupported by this checkpoint. Metadata assertions do not independently prove radiometric calibration.
- Retained model identity/revision, class scores, threshold, SAR display image and original input in the evidence package. Scores are uncalibrated and do not mean accuracy. Scene classification is not unrestricted SAR VQA or grounding.
- Real HTTP upload -> routing -> CPU model execution -> evidence ZIP passed using an explicitly reprojected, finite crop of the existing external Bolivia Sentinel-1 example. ZIP integrity and original-input bytes were checked. This is functional regression evidence, not an unseen accuracy benchmark.
- Added a bounded preparation script for the exact official Cartosat sample archive. It verifies the archive hash and band grids, preserves native pixel values, and labels bands using NRSC's Cartosat-2E specifications (Table 4, PDF page 30). It makes no radiometric conversion. This is a manual CLI preparation step, not general ZIP ingestion in the UI.
- The prepared Cartosat GeoTIFF passed the actual optical ingestion path. NDVI correctly refused its uncalibrated DN values.
- A real optical VQA description run completed on that crop: 17.137 s total, 6.095 s checkpoint load, 5.580 s generation, 4.243 GiB peak allocated GPU memory. These are one-run measurements, not a latency distribution or total VRAM measurement.
- Raw answer: "Many buildings and green trees are in a dense residential area." Visual inspection supports buildings/trees; description completeness and accuracy were not independently scored. No sensor benchmark claim follows from this one run.
- Software regression: 76 tests passed in the isolated Python 3.11 test environment after the SAR changes. Browser interaction was not exercised in this pass; backend HTTP execution was exercised.

## Evidence

[Live SAR result](../paired_lab/evidence/compliance-20260926/sar-live.json), [SAR preparation](../paired_lab/evidence/compliance-20260926/sar-preparation.json), [SAR evidence package](../paired_lab/evidence/compliance-20260926/sar-live-evidence.zip).

[Cartosat preparation manifest](../paired_lab/evidence/compliance-20260926/cartosat-labelled.json), [ingestion and NDVI refusal](../paired_lab/evidence/compliance-20260926/cartosat-ingestion-check.json), [actual VQA result](../paired_lab/evidence/compliance-20260926/cartosat-vqa.json), [display preview](../paired_lab/evidence/compliance-20260926/cartosat-preview.png).

[Preparation tool](../scripts/prepare_cartosat_sample.py). Band reference: [NRSC report, Table 4](https://bhuvan-app3.nrsc.gov.in/nhai_gci/files/NRSC_NH-GCI_FinalReport_09Dec2025.pdf).

## Definition of Done and open gates

| Requirement/gate | Current boundary | Closure evidence required |
| --- | --- | --- |
| Single optical analysis | Existing bounded VQA; one official crop executed | Task-specific held-out quality evaluation; current sample is a smoke test |
| Single SAR | Bounded scene labels/description implemented | Appropriate SAR question-answering support and validation; this route does not satisfy unrestricted SAR VQA |
| Bi-temporal analysis | Bounded road/building MCI path; component acceptance recorded separately | Prescribed change-VQA evaluation and supported question coverage, not substitution with segmentation scores |
| Joint official optical/SAR | Sentinel pathways exist; official public samples inspected | Compatible co-registered official pair plus suitable validated inference path; public samples inspected are geographically unrelated |
| Prescribed benchmarks | Existing component evidence is heterogeneous | Required VRSBench/RSVQA/CDVQA coverage with explicit splits, assets, metrics and no evaluation leakage |
| Confidence | Raw model scores and limitations exposed | Calibrated confidence where required; no invented confidence percentages |
| Input formats | GeoTIFF support exists; generic image uploads also remain | Explicit prescribed-benchmark versus operational-input policy and verification |
| Final acceptance | Earlier bounded component acceptance retained | Freeze revised candidate and evaluate a genuinely unused end-to-end set; regression is not untouched acceptance |

Stop conditions: do not relabel Sentinel data as RISAT, invent coregistration, turn DN into surface reflectance by a metadata tag, or call a successful API response an accuracy result. Forecasting remains out of scope.
