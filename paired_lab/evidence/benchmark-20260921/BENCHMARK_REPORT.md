# SatQuery AI — benchmark findings, 21 September 2026

This is a bounded evaluation pass of the current local implementation, not ISRO certification, a full prescribed-benchmark run or proof of superiority to another team. Results, manifests, scripts and raw outputs are supplied alongside this report. Flood forecasting is removed from product scope.

## Results worth presenting

| Evidence | Measured result | Necessary qualification |
|---|---|---|
| Temporal road change | 80.99% IoU; 89.50% F1 | 100 LEVIR-MCI test pairs, 50 changed/50 unchanged; checkpoint inherited |
| Temporal building change | 81.69% IoU; 89.92% F1 | Same fixed subset; not CDVQA |
| Water segmentation | 82.64% joint IoU | 90 Sen1Floods11 test chips; previously evaluated split |
| Geographic water holdout replay | 81.58% joint IoU | 15 Bolivia chips; previously evaluated holdout |
| Negative controls | 0 predicted change pixels in all 10 controlled runs | 5 identical pairs + 5 brightness variants of those same scenes |
| Evidence integrity | NDVI, water and temporal measurements independently recomputed from exports | Selected live runs, not every stored run |
| Regression | 70 tests passed after targeted routing fixes | Includes mocked workflow tests; not 70 scientific accuracy trials |

The model and prompt were not tuned during this pass. Routing guards were fixed after baseline failures; post-fix routing results are regression evidence, not untouched accuracy.

## Frozen baseline and data exposure

`baseline.json` records source hashes, checkpoint hashes, installed packages, CPU/GPU and protocol. This run used a local RTX 5060 Laptop GPU (8151 MiB reported by driver); paired quality evaluation used CPU float32 with four PyTorch threads. Source entry points: paired_lab/mci.py, flood.py, engine.py, controller.py; root routing.py handles single-image dispatch.

Water: all 90 test and 15 Bolivia IDs; no overlap with local train/validation IDs asserted. These splits were evaluated before this task, so they are repeat evidence. Per-input hashes are stored in water-rows.jsonl. Temporal: fixed seed 20260921, excluding filenames from the prior local 100-case trial. The newly selected 100 pairs were frozen before inference. Source-scene independence between chips and upstream checkpoint exposure are not established. VQA: only 16 additional image IDs survived exclusions (9 rural, 7 urban); no sample-count inflation. Upstream VLM exposure remains unknown. Land cover: all 12 nontraining local BENv2 fixtures; geographically narrow, historically used. VRSBench: 12 images from distinct filename prefixes; official revision pinned and image hashes recorded. Review makes these development cases for any future prompt changes.

## Water: retain the three pathways

| Split | Chips | SAR IoU | Optical IoU | Joint IoU |
|---|---:|---:|---:|---:|
| test | 90 | 63.64% | 83.90% | 82.64% |
| bolivia | 15 | 64.05% | 81.44% | 81.58% |

Optical alone exceeds joint on the 90-chip test aggregate. Joint is slightly higher on Bolivia. Do not claim universal fusion superiority. Water includes permanent water; these are not verified flood-only masks. Scores use common finite input pixels and nonnegative reference labels. Confusion counts, F1, precision, recall and path disagreement are saved per chip. Metrics are pooled over pixels; pixels are not independent samples.

| Event | Chips | SAR IoU | Optical IoU | Joint IoU |
|---|---:|---:|---:|---:|
| Bolivia | 15 | 64.05% | 81.44% | 81.58% |
| Ghana | 11 | 56.59% | 57.53% | 63.39% |
| India | 14 | 68.34% | 88.67% | 87.87% |
| Mekong | 6 | 85.42% | 93.18% | 92.84% |
| Nigeria | 4 | 88.72% | 93.95% | 93.62% |
| Pakistan | 6 | 17.25% | 76.77% | 64.33% |
| Paraguay | 14 | 53.37% | 73.39% | 72.53% |
| Somalia | 6 | 45.12% | 80.72% | 79.97% |
| Spain | 6 | 69.89% | 84.20% | 83.61% |
| Sri-Lanka | 9 | 83.13% | 90.63% | 91.56% |
| USA | 14 | 49.42% | 80.41% | 74.46% |

