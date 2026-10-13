"""Build/check browser evidence from saved scores, never from hand-entered percentages."""
import csv,hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
DEST=ROOT/'paired_lab/web/benchmark-data.json'
def build():
    paths=['paired_lab/evidence/cdvqa-trained-20260928/final-test-summary.json','paired_lab/evidence/benchmark-20260921/metrics.csv']
    cd=json.loads((ROOT/paths[0]).read_text())
    for split in cd.values():
        for scope in ('all_official','excluding_12_previously_inspected_pairs'):
            for score in split[scope].values():
                assert abs(score['oa']-score['correct']/score['n'])<1e-12
                assert abs(score['aa']-sum(t['accuracy'] for t in score['by_type'].values())/len(score['by_type']))<1e-12
    with (ROOT/paths[1]).open(newline='') as f:rows=list(csv.DictReader(f))
    for r in rows:r['samples']=int(r['samples']);r['value_0_to_1']=float(r['value_0_to_1']);assert 0<=r['value_0_to_1']<=1
    return {'cdvqa':cd,'metrics':rows,'sources':[{'path':p,'sha256':hashlib.sha256((ROOT/p).read_bytes()).hexdigest()} for p in paths]}
if __name__=='__main__':
    data=build()
    if '--check' in sys.argv:assert json.loads(DEST.read_text())==data,'Browser evidence stale: run scripts/build_evidence_page.py'
    else:DEST.write_text(json.dumps(data,indent=2)+'\n')
    print('Browser benchmark data matches saved source metrics.')
