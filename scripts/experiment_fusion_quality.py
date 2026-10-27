"""Validation-only quality gating; no test/Bolivia scores used for fitting."""
import argparse,hashlib,json,time
from pathlib import Path
import numpy as np
import rasterio

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def metrics(c):
    tp,fp,fn,tn=map(int,c)
    return dict(tp=tp,fp=fp,fn=fn,tn=tn,iou=tp/(tp+fp+fn) if tp+fp+fn else None)
def main():
    p=argparse.ArgumentParser();p.add_argument("--repo",type=Path,required=True);p.add_argument("--out",type=Path,required=True);a=p.parse_args()
    assert not a.out.exists();a.out.mkdir(parents=True)
    source=a.repo/"paired_lab/evidence/resumed/water-evaluation.json"
    manifest=dict(version=1,scope="Existing validation only, no test/Bolivia scoring or fitting",
        hypotheses="Input-quality proxies predict when to choose optical, SAR or joint",
        features=["optical_bright_fraction","shared_valid_fraction","sar_clip_fraction"],
        bright_rule="All B04/B03/B02 exceed 2500 DN among shared finite pixels; brightness proxy, not cloud classification",
        fixed_rule="Choose joint if optical_bright_fraction >=0.10, otherwise optical",
        fitted_rule="Leave one event prefix out; choose one depth-1 threshold rule by pooled IoU on other validation events",
        thresholds=[.01,.05,.10,.20,.50,.80,.95],
        leaves=["s2","all","s1"],tie_break="first candidate: fixed optical, joint, SAR, then deterministic feature/threshold/leaf order",
        intervals="1000 paired event bootstrap samples seed20261020; scene interval separately",
        limits=dict(seconds=300,disk_bytes=50*1024**2),source_sha256=sha(source),script_sha256=sha(Path(__file__)),
        caveats="Validation was already used for water checkpoint selection. Leave-event-out gating does not undo model exposure. No causal cloud or registration claim.")
    (a.out/"manifest.json").write_text(json.dumps(manifest,indent=2))
    start=time.monotonic()
    records=json.loads(source.read_text())["valid"]["samples"]
    data=Path("/root/satquery/paired-lab/sen1floods11")
    features=[];details=[]
    for row in records:
        arrays=[];hashes={}
        for layer in ("S1Hand","S2Hand"):
            path=data/layer/(row["sample"]+"_"+layer+".tif");hashes[layer]=sha(path)
            with rasterio.open(path) as ds:arrays.append(ds.read(masked=True).astype("float32").filled(np.nan))
        s1,s2=arrays;valid=np.isfinite(s1).all(0)&np.isfinite(s2).all(0)
        bright=float((s2[[3,2,1],:,:][:,valid]>2500).all(0).mean()) if valid.any() else 0.
        clip=float(((s1[:,valid]<-50)|(s1[:,valid]>10)).mean()) if valid.any() else 0.
        features.append([bright,float(valid.mean()),clip])
        details.append(dict(sample=row["sample"],event=row["sample"].split("_")[0],features=features[-1],sha256=hashes))
        assert time.monotonic()-start<300
    X=np.array(features);modes=["s2","all","s1"]
    C=np.array([[[row[m][k] for k in ("tp","fp","fn","tn")] for m in modes] for row in records])
    events=np.array([d["event"] for d in details]);n=len(records)
    rules=[dict(constant=i) for i in range(3)]
    for f in range(3):
        for threshold in manifest["thresholds"]:
            for low in range(3):
                for high in range(3):
                    if low!=high:rules.append(dict(feature=f,threshold=threshold,low=low,high=high))
    def choose(rule):
        return np.full(n,rule["constant"]) if "constant" in rule else np.where(X[:,rule["feature"]]>=rule["threshold"],rule["high"],rule["low"])
    choices=[choose(rule) for rule in rules]
    cross=np.zeros(n,dtype=int);folds=[]
    for event in sorted(set(events)):
        train=events!=event;test=~train;best=-1;selected=0
        for i,choice in enumerate(choices):
            met=metrics(C[np.arange(n)[train],choice[train]].sum(0));score=met["iou"]
            if score is not None and score>best:best=score;selected=i
        cross[test]=choices[selected][test]
        folds.append(dict(held_out_event=event,rule=rules[selected],other_events_iou=best))
    predictions={**{m:np.full(n,i) for i,m in enumerate(modes)},
                 "fixed_quality":np.where(X[:,0]>=.1,1,0),"cross_event_stump":cross}
    results={}
    for name,choice in predictions.items():
        selected=C[np.arange(n),choice];baseline=C[:,0]
        event_counts=np.array([selected[events==e].sum(0) for e in sorted(set(events))])
        event_base=np.array([baseline[events==e].sum(0) for e in sorted(set(events))])
        def ci(c,b):
            rng=np.random.default_rng(20261020);delta=[]
            for _ in range(1000):
                ix=rng.integers(0,len(c),len(c));ma,mb=metrics(c[ix].sum(0)),metrics(b[ix].sum(0))
                if ma["iou"] is not None and mb["iou"] is not None:delta.append((ma["iou"]-mb["iou"])*100)
            return list(map(float,np.percentile(delta,[2.5,97.5])))
        results[name]=dict(aggregate=metrics(selected.sum(0)),scene_ci_gain_pp=ci(selected,baseline),
             event_ci_gain_pp=ci(event_counts,event_base),selected_modes={m:int((choice==i).sum()) for i,m in enumerate(modes)},
             by_event={e:metrics(selected[events==e].sum(0)) for e in sorted(set(events))})
    report=dict(scope=manifest["scope"],results=results,folds=folds,inputs=details,
        rows=[dict(sample=r["sample"],event=events[i],counts={name:metrics(C[i,choice[i]]) for name,choice in predictions.items()}) for i,r in enumerate(records)],
        empty_scored_chips=[r["sample"] for i,r in enumerate(records) if C[i,0].sum()==0],
        note="Same historical shared valid/label denominator; no refusal or coverage advantage introduced",
        source_sha256=sha(source),seconds=time.monotonic()-start)
    (a.out/"results.json").write_text(json.dumps(report,indent=2))
    print(json.dumps({k:v for k,v in results.items()},indent=2))
if __name__=="__main__":main()
