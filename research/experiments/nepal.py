"""Frozen Nepal road-grade screening diagnostic. Never water/debris accuracy."""
from __future__ import annotations

import argparse
from collections import Counter
import csv
import json
import math
from pathlib import Path
import time

import numpy as np
import fiona
from rasterio.features import rasterize
from shapely.geometry import shape, mapping, box
from shapely.ops import unary_union

from research.evaluation.metrics import binary_metrics, ranking_metrics, paired_spatial_interval
from research.terrain_exposure.graph import project, mask_geometry, touched_cells, finite_stat
from research.terrain_exposure.hydrology import derive, path
from research.terrain_exposure.io import read_raster, sha256, canonical_hash, save_json
from research.terrain_exposure.replay import load_nepal, verify_output


def vector_layer(filename, layer, crs):
    geometries=[];properties=[]
    with fiona.open(filename,layer=layer) as src:
        if not src.crs_wkt:raise ValueError('Reference CRS unavailable')
        for feature in src:
            if feature['geometry']:
                geometry=shape(feature['geometry'])
                if not geometry.is_valid:raise ValueError('Invalid reference geometry; no silent repair')
                geometries.append(project(geometry,src.crs_wkt,crs))
                properties.append({'reference_feature_id':str(feature['id']),**dict(feature['properties'])})
    return geometries,properties


def downstream_distances(hydro,source_cells):
    reach={}
    for start in sorted(source_cells):
        route=path(hydro,start);length=0
        for previous,cell in zip(route,route[1:]):
            length+=math.dist(hydro.grid.centre(previous),hydro.grid.centre(cell))
            if cell not in reach or length<reach[cell]:reach[cell]=length
    return reach


