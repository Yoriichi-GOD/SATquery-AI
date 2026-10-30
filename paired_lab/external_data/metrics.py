"""Independent metrics from explicit class/ignore semantics; no prediction-only accuracy."""
import csv
from pathlib import Path
import numpy as np
import rasterio
from .common import CHUNK, fail
from .raster import ENV, windows


def protocol_check(protocol):
    for key in ('task','dataset_revision','scene_ids','split','reference_provenance','license','training_exposure','excluded_case_ids'):
        if key not in protocol or protocol[key] is None or protocol[key]=='':fail('INCOMPLETE_PROTOCOL','Freeze protocol field: '+key)
    if protocol['task'] not in ('segmentation','classification','multilabel','vqa'):fail('UNSUPPORTED_TASK','Choose segmentation, classification, multilabel or VQA metrics.')
    if not isinstance(protocol['scene_ids'],list) or not protocol['scene_ids'] or len(set(protocol['scene_ids']))!=len(protocol['scene_ids']):fail('INVALID_PROTOCOL','Scene IDs must be a nonempty unique list.')
    if protocol['split'] not in ('evaluation','test','development'):fail('INVALID_PROTOCOL','Declare evaluation, test or development split.')
    if protocol['task']!='vqa':
        if not isinstance(protocol.get('classes'),dict) or not 1<=len(protocol['classes'])<=64:fail('CLASS_MAPPING_REQUIRED','Declare 1–64 explicit class IDs and their semantics.')
        if any(not isinstance(v,str) or not v for v in protocol['classes'].values()):fail('CLASS_MAPPING_REQUIRED','Every class needs a semantic name.')
    if protocol['task']=='segmentation':
        for key in ('prediction_class_mapping','reference_class_mapping','ignore_values'):
            if key not in protocol:fail('CLASS_MAPPING_REQUIRED','Freeze '+key+'; no label convention is guessed.')
        if not isinstance(protocol['ignore_values'],list):fail('INVALID_PROTOCOL','Ignore values must be an explicit list, including [] if none.')
        try:
            classes={int(k) for k in protocol['classes']}
            for key in ('prediction_class_mapping','reference_class_mapping'):
                mapping=protocol[key]
                if not isinstance(mapping,dict) or not mapping or any(int(v) not in classes for v in mapping.values()):raise ValueError()
                if any(str(int(k))!=k for k in mapping):raise ValueError()
        except (ValueError,TypeError):fail('CLASS_MAPPING_REQUIRED','Raster mappings need integer native labels mapped to declared integer classes.')
    if protocol['task']=='vqa' and protocol.get('answer_normalization') not in ('exact','casefold_whitespace'):
        fail('INVALID_PROTOCOL','Freeze exact or casefold_whitespace answer normalization.')
    return protocol


def divide(a,b):
    return float(a/b) if b else None


def mean(values):
    values=[v for v in values if v is not None]
    return float(sum(values)/len(values)) if values else None


def from_confusion(matrix, classes):
    matrix=np.asarray(matrix,dtype='int64');total=int(matrix.sum());rows=[]
    if not total:fail('NO_VALID_PIXELS','No evaluable pixels/cases remain; all accuracy and overlap scores are undefined.')
    for i,label in enumerate(classes):
        tp=int(matrix[i,i]);fn=int(matrix[i].sum())-tp;fp=int(matrix[:,i].sum())-tp;tn=total-tp-fn-fp
        rows.append(dict(class_id=label,class_name=classes[label],TP=tp,FP=fp,TN=tn,FN=fn,
            support=tp+fn,predicted=tp+fp,class_frequency=divide(tp+fn,total),
            IoU=divide(tp,tp+fp+fn),precision=divide(tp,tp+fp),recall=divide(tp,tp+fn),F1=divide(2*tp,2*tp+fp+fn)))
    tp=sum(r['TP'] for r in rows);fp=sum(r['FP'] for r in rows);fn=sum(r['FN'] for r in rows)
    return dict(per_class=rows,confusion_matrix=matrix.tolist(),confusion_order=list(classes),confusion_orientation='rows reference; columns prediction',
        denominator=total,accuracy=divide(int(np.trace(matrix)),total),
        macro=dict(IoU=mean([r['IoU'] for r in rows]),precision=mean([r['precision'] for r in rows]),recall=mean([r['recall'] for r in rows]),F1=mean([r['F1'] for r in rows])),
        micro=dict(IoU=divide(tp,tp+fp+fn),precision=divide(tp,tp+fp),recall=divide(tp,tp+fn),F1=divide(2*tp,2*tp+fp+fn)),
        undefined_rule='Zero-denominator class scores are null and excluded from that macro mean; support is retained.',
        accuracy_limitation='Accuracy may hide rare-class errors and is not interchangeable with per-class IoU/F1.')


