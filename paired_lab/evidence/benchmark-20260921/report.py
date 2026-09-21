from pathlib import Path
import json,csv,html,statistics,re,hashlib
O=Path(__file__).resolve().parent
def load(n):return json.loads((O/n).read_text(encoding='utf-8-sig'))
def lines(n):return [json.loads(x) for x in (O/n).read_text(encoding='utf-8-sig').splitlines()]
def pct(x):return f'{100*x:.2f}%'
w=load('water-summary.json');t=load('temporal-summary.json');land=load('land-summary.json');v=load('vqa-summary.json');ground=load('grounding-results.json');grefs=[x for r in ground for x in r['references']]
base=load('routing-baseline.json');post=load('routing-results.json');valid=lambda r:r['query']!='How many cars are there?'
before=[r for r in base['rows'] if valid(r)];after=[r for r in post['rows'] if valid(r)]
presence=lines('presence-rows.jsonl');fix=load('presence-postfix.json') if (O/'presence-postfix.json').exists() else [];fixmap={r['image_id']:r for r in fix}
def decision(answer):
 out=re.findall(r'\banswer is\s+(yes|no)\b',answer.lower());m=re.match(r'\s*(yes|no)\b',answer.lower())
 if m:out.append(m[1])
 return out[0] if out and len(set(out))==1 else None
presence_rows=[]
for r in presence:
 d=fixmap.get(r['image_id'],r);answer=d['run'].get('result',{}).get('answer','');pred=decision(answer);presence_rows.append({'image_id':r['image_id'],'reference':r['reference'],'prediction':pred,'correct':pred==r['reference'],'state':d['run']['state']})
ps={'n':len(presence_rows),'completed':sum(r['state']=='complete' for r in presence_rows),'correct':sum(r['correct'] for r in presence_rows),'abstain_or_unparsed':sum(r['prediction'] is None for r in presence_rows),'tp':sum(r['prediction']=='yes' and r['reference']=='yes' for r in presence_rows),'fp':sum(r['prediction']=='yes' and r['reference']=='no' for r in presence_rows),'fn':sum(r['prediction']!='yes' and r['reference']=='yes' for r in presence_rows),'rows':presence_rows,'scoring':'Decision extracted only from leading yes/no or explicit answer-is yes/no; inconsistent or absent decision unscored/incorrect. Exploratory scoring protocol; not published RSVQA exact-match protocol.'};(O/'presence-summary.json').write_text(json.dumps(ps,indent=2))
metrics=[]
for split in ['test','bolivia']:
 for mode in ['s1','s2','all']:
  r=w['groups'][split]['modalities'][mode]
  for metric in ['iou','f1','precision','recall']:metrics.append(['water',split,w['groups'][split]['n'],mode,metric,r[metric]])
for name,r in t['classes'].items():
 for metric in ['iou','f1']:metrics.append(['temporal','balanced 100-pair subset',100,name,metric,r[metric]])
for mode,r in land['modalities'].items():metrics.append(['land_cover','12 existing fixtures',12,mode,'micro_f1',r['f1']])
with (O/'metrics.csv').open('w',newline='') as f:
 wr=csv.writer(f);wr.writerow(['workflow','split','samples','path_or_class','metric','value_0_to_1']);wr.writerows(metrics)
