"""Provision allowlisted local frozen examples; never acquire data or copy credentials."""
import argparse,json,shutil,sys,os
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from research.terrain_exposure.io import sha256,save_json
from research.terrain_exposure.replay import verify_freeze

ROOT=Path(__file__).resolve().parents[1]

def checked_copy(src,dst,expected):
    if sha256(src)!=expected:raise ValueError('Source hash mismatch: '+src.name)
    dst.parent.mkdir(parents=True,exist_ok=True)
    if dst.exists() and sha256(dst)!=expected:raise FileExistsError('Refusing to replace different local data')
    if not dst.exists():shutil.copyfile(src,dst)
    if sha256(dst)!=expected:raise ValueError('Copy verification failed')

def prepare(source,terrain_source=None):
    source=Path(source).resolve();component=ROOT/'components/floodlab';records=[]
    for identity in ['event-fe47db331390','nepal-syapru-004']:
        run=source/'artifacts/runs'/identity;freeze=verify_freeze(run)
        for name,expected in {**freeze['files'],'freeze.json':sha256(run/'freeze.json')}.items():
            if Path(name).name!=name:raise ValueError('Unsafe freeze name')
            dst=component/'artifacts/runs'/identity/name;checked_copy(run/name,dst,expected)
            records.append({'file':str(dst.relative_to(ROOT)).replace('\\','/'),'sha256':expected,'role':'frozen_demonstration_not_new_validation'})
    refs=json.loads((component/'docs/dataset-readiness.json').read_text())['references']
    for item in refs:
        name=item['filename']
        if Path(name).name!=name:raise ValueError('Unsafe reference name')
        dst=component/'evaluation_only/emsr'/name
        checked_copy(source/'evaluation_only/emsr'/name,dst,item['sha256'])
        records.append({'file':str(dst.relative_to(ROOT)).replace('\\','/'),'sha256':item['sha256'],
            'role':'previously_inspected_development_reference_not_untouched_test'})
    save_json(ROOT/'.runtime/case-campaign-20261107/local-provisioning.json',{'copied':records,'originals_modified':False})
    if terrain_source:
        from jai_extension.terrain import TerrainStore
        store=TerrainStore(terrain_source)
        for item in store.status()['scenes']:
            scene=store.scene(item['id']);origin=Path(terrain_source)/item['id']
            for name,expected in {**scene['hashes'],'scene.json':sha256(origin/'scene.json')}.items():
                checked_copy(origin/name,ROOT/'.runtime/jai/terrain'/item['id']/name,expected)
    # One active scientific replay avoids ambiguous selection in deterministic investigations.
    origin=ROOT/'.runtime/case-campaign-20261107/nepal-resolution-v1/replay-30m'
    if origin.is_dir():
        from research.terrain_exposure.replay import verify_output
        manifest,_=verify_output(origin)
        destination=ROOT/'.runtime/research-release/terrain-exposure/terrain-exposure-nepal-glo30'
        destination.mkdir(parents=True,exist_ok=True)
        for name,expected in {**manifest['files'],'manifest.json':sha256(origin/'manifest.json')}.items():
            target=destination/name
            if not target.exists():
                try:os.link(origin/name,target)
                except OSError:shutil.copyfile(origin/name,target)
            if sha256(target)!=expected:raise ValueError('Active replay link mismatch')
    print(json.dumps({'verified_copies':len(records),'credentials_copied':False}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--flood-source',required=True);p.add_argument('--terrain-source')
    a=p.parse_args();prepare(a.flood_source,a.terrain_source)
