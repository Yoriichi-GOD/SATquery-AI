# Local flood workspace

Open http://localhost:8770/ and select event-fe47db331390 for the verified Syapru area/date run. event-02163045d752 is the second official AOI sample at Timure.

Run locally in PowerShell:
Set-Location -LiteralPath 'C:\Users\nrgen\.codex\scratch\satquery-flood-lab'
.\start-demo.ps1

The original SatQuery on port 8767 remains separate. The report and test results are in output/pdf/flood-impact-final-report.pdf and docs/test-results.xml.

## Evidence status

- Predictions were frozen before UNOSAT and EMSR reference inspection.
- UNOSAT Product 4259 comparison across two AOIs is poor map agreement, not validated accuracy: IoU 0.0134, F1 0.0264, recall 1.37%. The source is preliminary and not field-validated.
- EMSR927 labels inspected here are mass movement / landslide classes. Their comparison with the debris proxy is a class-mismatched diagnostic, not debris validation.
- Synthetic road-graph tests pass. Actual settlement isolation remains unknown where hubs, coverage or AOI boundary are unresolved.
- Native Nepali review and demo recording remain pending. Official Track B PDF requirements and organizer reuse clearance still need confirmation.

Do not claim validated flood or debris accuracy, actual road closure, real settlement isolation, response outcomes, or general runtime based on this prototype.