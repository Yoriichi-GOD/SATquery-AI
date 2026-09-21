import sys,json,uuid,time,threading,zipfile,traceback,shutil
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from fastapi import FastAPI,UploadFile,File,Form,HTTPException,Request
from fastapi.responses import FileResponse,JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.trustedhost import TrustedHostMiddleware
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
import engine
import controller,single_bridge,mci,flood
import rasterio
from inputs import inspect,route,validate
import numpy as np
DATA=engine.DATA/'app';DATA.mkdir(exist_ok=True)
UPLOADS=DATA/'uploads';UPLOADS.mkdir(exist_ok=True)
RUNS=DATA/'runs';RUNS.mkdir(exist_ok=True)
app=FastAPI(title='SATquery Paired Lab',docs_url=None,redoc_url=None)
app.add_middleware(TrustedHostMiddleware,allowed_hosts=['localhost','127.0.0.1','testserver'])
executor=ThreadPoolExecutor(max_workers=1);lock=threading.Lock();busy=False;jobs={};images={}
catalog=json.loads((ROOT/'samples/catalog.json').read_text());samples={s['id']:s for s in catalog}

@app.middleware('http')
async def local_only(request:Request,call_next):
    if request.headers.get('origin') not in [None,'http://localhost:8767','http://127.0.0.1:8767']:
        return JSONResponse({'detail':'Use the local paired lab.'},status_code=403)
    try:size=int(request.headers.get('content-length','0'))
    except ValueError:return JSONResponse({'detail':'Invalid size.'},status_code=400)
    if size>24*1024*1024:return JSONResponse({'detail':'Upload limit is 20 MB.'},status_code=413)
    response=await call_next(request);response.headers['X-Content-Type-Options']='nosniff';return response

@app.get('/')
def home():return FileResponse(ROOT/'web/index.html')
@app.get('/api/status')
def status():return {'state':'processing' if busy else 'ready','device':'Paired CPU · single-image demo GPU','demo_port':8765,'lab_port':8767,'controller':controller.VERSION}
@app.get('/api/samples')
def list_samples():return catalog
@app.get('/api/resumed-evaluation')
def resumed_evaluation():
    water=ROOT/'evidence/resumed/water-evaluation.json';temporal=ROOT/'evidence/resumed/mci/evaluation.json'
    return {'water':json.loads(water.read_text()) if water.exists() else None,'temporal':json.loads(temporal.read_text()) if temporal.exists() else None}

@app.get('/api/evaluation')
def evaluation():return json.loads((ROOT/'evidence/selected-trials/summary.json').read_text())
@app.get('/api/sample/{sid}/{filename}')
def sample_file(sid:str,filename:str):
    if sid not in samples or filename not in samples[sid]['files']+['manifest.json']:raise HTTPException(404)
    return FileResponse(ROOT/'samples'/sid/filename)

@app.get('/api/preview/{sid}/{filename}')
def sample_preview(sid:str,filename:str):
    if sid not in samples or filename not in ['before.png','after.png','optical.png','sar.png']:raise HTTPException(404)
    p=ROOT/'samples'/sid/filename
    if not p.is_file():p=ROOT/'evidence/first-trials'/sid/filename
    if not p.is_file():raise HTTPException(404)
    return FileResponse(p)

@app.post('/api/images')
async def upload(file:UploadFile=File(...),modality:str=Form(...),date:str=Form(''),units:str=Form('')):
    raw=await file.read(20*1024*1024+1)
    if len(raw)>20*1024*1024:raise HTTPException(413,'Use a TIFF smaller than 20 MB.')
    iid=uuid.uuid4().hex;path=UPLOADS/(iid+'.tif');path.write_bytes(raw)
    try:r=inspect(path,modality,date,units)
    except Exception as e:path.unlink(missing_ok=True);raise HTTPException(400,str(e))
    r['id']=iid;r['name']=Path(file.filename or 'image.tif').name;images[iid]=r
    return {k:v for k,v in r.items() if k not in ['data','path']}

@app.post('/api/single-images')
async def upload_single(file:UploadFile=File(...)):
    raw=await file.read(20*1024*1024+1)
    if len(raw)>20*1024*1024:raise HTTPException(413,'Upload limit is 20 MB.')
    iid=uuid.uuid4().hex;path=UPLOADS/(iid+'.upload');path.write_bytes(raw)
    try:r=single_bridge.upload(path,Path(file.filename or 'image').name)
    except ValueError as e:path.unlink(missing_ok=True);raise HTTPException(400,str(e))
    record={**r,'main_id':r['id'],'id':iid,'path':str(path),'modality':'optical','is_single':True};images[iid]=record
    preview=single_bridge.request('GET','/api/images/'+r['id']).content;(UPLOADS/(iid+'.png')).write_bytes(preview)
    return {k:v for k,v in record.items() if k!='path'}

@app.get('/api/single-images/{iid}')
def single_preview(iid:str):
    if iid not in images or not images[iid].get('is_single'):raise HTTPException(404)
    return FileResponse(UPLOADS/(iid+'.png'))

