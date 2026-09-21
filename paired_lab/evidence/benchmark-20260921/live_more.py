from pathlib import Path
import json,random,re,time
from live_vqa import run,save,OUT,DATA
manifest=json.loads((OUT/'vqa-manifest.json').read_text());ids={c['image_id']:c for c in manifest['cases']};qs=json.loads((DATA/'LR_split_test_questions.json').read_text())['questions'];ans={r['id']:r for r in json.loads((DATA/'LR_split_test_answers.json').read_text())['answers']};rng=random.Random(20260921);cases=[]
for iid,c in ids.items():
 pool=[q for q in qs if q.get('active') and q['img_id']==iid and q['type']=='presence' and not re.search(r'commercial|residential|left|right|top|bottom|medium|small|large',q['question'])]
 if pool:
  q=rng.choice(pool);cases.append({'image':c['image'],'image_id':iid,'question':q['question'],'reference':ans[q['answers_ids'][0]]['answer']})
save('presence-manifest.json',{'cases':cases,'scope':'One fixed presence question per available newly selected RSVQA image. Images shared with classification subset, not additional independent scenes.'})
for i,c in enumerate(cases):
 d=run(Path(c['image']),c['question']);answer=d.get('result',{}).get('answer','');normal=re.sub(r'[.!?]+$','',' '.join(answer.lower().strip().split()));row={**c,'run':d,'normalized':normal,'exact_correct':normal==c['reference']}
 with (OUT/'presence-rows.jsonl').open('a') as f:f.write(json.dumps(row)+'\n')
 print('presence',i+1,repr(answer),flush=True)
for i,c in enumerate(json.loads((OUT/'vrs-manifest.json').read_text())['cases']):
 d=run(OUT/'vrs-inputs'/c['image_id'],'Describe this image in detail.');row={**c,'run':d}
 with (OUT/'description-rows.jsonl').open('a') as f:f.write(json.dumps(row)+'\n')
 print('caption',i+1,d['state'],d.get('result',{}).get('answer',''),flush=True)