reviews=[
('P1598_0050.png','Airport context mentioned; two aircraft and roundabout omitted. Calling trees green is not supported by the grayscale input.','Omission; unsupported colour'),
('P1390_0090.png','Aircraft presence captured; ground/runway context and layout largely omitted.','Sparse but core object supported'),
('P0110_0015.png','Model calls the long structure a ship; reference calls it a harbor. Visual inspection supports a long fixed structure but does not certify its identity.','Disputed object identity; human review needed'),
('P1377_0054.png','Houses and swimming pools captured; road, vehicles and vegetation not described.','Partial coverage'),
('10086_0000.png','Baseball field and surrounding grass/trees captured. Organized-game use and suburban/semi-rural context are inferred, not established.','Unsupported contextual claims'),
('08078_0000.png','Water and surrounding trees captured; dam feature omitted.','Major-feature omission'),
('P8656_0106.png','Building/roof captured; roads beside it are not clearly established in the crop.','Possible unsupported feature; review needed'),
('P2645_0012.png','Model describes railways, buildings and greenery. These match visible tracks better than the reference airport/ship description. Recreational-use inference remains unsupported.','Reference caption disputed; do not score by caption agreement alone'),
('06739_0000.png','Aircraft identified; two-plane count can include a partial aircraft at the right edge. Ground-service detail omitted.','Count sensitive to crop boundary; partial coverage'),
('P0217_0000.png','Two planes and grass/tarmac context captured; both aircraft are partially cropped.','Broadly supported description'),
('P1323_0020.png','River/bank context captured; bridges omitted and green colour cannot be established from grayscale.','Omission; unsupported colour'),
('08284_0000.png','Buildings/trees captured; prominent smoke plume and industrial detail omitted.','Major-feature omission')]
review='# Description review — exploratory, not a certified accuracy score\n\n12 frozen VRSBench evaluation images. Review by the coding assistant using images, model outputs and official reference captions; no independent human adjudicator. These cases are now development evidence. Do not report a human-validated caption accuracy percentage.\n\n| Image | Finding | Category |\n|---|---|---|\n'+'\n'.join('| '+ ' | '.join(r)+' |' for r in reviews)
(O/'DESCRIPTION_REVIEW.md').write_text(review)
events=[k for k in w['groups'] if k not in ['test','bolivia']]
wr='\n'.join(f"| {split} | {w['groups'][split]['n']} | "+' | '.join(pct(w['groups'][split]['modalities'][m]['iou']) for m in ['s1','s2','all'])+' |' for split in ['test','bolivia'])
eventrows='\n'.join(f"| {k} | {w['groups'][k]['n']} | "+' | '.join(pct(w['groups'][k]['modalities'][m]['iou']) for m in ['s1','s2','all'])+' |' for k in events)
lat=[]
for name,file in [('VQA classification','vqa-rows.jsonl'),('Description','description-rows.jsonl')]:
 rr=[r['run'] for r in lines(file) if r['run']['state']=='complete'];seconds=[r['end_to_end_seconds'] for r in rr];lat.append(f"| {name} | {len(rr)} | {statistics.median(seconds):.2f} | {min(seconds):.2f}–{max(seconds):.2f} |")
