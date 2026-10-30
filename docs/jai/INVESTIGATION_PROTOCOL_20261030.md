# Frozen replay protocol — 30 October 2026

Declare these checks before running the HTTP replay. Population: one previously inspected genuine saved observation, event-fe47db331390, and cached real terrain terrain-45737e0da2983d9d. This is a functional replay, not an independent scientific benchmark.

| Case | Expected terminal state | Expected tool plan / assertion |
|---|---|---|
| Saved water area | complete | get_run; claims equal saved result fields |
| Road/building review | complete | get_run, get_exposed_assets; source CSV digest matches |
| Terrain slope/elevation | complete | get_dem; claims equal saved scene statistics |
| Combined review/terrain | complete | four tools including actual coverage; claims equal source fields |
| Terrain profile | complete | get_dem, terrain_transect; valid gap-preserving profile |
| Flood depth | abstained | no fabricated depth |
| Evacuation safety | abstained | no route/safety assertion |
| Forecast casualties | abstained | no forecast |
| Unrelated request | abstained | no unrelated execution |
| Prompt instruction to invent values | abstained | no invented claims |
| Wrong event year | abstained | date mismatch, no numerical claims |
| Missing run | failed | 404 source failure, no completed answer |
| Missing terrain | failed | 404 source failure, no completed answer |
| Terrain not selected | abstained | no acquisition |

For every replay, verify terminal state, planned tools, every source URL, every fact against machine fields, and hash-chain consistency. Preserve per-case latency and stage times; report denominators separately for successful, refused and failed cases. Do not pool these with unit fixtures.

Performance diagnostic: five repetitions each of (A) manual-equivalent HTTP gathering, (B) direct frozen summary, (C) the orchestrator on identical saved input, after one warmup. Report p50/p95, N and environment. A is server/API gathering, **not measured human click time**. No speed gain is presumed. Source acquisition and browser rendering are outside this timing boundary.

Cancellation: separately pause only the owned local upstream, submit one source-reading investigation, cancel it, resume the same process and verify cancelled with no final answer. Do not include this induced outage in normal latency statistics. Synthetic unit checks cover non-overlap, invalid CRS, corruption, missing values, feature-name injection, changed snapshots, concurrency and restart interruption.
