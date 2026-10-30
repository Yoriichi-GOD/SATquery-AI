"""Execute a selected eligible specialist or independently evaluate imported predictions."""
import argparse
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from paired_lab.external_data.store import DatasetStore
from paired_lab.external_data.runner import run,verify
from paired_lab.external_data.common import read_json


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dataset',type=Path,required=True,help='Registered dataset_manifest.json')
    parser.add_argument('--request',type=Path,required=True,help='Explicit specialist/IDs/parameters and predeclared protocol JSON')
    parser.add_argument('--output',type=Path,required=True,help='New output directory; existing runs are refused')
    args=parser.parse_args();manifest=args.dataset.resolve();dataset=read_json(manifest)
    if manifest.name!='dataset_manifest.json' or manifest.parent.name!=dataset['id']:raise ValueError('Use a registered dataset manifest in its private dataset directory.')
    store=DatasetStore(manifest.parent.parent,recover=False)
    result=run(store,dataset['id'],args.output,read_json(args.request))
    print(json.dumps(dict(result=result,verification=verify(args.output)),indent=2))
    return 1 if result['failures'] else 0


if __name__=='__main__':raise SystemExit(main())
