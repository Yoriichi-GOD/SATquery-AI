# Day 1 implementation and verification — 20 September 2026

## Delivered scope
One workspace at http://localhost:8767/ routes VQA, NDVI, temporal road/building change, optical–SAR water, optical–SAR land cover and experimental grounding. The main and grounding landing pages redirect here; preserved classic pages remain accessible. Existing scientific input contracts and model computations are retained. Uploaded compatible files are accepted; this does not mean arbitrary satellite imagery is scientifically supported.

The selected specialist, device, routing reason and real processing stages are visible during execution. Final answers precede processing history. The final output is the default large image, with selectable horizontal thumbnails and a full-size viewer. Numerical results use highlighted cards. Original sepia colors, evaluation illustration and floating Earth/satellite processing artwork are restored. Input selectors use custom black/white menus with keyboard navigation.

Evidence has a concise overview and detailed evaluations. VQA development comparisons, NDVI numerical checks, archived routing/ChangeFormer trials, land-cover trials and the existing 100-pair temporal / 90-pair water / 15-pair Bolivia evaluations remain distinct. No new large-dataset benchmark was performed by this integration work.

## Definition of Done and evidence
- Six workflow types connected through the common controller: verified by live executions.
- Invalid requests fail without inappropriate fallback: 6 live refusals plus unit coverage.
- Existing functionality retained: corrected baseline 39 tests passed; final suite 50 tests passed.
- Evidence packages retain original inputs, execution selection, intermediate artifacts and result: ZIP integrity and numerical recomputation checked by live verifier.
- UI checked in browser: custom selector, NDVI result-first layout and metric cards, horizontal thumbnail selection, full-size dialog, sepia evidence overview, detailed VQA/NDVI/paired evaluation content, real VQA processing animation and completion.
- JavaScript syntax check passed after final edits.

Live records: paired_lab/evidence/day1-20260920/live-verification.json and individual run/refusal JSON files. The eight runs cover VQA, temporal, uploaded water pair, land cover, calibrated NDVI, synthetic external NDVI, grounding and VQA after grounding. Final progress/evidence-page adjustments were followed by the 50-test suite and another browser VQA run (69d2c4d647de4cf38ac5c36af465c973). These are integration checks, not scientific accuracy benchmarks.

## Boundaries and unresolved work
- Grounding remains experimental; it operates on the normalized RGB preview.
- Inputs require the existing sensor, bands, units, dimensions and metadata contracts; calibration/physical co-registration are not newly automated.
- Cartosat/RISAT transfer remains unverified.
- Current deployment remains local, two services, with a one-run controller guard. This is not enterprise multi-user SaaS certification.
- Upload/job indexes are in memory; restarting services loses those indexes. Persisted artifact files alone do not implement historical run browsing.
- Existing larger evaluation records are presented, not rerun or expanded today. No claims of labor savings, infrastructure cost savings or competitor superiority follow from these tests.

Original edited files are backed up under backups/day1-20260920. Launch with start.ps1 or paired_lab/start.ps1.
