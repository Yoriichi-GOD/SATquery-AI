"""One isolated, stoppable intake/inference/evaluation operation."""
import json
import sys
import time
from pathlib import Path
from .common import DataError,fail,read_json,write_json
from .store import DatasetStore,inspect_dataset


def main(request_path):
    path=Path(request_path);request=read_json(path);jobdir=path.parent
    store=DatasetStore(request['root'],recover=False)
    def check():
        if (jobdir/'cancel.flag').exists():fail('CANCELLED','Operator cancelled this external-data operation.')
    last=[0.]
    def progress(value):
        if isinstance(value,str):value=dict(stage=value)
        if time.monotonic()-last[0]>.15:
            write_json(jobdir/'progress.json',value);last[0]=time.monotonic()
    try:
        if request['operation']=='inspect':
            value=inspect_dataset(store,request['dataset_id'],check,progress,request['parameters'].get('full_scan',True))
            result=dict(state='COMPLETE',dataset_id=value['id'],dataset_state=value['state'],failures=value['failures'])
        else:
            from .runner import run
            result=run(store,request['dataset_id'],jobdir/'evidence',request['parameters'],check,progress)
        write_json(jobdir/'worker_result.json',result)
    except Exception as exc:
        write_json(jobdir/'worker_result.json',dict(state='CANCELLED' if getattr(exc,'code',None)=='CANCELLED' else 'PROCESSING_FAILED',failures=[dict(code=getattr(exc,'code','PROCESSING_FAILED'),message=str(exc))]))


if __name__=='__main__':main(sys.argv[1])
