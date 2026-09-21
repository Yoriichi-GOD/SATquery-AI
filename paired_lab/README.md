# SATquery Paired Lab

Open http://localhost:8767. The unchanged main demo is http://localhost:8765.

Start in PowerShell with `./start.ps1` from this folder. This starts only the paired lab; it does not stop or modify the main app.

Choose a LEVIR pair and ask: "What changed between these two dates, and where?"
Choose a BigEarthNet pair and ask: "Use the optical and SAR images together to identify land-cover classes."
Open Evidence to inspect the saved trials. Click processing images to enlarge them. Download evidence to obtain the original TIFF inputs, output images, score arrays where available, and JSON trace.

Read STATUS.md before presenting claims. PLAN.md records scope and acceptance criteria. samples/ contains 19 downloadable paired examples and publisher manifests. Original dataset files and checkpoints live in /root/satquery/paired-lab, outside the demo's data folders.

Runtime: existing Python 3.11 / torch 2.8 CPU operations, separate pip dependency target at /root/satquery/paired-lab/deps. Four CPU threads, one lab job at a time. No GPU calls; the main VQA GPU remains available. Cold model loading adds time; timings inside JSON are per-run local observations, not service guarantees.

Reproduce input validation: run test_inputs.py using /root/satquery/.venv/bin/python. Reproduce live API checks: run test_live.py while port 8767 is running. evaluate.py makes a new timestamped trial directory; preserved first/selected trials are not overwritten. Model-download manifests record exact revisions. bootstrap.py can restore pinned runtime assets using the existing Python environment.

Model provenance: ChangeFormer (https://github.com/wgcban/ChangeFormer) uses published LEVIR weights, not our training. Its README restricts use to non-commercial research; review licensing before commercial distribution. BIFOLD BigEarthNet v2 ResNet50 model cards mark weights MIT. ConfigILM (https://github.com/lhackel-tub/ConfigILM) provides the preprocessing constants and a small real-data fixture copied from BigEarthNet v2. Dataset licenses remain separate from code/model licenses. Do not redistribute the models or data as our original work.

Scope: building-related binary temporal change; Sentinel-1 VV/VH + ten Sentinel-2 bands scene classification. No arbitrary SAR sensor transfer, generic temporal reasoning, direction-of-change guarantee, calibrated confidence, exact building counts, or spatial fusion segmentation.
