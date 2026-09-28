# Prompt and input-preview verification — 28 September 2026

## Delivered

- Whole-question descriptive location/context routes now accept the three previously refused VRSBench questions about surrounding area, bridge position and roundabout position. Explicit grounding and physical-measurement restrictions remain.
- Ambiguous RGB pair requests such as "Analyze these images" ask what to compare. Suggested questions are filtered through the existing input checks; selecting one fills the prompt and requires an explicit Analyze action.
- "Analyze this image" / "Analyse the scene" use the existing detailed whole-scene description policy. Specific questions retain their own prompts.
- Original PNG/JPEG/WebP previews appear on selection. TIFF previews use a bounded CPU read, clearly labeled display stretch, and original files remain unchanged. Paired uploads appear side by side, with modality, filename and declared date. No acquisition date is invented.
- Previewing does not establish sensor compatibility, physical co-registration or scientific validity. Analysis still performs its original checks. Preview file limit: 20 MB; longest raster preview edge: 900 pixels.

## Verification

- 94 software regression tests passed locally, including 9 new focused tests.
- Both JavaScript files passed Node syntax checks.
- Live TIFF endpoint returned a PNG with its display-transform description.
- Browser verification: immediate single PNG preview; both uploaded TIFFs visible side by side before Analyze; ambiguous prepared-pair request showed a compatible question button; clicking it populated the prompt without starting analysis. Browser console had no errors at the paired-preview check.
- Three previously refused descriptive questions completed through the actual model, saved in [live-rows.json](live-rows.json). This establishes repaired dispatch and completion, not three correct answers. The bridge location disagrees with its reference.

## Rejected answer-quality experiment

A narrowly scoped extra instruction requested one sentence without inferred purpose/ownership/activities. It was compared on the same three reused development questions, saved in [focused-rows.json](focused-rows.json). It did not reliably obey the instruction, retained speculation and lost useful location detail. The instruction was removed before release. No model weights, benchmark scores or frozen historical predictions were changed.

The three cases are development/regression evidence, not an untouched test set or a replacement VRSBench score. Descriptive answer factuality remains an open quality issue. No new accuracy claim is made.
