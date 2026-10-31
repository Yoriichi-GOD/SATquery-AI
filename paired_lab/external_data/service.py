"""Local-only APIs with bounded streamed chunks and one isolated operation at a time."""
import json
import os
import signal
import subprocess
import sys
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import psutil
from fastapi import APIRouter,Request
from fastapi.responses import FileResponse,JSONResponse,Response
from .common import CHUNK,DataError,contained,fail,identifier,read_json,request_check,utc,write_json,worker_limit_bytes
from .contracts import REGISTRY,asset_inventory,preflight,report_csv
from .store import DatasetStore

TERMINAL={'COMPLETE','EVALUATED','EVALUATION_NOT_POSSIBLE','PROCESSING_FAILED','CANCELLED','INTERRUPTED'}


class Service:
    def __init__(self,root,timeout=900):
        self.root=Path(root).resolve();self.store=DatasetStore(self.root/'datasets');self.jobs=self.root/'jobs';self.jobs.mkdir(exist_ok=True)
        self.timeout=timeout;self.lock=threading.Lock();self.active=None;self.process=None;self.pool=ThreadPoolExecutor(max_workers=1)
        for path in self.jobs.glob('*/job.json'):
            value=read_json(path)
            if value['state'] not in TERMINAL:
                value.update(state='INTERRUPTED',message='Prior application process stopped; original inputs and evidence retained.');write_json(path,value)
        self.assets=None;self.asset_time=0

    def inventory(self):
        if self.assets is None or time.monotonic()-self.asset_time>300:
            self.assets=asset_inventory();self.asset_time=time.monotonic()
        return self.assets

    def report(self,did,parameters):
        request_check(parameters)
        return preflight(self.store.get(did),parameters.get('inputs'),self.inventory(),parameters,root=self.store.directory(did))

    def jobdir(self,jid):return contained(self.jobs,identifier(jid))

    def get(self,jid):
        path=self.jobdir(jid)/'job.json'
        if not path.is_file():fail('JOB_NOT_FOUND','External operation not found.')
        value=read_json(path)
        progress=path.parent/'progress.json'
        if progress.is_file():value['progress']=read_json(progress)
        return value

    def submit(self,did,operation,parameters):
        if operation not in ('inspect','analyze','evaluate'):fail('UNSUPPORTED_TASK','Choose inspect, analyze or evaluate.')
        request_check(parameters)
        if not self.store.upload_lock.acquire(False):fail('UPLOAD_BUSY','Finish the current upload chunk before starting an operation.')
        try:
          with self.lock,self.store.lock:
            dataset=self.store.get(did)
            if self.active:fail('WORKER_BUSY','One external operation is already active; wait or cancel it.')
            if operation=='inspect' and (not dataset['files'] or any(f['state'] not in ('STORED','INSPECTED','REJECTED') for f in dataset['files'])):fail('INCOMPLETE_UPLOAD','Finish or explicitly restart incomplete uploads before inspection.')
            if operation!='inspect' and not dataset.get('revision'):fail('DATASET_NOT_INSPECTED','Complete inspection before analysis or evaluation.')
            ceiling=worker_limit_bytes(operation,parameters.get('specialist'))
            if psutil.virtual_memory().available<ceiling+256*CHUNK:fail('INSUFFICIENT_MEMORY','Available RAM is below this worker ceiling plus 256 MiB reserve. Free memory or explicitly configure a smaller bounded ceiling; no worker was launched.')
            jid=uuid.uuid4().hex;folder=self.jobdir(jid);folder.mkdir()
            value=dict(id=jid,dataset_id=did,operation=operation,state='QUEUED',created_utc=utc(),dataset_previous_state=dataset['state'],worker_rss_limit_bytes=ceiling,message='Waiting for the isolated data worker.')
            write_json(folder/'job.json',value)
            write_json(folder/'request.json',dict(root=str(self.store.root),dataset_id=did,operation=operation,parameters=parameters))
            dataset['state']='INSPECTING' if operation=='inspect' else 'PROCESSING';self.store.save(dataset)
            self.active=jid;self.pool.submit(self.work,jid)
        finally:self.store.upload_lock.release()
        return value

    def terminate(self,process):
        if process and process.poll() is None:
            if os.name=='posix':os.killpg(process.pid,signal.SIGTERM)
            else:process.terminate()
            try:process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                if os.name=='posix':os.killpg(process.pid,signal.SIGKILL)
                else:process.kill()
                process.wait(timeout=3)

    def work(self,jid):
        folder=self.jobdir(jid);value=self.get(jid);started=time.perf_counter();peak=0;failure=None
        limit=value['worker_rss_limit_bytes']
        env={**os.environ,'HF_HUB_OFFLINE':'1','TRANSFORMERS_OFFLINE':'1','OMP_NUM_THREADS':'4','OPENBLAS_NUM_THREADS':'1'}
        repo=Path(__file__).resolve().parents[2]
        try:
            value.update(state='RUNNING',message='Running a bounded isolated worker.');write_json(folder/'job.json',value)
            with (folder/'worker.log').open('w',encoding='utf-8') as log:
                process=subprocess.Popen([sys.executable,'-m','paired_lab.external_data.worker',str(folder/'request.json')],cwd=repo,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=os.name=='posix')
                with self.lock:self.process=process
                while process.poll() is None:
                    if (folder/'cancel.flag').exists():failure=dict(code='CANCELLED',message='The actual isolated worker was stopped.');self.terminate(process);break
                    if time.perf_counter()-started>self.timeout:failure=dict(code='WORKER_TIMEOUT',message='The configured external-operation deadline was exceeded.');self.terminate(process);break
                    try:
                        proc=psutil.Process(process.pid);rss=proc.memory_info().rss+sum(p.memory_info().rss for p in proc.children(recursive=True));peak=max(peak,rss)
                        if rss>limit:failure=dict(code='WORKER_MEMORY_LIMIT',message='Worker exceeded its configured resident-memory cap.');self.terminate(process);break
                    except psutil.Error:pass
                    time.sleep(.1)
            if failure is None and (folder/'worker_result.json').exists():
                result=read_json(folder/'worker_result.json');value.update(state=result['state'],result=result,message=result['state'])
            else:
                failure=failure or dict(code='WORKER_EXIT',message='Worker exited without a complete result. Inspect the retained local worker log.')
                value.update(state='CANCELLED' if failure['code']=='CANCELLED' else 'PROCESSING_FAILED',failures=[failure],message=failure['message'])
        except Exception as exc:value.update(state='PROCESSING_FAILED',failures=[dict(code='WORKER_START_FAILED',message=str(exc))])
        finally:
            value.update(finished_utc=utc(),wall_seconds=time.perf_counter()-started,peak_observed_worker_rss_bytes=peak,worker_rss_limit_bytes=limit)
            if (folder/'cancel.flag').exists():value.update(state='CANCELLED',message='Operation stopped; completed originals retained. No later successful result is accepted.')
            write_json(folder/'job.json',value)
            try:
                dataset=self.store.get(value['dataset_id'])
                if dataset['state']=='INSPECTING' and value['state'] in ('CANCELLED','PROCESSING_FAILED'):
                    dataset['state']=value['state'];dataset['message']=value.get('message');self.store.save(dataset)
                elif dataset['state']=='PROCESSING':
                    dataset['state']=value['dataset_previous_state'];dataset['last_job']=jid;self.store.save(dataset)
            finally:
                with self.lock:self.active=None;self.process=None

    def cancel(self,jid):
        value=self.get(jid)
        if value['state'] in TERMINAL:return value
        (self.jobdir(jid)/'cancel.flag').touch()
        value['state']='CANCELLING';value['message']='Stopping the actual isolated data worker.';write_json(self.jobdir(jid)/'job.json',value)
        return value

    def close(self):
        if self.active:self.cancel(self.active)
        self.terminate(self.process);self.pool.shutdown(wait=True,cancel_futures=True)


