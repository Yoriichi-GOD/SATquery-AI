"""Exhaustive tiny directed-network contract audit; NOT event accuracy or full Lifeline scoring."""
from __future__ import annotations
import argparse,ast,hashlib,itertools,json,sys,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import networkx as nx
import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import dijkstra
from floodlab.response import assess


def kernel(root,audit):
    path=Path(root)/'src/lifeline/access/montecarlo.py'
    raw=path.read_bytes();expected=audit['files']['src/lifeline/access/montecarlo.py']
    if hashlib.sha256(raw).hexdigest()!=expected:raise ValueError('Upstream kernel source changed')
    tree=ast.parse(raw.decode());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='_undirected_csr')
    # Only the audited pure numerical function is executed; no imports, provider
    # code, repository startup, model loading or network/file access is allowed.
    if any(isinstance(n,(ast.Import,ast.ImportFrom,ast.With,ast.Try,ast.Raise,ast.Lambda)) for n in ast.walk(fn)):
        raise ValueError('Unexpected upstream kernel operations')
    calls={ast.unparse(n.func) for n in ast.walk(fn) if isinstance(n,ast.Call)}
    if calls-{'np.concatenate','np.lexsort','np.ones','csr_matrix','len'}:raise ValueError('Unreviewed upstream kernel call')
    namespace={'__builtins__':{'len':len,'bool':bool},'np':np,'csr_matrix':csr_matrix}
    exec(compile(ast.Module(body=[fn],type_ignores=[]),str(path),'exec'),namespace)
    return namespace['_undirected_csr']


def oracle(edges,allowed):
    reached={2};queue=[2]
    while queue:
        node=queue.pop()
        for a,b,state in edges:
            if a==node and state in allowed and b not in reached:reached.add(b);queue.append(b)
    return 0 in reached


def run(upstream,audit_path,output):
    output=Path(output)
    if output.exists():raise FileExistsError('Do not overwrite a benchmark receipt')
    audit=json.loads(Path(audit_path).read_text());function=kernel(upstream,audit)
    pairs=[(a,b) for a in range(3) for b in range(3) if a!=b]
    totals={'all_graphs':0,'our_bound_matches':0,'known_state_graphs':0,'our_known_matches':0,
            'upstream_undirected_kernel_matches':0,'upstream_false_route_positives':0,'upstream_false_route_negatives':0}
    mismatches=[];started=time.perf_counter()
    for states in itertools.product(range(4),repeat=len(pairs)):
        # 0 absent, 1 observed-clear, 2 candidate-disrupted, 3 observation unknown.
        edges=[(a,b,state) for (a,b),state in zip(pairs,states) if state]
        g=nx.MultiDiGraph();g.add_nodes_from(range(3))
        for i,(a,b,state) in enumerate(edges):
            g.add_edge(a,b,key=str(i),source_id=f'way-{a}-{b}',edge_id=str(i),length_m=1.0,
                       state={1:'clear',2:'disrupted',3:'unknown'}[state])
        row=assess(g,[{'id':'place','node_id':2,'boundary_truncated':False}],[0],include_paths=False)['rows'][0]
        lower=oracle(edges,{1});upper=oracle(edges,{1,3})
        correct=row['after_conservative']==lower and row['after_optimistic']==upper
        totals['all_graphs']+=1;totals['our_bound_matches']+=correct
        if 3 in states:continue
        totals['known_state_graphs']+=1;totals['our_known_matches']+=row['after_conservative']==lower
        open_edges=[(a,b) for a,b,state in edges if state==1]
        u=np.array([a for a,b in open_edges],dtype=int);v=np.array([b for a,b in open_edges],dtype=int)
        matrix=function(3,u,v,np.ones(len(u)))
        predicted=bool(np.isfinite(dijkstra(matrix,directed=True,indices=2)[0]))
        totals['upstream_undirected_kernel_matches']+=predicted==lower
        totals['upstream_false_route_positives']+=predicted and not lower
        totals['upstream_false_route_negatives']+=lower and not predicted
        if predicted!=lower and len(mismatches)<8:
            mismatches.append({'edges':edges,'expected_directed_route':lower,'upstream_undirected_route':predicted})
    assert totals['all_graphs']==4096 and totals['known_state_graphs']==729
    assert totals['our_bound_matches']==4096 and totals['our_known_matches']==729
    result={'population':'EXHAUSTIVE_SYNTHETIC_DIRECTED_NETWORK_CONTRACT',
        'contract':'Three fixed nodes; settlement 2 to service node 0; every directed edge independently absent/clear/disrupted/unknown',
        'upstream_commit':audit['commit'],'upstream_source_sha256':audit['files']['src/lifeline/access/montecarlo.py'],
        'our_response_source_sha256':hashlib.sha256((Path(__file__).resolve().parents[1]/'floodlab/response.py').read_bytes()).hexdigest(),
        'upstream_scope':'Actual audited _undirected_csr numerical function; NOT full acquisition/detection/closure pipeline',
        'totals':totals,'counterexamples':mismatches,'seconds':time.perf_counter()-started,
        'limitations':['Synthetic route semantics only, not flood/landslide accuracy or real settlement access',
                      'Unknown-observation cases test our bounds; no comparison with an assumed upstream closure prior',
                      'This establishes a bounded directionality improvement, not overall superiority']}
    output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--upstream',required=True)
    p.add_argument('--audit',default='docs/lifeline/UPSTREAM_AUDIT.json');p.add_argument('--output',required=True)
    a=p.parse_args();run(a.upstream,a.audit,a.output)
