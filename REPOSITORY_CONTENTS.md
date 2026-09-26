# Repository contents

| Location | Role |
| --- | --- |
| Root Python modules and `web/` | Current single-image service and UI |
| `paired_lab/server.py`, `controller.py`, `web/` | Current unified interface and dispatch |
| `paired_lab/mci.py`, `mci_vendor/` | Active temporal specialist |
| `paired_lab/engine.py` | Active BIFOLD land-cover functions; explicitly marked legacy ChangeFormer functions |
| `grounding_lab/` | Experimental grounding implementation and its historical evidence |
| `tests/` | Model-free software regression suite |
| `paired_lab/evidence/benchmark-20260921/` | Frozen benchmark inputs, outputs, methodology and hashes |
| `docs/` | Setup, claims, closure and acceptance protocol |
| `backups/`, `demo-freeze-20260907/`, `SATquery-evidence-pack/`, same-named ZIPs | Historical snapshots; not active code or authoritative current claims |
| `results/`, `ppt_handoff/`, `demo run/`, `design/`, `UI/` | Earlier evaluation, presentation and design material; inspect dates before reuse |

Historical bundles remain in place to preserve existing references and provenance. They duplicate some expanded files; do not run deployment from them. `.gitignore` prevents new caches and archives from being added, but does not remove historical tracked archives. No history rewrite is performed.
