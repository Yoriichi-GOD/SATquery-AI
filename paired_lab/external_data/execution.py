"""Reuse existing bounded specialists. No model substitution or automatic raster preparation."""
import csv
import json
import sys
from pathlib import Path
import numpy as np
import rasterio
from .common import copy_stream, digest, fail


def model_manifest(specialist,availability,check=lambda:None):
    from scripts.preflight import inventory
    specs={v['id']:v for v in inventory()}
    rows=[]
    for record in availability.get('assets',[]):
        path=Path(record['path']);files=[path] if path.is_file() else sorted(p for p in path.iterdir() if p.is_file() and p.suffix in ('.safetensors','.bin','.pt','.pth','.json')) if path.is_dir() else []
        if record['id']=='configilm':files.append(path/'configilm/extra/BENv2_utils.py')
        hashes=[dict(name=f.relative_to(path).as_posix() if path.is_dir() else f.name,bytes=f.stat().st_size,sha256=digest(f,check)) for f in files]
        expected=specs.get(record['id'],{})
        if path.is_file() and expected.get('sha256') and hashes[0]['sha256']!=expected['sha256']:fail('MODEL_HASH_MISMATCH','Checkpoint differs from the pinned source inventory; no model was substituted.')
        rows.append(dict(id=record['id'],path=str(path),source=expected.get('source'),revision=expected.get('revision'),expected_sha256=expected.get('sha256'),files=hashes))
    return dict(specialist=specialist,assets=rows,dependencies=availability.get('dependencies',{}),
        checkpoint_policy='Actual existing checkpoints only; no retraining, fallback model or network acquisition.')


def categorical(path,values,source,semantics,threshold=None):
    with rasterio.open(source) as src:
        profile={k:src.profile[k] for k in ('crs','transform','height','width')}
    profile.update(driver='GTiff',count=1,dtype='uint8',nodata=255,compress='deflate')
    with rasterio.open(path,'w',**profile) as dst:
        dst.write(values.astype('uint8'),1);dst.set_band_description(1,semantics)
        dst.update_tags(prediction_semantics=semantics,threshold=str(threshold) if threshold is not None else 'not applicable')


