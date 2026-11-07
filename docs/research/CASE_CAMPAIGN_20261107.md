# Four-case campaign: reproduction and application access

Read [the measured report](../../research/results/case-campaign-20261107/REPORT.md) before quoting a
number. This release adds acquired case inputs, deterministic processing, provenance checks and local
API integration. It does not add trained models or establish independent exposure accuracy.

## Local release

The active branch is `codex/research-release-20261107`. The application shell was merged from current
main with the November5 scientific branch. `components/floodlab/` is a byte-pinned tracked source
snapshot of `d4c917f865b295f30c712b4f0c12ed1f3849acd1`; its source manifest and original attributions
are retained. Its upstream history is referenced, not fabricated as new hackathon or research work.
No original worktree, private credentials, model weights or immutable Day1 checkpoint was altered.

Two services use separate environments because the original application and Flood Lab have different
dependency locks. The CPU research measurements use `research/requirements-scientific-lock.txt`.
The application also needs the established inference runtime documented in `docs/SETUP.md` and
`requirements-inference-tested.txt`; the scientific lock alone does not contain Torch. The actual local
check reused installed Torch2.8.0+cu128 via an isolated environment fallback; existing research packages
take precedence. No model was fetched, trained or inference-benchmarked by these HTTP checks.
Exact versions and module locations are in the environment receipt.

From the release checkout, with those environments and local data provisioned:

```bash
python scripts/start_research_release.py --port 18968 --flood-port 18970 \
  --flood-python /path/to/floodlab-env/bin/python
```

The launcher refuses occupied ports, binds loopback only, keeps writable application state isolated,
and stops its own child services on exit. It does not replace other running SATQuery instances.

- Main workspace: `http://127.0.0.1:18968/`
- Four-case catalogue: `http://127.0.0.1:18968/api/research/cases`
- Case summary/source receipts/image: `/api/research/cases/{case}`, `/{case}/sources`, `/{case}/panels.png`
- Scientific terrain catalogue: `/api/terrain-exposure/runs`
- Pinned Flood Lab/response interface: `http://127.0.0.1:18970/`
- Example response API: `http://127.0.0.1:18970/api/response/runs/nepal-syapru-004`

Case IDs are `nepal`, `kedarnath`, `varanasi`, `sangam-vihar`. Read APIs verify artifact hashes and
reject missing/tampered data; HTTP does not accept arbitrary local paths, imagery URLs or acquisition
requests. The new cases are exposed through these read APIs and the research pack, not new terrain UI
controls. The existing transparent-header/body-clipping design and specialist workflows are retained.

One active30m Nepal scientific replay is provisioned so deterministic investigations cannot silently
choose between two experiments. The90m sensitivity output stays separate. Infrastructure questions
correctly abstain because the declared10m feature-resolution requirement remains unsatisfied.

## New public case acquisition and measurements

Use a fresh output directory; complete local runs are never silently overwritten. Commands below do
not install packages or acquire the original saved Nepal event. Native windows use bounded HTTP-range
reads; public signing is account-free and tokens remain in memory. Network access and provider
availability still determine whether a fresh acquisition succeeds.

```bash
python -m research.cases.acquire_campaign --output research/datasets/local/campaign-new/sources
python -m research.cases.process_campaign \
  --sources research/datasets/local/campaign-new/sources \
  --output research/results/local-campaign-new/measurements
```

The frozen protocol is `research/experiments/case-campaign-20261107.json`. It declares boxes, dates,
class semantics, QA exclusions, index thresholds, terrain settings, limits and reference roles before
new measurements. Processing checks the acquisition's case/protocol identity, each receipt/ROI/hash,
and required registered inputs. Extra TIFFs in the folder cannot enter the computation.
Native10m urban arithmetic is separate from30m terrain computation; coarsening cannot create detail.

The general case API is read-only and does not acquire data or run a model. Unavailable inputs fail
explicitly; do not copy a convenient stale file in place of a declared source. Landsat's postevent
Kedarnath date was cloudy; its retained quality failure is an actual result, not a download failure.

## Nepal replay and baseline prerequisites

The graph replay requires the unchanged saved `event-fe47db331390` artifacts and historical OSM.
Road diagnostics additionally require its retained pre/post SAR rasters and the original inspected
EMSR927 AOI01 GeoPackage with the protocol's exact hash. The response component also requires the
separate `nepal-syapru-004` example. These are conditional reproducibility prerequisites, not an assertion
that a fresh public query reproduces all historic files. Sources/licenses are distinct from code licensing.

```bash
python scripts/prepare_research_release.py --flood-source /path/to/retained-floodlab \
  --terrain-source /path/to/retained/terrain-cache
python -m research.experiments.nepal_resolution_campaign \
  --flood-root /path/to/retained-floodlab \
  --sources research/datasets/local/campaign-new/sources \
  --output research/results/local-campaign-new/nepal-resolution
```

The preparation script copies only hash-verified frozen artifacts, two explicitly registered references,
and the verified original3D scene. It does not scan/copy `.env`, credentials, untracked experiments or
arbitrary source folders. A new buffered GLO30 source is separately declared before its replay. Set
`--prediction-run` to either new replay when running `python -m research.experiments.nepal`; use the
unchanged `research/experiments/nepal-road-screening.json` protocol and registration audit. Run both
resolutions, all declared methods and abstention counts. Never select the best column as a blind result.

## Verification and evidence

```bash
python -m unittest discover -s tests -q
# Run separately inside components/floodlab using its environment:
python -m pytest -q
python scripts/check_research_release_http.py \
  --output /path/to/new-http-receipt.json
```

Final local evidence:302 main tests,86 component tests,31 live HTTP checks, an independently recomputed
383,871-relationship graph and two native urban transition matrices, plus43 scripted typed-claim
challenge trials. Failed acquisition/registration attempts and a rejected ingestion repeat are retained.
The corrected manifest-only pipeline reproduced the first declared-input numeric run; the final guarded
pipeline was run again. Browser rendering, fresh specialist inference, humans, field conditions and
independent exposure accuracy were not validated by this campaign.

`scripts/package_case_campaign.py` collects initial review receipts; `scripts/verify_case_campaign.py`
independently checks copies, arithmetic and the recorded repeat. `scripts/freeze_case_pack.py` hashes
the finished pack and selected executable sources. For a Windows-created worktree processed in WSL,
Windows Git must supply the actual full `--source-commit`; Linux Git cannot resolve the Windows `.git`
pointer. Per-file hashes record actual source bytes. They are integrity receipts, not signatures.

AI assistance: Codex implemented the integration, acquisition/measurement code, tests and documentation;
scoped research agents checked primary-source dataset access and literature. No assertion of expert
geoscience review, first-ever novelty, autonomous LLM reasoning, or validated scientific superiority is made.
