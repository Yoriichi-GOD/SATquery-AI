"""One-off migration of an already computed v1 replay to normalized graph/CSV storage."""
import argparse
import json
from pathlib import Path

from .graph import receptor_summary
from .io import canonical_hash, save_json, sha256
from .replay import verify_output


def compact(source, target):
    import shutil
    _,graph=verify_output(source)
    source,target=Path(source),Path(target)
    target.mkdir(parents=True,exist_ok=False)
    for p in source.iterdir():
        if p.name not in {'manifest.json','graph.json','summary.json'}:
            shutil.copyfile(p,target/p.name)
    save_json(target/'receptors.json',receptor_summary(graph))
    stored={k:v for k,v in graph.items() if k not in {'relationships','content_sha256'}}
    stored['relationships_artifact']={'filename':'relationships.csv','sha256':sha256(target/'relationships.csv'),
        'rows':len(graph['relationships']),'note':'Normalized shared node metadata; CSV retains all source/receptor relationships'}
    stored['content_sha256']=canonical_hash(stored)
    save_json(target/'graph.json',stored)
    summary=json.loads((source/'summary.json').read_text())
    summary['graph_content_sha256']=stored['content_sha256']
    summary['storage_migration']={'source_manifest_sha256':sha256(source/'manifest.json'),
        'source_graph_sha256':sha256(source/'graph.json'),'algorithm_rerun':False}
    save_json(target/'summary.json',summary)
    manifest=json.loads((source/'manifest.json').read_text())
    manifest['files']={p.name:sha256(p) for p in sorted(target.iterdir()) if p.is_file()}
    save_json(target/'manifest.json',manifest)
    print(json.dumps({'output':str(target),'graph_bytes':(target/'graph.json').stat().st_size,
                      'csv_bytes':(target/'relationships.csv').stat().st_size,'receptor_count':len(graph['nodes'])}))

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source');parser.add_argument('target')
    args=parser.parse_args();compact(args.source,args.target)
