import io,json,time,uuid,threading,hashlib,traceback
import geo
from scene_description import is_scene_description, PROMPT as SCENE_PROMPT, VERSION as SCENE_POLICY
from routing import route
from counting import count_fields
from count_description import add_count_description
from vqa_answers import present_answer, present_open_answer, present_count_answer, VERSION as ANSWER_POLICY
from stages import create_stages
import evaluation as saved_evaluation
from contextlib import nullcontext
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from fastapi import FastAPI,UploadFile,File,Form,HTTPException,Request
from fastapi.responses import FileResponse,JSONResponse,RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.trustedhost import TrustedHostMiddleware
from PIL import Image,ImageOps,UnidentifiedImageError
ROOT=Path(__file__).resolve().parent
DATA=Path('/root/satquery/app-data');DATA.mkdir(exist_ok=True)
UPLOADS=DATA/'images';UPLOADS.mkdir(exist_ok=True)
RUNS=DATA/'runs';RUNS.mkdir(exist_ok=True)
MODEL_ID='AdaptLLM/remote-sensing-Qwen2-VL-2B-Instruct'
REVISION='7f5dd71bf0f40c282193d50160e848a387a08ffe'
app=FastAPI(title='SATquery AI',docs_url=None,redoc_url=None)
app.add_middleware(TrustedHostMiddleware,allowed_hosts=['localhost','127.0.0.1','testserver'])
executor=ThreadPoolExecutor(max_workers=1)
lock=threading.Lock();jobs={};images={};busy=False;model=None;processor=None
Image.MAX_IMAGE_PIXELS=25_000_000
@app.middleware('http')
async def local_requests(request:Request,call_next):
    origin=request.headers.get('origin')
    if origin and origin not in ['http://localhost:8765','http://127.0.0.1:8765']:
        return JSONResponse({'detail':'Only the local app may send requests.'},status_code=403)
    if int(request.headers.get('content-length','0'))>21*1024*1024:
        return JSONResponse({'detail':'Image must be smaller than 20 MB.'},status_code=413)
    response=await call_next(request)
    response.headers['X-Content-Type-Options']='nosniff'
    return response
