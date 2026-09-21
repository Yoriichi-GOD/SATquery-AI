"""Restore pinned isolated lab assets. Does not modify main demo packages."""
from pathlib import Path
import sys,json,subprocess,hashlib,zipfile,requests
from huggingface_hub import snapshot_download,hf_hub_download
ROOT=Path(__file__).resolve().parent
manifest=json.loads((ROOT/'runtime-manifest.json').read_text())
DATA=Path('/root/satquery/paired-lab');DATA.mkdir(exist_ok=True)
for name,url,revision in [('ChangeFormer','https://github.com/wgcban/ChangeFormer.git',manifest['temporal_revision']),('ConfigILM','https://github.com/lhackel-tub/ConfigILM.git',manifest['configilm_revision'])]:
    target=DATA/name
    if not target.exists():
        subprocess.run(['git','clone',url,str(target)],check=True)
        subprocess.run(['git','-C',str(target),'checkout','--detach',revision],check=True)
    current=subprocess.check_output(['git','-C',str(target),'rev-parse','HEAD'],text=True).strip()
    if current!=revision:raise RuntimeError(f'{name} revision differs: inspect it rather than overwriting local changes.')
subprocess.run([sys.executable,'-m','pip','install','--target',str(DATA/'deps'),'--no-deps',*[f'{k}=={v}' for k,v in manifest['dependency_versions'].items()]],check=True)
models=manifest['models']
for kind in ['all','s1','s2']:
    m=models[kind];m['path']=snapshot_download(m['repo'],revision=m['revision'],allow_patterns=['config.json','model.safetensors','README.md'])
checkpoint=DATA/'changeformer-levir.pt'
if not checkpoint.exists():
    url='https://github.com/wgcban/ChangeFormer/releases/download/v0.1.0/CD_ChangeFormerV6_LEVIR_b16_lr0.0001_adamw_train_test_200_linear_ce_multi_train_True_multi_infer_False_shuffle_AB_False_embed_dim_256.zip'
    archive=DATA/'changeformer-levir.zip'
    if not archive.exists():
        response=requests.get(url,stream=True,timeout=60);response.raise_for_status()
        partial=archive.with_suffix('.partial')
        with partial.open('wb') as f:
            for chunk in response.iter_content(1024*1024):f.write(chunk)
        partial.rename(archive)
    with zipfile.ZipFile(archive) as z:
        names=[n for n in z.namelist() if n.endswith('/best_ckpt.pt')]
        if len(names)!=1:raise RuntimeError('Unexpected checkpoint archive.')
        checkpoint.write_bytes(z.read(names[0]))
if hashlib.sha256(checkpoint.read_bytes()).hexdigest()!=models['temporal']['sha256']:raise RuntimeError('Checkpoint hash mismatch.')
models['temporal']['path']=str(checkpoint)
(DATA/'models.json').write_text(json.dumps(models,indent=2))
m=manifest['mci']
path=hf_hub_download(m['repo'],'MCI_model.pth',revision=m['revision'],local_dir=str(DATA/'mci-model'))
if hashlib.sha256(Path(path).read_bytes()).hexdigest()!=m['sha256']:raise RuntimeError('MCI checkpoint hash mismatch.')
m['path']=path;(DATA/'mci-model/manifest.json').write_text(json.dumps(m,indent=2))
water=ROOT/'checkpoints/water-v1.pt'
if not water.exists() or hashlib.sha256(water.read_bytes()).hexdigest()!=manifest['water_model']['sha256']:raise RuntimeError('Restore the bundled water checkpoint; do not silently substitute or retrain it.')
print('Pinned paired-lab assets ready. Main demo environment unchanged.')
