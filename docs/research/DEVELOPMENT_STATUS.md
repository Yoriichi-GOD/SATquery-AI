# Scientific development status

Started 5 November 2026. Branch `codex/scientific-terrain-20261105`, isolated worktree.
Baseline commit: `fe8a038d1aebe84e1385e228749901c4a18f7f36`; original main was clean.
Immutable `day1-final`: `f3945347cf0f0a4581aa1480c8fa1501a25da4b4`.

## Current milestone closure

**PARTIAL — independently validated exposure assessment has not been established.**
The initial audit below is retained as history. Current evidence and completion gates are in the
[measured report](../../research/results/terrain-exposure-20261105/REPORT.md) and
[machine-readable status](../../research/results/terrain-exposure-20261105/completion.json).

| Priority | Requirement | Current status |
|---|---|---|
| P0 | Typed terrain graph, metric hydrology and genuine terrain replay | PASS for coarse numerical/geometry scope |
| P0 | Infrastructure relationship exports | PARTIAL; operational, but 90 m insufficient for infrastructure scale |
| P0 | Independent class-compatible Nepal exposure/extent validation | BLOCKED; suitable labels and registration unavailable |
| P0 | Controlled ablations | PARTIAL; eight methods on 22 explicitly graded road fragments, diagnostic target |
| P1 | Registration | PARTIAL; synthetic transforms tested, genuine optical audit unavailable |
| P1 | Urban transfer | PARTIAL; two genuine public DSM runs, ingestion and resolution refusals |
| P1 | Reproducibility | PARTIAL; pinned CPU/public examples, externally provisioned Nepal source dependencies |
| P2 | Analyst harness | PASS for 40 scripted operations; no human productivity evidence |
| P0 | Application/evidence preservation | PASS; 287 Python tests, retained 6/5 helper checks, 5 UI contracts and genuine HTTP checks |

The new branch has additive commits `bf05367`, `9a6c32a` and `055fa8b` plus the final closure commit.
No original benchmark score, model checkpoint, Day 1 tag or main history was rewritten.
The complete local exports are under `research/results/local-20261105/`; large third-party data remain ignored.
Do not start parameter tuning on the inspected reference labels. The next dependency is compatible independent
Nepal labels, trustworthy registration and appropriate terrain/drainage data. Rendered UI behaviour and human
analyst improvements remain unverified.

## Definition of done

| Priority | Requirement | Initial status | Acceptance evidence |
|---|---|---|---|
| P0 | Conditioned DEM, D8, accumulation, streams, catchments, HAND | FAIL | Numerical invariants and genuine DSM replay |
| P0 | Typed source/pathway/receptor graph and exposure exports | FAIL | Geometry/unknown tests, real run, source hashes |
| P0 | Independent class-compatible Nepal task | BLOCKED | Inspect original reference semantics first; no mixed-class debris/water accuracy |
| P0 | Frozen fair ablations A/B/C/D | FAIL | Same task/support, measured results, unavailable inputs explicit |
| P1 | Registration diagnostics | PARTIAL | Existing SIFT diagnostic lacks residual/support audit; genuine and known-shift trials required |
| P1 | Varanasi/Sangam Vihar | FAIL | Executable ingestion/discovery and resolution guards, genuine coarse replay where accessible |
| P1 | Reproducibility | PARTIAL | CPU environment, CLI, hashes, licenses, frozen configuration and independent recomputation |
| P2 | Analyst harness | FAIL | Scripted timing distinguished from human measurements |
| P0 | Preserve existing application and scientific evidence | PARTIAL | Full regression and unchanged historical files/tag |

## Baseline audit

The existing JAI terrain module supplies metric reprojection and Horn slope, not hydrological routing.
Flood Lab already retains water/debris candidates, OSM intersections, and evaluation-only EMSR927/UNOSAT files.
The original benchmark measurements are retained unchanged. CDVQA results are not Nepal validation.

First isolated-checkout regression: 258 tests, one error in `test_saved_predictions_and_regressions`.
`core.autocrlf=true` changed a byte-hashed JSONL input to CRLF; the scientific hash guard correctly rejected it.
The fix is an explicit LF checkout attribute, preserving the frozen bytes and expected hash.
Full baseline log is retained outside source at `../baseline-tests.log`.

## Scientific boundaries

DEM routing describes potential topographic connections under declared conditioning/boundary assumptions.
It does not simulate a floodwave or debris-flow dynamics. Coarse DSM cells cannot resolve individual urban drains.
Direct geometric intersections are distinct from potential paths, observed candidates, unknown coverage and damage.
No parameter is to be selected against the previously inspected Nepal reference labels.
The new Nepal work is a development/reference replay, never an untouched test.

## Execution

Inspect/baseline → core engine → compatible Nepal tasks → ablations → registration (earlier if required)
→ geographic transfer → reproducibility closure → analyst comparison. Update this document with evidence,
including negative results and blocked scientific requirements. Code existence alone does not satisfy validation.
