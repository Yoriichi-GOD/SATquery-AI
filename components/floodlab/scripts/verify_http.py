import urllib.request,json,hashlib
from pathlib import Path
b=Path(__file__).resolve().parents[1];base='http://localhost:8770'; results=[]
for port in (8767,8770):
 with urllib.request.urlopen(f'http://localhost:{port}',timeout=10) as r:results.append({'port':port,'status':r.status})
with urllib.request.urlopen(base+'/api/runs') as r:runs=json.load(r)
for item in runs:
 root=b/'artifacts/runs'/item['run_id'];freeze=json.loads((root/'freeze.json').read_text())
 for name,sha in freeze['files'].items():
  with urllib.request.urlopen(base+'/runs/'+item['run_id']+'/'+name) as r:body=r.read()
  assert hashlib.sha256(body).hexdigest()==sha,name
 results.append({'run':item['run_id'],'verified_downloads':len(freeze['files'])})
print(json.dumps(results,indent=2));(b/'docs/http-verification.json').write_text(json.dumps(results,indent=2))
