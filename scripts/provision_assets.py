"""Explicitly acquire pinned public assets. Never trains or substitutes a model."""
import argparse
import json
import subprocess
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import runtime_paths as paths
from preflight import inventory, digest, inspect, WORKFLOWS


def save_manifest(path, record):
    path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists():
        if paths.read_manifest(path)!=record:
            raise ValueError(f'{path} already differs. Inspect it; this tool will not overwrite an installation.')
        return
    path.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')


def provision(workflow):
    roots=dict(assets=paths.ASSET_ROOT,paired=paths.PAIRED,grounding=paths.GROUNDING,
               water=paths.WATER,adapter=paths.ADAPTER,cdvqa=paths.CDVQA,encoder=paths.ENCODER)
    chosen={workflow,'vqa'} if workflow=='vqa-adapter' else {workflow}
    records={};grounding=[];blocked=[]
    for asset in inventory():
        if not chosen.intersection(asset['workflows']):continue
        target=roots[asset['root']]/asset['path']
        if asset['access']=='manual':
            row=inspect(asset,True)
            if row['status']=='blocked':blocked.append(row)
            print(f"{asset['id']}: {row['status']}; {row['recovery']}",flush=True)
            continue
        print(f"Provisioning {asset['id']} at {target}",flush=True)
        if asset['kind']=='hf_snapshot':
            from huggingface_hub import snapshot_download
            if target.exists():
                # Avoid silently mixing a pre-existing snapshot and newly fetched files.
                receipt=target/'satquery-source.json'
                expected={'repo':asset['source'],'revision':asset['revision']}
                if not receipt.exists() or paths.read_manifest(receipt)!=expected:
                    raise ValueError(f'Unrecognized existing snapshot {target}; choose an empty asset root or inspect it manually.')
            target.mkdir(parents=True,exist_ok=True)
            save_manifest(target/'satquery-source.json',{'repo':asset['source'],'revision':asset['revision']})
            snapshot_download(asset['source'],revision=asset['revision'],local_dir=target,
                              allow_patterns=['*.json','*.safetensors','*.txt','*.model','README.md','LICENSE*'])
            if asset['id'].startswith('bifold-'):
                kind=asset['id'].split('-')[1]
                records[kind]=dict(repo=asset['source'],revision=asset['revision'],path='models/'+kind)
            if asset['id'] in ('dino','sam'):
                grounding.append(dict(model=asset['source'],revision=asset['revision'],path='models/'+asset['id'],license=asset['license']))
        elif asset['kind']=='git':
            if not target.exists():
                target.parent.mkdir(parents=True,exist_ok=True)
                subprocess.run(['git','clone',asset['source'],str(target)],check=True)
                subprocess.run(['git','-C',str(target),'checkout','--detach',asset['revision']],check=True)
            actual=subprocess.check_output(['git','-C',str(target),'rev-parse','HEAD'],text=True).strip()
            if actual!=asset['revision']:raise ValueError(f'Wrong revision at {target}; inspect existing checkout.')
        elif asset['kind']=='hf_file':
            from huggingface_hub import hf_hub_download
            if not target.exists():
                hf_hub_download(asset['source'],target.name,revision=asset['revision'],local_dir=target.parent)
        elif asset['kind']=='url' and not target.exists():
            target.parent.mkdir(parents=True,exist_ok=True)
            partial=target.with_suffix('.partial')
            with urllib.request.urlopen(asset['source'],timeout=60) as response,partial.open('wb') as output:
                while chunk:=response.read(1024*1024):output.write(chunk)
            if digest(partial)!=asset['sha256']:raise ValueError(f'Hash mismatch at {partial}; download retained for inspection.')
            partial.rename(target)
        if asset.get('sha256'):
            if not target.is_file() or digest(target)!=asset['sha256']:
                raise ValueError(f'Missing or incorrect {target}; expected SHA256 {asset["sha256"]}.')
        if asset['id']=='mci':
            original=paths.read_manifest(paths.REPO/'paired_lab/runtime-manifest.json')['mci']
            save_manifest(target.parent/'manifest.json',{**original,'path':target.name})
    if records:
        manifest=paths.PAIRED/'models.json'
        previous=paths.read_manifest(manifest) if manifest.exists() else {}
        for kind,record in records.items():
            if kind in previous and previous[kind]!=record:raise ValueError(f'Existing {kind} manifest differs; inspect {manifest}.')
        merged={**previous,**records}
        if merged!=previous:
            manifest.parent.mkdir(parents=True,exist_ok=True)
            manifest.write_text(json.dumps(merged,indent=2)+'\n',encoding='utf-8')
    if grounding:save_manifest(paths.GROUNDING/'models.json',grounding)
    return 1 if blocked else 0


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--workflow',required=True,choices=WORKFLOWS)
    args=p.parse_args()
    try:return provision(args.workflow)
    except (OSError,ValueError,subprocess.CalledProcessError) as exc:
        print(f'Provisioning stopped: {exc}',file=sys.stderr);return 1


if __name__=='__main__':raise SystemExit(main())
