import ast,hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'tests'))
from routing import route
from test_routing import CASES
from test_baseball_counting import SUPPORTED,UNSUPPORTED
OUT=ROOT/'results/reliability-20260907'
ndvi=json.loads((OUT/'ndvi-independent-summary.json').read_text())
adapter=json.loads((OUT/'vqa/existing-adapter-fresh-summary.json').read_text())
count=json.loads((OUT/'counting/live-summary.json').read_text())
live=[json.loads(line) for line in (OUT/'vqa/live-validation-v2.jsonl').read_text().splitlines()]
routing=[dict(question=q,expected=expect,actual=route(q,ndvi_supported=True)['tool']) for q,expect in CASES]
routing += [dict(question=q,expected='baseball_count',actual=route(q)['rule']) for q in SUPPORTED]
routing += [dict(question=q,expected='refuse',actual=route(q)['tool']) for q in UNSUPPORTED]
assert all(r['actual']==r['expected'] for r in routing)
(OUT/'routing-regression.json').write_text(json.dumps(dict(version='rules-v2',total=len(routing),passed=len(routing),scope='58 developer-defined regression cases; not held-out natural-language routing accuracy.',cases=routing),indent=2),encoding='utf-8')
names={'dehradun':'Dehradun','assam-monsoon':'Assam monsoon','bengaluru-lake-city':'Bengaluru','jaisalmer-arid':'Jaisalmer','punjab-farmland':'Punjab','sundarbans-coast':'Sundarbans'}
scenes=[dict(name=names[r['scene']],valid_pixels=r['valid_pixels'],percent=r['percent_of_valid'],hectares=r['selected_hectares']) for r in ndvi['cases'] if r['threshold']==.5]
report=dict(updated='2026-09-07',metrics=[
 dict(label='NDVI numerical checks',value=f'{ndvi["passed"]}/{ndvi["total"]}',note='Six scenes × three thresholds; independent decoder and scalar calculation.'),
 dict(label='Fresh adapter diagnostic',value=f'{adapter["raw_exact_correct"]}/{adapter["total"]}',note='12/12 rural/urban; 7/12 presence. Small custom subset, not broad VQA accuracy.'),
 dict(label='Routing regression',value=f'{len(routing)}/{len(routing)}',note='Defined routing cases, including baseball counting and compound-request refusals.')],
 notes=[
 'Baseball/softball counting: full sample = 4. Seven answered reference cases were correct; a blank image and an ambiguous partial crop were withheld. Related crops/transforms share one baseball scene: this is a development smoke test, not independent-scene accuracy.',
 'Final VQA: all 11 live requests completed. Six fresh descriptions returned bounded observations; the two known overclaim regressions were suppressed. Qualitative review does not establish complete description accuracy.',
 'Known limitation retained: in a negative river-presence check, Original answered No while the yes/no adapter answered Yes. The adapter still makes false-positive presence errors.',
 'The prompt-only candidate and direct-answer decoding probe did not resolve speculative descriptions and were not deployed. Current safeguards preserve raw output and omit unsupported claims; they are not a visual verifier.',
 'NDVI agreement verifies arithmetic, masks, counts, denominators and projected area. It is not field validation of vegetation cover or cloud classification.'],
 ndvi_scenes=scenes,counting=count,adapter=adapter,final_vqa=dict(total=len(live),completed=sum(r['run']['state']=='complete' for r in live),fresh_descriptions=6,known_regression_cases=2),
 regression_tests=dict(passed=30,total=30,scope='Python scientific, routing, dispatch, answer and counting-parser tests'),evidence=[])
paths=['ndvi-independent-summary.json','before-fix-ndvi-independent-summary.json','routing-regression.json',
 'vqa/paired-summary.json','vqa/paired-predictions.jsonl','vqa/frozen-cases.json',
 'vqa/direct-answer-development-probe.jsonl','vqa/existing-adapter-fresh-summary.json',
 'vqa/existing-adapter-fresh-predictions.jsonl','vqa/live-validation.jsonl','vqa/live-validation-v2.jsonl',
 'vqa/fresh-review-observations.json','vqa/live-refusals-v2.json','counting/development-predictions.json',
 'counting/live-predictions.json','counting/live-summary.json']
