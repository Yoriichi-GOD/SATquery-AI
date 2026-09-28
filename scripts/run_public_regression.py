"""Run fixed, reused public-image cases through the current unified API.

This is a regression subset, not full benchmark or untouched acceptance evidence.
Exact match is a diagnostic, not VRSBench's published GPT-judged metric.
"""
import argparse, hashlib, io, json, re, subprocess, sys, time, zipfile
from pathlib import Path
import requests

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def norm(s): return re.sub(r'[.!?]+$', '', ' '.join(str(s).lower().strip().split()))
def save(p, x): p.write_text(json.dumps(x, indent=2))

def scoring_context(dataset):
    return {
        'metric_name': 'normalized_whole_response_exact_match_diagnostic',
        'definition': 'Lowercase and collapse whitespace; remove terminal .!?; compare the entire presented answer with the short reference. Refusals/errors count as non-matches.',
        'interpretation': 'Exact-response matches are not semantic correctness. Explanatory text and appended presentation disclaimers can prevent matching a correct short answer; genuinely wrong answers and refusals also contribute.',
        'semantic_accuracy': None,
        'semantic_review_status': 'Not scored; no retrospective replacement accuracy computed.',
        'published_benchmark_score': False,
        'scope': 'Reused-image regression subset, not a full benchmark or untouched acceptance set.',
        'readme': 'README.md',
    }

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,required=True);args=ap.parse_args()
    root=args.root.resolve();old=root/'paired_lab/evidence/benchmark-20260921';out=root/'paired_lab/evidence/public-benchmarks-20260927'
    out.mkdir(exist_ok=True);rowsfile=out/'rows.jsonl'
    if rowsfile.exists(): raise RuntimeError('Preserve previous results: choose a fresh output directory before another run.')
    cases=[];ims={p.name:p for p in (old/'vrs-inputs').glob('*.png')}
    for q in json.loads((out/'VRSBench_EVAL_vqa.json').read_text()):
        if q['image_id'] in ims:
            cases.append(dict(dataset='VRSBench',image=str(ims[q['image_id']]),question_id=q['question_id'],question=q['question'],reference=q['ground_truth'],category=q['type']))
    for filename in ['vqa-manifest.json','presence-manifest.json']:
        for c in json.loads((old/filename).read_text())['cases']:
            cases.append(dict(dataset='RSVQA-LR',image=str(old/'vqa-inputs'/f"{c['image_id']}.png"),question_id=c.get('question_id'),question=c['question'],reference=c['reference'],category=c.get('category','presence')))
    for c in cases:c['sha256']=sha(Path(c['image']))
    assert len(cases)==77, len(cases)
    snapshot={str(p.relative_to(root)):sha(p) for p in root.rglob('*.py') if '.git' not in p.parts and 'evidence' not in p.parts and 'backups' not in p.parts}
    save(out/'manifest.json',dict(cases=cases,code_sha256=snapshot,labels_sha256=sha(out/'VRSBench_EVAL_vqa.json'),vrs_revision='6cee2968fd752a6d51c6cb2d18dded2bc0baa218',scope='45 original VRSBench questions on 12 previously used images; 32 existing RSVQA regression questions on 16 shared images. Not untouched or full benchmarks. Model pretraining exposure unknown. Rural/urban question wording retains previous adapted prompt. No model or threshold changes during run.',scoring='lowercase, whitespace normalization, terminal .!? removal; exact string equality; refusals/errors count incorrect. VRSBench published GPT-judge score is NOT computed.'))
    children=[];logs=[];base='http://127.0.0.1:8767';rows=[]
    try:
        for port,folder in [(8765,root),(8767,root/'paired_lab')]:
            try:
                if requests.get(f'http://127.0.0.1:{port}/api/status',timeout=2).ok:raise RuntimeError(f'Port {port} already occupied; stop here to avoid testing an unknown server revision.')
            except requests.ConnectionError:pass
            log=(out/f'service-{port}.log').open('w');logs.append(log)
            p=subprocess.Popen([sys.executable,'-m','uvicorn','server:app','--app-dir',str(folder),'--host','127.0.0.1','--port',str(port),'--no-access-log'],stdout=log,stderr=subprocess.STDOUT);children.append(p)
            for _ in range(120):
                if p.poll() is not None:raise RuntimeError(f'Server {port} failed')
                try:
                    if requests.get(f'http://127.0.0.1:{port}/api/status',timeout=1).ok:break
                except requests.RequestException:pass
                time.sleep(.5)
            else:raise RuntimeError('Server startup timeout')
        save(out/'status.json',requests.get(base+'/api/status',timeout=10).json())
        for i,c in enumerate(cases):
            start=time.perf_counter();row=dict(c)
            try:
                image=Path(c['image']);raw=image.read_bytes()
                r=requests.post(base+'/api/single-images',files={'file':(image.name,raw)},timeout=60);r.raise_for_status()
                r=requests.post(base+'/api/analyze',json={'images':[r.json()['id']],'query':c['question'],'threshold':.5},timeout=60)
                if not r.ok:
                    row.update(state='refused' if r.status_code<500 else 'error',http_status=r.status_code,detail=r.json())
                else:
                    job=r.json();deadline=time.monotonic()+660
                    while time.monotonic()<deadline:
                        r=requests.get(base+'/api/jobs/'+job['id'],timeout=30);r.raise_for_status();d=r.json()
                        if d['state'] in ['complete','failed']:break
                        time.sleep(.3)
                    else:raise TimeoutError('Analysis exceeded 660 seconds')
                    row.update(state=d['state'],run=d,answer=d.get('result',{}).get('answer',''))
                    if d['state']=='complete':
                        r=requests.get(base+'/api/runs/'+job['id']+'/evidence.zip',timeout=60);r.raise_for_status()
                        archive=out/'artifacts'/f'{i:03d}-{job["id"]}.zip';archive.parent.mkdir(exist_ok=True);archive.write_bytes(r.content)
                        with zipfile.ZipFile(io.BytesIO(r.content)) as z:
                            originals=[n for n in z.namelist() if n.startswith('input-1.')]
                            row['archive_original_verified']=z.testzip() is None and len(originals)==1 and z.read(originals[0])==raw
                            if 'main-raw-result.json' in z.namelist():row['raw_specialist']=json.loads(z.read('main-raw-result.json'))
                        row['archive_sha256']=sha(archive)
            except Exception as e:row.update(state='error',error=f'{type(e).__name__}: {e}')
            row['end_to_end_seconds']=time.perf_counter()-start
            row['exact_match']=row.get('state')=='complete' and norm(row.get('answer',''))==norm(c['reference'])
            rows.append(row)
            with rowsfile.open('a') as f:f.write(json.dumps(row)+'\n')
            print(i+1,len(cases),c['dataset'],row['state'],repr(row.get('answer',row.get('detail',row.get('error')))),flush=True)
        summary={}
        for ds in sorted({r['dataset'] for r in rows}):
            subset=[r for r in rows if r['dataset']==ds]
            summary[ds]={'n':len(subset),'complete':sum(r['state']=='complete' for r in subset),'exact_match':sum(r['exact_match'] for r in subset),'states':{s:sum(r['state']==s for r in subset) for s in sorted({r['state'] for r in subset})},'categories':{cat:{'n':sum(r['category']==cat for r in subset),'exact_match':sum(r['exact_match'] for r in subset if r['category']==cat)} for cat in sorted({r['category'] for r in subset})}}
        for ds in summary: summary[ds]['scoring_context']=scoring_context(ds)
        save(out/'summary.json',summary);print(json.dumps(summary),flush=True)
    finally:
        for p in children:
            if p.poll() is None:p.terminate()
        for p in children:
            try:p.wait(timeout=15)
            except subprocess.TimeoutExpired:p.kill();p.wait()
        for log in logs:log.close()

if __name__=='__main__':main()
