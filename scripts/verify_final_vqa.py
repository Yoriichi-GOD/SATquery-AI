import hashlib
import json
from pathlib import Path
import time
import requests

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/reliability-20260907/vqa'
BASE='http://127.0.0.1:8765'
cases=json.loads((OUT/'fresh-review-cases.json').read_text())
cases += [dict(id='regression-dehradun',image=str(OUT/'dehradun.png'),question='Describe the major visible features briefly.'),
          dict(id='regression-sundarbans',image=str(OUT.parent/'scenes/sundarbans-coast/rgb.png'),question='Describe the major visible features briefly.'),
          dict(id='pilot-rural-live',image=str(OUT/'image-265.png'),question='Is this image rural or urban?',mode='pilot_rural'),
          dict(id='original-after-pilot',image=str(OUT/'fresh-245.png'),question='Is there a river visible in this image?'),
          dict(id='pilot-binary-live',image=str(OUT/'fresh-245.png'),question='Is there a river visible in this image?',mode='pilot_binary')]
path=OUT/'live-validation-v2.jsonl'
assert not path.exists(), 'Preserve previous live validation'
for case in cases:
    source=Path(case['image'])
    response=requests.post(BASE+'/api/images',files={'file':(source.name,source.read_bytes(),'image/png')},timeout=30)
    response.raise_for_status()
    image=response.json()
    response=requests.post(BASE+'/api/analyze',data=dict(image_id=image['id'],question=case['question'],mode=case.get('mode','baseline')),timeout=30)
    response.raise_for_status()
    rid=response.json()['id']
    deadline=time.monotonic()+240
    while True:
        response=requests.get(BASE+f'/api/runs/{rid}',timeout=30)
        response.raise_for_status()
        run=response.json()
        if run['state'] in ('complete','error'):
            break
        if time.monotonic()>deadline:raise TimeoutError(rid)
        time.sleep(.5)
    assert run['state']=='complete',run
    assert run['answer_policy']=='bounded-answer-v2'
    assert 'raw_answer' in run and 'answer_validation' in run
    if case['id']=='regression-dehradun':
        assert all(word not in run['answer'].lower() for word in ['congestion','accidents','good condition'])
    if case['id']=='regression-sundarbans':
        assert all(word not in run['answer'].lower() for word in ['healthy','snow','season'])
    saved=Path('/root/satquery/app-data/runs')/f'{rid}.json'
    for _ in range(20):
        if saved.exists():break
        time.sleep(.1)
    disk=json.loads(saved.read_text())
    assert disk['raw_answer']==run['raw_answer'] and disk['answer']==run['answer']
    row=dict(case=case,run=run,saved_run_sha256=hashlib.sha256(saved.read_bytes()).hexdigest())
    with path.open('a',encoding='utf-8') as handle:handle.write(json.dumps(row)+'\n')
    print(case['id'],run['answer'],flush=True)

refusals=[]
for question in ['Compare this to last year','Count the buildings','Locate the buildings','Analyze SAR backscatter','What is vegetation health?','How green is this?','Describe vegetation and tell me its percentage','Calculate NDVI']:
    response=requests.post(BASE+'/api/analyze',data=dict(image_id=image['id'],question=question),timeout=30)
    assert response.status_code==422,(question,response.text)
    refusals.append(dict(question=question,status=response.status_code,detail=response.json()))
(OUT/'live-refusals-v2.json').write_text(json.dumps(refusals,indent=2),encoding='utf-8')
print('Live VQA completed; all eight refusal cases passed',flush=True)