@app.get('/api/status')
def status():return {'state':'processing' if busy else ('ready' if model is not None else 'idle'),'model':MODEL_ID,'revision':REVISION,'device':'Local GPU','adapter':'Baseline - no adapter'}
@app.post('/api/images')
async def upload(file:UploadFile=File(...)):
    raw=await file.read(20*1024*1024+1)
    if len(raw)>20*1024*1024:raise HTTPException(413,'Image must be smaller than 20 MB.')
    iid=uuid.uuid4().hex
    metadata=None
    try:
        if raw[:4] in [b'II*\x00',b'MM\x00*',b'II+\x00',b'MM\x00+']:
            im,metadata=geo.ingest(raw,UPLOADS/f'{iid}.tif')
            size=list(im.size)
        else:
            with Image.open(io.BytesIO(raw)) as source:
                if source.format not in ['PNG','JPEG','WEBP','TIFF']:raise ValueError('Use PNG, JPEG, WebP, or an RGB TIFF.')
                if source.width*source.height>25_000_000:raise ValueError('Use an image with no more than 25 million pixels.')
                if getattr(source,'n_frames',1)>1:raise ValueError('Export one image, not multiple frames.')
                if source.format=='TIFF' and source.mode!='RGB':raise ValueError('This TIFF needs band selection. Export an optical RGB preview first.')
                im=ImageOps.exif_transpose(source).convert('RGB');im.load();size=list(im.size)
    except (UnidentifiedImageError,OSError,ValueError,Image.DecompressionBombError) as e:raise HTTPException(400,str(e) or 'Unable to read image.')
    im.save(UPLOADS/f'{iid}.png')
    record={'id':iid,'name':Path(file.filename or 'image').name,'width':size[0],'height':size[1],'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'preview':f'/api/images/{iid}'}
    record['geo']=metadata
    images[iid]=record;return record
@app.get('/api/images/{iid}')
def preview(iid:str):
    if iid not in images:raise HTTPException(404,'Upload the image again.')
    return FileResponse(UPLOADS/f'{iid}.png',media_type='image/png')
@app.get('/api/sample')
def sample():return FileResponse('/root/satquery/demo_image.png',media_type='image/png')
@app.post('/api/analyze')
def analyze(image_id:str=Form(...),question:str=Form(...),mode:str=Form('baseline'),threshold:float=Form(0.5)):
    global busy
    if mode not in ['baseline','pilot_binary','pilot_rural']:raise HTTPException(400,'Unknown model mode.')
    question=question.strip()
    if not question or len(question)>500:raise HTTPException(400,'Enter a question between 1 and 500 characters.')
    if image_id not in images:raise HTTPException(404,'Upload an image first.')
    routing=route(question,ndvi_supported=(images[image_id].get('geo') or {}).get('ndvi_supported',False),threshold=threshold)
    if routing['tool']=='refuse':raise HTTPException(422,routing)
    if routing['tool']=='ndvi':return ndvi_run(image_id,threshold,question)
    classification_question=routing.get('canonical_question',question)
    requested_mode=mode
    if routing['rule'] in ('baseball_count','visual_count','general_visual_question'):mode='baseline'
    if mode=='pilot_binary' and not question.lower().startswith(('is ','are ','does ')):
        raise HTTPException(422,'The yes/no adapter requires a supported yes/no question. Select Original for descriptions.')
    if mode=='pilot_binary' and 'rural or urban' in classification_question.lower():
        raise HTTPException(422,'Select the rural/urban adapter or Original for this question.')
    if mode=='pilot_rural' and 'rural or urban' not in classification_question.lower():
        raise HTTPException(422,'The rural/urban adapter requires a rural or urban question. Select Original for other questions.')
    if mode!='baseline' and not Path('/root/satquery/experiments/lora-pilot-v1/adapter/adapter_config.json').exists():raise HTTPException(503,'Pilot adapter is not available.')
    with lock:
        if busy:raise HTTPException(409,'The model is processing a question. Please wait.')
        busy=True
    rid=uuid.uuid4().hex
    jobs[rid]={'id':rid,'state':'queued','stage':'Preparing image','question':question,'image':images[image_id],'started':time.time(),'model':MODEL_ID,'revision':REVISION,'adapter':None if mode=='baseline' else 'lora-pilot-v1','mode':mode,'route':'Single-image optical VQA','trace':[]}
    jobs[rid]['routing']=routing
    jobs[rid]['requested_mode']=requested_mode
    executor.submit(run_job,rid,image_id);return {'id':rid,'routing':routing}
def run_job(rid,iid):
    global model,processor,busy
    job=jobs[rid]
    try:
        import torch
        from huggingface_hub import snapshot_download
        from transformers import Qwen2VLForConditionalGeneration,AutoProcessor
        if model is None:
            job.update(state='running',stage='Loading local model');start=time.perf_counter()
            path=snapshot_download(MODEL_ID,revision=REVISION,local_files_only=True)
            processor=AutoProcessor.from_pretrained(path,use_fast=False,min_pixels=256*28*28,max_pixels=512*28*28,size={'shortest_edge':256*28*28,'longest_edge':512*28*28})
            model=Qwen2VLForConditionalGeneration.from_pretrained(path,torch_dtype=torch.bfloat16,device_map={'':'cuda:0'},attn_implementation='sdpa').eval()
            job['trace'].append({'step':'Load pinned checkpoint','seconds':round(time.perf_counter()-start,3)})
        job.update(state='running',stage='Analyzing image')
        im=Image.open(UPLOADS/f'{iid}.png').convert('RGB')
        if job['routing']['rule']=='baseball_count':
            estimate=count_fields(model,processor,im)
            job.update(state='running',stage='Describing scene',answer=estimate['answer'],
                raw_answer='\n'.join(v['raw_answer'] for v in estimate['views']),
                counting=estimate,answer_policy=estimate['policy'],answer_validation=estimate,
                seconds=round(time.time()-job['started'],3),generation_seconds=estimate['generation_seconds'],
                peak_allocated_GiB=estimate['peak_allocated_GiB'],generated_tokens=estimate['generated_tokens'],
                max_new_tokens=estimate['max_new_tokens'],visual_token_bounds=[256,512])
            job['trace'].append({'step':'Compare original and mirrored image counts','seconds':estimate['generation_seconds']})
            add_count_description(job,model,processor,im)
            job.update(state='complete',stage='Complete',seconds=round(time.time()-job['started'],3))
            return
        pilot=job['mode']!='baseline'
        if pilot and not hasattr(model,'peft_config'):
            from peft import PeftModel
            model=PeftModel.from_pretrained(model,'/root/satquery/experiments/lora-pilot-v1/adapter').eval()
        selected_processor=processor
        suffix=''
        if pilot:
            selected_processor=AutoProcessor.from_pretrained(snapshot_download(MODEL_ID,revision=REVISION,local_files_only=True),use_fast=False,min_pixels=64*28*28,max_pixels=128*28*28,size={'shortest_edge':64*28*28,'longest_edge':128*28*28})
            suffix=' Answer with only rural or urban.' if job['mode']=='pilot_rural' else ' Answer with only yes or no.'
        if job['routing']['rule']=='visual_count':
            suffix=' Answer with only a single integer. Do not describe the image.'
        whole_scene=not pilot and is_scene_description(job['question'])
        job['effective_question']=SCENE_PROMPT if whole_scene else job['routing'].get('canonical_question',job['question'])+suffix
        if whole_scene:job['description_policy']=SCENE_POLICY
        job['visual_token_bounds']=[64,128] if pilot else [256,512]
        messages=[{'role':'user','content':[{'type':'image'},{'type':'text','text':job['effective_question']}]}]
        prompt=selected_processor.apply_chat_template(messages,tokenize=False,add_generation_prompt=True)
        inputs=selected_processor(text=[prompt],images=[im],return_tensors='pt').to('cuda')
        torch.cuda.reset_peak_memory_stats();torch.cuda.synchronize();start=time.perf_counter()
        adapter_context=model.disable_adapter() if not pilot and hasattr(model,'peft_config') else nullcontext()
        limit=16 if pilot else 192 if whole_scene else 128
        with torch.inference_mode(),adapter_context:output=model.generate(**inputs,max_new_tokens=limit,do_sample=False,temperature=None,top_p=None,top_k=None)
        torch.cuda.synchronize()
        answer=processor.batch_decode(output[:,inputs.input_ids.shape[1]:],skip_special_tokens=True)[0]
        job['raw_answer']=answer
        job['answer_validation']=(present_answer(job['routing'].get('canonical_question',job['question']),answer,truncated=output.shape[1]-inputs.input_ids.shape[1]>=limit) if pilot else present_open_answer(answer,truncated=output.shape[1]-inputs.input_ids.shape[1]>=limit,count=job['routing']['rule']=='visual_count'))
        if job['routing']['rule']=='visual_count':
            job['answer_validation']=present_count_answer(answer,truncated=output.shape[1]-inputs.input_ids.shape[1]>=limit)
        job['answer_policy']=job['answer_validation']['policy']
        answer=job['answer_validation']['answer']
        job.update(state='running',stage='Finalizing answer',answer=answer,seconds=round(time.time()-job['started'],3),generation_seconds=round(time.perf_counter()-start,3),peak_allocated_GiB=round(torch.cuda.max_memory_allocated()/2**30,3),generated_tokens=output.shape[1]-inputs.input_ids.shape[1],max_new_tokens=limit)
        job['trace'].append({'step':'Generate model answer','seconds':job['generation_seconds']})
        if job['routing']['rule']=='visual_count':
            add_count_description(job,model,processor,im)
        job.update(state='complete',stage='Complete',seconds=round(time.time()-job['started'],3))
    except Exception:
        traceback.print_exc();job.update(state='error',stage='Unable to complete',error='The model could not complete this request. Check the server log; a smaller image or restarting the server may help.')
    finally:
        try:
            (RUNS/f'{rid}.json').write_text(json.dumps(job,indent=2))
        finally:
            with lock:busy=False
@app.get('/api/runs/{rid}')
def result(rid:str):
    if rid not in jobs:raise HTTPException(404,'Run not found.')
    return jobs[rid]
@app.get('/api/evaluation')
def evaluation():return json.loads(saved_evaluation.EVIDENCE['diagnostic'].read_text())
@app.get('/api/development')
def development():
    try:return saved_evaluation.development()
    except (OSError,ValueError,KeyError) as e:raise HTTPException(503,'Saved development evidence could not be verified; comparison withheld.') from e

@app.get('/api/evidence/{key}')
def evaluation_evidence(key:str):
    if key not in saved_evaluation.EVIDENCE:raise HTTPException(404,'Evidence not found.')
    path=saved_evaluation.EVIDENCE[key]
    return FileResponse(path,filename=path.name)
@app.get('/')
def index():return RedirectResponse('http://localhost:8767/',status_code=307)
@app.get('/classic')
def classic():return FileResponse(ROOT/'web/index.html')
app.mount('/static',StaticFiles(directory=ROOT/'web'),name='static')

@app.get('/api/scene-sample')
def scene_sample():
    return FileResponse('/root/satquery/scenes/dehradun-sentinel2-20211125.tif',media_type='image/tiff',filename='dehradun-sentinel2-20211125.tif')

@app.post('/api/ndvi')
def ndvi_run(image_id:str=Form(...),threshold:float=Form(0.5),question:str=Form('Calculate NDVI')):
    global busy
    if image_id not in images:raise HTTPException(404,'Upload an image first.')
    routing=route(question,ndvi_supported=(images[image_id].get('geo') or {}).get('ndvi_supported',False),threshold=threshold)
    if routing['tool']!='ndvi':
        raise HTTPException(422,routing if routing['tool']=='refuse' else {'tool':'refuse','rule':'ndvi_endpoint_intent','reason':'This question requires VQA. Use automatic analysis; NDVI cannot answer it.'})
    if not (images[image_id].get('geo') or {}).get('ndvi_supported'):
        raise HTTPException(422,'NDVI needs labelled, calibrated red and near-infrared bands. Load the multispectral sample or a supported GeoTIFF.')
    if not -1<=threshold<=1:raise HTTPException(422,'Threshold must be between -1 and 1.')
    with lock:
        if busy:raise HTTPException(409,'Another analysis is running.')
        busy=True
    rid=uuid.uuid4().hex
    jobs[rid]={'id':rid,'state':'queued','stage':'Calculating NDVI','image':images[image_id],'started':time.time(),'route':'NDVI from calibrated red/NIR','threshold':threshold}
    jobs[rid].update(question=question,routing=routing)
    executor.submit(run_ndvi,rid,image_id)
    return {'id':rid}

def run_ndvi(rid,iid):
    global busy
    job=jobs[rid]
    try:
        out=RUNS/rid
        stats=geo.analyse(UPLOADS/f'{iid}.tif',out,job['threshold'])
        area=stats['selected_area_m2']
        answer=f"NDVI ≥ {job['threshold']:.2f}: {stats['selected_percent_of_valid']:.2f}% of valid pixels."
        answer+=f" Selected pixels cover {stats['selected_percent_of_crop']:.2f}% of the whole crop."
        if area is not None:answer+=f" Projected grid area: {area/10000:.2f} hectares."
        answer+=f" Valid pixels cover {stats['valid_coverage_percent']:.2f}% of this crop. This is threshold-based coverage, not a vegetation-health diagnosis."
        job.update(state='running',stage='Building processing views',answer=answer,statistics=stats,overlay=f'/api/runs/{rid}/overlay',raster=f'/api/runs/{rid}/ndvi',seconds=round(time.time()-job['started'],3))
        try:
            artifacts=create_stages(UPLOADS/f'{iid}.tif',UPLOADS/f'{iid}.png',out,job['threshold'])
            job['processing_stages']={name:f'/api/runs/{rid}/{name}' for name in artifacts}
        except Exception:
            traceback.print_exc()
            job['processing_stages_error']='Processing views could not be generated. The analytical result and original exports remain available.'
        job.update(state='complete',stage='Complete',seconds=round(time.time()-job['started'],3))
    except Exception as e:
        traceback.print_exc()
        job.update(state='error',error=str(e),stage='Unable to calculate NDVI')
    finally:
        try:(RUNS/f'{rid}.json').write_text(json.dumps(job,indent=2))
        finally:
            with lock:busy=False

@app.get('/api/runs/{rid}/{artifact}')
def analytical_artifact(rid:str,artifact:str):
    artifacts={'overlay':'overlay.png','ndvi':'ndvi.tif','rgb':'rgb.png','false-colour':'false-colour.png','evidence':'evidence.png','mask':'mask.png'}
    if rid not in jobs or jobs[rid].get('state')!='complete' or artifact not in artifacts:
        raise HTTPException(404,'Artifact not found.')
    name=artifacts[artifact]
    path=RUNS/rid/name
    if not path.exists():raise HTTPException(404,'Artifact not found.')
    return FileResponse(path,media_type='image/tiff' if artifact=='ndvi' else 'image/png',filename=name)

@app.get('/api/reliability')
def reliability():
    path=ROOT/'results/reliability-20260907/public-summary.json'
    if not path.exists():raise HTTPException(503,'Final verification is being completed.')
    report=json.loads(path.read_text(encoding='utf-8'))
    for item in report['evidence']:
        evidence=ROOT/item['path']
        if not evidence.is_file() or hashlib.sha256(evidence.read_bytes()).hexdigest()!=item['sha256']:
            raise HTTPException(503,'Verification evidence changed; results withheld.')
    return report

@app.get('/api/reliability/evidence')
def reliability_evidence():
    report=reliability()
    return JSONResponse(report,headers={'Content-Disposition':'attachment; filename="satquery-combined-verification.json"'})


# Manual lab shares the web server; it is not connected to the question router.
from grounding_lab.app import app as grounding_app
def reserve_lab_gpu():
    global busy
    with lock:
        if busy:raise HTTPException(409,'Another analysis is running. Please wait before starting the lab.')
        busy=True

def prepare_lab_gpu():
    global model,processor
    if model is not None:
        import gc,torch
        model=None;processor=None
        gc.collect();torch.cuda.empty_cache()

def release_lab_gpu():
    global busy
    with lock:busy=False

grounding_app.state.gpu_busy=lambda:busy
grounding_app.state.reserve_gpu=reserve_lab_gpu
grounding_app.state.prepare_gpu=prepare_lab_gpu
grounding_app.state.release_gpu=release_lab_gpu
app.mount("/grounding", grounding_app, name="grounding-lab")
