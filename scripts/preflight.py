"""Read-only asset/dependency checks. No downloads, model loading, or inference."""
import argparse
import hashlib
import importlib.metadata
import json
import os
import sys
import subprocess
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import runtime_paths as paths

WORKFLOWS = ('numerical', 'vqa', 'vqa-adapter', 'grounding', 'temporal', 'water', 'land-cover', 'sar-scene', 'cdvqa')


def inventory():
    return paths.read_manifest(paths.REPO/'docs/RUNTIME_ASSETS.json')['assets']


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024*1024), b''):
            h.update(chunk)
    return h.hexdigest()


def asset_path(asset):
    roots = dict(assets=paths.ASSET_ROOT, paired=paths.PAIRED, grounding=paths.GROUNDING,
                 water=paths.WATER, adapter=paths.ADAPTER, cdvqa=paths.CDVQA, encoder=paths.ENCODER)
    target = roots[asset['root']]/asset['path']
    # Inspect existing manifests as well as the portable installation layout.
    if asset['id'] == 'vqa':
        if os.environ.get('SATQUERY_VQA_MODEL'):
            return Path(os.environ['SATQUERY_VQA_MODEL']).expanduser()
        if not target.exists():
            try:return Path(paths.vqa_path())
            except (ImportError, OSError, ValueError):pass
    if asset['id'].startswith('bifold-') and (paths.PAIRED/'models.json').exists():
        manifest=paths.PAIRED/'models.json'
        record=paths.read_manifest(manifest).get(asset['id'].split('-')[1])
        if record:return paths.manifest_path(record,manifest)
    if asset['id'] in ('dino','sam') and (paths.GROUNDING/'models.json').exists():
        manifest=paths.GROUNDING/'models.json'
        records=paths.read_manifest(manifest)
        for record in records:
            if record.get('model')==asset['source']:return paths.manifest_path(record,manifest)
    if asset['id']=='mci' and (paths.PAIRED/'mci-model/manifest.json').exists():
        manifest=paths.PAIRED/'mci-model/manifest.json'
        return paths.manifest_path(paths.read_manifest(manifest),manifest)
    return target


def inspect(asset, verify_hashes=False):
    recovery=(f'Provision from the maintainer release; see docs/ASSETS.md ({asset["source"]}).'
              if asset['access']=='manual' else
              f'Run python scripts/provision_assets.py --workflow {asset["workflows"][0]}; see docs/ASSETS.md.')
    row=dict(id=asset['id'],status='present_not_executed',recovery=recovery)
    try:
        target=asset_path(asset);row['path']=str(target)
        if not target.exists():raise ValueError('Missing path')
        if asset['kind']=='git':
            actual=subprocess.check_output(['git','-C',str(target),'rev-parse','HEAD'],text=True).strip()
            dirty=subprocess.check_output(['git','-C',str(target),'status','--porcelain','--untracked-files=no'],text=True).strip()
            if actual!=asset['revision'] or dirty:raise ValueError('Source revision differs or tracked source is modified')
        if asset['kind']=='hf_snapshot':
            receipt=target/'satquery-source.json'
            if receipt.exists():
                if paths.read_manifest(receipt)!={'repo':asset['source'],'revision':asset['revision']}:
                    raise ValueError('Snapshot provenance differs from pinned revision')
            elif target.name!=asset['revision']:
                raise ValueError('Snapshot provenance unknown; use pinned provisioner or a revision-named Hugging Face snapshot')
        if asset['id'].startswith('bifold-'):
            manifest=paths.read_manifest(paths.PAIRED/'models.json')
            record=manifest[asset['id'].split('-')[1]]
            if record.get('revision')!=asset['revision']:raise ValueError('Model manifest revision mismatch')
        if asset['id'] in ('dino','sam'):
            records=paths.read_manifest(paths.GROUNDING/'models.json')
            if not any(r.get('model')==asset['source'] and r.get('revision')==asset['revision'] for r in records):
                raise ValueError('Grounding manifest revision mismatch')
        if asset['id']=='mci':
            paths.read_manifest(paths.PAIRED/'mci-model/manifest.json')
        for required in asset['required']:
            if not any(p.is_file() and p.stat().st_size for p in target.glob(required)):
                raise ValueError('Missing or empty '+required)
        # A shard index is not enough: every referenced weight shard must exist.
        if target.is_dir():
            for index in target.glob('*.safetensors.index.json'):
                data=paths.read_manifest(index)
                for name in set(data['weight_map'].values()):
                    if not (target/name).is_file():raise ValueError('Missing model shard '+name)
        elif not target.stat().st_size:raise ValueError('Empty file')
        if verify_hashes and asset.get('sha256'):
            row['sha256']=digest(target)
            if row['sha256']!=asset['sha256']:raise ValueError('SHA256 mismatch; do not substitute weights')
            row['status']='hash_verified_not_executed'
    except (OSError, ValueError, KeyError, TypeError, subprocess.CalledProcessError) as exc:
        row.update(status='blocked',reason=str(exc))
    return row


