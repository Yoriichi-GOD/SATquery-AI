# November 7 publication verification

This publication carries the previously committed research branch and current cosmic application shell, a pinned SIH repository comparison, and a new README terrain screenshot. Product source baseline before the documentation/test-fixture changes: `727793592d083c1fb4b8b22a0ff0844db47fbf64`.

## Checks executed for this publication

| Check | Actual result | Scope |
|---|---|---|
| Application Python regression | 312 tests passed | Provisioned Python 3.11 environment; includes mocks/synthetic fixtures, not 312 accuracy trials |
| Flood Lab regression | 86 tests passed | Existing separate Flood Lab environment; dependency deprecation warnings retained |
| Legacy workspace DOM wiring | Passed | Corrected stale fake-DOM event/URL/navigation support; click opens the image and dragging does not |
| Nepal UI display contracts | 5 checks passed | Separate debris/water denominators, missing values, provenance and display contracts |
| Fixed-header workspace shell | 9 tests passed | Header/footer offsets, input modality and reduced-motion behavior using explicit doubles |
| Terrain JavaScript syntax | Passed | `node --check jai_extension/web/earth.js` |
| Live terrain/RGB rendering | Verified at 1280 × 720 | Actual browser, saved Nepal run, real terrain canvas and decoded optical RGB; focused view only |
| Documentation and asset integrity | Passed | 90 local documentation targets resolved; screenshot and six UI source hashes match; all four historical screenshot hashes preserved |
| Credential marker scan | No matches | Scanned new publication text for selected token/private-key patterns; limited pattern check, not a security certification |

The legacy UI fixture initially failed because it lacked browser-standard event and navigation APIs used by the existing source. The fixture now uses `EventTarget`, a default URL hash and HTML-derived navigation lookup, with click-versus-drag assertions. No application behavior was changed to accommodate that test.

The browser check confirmed the header is fixed at y=0 with `backdrop-filter: none`. The unedited [README screenshot](images/terrain-workspace-20261107.jpg), [capture manifest](images/terrain-capture-20261107.json) and [provenance](images/README.md) preserve the exact state. The screenshot uses the 90 m demonstration DSM, not the separate 2 m research audit.

Existing environments and assets were reused. The two retained optical crops were restored locally only after matching the saved run's frozen source hashes. Raw optical crops, runtime profiles, model weights and credentials are not part of the documentation change. This is not a fresh-machine restoration or every-route browser verification claim.

The [four-case measurements](../research/results/case-campaign-20261107/REPORT.md), [validation closure](../research/results/validation-closure-20261107/REPORT.md), and [SIH source comparison](../research/results/sih-public-comparison-20261107/REPORT.md) retain their separate scopes and limitations. Publication does not turn candidate areas into confirmed damage or establish exposure accuracy, transfer, registration or novelty.

## Preserved checkpoint

`day1-final` tag object: `a08d2706397d359edb060993ee3a14374b3d136f`.

Peeled Day 1 commit: `f3945347cf0f0a4581aa1480c8fa1501a25da4b4`.

No history rewriting, tag movement, backdating or overwrite of frozen research packs is used.
