# Repository contents

Start with the [README](README.md), [reviewer walkthrough](docs/REVIEWER_GUIDE.md), [architecture](docs/ARCHITECTURE.md), [setup guide](docs/SETUP.md), and [claim register](docs/CLAIM_REGISTER.md). The served application includes an explicit experimental CDVQA mode; historical specialist benchmarks retain their own evidence. [Product captures](docs/images/README.md) identify real screens; [presentation verification](docs/PRESENTATION_VERIFICATION.md) records the checks.

| Location | Role |
| --- | --- |
| Root Python modules and `web/` | Current single-image service and UI |
| `paired_lab/server.py`, `paired_lab/controller.py`, `paired_lab/web/` | Current unified interface and dispatch |
| `paired_lab/mci.py`, `paired_lab/mci_vendor/` | Active temporal specialist |
| `paired_lab/engine.py` | Active BIFOLD land-cover functions; explicitly marked legacy ChangeFormer functions |
| [CDVQA model](paired_lab/cdvqa_model.py), [browser bridge](paired_lab/cdvqa_bridge.py), [CLI](scripts/predict_cdvqa.py) | Experimental change-question specialist; explicit mode and supported templates |
| [Runtime paths](runtime_paths.py), [asset inventory](docs/ASSETS.md), [preflight](scripts/preflight.py) | Configurable assets, pinned provenance and missing-dependency checks |
| [Implementation review](docs/PENDING_RELEASE_REVIEW_20261027.md) | Reviewed local improvements, executed checks and remaining gates |
| `grounding_lab/` | Experimental grounding implementation and its historical evidence |
| `tests/` | Model-free software regression suite |
| `paired_lab/evidence/benchmark-20260921/` | Frozen benchmark inputs, outputs, methodology and hashes |
| [CDVQA report](docs/CDVQA_FINAL_REPORT.md), [saved predictions and summary](paired_lab/evidence/cdvqa-trained-20260928/) | 28 September experimental benchmark, controls and exclusion sensitivity |
| [Public VQA diagnostics](paired_lab/evidence/public-benchmarks-20260927/README.md) | Raw VRSBench results and whole-response exact-match limitations |
| [Publication checker](scripts/check_publication.py), [CI](.github/workflows/software-tests.yml) | Saved-metric consistency, new-commit hygiene and software regression |
| `docs/` | Setup, claims, closure and acceptance protocol |
| `backups/`, `demo-freeze-20260907/`, `SATquery-evidence-pack/`, same-named ZIPs | Historical snapshots; not active code or authoritative current claims |
| `results/`, `ppt_handoff/`, `demo run/`, `design/`, `UI/` | Earlier evaluation, presentation and design material; inspect dates before reuse |

Historical bundles remain in place to preserve existing references and provenance. They duplicate some expanded files; do not run deployment from them. `.gitignore` prevents new caches and archives from being added, but does not remove historical tracked archives. No history rewrite is performed.

## Historical material: why paths remain stable

| Location | Retention reason |
| --- | --- |
| `ppt_handoff/` | Original evidence; `evaluation.py`, `tests/test_stages.py` and the pack's own collector still refer to this path |
| `SATquery-evidence-pack/` and `SATquery-evidence-pack.zip` | Expanded snapshot and original archive; `scripts/verify_overnight.py` reads the ZIP |
| `demo-freeze-20260907/` and `SATquery-demo-freeze-20260907.zip` | Older UI/source freeze and provenance referenced by the handoff and paired-lab audit |
| `backups/` | Historical source snapshots referenced by implementation and verification reports |
| `demo run/`, `results/`, `ppt_handoff/` | Earlier samples and results; dates and evaluation protocols must be checked before reuse |

On 18 October 2026, all 121 evidence-pack archive members and all 32 demo-freeze archive members matched their expanded local counterparts by SHA256. This establishes duplication for those archive members only, not that every historical directory is disposable. Retaining the paths avoids changing tests and historical audit trails for presentation alone; moving files would not reduce Git history or historical clone weight.

For external runtime assets and omitted data, see [evidence storage](docs/EVIDENCE_STORAGE.md) and its manifest.
