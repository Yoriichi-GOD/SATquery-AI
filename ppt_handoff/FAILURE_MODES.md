# Failure-mode audit: tests versus code inspection
| Case | Observed/current behavior | Desired/assessment |
|---|---|---|
| Malformed PNG | Tested400, raw decoder message | Graceful status; message needs polish |
| Malformed TIFF | Tested400, GDAL error text | Graceful status; technical message |
| Unlabelled TIFF | Tested400 | Explicit band identification needed |
| Missing NIR | Upload200; NDVI422 | Correct: RGB preview valid, spectral analysis unavailable |
| >20MB | Tested413 | Correct refusal |
| Nodata-heavy4x4 | Job completes with1/16 valid | Correct coverage denominator; low coverage warning could improve |
| Zero denominator | Job state error, no valid pixels | Handled, no division-generated number |
| Missing CRS | NDVI completes; area unavailable | Correct: no invented ground area |
| Invalid/unparseable CRS | Not independently injected; raster library likely rejects/ignores malformed metadata | Unverified, do not claim tested |
| Near-zero positive denominator | geo.calculate excludes sum<=1e-8 (code inspected); exact zero tested | Boundary test breadth remains limited |
| Old invalid sample | Tested400 in calibration audit | Explicit correction instruction |
| Empty/>500char question | Tested400 | Handled |
| Explicit SAR request | Tested422 | Handled only known patterns |
| Coordinate request | Tested422 | Helper is not a UI feature |
| “Compare this to last year” | Tested200: incorrectly accepted into VQA | OPEN ROUTING DEFECT; must refuse without paired workflow |
| “Count buildings” | No specific guard (code inspected) | VQA may estimate; not certified count/grounding |
| Model wrong format |20 original dev failures,0adapter | Real measured weakness |
| Model wrong answer | Two real regressions in EXAMPLES.md | No reliable per-answer correctness detection |
| Timeout | No server job timeout or cancel; browser polls indefinitely | OPEN robustness limitation; not induced |
| Corrupt checkpoint | Broad exception handler exists; did not corrupt model | Destructive experiment intentionally not performed |
| Restart | Image/job indexes process-local; upload again | No durable recovery |
Raw requests/results: metrics/failure_checks.json. Failure-test output truncates long response strings; retain originating run IDs for full local records. No user files or weights were corrupted.
