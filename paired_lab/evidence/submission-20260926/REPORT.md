# Official-product checks and bounded submission acceptance

## Decision

Official product inspection is complete. **Official-sensor inference compatibility and accuracy have NOT passed.** The downloaded products are not an overlapping optical/SAR pair, and the current paired models enforce Sentinel training contracts. The bounded temporal component passed the predeclared internal floor; the original routing acceptance failed one case, subsequently fixed and regression-tested. This is not full-system untouched acceptance.

## Official products

Both downloaded ZIPs passed CRC checks for every archive member; SHA256, original metadata and raster inventories are preserved in this evidence directory.

| Product | Actual metadata | Findings |
| --- | --- | --- |
| Bhoonidhi Cartosat-2S MX listing, product 205132611 | SatID CARTOSAT-2E; 16 May 2020; four separate uint16 bands; 7687 × 7640; EPSG:32645; 1.6 m | Listing and product identity differ. No RGB band descriptions or confirmed surface-reflectance tags in the TIFFs. Native crop rejected by single-image ingestion and NDVI; metadata inspection succeeds. |
| EOS-04 FRS2, product 237516861 | 13 September 2023; HH/HV/VH/VV imagery; uint16; 6001 × 5601; EPSG:32643; 4.5 m | Calibration information is in sidecars; TIFF scale/offset alone does not establish Sentinel-compatible dB. Native HH crop rejected by optical ingestion and NDVI; metadata inspection succeeds. |

The products' geographic bounding boxes do not overlap and acquisition dates are 1,215 days apart. Actual paired validators refuse the native crops for mismatched geographic grids. A land-cover plan may be selected before validation, but that does not mean execution is eligible. No model inference was forced on these products. No labels, sensor names, calibration or grid alignment were fabricated. Full raw scenes also exceed current upload pixel limits.

Scope: one native central crop from a vendor optical band and one radar HH band, plus inventories of all raster members. This is an input compatibility/refusal audit, not a complete multispectral importer, co-registration certification or Cartosat/RISAT benchmark. No labelled official-sensor accuracy is available. These samples do not close that requirement.

## Frozen temporal acceptance

Candidate f24e970; seed 20260926. Forty LEVIR-MCI test pairs, 20 changed and 20 unchanged, excluding 200 previously referenced local test IDs and checking no byte-identical A/B image file against those exclusions. Model hash, input hashes, source hashes and thresholds were recorded before inference in acceptance-20260926/freeze.json.

Internal engineering criteria: road and building IoU each at least 70%; unchanged false-positive pixel fraction at most 1%; zero execution failures. These are predeclared internal floors, not ISRO acceptance requirements.

| Metric | Result |
| --- | --- |
| Road IoU | 72.00% |
| Building IoU | 71.60% |
| Road F1 | 83.72% |
| Building F1 | 83.45% |
| Unchanged-pair predicted change pixels | 0 across 20 pairs |
| Execution failures | 0/40 |

The temporal component passes that internal floor. Scores are lower than the earlier selected 100-pair results (80.99% / 81.69% IoU); retain both scopes rather than replacing the lower numbers. Raw captions are saved but not assigned a factuality score. Geographic independence and upstream checkpoint test exposure remain unknown. This is locally unused component evaluation, not full CDVQA or full-system untouched acceptance.

## Numerical, routing and regression checks

- 100 seeded NDVI calculations agreed with independent rational arithmetic (maximum absolute error 0).
- Original synthetic routing acceptance: **19/20**. A calibrated request, “Compute NDVI for this raster,” was falsely refused.
- Narrow fix: allow an image/raster/crop context in the existing complete NDVI grammar. Calibration, compound-request and threshold guards remain tested. Single-image router version rules-v7.
- Post-fix replay: **20/20**, explicitly regression evidence. The original failed result remains intact.
- Software regression: **72/72** passed in the isolated model-free Python 3.11 environment. This is not model-quality validation.

## Remaining submission boundaries

Water's 105 existing cases, land-cover fixtures, VQA and grounding evidence remain the earlier benchmark record; they were not relabelled as new acceptance data. A full-system untouched set, valid official paired inference, expert caption adjudication and clean-machine model restoration remain open. No demo or PPT work was performed in this pass.

## Evidence

See [official pair checks](pair-results.json), [native crop checks](contract-results.json), [temporal freeze](acceptance-20260926/freeze.json), [temporal results](acceptance-20260926/summary.json), [original routing acceptance](acceptance-20260926/contract-results.json), [post-fix regression](acceptance-20260926/contract-regression.json), [source changes](postfix-source.json), and [download provenance](sources.json). Prediction/reference NPZ files permit independent metric recomputation.
