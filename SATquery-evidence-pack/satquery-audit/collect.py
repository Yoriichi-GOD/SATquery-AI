import json, csv, hashlib, re, sys
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8')
ROOT=Path(r'C:\Users\nrgen\.codex\scratch\SATquery AI')
OUT=Path(__file__).resolve().parent
metrics=[]; inventory=[]; errors=[]
def walk(x,path,source):
    if isinstance(x,dict):
        for k,v in x.items():
            p=path+'.'+k
            if isinstance(v,(float,int,str)) and not isinstance(v,bool) and re.search(r'seconds|latency|elapsed|peak|vram|ram_|memory|allocated|reserved|gpu_.*mib|parameters',k,re.I):
                metrics.append(dict(source=str(source),field=p,value=v))
            walk(v,p,source)
    elif isinstance(x,list):
        for i,v in enumerate(x):walk(v,f'{path}[{i}]',source)
for folder in ['results','paired_lab/evidence','grounding_lab/evidence','ppt_handoff/raw','demo run']:
    for p in sorted((ROOT/folder).rglob('*.json')):
        try:walk(json.loads(p.read_text(encoding='utf-8-sig')),'$',p)
        except Exception as e:errors.append([str(p),str(e)])
with (OUT/'recorded-measurements.csv').open('w',newline='',encoding='utf-8') as f:
    w=csv.DictWriter(f,fieldnames=['source','field','value']);w.writeheader();w.writerows(metrics)
for p in ROOT.rglob('*'):
    if not p.is_file() or any(v in p.parts for v in ['.venv','__pycache__','backups','demo-freeze-20260907','SATquery-evidence-pack','UI']):continue
    if p.suffix.lower() not in ['.py','.js','.html','.json','.jsonl','.txt','.ps1','.pt','.safetensors']:continue
    inventory.append(dict(path=str(p),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
(OUT/'source-evidence-inventory.json').write_text(json.dumps(inventory,indent=2),encoding='utf-8')
(OUT/'collection-notes.json').write_text(json.dumps({'metric_rows':len(metrics),'inventory_files':len(inventory),'parse_errors':errors,'scope':'Preserved scalar fields; NOT new benchmarks. Duplicated/historical/superseded evidence retained and identified by source. Numeric differences must not be treated as comparable timings without inspecting scope.'},indent=2),encoding='utf-8')
print('metric rows',len(metrics),'inventory files',len(inventory),'parse errors',len(errors))
for prefix in ['results/','paired_lab/evidence/resumed/live/','grounding_lab/evidence/same-port-cycle/']:
    rows=[m for m in metrics if prefix.replace('/',str(Path('/')) if False else '\\') in m['source'] and any(t in m['field'] for t in ['generation_seconds','peak_allocated_GiB','trace[0].seconds'])]
    print(prefix, json.dumps(rows[:10],ensure_ascii=True))
