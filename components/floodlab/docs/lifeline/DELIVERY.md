# Lifeline comparison and Flood Lab implementation — 5 November 2026

The response implementation is complete and tested locally. Full Lifeline scientific parity and
superiority are **not established**. This receipt closes the implemented response workflow and records
the remaining scientific work explicitly. The cosmic UI request supplements the comparison work.

## What changed

- New **Response** screen inside Flood Lab, sharing the existing selected run with Workspace.
- Directed multigraph routing preserves one-way streets and parallel roads; existing mapped node IDs
  prevent invented connections at geometric crossings. Turn restrictions are still absent.
- Before, optimistic-after and conservative-after route witnesses retain every segment's source ID,
  length and observation state. Distances are mapped lengths, not travel times.
- Single-road and joint serial-cut repair scenarios return conditional gains. Unknown observations
  remain unknown after repairs. Missing hubs/off-network places remain not assessed; missing-hub
  route aggregates are null in the API rather than zero.
- Bounded repair search checks every single candidate way and joint bundles from directed pre-event
  shortest paths. This is not an exhaustive global minimum-repair solver.
- Content-addressed field kit: KML, GeoJSON, calculations, facts ledger, English/Nepali alert drafts,
  source hashes and ZIP. Original frozen observations are read-only. Nepali needs human review.
- Existing SATQuery Scientific Noir assets, Saturn identity, black cosmic background and glass panels
  reused in Flood Lab. Geist, Space Grotesk and IBM Plex Mono are bundled locally with OFL licenses.
  Manual road selection and source details are disclosures. Ranked actions are visible first.

No thresholds, masks, reference labels, model weights or frozen scientific results changed. “Clear”
means satellite-covered with no qualifying candidate intersection, not a field-confirmed open road.
Routes are hypothetical mapped-network scenarios, not evacuation or safe-navigation instructions.

## Evidence actually collected

| Check | Result | Scope / receipt |
|---|---|---|
| Original dirty baseline | 69 passed, 1 failed | Stale inspection/acquisition assertions; no model calculation failed |
| Final Python suite | **86 passed**, 36 warnings | `../test-results.xml`; meaningful routing, export-integrity and regression cases |
| Live HTTP | **PASS** | `http-ui-final.json`: GET, POST, errors, all 8 exports, SHA headers, ZIP CRC/payload identity, KML parse, exact served artwork/fonts/licenses |
| Frozen Nepal data | **15/15 files unchanged** | Same HTTP receipt, verified before and after scenario calculations |
| Original checkout preservation | **103 source + 59 data files unchanged** | `preservation-verification.json`, compared to the initial snapshot |
| JavaScript | Syntax passed | `node --check web/response-panel.js` |
| Browser | Core workflow passed | Saved Nepal load, four-road scenario, conservative absence, manual single repair, reset, dataset stale-state clearing, missing hubs, real field-kit download, sourced building answer, optical viewer, Workspace/Evidence navigation |
| Responsive UI | Partial rendered acceptance | 1440 px desktop, 390 px phone inspected; route-table overflow fixed and geometry verified. Final phone Evidence layout correction was not rendered after browser control became disabled |
| UI assets | **9/9 exact originals** | `UI_ASSETS.json`: five supplied artwork files and four font binaries; no evidence pixels restyled |

The original reference-registration test assumed that inspection and acquisition had never happened.
Both flags legitimately advanced. The replacement checks boolean status, evaluation-only roles and
retained hashes, and scans prediction/response source for reference-label leakage. It does not erase
a scientific failure. Logs outside this Git worktree retain the initial failures and final reruns.

Browser download `bundle.zip` matched the live endpoint's SHA-256:
`d88f100c837c1fe921188e93ce390c275b04bf1cf1b9c3a7e1131d199972373a`.
The saved screenshot `screenshots/response-phone.jpg` is the inspected cosmic phone layout after the
route overflow fix; it predates the final phone Evidence-only correction. No final desktop screenshot
was saved before browser use was disabled. Source hashes in `browser-verification.json` describe the
final files, with that unrendered delta explicitly disclosed.

## Real Nepal result

Run `nepal-syapru-004` uses SAR 16/28 August, optical 12/27 August and historical OSM 27 July 2026.
It is a different rectangle from `event-fe47db331390` (the 9.56 ha water / 10.41 ha debris example).
Their measurements and infrastructure snapshots must not be pooled.

For the selected study population of **two** places, one has a mapped baseline route; one is off-network.
There are 13 candidate-disrupted source ways. All 13 single-way repairs add zero possible routes.
One four-way bundle adds one possible route for Syabru Bensi:

`way/332122791`, `way/83925854`, `way/84566285`, `way/84566287`.

