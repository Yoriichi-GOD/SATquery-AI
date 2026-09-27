# CDVQA acquisition, testing and EOS-04 methodology follow-through

27 September 2026. Status: data acquisition completed for a selected public subset; bounded tests completed; full CDVQA and official-sensor semantic compliance remain open.

## What was acquired

The [SECOND author's dataset link](https://captain-whu.github.io/SCD/) resolves to a 3,785,055,247-byte ZIP. Its imagery is nested in archives, so selective PNG retrieval directly from the outer ZIP was not possible. Downloaded only its `SECOND_train_set.rar` member: 2,406,111,691 bytes, outer ZIP member CRC verified, SHA-256 `5ee2a82b5824b3f5e3c5bfaf018835862e7623993ff9ac5ce57fd11fcfad2b4e`. The whole outer ZIP was not downloaded or hashed.

Extracted 12 distinct selected pairs, 24 RGB images and 24 semantic-change label images, matched by original filenames. Selection used seed 20260927 before inference and without consulting answers. All selected file hashes are saved. “SECOND training set” is the source archive name; CDVQA makes its own split from those publicly available images. These are from the CDVQA `Test` annotation files, not a claim of unseen imagery for every upstream checkpoint.

[CDVQA annotations](https://github.com/YZHJessica/CDVQA) are pinned at commit `cc5893123dd32326de38745b65d2ffe45055937b`. Downloaded and hashed Test questions, answers and image mappings, plus repository README and license. The annotation license is not assumed to settle underlying imagery commercial rights.

Large source archive and selected original images are outside the Git repository in the task's `cdvqa-data` artifact folder. No paid products, API judge or email was used.

## What was actually tested

| Layer | Result | Meaning |
|---|---|---|
| Native image input, live API | 12/12 selected PNG uploads refused | Current paired workflow requires TIFF. |
| Lossless TIFF container conversion, live API | 12/12 analyses refused | No CRS or dates were invented. API correctly refused missing geographic grid metadata. Native images are also 512×512 rather than MCI's required 256×256. |
| Existing MCI component transfer | 12/12 inference calls completed | Full images explicitly resized bilinearly to 256×256 outside the served workflow. Existing model unchanged, CPU, four Torch threads. |
| Narrow building-change probe | 6/9 eligible answers matched | A yes/no diagnostic used `building mask pixels > 0`, fixed before inference. All nine reference answers are **yes**, so an always-yes baseline is 9/9. Three pairs lacked an eligible unqualified building question and were not scored. This is weak transfer evidence, not CDVQA accuracy. |
| Intent routing audit | All 39,686 Test questions replayed | No model inference per question. This measures dispatch/refusal behavior only. |
| Software regression after fixes | **85 tests passed**, 2.098 s | Full software suite; detailed log retained. Does not validate all model outputs. |

The 24 downloaded semantic masks were preserved, but no semantic segmentation IoU was computed from them in this pass. A caption is not an answer to every CDVQA question, and this test does not turn the existing MCI caption model into a CDVQA model.

## Routing defect and repair

Before repair, 23,749 question intents selected the temporal specialist, including 10,586 questions mentioning non-vegetated ground or playgrounds. That specialist has no corresponding change classes. Generic ratios, land-cover conversions and class rankings also reached it.

Added regression cases first: ten subcases failed as expected. Updated `paired_lab/controller.py` to `unified-rules-v8` to reject the exposed unsupported classes, semantic conversions, rankings and change ratios. Follow-up replay caught the additional wording “change proportion”; this was added to the tests and fixed. The final full suite passes.

Final intent replay:

| CDVQA question type | Temporal dispatch | Refused |
|---|---:|---:|
| Change or not | 2,325 | 11,557 |
| Change ratio | 0 | 1,936 |
| Change ratio by class | 0 | 5,811 |
| Change to what | 0 | 2,991 |
| Decrease or not | 803 | 3,855 |
| Increase or not | 770 | 3,830 |
| Largest change | 0 | 2,904 |
| Smallest change | 0 | 2,904 |
| **Total** | **3,898** | **35,788** |

These are not routing-accuracy scores: no independently labelled eligibility oracle was supplied. Accepted intents still need input validation, and the model does not provide verified before/after semantic class areas or reliable directional answers merely because a question dispatches. Directional captions remain interpretations. Conservative keyword rules can also produce false refusals; full natural-language coverage is not established.

The older VRSBench “what kind of area” false refusal and textual-location/grounding mismatch were not repaired by this temporal-only change. They remain in the earlier report.

## EOS-04 methodology: stronger source, same deployment boundary

Retrieved the freely linked [22-page SegFormer ATBD](https://bharathk113.github.io/sar-segformer-portfolio/assets/ATBD.pdf), rather than stopping at the portfolio abstract. It identifies itself as NRSC document `NRSC-RSA-WATER RE-WRD-OCT 2025-TD-0002915-V1.0`, revision 10 October 2025, unrestricted classification. It is hosted on the author's public portfolio.

Pages 7–9 describe two SAR channels plus co-registered elevation and slope, scene-wise min/max normalization, 1024×1024 patches and explicit invalid-pixel handling. The EOS-04 training discussion uses MRS at 18 m. Pages 13–15 discuss a noise-corrected Beta-nought dB experiment. This is not the same input/model contract as our existing Sentinel-trained WaterUNet or the FRS2 calibration sample.

The author site still says model weights and inference scripts are coming later. The document describes training a modified SegFormer; generic ImageNet/ADE20K weights would not reproduce its water model. Its invalid-data handling and normalization must not be copied into our current specialist without validating that specialist's training contract.

No EOS-04 semantic model was integrated. No IoU/accuracy from this document is a SatQuery result. Existing official FRS2 calibration checks remain separate from semantic validation. Official Cartosat–EOS-04 fusion still requires a genuinely overlapping, appropriately prepared pair.

## Evidence and rerun paths

All repository-relative paths below refer to the current SatQuery source checkout.

- `paired_lab/evidence/cdvqa-20260927/`: source/hash manifests, original annotation files, frozen selection, native input checks, component outputs, before/after routing rows and summaries, final software test log, and methodology PDF.
- `scripts/acquire_cdvqa.py`: pinned-label download and bounded archive inventory inspection.
- `scripts/test_cdvqa.py`: immutable component/input/routing test harness. Preserves existing outputs instead of overwriting them.
- `tests/test_cdvqa_boundaries.py`: five regression methods covering unsupported requests and preservation of supported temporal routes.
- `paired_lab/controller.py`: scoped routing repair. Final SHA-256 `0601a778bef6b2edfb873e67420eaa8a7c39428a501cd9d426783231b5289a56`.

Full CDVQA support remains unfinished. Acquisition is no longer the immediate blocker for this subset; input integration, multi-class semantic capability, answer generation and protocol-aligned evaluation are the remaining work. Reusing these observed cases for fixes makes them development/regression evidence, not untouched final acceptance data.
