"""Replay a genuine frozen network and create separately frozen scenario artifacts."""
from pathlib import Path
import argparse,json,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from floodlab.response_store import ResponseStore

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('run_id');p.add_argument('--restore',nargs='*',default=[])
    p.add_argument('--runs',type=Path,default=Path(__file__).resolve().parents[1]/'artifacts/runs')
    p.add_argument('--output',type=Path,default=Path(__file__).resolve().parents[1]/'.runtime/response')
    a=p.parse_args();value=ResponseStore(a.runs,a.output).calculate(a.run_id,a.restore)
    print(json.dumps({k:value[k] for k in ['state','scenario_id','summary','repair_search','source']},indent=2))
