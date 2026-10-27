# Pilot alignment and preprocessing review - 2026-10-20

## Decision

Preprocessing checks pass for the acquired pilot. Physical alignment is **NOT ESTABLISHED**. Six distributed regions were visually reviewed; zero stable control-point pairs were accepted. Median, p95 and RMSE remain null. This is insufficient evidence, not proof that the pair is misregistered.

The conditional next step (freeze an acceptance sample and run three modality comparisons) was not triggered. No model inference, scoring, training, thresholds or serving changes.

## Direct checks

- Native 10-metre B02, B03, B04 and B08 crops exactly equal the prepared optical bands; this independently checks coordinate/window and band placement.
- Prepared SAR exactly equals stored source values divided by 100.
- Both validity masks exactly equal the original source crops, preserving binary encoding.
- Original input hashes and all 22 frozen reference files remain unchanged.
- SAR clipping fractions under the current preprocessing limits: [{'band': 'VV', 'min_db': -31.639999389648438, 'max_db': 9.720000267028809, 'clip_fraction': 0.0}, {'band': 'VH', 'min_db': -48.65999984741211, 'max_db': -0.9900000095367432, 'clip_fraction': 0.0}].
- Optical fraction above the current upper clipping limit: 0.0.
- Lower-resolution optical bands were bilinearly resampled. This preserves the declared workflow but is not evidence that all source-dataset preprocessing matches the training distribution.

## Visual review

Regions 1, 2, 4 and 6 contain optically visible field geometry but insufficiently unique SAR ground-point correspondences. Regions 3 and 5 contain distinctive dark features plausibly associated with water; these were excluded under the static-ground control rule. Bright SAR returns were not assumed to be building centres.

The six regions cover top and bottom rows at left, middle and right positions. Panels include original RGB, raw VV and a display-only median-filtered view; the extra display filter never changes inference inputs. Review is by the assistant, not independent human adjudication. No points or warp were fitted.

## Source preprocessing

The [authors' SNAP recipe](https://github.com/MWieland/s1s2_water/blob/main/prepare/preproc_s1_snap.xml) specifies orbit correction, thermal-noise removal, sigma-band calibration, 3x3 median filtering, external-DEM terrain correction at 10 m with bilinear interpolation, dB conversion and reprojection. A hash-pinned copy is saved with this review. The image is already preprocessed: applying another filter to inference data would be an unregistered change.

Band/unit compatibility is verified; full equivalence to Sen1Floods11 processing has not been established. Provider cloud QA is automated; dataset validity masks combine invalid causes and are not independent cloud-only truth.

## Required evidence to advance

Obtain at least six spatially distributed, uniquely corresponding static ground landmarks, with source hashes, pixel coordinates, projected metre coordinates, uncertainty and reviewer identity. Keep them independent of any warp fitting. If this scene cannot supply those controls, mark it unsuitable for this alignment check and select another development pilot using an explicit metadata/feature criterion. Do not change acceptance selection based on accuracy.

There is no justified residual cutoff in the current protocol. Before accepting landmark measurements, record a task-resolution-based tolerance and localization uncertainty rather than choosing a cutoff after seeing residuals.

## Artifacts and verification

`.runtime/alignment-20261020/manifest.json`, `landmark-review.json`, `preprocessing.json`, `checks.json`, `regions-1.png`, `regions-2.png`.

The panel script initially encountered a missing optional SciPy dependency before writing outputs; its display filter was implemented with existing NumPy instead. No packages were installed. Real-pixel equality and source-preservation assertions passed. These checks establish only the properties listed above.
