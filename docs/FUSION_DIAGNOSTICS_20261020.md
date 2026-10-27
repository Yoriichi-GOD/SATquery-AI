# Fusion diagnostics - 2026-10-20

Retrospective analysis of the existing float32 CPU water evaluation. No model training, inference rerun, threshold tuning, label editing or serving change. Results are recomputed from saved TP/FP/FN/TN and match every original aggregate exactly. This is diagnostic evidence on exposed examples, not fresh acceptance.

## What the data says

| Split | Chips | SAR IoU | Optical IoU | Joint IoU | Joint minus optical (pp) | 95% paired scene bootstrap interval (pp) |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| Validation | 89 | 59.4547% | 83.2289% | 83.1284% | -0.1004 | [-0.8728, +0.7207] |
| Existing test | 90 | 63.6437% | 83.8969% | 82.6440% | -1.2529 | [-3.2545, +0.3664] |
| Bolivia replay | 15 | 64.0479% | 81.4442% | 81.5773% | +0.1331 | [-2.3914, +2.6249] |

Intervals use 1,000 paired scene resamples with seed 20261020, pooling confusion counts within each sample. Event resampling on the existing test gives [-3.9556, +0.7851] pp. These intervals include zero: do not claim general statistical superiority for optical or joint fusion from these results. Bolivia is one event and cannot estimate cross-event uncertainty. Event labels are taken from sample-name prefixes, not independently verified geographic boundaries.

On the existing test, joint beat optical on 25 chips, lost on 55, tied on 3; 7 comparisons have undefined IoU for at least one modality. Do not count undefined comparisons as wins. Pooled pixel IoU and equal-weight scene win counts answer different questions.

## Where fusion hurts

| Recorded test event | Joint minus optical IoU | Change in false positives | Change in false negatives | Observed error pattern |
| --- | ---: | ---: | ---: | --- |
| Pakistan | -12.4389 pp | -2,984 | +30,208 | Much more missed water despite fewer false positives |
| USA | -5.9486 pp | +12,589 | -1,769 | More false water detections despite recovering some water |
| Ghana | +5.8548 pp | +661 | -11,287 | Recovered water outweighs added false positives |
| Sri-Lanka | +0.9390 pp | -1,587 | -2,345 | Both error types improve |

Pakistan improves by +1.3462 pp on validation but drops on the existing test. Event-name-based modality selection would therefore be a poor justified shortcut, apart from its inability to establish generalization. No gate is trained from these exposed test outcomes.

## Denominators and input diagnostics

Three validation chips (Ghana_5079, Ghana_234935, Ghana_277) and test chip Ghana_83483 have all labels equal to -1, despite mostly/fully finite image inputs. They contribute no scored pixels. Test chip Paraguay_34417 has no shared finite inputs; both sensor arrays are entirely masked/non-finite. Its label file contains water pixels but there is no input-valid evaluation support. None of these chips is a successful prediction. Other undefined IoUs can arise from zero positive union; their identities remain in the machine-readable report.

The existing evaluator compares modalities on the common finite-input and valid-label footprint. Thus its optical/SAR scores do not measure each sensor's independent usable coverage. Preserve this denominator for historical comparison; a future modality-specific coverage experiment needs a separate protocol.

Inspected 15 selected cases: zero-scored chips, three worst cases per split, and one Ghana comparator. Metadata corner differences are at most approximately 2.33e-10 pixels, so strict floating-point transform inequality is not meaningful misregistration. This does not establish physical co-registration. Optical values did not exceed the model's clipping limits in these selected cases; SAR clipping fractions were small. These checks do not explain the errors and cannot substitute for cloud labels, temporal-gap metadata, or measured registration residuals.

## Decision

Do not advertise a universal fusion gain or immediately add a complex fusion network. The next justified investigation is validation-only measurement of sensor-quality/disagreement features and a simple quality-based baseline, compared with fixed optical/SAR/joint operation at matched coverage. Collect physical quality evidence before attributing failures to clouds or alignment. Keep the current model unchanged in this step.

## Reproduction and evidence

Source: paired_lab/evidence/resumed/water-evaluation.json. Its byte hash, per-event confusion counts, all scene rows and bootstrap results are retained in .runtime/step2-20261020/fusion-complete/audit.json; scenes.csv is the flat table; input-diagnostics.json records inspected raster hashes and measurements. These ignored local artifacts are not distributed by a public clone.

Run scripts/audit_fusion_counts.py SOURCE_JSON NEW_OUTPUT_DIRECTORY --data /root/satquery/paired-lab/sen1floods11. It refuses to overwrite an output directory. Earlier exploratory aggregation folders under .runtime/step2-20261020 are retained; fusion-complete is the final audit.