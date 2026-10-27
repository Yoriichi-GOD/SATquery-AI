# Pending improvements — publication review, 27 October 2026

These improvements existed as local work after `cafdb80`. They add configurable runtime locations, explicit asset provisioning/preflight, bounded experimental CDVQA browser integration, prompt-routing corrections, and validation/acquisition tooling. Trained production checkpoints and historical benchmark numbers are preserved.

## Reviewed scope

- Runtime paths are configurable; optional BIFOLD assets load on demand. The asset inventory records pinned revisions, known hashes, required files, and manual-release dependencies.
- CDVQA uses an explicit prepared-RGB-pair mode with 300 supported question templates, equal dimensions, and an alignment/order declaration. Checkpoint and encoder hashes are verified before prediction. This integration does not improve the historical benchmark score or support arbitrary questions.
- Ordinary scene questions using “area” and image-relative location wording reach VQA; physical measurement, compound, forecasting and explicit grounding boundaries are retained.
- Validation-only model/gating experiments remain experimental scripts and dated reports. Rejected candidates were not promoted. Their cached features, weights, downloaded imagery and ignored execution outputs are not uploaded.
- The evaluation freeze records a historical dirty-tree baseline, not this new revision. Do not rewrite it or historical scores to match later code changes. The acquisition/alignment helpers retain the paths and assumptions of their recorded runs; they are not general-purpose installers.

## Fixes made during review

1. Corrected Windows-to-WSL argument handling in `start.ps1` using forward-slash paths and direct execution; retained asset-root and health-check options.
2. Required pinned VQA provenance for explicit model-directory overrides, preventing a different local model from inheriting the displayed pinned identity. Two regression tests cover this requirement.
3. Changed the HTTP smoke default to port 8767, added the browser Origin header, and verified byte-exact original uploads in the exported ZIP.
4. Updated the Evidence page's obsolete “not connected” CDVQA wording without changing its saved numerical data. Advanced static asset versions so cached local files refresh.
5. Added the 11 measurement-helper checks to GitHub Actions. Private research and separate Nepal/Flood Lab acquisition directories are ignored locally; their contents were retained.

## Executed verification

| Check | Result and practical limit |
| --- | --- |
| Application tests | 115 passed in the isolated Linux review checkout; includes mocks and synthetic inputs |
| Measurement helpers | 11 passed; known displacement, invalid landmarks, duplicate locations, and grid differences |
| JavaScript | Syntax checks and existing jsdom interaction check passed; jsdom alone is not layout evidence |
| Real CPU smoke | Water, MCI temporal, and three-path land-cover inference passed on tracked, previously inspected development examples; new outputs and CRC-checked ZIPs |
| CDVQA HTTP | Supported question completed; missing alignment and unsupported query refused; 19 scores, matching checkpoint identity, ZIP CRC and original bytes checked |
| Real browser | Template selection, uploads, missing-alignment refusal, CPU inference, two input views, 19 scores, image expansion, evidence download, replacement clearing, and unsupported-question refusal passed; zero JavaScript errors |
| Documentation merge | 167 local links/anchors checked across 12 guides; 16 desktop/mobile light/dark previews passed; published product screenshots and provenance retained |
| Preservation | 2,708 unrelated original files hashed unchanged, including all 395 excluded private/research/dataset files; historical measurements and model assets retained |
| Layout | Desktop 1440 × 1000, dark/light; mobile 390 × 844 had no document-level horizontal overflow. These are bounded checks of the CDVQA flow, not every workflow or viewport |

These are functional/regression results, not new accuracy measurements or new-machine model restoration. The existing isolated CPU environment and existing model assets were reused. GPU restoration, independent acceptance, broad grounding/description quality, and official paired-sensor semantic accuracy remain open.

Run the application suite with `python -m unittest discover -s tests -v` and helpers with `python scripts/test_measure_landmarks.py -v` and `python scripts/test_quality_readiness.py -v`. [Setup](SETUP.md) describes the runtime; [the improvement audit](IMPROVEMENT_AUDIT.md) retains earlier evidence and [the protocol](EVALUATION_PROTOCOL_V1.md) defines evaluation boundaries. Existing frozen byte-hash checks still require an LF-preserving checkout; Windows CRLF conversion must not be “fixed” by changing a frozen expected hash.

## Publication boundary

Only reviewed application, test, configuration, tool source and documentation changes are committed. `Research/`, `emsr/`, and both Nepal dataset starter directories remain on the original machine. No raw acquisition data, private manuscript/PDF, runtime uploads, database, installed dependency directory, new model weight, or generated experiment cache is part of this release. Historical tracked evidence is retained.

## CI portability follow-up

The first pushed integration commit failed GitHub Actions because Python 3.11 raised PermissionError while probing the developer's private legacy asset directory. Local privileged WSL checks had masked this condition. Asset discovery now uses explicit overrides without probing that directory and falls back to the current user's data directory when the legacy location is inaccessible. Two import-level regressions reproduce denied access and verify override precedence. After the fix, 117 application tests and 11 helper tests passed in the isolated Python 3.11 CPU environment. This changes runtime discovery, not models or historical scores.

The follow-up CI run passed all 117 application checks, then exposed a helper-discovery error: the broad scripts pattern imported the historical PyTorch CDVQA experiment. CI and setup commands now name the two model-free helper suites explicitly (6 landmark + 5 readiness tests), preserving the experiment unchanged. The final check uses a fresh Python 3.11 environment with only requirements-test.txt installed, without model dependencies or downloads.
