# Browser benchmark evidence

The Evidence overview displays CDVQA Test-1/Test-2, all three water pathways, and road/building change. Detailed evaluations include controls, per-type CDVQA scores, exclusion sensitivity, both water splits, temporal classes and the narrow land-cover fixture evaluation. Existing VQA/NDVI development checks remain labeled as archived/development evidence.

Scores are generated from saved evaluation artifacts by `python scripts/build_evidence_page.py`. Run it after changing source evidence. `python scripts/build_evidence_page.py --check` and the software regression suite detect stale browser data. Source hashes use LF-normalized UTF-8 text to remain stable across Git checkouts on Windows and Linux, and are included in the downloadable JSON.

CDVQA remains a separately evaluated experimental specialist, not an integrated browser workflow. Split overlap, sample counts and metric definitions are shown beside the results. No model was rerun or benchmark score changed for this page update.

Verification: 96 software tests passed; JavaScript syntax checks passed; overview and detailed tables inspected in the local browser with no console errors. Fixed artwork layout preserved.