## Temporal: segmentation and captions are separate

Road IoU 80.99%; building IoU 81.69%. Label encoding was checked as 0 unchanged / 128 road / 255 building. Published test references and raw model captions are retained in temporal-rows.jsonl. No caption factuality percentage is assigned.

Across 50 unchanged reference pairs, 1,213 of 3,276,800 pixels were predicted as changed (0.0370%). This pixel rate can coexist with scene-level errors; it is not a scene accuracy percentage. Ten additional identical/brightness controls predicted zero changed pixels. Construction versus demolition and CDVQA question answering are not established by these masks.

## Single-image findings

Rural/urban: 12/16 correct on the fresh availability-limited subset, using the current routed adapter. This small, imbalanced result is not a general VQA accuracy score.

Presence: the baseline completed 9/16 and incorrectly refused seven questions containing the noun “area”. The guard was fixed without enabling numerical area estimates. Post-fix decision extraction gives 9/16 correct, 16/16 completed and 0 unparsed/abstained. This exploratory extraction ignores added prose and is not comparable to published strict exact-match scores; prose still includes unsupported interpretations. These 16 questions reuse the classification images and must not be counted as 16 additional scenes.

Descriptions: all 12 live runs completed. Several missed aircraft, bridges, a dam or a smoke plume, and some added unsupported colour/use claims. DESCRIPTION_REVIEW.md records each finding. One reference caption appears inconsistent with the visible scene. No independent human adjudication, validated caption accuracy, or successful comprehensive-description fix is claimed.

Grounding: 3/6 aircraft reference boxes had at least one proposal overlapping at IoU >=0.5 across 4 images. This is **oracle proposal recall** on a selected category, not referring-expression accuracy, detector precision, or mask IoU. It is not comparable to the competitor's highest-score referring-box metric. No segmentation mask ground truth was available. Grounding remains experimental.

## Land-cover classification

Micro-F1 over 12 existing BENv2 fixtures: SAR 66.04%, optical 62.75%, joint 75.00%. These are scene-level labels across 19 classes, not pixel maps or urban expansion. This fixture set cannot establish broad geographic generalization.

## Routing and failure prevention

The 62-case baseline challenge contained one erroneous test expectation: general car counting is an explicitly labelled VQA estimate, not an unsupported route. Its original result is preserved and excluded from scored comparisons. Among the remaining 61 cases, baseline passed 55/61; the corrected router passed 61/61. Five unsupported/partial requests had dispatched and one valid road comparison was refused. Fixes cover unavailable physical variables, mixed water/vegetation requests, classifier location requests and natural road comparisons. Twelve additional hand-written paraphrases passed. These are bounded challenge sets, not population-level natural-language accuracy.

All 70 regression tests passed after adding six test methods. Existing fault-injection unit tests cover worker errors, unknown specialists and no VQA fallback; they are not live server-crash experiments. A missing water checkpoint was rejected. On one real optical crop, an 8-pixel artificial shift was diagnosed as approximately 8 pixels; low-texture content returned unverified. This does not establish optical-SAR registration detection, which remains metadata-based.

## Evidence and operational checks

Live temporal, water, land cover, NDVI, VQA and grounding runs completed. NDVI arrays matched independent float64 calculation to absolute tolerance 1e-12; threshold counts and affine grid area matched. Water mask counts and temporal change counts matched exported arrays. Land-cover ZIP integrity was checked, not independently re-inferred. VQA/grounding archives were checked for ZIP integrity and byte-exact original upload preservation.

