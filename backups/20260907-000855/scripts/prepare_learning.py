import json,random,hashlib,zipfile,collections
from pathlib import Path
from PIL import Image
p=Path('/root/satquery/data');rng=random.Random(26167)
load=lambda kind:[r for r in json.loads((p/f'LR_split_train_{kind}.json').read_text())[kind] if r.get('active')]
images=load('images');answers={r['id']:r for r in load('answers')};questions=load('questions')
scene=lambda r:r['original_name'].rsplit('_',1)[0]
test=[r for r in json.loads(Path('/root/satquery/evaluation/LR_split_test_images.json').read_text())['images'] if r.get('active')]
testscenes=set(map(scene,test));assert not testscenes.intersection(map(scene,images))
devscene=next(scene(r) for r in images if 'T31UGS_' in r['original_name'])
train=[r for r in images if scene(r)!=devscene];dev=[r for r in images if scene(r)==devscene];rng.shuffle(train);rng.shuffle(dev)
selected={'train':train[:120],'dev':dev[:20]};manifest={}
with zipfile.ZipFile('/root/satquery/evaluation/Images_LR.zip') as z:
 names={Path(n).name:n for n in z.namelist() if n.endswith('.tif')}
 for split,ims in selected.items():
  rows=[];(p/split).mkdir(exist_ok=True)
  for im in ims:
   target=p/split/f'{im["id"]}.png'
   with z.open(names[str(im['id'])+'.tif']) as f:Image.open(f).convert('RGB').save(target)
   for typ,count in [('rural_urban',1),('presence',2 if split=='train' else 1),('comp',3 if split=='train' else 1)]:
    pool=[q for q in questions if q['img_id']==im['id'] and q['type']==typ];rng.shuffle(pool)
    for q in pool[:count]:
     a=answers[q['answers_ids'][0]];assert a['question_id']==q['id']
     rows.append({'image':str(target),'image_id':im['id'],'question_id':q['id'],'question':q['question'],'answer':a['answer'],'category':typ,'source_scene':scene(im),'split':split,'image_sha256':hashlib.sha256(target.read_bytes()).hexdigest()})
  rng.shuffle(rows);content=''.join(json.dumps(r)+'\n' for r in rows);out=p/f'{split}.jsonl'
  if out.exists():assert out.read_text()==content
  else:out.write_text(content)
  manifest[split]={'questions':len(rows),'images':len(ims),'source_scenes':sorted(set(map(scene,ims))),'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'answers':dict(collections.Counter(r['category']+':'+r['answer'] for r in rows))}
trainrows=[json.loads(x) for x in (p/'train.jsonl').read_text().splitlines()];devrows=[json.loads(x) for x in (p/'dev.jsonl').read_text().splitlines()]
assert not {r['image_sha256'] for r in trainrows}&{r['image_sha256'] for r in devrows}
testhashes={hashlib.sha256(f.read_bytes()).hexdigest() for f in Path('/root/satquery/evaluation/images').glob('*.png')}
assert not testhashes&{r['image_sha256'] for r in trainrows+devrows}
manifest.update(source='https://zenodo.org/records/6344334',seed=26167,notes='Train/dev sampled only from official training split; development source scene wholly excluded from training. Official test scene excluded. Scene disjointness is not proof of zero spatial adjacency. Published labels may be noisy. No test answers used for adaptation.')
(p/'learning_manifest.json').write_text(json.dumps(manifest,indent=2));print(json.dumps(manifest,indent=2))
