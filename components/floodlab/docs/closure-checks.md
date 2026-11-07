# Flood workspace closure verification · 15 October 2026

## Verified

- Fresh regression run: 70 passed, 0 failed, 0 errors, 0 skipped; 31 warnings in 2.40 seconds. Warnings are Rasterio/Shapely deprecations and synthetic-test georeferencing warnings.
- Local browser inspection confirms Workspace at port 8770, selectable saved runs, optical/SAR view choices, always-visible question controls, saved result metrics, processing record, and collapsible access/evidence/limitations sections.
- Label-blind Timure area/date job event-02163045d752 completed in 47.1 seconds. Five recorded successful area/date requests average 51.6 seconds (range 35.5–81.8 seconds): four Syapru rectangle runs and one Timure request.
- The Syapru rectangle run event-fe47db331390 has 15 frozen downloadable artifacts; hashes were checked before reference scoring.
- Post-freeze UNOSAT comparison over two disjoint AOIs: 57,446 valid pixels; TP 318, FP 531, FN 22,906, TN 33,691; IoU 0.01339, F1 0.02642, precision 0.37456, recall 0.01369. This is poor external map agreement, not accuracy against field truth: Product 4259 is preliminary, not field-validated, and not water-only.
- EMSR927 landslide-proxy comparison over 47,127 valid pixels: TP 4,425, FP 64, FN 10,740, TN 31,898; IoU 0.29056, F1 0.45029, precision 0.98574, recall 0.29179. Class mismatch; not debris validation.
- Eleven synthetic graph tests cover bridge cuts, alternate routes, overpasses, one-way edges, boundary and missing-hub uncertainty. These do not prove real settlement isolation.

## Still open

- Field-validated water labels and independent event-level accuracy validation.
- Direct debris reference labels and expert review.
- Real settlement-access conclusions where required graph hubs or coverage are missing.
- Native Nepali review; development question routing scored 9/12.
- Demo recording remains outstanding; a timed 90-second narration and click guide is prepared in docs/demo-script.md and Appendix A of the final PDF.
- Line-by-line confirmation of the official IIT Mandi Track B PDF constraints, organizer reuse clearance, and submission authorization.

## Interpretation

Stop model tuning against the inspected references. The external comparison is poor and the sources are not ground truth. Fixing thresholds on these same references would leak evaluation labels into development. The local workspace can be demonstrated as an experimental engineering baseline with its limits visible; it is not a validated operational product or a submission-ready result.

