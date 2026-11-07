# Flood workspace UI

Port 8770 contains only Workspace and Evidence. Flood-impact results are rendered directly in the main workspace; no iframe or Experimental tab is used. The original SatQuery stylesheet, gray-black theme, artwork and left-visual/right-analysis structure are retained. Unrelated VQA, NDVI, generic change and grounding controls are absent from this application's UI.

Workspace currently inspects saved flood-pipeline runs, infrastructure, access and downloads. Live raw-scene acquisition/analysis remains unimplemented; the interface does not pretend that saved synthetic results are a real event run.

Evidence reads the local test report and independent benchmark registry. Source MIT notice: vendor/SATQUERY-LICENSE.txt. No requests are forwarded to original SatQuery. All changes remain local; source SatQuery is unchanged.
