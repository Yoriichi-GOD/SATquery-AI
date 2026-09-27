"""Frozen-candidate test evaluation, including previously inspected-pair separation."""
import sys,json,hashlib,time,collections
from pathlib import Path
import numpy as np,torch
ROOT=Path('/mnt/c/Users/nrgen/.codex/scratch/SATquery AI');sys.path.insert(0,str(ROOT/'paired_lab'))
from cdvqa_model import PairedAnswerModel,encode_questions
DATA=Path('/root/satquery/cdvqa');OUT=ROOT/'paired_lab/evidence/cdvqa-trained-20260928';OLD=ROOT/'paired_lab/evidence/cdvqa-20260927'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,x):(OUT/n).write_text(json.dumps(x,indent=2))
def main():
    if (OUT/'final-test-summary.json').exists():raise RuntimeError('Final test already exists; preserve it')
    torch.set_num_threads(4);torch.manual_seed(20260928)
    training=json.loads((OUT/'training-summary.json').read_text());assert set(training)=={'paired','question_only'}
    save('candidate-freeze.json',dict(checkpoints={k:sha(DATA/(k+'-best.pt')) for k in training},selection='Checkpoints chosen exclusively by validation OA before this script reads Test/Test2 answers',code_sha256=sha(ROOT/'scripts/evaluate_cdvqa.py')))
    cache=torch.load(DATA/'resnet50-features.pt',weights_only=True);names=cache['names'];index={n:i for i,n in enumerate(names)};feat=cache['features'].cuda()
    prior=set(json.loads((OLD/'selection.json').read_text())['filenames']);models={};ckpts={}
    for kind in ['question_only','paired']:
        c=torch.load(DATA/(kind+'-best.pt'),weights_only=True);m=PairedAnswerModel(len(c['vocab'])+2,len(c['answers']),c['question_only']).cuda();m.load_state_dict(c['state_dict']);m.eval();models[kind]=m;ckpts[kind]=c
    results={}
    for split in ['Test','Test2']:
        folder=OLD if split=='Test' else DATA
        ims={i['id']:i['file_name'] for i in json.loads((folder/(split+'_images.json')).read_text())['images']};ans={a['id']:a['answer'] for a in json.loads((folder/(split+'_answers.json')).read_text())['answers']};qs=json.loads((folder/(split+'_questions.json')).read_text())['questions']
        rows=[dict(id=q['id'],image=ims[q['img_id']],question=q['question'],type=q['type'],reference=ans[q['answers_ids'][0]],previously_inspected=ims[q['img_id']] in prior) for q in qs if q['active']]
        assert all(r['image'] in index for r in rows)
        for kind in ['question_only','paired','paired_shuffled_images']:
            source='paired' if kind=='paired_shuffled_images' else kind;c=ckpts[source];m=models[source]
            image_names=sorted({r['image'] for r in rows});shuffled={n:image_names[(i+1)%len(image_names)] for i,n in enumerate(image_names)}
            ids=torch.tensor([index[shuffled[r['image']] if kind=='paired_shuffled_images' else r['image']] for r in rows],device='cuda');q=encode_questions([r['question'] for r in rows],c['vocab']).cuda();pred=[];torch.cuda.synchronize();start=time.perf_counter()
            with torch.inference_mode(),torch.autocast('cuda',dtype=torch.bfloat16):
                for b in range(0,len(rows),256):
                    ix=ids[b:b+256];pred.extend(m(feat[ix,0],feat[ix,1],q[b:b+256]).argmax(-1).tolist())
            torch.cuda.synchronize();elapsed=time.perf_counter()-start
            for r,p in zip(rows,pred):r[kind]=c['answers'][p]
            print(split,kind,len(rows),'seconds',round(elapsed,3),flush=True)
        def metrics(rr,kind):
            types=sorted({r['type'] for r in rr});by={t:dict(n=sum(r['type']==t for r in rr),correct=sum(r[kind]==r['reference'] for r in rr if r['type']==t)) for t in types}
            for x in by.values():x['accuracy']=x['correct']/x['n']
            return dict(n=len(rr),pairs=len({r['image'] for r in rr}),correct=sum(r[kind]==r['reference'] for r in rr),oa=sum(r[kind]==r['reference'] for r in rr)/len(rr),aa=float(np.mean([x['accuracy'] for x in by.values()])),by_type=by)
        result={scope:{kind:metrics(rr,kind) for kind in ['question_only','paired','paired_shuffled_images']} for scope,rr in [('all_official',rows),('excluding_12_previously_inspected_pairs',[r for r in rows if not r['previously_inspected']])]}
        # Scene-level bootstrap preserves within-pair question dependence.
        rr=[r for r in rows if not r['previously_inspected']];by=collections.defaultdict(lambda:np.zeros(3))
        for r in rr:by[r['image']]+=np.array([r['paired']==r['reference'],r['question_only']==r['reference'],1])
        arr=np.stack(list(by.values()));rng=np.random.default_rng(20260928);deltas=[]
        for _ in range(1000):
            a=arr[rng.integers(0,len(arr),len(arr))].sum(0);deltas.append((a[0]-a[1])/a[2])
        result['paired_minus_question_only_scene_bootstrap_95pct']=np.quantile(deltas,[.025,.975]).tolist()
        save(split+'-predictions.json',rows);results[split]=result
    save('final-test-summary.json',results)
    print(json.dumps({s:{scope:{m:round(v['oa'],4) for m,v in x.items()} for scope,x in r.items() if isinstance(x,dict)} for s,r in results.items()},indent=2),flush=True)
if __name__=='__main__':main()