def segmentation(prediction,reference,protocol,check=lambda:None):
    protocol_check(protocol)
    classes={str(k):v for k,v in sorted(protocol['classes'].items(),key=lambda x:int(x[0]))};order={int(k):i for i,k in enumerate(classes)}
    mappings=[{int(k):int(v) for k,v in protocol[key].items()} for key in ('prediction_class_mapping','reference_class_mapping')]
    matrix=np.zeros((len(order),len(order)),dtype='int64');total=valid_count=ref_invalid=pred_invalid=ignored=0
    with rasterio.Env(**ENV),rasterio.open(prediction,driver='GTiff') as p,rasterio.open(reference,driver='GTiff') as r:
        if p.count!=1 or r.count!=1:fail('LABEL_BAND_MISMATCH','Prediction and reference each require one categorical band.')
        if any(np.dtype(t).kind not in 'ui' for t in p.dtypes+r.dtypes):fail('LABEL_DTYPE_MISMATCH','Categorical prediction/reference labels must use integer rasters.')
        if not p.crs or not r.crs or p.crs!=r.crs or p.shape!=r.shape or not np.allclose(list(p.transform),list(r.transform),rtol=0,atol=1e-10):
            fail('LABEL_ALIGNMENT_MISMATCH','Prediction/reference CRS, dimensions and affine must match. No implicit reprojection.')
        if not all(np.isfinite(list(p.transform))) or abs(p.transform.determinant)<1e-15:fail('INVALID_TRANSFORM','Cannot evaluate a singular or non-finite grid.')
        for window in windows(p.width,p.height):
            check();pa=p.read(1,window=window,masked=True);ra=r.read(1,window=window,masked=True)
            pv=~np.ma.getmaskarray(pa);rv=~np.ma.getmaskarray(ra);iv=np.isin(ra.data,protocol['ignore_values'])
            usable=pv&rv&~iv;total+=usable.size;valid_count+=int(usable.sum())
            ref_invalid+=int((~rv).sum());pred_invalid+=int((~pv).sum());ignored+=int((rv&iv).sum())
            native=[pa.data[usable],ra.data[usable]];mapped=[]
            for array,mapping in zip(native,mappings):
                unknown=set(int(v) for v in np.unique(array))-set(mapping)
                if unknown:fail('CLASS_MISMATCH','Unmapped native labels encountered: '+str(sorted(unknown)))
                result=np.empty(array.size,dtype='int16')
                for raw,target in mapping.items():result[array==raw]=order[target]
                mapped.append(result)
            matrix+=np.bincount(mapped[1]*len(order)+mapped[0],minlength=len(order)**2).reshape(matrix.shape)
    result=from_confusion(matrix,classes)
    result.update(task='segmentation',state='EVALUATED',total_pixels=total,valid_pixels=valid_count,
        excluded_pixels=total-valid_count,reference_nodata_pixels=ref_invalid,prediction_nodata_pixels=pred_invalid,
        explicit_reference_ignore_pixels=ignored,coverage_fraction=divide(valid_count,total),
        pixel_accuracy=result.pop('accuracy'),class_semantics=protocol['classes'],
        denominator_rule='Only jointly valid prediction/reference pixels outside explicit reference ignore values; exclusion categories may overlap.')
    return result


def table(path,required):
    if Path(path).stat().st_size>16*CHUNK:fail('TABLE_LIMIT','This checkpoint accepts label tables up to 16 MiB; batch larger tables explicitly.')
    with Path(path).open(encoding='utf-8-sig',newline='') as stream:
        reader=csv.DictReader(stream)
        if not set(required).issubset(reader.fieldnames or []):fail('TABLE_COLUMNS','Required table columns: '+','.join(required))
        return list(reader)