def execute(specialist,files,root,out,parameters,check,progress):
    # Rechecked by the caller against the full preflight before any model import.
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
    paths=[root/f['path'] for f in files]
    if specialist=='vqa':fail('UNSUPPORTED_TASK','External Qwen execution is withheld until the shared single-image worker has a verifiable cancellation boundary. Use the existing Workspace for optical interpretation.')
    if specialist=='flood_lab':fail('UNSUPPORTED_TASK','Use the existing Flood Lab prepared event/OSM workflow; arbitrary external TIFFs are not an event manifest.')
    if specialist=='ndvi':
        import geo
        result=geo.analyse(paths[0],out,float(parameters.get('threshold',.5)))
        with rasterio.open(out/'ndvi.tif') as ds:arr=ds.read(1)
        threshold=float(parameters.get('threshold',.5));values=np.where(np.isfinite(arr),(arr>=threshold).astype('uint8'),255)
        categorical(out/'predicted_mask.tif',values,paths[0],'ndvi_threshold',threshold)
        return dict(task='ndvi',statistics=result,threshold=threshold), 'ndvi_threshold'
    if specialist=='terrain':
        from jai_extension.terrain import slope_degrees,grid_summary
        with rasterio.open(paths[0]) as src:
            elevation=src.read(1,masked=True).astype('float32').filled(np.nan);resolution=src.res;transform=src.transform;crs=src.crs
        # Existing Horn operator and native metre spacing. No new terrain reprojection.
        slope=slope_degrees(elevation,np.isfinite(elevation),resolution[0],resolution[1])
        good=np.isfinite(elevation);valid=np.isfinite(slope)
        statistics,_=grid_summary(elevation,good,transform,crs)
        result=dict(task='terrain',statistics=statistics,valid_pixels=int(good.sum()),total_pixels=elevation.size,
            elevation_min_m=float(elevation[good].min()),elevation_max_m=float(elevation[good].max()),
            median_slope_deg=float(np.median(slope[valid])) if valid.any() else None,
            limitation='Known metre source units required; datum/provenance not independently certified. No hazard inference.')
        with rasterio.open(paths[0]) as src:profile=src.profile.copy()
        profile.update(count=1,dtype='float32',nodata=np.nan)
        with rasterio.open(out/'slope.tif','w',**profile) as dst:dst.write(slope.astype('float32'),1)
        return result,None
    if specialist=='cdvqa':
        import cdvqa_bridge
        records=[]
        for file,path in zip(files,paths):
            r=cdvqa_bridge.inspect_rgb(path);r['name']=file['name'];records.append(r)
        cdvqa_bridge.validate(records,parameters.get('aligned_ordered'))
        question=parameters.get('question','')
        if not cdvqa_bridge.supported(question):fail('UNSUPPORTED_TASK','Question is outside the exact frozen CDVQA templates.')
        return cdvqa_bridge.run(records,question,out,progress), 'vqa'
    from inputs import inspect,validate
    records=[]
    for file,path in zip(files,paths):
        sensor=file['raster']['tags'].get('sensor','')
        modality='sar' if sensor in ('Sentinel-1','Sentinel-1 GRD') else 'optical'
        record=inspect(path,modality);record['name']=file['name'];records.append(record)
    check()
    if specialist=='water_map':
        import flood
        validate(records,'water_map')
        optical=next(r for r in records if r['modality']=='optical');sar=next(r for r in records if r['modality']=='sar')
        with rasterio.open(optical['path']) as src:profile=src.profile.copy()
        result=flood.segment(sar['data'],optical['data'],out,profile,progress)
        copy_stream(out/'water-mask.tif',out/'predicted_mask.tif',check)
        return result,'water'
    if specialist=='spectral_pair':
        import spectral_pair
        return spectral_pair.analyse(records,['vegetation','water'],float(parameters.get('threshold',.5)),float(parameters.get('water_threshold',0)),out,progress),None
    if specialist=='temporal':
        import mci
        validate(records,'temporal',enforce_content=True)
        result=mci.temporal(records[0]['data'].transpose(1,2,0),records[1]['data'].transpose(1,2,0),out,progress)
        with np.load(out/'scores.npz',allow_pickle=False) as z:mask=z['classes']
        categorical(out/'predicted_mask.tif',mask,paths[0],'road_building_change')
        return result,'road_building_change'
    if specialist=='optical_sar':
        import engine
        validate(records,'optical_sar')
        bands={name:r['data'][i] for r in records for i,name in enumerate(r['bands'])}
        return engine.fusion(bands,out,progress),'multilabel'
    if specialist=='sar_scene':
        import sar_single
        return sar_single.run(records[0],out,progress),'multilabel'
    fail('UNSUPPORTED_TASK','No executable adapter exists for this specialist.')


def prediction_table(out,result,scene_ids,kind):
    with (out/'predictions.csv').open('w',newline='',encoding='utf-8') as stream:
        if kind=='vqa':
            writer=csv.writer(stream);writer.writerow(['case_id','answer']);writer.writerow([scene_ids[0],result['answer']])
        elif kind=='multilabel':
            writer=csv.writer(stream);writer.writerow(['case_id','class_name','value'])
            scores=result['scores'].get('all',result['scores'])
            for name,score in scores.items():writer.writerow([scene_ids[0],name,int(score>=.5)])
        else:
            writer=csv.writer(stream);writer.writerow(['case_id','prediction_file','output_kind'])
            writer.writerow([scene_ids[0],'predicted_mask.tif' if (out/'predicted_mask.tif').exists() else 'result.json',kind or 'numerical evidence; no categorical evaluation output'])
