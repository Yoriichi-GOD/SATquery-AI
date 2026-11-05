"""Instrument actual scripted GIS versus prepared SATquery evidence retrieval."""
import argparse
import json
from pathlib import Path
import time

from shapely.geometry import shape
from research.terrain_exposure.graph import mask_geometry,project
from research.terrain_exposure.io import candidate_raster,sha256,save_json,canonical_hash
from research.terrain_exposure.replay import verify_output


def run(flood_root,terrain_source,terrain_run,output,repeats=5):
    if not 1<=repeats<=20:raise ValueError('Bounded repetition count required')
    output=Path(output)
    if output.exists():raise FileExistsError('Choose new immutable analyst-harness output')
    verify_output(terrain_run)
    terrain_run=Path(terrain_run);source=Path(flood_root)/'artifacts/runs/event-fe47db331390'
    protocol_path=Path(__file__).with_name('analyst-tasks.json')
    protocol=json.loads(protocol_path.read_text());logs=[]

    def conventional(task):
        if task=='water-measurement':
            a,v,g,m=candidate_raster(source/'prediction.tif',[2],[0,1,2])
            return {'pixels':int(a.sum()),'area_m2':float(a.sum()*g.area),'valid_pixels':int(v.sum())},1
        if task=='candidate-building-intersections':
            a,v,g,m=candidate_raster(source/'prediction.tif',[2],[0,1,2]);geometry=mask_geometry(a,g)
            collection=json.loads((source/'layers.geojson').read_text())
            ids=sorted(str(f['id']) for f in collection['features'] if f['properties'].get('kind')=='building'
                and geometry.intersects(project(shape(f['geometry']),'EPSG:4326',g.crs)))
            return {'ids':ids},2
        if task=='downstream-building-assessment':
            config=json.loads((terrain_run/'configuration.json').read_text())
            return {'status':'ABSTAIN_INSUFFICIENT_RESOLUTION' if 2*config['dem_resolution_m']>config['required_feature_width_m'] else 'REQUIRES_FURTHER_VALIDATION'},1
        return {'candidate_sha256':sha256(source/'prediction.tif'),'terrain_sha256':sha256(terrain_source)},2

    def satquery(task):
        if task=='candidate-building-intersections':
            rows=json.loads((terrain_run/'receptors.json').read_text())['receptors']
            return {'ids':sorted(row['id'] for row in rows if row['kind']=='building' and row['layers'].get('water',{}).get('direct_intersection'))},1
        summary=json.loads((terrain_run/'summary.json').read_text())
        if task=='water-measurement':
            o=summary['observations']['water']
            return {'pixels':o['candidate_pixels'],'area_m2':o['candidate_area_m2'],'valid_pixels':o['valid_pixels']},1
        if task=='downstream-building-assessment':
            return {'status':'ABSTAIN_INSUFFICIENT_RESOLUTION' if summary['resolution']['status']=='INSUFFICIENT_RESOLUTION' else 'REQUIRES_FURTHER_VALIDATION'},1
        manifest=json.loads((terrain_run/'manifest.json').read_text())
        return {'candidate_sha256':manifest['original_sources']['water']['sha256'],
                'terrain_sha256':manifest['original_sources']['terrain']['sha256']},2

    for repetition in range(repeats):
        methods=[('scripted_gis',conventional),('satquery_prepared_evidence',satquery)]
        if repetition%2:methods.reverse()
        for task in protocol['tasks']:
            outputs={}
            for name,method in methods:
                started=time.perf_counter();answer,reads=method(task['id']);elapsed=time.perf_counter()-started
                outputs[name]=answer
                logs.append({'repetition':repetition,'method':name,'task_id':task['id'],'seconds':elapsed,
                    'logical_artifact_reads':reads,'active_analyst_seconds':None,'human_manual_actions':None,
                    'answer':answer,'answer_sha256':canonical_hash(answer),'completed':True})
            equal=outputs['scripted_gis']==outputs['satquery_prepared_evidence']
            for log in logs[-2:]:log['rubric_match']=equal
    output.mkdir(parents=True)
    save_json(output/'protocol.json',protocol);save_json(output/'logs.json',logs)
    result={'population':protocol['population'],'human_participants':0,'repeats':repeats,
            'timing_scope':protocol['timing_scope'],'claim_policy':protocol['claim_policy'],
            'completed_operations':len(logs),'rubric_matches':sum(row['rubric_match'] for row in logs),
            'active_analyst_seconds':None,'human_manual_actions':None,
            'source_run_manifest_sha256':sha256(terrain_run/'manifest.json'),'protocol_sha256':sha256(protocol_path),
            'methods':{name:{'operations':sum(row['method']==name for row in logs),
                'median_seconds':__import__('statistics').median(row['seconds'] for row in logs if row['method']==name)}
                for name in ['scripted_gis','satquery_prepared_evidence']},
            'limitations':['Prepared evidence shifts work into preprocessing; raw engine creation is excluded',
                'Logical artifact opens are instrumented software operations, not human actions',
                'OS/file caches and repeated same-case operations affect timings; no productivity inference']}
    save_json(output/'summary.json',result)
    save_json(output/'manifest.json',{'state':'complete','files':{p.name:sha256(p) for p in sorted(output.iterdir()) if p.is_file()}})
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['flood-root','terrain-source','terrain-run','output']:p.add_argument('--'+name,required=True)
    p.add_argument('--repeats',type=int,default=5);a=p.parse_args()
    print(json.dumps(run(a.flood_root,a.terrain_source,a.terrain_run,a.output,a.repeats),indent=2))
