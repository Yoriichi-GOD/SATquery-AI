# Actual JAI extension architecture

The optional `start_jai.py` process loads the approved prior SATQuery installation in place and adds isolated routes. Original specialist handlers remain unchanged. Current demo port: loopback 8768; original SATQuery stays at 8767. The read-only adapter calls Flood Lab at loopback 8770. No iframe, public listener or paid service is introduced.

```text
Native SATQuery workspace
  Flood Intelligence -> /api/flood/* -> bounded loopback HTTP -> prior Flood Lab
  Terrain -> /api/terrain/* -> verified local GLO-90 source/analysis TIFFs
  Align -> /api/context/coverage -> hash-checked raster reprojection + shared support
  Profile -> /api/terrain/scenes/{id}/transect -> bilinear metric samples with gaps
  Investigate -> /api/investigations -> one bounded worker
      deterministic plan -> actual registered tools -> hash-chained records
      source-value claims + evidence pointers -> human review
      explicit Stop -> cancellation check, including after in-flight read timeout
```

| Registered tool | Reads/calculates | Output boundary |
|---|---|---|
| get_run | Verified saved result/manifest | Historical heuristic candidates and source dates |
| get_exposed_assets | Verified exposure.csv | Historical mapped-feature intersections; no damage |
| get_dem | Verified cached DSM | Statistics and source identity; no acquisition |
| analyze_coverage | Actual prediction/DSM TIFFs | CRS mapping, shared valid support and coordinate controls |
| terrain_transect | Cached projected DEM | Bounded bilinear profile, no missing-data bridging |

The registry is visible at `/api/investigations/tools`. Derived coverage/profile evidence is served from `/api/investigations/{id}/tools/{tool}` using recorded outputs. Original files remain available through their guarded source routes. Facts name the machine field used; settlement status is explicitly NOT_ASSESSED when the saved record says assessment was not performed.

The planner is deterministic and the UI declares that no AI model is called. There is no prompt evaluation of feature names; they are inert text. Requests have identifier/size/sample limits, one active job, a 45s checked deadline and bounded HTTP reads. Stop suppresses later output and takes precedence over a source timeout. Job traces survive server restart; unfinished jobs become interrupted. Hash chains detect local trace modification but are not signatures against a fully rewritten local store.

Runtime paths: `.runtime/jai/terrain`, `.runtime/jai/investigations` and `.runtime/jai/*.log`. Keep them out of Git. The original providers' licenses and source-time caveats remain applicable; source images, weights, credentials and private Research are not imported. See DATA_SOURCES.md and BASELINE_PROVENANCE.md.
