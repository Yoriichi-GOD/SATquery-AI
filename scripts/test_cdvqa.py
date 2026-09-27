"""Separate CDVQA route coverage, real input-contract checks, and MCI transfer probes.
No production bypasses or CDVQA leaderboard claims. Test output is immutable.
"""
import json,sys,hashlib,re,time,subprocess,collections
from pathlib import Path
import requests,numpy as np,torch
from PIL import Image
ROOT=Path('/mnt/c/Users/nrgen/.codex/scratch/SATquery AI')
OUT=ROOT/'paired_lab/evidence/cdvqa-20260927'
DATA=Path('/mnt/c/Users/nrgen/.codex/visualizations/2026/09/19/01a0b9f9-b20e-71a2-b139-ca9ab926b94e/cdvqa-data/selected')
sys.path.insert(0,str(ROOT/'paired_lab'))
import controller,mci
def save(n,x):(OUT/n).write_text(json.dumps(x,indent=2))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    if (OUT/'transfer-rows.jsonl').exists():raise RuntimeError('Preserve existing run; no overwrite')
    qs=json.loads((OUT/'Test_questions.json').read_text())['questions']
    ans={a['id']:a for a in json.loads((OUT/'Test_answers.json').read_text())['answers']}
    ims={i['id']:i for i in json.loads((OUT/'Test_images.json').read_text())['images']}
    selection=json.loads((OUT/'selection.json').read_text())['filenames']
    paths=json.loads((OUT/'selected-paths.json').read_text())
    routes=[]
    for q in qs:
        try:p=controller.plan(q['question'],[{'modality':'optical'},{'modality':'optical'}]);row=dict(id=q['id'],type=q['type'],question=q['question'],dispatch=p['task'])
        except ValueError as e:row=dict(id=q['id'],type=q['type'],question=q['question'],dispatch='refused',reason=str(e))
        routes.append(row)
    save('routing-rows.json',routes)
    save('routing-summary.json',dict(n=len(routes),scope='Intent dispatch only, before input validation; accepted does not mean executable or semantically answerable.',by_type={k:dict(collections.Counter(r['dispatch'] for r in routes if r['type']==k)) for k in sorted({r['type'] for r in routes})},nonvegetated_or_playground_accepted=sum(r['dispatch']!='refused' and bool(re.search(r'non-vegetated|playground',r['question'])) for r in routes)))
    cases=[]
    for name in selection:
        pa,pb=[DATA/paths[name][k] for k in ['im1','im2']]
        aa,bb=[np.asarray(Image.open(p).convert('RGB')) for p in [pa,pb]]
        assert aa.shape==bb.shape==(512,512,3)
        out=OUT/'inputs'/Path(name).stem;out.mkdir(parents=True,exist_ok=True)
        # Lossless container conversion only: no CRS, dates or resolutions invented.
        for arr,label in [(aa,'before'),(bb,'after')]:Image.fromarray(arr).save(out/(label+'.tif'))
        questions=[q for q in qs if ims[q['img_id']]['file_name']==name]
        binary=[q for q in questions if q['type']=='change_or_not' and re.fullmatch(r'(?:Have|Did) the (?:regions|areas) of buildings (?:changed|change)\?',q['question'])]
        case=dict(name=name,before=str(pa),after=str(pb),sha256_before=sha(pa),sha256_after=sha(pb),native_shape=list(aa.shape),question_count=len(questions),building_questions=[dict(id=q['id'],question=q['question'],reference=ans[q['answers_ids'][0]]['answer']) for q in binary])
        cases.append(case)
    save('transfer-manifest.json',dict(cases=cases,code_hashes={str(p.relative_to(ROOT)):sha(p) for p in [ROOT/'paired_lab/mci.py',ROOT/'paired_lab/controller.py',ROOT/'paired_lab/inputs.py',ROOT/'scripts/test_cdvqa.py']},protocol='Component-only exploratory transfer: full RGB images bilinearly resized 512 to 256; no crop; no CRS/dates fabricated. Existing MCI unchanged, CPU, one call per pair. Binary building-change probe is yes iff at least one building-class mask pixel; threshold fixed before inference, no tuning. Only unqualified full-pair building change-or-not questions scored; other CDVQA tasks not answered. Not the served product or published CDVQA protocol. Images selected without labels; upstream exposure unknown.',source_checkpoint=json.loads(mci.MANIFEST.read_text())))
    base='http://127.0.0.1:18767'
    log=(OUT/'contract-service.log').open('w');p=subprocess.Popen([sys.executable,'-m','uvicorn','server:app','--app-dir',str(ROOT/'paired_lab'),'--host','127.0.0.1','--port','18767','--no-access-log'],stdout=log,stderr=subprocess.STDOUT)
    contract=[]
    try:
        for _ in range(120):
            if p.poll() is not None:raise RuntimeError('Service failed')
            try:
                if requests.get(base+'/api/status',timeout=1).ok:break
            except requests.RequestException:pass
            time.sleep(.5)
        else:raise RuntimeError('Startup timeout')
        for case in cases:
            raw=Path(case['before'])
            r=requests.post(base+'/api/images',files={'file':(raw.name,raw.read_bytes())},data={'modality':'optical'},timeout=30)
            record=dict(name=case['name'],png_status=r.status_code,png_detail=r.json());ids=[]
            for label in ['before','after']:
                f=OUT/'inputs'/Path(case['name']).stem/(label+'.tif')
                r=requests.post(base+'/api/images',files={'file':(f.name,f.read_bytes())},data={'modality':'optical'},timeout=30);r.raise_for_status();ids.append(r.json()['id'])
            r=requests.post(base+'/api/analyze',json={'images':ids,'query':'Have the regions of buildings changed?'},timeout=30)
            record.update(tiff_analysis_status=r.status_code,tiff_analysis_detail=r.json());contract.append(record)
        save('input-contract.json',contract)
    finally:
        p.terminate()
        try:p.wait(timeout=15)
        except subprocess.TimeoutExpired:p.kill();p.wait()
        log.close()
    torch.set_num_threads(4);rows=[]
    for case in cases:
        row=dict(name=case['name']);start=time.perf_counter()
        try:
            images=[np.asarray(Image.open(case[k]).convert('RGB').resize((256,256),Image.Resampling.BILINEAR)) for k in ['before','after']]
            result=mci.temporal(*images,OUT/'transfer'/Path(case['name']).stem)
            prediction='yes' if result['class_pixels']['building']>0 else 'no'
            row.update(state='complete',result=result,prediction=prediction,answers=[dict(**q,correct=prediction==q['reference']) for q in case['building_questions']])
        except Exception as e:row.update(state='error',error=f'{type(e).__name__}: {e}')
        row['seconds']=time.perf_counter()-start;rows.append(row)
        with (OUT/'transfer-rows.jsonl').open('a') as f:f.write(json.dumps(row)+'\n')
        print(case['name'],row['state'],row.get('prediction'),row.get('answers',row.get('error')),flush=True)
    scored=[a for r in rows for a in r.get('answers',[])]
    save('transfer-summary.json',dict(pairs=len(rows),completed=sum(r['state']=='complete' for r in rows),eligible_questions=len(scored),correct=sum(a['correct'] for a in scored),reference_distribution=dict(collections.Counter(a['reference'] for a in scored)),scope='Exploratory component probe only; see transfer-manifest.json. No full CDVQA score. Native inputs remain unsupported by served workflow.'))

if __name__=='__main__':main()