After a controlled idle restart, known run JSON and ZIP returned HTTP 200, while the in-memory job-status endpoint returned 404. Persisted artifacts therefore survive at known IDs; a persistent job history/queue is not established. A forced mid-inference process kill and multi-user isolation test were not performed.

## Resource measurements and limits

Standalone CPU water evaluation: model-load 0.10 s, complete 105-chip/three-path pass 76.49 s, peak process RSS 878.3 MiB. Temporal: model-load 12.26 s, 100 pairs plus 10 controls 41.13 s, peak process RSS 2145.0 MiB. These are process high-water marks including libraries, not minimum deployment RAM. Runs used cached local files and shared the machine with other activity.

| Live workflow | Runs | Median upload-to-result seconds | Range |
|---|---:|---:|---:|
| VQA classification | 16 | 0.95 | 0.94–20.53 |
| Description | 12 | 0.98 | 0.95–4.32 |

These live distributions mix initial and subsequent runs; they are not a controlled cold/warm study. Grounding trace peak allocated GPU memory values: [2.678, 2.678, 2.678, 1.444]. GPU allocator peaks are not whole-device VRAM. No validated VQA peak RAM/VRAM, concurrent load capacity, financial savings or human time savings is claimed.

## Comparator reference

Public repository inspected at `e260c9f41eb327832325db5d7bb505b27f2b4e78`. Selected published artifacts are archived under comparator/. Their final grounding record reports 8 scenes/16 references and 18.75% accuracy at 0.5 IoU using highest-score selection; our proposal-recall diagnostic uses a different rule. Their temporal closeout reports blocked learned-model lanes alongside deterministic checks. Their separate land-cover complementarity artifact reports 3,000 validation samples at threshold 0.5, with joint micro-F1 73.41%. The inspected evaluation code explicitly restricts that run to validation. Our 12-fixture micro-F1 of 75% is not evidence of superiority: the samples and scope differ substantially. These are reported artifacts, not reproduced executions or a complete audit of their current product. No overall winner or numerical ranking is defensible from these differently constructed evaluations.

## Outstanding gates

- Full prescribed RSVQA/VRSBench scoring and CDVQA evaluation are not complete. The current road/building caption specialist does not establish general CDVQA coverage.
- Independent human description review, reference-label adjudication and broad grounding evaluation remain open.
- Broad multisensor/multiregion land-cover evaluation requires more than the current fixture set.
- Cartosat-2S/RISAT compatibility and quality remain untested without representative official products.
- Controlled cold/warm resource profiling, interruption/load tests and timed analyst study remain open.
- No new untouched final test remains claimed after using diagnostics to change routing. A separately frozen final acceptance set is still needed.

## Reproduction

Use the recorded WSL Python environment. Run benchmark.py water / temporal / land separately; manifests and raw JSONL rows identify exact cases. Scripts append results: use a fresh output directory for a new pass and preserve original evidence. live_vqa.py, live_more.py and live_gates.py exercise localhost:8767 and require the local services. Source paths and dataset paths are environment-specific. integrity.py recomputes exported measurements. Original baseline and post-fix source hashes are separate. No competitor code was executed.

## Sources

- [VRSBench official repository](https://github.com/lx709/VRSBench) and pinned dataset revision 6cee2968fd752a6d51c6cb2d18dded2bc0baa218. Annotation terms CC-BY-4.0; source-image commercial-use restrictions require review.
- [Sen1Floods11](https://github.com/cloudtostreet/Sen1Floods11).
- [LEVIR-MCI dataset](https://huggingface.co/datasets/lcybuaa/LEVIR-MCI), local archive hash in temporal-manifest.json.
- [CDVQA task paper](https://arxiv.org/abs/2112.06343): change-question answering is a distinct evaluation from segmentation.
- [Comparator at inspected revision](https://github.com/bishuk-dev/SIH-26167-SATQuery/tree/e260c9f41eb327832325db5d7bb505b27f2b4e78).
