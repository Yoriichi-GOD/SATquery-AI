from pathlib import Path
import shutil,requests,json,time
R=Path('/mnt/c/Users/nrgen/.codex/scratch/SATquery AI');L=R/'grounding_lab';E=L/'evidence/additional';E.mkdir(exist_ok=True)
cases=[dict(name='mountain-car',source='/root/satquery/app-data/images/037f45c84eb34a89aec4cd5e9e355032.png',category='car',expected=1),dict(name='river-negative',source=str(R/'results/reliability-20260907/counting/river.png'),category='stadium',expected=0),dict(name='blank-negative',source=str(R/'results/reliability-20260907/counting/blank.png'),category='car',expected=0)]
(E/'cases-before-predictions.json').write_text(json.dumps(cases,indent=2));rows=[];B='http://127.0.0.1:8766'
for c in cases:
 p=Path(c['source']);shutil.copy2(p,L/'samples'/(c['name']+'.png'))
 r=requests.post(B+'/api/images',files={'file':(p.name,p.read_bytes())});r.raise_for_status();im=r.json()
 r=requests.post(B+'/api/runs',json=dict(image_id=im['id'],category=c['category'],mode='both'));r.raise_for_status();rid=r.json()['id'];start=time.monotonic()
 while time.monotonic()-start<240:
  j=requests.get(B+'/api/runs/'+rid).json()
  if j['state']!='running':break
  time.sleep(.3)
 assert j['state']=='complete',j
 rows.append(dict(case=c,run=j,count_matches=j['result']['objects']==c['expected']));(E/'predictions.json').write_text(json.dumps(rows,indent=2));print(c['name'],j['result']['objects'],'expected',c['expected'],j['result']['seconds'],flush=True)
