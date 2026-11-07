"""Finalize the review pack after tests; verify every stored checksum."""
import argparse,json,subprocess,sys,re
from pathlib import Path
from datetime import datetime,timezone
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from research.terrain_exposure.io import sha256,save_json
ROOT=Path(__file__).resolve().parents[1]

def freeze(root,source_commit=None):
    root=Path(root);code={}
    for folder in ['research/cases','research/datasets','research/experiments','research/evaluation','research/registration','research/terrain_exposure','jai_extension','scripts','tests']:
        for p in (ROOT/folder).rglob('*.py'):
            if 'local' in p.relative_to(ROOT).parts:continue
            code[p.relative_to(ROOT).as_posix()]=sha256(p)
    for p in ROOT.glob('*.py'):code[p.name]=sha256(p)
    source_commit=source_commit or subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    if not re.fullmatch('[a-f0-9]{40}',source_commit):raise ValueError('A full verified source commit is required')
    save_json(root/'SOURCE_CODE_SHA256.json',{'files':code,
        'source_commit':source_commit,
        'scope':'Current executable source hashes; binary assets and private raw datasets have separate manifests'})
    files={p.relative_to(root).as_posix():sha256(p) for p in sorted(root.rglob('*')) if p.is_file() and p.name!='RELEASE_MANIFEST.json'}
    value={'schema':'satquery.case-research-release/1','recorded_utc':datetime.now(timezone.utc).isoformat(),'files':files,
        'manifest_scope':'Derived paper pack integrity; not validation of satellite truth or upstream authenticity'}
    save_json(root/'RELEASE_MANIFEST.json',value)
    for name,expected in files.items():
        p=(root/name).resolve()
        if not p.is_relative_to(root.resolve()) or sha256(p)!=expected:raise AssertionError('Pack hash mismatch')
    print(json.dumps({'verified_pack_files':len(files),'source_files_hashed':len(code)}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--pack',default='research/results/case-campaign-20261107');p.add_argument('--source-commit')
    a=p.parse_args();freeze(a.pack,a.source_commit)
