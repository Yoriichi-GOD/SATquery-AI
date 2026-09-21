from live_vqa import *
import numpy as np
def launch(payload):
 t=time.perf_counter();r=requests.post(BASE+'/api/analyze',json=payload,timeout=60);r.raise_for_status();jid=r.json()['id']
 for _ in range(1800):
  d=requests.get(BASE+'/api/jobs/'+jid).json()
  if d['state'] in ['complete','failed']:break
  time.sleep(.3)
 d['end_to_end_seconds']=time.perf_counter()-t
 if d['state']=='complete':
  raw=requests.get(BASE+'/api/runs/'+jid+'/evidence.zip').content;z=zipfile.ZipFile(io.BytesIO(raw));d['zip_valid']=z.testzip() is None;(OUT/'live-artifacts'/(jid+'.zip')).write_bytes(raw)
 return d
def iou(a,b):
 x=max(0,min(a[2],b[2])-max(a[0],b[0]));y=max(0,min(a[3],b[3])-max(a[1],b[1]));inter=x*y;union=(a[2]-a[0])*(a[3]-a[1])+(b[2]-b[0])*(b[3]-b[1])-inter
 return inter/union if union else 0
prior=json.loads((OUT/'vqa-rows.jsonl').read_text().splitlines()[0])['run']['result']['id']
save('restart-retrieval.json',{'job_status':requests.get(BASE+'/api/jobs/'+prior).status_code,'json_status':requests.get(BASE+'/api/runs/'+prior+'/result.json').status_code,'zip_status':requests.get(BASE+'/api/runs/'+prior+'/evidence.zip').status_code,'interpretation':'Job index is in memory; saved artifacts are addressable after restart by known run ID.'})
rows=[];catalog=requests.get(BASE+'/api/samples').json()
for kind,q in [('temporal','What changed between these dates?'),('water_map','Map water'),('optical_sar','Identify land-cover classes')]:
 sample=next(c for c in catalog if c['kind']==kind);d=launch({'sample':sample['id'],'query':q});rows.append({'kind':kind,'sample':sample['id'],'run':d});print('workflow',kind,d['state'],flush=True)
p=OUT/'ndvi-input.tif';p.write_bytes(requests.get(BASE+'/api/single-sample/ndvi').content);d=run(p,'Calculate NDVI');rows.append({'kind':'ndvi','run':d});print('workflow ndvi',d['state'],flush=True)
save('workflow-gates.json',rows)
refs=json.loads((OUT/'grounding-references.json').read_text());ground=[]
ids=sorted({r['image_id'] for r in refs if r['obj_cls']=='airplane'})
save('grounding-protocol.json',{'images':ids,'query':'Outline aircraft','metric':'Best proposal overlap with each airplane reference (oracle proposal recall, NOT referring-expression accuracy). No mask ground truth; no mask IoU. Repeated referring annotations deduplicated by image and reference box.','threshold':.5,'settings':'Unmodified production defaults; no tuning.'})
for iid in ids:
 d=run(OUT/'vrs-inputs'/iid,'Outline aircraft');width,height=Image.open(OUT/'vrs-inputs'/iid).size;seen=set();scored=[]
 for ref in refs:
  if ref['image_id']!=iid or ref['obj_cls']!='airplane':continue
  box=tuple(int(x)/100 for x in re.findall(r'\d+',ref['ground_truth']));
  if box in seen:continue
  seen.add(box);proposals=[v['box_xyxy'] for v in d.get('result',{}).get('detections',[])];norm=[[b[0]/width,b[1]/height,b[2]/width,b[3]/height] for b in proposals];best=max([iou(b,box) for b in norm],default=0);scored.append({'reference':box,'best_proposal_iou':best,'hit_at_0_5':best>=.5})
 ground.append({'image':iid,'run':d,'references':scored});save('grounding-results.json',ground);print('grounding',iid,d['state'],flush=True)