def table_metrics(prediction,reference,protocol):
    protocol_check(protocol);task=protocol['task']
    column='answer' if task=='vqa' else 'label' if task=='classification' else 'class_name'
    required=['case_id',column]+(['value'] if task=='multilabel' else [])
    tables=[table(path,required) for path in (prediction,reference)]
    if task!='multilabel' and any(len({r['case_id'] for r in rows})!=len(rows) for rows in tables):fail('DUPLICATE_CASE','Case IDs must be unique.')
    ids=[{r['case_id'] for r in rows} for rows in tables];excluded=set(protocol['excluded_case_ids']);frozen=set(protocol['scene_ids'])
    if ids[0]-excluded!=ids[1]-excluded or ids[1]-excluded!=frozen-excluded:
        fail('CASE_POPULATION_MISMATCH','Prediction, reference and frozen scene IDs must match after predeclared exclusions. No silent dropping.')
    selected=sorted(frozen-excluded)
    if not selected:fail('NO_VALID_CASES','No evaluable cases remain.')
    if task=='vqa':
        p,r=[{v['case_id']:v['answer'] for v in rows} for rows in tables]
        normalize=(lambda value:value) if protocol['answer_normalization']=='exact' else (lambda value:' '.join(value.casefold().split()))
        count=sum(normalize(p[k])==normalize(r[k]) for k in selected)
        return dict(state='EVALUATED',task='vqa',correct=count,denominator=len(selected),exact_match=count/len(selected),
            normalization=protocol['answer_normalization'],predictions=len(p),references=len(r),excluded_cases=sorted(excluded),
            interpretation='Question-answer metric only; captions are not segmentation masks.')
    classes={str(k):v for k,v in protocol['classes'].items()}
    if task=='classification':
        order={k:i for i,k in enumerate(classes)};p,r=[{v['case_id']:v['label'] for v in rows} for rows in tables]
        if any(v[k] not in order for v in (p,r) for k in selected):fail('CLASS_MISMATCH','Table contains an undeclared class ID.')
        matrix=np.zeros((len(order),len(order)),dtype='int64')
        for k in selected:matrix[order[r[k]],order[p[k]]]+=1
        result=from_confusion(matrix,classes);result.update(state='EVALUATED',task=task,predictions=len(p),references=len(r),excluded_cases=sorted(excluded));return result
    indexed=[]
    for rows in tables:
        values={}
        for row in rows:
            key=(row['case_id'],row['class_name'])
            if key in values:fail('DUPLICATE_CASE','Multilabel case/class pairs must be unique.')
            if row['class_name'] not in classes or row['value'] not in ('0','1'):fail('CLASS_MISMATCH','Multilabel values must be explicit 0/1 for each declared class ID.')
            values[key]=int(row['value'])
        if any((k,c) not in values for k in selected for c in classes):fail('MISSING_MULTILABEL_VALUE','Missing case/class labels cannot be assumed negative.')
        indexed.append(values)
    p,r=indexed;metrics=[]
    for c,label in classes.items():
        a=np.array([p[k,c] for k in selected]);b=np.array([r[k,c] for k in selected]);tp=int(((a==1)&(b==1)).sum());fp=int(((a==1)&(b==0)).sum());fn=int(((a==0)&(b==1)).sum());tn=len(a)-tp-fp-fn
        metrics.append(dict(class_id=c,class_name=label,TP=tp,FP=fp,TN=tn,FN=fn,support=tp+fn,precision=divide(tp,tp+fp),recall=divide(tp,tp+fn),F1=divide(2*tp,2*tp+fp+fn)))
    tp=sum(v['TP'] for v in metrics);fp=sum(v['FP'] for v in metrics);fn=sum(v['FN'] for v in metrics)
    return dict(state='EVALUATED',task='multilabel',per_class=metrics,denominator_cases=len(selected),label_decisions=len(selected)*len(classes),
        micro=dict(precision=divide(tp,tp+fp),recall=divide(tp,tp+fn),F1=divide(2*tp,2*tp+fp+fn)),macro_F1=mean([v['F1'] for v in metrics]),
        confusion_matrix_kind='One binary TP/FP/TN/FN matrix per class; not a single-label matrix.',excluded_cases=sorted(excluded))


def evaluate(prediction,reference,protocol,check=lambda:None):
    if reference is None:return dict(state='EVALUATION_NOT_POSSIBLE',code='COMPATIBLE_GROUND_TRUTH_NOT_PROVIDED',message='EVALUATION_NOT_POSSIBLE — COMPATIBLE_GROUND_TRUTH_NOT_PROVIDED')
    return segmentation(prediction,reference,protocol,check) if protocol['task']=='segmentation' else table_metrics(prediction,reference,protocol)
