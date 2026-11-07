from pathlib import Path
import json,re
from fastapi import FastAPI,HTTPException
from fastapi.responses import FileResponse, RedirectResponse
ROOT=Path(__file__).resolve().parents[1]
RUNS=ROOT/'artifacts/runs'
ALLOWED={'result.json','manifest.json','connectivity.json','sensitivity.json','graph.json','layers.geojson','exposure.csv','prediction.tif','report-en.html','report-ne.html','freeze.json','pre.png','post.png','topology-audit.json','debris-candidates.tif','debris-exposure.csv'}
app=FastAPI(title='SatQuery - Flood Impact',docs_url=None,redoc_url=None)
from .response_store import ResponseStore
from .response_api import router as response_router
app.include_router(response_router(ResponseStore(RUNS,ROOT/'.runtime/response')))
@app.get('/')
def home():return FileResponse(ROOT/'web/index.html')
@app.get('/api/health')
def health():return {'status':'ok','service':'satquery-flood-lab','real_event_complete':False}
@app.get('/api/runs')
def runs():
    items=[]
    for p in sorted(RUNS.glob('*/result.json')):
        if (p.parent/'freeze.json').exists():items.append(json.loads(p.read_text()))
    return items
@app.get('/runs/{run_id}/{name}')
def artifact(run_id:str,name:str):
    if not re.fullmatch(r'[A-Za-z0-9_-]+',run_id) or name not in ALLOWED:raise HTTPException(404)
    path=RUNS/run_id/name
    if not path.is_file():raise HTTPException(404)
    return FileResponse(path,filename=name if name.endswith(('.tif','.csv','.geojson')) else None)

# Independent UI compatibility routes; never forward requests to the original app.
from fastapi.staticfiles import StaticFiles
import xml.etree.ElementTree as ET
from collections import Counter
@app.get('/flood')
def flood_view(): return RedirectResponse('/')
@app.get('/api/status')
def workspace_status(): return {'state':'saved flood evidence and bounded automatic water/exposure runs available','lab_port':8770}
@app.get('/api/samples')
def samples(): return []
@app.get('/api/experimental-evidence')
def experimental_evidence():
    root=ET.parse(ROOT/'docs/test-results.xml').getroot()
    cases=root.findall('.//testcase');counts=Counter(c.attrib['classname'] for c in cases)
    failures=sum(c.find('failure') is not None for c in cases);errors=sum(c.find('error') is not None for c in cases);skipped=sum(c.find('skipped') is not None for c in cases)
    return {'tests':{'passed':len(cases)-failures-errors-skipped,'failures':failures,'errors':errors,'skipped':skipped,'suites':[{'name':k,'count':v} for k,v in sorted(counts.items())]},'runs':runs(),'benchmarks':json.loads((ROOT/'web/benchmark-data.json').read_text(encoding='utf-8-sig'))}
from pydantic import BaseModel,Field
from typing import Literal
import requests
from .copilot import frozen_result,render
class CopilotQuery(BaseModel):
    run_id:str=Field(pattern=r'^[A-Za-z0-9_-]+$',max_length=100)
    question:str=Field(min_length=1,max_length=1200)
    language:Literal['en','ne']='en'
    topic:Literal['auto','summary','water','buildings','roads','connectivity','limitations']='auto'
@app.post('/api/copilot')
def copilot(q:CopilotQuery):
    root=RUNS/q.run_id
    if not (root/'freeze.json').is_file():raise HTTPException(404,'Frozen run not found')
    try:result=frozen_result(root)
    except ValueError:raise HTTPException(409,'Evidence integrity check failed')
    route={'intent':q.topic,'method':'explicit topic selection','ai_used':False}
    if q.topic=='auto':
        if re.search(r'death|casualt|evacuat|confiden|accura|certain|validat|invent|ignore|मृत्यु|निश्चित|शुद्धता',q.question,re.I):
            route={'intent':'limitations','method':'unsupported-claim guardrail','ai_used':False}
        else:
            try:
                response=requests.post('http://127.0.0.1:8771/route',json={'question':q.question},timeout=90)
                response.raise_for_status();route=response.json();route['ai_used']=True
            except requests.RequestException:raise HTTPException(503,'Local AI unavailable. Select a topic to use evidence-backed answers.')
    answer=render(result,route['intent'],q.language);answer['routing']=route
    answer['routing_notice']='Topic selection can be wrong, especially in Nepali. Check or override it. Development routing test: 9/12 before guardrails; not an independent benchmark.'
    return answer
from .jobs import router as jobs_router
app.include_router(jobs_router)
@app.post('/api/{path:path}')
def disconnected_analysis(path:str):
    raise HTTPException(503,'Automatic area/date acquisition is not connected. Use Workspace for saved flood runs and Evidence for validation.')
app.mount('/assets',StaticFiles(directory=ROOT/'web'),name='assets')
app.mount('/art',StaticFiles(directory=ROOT/'web/art'),name='art')

