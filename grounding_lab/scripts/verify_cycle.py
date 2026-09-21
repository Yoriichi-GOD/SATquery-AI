import requests,time,json,subprocess
from pathlib import Path
B='http://127.0.0.1:8765';R=Path('/mnt/c/Users/nrgen/.codex/scratch/SATquery AI/grounding_lab');E=R/'evidence/same-port-cycle';E.mkdir(exist_ok=True)
def gpu():
 return subprocess.check_output(['nvidia-smi','--query-gpu=memory.used,memory.total','--format=csv,noheader,nounits'],text=True).strip()
def wait(url):
 start=time.monotonic()
 while time.monotonic()-start<300:
  j=requests.get(url).json()
  if j['state'] in ['complete','error']:return j,round(time.monotonic()-start,3)
  time.sleep(.2)
 raise RuntimeError('timeout')
p=R/'samples/stadium.png'
a=requests.post(B+'/api/images',files={'file':(p.name,p.read_bytes())});a.raise_for_status();iid=a.json()['id']
rows=[]
for label in ['vqa-before','lab','vqa-after']:
 before=gpu();start=time.monotonic()
 if label=='lab':
  im=requests.post(B+'/grounding/api/images',files={'file':(p.name,p.read_bytes())}).json()
  q=requests.post(B+'/grounding/api/runs',json=dict(image_id=im['id'],category='stadium',mode='both'));q.raise_for_status()
  blocked=requests.post(B+'/api/analyze',data=dict(image_id=iid,question='Describe this image.'));assert blocked.status_code==409,blocked.text
  j,elapsed=wait(B+'/grounding/api/runs/'+q.json()['id'])
  assert requests.get(B+'/api/status').json()['state']=='idle'
 else:
  q=requests.post(B+'/api/analyze',data=dict(image_id=iid,question='Is there a stadium in this image?'));q.raise_for_status()
  if label=='vqa-before':
   im=requests.post(B+'/grounding/api/images',files={'file':(p.name,p.read_bytes())}).json()
   blocked=requests.post(B+'/grounding/api/runs',json=dict(image_id=im['id'],category='stadium'));assert blocked.status_code==409,blocked.text
  j,elapsed=wait(B+'/api/runs/'+q.json()['id'])
 assert j['state']=='complete',j
 (E/(label+'.json')).write_text(json.dumps(j,indent=2))
 row=dict(case=label,wall_seconds=round(time.monotonic()-start,3),gpu_before_MiB=before,gpu_after_MiB=gpu(),answer=j.get('answer'),objects=j.get('result',{}).get('objects'));rows.append(row);print(row,flush=True)
 (E/'summary.json').write_text(json.dumps(rows,indent=2))
