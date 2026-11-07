"""Independent saved-output arithmetic/topology checks. No neural models required."""
import argparse
from collections import Counter
import csv
import json
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np
from research.terrain_exposure.io import read_raster,sha256,canonical_hash,save_json
from research.terrain_exposure.replay import verify_output
from research.evaluation.metrics import ranking_metrics


def verify(root,experiment=None):
    root=Path(root);manifest,graph=verify_output(root)
    arrays={}
    for name in ['original_dem','conditioned_dem','downstream_index','flow_direction_d8','contributing_area_m2','streams','catchment_outlet','hand_m']:
        data,valid,grid,meta=read_raster(root/(name+'.tif'));arrays[name]=(data,valid)
    z,valid=arrays['original_dem'];d=arrays['downstream_index'][0].astype(int).ravel()
    original=z.ravel();conditioned=arrays['conditioned_dem'][0].ravel()
    stream=arrays['streams'][0].ravel()==1
    independently_accumulated=np.zeros(z.size,dtype='int64');outlets={};hand_checked=0
    codes={(0,1):1,(1,1):2,(1,0):4,(1,-1):8,(0,-1):16,(-1,-1):32,(-1,0):64,(-1,1):128}
    for start in map(int,np.flatnonzero(valid)):
        current=start;seen=set();drainage=None
        while current>=0:
            if current in seen:raise AssertionError('Cycle')
            seen.add(current);independently_accumulated[current]+=1
            if stream[current] and drainage is None:drainage=current
            downstream=d[current]
            if downstream>=0:
                assert downstream<z.size and valid.ravel()[downstream]
                r,c=divmod(current,z.shape[1]);rr,cc=divmod(int(downstream),z.shape[1])
                assert (rr-r,cc-c) in codes
                assert arrays['flow_direction_d8'][0].ravel()[current]==codes[(rr-r,cc-c)]
                assert conditioned[downstream]<=conditioned[current]+1e-8
            else:outlets[start]=current
            current=int(downstream)
        assert arrays['catchment_outlet'][0].ravel()[start]==outlets[start]
        actual=arrays['hand_m'][0].ravel()[start];available=arrays['hand_m'][1].ravel()[start]
        expected=None if drainage is None else original[start]-original[drainage]
        if expected is None or expected<0:assert not available
        else:assert available and abs(actual-expected)<1e-8;hand_checked+=1
    np.testing.assert_allclose(independently_accumulated[valid.ravel()]*grid.area,
                               arrays['contributing_area_m2'][0][valid],rtol=0,atol=1e-8)
    nodes={n['id'] for n in graph['nodes']}
    assert len(nodes)==len(graph['nodes'])
    assert all(e['source'] in nodes and e['target'] in nodes for e in graph['edges'])
    counts=Counter();rows=0
    with (root/'relationships.csv').open(newline='') as stream:
        for row in csv.DictReader(stream):
            assert row['source_id'] in nodes and 'receptor:'+row['receptor_id'] in nodes
            if row['status'] in {'UNAVAILABLE_EVIDENCE','UNRESOLVED_WITHIN_DEM_CELL'}:
                assert row['ordinal_screening_tier']==''
            counts[row['status']]+=1;rows+=1
    assert rows==graph['summary']['relationship_count']
    assert dict(counts)==graph['summary']['relationship_statuses']
    for layer,obs in graph['observations'].items():
        source_nodes=[n for n in graph['nodes'] if n['type']=='source' and n['attributes']['layer']==layer]
        assert sum(n['support']['native_pixel_count'] for n in source_nodes)==obs['candidate_pixels']
        assert abs(sum(n['attributes']['area_m2'] for n in source_nodes)-obs['candidate_area_m2'])<.01
    result={'status':'PASS','scope':'Saved artifact integrity, numeric invariants, topology and metric recalculation; not scientific accuracy',
            'valid_dem_cells':int(valid.sum()),'independent_hand_cells_checked':hand_checked,
            'relationships_checked':rows,'relationship_statuses':dict(counts),
            'source_manifest_sha256':sha256(root/'manifest.json')}
    if experiment:
        experiment=Path(experiment);protocol=json.loads((experiment/'protocol.json').read_text())
        rows=json.loads((experiment/'rows.json').read_text());report=json.loads((experiment/'metrics.json').read_text())
        freeze=json.loads((experiment/'freeze.json').read_text())
        assert canonical_hash(rows)==freeze['rows_sha256']
        assert canonical_hash(protocol)==freeze['protocol_sha256']
        for method,saved in report['results'].items():
            measured=ranking_metrics([r['scores'][method] for r in rows],[r['label'] for r in rows],protocol['k'])
            for key,value in measured.items():assert saved[key]==value,(method,key)
        result['ranking_methods_recomputed']=len(report['results'])
        result['reference_units']=len(rows)
        result['experiment_manifest_sha256']=sha256(experiment/'manifest.json')
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('run');p.add_argument('--experiment');p.add_argument('--output',required=True);a=p.parse_args()
    if Path(a.output).exists():raise FileExistsError('Do not overwrite a verification receipt')
    result=verify(a.run,a.experiment);save_json(a.output,result);print(json.dumps(result,indent=2))
