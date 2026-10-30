"""Operator-only local file/directory registration; no public arbitrary-path endpoint."""
import argparse
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from paired_lab.external_data.store import DatasetStore,inspect_dataset
from paired_lab.external_data.contracts import asset_inventory,preflight,report_csv
from paired_lab.external_data.common import write_json


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,required=True);parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--name',required=True);parser.add_argument('--role',choices=['input','reference','prediction','metadata'],default='input')
    parser.add_argument('--dataset',help='Append files to an existing registered dataset ID')
    parser.add_argument('--sampled',action='store_true',help='Fast five-window inspection; does not enable inference')
    args=parser.parse_args();store=DatasetStore(args.root)
    value=store.get(args.dataset) if args.dataset else store.create(args.name)
    store.import_local(value['id'],args.source,args.role);value=inspect_dataset(store,value['id'],full=not args.sampled)
    folder=store.directory(value['id']);report=preflight(value,assets=asset_inventory(),root=folder)
    write_json(folder/'compatibility_report.json',report);(folder/'compatibility_report.csv').write_text(report_csv(report),encoding='utf-8')
    print(json.dumps(dict(dataset_id=value['id'],manifest=str(folder/'dataset_manifest.json'),state=value['state'],revision=value['revision'],eligible=report['eligible_specialists']),indent=2))
    return 0 if not value['failures'] else 1


if __name__=='__main__':raise SystemExit(main())