def run(flood_root,terrain_source,prediction_run,protocol_path,output,registration_audit):
    started=time.perf_counter()
    output=Path(output)
    if output.exists():raise FileExistsError('Choose a new immutable experiment output')
    manifest,graph=verify_output(prediction_run)
    cfg=json.loads((Path(prediction_run)/'configuration.json').read_text())
    protocol=json.loads(Path(protocol_path).read_text())
    registration=json.loads(Path(registration_audit).read_text())
    z,v,grid,observations,receptors,terrain_provenance=load_nepal(flood_root,terrain_source,cfg)
    hydro=derive(z,v,grid,cfg['stream_area_m2'],cfg['conditioning'])
    water=next(o for o in observations if o.layer=='water')
    root=Path(flood_root)
    reference=root/'evaluation_only/emsr'/protocol['reference']
    if sha256(reference)!=protocol['reference_sha256']:raise ValueError('Frozen reference changed')
    # Source metadata tables have no geometry. Read their attributes separately.
    with fiona.open(reference,layer='source_v1') as src:source_properties=[dict(f['properties']) for f in src]
    aoi,_=vector_layer(reference,'areaOfInterestA_v1',grid.crs)
    footprints,footprint_properties=vector_layer(reference,'imageFootprintA_v1',grid.crs)
    post=[g for g,p in zip(footprints,footprint_properties) if p.get('or_src_id')==2]
    if not aoi or not post:raise ValueError('Reference coverage cannot be established')
    support=mask_geometry(water.valid,water.grid).intersection(unary_union(aoi)).intersection(unary_union(post))
    if support.is_empty:raise ValueError('No common independently covered area')
    temporal_geometry=mask_geometry(water.candidate,water.grid)
    pre,pre_valid,pre_grid,pre_meta=read_raster(root/'data/automatic'/cfg['run_id']/'prepared/pre.tif')
    post_values,post_valid,post_grid,post_meta=read_raster(root/'data/automatic'/cfg['run_id']/'prepared/post.tif')
    if pre_grid!=water.grid or post_grid!=water.grid:raise ValueError('SAR grids changed')
    original_manifest=json.loads((root/'artifacts/runs'/cfg['run_id']/'manifest.json').read_text())
    if pre_meta['sha256']!=original_manifest['pre']['sha256'] or post_meta['sha256']!=original_manifest['post']['sha256']:
        raise ValueError('SAR source identity mismatch')
    # Single-date source uses only post-event VV. The common evaluation support is
    # fixed by protocol, not changed to benefit either method.
    single=(post_values < -17)&post_valid
    single_geometry=mask_geometry(single,post_grid)
    source_cells=touched_cells(temporal_geometry,grid,hydro.valid)
    reachable=downstream_distances(hydro,source_cells)
    geometries,properties=vector_layer(reference,protocol['layer'],grid.crs)
    rows=[];exclusions=[]
    for geometry,prop in zip(geometries,properties):
        identity=prop['reference_feature_id'];grade=prop[protocol['label_field']]
        if grade in protocol['unknown_grades']:
            exclusions.append({'reference_id':identity,'reason':'UNKNOWN_REFERENCE_GRADE','grade':grade});continue
        if grade not in protocol['positive_grades']+protocol['negative_grades']:
            raise ValueError('Unrecognized reference grade')
        fragment=geometry.intersection(support)
        if fragment.is_empty or fragment.length<protocol['minimum_fragment_length_m']:
            exclusions.append({'reference_id':identity,'reason':'OUTSIDE_COMMON_SUPPORT_OR_TOO_SHORT','grade':grade});continue
        cells=touched_cells(fragment,grid,hydro.valid)
        direct_fraction=fragment.intersection(temporal_geometry).length/fragment.length
        single_fraction=fragment.intersection(single_geometry).length/fragment.length
        lengths=[reachable[c] for c in cells if c in reachable]
        network=min(lengths) if lengths else None
        # A source and receptor in one DEM cell without a path beyond that cell
        # remains unresolved. It is not assigned a connected score.
        same_cell=bool(source_cells&cells) and not direct_fraction and network is None
        terrain_score=(float(direct_fraction>0),float(network is not None),-network if network is not None else 0.0)
        full_score=None if not cells or same_cell else terrain_score
        hand=finite_stat(hydro.hand,cells)
        label=grade in protocol['positive_grades']
        centroid=fragment.centroid
        rows.append({'reference_id':identity,'reference_grade':grade,'label':label,'infrastructure_type':'road',
                     'evaluated_length_m':fragment.length,'original_length_m':geometry.length,
                     'reference_fragment_fraction':fragment.length/geometry.length,
                     'spatial_block':f'{int(centroid.x//protocol["spatial_block_m"])}:{int(centroid.y//protocol["spatial_block_m"])}',
                     'geometry':mapping(fragment),'scores':{
                         'A_image_only':single_fraction,'B_image_temporal':direct_fraction,
                         'C_temporal_terrain':terrain_score,'D_full_graph':full_score,
                         'proximity_only':-float(fragment.distance(temporal_geometry)),
                         'terrain_only':-hand if hand is not None else None,
                         'no_terrain_graph':direct_fraction,'no_temporal_information':single_fraction},
                     'attributes':{'direct_candidate_fraction':direct_fraction,'along_network_distance_m':network,
                                   'hand_m':hand,'same_cell_unresolved':same_cell,
                                   'interpretation':'Screening association, not damage/exposure validation'}})
    output.mkdir(parents=True)
    # Freeze identities, labels, support and parameters before metric calculation.
    freeze={'protocol_sha256':canonical_hash(protocol),'source_prediction_manifest_sha256':sha256(Path(prediction_run)/'manifest.json'),
            'reference_sha256':sha256(reference),'registration_audit_sha256':sha256(registration_audit),
            'evaluation_support_sha256':canonical_hash(mapping(support)),
            'rows_sha256':canonical_hash(rows),'receptor_ids':[r['reference_id'] for r in rows],
            'configuration_sha256':canonical_hash(cfg),'exclusions':exclusions,'split':protocol['split']}
    save_json(output/'freeze.json',freeze);save_json(output/'protocol.json',protocol)
    save_json(output/'rows.json',rows)
    save_json(output/'evaluation-support.geojson',{'type':'FeatureCollection','features':[{'type':'Feature',
        'geometry':mapping(project(support,grid.crs,'EPSG:4326')),'properties':{'role':'fixed evaluation support'}}]})
    labels=[r['label'] for r in rows]
    results={}
    for method in protocol['methods']:
        scores=[r['scores'][method] for r in rows]
        results[method]=ranking_metrics(scores,labels,protocol['k'])
        if method in ['A_image_only','B_image_temporal','C_temporal_terrain','D_full_graph']:
            observed=np.array([s is not None for s in scores],bool)
            decision=np.array([s>0 if isinstance(s,(float,int)) else bool(s[0] or s[1]) if s is not None else False for s in scores],bool)
            results[method]['conditional_confusion']=binary_metrics(decision,np.array(labels,bool),observed)
    paired={}
    for a,b in [('A_image_only','B_image_temporal'),('B_image_temporal','C_temporal_terrain'),
                ('C_temporal_terrain','D_full_graph'),('proximity_only','D_full_graph')]:
        ma,mb=results[a]['average_precision'],results[b]['average_precision']
        paired[a+'__to__'+b]={'average_precision_difference':None if ma is None or mb is None else mb-ma,
            'spatial_interval':paired_spatial_interval([r['scores'][a] for r in rows],[r['scores'][b] for r in rows],
                labels,[r['spatial_block'] for r in rows],protocol['bootstrap_replicates'],protocol['seed'])}
    report={'task':protocol['task'],'scientific_status':protocol['scientific_status'],
            'reference':{'publisher':'Copernicus EMS Rapid Mapping','product':'EMSR927 AOI01 GRA v1',
                         'url':'https://mapping.emergency.copernicus.eu/activations/EMSR927/',
                         'sha256':sha256(reference),'layer':protocol['layer'],'source_records':source_properties,
                         'grade_counts':dict(Counter(p[protocol['label_field']] for p in properties))},
            'common_denominator':len(rows),'excluded':exclusions,'results':results,'paired_differences':paired,
            'source_freeze':freeze,'registration':{k:registration[k] for k in ['status','physical_registration','reason']},
            'resolution':graph['resolution'],'seconds':time.perf_counter()-started,
            'blocked_tasks':{'water_extent':'UNAVAILABLE: no independent water-only labels',
                             'debris_extent':'UNAVAILABLE: mass-movement class is not the vegetation-loss proxy',
                             'building_precision':'UNAVAILABLE: reference building grades contain no known negatives',
                             'confidence_ablation':protocol['confidence_ablation'],
                             'H1_H3_validation':'BLOCKED: exposure labels, sufficient resolution and registration needed'},
            'limitations':[protocol['target_caveat'],'One previously inspected event; no untouched test or threshold tuning',
                'Road fragment inherits source-segment grade; no visible damage is not a no-exposure label',
                'Potential D8 path is not a dynamic floodwave or debris-flow simulation',
                'Registration unavailable; these are exploratory map associations, not validated accuracy']}
    save_json(output/'metrics.json',report)
    with (output/'metrics.csv').open('w',newline='',encoding='utf-8') as stream:
        writer=csv.DictWriter(stream,fieldnames=['method','n','positives','negatives','abstentions','average_precision','precision_at_5','recall_at_5','precision_at_10','recall_at_10'])
        writer.writeheader()
        for method,values in results.items():writer.writerow({'method':method,**{k:values.get(k) for k in writer.fieldnames if k!='method'}})
    save_json(output/'manifest.json',{'state':'complete','files':{p.name:sha256(p) for p in sorted(output.iterdir()) if p.is_file()},
                                     'population':'GENUINE_REFERENCE_SCREENING_DIAGNOSTIC','source_config_sha256':canonical_hash(protocol)})
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for arg in ['flood-root','terrain-source','prediction-run','output','registration-audit']:parser.add_argument('--'+arg,required=True)
    parser.add_argument('--protocol',default='research/experiments/nepal-road-screening.json')
    args=parser.parse_args();value=run(args.flood_root,args.terrain_source,args.prediction_run,args.protocol,args.output,args.registration_audit)
    print(json.dumps({k:value[k] for k in ['scientific_status','common_denominator','results','blocked_tasks']},indent=2))


if __name__=='__main__':main()
