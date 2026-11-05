# Terrain-conditioned graph and API contract

Schema: `satquery.terrain-exposure/1`. This is a bounded CPU research extension of the existing application.
It is not a second UI, a hydraulic simulator, a trained debris model or a damage detector.

## Processing API

- `hydrology.derive(z, valid, grid, stream_area_m2, conditioning)` returns original and conditioned elevations,
  D8 and flattened downstream IDs, contributing area, drainage threshold mask, outlet catchments,
  flowpath HAND, original-surface Horn slope/aspect and explicit boundary metadata.
- `graph.Observation` requires a candidate mask, separate valid mask, metric grid, times, method and source hash.
  Supported source classes are explicit observation layers; no class is inferred from a filename.
- `graph.Receptor` requires a unique ID, declared type, valid geometry/CRS, source hash and time.
- `graph.build_graph(...)` creates typed source, pathway and receptor nodes, typed directed edges,
  all source–receptor relationship attributes and per-layer coverage counts.
- `graph.export_graph(...)` writes normalized graph JSON, relationship CSV, compact receptor attributes,
  WGS84 GeoJSON and metric GeoTIFF derivatives. Detailed rows are separate from the interactive summary.

All graph geometries carry a declared projected CRS. GeoJSON exports use WGS84 coordinates.
Distances use metric projected units; pixel area comes from the affine, not nominal sensor resolution.
Source masks retain native pixel support; coarse routing does not upsample the DEM into false detail.

## States and ranking

| State | Meaning | Ordinal tier |
|---|---|---:|
| `DIRECT_GEOMETRIC_INTERSECTION` | Candidate geometry intersects the mapped receptor | 3 |
| `POTENTIAL_DOWNSTREAM_CONNECTION` | One or more D8 steps reach receptor-overlapping terrain cells | 2 |
| `NOT_CONNECTED_WITHIN_DOMAIN` | No supported in-domain route under this conditioning | 0 |
| `UNRESOLVED_WITHIN_DEM_CELL` | Same coarse cell without a resolved path or direct intersection | null |
| `UNAVAILABLE_EVIDENCE` | Required observation/terrain support is incomplete | null |

Tier values encode order, not calibrated probabilities, expected loss or a weighted risk formula.
No in-domain route is not proof that a physical event could never reach the receptor.
Sources are observed candidates, not confirmed hazards; invalid observations never become noncandidates.
Water and debris coverage populations remain separate.

Each relationship records direct area/length, planar and along-network distance, relative elevation,
HAND, slope, observation fractions, source/receptor times, resolution and registration status.
Node metadata preserve source hashes, native support, inference method and confidence unavailability.
The graph retains both the conditioned and original heights and reports fill magnitude.

## Terrain assumptions

Priority-Flood fills depressions to spill height; deterministic parent order routes equal-height flats
without adding fictitious epsilon elevation. `conditioning=none` retains sinks for a declared sensitivity run.
Outer edges and NoData perimeters are open unknown boundaries; routes cannot cross NoData.
Contributing area excludes external catchments. Streams are defined by a declared contributing-area threshold,
not verified river geometry. Catchments refer to this finite routing domain.

HAND uses the first downstream derived drainage cell's original height. Missing drainage and negative
original-height differences caused by conditioning remain unavailable. HAND is not water depth.
The minimum two-cells-across-target scale gate is an explicit sampling rule, not validation of physics.
The saved 90 m DSM fails both the 10 m Nepal infrastructure and 5 m urban target-width requirements.

## Read-only HTTP

| Endpoint | Response |
|---|---|
| `GET /api/terrain-exposure/runs` | Complete supported replay IDs, rejected/incomplete entries and scale status |
| `GET /api/terrain-exposure/runs/{id}` | Verified summary, compact receptor attributes and source links |
| `GET /api/terrain-exposure/runs/{id}/artifact/{name}` | Allowlisted hash-checked artifact, `X-Artifact-SHA256` |
| Existing `POST /api/investigations` | Existing job/trace contract with additive `get_terrain_exposure` tool |

The selected flood run must match the replay's source ID and both frozen mask hashes. Multiple matching
replays are rejected as ambiguous. Missing/incomplete data abstain instead of falling back to a different run.
Path escapes, unknown artifact names, bad manifests and tampered summaries fail closed.
Cancellation/deadline checks surround source access; existing job cancellation and hash-chain verification remain active.

Supported example: `Show catchments and flow accumulation` with the selected saved Nepal run.
`Which buildings have downstream connections?` returns the coarse context and an explicit abstention
because infrastructure-scale connectivity is unsupported. Depth, safety, damage and forecast questions
remain outside this observational workflow. No UI styling was changed; rendered UI behaviour was not reverified.
