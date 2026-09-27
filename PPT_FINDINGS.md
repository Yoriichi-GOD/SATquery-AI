# PPT-ready findings — use with the scope footnotes

## New CDVQA specialist — measured 28 September 2026

**69.90% overall accuracy — CDVQA Test-1, all 39,686 questions / 968 image pairs.**

Test-2: **65.05%**, all 31,036 questions on the same 968 pairs. Macro accuracy: 61.13% / 61.19%. Question-only controls: 68.06% / 63.24%; paired inputs improve OA by 1.84 / 1.81 percentage points.

Footnote: Experimental 19-answer specialist trained on official Train and selected on Val; separate CLI evaluation, not the served UI/router. Test sets share imagery/questions. Excluding 12 previously inspected pairs: 69.89% / 65.03%. No combined product-accuracy or official-sensor claim. [Full report and evidence](docs/CDVQA_FINAL_REPORT.md).


## Primary evidence slide

**Query-driven analysis with inspectable spatial evidence**

- Road change: **80.99% IoU**
- Building change: **81.69% IoU**
- Water mapping: **SAR 63.64% | Optical 83.90% | Joint 82.64% IoU**
- Exported NDVI, water and temporal measurements independently recomputed.

Footnote: Temporal: fixed 100-pair LEVIR-MCI subset, 50 changed/50 unchanged. Water: 90-chip Sen1Floods11 test replay. Inherited temporal checkpoint; locally trained water model. No ISRO/SAC sensor validation claim.

## Verification slide / backup

- 85 software regression tests passed (28 September 2026).
- 61/61 valid routing development challenges passed after fixes; 12 additional paraphrases passed.
- 10 identical/brightness controls produced zero change pixels (five base scenes).
- Original inputs and downloadable evidence retained; known artifact URLs remained accessible after restart.

Footnote: Software tests include mocks; controls and routing challenges are bounded development evidence. Optical-only water IoU is 83.90% on the same test split, versus 82.64% joint; do not claim universal fusion superiority.

## Keep out of headline claims

No overall SatQuery accuracy, “beats competitors”, “ISRO-ready”, flood prediction, guaranteed cost/time savings, validated caption accuracy or general urban-expansion claim. Keep detailed failure analysis in the technical report/backup slides; retain material metric footnotes on the main slide.

Source tables: [metrics.csv](paired_lab/evidence/benchmark-20260921/metrics.csv). Full methodology and unresolved gates: [BENCHMARK_REPORT.md](BENCHMARK_REPORT.md). Caption evidence: [DESCRIPTION_REVIEW.md](paired_lab/evidence/benchmark-20260921/DESCRIPTION_REVIEW.md).
