"""Immutable evidence export and independent verification, shared by CLI and service."""
import csv
import importlib.metadata
import json
import os
import platform
import resource
import subprocess
import sys
import time
import zipfile
from pathlib import Path
from .common import contained,copy_stream,digest,fail,read_json,request_check,utc,write_json
from .contracts import REGISTRY,asset_inventory,preflight,report_csv
from .execution import execute,model_manifest,prediction_table
from .metrics import evaluate,protocol_check


def code_manifest():
    repo=Path(__file__).resolve().parents[2]
    try:
        revision=subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True,stderr=subprocess.DEVNULL).strip()
        dirty=subprocess.check_output(['git','-C',str(repo),'status','--porcelain','--untracked-files=no'],text=True,stderr=subprocess.DEVNULL).splitlines()
    except (OSError,subprocess.CalledProcessError):revision='unavailable';dirty=['source Git metadata unavailable']
    sources=list(Path(__file__).parent.glob('*.py'))+[repo/p for p in ['geo.py','paired_lab/inputs.py','paired_lab/flood.py','paired_lab/mci.py','paired_lab/sar_single.py','paired_lab/engine.py','paired_lab/spectral_pair.py','paired_lab/cdvqa_bridge.py']]
    return dict(revision=revision,tracked_worktree_changes=dirty,source_sha256={p.relative_to(repo).as_posix():digest(p) for p in sources},
        python=sys.version,platform=platform.platform(),packages={k:importlib.metadata.version(k) for k in ('numpy','rasterio','Pillow')})


def peak_rss():
    path=Path('/proc/self/status')
    if path.is_file():
        row=next(v for v in path.read_text().splitlines() if v.startswith('VmHWM:'))
        return int(row.split()[1])*1024,'Linux /proc/self/status VmHWM after exec'
    import psutil
    memory=psutil.Process().memory_info()
    return getattr(memory,'peak_wset',memory.rss),'Process peak working set, or current RSS if unavailable'


def mask_preview(source,target,ignore_values=None):
    import numpy as np
    import rasterio
    from PIL import Image
    from rasterio.windows import Window
    with rasterio.open(source,driver='GTiff') as ds:
        array=ds.read(1,window=Window(0,0,min(512,ds.width),min(512,ds.height)),masked=True)
        valid=~np.ma.getmaskarray(array)
        if ignore_values:valid&=~np.isin(array.data,ignore_values)
        rgba=np.zeros((*array.shape,4),dtype='uint8');rgba[valid]=[55,55,55,255]
        for value,colour in [(1,[214,182,106,255]),(2,[183,111,73,255])]:rgba[valid&(array.data==value)]=colour
        Image.fromarray(rgba).save(target)


def freeze_protocol(dataset,parameters):
    supplied=parameters.get('protocol')
    if supplied and supplied.get('dataset_revision')!=dataset['revision']:fail('DATASET_REVISION_MISMATCH','Protocol does not name the current inspected dataset revision.')
    if parameters.get('reference_id'):
        if not isinstance(supplied,dict):fail('EVALUATION_PROTOCOL_REQUIRED','Freeze an explicit evaluation protocol before execution with labels.')
        protocol_check(supplied)
        if supplied['dataset_revision']!=dataset['revision']:fail('DATASET_REVISION_MISMATCH','Protocol does not name the current inspected dataset revision.')
        return supplied
    # Prediction-only run: no independent evaluation or accuracy implied.
    return supplied or dict(task='prediction_only',dataset_revision=dataset['revision'],scene_ids=[dataset['id']],
        split='not scored',training_exposure='unknown',reference_provenance=None,license='Operator must supply original dataset licence; not redistributed by this tool.',excluded_case_ids=[])