def check(workflow, verify_hashes=False, check_cuda=False):
    chosen=set(WORKFLOWS if workflow=='all' else [workflow])
    if 'vqa-adapter' in chosen:chosen.add('vqa')
    rows=[inspect(a,verify_hashes) for a in inventory() if chosen.intersection(a['workflows'])]
    packages=['numpy','Pillow','rasterio','pyproj','fastapi','python-multipart','requests','uvicorn']
    if chosen-{'numerical'}:packages+=['torch','torchvision']
    if chosen.intersection({'vqa','grounding','vqa-adapter'}):packages+=['transformers','accelerate','huggingface-hub','qwen-vl-utils','peft']
    if chosen.intersection({'temporal','land-cover','sar-scene'}):packages+=['timm','einops']
    deps={}
    for name in packages:
        try:deps[name]=importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:deps[name]='MISSING'
    gpu_required=bool(chosen.intersection({'vqa','grounding','vqa-adapter'}))
    cuda='not_checked'
    if check_cuda:
        try:
            import torch
            cuda=bool(torch.cuda.is_available())
        except ImportError:cuda=False
    blocked=any(r['status']=='blocked' for r in rows) or 'MISSING' in deps.values() or (gpu_required and cuda is False)
    return dict(workflow=workflow,asset_root=str(paths.ASSET_ROOT),assets=rows,dependencies=deps,
                dependency_recovery='Install requirements-runtime.txt in an isolated Python 3.11 environment; see docs/SETUP.md.',
                gpu_required=gpu_required,cuda_available=cuda,status='blocked' if blocked else 'checks_passed_inference_unverified',
                limitation='Presence and hashes are not deployment or accuracy. Use a real inference smoke test. GPU not checked unless --check-cuda is supplied.')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--workflow',choices=('all',)+WORKFLOWS,default='all')
    p.add_argument('--verify-hashes',action='store_true');p.add_argument('--check-cuda',action='store_true')
    p.add_argument('--json',action='store_true');args=p.parse_args()
    report=check(args.workflow,args.verify_hashes,args.check_cuda)
    if args.json:print(json.dumps(report,indent=2))
    else:
        print(f"{report['status']}: {args.workflow}; asset root {report['asset_root']}")
        for row in report['assets']:
            print(f"{row['id']}: {row['status']} — {row.get('path','invalid manifest')}")
            if row['status']=='blocked':print(f"  {row['reason']}. {row['recovery']}")
        print('Dependencies: '+', '.join(f'{k}={v}' for k,v in report['dependencies'].items()))
        print(report['dependency_recovery']);print(report['limitation'])
        if report['gpu_required']:print('VQA/grounding require CUDA in the current implementation; --check-cuda probes availability.')
    return 1 if report['status']=='blocked' else 0


if __name__=='__main__':raise SystemExit(main())
