"""Reaggregate existing confusion counts; no inference, label changes or selection."""
import collections
import csv
import hashlib
import json
from pathlib import Path

import numpy as np


def interval(counts):
    """Paired pooled-IoU difference, sampling scenes/events rather than pixels."""
    rng=np.random.default_rng(20261020);gains=[]
    values=np.asarray(counts,dtype=np.int64)
    for _ in range(1000):
        totals=values[rng.integers(0,len(values),len(values))].sum(0)
        denominator=totals[:,:3].sum(1)
        if (denominator>0).all():
            gains.append(float((totals[1,0]/denominator[1]-totals[0,0]/denominator[0])*100))
    return dict(ci95_pp=list(map(float,np.percentile(gains,[2.5,97.5]))) if gains else None,
                valid_resamples=len(gains),attempted_resamples=1000)

def calculate(counts):
    tp, fp, fn, tn = counts
    return dict(tp=tp, fp=fp, fn=fn, tn=tn,
                valid_pixels=sum(counts),
                iou=tp/(tp+fp+fn) if tp+fp+fn else None,
                precision=tp/(tp+fp) if tp+fp else None,
                recall=tp/(tp+fn) if tp+fn else None)


def inspect_inputs(report, data):
    import rasterio
    selected=set()
    for split in report["splits"].values():
        selected.update(split["zero_valid_samples"])
        selected.update(r["sample"] for r in split["worst"][:3])
    selected.add("Ghana_313799")
    results=[]
    for sid in sorted(selected):
        arrays=[];metadata=[];hashes={}
        for layer in ("S1Hand","S2Hand","LabelHand"):
            path=data/layer/(sid+"_"+layer+".tif")
            hashes[layer]=hashlib.sha256(path.read_bytes()).hexdigest()
            with rasterio.open(path) as ds:
                arrays.append(ds.read(masked=True).astype("float32").filled(np.nan))
                metadata.append(dict(shape=ds.shape,crs=str(ds.crs),transform=ds.transform))
        sar,optical,label=arrays;label=label[0]
        finite=np.isfinite(sar).all(0)&np.isfinite(optical).all(0)
        labels,counts=np.unique(label[np.isfinite(label)],return_counts=True)
        offsets=[]
        for meta in metadata[1:]:
            if meta["crs"]!=metadata[0]["crs"]:
                offsets.append(None)
                continue
            offsets.append(max(max(abs(v-e) for v,e in zip(
                (~metadata[0]["transform"])*(meta["transform"]*xy),xy))
                for xy in ((0,0),(512,0),(0,512),(512,512))))
        results.append(dict(sample=sid,source_sha256=hashes,
            input_finite_fraction=float(finite.mean()),
            labeled_input_pixels=int((finite&(label>=0)&np.isfinite(label)).sum()),
            label_counts=dict(zip(map(str,labels),map(int,counts))),
            finite_fraction_by_layer={name:float(np.isfinite(a).all(0).mean())
                                      for name,a in zip(("sar","optical","label"),arrays)},
            max_corner_displacement_pixels_relative_sar=offsets,
            sar_outside_clip_fraction=float(((sar<-50)|(sar>10)).mean()),
            optical_outside_clip_fraction=float(((optical<0)|(optical>12000)).mean()),
            limits="Targeted exposed failure cases; metadata agreement is not physical registration; clipping is not cloud detection."))
    return results