def run(store,did,out,parameters,check=lambda:None,progress=lambda v:None):
    out=Path(out)
    request_check(parameters)
    if out.exists():fail('RUN_EXISTS','Choose a new immutable output directory; existing runs are never overwritten.')
    dataset=store.get(did)
    if not dataset.get('revision'):fail('DATASET_NOT_INSPECTED','Complete dataset inspection first.')
    protocol=freeze_protocol(dataset,parameters);out.mkdir(parents=True)
    started=time.perf_counter();timings={};failed=[];result=None;metrics=None
    write_json(out/'evaluation_protocol.json',protocol)
    write_json(out/'request.json',parameters)
    code=code_manifest();write_json(out/'software_manifest.json',code)
    write_json(out/'dataset_manifest.json',dataset)
    write_json(out/'preprocessing_manifest.json',dict(intake_transformations=[],policy='Original bytes retained. No implicit resize, reprojection, band repair, NoData filling or unit guessing.',parameters=parameters))
    try:
        inputs=parameters.get('inputs')
        assets=asset_inventory();report=preflight(dataset,inputs,assets,parameters,root=store.directory(did))
        write_json(out/'compatibility_report.json',report);(out/'compatibility_report.csv').write_text(report_csv(report),encoding='utf-8')
        lookup={f['id']:f for f in dataset['files']}
        selected=[lookup[i] for i in (inputs or report['selected_inputs']) if i in lookup]
        if inputs is not None and len(selected)!=len(inputs):fail('FILE_NOT_FOUND','A selected file is not in this dataset.')
        reference=lookup.get(parameters.get('reference_id'))
        imported_prediction=lookup.get(parameters.get('prediction_id'))
        if parameters.get('reference_id') and (not reference or reference['role']!='reference'):fail('INVALID_REFERENCE','Use a registered file explicitly assigned the independent reference role.')
        if reference and reference['state']!='INSPECTED':fail('INVALID_REFERENCE','The selected reference did not pass intake inspection.')
        if imported_prediction and imported_prediction['state']!='INSPECTED':fail('INVALID_PREDICTION','The selected prediction did not pass intake inspection.')
        for file in dataset['files']:
            check()
            if file.get('sha256') and digest(contained(store.directory(did),file['path']),check)!=file['sha256']:
                fail('DATASET_HASH_MISMATCH','Stored original hash changed; no analysis/evaluation was accepted.')
        if parameters.get('prediction_job_id'):
            previous=contained(store.root.parent/'jobs',parameters['prediction_job_id'])
            prior=read_json(previous/'job.json')
            if prior['dataset_id']!=did or prior['state'] not in ('EVALUATED','EVALUATION_NOT_POSSIBLE'):fail('INVALID_PREDICTION','Choose a completed prediction from this same dataset.')
            verify(previous/'evidence')
            prior_dataset=read_json(previous/'evidence/dataset_manifest.json')
            if any(f['id'] not in lookup or lookup[f['id']].get('sha256')!=f.get('sha256') for f in prior_dataset['files']):fail('DATASET_HASH_MISMATCH','The prior prediction source files differ from this dataset.')
            name='predicted_mask.tif' if protocol['task']=='segmentation' else 'predictions.csv'
            copy_stream(previous/'evidence'/name,out/name,check)
            if name.endswith('.tif'):prediction_table(out,{},protocol['scene_ids'],'unchanged prior prediction')
            model=read_json(previous/'evidence/model_manifest.json');model['reused_prediction_from_job']=parameters['prediction_job_id']
            previous_specialist=model.get('specialist')
            semantics={'water_map':'water','ndvi':'ndvi_threshold','temporal':'road_building_change'}
            if protocol['task']=='segmentation' and protocol.get('prediction_semantics')!=semantics.get(previous_specialist):fail('LABEL_SEMANTICS_MISMATCH','Declare the exact semantics of this unchanged prior model output.')
            result=dict(task='independent_evaluation_of_unchanged_prediction',prior_job_id=parameters['prediction_job_id'])
        elif imported_prediction:
            if imported_prediction['role']!='prediction':fail('INVALID_PREDICTION','Imported predictions must have the prediction role.')
            extension='.tif' if imported_prediction.get('raster') else '.csv'
            copy_stream(contained(store.directory(did),imported_prediction['path']),out/('predicted_mask.tif' if extension=='.tif' else 'predictions.csv'),check)
            model=dict(specialist='imported_prediction',model='Not independently authenticated; operator-supplied predictions',source_sha256=imported_prediction['sha256'])
            if extension=='.tif':prediction_table(out,{},protocol['scene_ids'],'imported categorical prediction')
            result=dict(task='independent_evaluation_of_imported_predictions',prediction_origin=model)
        else:
            specialist=parameters.get('specialist')
            if specialist not in REGISTRY:fail('UNSUPPORTED_TASK','Select one named registered specialist; no unrelated fallback is used.')
            choice=next(r for r in report['specialists'] if r['specialist']==specialist)
            if not choice['eligible']:fail(choice['status'],'Specialist preflight failed. Inspect every blocking parameter in compatibility_report.json.')
            if specialist=='vqa':fail('UNSUPPORTED_TASK','The shared Qwen worker lacks a verifiable cancellation adapter; external execution is withheld.')
            model=model_manifest(specialist,assets[specialist],check)
            write_json(out/'model_manifest.json',model);check();start=time.perf_counter()
            result,kind=execute(specialist,selected,store.directory(did),out,parameters,check,progress)
            timings['inference_seconds']=time.perf_counter()-start
            prediction_table(out,result,protocol['scene_ids'],kind)
            if reference:
                expected='vqa' if kind=='vqa' else 'multilabel' if kind=='multilabel' else 'segmentation'
                if protocol['task']!=expected:fail('TASK_PROTOCOL_MISMATCH','Reference protocol task differs from the actual specialist output.')
                if expected=='segmentation' and protocol.get('prediction_semantics')!=kind:
                    fail('LABEL_SEMANTICS_MISMATCH','Freeze prediction_semantics='+str(kind)+' and the actual reference class mapping; a flood/land-cover label is not assumed equivalent.')
        write_json(out/'model_manifest.json',model);write_json(out/'result.json',result)
        check();progress(dict(stage='Evaluating independent labels' if reference else 'Exporting predictions without an accuracy claim'))
        start=time.perf_counter()
        if reference:
            extension='.tif' if reference.get('raster') else '.csv'
            copy_stream(contained(store.directory(did),reference['path']),out/('reference'+extension),check)
            prediction=out/'predicted_mask.tif' if protocol['task']=='segmentation' else out/'predictions.csv'
            metrics=evaluate(prediction,out/('reference'+extension),protocol,check)
        else:metrics=evaluate(None,None,{})
        timings['evaluation_seconds']=time.perf_counter()-start
        write_json(out/'metrics.json',metrics)
        if metrics.get('confusion_matrix'):
            with (out/'confusion_matrix.csv').open('w',newline='',encoding='utf-8') as stream:
                writer=csv.writer(stream);writer.writerow(['reference/prediction']+metrics['confusion_order'])
                for label,row in zip(metrics['confusion_order'],metrics['confusion_matrix']):writer.writerow([label]+row)
        elif protocol.get('task')=='multilabel' and metrics['state']=='EVALUATED':
            with (out/'confusion_matrix.csv').open('w',newline='',encoding='utf-8') as stream:
                writer=csv.writer(stream);writer.writerow(['class_id','TP','FP','TN','FN'])
                for row in metrics['per_class']:writer.writerow([row[k] for k in ('class_id','TP','FP','TN','FN')])
    except Exception as exc:
        failed.append(dict(code=getattr(exc,'code','PROCESSING_FAILED'),message=str(exc),at_utc=utc()))
        metrics=dict(state='CANCELLED' if getattr(exc,'code',None)=='CANCELLED' else 'PROCESSING_FAILED',failures=failed)
        write_json(out/'metrics.json',metrics)
    finally:
        if metrics and metrics['state'] in ('EVALUATED','EVALUATION_NOT_POSSIBLE'):
            for name,target in [('predicted_mask.tif','prediction-preview.png'),('reference.tif','reference-preview.png')]:
                if (out/name).exists():mask_preview(out/name,out/target,protocol.get('ignore_values') if name=='reference.tif' else None)
        write_json(out/'failures.json',failed)
        for name,placeholder in [('model_manifest.json',{'status':'not executed'}),('compatibility_report.json',{'status':'preflight not reached'})]:
            if not (out/name).exists():write_json(out/name,placeholder)
        if not (out/'compatibility_report.csv').exists():(out/'compatibility_report.csv').write_text('specialist,parameter,status\n',encoding='utf-8')
        if not (out/'predictions.csv').exists():(out/'predictions.csv').write_text('case_id,status\n',encoding='utf-8')
        peak,method=peak_rss()
        timings.update(total_worker_seconds=time.perf_counter()-started,peak_rss_bytes=peak,peak_rss_method=method,
            rss_scope='This isolated worker, including metric/model imports. A remote/shared service GPU process is not included.',
            input_bytes=sum(f['bytes'] for f in dataset['files']),export_bytes_before_zip=sum(p.stat().st_size for p in out.iterdir() if p.is_file()))
        write_json(out/'timings.json',timings)
        (out/'metrics.md').write_text('# External evaluation\n\n'+metrics['state']+'\n\n```json\n'+json.dumps(metrics,indent=2)+'\n```\n\nNo score is inferred from prediction coverage. Undefined denominators remain null.\n',encoding='utf-8')
        (out/'reproduce.md').write_text('# Independent verification\n\nFrom the repository in a provisioned Python environment:\n\n```sh\npython scripts/verify_external.py /absolute/path/to/this/run\npython scripts/evaluate_external.py --dataset /absolute/path/to/private/dataset_manifest.json --request /absolute/path/to/this/run/request.json --output /absolute/path/to/a/new/run\n```\n\nInstall requirements-test.txt for raster/metric verification; model execution needs the assets and dependencies listed in model_manifest.json and docs/ASSETS.md. Keep source files at their registered private dataset paths, or import the same licensed bytes again and freeze a new revision. Predictions and the supplied reference copy in this export can be evaluated without model weights or the dashboard. Protocol parameters, software versions and source hashes are frozen in the JSON manifests.\n\nDataset licensing: '+str(protocol.get('license'))+'\nReference provenance: '+str(protocol.get('reference_provenance'))+'\nNo model weights are redistributed. This package verifies internal consistency, not independent sensor/source authenticity.\n',encoding='utf-8')
        lines=[digest(p)+'  '+p.name for p in sorted(out.iterdir()) if p.is_file() and p.name not in ('checksums.sha256','evidence.zip')]
        (out/'checksums.sha256').write_text('\n'.join(lines)+'\n',encoding='utf-8')
        with zipfile.ZipFile(out/'evidence.zip','x',zipfile.ZIP_DEFLATED) as archive:
            for p in sorted(out.iterdir()):
                if p.is_file() and p.name!='evidence.zip':archive.write(p,p.name)
    return dict(state=metrics['state'],metrics=metrics,failures=failed,timings=timings,artifacts=sorted(p.name for p in out.iterdir() if p.is_file()))