Together they represent 1,206.80 m of candidate road length in this model. The route is about 15.16 km,
but unknown observations remain: **one possible route, zero routes without unknown sections**.
Fourteen scenarios were evaluated. This does not establish that those roads actually closed, that a
repair would physically reconnect the settlement, or that other unmapped/out-of-area routes do not exist.

The 9.56 ha example has no usable destination set in its saved graph, so this workflow returns
`NOT_ASSESSED_NO_HUBS`. It does not borrow service destinations from the other rectangle.

## Matched comparison we can defend

Pinned upstream: [kinnuworks/lifeline](https://github.com/kinnuworks/lifeline/tree/2945725810d6088317f65e3edb72db578c0b9528).
The MIT license is retained in `LIFELINE_LICENSE.txt`. Our response code is independently implemented.
Only the audited `_undirected_csr` function was executed for comparison, extracted from its hash-pinned
source with a restricted numerical namespace; the complete competitor system was not run.

`network-contract-benchmark-final.json` enumerates **all** 4,096 three-node directed graphs where each
possible directed edge is absent, clear, disrupted or unknown. An independent forward BFS checks the
optimistic/conservative reachability bounds: Flood Lab matches **4,096/4,096**.

For the **729 known-state graphs**, the supplied directed-edge contract has no probabilistic assumptions:

| Kernel | Matches independent directed-route oracle | False route positives |
|---|---:|---:|
| Flood Lab response bounds | 729/729 | 0 |
| Lifeline's actual undirected CSR kernel | 521/729 | 208 |

The difference follows from symmetrizing directed edges. This is a directionality-contract advantage,
not a whole-system leaderboard, flood accuracy score, representative road prevalence estimate or
proof that Lifeline's intended undirected contract is implemented incorrectly. Flood Lab already
preserved directed topology before this change; this work extends that property through repair scenarios.

Native competitor raster outputs were absent from the pinned public snapshot. Published scalar scores
and PNG previews cannot substitute for native predictions on the same labels, resolution and support.
No claim is made to outperform their extent detector, trained model, field access or event generalization.

## Run and inspect

Local demonstration: `http://127.0.0.1:18870/#response`.

For a checkout with the required retained inputs installed:

```sh
python -m pytest -q
python -m uvicorn floodlab.server:app --host 127.0.0.1 --port 18870
python scripts/run_response.py nepal-syapru-004
python scripts/verify_response_http.py --output docs/lifeline/http-new-receipt.json
python scripts/benchmark_response_contract.py --upstream ../reference --output docs/lifeline/network-new-receipt.json
```

This machine's active worktree contains the prepared/frozen data listed in `BASELINE_SNAPSHOT.json`.
They are Git-ignored, and a clean clone does not include them. The separate upstream source clone is
required only for reproducing the comparison. `requirements-lock.txt` is the existing Python environment
specification; no new Python or JavaScript runtime packages were installed.

APIs: `GET /api/response/runs/{run_id}`, `POST /api/response/runs/{run_id}/scenarios` with
`{"restore_way_ids":["way/332122791"]}`, and per-scenario artifact URLs returned by those responses.
Invalid repairs return 422, absent runs 404, incomplete/integrity-failed or busy exports 409.
Server-side calculations may continue after a client cancels; only one scenario calculation runs at a time.

## Two-minute demonstration

1. Workspace: select `nepal-syapru-004`; show genuine optical before/after dates and candidate layers.
2. Ask “How many buildings intersect the water candidates?” with Buildings selected; open its source.
3. Response: load evidence; show boundary uncertainty and the off-network place.
4. Test the four-road scenario. Show the possible route, then exclude unknown sections: no witnessed route.
5. Download the field kit; open source hashes. Switch to `event-fe47db331390` to show honest missing hubs.
6. Evidence: distinguish the 86 software checks from the still-unproved event accuracy.

No recording was made. Final small-screen Evidence acceptance remains incomplete. The comparison's
remaining scientific requirements are in `COMPETITION_PLAN.md`; this work must not be called a full win.

## Change ownership and history

`1ec2a11` preserves pre-existing uncommitted Flood Lab work; it is not a new-contribution claim.
`6ea078b` adds the verified response engine/API/exports/tests/audit. The UI and delivery receipt follow
in a separate genuine commit. Development stays in `codex/lifeline-response-20261105`; the original
dirty checkout, SATQuery main, scientific-development branch and immutable Day 1 tag are preserved.
Nothing was published or pushed. Codex assisted implementation, tests, comparison and documentation.

Final preservation check: SATQuery main is still `fe8a038d1aebe84e1385e228749901c4a18f7f36`;
`day1-final` remains tag object `a08d2706397d359edb060993ee3a14374b3d136f`, pointing to
`f3945347cf0f0a4581aa1480c8fa1501a25da4b4`. No history was rewritten.
