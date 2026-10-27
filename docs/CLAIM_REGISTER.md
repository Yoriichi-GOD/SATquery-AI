# Claim register

Sources: [benchmark report](../BENCHMARK_REPORT.md), [metrics](../paired_lab/evidence/benchmark-20260921/metrics.csv), and [CDVQA report](CDVQA_FINAL_REPORT.md). Values are historical 21 September evidence except the explicitly dated CDVQA result; none is a fresh measurement of later changes.

| Permitted claim | Evidence scope | Must accompany it / forbidden extrapolation |
| --- | --- | --- |
| CDVQA Test-1 / Test-2 OA 69.90% / 65.05% | 28 September; 39,686 / 31,036 questions on the same 968 pairs | Experimental classifier; later interface integration does not change these benchmark scores. Overlapping splits must not be pooled. Question-only OA 68.06% / 63.24%; 12 previously inspected pairs and exclusion analysis disclosed in report |
| Road IoU 80.99%; building IoU 81.69% | 100 selected LEVIR-MCI pairs, 50 changed/50 unchanged | Inherited checkpoint; not full CDVQA or official-sensor validation |
| Water SAR 63.64%, optical 83.90%, joint 82.64% IoU | 90 Sen1Floods11 test chips replayed | Previously evaluated; no universal fusion advantage |
| Bolivia joint IoU 81.58% | 15 held-region chips replayed | Small region-specific result; not universal transfer |
| Joint land-cover micro-F1 75.0% | 12 narrow fixtures | Not pixel mapping or a broad benchmark; not comparable to competitor 3,000-case scores |
| 61/61 routing challenges passed after fixes | Development/regression; plus 12 paraphrases | Not untouched routing accuracy |
| 70 software tests passed in benchmark pass | Mocks, synthetic and deterministic checks | Not model accuracy; latest check recorded separately in closure table |
| Exported numerical evidence independently recomputed | NDVI, water and temporal bounded runs | Not proof of scientifically correct masks |
| Three water pathways remain inspectable | Implemented outputs | Their disagreement is evidence, not confidence calibration |

No supported claim of overall accuracy, competitor superiority, guaranteed savings, production readiness, flood forecasting or broad caption accuracy. Official sensor sample access alone is not validation. Model scores are not accuracy.
