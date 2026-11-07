"""Separate evaluation entry point; only binary-compatible labels are accepted."""
import argparse,json
from pathlib import Path
import numpy as np
import rasterio
from .pipeline import digest,write_json


def binary_metrics(pred,truth,valid):
    if pred.shape!=truth.shape or pred.shape!=valid.shape:raise ValueError('Shape mismatch')
    p=pred[valid].astype(bool);t=truth[valid].astype(bool)
    tp=int((p&t).sum());fp=int((p&~t).sum());fn=int((~p&t).sum());tn=int((~p&~t).sum())
    ratio=lambda a,b: a/b if b else None
    return dict(tp=tp,fp=fp,fn=fn,tn=tn,valid_pixels=len(p),iou=ratio(tp,tp+fp+fn),f1=ratio(2*tp,2*tp+fp+fn),precision=ratio(tp,tp+fp),recall=ratio(tp,tp+fn))


def evaluate(run_dir,reference,classes_match=False):
    if not classes_match: raise ValueError('Explicit matching new-water semantics required')
    r=Path(run_dir);frozen=json.loads((r/'freeze.json').read_text())
    for name,sha in frozen['files'].items():
        if digest(r/name)!=sha: raise ValueError('Frozen artifact changed: '+name)
    with rasterio.open(r/'prediction.tif') as p,rasterio.open(reference) as t:
        if any(getattr(p,k)!=getattr(t,k) for k in ('crs','transform','width','height')): raise ValueError('Reference grid mismatch')
        pred=p.read(1); truth=t.read(1);valid=(pred!=255)&(t.read_masks(1)>0)&np.isin(truth,[0,1])
    result={'metrics':binary_metrics(pred==2,truth==1,valid),'reference_sha256':digest(reference),'prediction_sha256':digest(r/'prediction.tif'),'scope':'New-water candidates; one raster; not an event-generalization estimate'}
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('run_dir');p.add_argument('reference');p.add_argument('--matching-new-water-semantics',action='store_true');p.add_argument('--output',required=True);a=p.parse_args()
    output=Path(a.output).resolve()
    if output.is_relative_to(Path(a.run_dir).resolve()):raise ValueError('Store evaluation separately from frozen predictions')
    if output.exists():raise ValueError('Evaluation output already exists')
    write_json(output,evaluate(a.run_dir,a.reference,a.matching_new_water_semantics))
