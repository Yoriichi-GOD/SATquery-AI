"""Deterministic, bounded tool orchestration over saved evidence; no LLM used."""
from __future__ import annotations

import copy
import hashlib
import json
import re
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

from jai_extension.flood_bridge import BridgeError,FloodBridge
from jai_extension.geo_context import GeoContext

REGISTRY={
    'get_run':'Verified saved summary, dates and artifact identities',
    'get_exposed_assets':'Verified historical feature intersections; not damage',
    'get_debris_evidence':'Verified possible debris/surface-change proxy, its own coverage and intersections; not damage',
    'get_dem':'Verified cached DSM statistics and source identities',
    'analyze_coverage':'Actual reprojection and shared valid support',
    'terrain_transect':'Bilinear metric profile with missing-data gaps',
}
TERMINAL={'complete','abstained','cancelled','failed','interrupted'}


def utc():return datetime.now(timezone.utc).isoformat()
def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,allow_nan=False,separators=(',',':')).encode()).hexdigest()


def verify_trace(entries):
    previous='0'*64
    for entry in entries:
        if (entry['previous_event_sha256']!=previous or entry['output_sha256']!=digest(entry['output']) or
                entry['event_sha256']!=digest({k:v for k,v in entry.items() if k!='event_sha256'})):
            raise ValueError('Trace integrity mismatch')
        previous=entry['event_sha256']


def plan(question):
    text=question.lower()
    if re.search(r'\b(depth|casualt\w*|death\w*|evacuat\w*|predict\w*|forecast\w*|confidence|probability|accuracy|safe|safest|damage|damaged|destroyed|guarantee|risk|closed|closure|cut off)\b|ignore.*instruction|system prompt|\b(send|email|publish|delete|execute|download|acquire)\b',text):
        return [],'The saved evidence cannot establish depth, damage, safety, forecasts or casualties, or perform external actions. Ask about observed candidates, recorded intersections or terrain.'
    terrain=bool(re.search(r'\b(terrain|slope|elevation|dem|height|hill|mountain|coverage|overlap|align\w*)\b',text))
    assets=bool(re.search(r'\b(road\w*|building\w*|asset\w*|infrastructure|inspect\w*|exposure|intersect\w*)\b',text))
    water=bool(re.search(r'\b(water|flood|candidate\w*|summary|situation)\b',text))
    debris=bool(re.search(r'\b(debris|landslide\w*|surface[ -]change\w*)\b',text))
    profile=bool(re.search(r'\b(transect|profile|cross.section)\b',text))
    if profile:return ['get_dem','terrain_transect'],None
    if not any([terrain,assets,water,debris]):return [],'Supported questions cover saved water and possible debris/surface-change candidates, road/building intersections, terrain and metric profiles.'
    tools=[]
    if water or assets or debris:tools.append('get_run')
    if assets:tools.append('get_exposed_assets')
    if debris:tools.append('get_debris_evidence')
    if terrain:tools.append('get_dem')
    if terrain and (water or assets):tools.append('analyze_coverage')
    return tools,None