for relative in paths:
 path=OUT/relative
 report['evidence'].append(dict(path=str(path.relative_to(ROOT)),sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
(OUT/'public-summary.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
table='\n'.join(f'| {s["name"]} | {s["valid_pixels"]:,} | {s["percent"]:.2f}% | {s["hectares"]:.2f} |' for s in scenes)
text=f'''# SATquery combined verification — 7 September 2026

## Implemented and checked

- NDVI now uses float64 arithmetic, threshold comparison and export. Real multi-scene trials exposed one-to-five-pixel threshold-rounding differences; all 18 independent comparisons now agree exactly on selected pixels and masks.
- VQA retains raw output and records its answer policy. Bounded observation clauses are preserved; speculative explanations and ambiguous final labels are withheld. No new fine-tuning or model download was performed during this reliability pass.
- Baseball/softball diamond questions now route to a bounded two-view VQA count. The original model is used automatically even when a binary adapter was selected. Low-detail images, unparsable counts and original/mirrored disagreement are withheld. Other object counting remains unavailable. Grounding is outside scope.
- Evaluation data scrolls independently beside the fixed user-supplied astronaut artwork on desktop. Mobile prioritizes the data. The new overview presents separate metrics and validates the hashes of its source evidence.

## Combined results (do not pool these into one accuracy score)

| Evaluation | Result | Interpretation |
|---|---|---|
| Existing matched development comparison | Original 23/60 (38.3%); adapter 47/60 (78.3%) | Historical development data; includes formatting effects. No new training today. |
| Earlier original-only diagnostic | 24/60 (40.0%) | Historical separate 60-image run; not comparable to the 20-image development score. |
| Fresh existing-adapter diagnostic | 19/24 (79.2%) | 12/12 rural/urban; 7/12 presence. Test images excluded from adapter train/dev and previous diagnostic images; same official test source scene as earlier diagnostic. |
| NDVI live + independent numerical comparison | 18/18 | Six scenes × thresholds 0.30, 0.50, 0.70; all six downloadable artifact endpoints checked per run. |
| Routing regression | 58/58 | 37 existing cases plus 21 baseball/compound cases. Developer-defined, not held-out routing accuracy. |
| Final live VQA | 11/11 completed | Six fresh descriptions, two known overclaim regressions and three adapter-switching/presence checks. Completion is not semantic accuracy. |
| Counting live smoke test | 7/7 answered reference cases correct; 2 cases withheld | One baseball source scene and related crops/transforms plus negative controls. Blank image withheld; partial crop unscored and withheld. |
| Python regression suite | 30/30 | Scientific, dispatch, routing, answer handling and count parsing. |

## NDVI scene results at threshold 0.50

Percentages use valid pixels as the denominator. Area is projected grid area.

| Scene | Valid pixels | NDVI ≥ 0.50 | Selected hectares |
|---|---:|---:|---:|
{table}

Source imagery: Sentinel-2 Collection 1 Level-2A from Element 84 Earth Search / AWS. Red, green, blue, NIR and SCL identities are retained. COG headers and catalog scale/offset matched before conversion, applied exactly once. Raw DN windows and manifests are preserved for the five new scenes. SCL classes 4/5/6/7 are retained. Independent validation uses tifffile and scalar Python float64 rather than the application analytical functions.

## VQA experiments and retained failures

The paired prompt trial froze 24 QA cases plus 10 descriptions. Both original and evidence-limited prompts scored 0/24 under strict whole-output label matching because they produced narratives. This is a formatting result, **not zero visual accuracy**. Extracting unambiguous original final labels yielded 14/24 correct with one withheld answer. The pilot adapter independently produced 19/24 exact labels on those same cases, but used its deployment prompt and lower token budget, so this is not a controlled adapter-only ablation.

The prompt-only candidate continued to claim road condition, traffic, season and vegetation health. A separate assistant-prefill probe still speculated and sometimes repeated feature lists. Neither decoding change was deployed.

The first conservative answer policy withheld four of six fresh descriptions. The final policy preserves an existing observation clause when a following relative clause speculates, so all six now produce short observations. These cases became development cases after inspection; do not call the revised policy a new held-out success. Descriptions can omit important features, and an incorrect object label can still survive these rules.

The negative river-presence live check remains a failure for the yes/no adapter: Original answered No; pilot answered Yes. No postprocessor was used to replace that wrong answer with an expected label. The presence diagnostic also contains five false-positive errors among six negative reference cases. Published labels can be noisy, but this is an unresolved reliability issue.

## Baseball counting scope

Ask **“How many baseball fields are there in this image?”** after loading the built-in sample. The live result is **4 identifiable baseball/softball diamonds**. The full image is analyzed regardless of viewer zoom. Both single-field crops return 1; farmland and river controls return 0. Original/mirrored agreement is a consistency check, not calibrated confidence or independent confirmation. Counting does not produce object boxes or geographic locations.

The one-view exploratory model hallucinated 3 fields on a uniform image. The deployed detail check now withholds it. The ambiguous partial crop produced disagreement and is also withheld. Further independent high-resolution scenes are needed before claiming general counting accuracy.

## Preserved evidence

Historical freezes, ZIPs, training records and original verification reports remain unchanged. New raw trials are under this folder, including failures and both answer-policy versions. `public-summary.json` lists evidence hashes. Source backups are in `backups/reliability-20260907-before` and `backups/final-verification-layout-20260907`.
'''
(OUT/'COMBINED_RESULTS.md').write_text(text,encoding='utf-8')
with zipfile.ZipFile(OUT/'NDVI_TRIAL_SAMPLES.zip','w',zipfile.ZIP_DEFLATED) as archive:
 archive.write('/root/satquery/scenes/dehradun-sentinel2-20211125.tif','dehradun.tif')
 for p in (OUT/'scenes').glob('*/manifest.json'):
  name=p.parent.name;archive.write(p.parent/f'{name}.tif',f'{name}.tif');archive.write(p,f'provenance/{name}.json')
 archive.write(OUT/'COMBINED_RESULTS.md','COMBINED_RESULTS.md')
print(json.dumps(dict(routing_cases=len(routing),ndvi=ndvi['passed'],adapter=adapter['raw_exact_correct'],counting=count,report=str(OUT/'COMBINED_RESULTS.md')),indent=2))
