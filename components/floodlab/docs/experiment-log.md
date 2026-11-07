# Experiment log - 2026-10-14 IST

1. Read user handoff and reconstructed brief. Confirmed actual source location; existing SatQuery working tree clean at 4045ce3.
2. Verified Devpost deadline 15 October 00:15 IST. Downloaded organizer PDF index, extracted Track B and submission links, then read both versions of the full Track B brief. Saved requirement corrections before implementation.
3. Inspected WaterUNet contract and MIT license read-only. No copied model or new model download.
4. Created separate Windows source and WSL Python 3.11 environment. System Python 3.14 venv creation failed due to missing ensurepip; used installed Python 3.11 to create an independent venv. No original environment modified. The failed /root/satquery-flood-lab/.venv is unused; active path is /root/satquery-flood-lab/venv.
5. Queried CDSE, PC RTC and ohsome metadata. Saved responses. Actual access failures and next actions are in data-access.md. No raw imagery, historical infrastructure or EMS reference acquired.
6. Implemented contracts/SAR change; 14 tests passed. Added exposure/graph; 24 passed. Connected synthetic exports/reports; 29 passed. Separate frozen-artifact evaluator; 34 passed. Repeatability/service guards; 39 passed. Added explicit all-invalid failure during final review.
7. Generated artifacts/runs/synthetic-bridge-001. Expected 32 new-water candidate pixels, 3200 m2, 200 m2 intersected building footprint, 40 m bridge intersection, 1 synthetic settlement losing access; confirmed by independent fixture expectations. These are NOT real-event measurements.
8. Browser on localhost:8770 verified correct title and synthetic warning, saved statistics, links and layer toggle (4 paths enabled, 3 with candidate layer hidden). Restored layer enabled. No console error observed in ordinary interaction.
9. HTTP verification: both 8767 and 8770 return 200. All 10 frozen downloadable files match their saved SHA-256 hashes. See http-verification.json.
10. Final test count and result: see test-results.xml. Dependencies emit Shapely/Affine deprecation warnings; they do not fail checks. No real flood metrics exist.

## Stop point
Do not expand the dashboard or train models before solving permitted real-data acquisition/preprocessing. The app is a tested calculation prototype. Real-event Definition of Done and submission readiness are unmet.

## Next bounded milestone
Authenticate permitted imagery access, retrieve one verified same-orbit pair and pre-event road topology, implement/verify preparation into the strict manifest contract, then execute a real run before choosing AI integration. User was asked to configure access; no credentials were requested in chat.

11. Final regression: 40 passed. Restarted only flood-lab as a hidden persistent process; browser reload and all 10 download hashes passed after restart. Original SatQuery on 8767 returned HTTP 200 and its Git tree remained clean.
12. User explicitly chose: Continue with tests and document the data blocker. No further account setup or acquisition was attempted.
