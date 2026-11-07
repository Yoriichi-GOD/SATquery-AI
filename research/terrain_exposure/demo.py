"""Small portable synthetic geometry example; NEVER satellite validation."""
import argparse
import json
from pathlib import Path

import numpy as np
from affine import Affine
from shapely.geometry import Point
from .io import Grid,canonical_hash,save_json,sha256
from .graph import Observation,Receptor,build_graph,export_graph
from .hydrology import derive


def run(output):
    grid=Grid((7,7),Affine(10,0,300000,0,-10,3100000),'EPSG:32645')
    z=np.tile(np.arange(7,0,-1),(7,1)).astype(float);valid=np.ones_like(z,bool)
    hydro=derive(z,valid,grid,300)
    candidate=np.zeros_like(valid);candidate[3,2]=True
    observation=Observation('water',candidate,valid,grid,{'sha256':canonical_hash(candidate.tolist()),
        'dataset':'SYNTHETIC KNOWN MASK'},['2026-01-01','2026-01-02'],'Synthetic fixture')
    receptors=[Receptor(name,'building',Point(grid.centre(cell)),grid.crs,
        {'sha256':canonical_hash([name,cell]),'dataset':'SYNTHETIC GEOMETRY'},'2026-01-01')
        for name,cell in [('upstream',22),('direct',23),('downstream',27)]]
    graph=build_graph(hydro,[observation],receptors,{'sha256':canonical_hash(z.tolist()),'dataset':'SYNTHETIC PLANE'})
    stored=export_graph(graph,hydro,output);output=Path(output)
    save_json(output/'example.json',{'population':'SYNTHETIC_SOFTWARE_EXAMPLE','summary':stored['summary'],
        'expected':{'upstream':'NOT_CONNECTED_WITHIN_DOMAIN','direct':'DIRECT_GEOMETRIC_INTERSECTION','downstream':'POTENTIAL_DOWNSTREAM_CONNECTION'}})
    save_json(output/'manifest.json',{'state':'complete','population':'SYNTHETIC_SOFTWARE_EXAMPLE',
        'files':{p.name:sha256(p) for p in sorted(output.iterdir()) if p.is_file()}})
    return graph


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',required=True);a=p.parse_args();g=run(a.output)
    print(json.dumps({'population':'SYNTHETIC_SOFTWARE_EXAMPLE','relationships':g['relationships']},indent=2))
