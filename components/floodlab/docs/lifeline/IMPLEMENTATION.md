# Lifeline-targeted Flood Lab work

Target: `kinnuworks/lifeline`, pinned revision `2945725810d6088317f65e3edb72db578c0b9528`.
Read-only source snapshot inspected 5 November 2026. MIT license retained in `LIFELINE_LICENSE.txt`.
Source: https://github.com/kinnuworks/lifeline . Prior competitor review is context, not a runtime verdict.

The dirty Flood Lab baseline was copied unchanged into an isolated worktree. The snapshot commit is
pre-existing local work, not a claim of new Lifeline implementation. Original checkout/data remain untouched.

## Acceptance gates

1. Close the known stale reference-inspection assertion while enforcing evaluation-only reference roles.
2. Add an integrated directed-network response workflow: before/after route evidence, explicit observation
   bounds, single-way and joint repair scenarios, ranked conditional gains and field exports.
3. Verify direction, overpasses, parallel edges, unknown coverage, AOI boundaries, missing hubs, and serial cuts
   against an independent small-graph oracle and the actual upstream undirected routing kernel.
4. Replay real Nepal evidence without changing its masks, dates or frozen files. Do not turn an unknown
   access state into “safe,” “no affected settlements,” or field-confirmed road closure.
5. Use the same task, input support and reference to assess performance. Do not compare our 22-road screening
   diagnostic with Lifeline's event-wide extent F1. Native competitor rasters are absent from the public source
   snapshot; published scalar tables cannot supply a matched pixel benchmark.

## Source-level findings

- `radar/change.py`: robust multi-date VV/VH change, high-HAND null threshold, multi-orbit fusion, constrained
  growth and separate terrain-inferred pixels. These are more developed than Flood Lab's fixed VV pair rule.
- `access/montecarlo.py`: `_undirected_csr` symmetrizes edges. `access/chokepoints.py` also uses undirected
  component connectivity. This is a concrete directionality comparison target; it does not prove the whole
  upstream system fails every route or that Flood Lab has better event accuracy.
- Upstream hit/closure scores and the 0.15 unseen-road prior are assumptions, not calibrated probabilities.
  Our first response implementation uses explicit optimistic/conservative graph bounds instead.
- The public run folders retain summaries and validation outputs; the advertised native raster
  products are not present in this clone. No preview image will be substituted for a native prediction.

## Remaining competition scope

After the response workflow closes: multi-baseline/multi-track SAR ingestion, radar-visibility diagnostics,
terrain-constrained event-impact candidates, same-support independent extent benchmarks, placebo events,
and geographic holdouts. Genuine historical observations and reference-compatible target definitions are
required. No winner or superiority claim follows from implementing a feature or passing synthetic tests.
