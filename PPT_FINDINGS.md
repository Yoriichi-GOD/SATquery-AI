# PPT-ready findings — use with the scope footnotes

## Primary evidence slide

**Query-driven analysis with inspectable spatial evidence**

- Road change: **80.99% IoU**
- Building change: **81.69% IoU**
- Water mapping: **82.64% joint IoU**
- Exported NDVI, water and temporal measurements independently recomputed.

Footnote: Temporal: fixed 100-pair LEVIR-MCI subset, 50 changed/50 unchanged. Water: 90-chip Sen1Floods11 test replay. Inherited temporal checkpoint; locally trained water model. No ISRO/SAC sensor validation claim.

## Verification slide / backup

- 70 software regression tests passed.
- 61/61 valid routing development challenges passed after fixes; 12 additional paraphrases passed.
- 10 identical/brightness controls produced zero change pixels (five base scenes).
- Original inputs and downloadable evidence retained; known artifact URLs remained accessible after restart.

Footnote: Software tests include mocks; controls and routing challenges are bounded development evidence. Optical-only water IoU is 83.90% on the same test split, versus 82.64% joint; do not claim universal fusion superiority.

## Keep out of headline claims

No overall SatQuery accuracy, “beats competitors”, “ISRO-ready”, flood prediction, guaranteed cost/time savings, validated caption accuracy or general urban-expansion claim. Keep detailed failure analysis in the technical report/backup slides; retain material metric footnotes on the main slide.

Source tables: metrics.csv. Full methodology and unresolved gates: BENCHMARK_REPORT.md.