class InvestigationEngine:
    def __init__(self,bridge,terrain):self.bridge,self.terrain=bridge,terrain

    def execute(self,payload,check,record):
        tools,refusal=plan(payload['question'])
        if refusal:return {'state':'abstained','answer':refusal,'claims':[],'sources':[],'planned_tools':[],'mode':'DETERMINISTIC_TOOL_WORKFLOW','ai_model_used':False}
        if 'get_dem' in tools and not payload.get('scene_id'):
            return {'state':'abstained','answer':'Select an available cached terrain scene first. No acquisition was performed.','claims':[],'sources':[],'planned_tools':tools}
        if 'get_run' in tools and not payload.get('run_id'):
            return {'state':'abstained','answer':'Select a saved flood run first.','claims':[],'sources':[],'planned_tools':tools}
        if 'terrain_transect' in tools and not payload.get('profile'):
            return {'state':'abstained','answer':'Provide the two projected metric profile endpoints first.','claims':[],'sources':[],'planned_tools':tools}
        output={};sources=[]
        geo=GeoContext(self.bridge,self.terrain)
        for name in tools:
            check();started=time.perf_counter()
            if name=='get_run':
                value=self.bridge.detail(payload['run_id'])
                if value['population']!='FROZEN_REAL_OBSERVATION':
                    raise BridgeError(422,'Choose a genuine saved observation; synthetic fixtures are a separate population')
                years=set(re.findall(r'\b20\d{2}\b',payload['question']))
                event=value['provenance'].get('event_time') or ''
                if years and years!={event[:4]}:
                    record(name,{'status':'DATE_MISMATCH','available_event_time':event},time.perf_counter()-started)
                    return {'state':'abstained','answer':'Requested year does not match the selected saved event ('+event+'). Select matching evidence.','claims':[],'sources':[],'planned_tools':tools}
                value=copy.deepcopy(value)
                sources.append({'label':'Frozen run summary','url':f"/api/flood/runs/{payload['run_id']}/artifact/result.json",'sha256':next(a['sha256'] for a in value['artifacts'] if a['name']=='result.json')})
            elif name=='get_exposed_assets':
                value=self.bridge.exposure(payload['run_id'])
                expected=next(a['sha256'] for a in output['get_run']['artifacts'] if a['name']=='exposure.csv')
                if value['source_sha256']!=expected:raise BridgeError(409,'Exposure snapshot changed during investigation')
                sources.append({'label':'Historical feature intersections','url':f"/api/flood/runs/{payload['run_id']}/artifact/exposure.csv",'sha256':value['source_sha256']})
            elif name=='get_debris_evidence':
                value=self.bridge.debris(payload['run_id'],run=output['get_run'])
                if not value['debris_available']:
                    record(name,value,time.perf_counter()-started)
                    return {'state':'abstained','answer':'Possible debris/surface change is NOT_ASSESSED for this selected run. Complete verified debris evidence is unavailable; no zero or water-only answer is substituted.',
                            'claims':[],'sources':sources,'planned_tools':tools,'tool_outputs':{**output,name:value},
                            'mode':'DETERMINISTIC_TOOL_WORKFLOW','ai_model_used':False}
                expected={a['name']:a['sha256'] for a in output['get_run']['artifacts']}
                for artifact in value['artifacts']:
                    if artifact['sha256']!=expected.get(artifact['name']):
                        raise BridgeError(409,'Debris snapshot changed during investigation')
                    sources.append({'label':'Possible debris · '+artifact['name'],'url':artifact['url'],'sha256':artifact['sha256']})
            elif name=='get_dem':
                full=self.terrain.scene(payload['scene_id'])
                value={k:full[k] for k in ['id','statistics','hashes','provenance','population']}
                sources.append({'label':'Cached DSM and statistics','url':f"/api/terrain/scenes/{payload['scene_id']}",'sha256':full['hashes']['analysis.tif']})
            elif name=='analyze_coverage':
                value=geo.coverage(payload['run_id'],payload['scene_id'],run=output['get_run'])
                value={k:v for k,v in value.items() if k not in ['candidate_points','classes_on_mesh','candidate_fraction_on_mesh']}
                if value['source_hashes']['analysis.tif']!=output['get_dem']['hashes']['analysis.tif']:raise BridgeError(409,'Terrain snapshot changed during investigation')
                jid=payload.get('_job_id','recorded')
                sources.append({'label':'Recorded grid coverage calculation','url':f"/api/investigations/{jid}/tools/analyze_coverage",'sha256':digest(value),'hash_kind':'canonical_json'})
            else:
                p=payload['profile'];value=geo.transect(payload['scene_id'],p['start'],p['end'],p.get('samples',128))
                jid=payload.get('_job_id','recorded')
                sources.append({'label':'Recorded terrain profile','url':f"/api/investigations/{jid}/tools/terrain_transect",'sha256':digest(value),'hash_kind':'canonical_json'})
            check();output[name]=value;record(name,value,time.perf_counter()-started)
        claims=[]
        def claim(label,value,unit,source,field):claims.append({'label':label,'value':value,'unit':unit,'source':source,'field':field})
        run=output.get('get_run')
        if run:
            for label,key,unit in [('New-water candidate area','new_water_m2','m²'),('Water intersected buildings','exposed_buildings','buildings'),('Water intersected road length','exposed_road_m','m'),('Settlement access','connectivity_status','')]:
                if key in run['summary']:claim(label,run['summary'][key],unit,0,'/summary/'+('connectivity_assessed' if key=='connectivity_status' else key))
        debris=output.get('get_debris_evidence')
        if debris:
            for label,key,unit in [('Possible debris candidate area','debris_candidate_m2','m²'),('Debris intersected buildings','debris_intersected_buildings','buildings'),('Debris intersected road length','debris_intersected_road_m','m'),('Debris valid coverage','debris_valid_pixels','pixels')]:
                claim(label,debris['summary'][key],unit,0,'/summary/'+key)
            if 'valid_pixels' in run['summary']:
                claim('Water valid coverage',run['summary']['valid_pixels'],'pixels',0,'/summary/valid_pixels')
        terrain=output.get('get_dem')
        if terrain:
            source=next(i for i,s in enumerate(sources) if s['label']=='Cached DSM and statistics')
            for label,key,unit in [('Minimum DSM height','elevation_min_m','m'),('Maximum DSM height','elevation_max_m','m'),('Median slope','slope_median_deg','degrees')]:claim(label,terrain['statistics'][key],unit,source,'/statistics/'+key)
        if 'analyze_coverage' in output:
            source=next(i for i,s in enumerate(sources) if s['label']=='Recorded grid coverage calculation')
            claim('Common valid DEM cell centres',output['analyze_coverage']['common_valid_dem_cells'],'cells',source,'/common_valid_dem_cells')
        if 'terrain_transect' in output:
            source=next(i for i,s in enumerate(sources) if s['label']=='Recorded terrain profile')
            claim('Transect length',output['terrain_transect']['length_m'],'m',source,'/length_m')
            claim('Valid transect samples',output['terrain_transect']['valid_samples'],'samples',source,'/valid_samples')
        rows=[]
        rows_by_layer={}
        if 'get_exposed_assets' in output:
            selected=[r for r in output['get_exposed_assets']['rows'] if r['status'] in ['exposed','unknown']]
            rows=sorted(selected,key=lambda r:(r['status']!='exposed',-r['exposed']))[:30]
            rows_by_layer['water']=rows
        if debris:
            selected=[r for r in debris['rows'] if r['status'] in ['exposed','unknown']]
            rows_by_layer['debris']=sorted(selected,key=lambda r:(r['status']!='exposed',-r['exposed']))[:30]
        lines=['Measured values come from the selected saved evidence.']
        if rows:lines.append('The table lists candidate intersections and missing-coverage records for human inspection; ordering is by recorded intersection, not hazard probability.')
        if run:lines.append('These are heuristic water candidates and historical OSM intersections. They do not establish damage, actual road closure or settlement isolation.')
        if debris:lines.append('Possible debris/surface-change candidates use a fixed vegetation-to-bare, NDVI-loss and SAR-change proxy, not a trained or independently validated debris classifier. Water and debris have distinct valid coverage; counts and road lengths are not added. EMSR927 is class-mismatched checking-only evidence, not debris accuracy.')
        if terrain:lines.append('Terrain is the historical Copernicus DSM, not a flood-date measurement or a flood-depth estimate.')
        if 'analyze_coverage' in output:lines.append('Grid reprojection is checked; physical co-registration has not been independently validated.')
        return {'state':'complete','answer':' '.join(lines),'claims':claims,'sources':sources,'review_rows':rows,'review_rows_by_layer':rows_by_layer,
                'planned_tools':tools,'tool_outputs':output,'mode':'DETERMINISTIC_TOOL_WORKFLOW','ai_model_used':False}