def audit(source, destination, data=None):
    raw = source.read_bytes()
    saved = json.loads(raw)
    destination.mkdir(parents=True, exist_ok=False)
    report = dict(source=str(source), sha256=hashlib.sha256(raw).hexdigest(),
                  precision=saved.get("evaluation_precision"),
                  scope="Retrospective existing exposed validation/test/Bolivia confusion counts, no new inference",
                  grouping="Sample-name prefix is the recorded event label; not independently verified geography",
                  causal_limits="No cloud labels, alignment residuals or per-pixel sensor-quality covariates here. Associations do not establish cause.",
                  splits={})
    flat = []
    for split in ("valid", "test", "bolivia"):
        totals = {mode: [0]*4 for mode in ("s1", "s2", "all")}
        events = collections.defaultdict(lambda: {m: [0]*4 for m in totals})
        zero, undefined, gains, scenes = [], [], [], []
        for row in saved[split]["samples"]:
            sid = row["sample"]
            event = sid.split("_")[0]
            metrics = {}
            for mode in totals:
                counts = [row[mode][key] for key in ("tp", "fp", "fn", "tn")]
                assert all(isinstance(v, int) and v >= 0 for v in counts)
                metrics[mode] = calculate(counts)
                expected = row[mode]["water_iou"]
                assert expected == metrics[mode]["iou"] or abs(expected-metrics[mode]["iou"]) < 1e-12
                totals[mode] = [a+b for a, b in zip(totals[mode], counts)]
                events[event][mode] = [a+b for a, b in zip(events[event][mode], counts)]
            assert len({v["valid_pixels"] for v in metrics.values()}) == 1
            if not metrics["all"]["valid_pixels"]:
                zero.append(sid)
            delta = None
            if metrics["all"]["iou"] is not None and metrics["s2"]["iou"] is not None:
                delta = 100*(metrics["all"]["iou"]-metrics["s2"]["iou"])
                gains.append(delta)
            else:
                undefined.append(sid)
            scenes.append(dict(sample=sid, event=event, joint_minus_optical_pp=delta, **metrics))
            flat.append(dict(split=split, sample=sid, event=event,
                             valid_pixels=metrics["all"]["valid_pixels"],
                             sar_iou=metrics["s1"]["iou"], optical_iou=metrics["s2"]["iou"],
                             joint_iou=metrics["all"]["iou"], joint_minus_optical_pp=delta))
        aggregate = {m: calculate(c) for m, c in totals.items()}
        for mode, m in aggregate.items():
            expected = saved[split]["aggregate"][mode]
            assert all(m[k] == expected[k] for k in ("tp", "fp", "fn", "tn"))
            assert abs(m["iou"]-expected["water_iou"]) < 1e-12
        groups = {event: {m: calculate(c) for m, c in modes.items()}
                  for event, modes in events.items()}
        for group in groups.values():
            group["joint_minus_optical_pp"] = (
                100*(group["all"]["iou"]-group["s2"]["iou"])
                if group["all"]["iou"] is not None and group["s2"]["iou"] is not None else None)
        report["splits"][split] = dict(
            n=len(scenes), aggregate=aggregate, events=groups, zero_valid_samples=zero,
            undefined_pair_iou_samples=undefined,
            joint_vs_optical_scenes=dict(better=sum(g>0 for g in gains),
                                        worse=sum(g<0 for g in gains), tied=sum(g==0 for g in gains),
                                        undefined=len(undefined)),
            joint_minus_optical_pooled_pp=100*(aggregate["all"]["iou"]-aggregate["s2"]["iou"]),
            paired_scene_bootstrap=interval([
                [[s[m][k] for k in ("tp","fp","fn","tn")] for m in ("s2","all")]
                for s in scenes]),
            paired_event_bootstrap=interval([
                [modes[m] for m in ("s2","all")] for modes in events.values()])
                if len(events)>1 else None,
            interval_limit="Retrospective exposed examples; event grouping from names. Single-event Bolivia cannot estimate cross-event uncertainty.",
            worst=sorted((s for s in scenes if s["joint_minus_optical_pp"] is not None),
                         key=lambda s:s["joint_minus_optical_pp"])[:10],
            scenes=scenes)
    (destination/"audit.json").write_text(json.dumps(report, indent=2)+"\n")
    with (destination/"scenes.csv").open("w", newline="") as f:
        writer=csv.DictWriter(f, fieldnames=list(flat[0]))
        writer.writeheader(); writer.writerows(flat)
    if data is not None:
        (destination/"input-diagnostics.json").write_text(
            json.dumps(inspect_inputs(report,data),indent=2)+"\n")
    print(json.dumps({s:{k:v for k,v in d.items() if k in (
        "n","zero_valid_samples","joint_vs_optical_scenes","joint_minus_optical_pooled_pp")}
        for s,d in report["splits"].items()},indent=2))


if __name__ == "__main__":
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument("source",type=Path)
    p.add_argument("destination",type=Path)
    p.add_argument("--data",type=Path)
    args=p.parse_args()
    audit(args.source,args.destination,args.data)
