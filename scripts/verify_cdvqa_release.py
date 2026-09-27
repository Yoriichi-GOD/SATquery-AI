import sys,json,hashlib,collections,tempfile,time,platform,subprocess
from pathlib import Path
ROOT=Path('/mnt/c/Users/nrgen/.codex/scratch/SATquery AI')
OUT=ROOT/'paired_lab/evidence/cdvqa-trained-20260928'
DATA=Path('/root/satquery/cdvqa');OLD=ROOT/'paired_lab/evidence/cdvqa-20260927'
RGB=Path('/mnt/c/Users/nrgen/.codex/visualizations/2026/09/19/01a0b9f9-b20e-71a2-b139-ca9ab926b94e/cdvqa-data/rgb')
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'paired_lab')]
from cdvqa_model import tokens,encode_questions
from predict_cdvqa import Predictor,sha
import torch
from PIL import Image

freeze=json.loads((OUT/'candidate-freeze.json').read_text())
encoder=json.loads((OUT/'encoder.json').read_text())
questions=json.loads((DATA/'Train_questions.json').read_text())['questions']
release=dict(checkpoint_sha256=freeze['checkpoints']['paired'],encoder_sha256=next(iter(encoder['checkpoint_hashes'].values())),supported_questions=sorted({' '.join(tokens(q['question'])) for q in questions if q['active']}),benchmark='CDVQA official Train/Val; final Test and Test2',main_ui_integration=False)
(DATA/'release.json').write_text(json.dumps(release,indent=2));(OUT/'release.json').write_text(json.dumps(release,indent=2))
summary=json.loads((OUT/'final-test-summary.json').read_text());checks={}
for split in ['Test','Test2']:
    rows=json.loads((OUT/(split+'-predictions.json')).read_text());folder=OLD if split=='Test' else DATA
    q={q['id']:q for q in json.loads((folder/(split+'_questions.json')).read_text())['questions'] if q['active']}
    a={a['id']:a['answer'] for a in json.loads((folder/(split+'_answers.json')).read_text())['answers']}
    images={i['id']:i['file_name'] for i in json.loads((folder/(split+'_images.json')).read_text())['images']}
    assert len(rows)==len(q)==len({r['id'] for r in rows})
    for r in rows:
        original=q[r['id']]
        assert r['question']==original['question'] and r['image']==images[original['img_id']]
        assert r['reference']==a[original['answers_ids'][0]]
    for kind in ['paired','question_only','paired_shuffled_images']:
        actual=sum(r[kind]==a[q[r['id']]['answers_ids'][0]] for r in rows)
        assert actual==summary[split]['all_official'][kind]['correct']
        groups=collections.defaultdict(list)
        for r in rows:groups[r['type']].append(r[kind]==r['reference'])
        macro=sum(sum(x)/len(x) for x in groups.values())/len(groups)
        assert abs(macro-summary[split]['all_official'][kind]['aa'])<1e-12
    checks[split]=dict(questions=len(rows),unique_pairs=len({r['image'] for r in rows}),references_and_metrics_verified=True)

start=time.perf_counter();predictor=Predictor(DATA,Path('/root/.cache/torch/hub/checkpoints/resnet50-11ad3fa6.pth'),'cuda');load_seconds=time.perf_counter()-start
cache=torch.load(DATA/'resnet50-features.pt',weights_only=True);index={n:i for i,n in enumerate(cache['names'])}
vals=json.loads((OUT/'paired-validation-predictions.json').read_text());selected=[];seen=set()
for r in vals:
    if r['image'] not in seen:selected.append(r);seen.add(r['image'])
    if len(selected)==16:break
parity=[];torch.cuda.reset_peak_memory_stats()
for r in selected:
    result=predictor.predict(RGB/'im1'/r['image'],RGB/'im2'/r['image'],r['question'],True)
    f=cache['features'][index[r['image']]].cuda()
    with torch.inference_mode(),torch.autocast('cuda',dtype=torch.bfloat16):
        logits=predictor.model(f[0:1],f[1:2],encode_questions([r['question']],predictor.ckpt['vocab']).cuda())
    expected=predictor.ckpt['answers'][logits.argmax(-1).item()]
    parity.append(dict(image=r['image'],question=r['question'],raw_input_answer=result['answer'],cached_answer=expected,match=result['answer']==expected,seconds=result['encoder_and_classifier_seconds']))
checks['raw_input_validation_replay']=parity
checks['runtime']=dict(device=torch.cuda.get_device_name(),load_seconds=load_seconds,peak_torch_allocated_bytes=torch.cuda.max_memory_allocated(),peak_torch_reserved_bytes=torch.cuda.max_memory_reserved(),parameter_count_classifier=sum(p.numel() for p in predictor.model.parameters()),parameter_count_encoder=sum(p.numel() for p in predictor.encoder.parameters()),scope='16 validation image pairs; raw RGB file loading/preprocessing not included in encoder_and_classifier_seconds; peak Torch memory includes loaded model; not process-wide GPU peak')
r=selected[0];before=RGB/'im1'/r['image'];after=RGB/'im2'/r['image']
negative={}
with tempfile.TemporaryDirectory() as d:
    gray=Path(d)/'gray.png';small=Path(d)/'small.png'
    Image.new('L',(512,512)).save(gray);Image.new('RGB',(128,128)).save(small)
    for name,b,a,q,aligned in [('unaligned',before,after,r['question'],False),('unsupported',before,after,'predict flood next week',True),('mismatched_dimensions',before,small,r['question'],True),('grayscale',gray,after,r['question'],True),('empty_question',before,after,'',True)]:
        try:predictor.predict(b,a,q,aligned)
        except ValueError as e:negative[name]=str(e)
        else:raise AssertionError('Expected refusal '+name)
checks['negative_controls']=negative
checks['software']=dict(python=platform.python_version(),torch=torch.__version__,cuda=torch.version.cuda)
assert all(r['match'] for r in parity),'Raw/cached answer discrepancy must be investigated before claiming inference parity'
(OUT/'release-verification.json').write_text(json.dumps(checks,indent=2))
print(json.dumps(dict(metric_checks=checks['Test'],test2_checks=checks['Test2'],replay_matches=sum(r['match'] for r in parity),negative_checks=len(negative),runtime=checks['runtime']),indent=2),flush=True)
