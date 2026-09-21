from pathlib import Path
import hashlib,json,subprocess,requests,zipfile,time
from huggingface_hub import snapshot_download,model_info
ROOT=Path('/mnt/c/Users/nrgen/.codex/scratch/SATquery AI')
LAB=ROOT/'paired_lab'; LAB.mkdir(exist_ok=True)
DATA=Path('/root/satquery/paired-lab'); DATA.mkdir(exist_ok=True)
e=LAB/'evidence'; e.mkdir(exist_ok=True)
manifest=e/'demo-before.json'
if not manifest.exists():
    files=list(ROOT.glob('*.py'))+list((ROOT/'web').rglob('*'))+list((ROOT/'grounding_lab').rglob('*.py'))+list((ROOT/'grounding_lab'/'web').rglob('*'))
    manifest.write_text(json.dumps({str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files if p.is_file()},indent=2))
(LAB/'PLAN.md').write_text('''# Paired-image lab — isolated development
The existing demo at port 8765 is frozen: no imports, routing, package updates or UI changes there.
New lab uses its own data, workers and port 8767. CPU inference initially avoids competing for demo GPU memory.

## Definition of Done
- Validate count, modality, band names, units, dates, grid compatibility and provenance before inference.
- Temporal: execute an actual paired change model; preserve both inputs, change map, score, trace and supported textual answer.
- Cross-modal: execute a jointly trained Sentinel-1/2 classifier, with S1-only and S2-only ablations on identical samples.
- Automatic dispatch based on question AND input configuration, with explicit ambiguity and unsupported-task responses.
- Real labelled positive and negative trials; save predictions and metrics, including failures. Same-image controls are not independent benchmark results.
- Interface, downloadable evidence, regression tests, and unchanged-demo hash verification.

## Boundaries
ChangeFormer binary building changes do not establish gain versus loss. BigEarthNet scene classes do not produce pixel regions.
Sentinel-1/2 models do not establish Cartosat-2S/RISAT compatibility. CDVQA performance remains unproved until evaluated.
Publisher scores are not our scores. Development samples are not an untouched benchmark. Do not train on evaluation labels.
Grounding/building-count optimisation is paused. Existing VQA/NDVI/grounding demo remains separate.
''')
src=DATA/'ChangeFormer'
if not src.exists(): subprocess.run(['git','clone','--depth','1','https://github.com/wgcban/ChangeFormer.git',str(src)],check=True)
rev=subprocess.check_output(['git','-C',str(src),'rev-parse','HEAD'],text=True).strip()
print('ChangeFormer source',rev,flush=True)
url='https://github.com/wgcban/ChangeFormer/releases/download/v0.1.0/CD_ChangeFormerV6_LEVIR_b16_lr0.0001_adamw_train_test_200_linear_ce_multi_train_True_multi_infer_False_shuffle_AB_False_embed_dim_256.zip'
dest=DATA/'changeformer-levir.zip'
if not dest.exists():
    r=requests.get(url,stream=True,timeout=60);r.raise_for_status()
    with dest.with_suffix('.partial').open('wb') as f:
        for chunk in r.iter_content(1024*1024):f.write(chunk)
    dest.with_suffix('.partial').rename(dest)
with zipfile.ZipFile(dest) as z:
    for n in z.namelist():
        if n.endswith('best_ckpt.pt'):
            with (DATA/'changeformer-levir.pt').open('wb') as f:f.write(z.read(n))
            print('extracted',n,flush=True)
models={}
for kind in ['all','s1','s2']:
    name=f'BIFOLD-BigEarthNetv2-0/resnet18-{kind}-v0.2.0'
    info=model_info(name); folder=snapshot_download(name,revision=info.sha,allow_patterns=['*.json','*.safetensors','README.md'])
    models[kind]={'repo':name,'revision':info.sha,'path':folder}
    print('Downloaded',name,flush=True)
models['temporal']={'repo':'https://github.com/wgcban/ChangeFormer','revision':rev,'path':str(DATA/'changeformer-levir.pt'),'sha256':hashlib.sha256((DATA/'changeformer-levir.pt').read_bytes()).hexdigest(),'license_note':'README restricts code to non-commercial research; review before commercial distribution.'}
(DATA/'models.json').write_text(json.dumps(models,indent=2)); (e/'models.json').write_text(json.dumps(models,indent=2))
print('Acquisition complete',flush=True)
