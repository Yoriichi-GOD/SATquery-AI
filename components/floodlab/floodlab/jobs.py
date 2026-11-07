"""Single-worker event jobs with persisted, non-sensitive status."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from threading import Lock
from datetime import date,datetime,timezone
import json,uuid
from fastapi import APIRouter,HTTPException
from pydantic import BaseModel,Field,field_validator
from .event_acquisition import validate_area,discover,acquire
from .automatic import prepare
from .pipeline import run
from .automatic_topology import attach_topology
from .automatic_optical import attach_optical
ROOT=Path(__file__).resolve().parents[1]
router=APIRouter();pool=ThreadPoolExecutor(max_workers=1);lock=Lock();active=None
class EventRequest(BaseModel):
 bbox:list[float]=Field(min_length=4,max_length=4)
 event_date:date
 @field_validator('bbox')
 @classmethod
 def area(cls,v):validate_area(v);return v
 @field_validator('event_date')
 @classmethod
 def past(cls,v):
  if v>=datetime.now(timezone.utc).date():raise ValueError('Choose a past event date with available post-event observations')
  return v

def write_status(job,state,message):
 folder=ROOT/'data/jobs';folder.mkdir(parents=True,exist_ok=True)
 path=folder/(job+'.json');now=datetime.now(timezone.utc).isoformat()
 previous=json.loads(path.read_text()) if path.exists() else {}
 events=previous.get('events',[])
 if not events or events[-1].get('state')!=state or events[-1].get('message')!=message:
  events.append({'state':state,'message':message,'at':now})
 payload={'job_id':job,'state':state,'message':message,'created_at':previous.get('created_at',now),'updated_at':now,'events':events[-80:],'run_id':job if state=='complete' else None}
 temp=path.with_suffix('.tmp');temp.write_text(json.dumps(payload));temp.replace(path)
 return payload

def execute(job,q):
 global active
 try:
  write_status(job,'running','Finding compatible pre/post satellite scenes')
  plan=discover(q.bbox,q.event_date.isoformat())
  root=ROOT/'data/automatic'/job
  acquire(plan,root,ROOT/'.env.local',lambda msg:write_status(job,'running',msg))
  write_status(job,'running','Preparing observations and acquiring historical infrastructure')
  manifest=prepare(root,ROOT/'.env.local')
  manifest=attach_topology(root,lambda msg:write_status(job,'running',msg))
  manifest=attach_optical(root,ROOT/'.env.local',lambda msg:write_status(job,'running',msg))
  write_status(job,'running','Calculating water candidates and infrastructure exposure')
  run(manifest,ROOT/'artifacts/runs'/job)
  write_status(job,'complete','Evidence saved. Debris coverage and road access may be incomplete; inspect the run limitations.')
 except Exception as error:
  # Provider exceptions may contain request URLs; never expose arbitrary exception text.
  write_status(job,'failed','Run failed during acquisition or validation ('+type(error).__name__+'). Partial inputs retained; no completed result claimed.')
 finally:
  with lock:active=None

@router.post('/api/event-jobs',status_code=202)
def submit(q:EventRequest):
 global active
 with lock:
  if active is not None:raise HTTPException(409,'A run is already processing. Wait for it to finish.')
  job='event-'+uuid.uuid4().hex[:12];active=job
  status=write_status(job,'queued','Waiting to acquire satellite observations')
  pool.submit(execute,job,q)
 return status

@router.get('/api/event-jobs/{job}')
def status(job:str):
 import re
 if not re.fullmatch(r'event-[a-f0-9]{12}',job):raise HTTPException(404)
 path=ROOT/'data/jobs'/(job+'.json')
 if not path.exists():raise HTTPException(404)
 payload=json.loads(path.read_text())
 if payload['state'] in ('queued','running') and active!=job:
  message='Server restarted before completion. Partial inputs retained; start a new run.'
  payload.update(state='interrupted',message=message)
  payload['events']=(payload.get('events',[])+[{'state':'interrupted','message':message,'at':datetime.now(timezone.utc).isoformat()}])[-80:]
 return payload
