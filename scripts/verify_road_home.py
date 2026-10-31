"""Genuine saved-run route checks; no new scientific accuracy or source recalculation."""
from datetime import datetime,timezone
from urllib.request import urlopen,Request
from urllib.error import HTTPError
from pathlib import Path
import hashlib,io,json,time,subprocess,sys
from PIL import Image
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from jai_extension.investigation import verify_trace

base='http://127.0.0.1:8768';rid='event-fe47db331390';prefix='/api/flood/runs/'+rid
checks=[]
def get(path):
 with urlopen(base+path,timeout=15) as r:return json.load(r)
def post(path,data):
 with urlopen(Request(base+path,json.dumps(data).encode(),{'Content-Type':'application/json'},method='POST'),timeout=15) as r:return json.load(r)
def ok(name,condition):
 assert condition,name
 checks.append({'check':name,'result':'PASS'})
run=get(prefix);s=run['summary'];d=get(prefix+'/debris')
ok('verified source identity and saved freeze',run['integrity']=='RESULT_AND_MANIFEST_VERIFIED' and run['freeze_sha256']=='ff6bb25ef3713d128bad95d9b44af0c33b0429ce6c767df6ac4c06524c3adb0e')
ok('separate exact source summary values',s['new_water_m2']==95600 and s['exposed_buildings']==2 and abs(s['exposed_road_m']-185.8461137204373)<1e-10 and s['debris_candidate_m2']==104100 and s['debris_intersected_buildings']==71 and abs(s['debris_intersected_road_m']-1458.9344344663516)<1e-10)
ok('separate valid coverage populations',s['valid_pixels']==99858 and s['debris_valid_pixels']==30239 and d['coverage']['invalid_pixels']==80759)
ok('native TIFF counts match source',d['coverage']['candidate_pixels']==1041 and d['coverage']['valid_pixels']==30239 and d['coverage']['pixel_area_m2']==100)
water=get(prefix+'/exposure')
ok('independent infrastructure tables retained',water['layer']=='water' and len(d['rows'])==len(water['rows']) and sum(r['kind']=='building' and r['exposed']>0 for r in d['rows'])==71)
ok('not-assessed access never rendered zero affected',s['connectivity_status']=='NOT_ASSESSED' and 'potentially_cut_off' not in s)
grid=get(prefix+'/grid')
ok('same native grid proved before both-layer comparison',all(grid[k]==d['grid'][k] for k in ('crs','transform','width','height')))
ok('optical and SAR dates remain distinct',d['provenance']['pre_date']=='2026-08-22' and d['provenance']['post_date']=='2026-08-27' and run['provenance']['inputs'][0]['datetime'].startswith('2026-08-16') and run['provenance']['inputs'][1]['datetime'].startswith('2026-08-28'))
absent=get('/api/flood/runs/auto-syapru-001/debris')
ok('genuine water-only run keeps debris NOT_ASSESSED',absent['status']=='NOT_ASSESSED' and not absent['debris_available'] and absent['summary']=={})
downloads={}
for name in (a['name'] for a in run['artifacts']):
 with urlopen(base+prefix+'/artifact/'+name) as r:
  raw=r.read();sha=hashlib.sha256(raw).hexdigest();ok('download hash '+name,sha==r.headers['X-Artifact-SHA256'] and sha==next(a['sha256'] for a in run['artifacts'] if a['name']==name));downloads[name]={'sha256':sha,'bytes':len(raw)}
  if name.endswith('.png'):
   with Image.open(io.BytesIO(raw)) as im:
    ok('native dated SAR display dimensions '+name,im.size==(254,437))
with urlopen(base+prefix+'/debris-candidate.png') as r:
 raw=r.read();header=r.headers['X-Source-SHA256']
 with Image.open(io.BytesIO(raw)) as image:
  ok('actual native debris preview and hash header',image.size==(254,437) and header==d['source_hashes']['debris-candidates.tif'])
question='Which mapped buildings and roads intersect water or possible debris-change candidates, and what can we verify?'
job=post('/api/investigations',{'question':question,'run_id':rid,'scene_id':'terrain-45737e0da2983d9d'})
for _ in range(200):
 job=get('/api/investigations/'+job['id'])
 if job['state'] in ('complete','abstained','failed','cancelled'):break
 time.sleep(.05)
ok('real supported investigation completes',job['state']=='complete')
verify_trace(job['trace']);ok('hash-linked debris tool trace',any(t['tool']=='get_debris_evidence' for t in job['trace']))
claims={c['field']:c['value'] for c in job['result']['claims']}
ok('question claims use separate source values',claims['/summary/debris_intersected_buildings']==71 and claims['/summary/exposed_buildings']==2 and claims['/summary/debris_valid_pixels']==30239)
for question in ('Estimate flood depth','Which road is safe for evacuation?','How many destroyed buildings?','Predict landslide risk','Assess road safety'):
 j=post('/api/investigations',{'question':question,'run_id':rid})
 for _ in range(100):
  j=get('/api/investigations/'+j['id'])
  if j['state'] in ('complete','abstained','failed','cancelled'):break
  time.sleep(.03)
 ok('unsupported question abstains: '+question,j['state']=='abstained' and j['result']['claims']==[])
try:
 urlopen(Request(base+prefix+'/debris',headers={'Origin':'https://foreign.invalid'}),timeout=5)
 raise AssertionError('Foreign origin accepted')
except HTTPError as e:ok('origin protection preserved',e.code==403)
receipt={'recorded_utc':datetime.now(timezone.utc).isoformat(),'source_revision':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),'source_file_sha256':{n:hashlib.sha256(Path(n).read_bytes()).hexdigest() for n in ('jai_extension/flood_bridge.py','jai_extension/investigation.py','jai_extension/server.py')},'scope':'Genuine already-saved Nepal data, route/integrity regression only. No new accuracy evaluation.','checks':checks,'run':rid,'freeze_sha256':run['freeze_sha256'],'summary':s,'debris_coverage':d['coverage'],'downloads':downloads,'question_job':job['id'],'planned_tools':job['result']['planned_tools'],'trace_verified':True}
out=Path('.runtime/jai/road-home');out.mkdir(exist_ok=True)
(out/'HTTP_RECEIPT.json').write_text(json.dumps(receipt,indent=2))
(out/'SUPPORTED_QUESTION.json').write_text(json.dumps(job,indent=2))
(out/'DEBRIS_RESPONSE.json').write_text(json.dumps(d,indent=2))
print(json.dumps({'passed':len(checks),'question_job':job['id'],'summary':s,'coverage':d['coverage']},indent=2))
