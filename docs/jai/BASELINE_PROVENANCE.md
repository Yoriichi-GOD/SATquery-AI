# Prior work and new extension

Main SATQuery: https://github.com/Yoriichi-GOD/SATquery-AI at `f5a5a5fb2af8466a304911e462ecfae305f09b6b`, clean local worktree at audit.

Flood Lab local checkout: HEAD `72b50701df53075b0f047c0e45ca8de2e0e18514`, with substantial existing modified/untracked implementation. This SHA alone does **not** identify its running code. `BASELINE_SOURCE_HASHES.json` records the actual source files inspected. The published repository has later documentation; the local implementation and original evidence are retained as separate baseline facts.

No prior application code is relabeled as new event implementation. The extension loads the participant's existing SATQuery installation explicitly and talks to the existing Flood Lab over loopback HTTP. Those sources, dependencies, models and saved observations remain prior work. New work is under `jai_extension/`, `tests/` and this repository's documentation.

The genuine saved run `event-fe47db331390` has 15 existing frozen artifacts. All 15 matched the saved SHA-256 map during preflight. It is a historical observation analysis, not a new acquisition or validation benchmark. Historical poor external agreement remains applicable; this integration adds access and terrain context, not demonstrated flood detection accuracy.

Both original software projects retain their existing license terms. Dataset and model licenses are separate. No credentials, imagery corpus, model weights or private manuscript are copied into this repository.
