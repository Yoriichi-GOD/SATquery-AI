"""Metrics with unknown labels, tied rankings and paired spatial resampling explicit."""
from __future__ import annotations

from collections import defaultdict
import numpy as np


def divide(a,b):
    return a/b if b else None


def binary_metrics(prediction, reference, valid):
    p,r,v=map(np.asarray,(prediction,reference,valid))
    if p.shape!=r.shape or p.shape!=v.shape or any(a.dtype!=bool for a in [p,r,v]):
        raise ValueError("Equal-shaped boolean prediction, reference and explicit support required")
    tp=int((p&r&v).sum());fp=int((p&~r&v).sum());fn=int((~p&r&v).sum());tn=int((~p&~r&v).sum())
    return {'status':'EVALUATED' if v.any() else 'UNAVAILABLE','tp':tp,'fp':fp,'fn':fn,'tn':tn,
            'evaluated':int(v.sum()),'ignored':int((~v).sum()),'iou':divide(tp,tp+fp+fn),
            'precision':divide(tp,tp+fp),'recall':divide(tp,tp+fn),'f1':divide(2*tp,2*tp+fp+fn)}


def ranking_metrics(scores, labels, ks=(5,10)):
    """Threshold AP. Boundary ties use expected inclusion, never arbitrary ID ordering.

    All labels must be known before entering this function. Missing scores remain
    abstentions, explicitly placed after all observed scores for a fixed denominator.
    This is not an assumption that unknown evidence is negative.
    """
    if len(scores)!=len(labels) or any(type(v) not in (bool,int,np.bool_) or v not in (0,1) for v in labels):
        raise ValueError("Ranking requires matched scores and known binary labels")
    groups=defaultdict(list); missing=[]
    for score,label in zip(scores,labels):
        if score is None:
            missing.append(int(label));continue
        key=tuple(float(v) for v in score) if isinstance(score,(tuple,list)) else (float(score),)
        if not np.isfinite(key).all():raise ValueError("Non-finite observed score")
        groups[key].append(int(label))
    ordered=[groups[key] for key in sorted(groups,reverse=True)]
    if missing:ordered.append(missing)
    n=len(labels);positives=int(sum(labels));seen=0;tp=0;ap=0.0
    for group in ordered:
        good=sum(group);seen+=len(group);tp+=good
        if positives:ap+=(good/positives)*(tp/seen)
    result={'n':n,'positives':positives,'negatives':n-positives,'abstentions':len(missing),
            'score_coverage':divide(n-len(missing),n),'average_precision':ap if positives else None,
            'tie_handling':'Threshold AP; expected precision/recall at tied K boundary',
            'abstention_policy':'Retained after all observed scores; fixed reference denominator'}
    for k in ks:
        if k<=0:raise ValueError('Positive K required')
        actual=min(k,n);remaining=actual;hits=0.0
        for group in ordered:
            take=min(remaining,len(group));hits+=take*sum(group)/len(group);remaining-=take
            if not remaining:break
        result[f'precision_at_{k}']=divide(hits,actual)
        result[f'recall_at_{k}']=divide(hits,positives)
        result[f'actual_k_{k}']=actual
    return result


def paired_spatial_interval(scores_a,scores_b,labels,blocks,replicates=500,seed=20261105):
    if not (len(scores_a)==len(scores_b)==len(labels)==len(blocks)):
        raise ValueError('Paired sample identities differ')
    names=sorted(set(blocks))
    if len(names)<5:
        return {'status':'UNAVAILABLE','reason':'Fewer than five spatial blocks','blocks':len(names),
                'interval':None,'resampling_unit':'spatial block, not pixel'}
    rng=np.random.default_rng(seed);deltas=[]
    for _ in range(replicates):
        chosen=rng.choice(len(names),len(names),replace=True)
        indices=[i for b in chosen for i,value in enumerate(blocks) if value==names[b]]
        y=[labels[i] for i in indices]
        a=ranking_metrics([scores_a[i] for i in indices],y)['average_precision']
        b=ranking_metrics([scores_b[i] for i in indices],y)['average_precision']
        if a is not None and b is not None:deltas.append(b-a)
    return {'status':'CONDITIONAL_SPATIAL_BOOTSTRAP','blocks':len(names),'replicates_requested':replicates,
            'replicates_with_both_classes_or_positive_labels':len(deltas),'seed':seed,
            'interval':np.percentile(deltas,[2.5,97.5]).tolist() if deltas else None,
            'resampling_unit':'spatial blocks shared between methods; one previously inspected event',
            'limitation':'Does not quantify event-to-event generalization, reference error or registration error'}


def reject_spatial_leakage(development_geometries,test_geometries):
    if any(a.intersects(b) for a in development_geometries for b in test_geometries):
        raise ValueError('Development/test geographic support overlaps')