def verify(out):
    out=Path(out);expected={}
    for line in (out/'checksums.sha256').read_text(encoding='utf-8').splitlines():
        sha,name=line.split('  ',1)
        if '/' in name or '\\' in name or name in expected:fail('INVALID_CHECKSUM_MANIFEST','Invalid or duplicate artifact name.')
        path=contained(out,name)
        if not path.is_file() or digest(path)!=sha:fail('EXPORT_HASH_MISMATCH','Export artifact differs: '+name)
        expected[name]=sha
    required={'dataset_manifest.json','compatibility_report.json','compatibility_report.csv','preprocessing_manifest.json','model_manifest.json','predictions.csv','metrics.json','metrics.md','timings.json','failures.json','reproduce.md','evaluation_protocol.json','software_manifest.json'}
    if not required.issubset(expected):fail('INCOMPLETE_EXPORT','Required evidence files are missing.')
    actual={p.name for p in out.iterdir() if p.is_file()}-{'checksums.sha256','evidence.zip'}
    if actual!=set(expected):fail('INCOMPLETE_CHECKSUMS','Unexpected or unhashed export artifacts exist.')
    metrics=read_json(out/'metrics.json');protocol=read_json(out/'evaluation_protocol.json')
    if metrics['state']=='EVALUATED':
        prediction=out/'predicted_mask.tif' if protocol['task']=='segmentation' else out/'predictions.csv'
        reference=out/'reference.tif' if protocol['task']=='segmentation' else out/'reference.csv'
        recomputed=evaluate(prediction,reference,protocol)
        if recomputed!=metrics:fail('METRIC_RECOMPUTE_MISMATCH','Recomputed source/reference metrics differ from the export.')
    elif metrics['state']=='EVALUATION_NOT_POSSIBLE':
        if any(key in metrics for key in ('accuracy','IoU','F1','pixel_accuracy','per_class')):fail('FABRICATED_SCORE','Prediction-only evidence must not contain evaluation scores.')
    return dict(status='VERIFIED',artifacts=len(expected),metrics_recomputed=metrics['state']=='EVALUATED',run_state=metrics['state'],
        limitation='Checks consistency of supplied artifacts; not independent source authenticity or unseen-data accuracy.')