async def small_json(request):
    raw=bytearray()
    async for chunk in request.stream():
        if len(raw)+len(chunk)>65536:fail('REQUEST_TOO_LARGE','JSON requests are limited to 64 KiB.')
        raw.extend(chunk)
    try:
        value=json.loads(raw)
        if not isinstance(value,dict):raise ValueError()
        return value
    except (ValueError,TypeError):fail('INVALID_JSON','Send a JSON object.')


def install(app,root):
    service=Service(root);app.state.external_data=service;router=APIRouter(prefix='/api/datasets')
    @app.exception_handler(DataError)
    async def error(request,exc):
        status=409 if exc.code in ('WORKER_BUSY','UPLOAD_BUSY','OFFSET_MISMATCH','DATASET_BUSY','ORIGINAL_IMMUTABLE','RUN_EXISTS') else 404 if exc.code.endswith('NOT_FOUND') else 413 if exc.code in ('REQUEST_TOO_LARGE','CHUNK_LIMIT','DATASET_CAP') else 400
        return JSONResponse(dict(code=exc.code,detail=str(exc)),status_code=status)
    @app.middleware('http')
    async def local(request,call_next):
        if request.url.path.startswith('/api/datasets') and (not request.client or request.client.host not in ('127.0.0.1','::1','localhost','testclient','testserver')):
            return JSONResponse(dict(code='LOCAL_ONLY',detail='External dataset operations accept local clients only.'),status_code=403)
        return await call_next(request)
    @router.get('')
    def listing():return dict(datasets=service.store.list(),active_job=service.active)
    @router.post('',status_code=201)
    async def create(request:Request):return service.store.create((await small_json(request)).get('name'))
    @router.get('/contracts')
    def contracts():return dict(contracts=REGISTRY,assets=service.inventory())
    @router.get('/jobs/{jid}')
    def job(jid:str):return service.get(jid)
    @router.post('/jobs/{jid}/cancel')
    def cancel(jid:str):return service.cancel(jid)
    @router.get('/jobs/{jid}/export/{name}')
    def artifact(jid:str,name:str):
        path=contained(service.jobdir(jid)/'evidence',name)
        if not path.is_file() or '/' in name or path.suffix not in ('.json','.csv','.tif','.png','.md','.zip','.sha256'):fail('FILE_NOT_FOUND','Export artifact not found.')
        return FileResponse(path,filename=name,headers={'Cache-Control':'no-store','X-Content-Type-Options':'nosniff'})
    @router.get('/{did}')
    def dataset(did:str):return service.store.get(did)
    @router.post('/{did}/files',status_code=201)
    async def register(did:str,request:Request):
        value=await small_json(request)
        return service.store.register_file(did,value.get('name'),value.get('size'),value.get('role','input'),value.get('sha256'))
    @router.put('/{did}/files/{fid}/content')
    async def content(did:str,fid:str,offset:int,request:Request):
        if not service.store.upload_lock.acquire(False):fail('UPLOAD_BUSY','One upload chunk is already active.')
        part=None;accepted=False
        try:
            row,part=service.store.upload_target(did,fid,offset);written=0
            with part.open('ab') as stream:
                async for chunk in request.stream():
                    written+=len(chunk)
                    if written>8*CHUNK or offset+written>row['bytes']:fail('CHUNK_LIMIT','A chunk exceeds 8 MiB or the declared remaining file size.')
                    stream.write(chunk)
                stream.flush()
            accepted=True;return service.store.record_chunk(did,fid,offset+written)
        finally:
            if part is not None and not accepted and part.exists():
                with part.open('r+b') as stream:stream.truncate(offset)
            service.store.upload_lock.release()
    @router.post('/{did}/files/{fid}/finish')
    def finish(did:str,fid:str):
        if not service.store.upload_lock.acquire(False):fail('UPLOAD_BUSY','Finish the current chunk first.')
        try:return service.store.finish_file(did,fid)
        finally:service.store.upload_lock.release()
    @router.post('/{did}/files/{fid}/restart')
    def restart(did:str,fid:str):return service.store.restart_file(did,fid)
    @router.post('/{did}/files/{fid}/role')
    async def role(did:str,fid:str,request:Request):
        value=await small_json(request);role=value.get('role')
        if role not in ('input','reference','prediction','metadata'):fail('INVALID_ROLE','Choose input, reference, prediction or metadata.')
        if service.active:fail('DATASET_BUSY','Wait or cancel the current operation before changing roles.')
        dataset,file,_=service.store.file(did,fid);file['role']=role;dataset['revision']=None;service.store.save(dataset);return file
    @router.get('/{did}/files/{fid}/preview')
    def preview(did:str,fid:str):
        _,row,path=service.store.file(did,fid);preview=path.with_name('preview.png')
        if not row.get('raster') or not preview.is_file():fail('FILE_NOT_FOUND','No bounded raster preview is available.')
        return FileResponse(preview,media_type='image/png',headers={'Cache-Control':'no-store'})
    @router.post('/{did}/cancel-upload')
    def cancel_upload(did:str):
        if service.active:fail('DATASET_BUSY','Stop the active worker before cancelling partial uploads.')
        return service.store.cancel_uploads(did)
    @router.post('/{did}/inspect',status_code=202)
    async def inspect(did:str,request:Request):return service.submit(did,'inspect',await small_json(request))
    @router.post('/{did}/compatibility')
    async def compatibility(did:str,request:Request):return service.report(did,await small_json(request))
    @router.get('/{did}/compatibility.csv')
    def compatibility_csv(did:str):return Response(report_csv(service.report(did,{})),media_type='text/csv',headers={'Content-Disposition':'attachment; filename="compatibility_report.csv"'})
    @router.post('/{did}/compatibility.csv')
    async def selected_compatibility_csv(did:str,request:Request):return Response(report_csv(service.report(did,await small_json(request))),media_type='text/csv',headers={'Content-Disposition':'attachment; filename="compatibility_report.csv"'})
    @router.post('/{did}/analyze',status_code=202)
    async def analyze(did:str,request:Request):return service.submit(did,'analyze',await small_json(request))
    @router.post('/{did}/evaluate',status_code=202)
    async def evaluate_route(did:str,request:Request):return service.submit(did,'evaluate',await small_json(request))
    app.include_router(router);app.add_event_handler('shutdown',service.close)
    return service