grt=[r['run']['result']['trace'][-1].get('peak_gpu_GiB') for r in ground];grt=[x for x in grt if isinstance(x,(int,float))]
report=f'''# SatQuery AI — benchmark findings, 21 September 2026

This is a bounded evaluation pass of the current local implementation, not ISRO certification, a full prescribed-benchmark run or proof of superiority to another team. Results, manifests, scripts and raw outputs are supplied alongside this report. Flood forecasting is removed from product scope.

## Results worth presenting

| Evidence | Measured result | Necessary qualification |
|---|---|---|
| Temporal road change | {pct(t['classes']['road']['iou'])} IoU; {pct(t['classes']['road']['f1'])} F1 | 100 LEVIR-MCI test pairs, 50 changed/50 unchanged; checkpoint inherited |
| Temporal building change | {pct(t['classes']['building']['iou'])} IoU; {pct(t['classes']['building']['f1'])} F1 | Same fixed subset; not CDVQA |
| Water segmentation | {pct(w['groups']['test']['modalities']['all']['iou'])} joint IoU | 90 Sen1Floods11 test chips; previously evaluated split |
| Geographic water holdout replay | {pct(w['groups']['bolivia']['modalities']['all']['iou'])} joint IoU | 15 Bolivia chips; previously evaluated holdout |
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
{wr}

Optical alone exceeds joint on the 90-chip test aggregate. Joint is slightly higher on Bolivia. Do not claim universal fusion superiority. Water includes permanent water; these are not verified flood-only masks. Scores use common finite input pixels and nonnegative reference labels. Confusion counts, F1, precision, recall and path disagreement are saved per chip. Metrics are pooled over pixels; pixels are not independent samples.

| Event | Chips | SAR IoU | Optical IoU | Joint IoU |
|---|---:|---:|---:|---:|
{eventrows}

## Temporal: segmentation and captions are separate

Road IoU {pct(t['classes']['road']['iou'])}; building IoU {pct(t['classes']['building']['iou'])}. Label encoding was checked as 0 unchanged / 128 road / 255 building. Published test references and raw model captions are retained in temporal-rows.jsonl. No caption factuality percentage is assigned.

Across 50 unchanged reference pairs, {t['unchanged_false_positive_pixels']:,} of {t['unchanged_total_pixels']:,} pixels were predicted as changed ({100*t['unchanged_false_positive_pixels']/t['unchanged_total_pixels']:.4f}%). This pixel rate can coexist with scene-level errors; it is not a scene accuracy percentage. Ten additional identical/brightness controls predicted zero changed pixels. Construction versus demolition and CDVQA question answering are not established by these masks.

## Single-image findings

Rural/urban: {v['exact_correct']}/{v['n']} correct on the fresh availability-limited subset, using the current routed adapter. This small, imbalanced result is not a general VQA accuracy score.

Presence: the baseline completed 9/16 and incorrectly refused seven questions containing the noun “area”. The guard was fixed without enabling numerical area estimates. Post-fix decision extraction gives {ps['correct']}/{ps['n']} correct, {ps['completed']}/{ps['n']} completed and {ps['abstain_or_unparsed']} unparsed/abstained. This exploratory extraction ignores added prose and is not comparable to published strict exact-match scores; prose still includes unsupported interpretations. These 16 questions reuse the classification images and must not be counted as 16 additional scenes.

Descriptions: all 12 live runs completed. Several missed aircraft, bridges, a dam or a smoke plume, and some added unsupported colour/use claims. DESCRIPTION_REVIEW.md records each finding. One reference caption appears inconsistent with the visible scene. No independent human adjudication, validated caption accuracy, or successful comprehensive-description fix is claimed.

Grounding: {sum(r['hit_at_0_5'] for r in grefs)}/{len(grefs)} aircraft reference boxes had at least one proposal overlapping at IoU >=0.5 across {len(ground)} images. This is **oracle proposal recall** on a selected category, not referring-expression accuracy, detector precision, or mask IoU. It is not comparable to the competitor's highest-score referring-box metric. No segmentation mask ground truth was available. Grounding remains experimental.

## Land-cover classification

Micro-F1 over 12 existing BENv2 fixtures: SAR {pct(land['modalities']['s1']['f1'])}, optical {pct(land['modalities']['s2']['f1'])}, joint {pct(land['modalities']['all']['f1'])}. These are scene-level labels across 19 classes, not pixel maps or urban expansion. This fixture set cannot establish broad geographic generalization.

## Routing and failure prevention

The 62-case baseline challenge contained one erroneous test expectation: general car counting is an explicitly labelled VQA estimate, not an unsupported route. Its original result is preserved and excluded from scored comparisons. Among the remaining 61 cases, baseline passed {sum(r['correct'] for r in before)}/61; the corrected router passed {sum(r['correct'] for r in after)}/61. Five unsupported/partial requests had dispatched and one valid road comparison was refused. Fixes cover unavailable physical variables, mixed water/vegetation requests, classifier location requests and natural road comparisons. Twelve additional hand-written paraphrases passed. These are bounded challenge sets, not population-level natural-language accuracy.

All 70 regression tests passed after adding six test methods. Existing fault-injection unit tests cover worker errors, unknown specialists and no VQA fallback; they are not live server-crash experiments. A missing water checkpoint was rejected. On one real optical crop, an 8-pixel artificial shift was diagnosed as approximately 8 pixels; low-texture content returned unverified. This does not establish optical-SAR registration detection, which remains metadata-based.

## Evidence and operational checks

Live temporal, water, land cover, NDVI, VQA and grounding runs completed. NDVI arrays matched independent float64 calculation to absolute tolerance 1e-12; threshold counts and affine grid area matched. Water mask counts and temporal change counts matched exported arrays. Land-cover ZIP integrity was checked, not independently re-inferred. VQA/grounding archives were checked for ZIP integrity and byte-exact original upload preservation.

After a controlled idle restart, known run JSON and ZIP returned HTTP 200, while the in-memory job-status endpoint returned 404. Persisted artifacts therefore survive at known IDs; a persistent job history/queue is not established. A forced mid-inference process kill and multi-user isolation test were not performed.

## Resource measurements and limits

Standalone CPU water evaluation: model-load {w['load_seconds']:.2f} s, complete 105-chip/three-path pass {w['elapsed_seconds']:.2f} s, peak process RSS {w['peak_process_rss_MiB']:.1f} MiB. Temporal: model-load {t['load_seconds']:.2f} s, 100 pairs plus 10 controls {t['elapsed_seconds']:.2f} s, peak process RSS {t['peak_process_rss_MiB']:.1f} MiB. These are process high-water marks including libraries, not minimum deployment RAM. Runs used cached local files and shared the machine with other activity.

| Live workflow | Runs | Median upload-to-result seconds | Range |
|---|---:|---:|---:|
{chr(10).join(lat)}

These live distributions mix initial and subsequent runs; they are not a controlled cold/warm study. Grounding trace peak allocated GPU memory values: {grt}. GPU allocator peaks are not whole-device VRAM. No validated VQA peak RAM/VRAM, concurrent load capacity, financial savings or human time savings is claimed.

## Comparator reference

Public repository inspected at `{load('competitor-tree.json')['revision']}`. Selected published artifacts are archived under comparator/. Their final grounding record reports 8 scenes/16 references and 18.75% accuracy at 0.5 IoU using highest-score selection; our proposal-recall diagnostic uses a different rule. Their temporal closeout reports blocked learned-model lanes alongside deterministic checks. Their separate land-cover complementarity artifact reports 3,000 validation samples at threshold 0.5, with joint micro-F1 73.41%. The inspected evaluation code explicitly restricts that run to validation. Our 12-fixture micro-F1 of 75% is not evidence of superiority: the samples and scope differ substantially. These are reported artifacts, not reproduced executions or a complete audit of their current product. No overall winner or numerical ranking is defensible from these differently constructed evaluations.

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
- [Comparator at inspected revision](https://github.com/bishuk-dev/SIH-26167-SATQuery/tree/{load('competitor-tree.json')['revision']}).
'''
(O/'BENCHMARK_REPORT.md').write_text(report,encoding='utf-8')
brief=f'''# PPT-ready findings — use with the scope footnotes

## Primary evidence slide

**Query-driven analysis with inspectable spatial evidence**

- Road change: **{pct(t['classes']['road']['iou'])} IoU**
- Building change: **{pct(t['classes']['building']['iou'])} IoU**
- Water mapping: **{pct(w['groups']['test']['modalities']['all']['iou'])} joint IoU**
- Exported NDVI, water and temporal measurements independently recomputed.

Footnote: Temporal: fixed 100-pair LEVIR-MCI subset, 50 changed/50 unchanged. Water: 90-chip Sen1Floods11 test replay. Inherited temporal checkpoint; locally trained water model. No ISRO/SAC sensor validation claim.

## Verification slide / backup

- 70 software regression tests passed.
- 61/61 valid routing development challenges passed after fixes; 12 additional paraphrases passed.
- 10 identical/brightness controls produced zero change pixels (five base scenes).
- Original inputs and downloadable evidence retained; known artifact URLs remained accessible after restart.

Footnote: Software tests include mocks; controls and routing challenges are bounded development evidence. Optical-only water IoU is 83.90% on the same test split, versus 82.64% joint; do not claim universal fusion superiority.

## Keep out of headline claims

No overall SatQuery accuracy, “beats competitors”, “ISRO-ready”, flood prediction, guaranteed cost/time savings, validated caption accuracy or general urban-expansion claim. Keep detailed failure analysis in the technical report/backup slides; retain material metric footnotes on the main slide.

Source tables: metrics.csv. Full methodology and unresolved gates: BENCHMARK_REPORT.md.
'''
(O/'PPT_FINDINGS.md').write_text(brief,encoding='utf-8')
# Standalone exportable chart; fixed 0-100 scale, labelled denominator and task.
bars=[('Road change',100*t['classes']['road']['iou']),('Building change',100*t['classes']['building']['iou']),('Water / SAR',100*w['groups']['test']['modalities']['s1']['iou']),('Water / optical',100*w['groups']['test']['modalities']['s2']['iou']),('Water / joint',100*w['groups']['test']['modalities']['all']['iou'])]
svg=['<svg xmlns="http://www.w3.org/2000/svg" width="1100" height="530" viewBox="0 0 1100 530"><rect width="1100" height="530" fill="#fcfaf5"/><g font-family="Arial" fill="#192c36"><text x="40" y="50" font-size="26">Measured segmentation quality · IoU (%)</text>']
for i,(label,value) in enumerate(bars):
 y=95+i*65;svg.append(f'<text x="40" y="{y+25}" font-size="20">{label}</text><rect x="260" y="{y}" width="650" height="38" rx="4" fill="#e6e6df"/><rect x="260" y="{y}" width="{6.5*value}" height="38" rx="4" fill="#216b72"/><text x="930" y="{y+26}" font-size="20">{value:.2f}</text>')
svg.append('<text x="40" y="465" font-size="16">Temporal: 100 LEVIR-MCI pairs. Water: 90 Sen1Floods11 test chips.</text><text x="40" y="494" font-size="16">Different tasks shown separately; no combined accuracy. No ISRO/SAC validation.</text></g></svg>');(O/'segmentation-results.svg').write_text(''.join(svg))
page='<!doctype html><meta charset="utf-8"><title>SatQuery benchmark report</title><style>body{max-width:1000px;margin:50px auto;padding:0 25px;background:#fcfaf5;color:#192c36;font:16px/1.65 system-ui}pre{white-space:pre-wrap;font:inherit}img{width:100%}a{color:#216b72}</style><h1>SatQuery AI — measured evidence</h1><img src="segmentation-results.svg" alt="Task-specific IoU results"><p><a href="PPT_FINDINGS.md">PPT findings</a> · <a href="metrics.csv">Metric table</a> · <a href="DESCRIPTION_REVIEW.md">Description review</a></p><pre>'+html.escape(report)+'</pre>'
(O/'REPORT.html').write_text(page,encoding='utf-8')
print('Report, PPT findings, CSV and SVG created.')
