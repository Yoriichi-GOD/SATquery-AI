import subprocess,time,json,sys,requests
from pathlib import Path
root=Path('/mnt/c/Users/nrgen/.codex/scratch/SATquery AI');out=root/'paired_lab/evidence/compliance-20260926';base='http://127.0.0.1:18765'
with (out/'cartosat-vqa.log').open('w') as log:
 p=subprocess.Popen([sys.executable,'-m','uvicorn','server:app','--app-dir',str(root),'--host','127.0.0.1','--port','18765','--no-access-log'],stdout=log,stderr=subprocess.STDOUT)
 try:
  for _ in range(60):
   try:
    if requests.get(base+'/api/status',timeout=1).ok:break
   except requests.RequestException:pass
   time.sleep(.5)
  with (out/'cartosat-labelled.tif').open('rb') as f:
   r=requests.post(base+'/api/images',files={'file':('cartosat-labelled.tif',f)},timeout=30);r.raise_for_status();upload=r.json()
  r=requests.post(base+'/api/analyze',data={'image_id':upload['id'],'question':'Describe this image','mode':'baseline'},timeout=30);r.raise_for_status();rid=r.json()['id']
  for _ in range(600):
   r=requests.get(base+'/api/runs/'+rid,timeout=10);r.raise_for_status();result=r.json()
   if result['state'] in ['complete','error']:break
   time.sleep(1)
  (out/'cartosat-vqa.json').write_text(json.dumps(result,indent=2))
  print(json.dumps(result,indent=2),flush=True)
  assert result['state']=='complete'
 finally:
  p.terminate()
  try:p.wait(timeout=15)
  except subprocess.TimeoutExpired:p.kill();p.wait()