def prepare(payload):
    if not isinstance(payload,dict):raise ValueError('Send a question with a sample or two uploaded image IDs.')
    sid=payload.get('sample')
    if sid is not None and not isinstance(sid,str):raise ValueError('Invalid sample ID.')
    if sid:
        if sid not in samples:raise ValueError('Unknown sample.')
        sample=samples[sid];paths=[ROOT/'samples'/sid/f for f in sample['files']]
        modes=['optical','optical'] if sample['kind']=='temporal' else ['optical','sar']
        records=[inspect(p,m) for p,m in zip(paths,modes)]
    else:
        ids=payload.get('images',[])
        if not isinstance(ids,list) or len(ids) not in [1,2] or any(not isinstance(i,str) or i not in images for i in ids):raise ValueError('Upload two images first.')
        records=[images[i] for i in ids];sample=None
    query=payload.get('query','');selected=controller.plan(query,records,payload.get('threshold',.5));task=selected['task']
    if len(records)==1:
        if not records[0].get('is_single'):raise ValueError('Use the single-image uploader for VQA or NDVI.')
        checks={'task':task,'inputs':[{k:v for k,v in records[0].items() if k not in ['path','data']}]}
    else:
        if any(r.get('is_single') for r in records):raise ValueError('Use paired TIFF uploads for two-image analysis.')
        checks=validate(records,task,trusted_benchmark=bool(sid),enforce_content=True)
    checks['plan']=selected
    if sample:checks['sample_manifest']=sample
    return records,query,task,checks

def work(jid,records,query,task,checks):
    global busy
    out=RUNS/jid;out.mkdir(exist_ok=True)
    try:
        jobs[jid]['stage']='Running paired specialist on CPU'
        if task in ['vqa','ndvi']:result=single_bridge.run(records[0],query,checks['plan'],out)
        elif task=='temporal':result=mci.temporal(records[0]['data'].transpose(1,2,0),records[1]['data'].transpose(1,2,0),out)
        elif task=='water_map':
            optical=next(r for r in records if r['modality']=='optical');sar=next(r for r in records if r['modality']=='sar')
            with rasterio.open(optical['path']) as ds:profile=ds.profile
            result=flood.segment(sar['data'],optical['data'],out,profile)
        else:
            bands={name:r['data'][i] for r in records for i,name in enumerate(r['bands'])}
            result=engine.fusion(bands,out)
        if task=='temporal' and any(word in query.lower() for word in ['increas','decreas','gain','loss']):
            result['answer']='Direction in this caption is a model interpretation, not a measured gain/loss. '+result['answer']
        if task=='optical_sar':
            groups={'water':['Inland waters','Marine waters'],'built-up':['Urban fabric','Industrial or commercial units'],'forest':['Broad-leaved forest','Coniferous forest','Mixed forest']}
            findings=[]
            for label,names in groups.items():
                requested=label in query.lower() or (label=='built-up' and 'urban' in query.lower())
                if requested:
                    found=[name for name in names if result['scores']['all'][name]>=0.5]
                    findings.append(label.capitalize()+': '+('the joint model suggests '+', '.join(found) if found else 'no class exceeded the fixed 0.5 threshold; absence is not established')+'.')
            if findings:result['answer']=' '.join(findings)+' '+result['answer']
        result.update({'id':jid,'query':query,'input_checks':checks,'controller':controller.VERSION,'created_at':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())})
        (out/'result.json').write_text(json.dumps(result,indent=2))
        for i,r in enumerate(records):shutil.copy2(r['path'],out/(f'input-{i+1}.original' if r.get('is_single') else f'input-{i+1}.tif'))
        with zipfile.ZipFile(out/'evidence.zip','w',zipfile.ZIP_DEFLATED) as z:
            for p in out.iterdir():
                if p.name!='evidence.zip':z.write(p,p.name)
        jobs[jid]={'state':'complete','result':result}
    except Exception as e:
        (out/'error.txt').write_text(traceback.format_exc());jobs[jid]={'state':'failed','error':str(e)}
    finally:
        with lock:busy=False

@app.post('/api/analyze')
async def analyze(request:Request):
    global busy
    try:records,query,task,checks=prepare(await request.json())
    except (ValueError,TypeError,KeyError) as e:raise HTTPException(400,str(e))
    with lock:
        if busy:raise HTTPException(409,'One paired run is already active. Please wait for it to finish.')
        busy=True
    jid=uuid.uuid4().hex;jobs[jid]={'state':'processing','stage':'Validated inputs; preparing specialist'}
    executor.submit(work,jid,records,query,task,checks);return {'id':jid,'task':task,'checks':checks}

@app.get('/api/jobs/{jid}')
def job(jid:str):
    if jid not in jobs:raise HTTPException(404,'Run not found.')
    return jobs[jid]
@app.get('/api/runs/{jid}/{filename}')
def artifact(jid:str,filename:str):
    if len(jid)!=32 or any(c not in '0123456789abcdef' for c in jid):raise HTTPException(404)
    if filename not in ['before.png','after.png','change-mask.png','overlay.png','optical.png','sar.png','scores.npz','result.json','evidence.zip','input-preview.png','rgb.png','false-colour.png','evidence.png','mask.png','ndvi.tif','s1-water.png','s2-water.png','all-water.png','water-overlay.png','water-mask.tif','water-scores.npz','main-raw-result.json']:raise HTTPException(404)
    p=RUNS/jid/filename
    if not p.is_file():raise HTTPException(404)
    return FileResponse(p,filename=filename if p.suffix in ['.zip','.json','.npz'] else None)
app.mount('/assets',StaticFiles(directory=ROOT/'web'),name='assets')
app.mount('/art',StaticFiles(directory=ROOT.parent/'web/art'),name='art')
