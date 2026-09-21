"""Independent localhost:8766 lab. Does not import or modify the main router."""
import hashlib,io,json,math,subprocess,sys,threading,time,uuid,zipfile
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from fastapi import FastAPI,UploadFile,File,HTTPException,Request
from fastapi.responses import FileResponse,JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.trustedhost import TrustedHostMiddleware
from pydantic import BaseModel,Field
from PIL import Image,ImageOps,UnidentifiedImageError
from engine import CATEGORIES
ROOT=Path(__file__).resolve().parent
DATA=Path('/root/satquery/grounding-lab/app-data');DATA.mkdir(parents=True,exist_ok=True)
app=FastAPI(title='SATquery Grounding Lab',docs_url=None,redoc_url=None)
app.add_middleware(TrustedHostMiddleware,allowed_hosts=['localhost','127.0.0.1','testserver'])
lock=threading.Lock();busy=False;pool=ThreadPoolExecutor(max_workers=1)
ARTIFACTS={'source':'source.png','boxes':'boxes.png','outlines':'outlines.png','masks':'masks.png','instances':'instances.png','arrays':'masks.npz','record':'result.json','bundle':'evidence.zip'}

@app.middleware('http')
async def local_only(request:Request,call_next):
    if request.headers.get('origin') and request.headers['origin'] not in ['http://localhost:8766','http://127.0.0.1:8766']:
        return JSONResponse({'detail':'Only the local lab may submit requests.'},status_code=403)
    if int(request.headers.get('content-length','0'))>21*1024*1024:return JSONResponse({'detail':'Maximum upload is 20 MB.'},status_code=413)
    result=await call_next(request);result.headers['X-Content-Type-Options']='nosniff';return result

def directory(identifier):
    if len(identifier)!=32 or any(c not in '0123456789abcdef' for c in identifier):raise HTTPException(404,'Not found')
    return DATA/identifier

@app.get('/')
def page():return FileResponse(ROOT/'web/index.html')

@app.get('/api/status')
def status():return dict(busy=busy,models_available=Path('/root/satquery/grounding-lab/models.json').exists(),isolated=True)

@app.post('/api/images')
async def upload(file:UploadFile=File(...)):
    raw=await file.read(20*1024*1024+1)
    if len(raw)>20*1024*1024:raise HTTPException(413,'Maximum upload is 20 MB.')
    try:
        with Image.open(io.BytesIO(raw)) as source:
            if source.format not in ['PNG','JPEG','WEBP','TIFF'] or getattr(source,'n_frames',1)>1:raise ValueError('Use a single PNG, JPEG, WebP or RGB TIFF.')
            if source.width*source.height>6_000_000 or min(source.size)<64:raise ValueError('Use an image from 64 pixels per side up to 6 megapixels.')
            if source.format=='TIFF' and source.mode!='RGB':raise ValueError('Export an RGB preview from a multispectral TIFF for this lab.')
            im=ImageOps.exif_transpose(source).convert('RGB');im.load()
    except (ValueError,OSError,UnidentifiedImageError,Image.DecompressionBombError) as e:raise HTTPException(400,str(e))
    iid=uuid.uuid4().hex;p=directory(iid);p.mkdir();im.save(p/'input.png')
    record=dict(id=iid,name=Path(file.filename or 'image').name,width=im.width,height=im.height,sha256=hashlib.sha256(raw).hexdigest(),preview=f'/api/images/{iid}')
    (p/'image.json').write_text(json.dumps(record));return record

@app.get('/api/images/{iid}')
def image(iid:str):
    p=directory(iid)/'input.png'
    if not p.exists():raise HTTPException(404,'Upload the image again.')
    return FileResponse(p)

@app.get('/api/samples/{name}')
def sample(name:str):
    if name not in ['stadium','car','baseball','farmland']:raise HTTPException(404,'Sample not found')
    return FileResponse(ROOT/'samples'/f'{name}.png')

class Selection(BaseModel):
    image_id:str
    category:str
    threshold:float=Field(default=.3,ge=.15,le=.8)
    mode:str='both'

@app.post('/api/runs')
def run(selection:Selection):
    global busy
    if selection.category not in CATEGORIES or selection.mode not in ['both','boxes']:raise HTTPException(422,'Choose a listed category and task.')
    if not math.isfinite(selection.threshold):raise HTTPException(422,'Use a finite score threshold.')
    src=directory(selection.image_id)
    if not (src/'input.png').exists():raise HTTPException(404,'Upload an image first.')
    with lock:
        if busy:raise HTTPException(409,'A lab run is already processing. Please wait.')
        busy=True
    rid=uuid.uuid4().hex;out=directory(rid);out.mkdir()
    info=dict(id=rid,state='running',stage='Starting isolated worker',started=time.time(),image=json.loads((src/'image.json').read_text()),selection=selection.model_dump())
    (out/'job.json').write_text(json.dumps(info))
    config=dict(source=str(src/'input.png'),out=str(out),category=selection.category,threshold=selection.threshold,mode=selection.mode)
    (out/'request.json').write_text(json.dumps(config));pool.submit(worker,rid);return info

def worker(rid):
    global busy
    out=directory(rid)
    try:
        with (out/'worker.log').open('w') as log:
            proc=subprocess.run([sys.executable,str(ROOT/'engine.py'),str(out/'request.json')],stdout=log,stderr=log,timeout=600)
        if proc.returncode and not (out/'error.json').exists():(out/'error.json').write_text(json.dumps({'error':'The model worker failed. See the saved worker log.'}))
        if proc.returncode==0:
            with zipfile.ZipFile(out/'evidence.zip','w',zipfile.ZIP_DEFLATED) as z:
                for p in out.iterdir():
                    if p.name in set(ARTIFACTS.values())-{'evidence.zip'}:z.write(p,p.name)
    except subprocess.TimeoutExpired:(out/'error.json').write_text(json.dumps({'error':'Run exceeded 10 minutes. Try a smaller image.'}))
    except Exception as e:(out/'error.json').write_text(json.dumps({'error':str(e)}))
    finally:
        (out/'finished').touch()
        with lock:busy=False

@app.get('/api/runs/{rid}')
def get_run(rid:str):
    out=directory(rid)
    if not (out/'job.json').exists():raise HTTPException(404,'Run not found')
    job=json.loads((out/'job.json').read_text())
    if (out/'error.json').exists():job.update(state='error',**json.loads((out/'error.json').read_text()))
    elif (out/'result.json').exists() and (out/'finished').exists():job.update(state='complete',result=json.loads((out/'result.json').read_text()))
    elif (out/'progress.json').exists():
        try:job.update(json.loads((out/'progress.json').read_text()))
        except json.JSONDecodeError:pass
    if job['state']=='running' and not busy:job.update(state='error',error='The lab restarted before this run finished. Start a new run.')
    return job

@app.get('/api/runs/{rid}/{artifact}')
def artifact(rid:str,artifact:str):
    if artifact not in ARTIFACTS:raise HTTPException(404,'Artifact not found')
    out=directory(rid);p=out/ARTIFACTS[artifact]
    if not (out/'finished').exists() or not p.is_file():raise HTTPException(404,'Artifact not ready')
    return FileResponse(p,filename=p.name)

app.mount('/assets',StaticFiles(directory=ROOT/'web'),name='lab-assets')
app.mount('/art',StaticFiles(directory=ROOT.parent/'web/art'),name='shared-art')
