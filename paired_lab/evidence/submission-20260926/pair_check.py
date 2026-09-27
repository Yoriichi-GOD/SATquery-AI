from pathlib import Path
import sys,json,datetime
ROOT=Path('/mnt/c/Users/nrgen/.codex/scratch/SATquery AI')
sys.path[:0]=[str(ROOT/'paired_lab'),str(ROOT)]
from inputs import inspect,validate
import controller
OUT=Path(__file__).resolve().parent
a=json.loads((OUT/'cartosat-mx-inventory.json').read_text())
b=json.loads((OUT/'eos04-frs2-inventory.json').read_text())
ab=a['rasters'][0]['bounds_wgs84'];bb=b['rasters'][0]['bounds_wgs84']
overlap=max(ab[0],bb[0])<min(ab[2],bb[2]) and max(ab[1],bb[1])<min(ab[3],bb[3])
result={'cartosat_bounds_wgs84':ab,'eos04_bounds_wgs84':bb,'bounding_boxes_overlap':overlap,'date_gap_days':(datetime.date(2023,9,13)-datetime.date(2020,5,16)).days,'checks':[]}
records=[]
for stem,modality,date,sensor in [('cartosat-mx','optical','2020-05-16','CARTOSAT-2E'),('eos04-frs2','sar','2023-09-13','EOS-04')]:
 try:
  r=inspect(OUT/(stem+'-native-crop.tif'),modality,date)
  r['sensor']=sensor # Exact sidecar identity; do not impersonate Sentinel.
  records.append(r)
 except ValueError as e:result['checks'].append({'check':stem+' inspect','outcome':'refused','reason':str(e)})
if len(records)==2:
 for task in ['water_map','optical_sar']:
  try:validate(records,task);row={'task':task,'outcome':'accepted'}
  except ValueError as e:row={'task':task,'outcome':'refused','reason':str(e)}
  result['checks'].append(row)
 for question in ['Map water in this pair.','Identify land cover.']:
  try:row={'query':question,'plan':controller.plan(question,records),'note':'Planning does not imply input validation or successful inference.'}
  except ValueError as e:row={'query':question,'outcome':'refused','reason':str(e)}
  result['checks'].append(row)
(OUT/'pair-results.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