class JobManager:
    def __init__(self,root,engine_factory):
        self.root=Path(root);self.root.mkdir(parents=True,exist_ok=True);self.engine_factory=engine_factory
        self.pool=ThreadPoolExecutor(max_workers=1);self.lock=threading.RLock();self.jobs={};self.cancel_events={};self.active=None
        for path in self.root.glob('investigation-*.json'):
            try:
                item=json.loads(path.read_text(encoding='utf-8'))
                try:verify_trace(item['trace'])
                except (ValueError,KeyError,TypeError):
                    item.update(state='failed',message='Saved trace integrity check failed',error_status=409);item.pop('result',None)
                if item['state'] not in TERMINAL:item.update(state='interrupted',message='Server restarted; no completed answer claimed')
                if re.fullmatch(r'investigation-[a-f0-9]{32}',item['id']):self.jobs[item['id']]=item
            except (ValueError,KeyError):continue

    def save(self,job):
        path=self.root/(job['id']+'.json');temp=path.with_suffix('.tmp')
        temp.write_text(json.dumps(job,indent=2,allow_nan=False),encoding='utf-8');temp.replace(path)

    def submit(self,payload):
        with self.lock:
            if self.active is not None:raise BridgeError(409,'An investigation is already running; stop it or wait')
            if len(self.jobs)>=200:raise BridgeError(429,'Local investigation history is full; archive it before more jobs')
            jid='investigation-'+uuid.uuid4().hex;event=threading.Event()
            job={'id':jid,'state':'queued','created_utc':utc(),'selection':copy.deepcopy(payload),'trace':[],
                 'mode':'DETERMINISTIC_TOOL_WORKFLOW','ai_model_used':False,'message':'Queued bounded saved-evidence workflow'}
            self.jobs[jid]=job;self.cancel_events[jid]=event;self.active=jid;self.save(job)
            self.pool.submit(self.execute,jid,event);return copy.deepcopy(job)

    def execute(self,jid,event):
        started=time.perf_counter()
        def check():
            if event.is_set():raise BridgeError(499,'Investigation cancelled')
            if time.perf_counter()-started>45:raise BridgeError(504,'Investigation exceeded 45-second time limit')
        def record(name,output,seconds):
            with self.lock:
                check();job=self.jobs[jid];previous=job['trace'][-1]['event_sha256'] if job['trace'] else '0'*64
                entry={'tool':name,'at_utc':utc(),'seconds':seconds,'output_sha256':digest(output),'previous_event_sha256':previous,'output':output}
                entry['event_sha256']=digest(entry);job['trace'].append(entry);self.save(job)
        try:
            with self.lock:self.jobs[jid].update(state='running',message='Executing bounded tools');self.save(self.jobs[jid])
            check();engine=self.engine_factory(check)
            result=engine.execute({**self.jobs[jid]['selection'],'_job_id':jid},check,record)
            with self.lock:
                check();self.jobs[jid].update(state=result['state'],result=result,message='Workflow '+result['state'])
        except BridgeError as error:
            with self.lock:
                cancelled=event.is_set() or error.status==499
                self.jobs[jid].update(state='cancelled' if cancelled else 'failed',message='Investigation cancelled' if cancelled else error.message,error_status=499 if cancelled else error.status)
        except Exception:
            with self.lock:
                cancelled=event.is_set()
                self.jobs[jid].update(state='cancelled' if cancelled else 'failed',message='Investigation cancelled' if cancelled else 'Tool execution failed; no completed answer claimed',error_status=499 if cancelled else 500)
        finally:
            with self.lock:
                self.jobs[jid]['finished_utc']=utc();self.jobs[jid]['seconds']=time.perf_counter()-started
                self.save(self.jobs[jid]);self.active=None

    def get(self,jid):
        if not re.fullmatch(r'investigation-[a-f0-9]{32}',jid):raise BridgeError(404,'Unknown investigation')
        with self.lock:
            if jid not in self.jobs:raise BridgeError(404,'Unknown investigation')
            return copy.deepcopy(self.jobs[jid])

    def cancel(self,jid):
        with self.lock:
            value=self.get(jid)
            if value['state'] not in TERMINAL:
                self.cancel_events[jid].set();self.jobs[jid].update(state='cancelling',message='Stopping; any in-flight local HTTP read has a bounded timeout');self.save(self.jobs[jid])
            return self.get(jid)

    def tool_output(self,jid,tool):
        if tool not in REGISTRY:raise BridgeError(404,'Unknown tool output')
        job=self.get(jid)
        try:verify_trace(job['trace'])
        except (ValueError,KeyError,TypeError):raise BridgeError(409,'Recorded tool trace integrity check failed') from None
        entry=next((e for e in job['trace'] if e['tool']==tool),None)
        if entry is None:raise BridgeError(404,'Tool has no recorded output in this investigation')
        return entry['output'],entry['output_sha256']

    def close(self):self.pool.shutdown(wait=True,cancel_futures=True)
