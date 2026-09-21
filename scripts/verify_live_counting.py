import json,time,hashlib
from pathlib import Path
import requests
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/reliability-20260907/counting'
BASE='http://127.0.0.1:8765'
cases=json.loads((OUT/'development-cases.json').read_text())
rows=[]
for case in cases:
 source=Path(case['image'])
 response=requests.post(BASE+'/api/images',files={'file':(source.name,source.read_bytes(),'image/png')},timeout=30);response.raise_for_status();image=response.json()
 question='How many baseball fields are there in this image?'
 response=requests.post(BASE+'/api/analyze',data=dict(image_id=image['id'],question=question,mode='pilot_binary'),timeout=30)
 response.raise_for_status();rid=response.json()['id'];deadline=time.monotonic()+150
 while True:
  response=requests.get(BASE+f'/api/runs/{rid}',timeout=30);response.raise_for_status();run=response.json()
  if run['state'] in ('complete','error'):break
  if time.monotonic()>deadline:raise TimeoutError(rid)
  time.sleep(.3)
 assert run['state']=='complete',run
 assert run['routing']['rule']=='baseball_count' and run['mode']=='baseline' and run['requested_mode']=='pilot_binary'
 estimate=run['counting']
 row=dict(case=case,run=run,correct=estimate['count']==case['reference'] if case['reference'] is not None else None)
 rows.append(row)
 (OUT/'live-predictions.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
 print(case['id'],'reference',case['reference'],'count',estimate['count'],'withheld',estimate['withheld'],flush=True)
assert next(r for r in rows if r['case']['id']=='full')['run']['counting']['count']==4
assert next(r for r in rows if r['case']['id']=='blank')['run']['counting']['withheld']
known=[r for r in rows if r['case']['reference'] is not None]
answered=[r for r in known if not r['run']['counting']['withheld']]
summary=dict(cases=len(rows),known_reference_cases=len(known),answered=len(answered),correct=sum(r['correct'] for r in answered),
 withheld=sum(r['run']['counting']['withheld'] for r in known),
 partial_unscored=[dict(id=r['case']['id'],count=r['run']['counting']['count']) for r in rows if r['case']['reference'] is None],
 scope='Development smoke tests: one baseball scene with related transformations/crops, a uniform image and two negative scenes. Not independent-scene counting accuracy. Ambiguous partial crop is unscored. Agreement between mirrored views is correlated, not proof of correctness.')
(OUT/'live-summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
print(json.dumps(summary,indent=2),flush=True)
